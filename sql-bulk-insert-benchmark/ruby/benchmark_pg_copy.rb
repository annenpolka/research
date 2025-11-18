#!/usr/bin/env ruby
# PostgreSQL COPY を使用したベンチマーク

require 'pg'
require 'active_record'
require 'activerecord-copy'
require_relative 'data_generator'
require_relative 'benchmark_utils'

# PostgreSQL接続設定
ActiveRecord::Base.establish_connection(
  adapter: 'postgresql',
  host: ENV.fetch('POSTGRES_HOST', 'localhost'),
  port: ENV.fetch('POSTGRES_PORT', 5432).to_i,
  username: ENV.fetch('POSTGRES_USER', 'benchmark'),
  password: ENV.fetch('POSTGRES_PASSWORD', 'benchmark'),
  database: ENV.fetch('POSTGRES_DB', 'benchmark')
)

# モデル定義
class SimpleRecord < ActiveRecord::Base
  self.table_name = 'simple_records'
end

def cleanup_table
  SimpleRecord.connection.execute("TRUNCATE TABLE simple_records RESTART IDENTITY CASCADE")
end

# ========================================
# Benchmark 1: activerecord-copy gem
# ========================================
def bench_activerecord_copy(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  # activerecord-copyを使用
  columns = [:name, :email, :age, :score]
  values = records.map { |r| [r[:name], r[:email], r[:age], r[:score]] }

  SimpleRecord.copy_from_client(columns) do |copy|
    values.each do |row|
      copy << row
    end
  end
end

# ========================================
# Benchmark 2: Raw pg gem COPY
# ========================================
def bench_raw_pg_copy(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  # pg gemを直接使用
  conn = PG.connect(
    host: ENV.fetch('POSTGRES_HOST', 'localhost'),
    port: ENV.fetch('POSTGRES_PORT', 5432).to_i,
    user: ENV.fetch('POSTGRES_USER', 'benchmark'),
    password: ENV.fetch('POSTGRES_PASSWORD', 'benchmark'),
    dbname: ENV.fetch('POSTGRES_DB', 'benchmark')
  )

  conn.exec("COPY simple_records (name, email, age, score) FROM STDIN WITH (FORMAT CSV)")

  records.each do |r|
    conn.put_copy_data("#{r[:name]},#{r[:email]},#{r[:age]},#{r[:score]}\n")
  end

  conn.put_copy_end
  conn.close
end

# ========================================
# Benchmark 3: pg gem COPY with tab delimiter
# ========================================
def bench_raw_pg_copy_tab(record_count)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  conn = PG.connect(
    host: ENV.fetch('POSTGRES_HOST', 'localhost'),
    port: ENV.fetch('POSTGRES_PORT', 5432).to_i,
    user: ENV.fetch('POSTGRES_USER', 'benchmark'),
    password: ENV.fetch('POSTGRES_PASSWORD', 'benchmark'),
    dbname: ENV.fetch('POSTGRES_DB', 'benchmark')
  )

  conn.exec("COPY simple_records (name, email, age, score) FROM STDIN")

  records.each do |r|
    conn.put_copy_data("#{r[:name]}\t#{r[:email]}\t#{r[:age]}\t#{r[:score]}\n")
  end

  conn.put_copy_end
  conn.close
end

# ========================================
# Benchmark 4: pg gem COPY with buffer
# ========================================
def bench_raw_pg_copy_buffered(record_count, buffer_size: 1000)
  cleanup_table
  records = DataGenerator.generate_simple_records(record_count)

  conn = PG.connect(
    host: ENV.fetch('POSTGRES_HOST', 'localhost'),
    port: ENV.fetch('POSTGRES_PORT', 5432).to_i,
    user: ENV.fetch('POSTGRES_USER', 'benchmark'),
    password: ENV.fetch('POSTGRES_PASSWORD', 'benchmark'),
    dbname: ENV.fetch('POSTGRES_DB', 'benchmark')
  )

  conn.exec("COPY simple_records (name, email, age, score) FROM STDIN WITH (FORMAT CSV)")

  buffer = []
  records.each_with_index do |r, i|
    buffer << "#{r[:name]},#{r[:email]},#{r[:age]},#{r[:score]}\n"

    if buffer.size >= buffer_size || i == records.size - 1
      conn.put_copy_data(buffer.join)
      buffer.clear
    end
  end

  conn.put_copy_end
  conn.close
end

# メイン実行
def main
  runner = BenchmarkRunner.new(output_file: '/results/ruby_pg_copy_results.json')

  test_sizes = [
    100_000,
    1_000_000,
    # 10_000_000,
  ]

  test_sizes.each do |size|
    puts "\n#{'#'*60}"
    puts "# Testing with #{size.to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse} records"
    puts "#{'#'*60}"

    runner.run_benchmark("pg_copy_activerecord_copy_#{size}", size) do
      bench_activerecord_copy(size)
    end

    runner.run_benchmark("pg_copy_raw_csv_#{size}", size) do
      bench_raw_pg_copy(size)
    end

    runner.run_benchmark("pg_copy_raw_tab_#{size}", size) do
      bench_raw_pg_copy_tab(size)
    end

    runner.run_benchmark("pg_copy_raw_buffered_#{size}", size) do
      bench_raw_pg_copy_buffered(size)
    end
  end

  runner.save_results
  runner.print_summary
end

if __FILE__ == $0
  puts "PostgreSQL COPY Benchmark - Ruby"
  puts "=" * 60
  main
end
