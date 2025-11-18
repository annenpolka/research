#!/usr/bin/env ruby
# MySQL用Rubyベンチマーク

require 'active_record'
require 'activerecord-import'
require 'mysql2'
require_relative 'data_generator'
require_relative 'benchmark_utils'

# MySQL接続設定
ActiveRecord::Base.establish_connection(
  adapter: 'mysql2',
  host: ENV.fetch('MYSQL_HOST', 'localhost'),
  port: ENV.fetch('MYSQL_PORT', 3306).to_i,
  username: ENV.fetch('MYSQL_USER', 'benchmark'),
  password: ENV.fetch('MYSQL_PASSWORD', 'benchmark'),
  database: ENV.fetch('MYSQL_DB', 'benchmark'),
  pool: 5
)

# モデル定義
class SimpleRecord < ActiveRecord::Base
  self.table_name = 'simple_records'
end

def cleanup_table
  SimpleRecord.connection.execute("TRUNCATE TABLE simple_records")
end

# ========================================
# Benchmark 1: create (1件ずつ)
# ========================================
def bench_create(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  records.each do |record|
    SimpleRecord.create(record)
  end
end

# ========================================
# Benchmark 2: insert_all
# ========================================
def bench_insert_all(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)
  SimpleRecord.insert_all(records)
end

# ========================================
# Benchmark 3: insert_all with batching
# ========================================
def bench_insert_all_batched(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  records.each_slice(batch_size) do |batch|
    SimpleRecord.insert_all(batch)
  end
end

# ========================================
# Benchmark 4: activerecord-import
# ========================================
def bench_activerecord_import(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  objects = records.map { |r| SimpleRecord.new(r) }
  SimpleRecord.import(objects)
end

# ========================================
# Benchmark 5: activerecord-import with batching
# ========================================
def bench_activerecord_import_batched(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  records.each_slice(batch_size) do |batch|
    objects = batch.map { |r| SimpleRecord.new(r) }
    SimpleRecord.import(objects)
  end
end

# ========================================
# Benchmark 6: activerecord-import (配列形式)
# ========================================
def bench_activerecord_import_arrays(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  columns = [:name, :email, :age, :score]
  values = records.map { |r| [r[:name], r[:email], r[:age], r[:score]] }

  SimpleRecord.import(columns, values)
end

# ========================================
# Benchmark 7: Raw mysql2 gem
# ========================================
def bench_raw_mysql2(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  client = Mysql2::Client.new(
    host: ENV.fetch('MYSQL_HOST', 'localhost'),
    port: ENV.fetch('MYSQL_PORT', 3306).to_i,
    username: ENV.fetch('MYSQL_USER', 'benchmark'),
    password: ENV.fetch('MYSQL_PASSWORD', 'benchmark'),
    database: ENV.fetch('MYSQL_DB', 'benchmark')
  )

  records.each_slice(batch_size) do |batch|
    values = batch.map do |r|
      "(#{client.escape(r[:name].to_s)}, #{client.escape(r[:email].to_s)}, #{r[:age]}, #{r[:score]})"
    end.join(', ')

    sql = "INSERT INTO simple_records (name, email, age, score) VALUES #{values}"
    client.query(sql)
  end

  client.close
end

# ========================================
# Benchmark 8: Raw mysql2 with prepared statement
# ========================================
def bench_raw_mysql2_prepared(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  client = Mysql2::Client.new(
    host: ENV.fetch('MYSQL_HOST', 'localhost'),
    port: ENV.fetch('MYSQL_PORT', 3306).to_i,
    username: ENV.fetch('MYSQL_USER', 'benchmark'),
    password: ENV.fetch('MYSQL_PASSWORD', 'benchmark'),
    database: ENV.fetch('MYSQL_DB', 'benchmark')
  )

  stmt = client.prepare("INSERT INTO simple_records (name, email, age, score) VALUES (?, ?, ?, ?)")

  records.each do |r|
    stmt.execute(r[:name], r[:email], r[:age], r[:score])
  end

  stmt.close
  client.close
end

# ========================================
# Benchmark 9: Multi-row INSERT with mysql2
# ========================================
def bench_mysql2_multi_row(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  client = Mysql2::Client.new(
    host: ENV.fetch('MYSQL_HOST', 'localhost'),
    port: ENV.fetch('MYSQL_PORT', 3306).to_i,
    username: ENV.fetch('MYSQL_USER', 'benchmark'),
    password: ENV.fetch('MYSQL_PASSWORD', 'benchmark'),
    database: ENV.fetch('MYSQL_DB', 'benchmark')
  )

  records.each_slice(batch_size) do |batch|
    placeholders = (['(?, ?, ?, ?)'] * batch.size).join(', ')
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES #{placeholders}"

    stmt = client.prepare(sql)
    values = batch.flat_map { |r| [r[:name], r[:email], r[:age], r[:score]] }
    stmt.execute(*values)
    stmt.close
  end

  client.close
end

# メイン実行
def main
  runner = BenchmarkRunner.new(output_file: '/results/ruby_mysql_results.json')

  test_sizes = [
    100_000,
    1_000_000,
    # 10_000_000,
  ]

  test_sizes.each do |size|
    puts "\n#{'#'*60}"
    puts "# Testing with #{size.to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse} records"
    puts "#{'#'*60}"

    # createは遅すぎるので10万件のみ
    if size <= 100_000
      runner.run_benchmark("mysql_create_#{size}", size) do
        bench_create(size)
      end

      runner.run_benchmark("mysql_raw_prepared_#{size}", size) do
        bench_raw_mysql2_prepared(size)
      end
    end

    runner.run_benchmark("mysql_insert_all_#{size}", size) do
      bench_insert_all(size)
    end

    runner.run_benchmark("mysql_insert_all_batched_#{size}", size) do
      bench_insert_all_batched(size)
    end

    runner.run_benchmark("mysql_activerecord_import_#{size}", size) do
      bench_activerecord_import(size)
    end

    runner.run_benchmark("mysql_activerecord_import_batched_#{size}", size) do
      bench_activerecord_import_batched(size)
    end

    runner.run_benchmark("mysql_activerecord_import_arrays_#{size}", size) do
      bench_activerecord_import_arrays(size)
    end

    runner.run_benchmark("mysql_raw_mysql2_#{size}", size) do
      bench_raw_mysql2(size)
    end

    runner.run_benchmark("mysql_mysql2_multi_row_#{size}", size) do
      bench_mysql2_multi_row(size)
    end
  end

  runner.save_results
  runner.print_summary
end

if __FILE__ == $0
  puts "MySQL Bulk Insert Benchmark - Ruby"
  puts "=" * 60
  main
end
