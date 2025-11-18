#!/usr/bin/env ruby
# ActiveRecordを使用したベンチマーク

require 'active_record'
require 'activerecord-import'
require_relative 'data_generator'
require_relative 'benchmark_utils'

# PostgreSQL接続設定
ActiveRecord::Base.establish_connection(
  adapter: 'postgresql',
  host: ENV.fetch('POSTGRES_HOST', 'localhost'),
  port: ENV.fetch('POSTGRES_PORT', 5432).to_i,
  username: ENV.fetch('POSTGRES_USER', 'benchmark'),
  password: ENV.fetch('POSTGRES_PASSWORD', 'benchmark'),
  database: ENV.fetch('POSTGRES_DB', 'benchmark'),
  pool: 5
)

# モデル定義
class SimpleRecord < ActiveRecord::Base
  self.table_name = 'simple_records'
end

def cleanup_table
  SimpleRecord.connection.execute("TRUNCATE TABLE simple_records RESTART IDENTITY CASCADE")
end

# ========================================
# Benchmark 1: create (1件ずつ - 最も遅い)
# ========================================
def bench_create(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  records.each do |record|
    SimpleRecord.create(record)
  end
end

# ========================================
# Benchmark 2: insert_all (Rails 6+)
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
# Benchmark 7: activerecord-import with validate: false
# ========================================
def bench_activerecord_import_no_validate(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  objects = records.map { |r| SimpleRecord.new(r) }
  SimpleRecord.import(objects, validate: false)
end

# ========================================
# Benchmark 8: activerecord-import with batch_size option
# ========================================
def bench_activerecord_import_batch_option(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  objects = records.map { |r| SimpleRecord.new(r) }
  SimpleRecord.import(objects, batch_size: batch_size)
end

# ========================================
# Benchmark 9: Raw SQL INSERT
# ========================================
def bench_raw_sql_insert(record_count, batch_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  records.each_slice(batch_size) do |batch|
    values = batch.map do |r|
      conn = SimpleRecord.connection
      "(#{conn.quote(r[:name])}, #{conn.quote(r[:email])}, #{r[:age]}, #{r[:score]})"
    end.join(', ')

    sql = "INSERT INTO simple_records (name, email, age, score) VALUES #{values}"
    SimpleRecord.connection.execute(sql)
  end
end

# ========================================
# Benchmark 10: upsert_all (Rails 6+)
# ========================================
def bench_upsert_all(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  # upsert_allは競合を処理できるが、ここでは単純な挿入として使用
  SimpleRecord.upsert_all(records, unique_by: :id)
end

# メイン実行
def main
  runner = BenchmarkRunner.new(output_file: '/results/ruby_activerecord_results.json')

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
      runner.run_benchmark("activerecord_create_#{size}", size) do
        bench_create(size)
      end
    end

    runner.run_benchmark("activerecord_insert_all_#{size}", size) do
      bench_insert_all(size)
    end

    runner.run_benchmark("activerecord_insert_all_batched_#{size}", size) do
      bench_insert_all_batched(size)
    end

    runner.run_benchmark("activerecord_import_#{size}", size) do
      bench_activerecord_import(size)
    end

    runner.run_benchmark("activerecord_import_batched_#{size}", size) do
      bench_activerecord_import_batched(size)
    end

    runner.run_benchmark("activerecord_import_arrays_#{size}", size) do
      bench_activerecord_import_arrays(size)
    end

    runner.run_benchmark("activerecord_import_no_validate_#{size}", size) do
      bench_activerecord_import_no_validate(size)
    end

    runner.run_benchmark("activerecord_import_batch_option_#{size}", size) do
      bench_activerecord_import_batch_option(size)
    end

    runner.run_benchmark("activerecord_raw_sql_#{size}", size) do
      bench_raw_sql_insert(size)
    end

    runner.run_benchmark("activerecord_upsert_all_#{size}", size) do
      bench_upsert_all(size)
    end
  end

  runner.save_results
  runner.print_summary
end

if __FILE__ == $0
  puts "PostgreSQL Bulk Insert Benchmark - ActiveRecord"
  puts "=" * 60
  main
end
