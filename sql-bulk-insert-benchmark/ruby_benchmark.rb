#!/usr/bin/env ruby
# frozen_string_literal: true

=begin
SQLバルクインサートベンチマーク - Ruby版

数千万件のデータをPostgreSQLに挿入する際の
様々なライブラリと手法のパフォーマンス比較
=end

require 'pg'
require 'active_record'
require 'activerecord-import'
require 'activerecord-copy'
require 'benchmark'
require 'securerandom'

# データベース接続設定（環境変数から取得、デフォルト値はローカル用）
DB_CONFIG = {
  adapter: 'postgresql',
  host: ENV.fetch('PGHOST', 'localhost'),
  port: ENV.fetch('PGPORT', '5432').to_i,
  database: ENV.fetch('PGDATABASE', 'benchmark_db'),
  username: ENV.fetch('PGUSER', 'benchmark_user'),
  password: ENV.fetch('PGPASSWORD', 'benchmark_pass')
}

# ActiveRecord接続
ActiveRecord::Base.establish_connection(DB_CONFIG)

# ベンチマーク用モデルの基底クラス
class BenchmarkRecord < ActiveRecord::Base
  self.abstract_class = true
end

# 各ベンチマーク用のモデル
class BenchmarkCreate < BenchmarkRecord
end

class BenchmarkInsertAll < BenchmarkRecord
end

class BenchmarkImport < BenchmarkRecord
end

class BenchmarkCopy < BenchmarkRecord
end

class BenchmarkRawPg < BenchmarkRecord
end

class BenchmarkRawPgCopy < BenchmarkRecord
end

# テーブル作成
def create_table(table_name)
  ActiveRecord::Base.connection.execute("DROP TABLE IF EXISTS #{table_name}")
  ActiveRecord::Base.connection.execute(<<-SQL)
    CREATE TABLE #{table_name} (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL,
      username VARCHAR(50) NOT NULL,
      email VARCHAR(100) NOT NULL,
      score FLOAT NOT NULL,
      created_at TIMESTAMP NOT NULL
    )
  SQL
end

# テストデータ生成
def generate_data(num_records)
  data = []
  num_records.times do |i|
    data << {
      user_id: rand(1..1_000_000),
      username: "user_#{SecureRandom.alphanumeric(10)}",
      email: "user#{i}@example.com",
      score: rand * 100,
      created_at: Time.now
    }
  end
  data
end

# 1. ActiveRecord の create (ベースライン - 大量データには不向き)
def benchmark_activerecord_create(num_records)
  table_name = 'benchmark_creates'
  BenchmarkCreate.table_name = table_name
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    data.each do |record|
      BenchmarkCreate.create!(record)
    end
  end

  {
    method: 'ActiveRecord create (個別)',
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# 2. ActiveRecord の insert_all (Rails 6+)
def benchmark_activerecord_insert_all(num_records, batch_size: 10_000)
  table_name = 'benchmark_insert_alls'
  BenchmarkInsertAll.table_name = table_name
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    data.each_slice(batch_size) do |batch|
      BenchmarkInsertAll.insert_all(batch)
    end
  end

  {
    method: "ActiveRecord insert_all (batch=#{batch_size})",
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# 3. activerecord-import gem
def benchmark_activerecord_import(num_records, batch_size: 10_000)
  table_name = 'benchmark_imports'
  BenchmarkImport.table_name = table_name
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    data.each_slice(batch_size) do |batch|
      records = batch.map { |attrs| BenchmarkImport.new(attrs) }
      BenchmarkImport.import(records, validate: false)
    end
  end

  {
    method: "activerecord-import (batch=#{batch_size})",
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# 4. activerecord-copy gem (PostgreSQL COPY)
def benchmark_activerecord_copy(num_records)
  table_name = 'benchmark_copies'
  BenchmarkCopy.table_name = table_name
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    columns = [:user_id, :username, :email, :score, :created_at]
    values = data.map { |row| columns.map { |col| row[col] } }

    BenchmarkCopy.copy_from_client(columns) do |copy|
      values.each do |row|
        copy << row
      end
    end
  end

  {
    method: 'activerecord-copy (COPY)',
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# 5. 生のPG gem - execute
def benchmark_raw_pg_execute(num_records, batch_size: 10_000)
  table_name = 'benchmark_raw_pgs'
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    conn = PG.connect(
      host: DB_CONFIG[:host],
      port: DB_CONFIG[:port],
      dbname: DB_CONFIG[:database],
      user: DB_CONFIG[:username],
      password: DB_CONFIG[:password]
    )

    begin
      data.each_slice(batch_size) do |batch|
        values_str = batch.map do |row|
          "(#{row[:user_id]}, '#{row[:username]}', '#{row[:email]}', #{row[:score]}, '#{row[:created_at]}')"
        end.join(', ')

        conn.exec(
          "INSERT INTO #{table_name} (user_id, username, email, score, created_at) VALUES #{values_str}"
        )
      end
    ensure
      conn.close
    end
  end

  {
    method: "Raw PG execute (batch=#{batch_size})",
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# 6. 生のPG gem - COPY
def benchmark_raw_pg_copy(num_records)
  table_name = 'benchmark_raw_pg_copies'
  create_table(table_name)

  data = generate_data(num_records)

  elapsed_time = Benchmark.realtime do
    conn = PG.connect(
      host: DB_CONFIG[:host],
      port: DB_CONFIG[:port],
      dbname: DB_CONFIG[:database],
      user: DB_CONFIG[:username],
      password: DB_CONFIG[:password]
    )

    begin
      conn.copy_data("COPY #{table_name} (user_id, username, email, score, created_at) FROM STDIN WITH (FORMAT CSV)") do
        data.each do |row|
          conn.put_copy_data([
            row[:user_id],
            row[:username],
            row[:email],
            row[:score],
            row[:created_at]
          ].join(',') + "\n")
        end
      end
    ensure
      conn.close
    end
  end

  {
    method: 'Raw PG COPY',
    records: num_records,
    time: elapsed_time,
    records_per_second: num_records / elapsed_time
  }
end

# ベンチマーク実行
def run_benchmarks(num_records)
  puts "\n#{'=' * 80}"
  puts "Ruby SQLバルクインサートベンチマーク - #{num_records.to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件"
  puts "#{'=' * 80}\n"

  results = []

  # 小規模データでのみActiveRecord createをテスト
  if num_records <= 10_000
    puts "1. ActiveRecord create をテスト中..."
    begin
      result = benchmark_activerecord_create(num_records)
      results << result
      puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
    rescue => e
      puts "   エラー: #{e.message}\n"
    end
  end

  puts "2. ActiveRecord insert_all をテスト中..."
  begin
    result = benchmark_activerecord_insert_all(num_records)
    results << result
    puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
  rescue => e
    puts "   エラー: #{e.message}\n"
  end

  puts "3. activerecord-import をテスト中..."
  begin
    result = benchmark_activerecord_import(num_records)
    results << result
    puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
  rescue => e
    puts "   エラー: #{e.message}\n"
  end

  puts "4. activerecord-copy (COPY) をテスト中..."
  begin
    result = benchmark_activerecord_copy(num_records)
    results << result
    puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
  rescue => e
    puts "   エラー: #{e.message}\n"
  end

  puts "5. Raw PG execute をテスト中..."
  begin
    result = benchmark_raw_pg_execute(num_records)
    results << result
    puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
  rescue => e
    puts "   エラー: #{e.message}\n"
  end

  puts "6. Raw PG COPY をテスト中..."
  begin
    result = benchmark_raw_pg_copy(num_records)
    results << result
    puts "   完了: #{result[:time].round(2)}秒, #{result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse}件/秒\n"
  rescue => e
    puts "   エラー: #{e.message}\n"
  end

  # 結果を速度順にソート
  results.sort_by! { |r| r[:time] }

  puts "\n#{'=' * 80}"
  puts "ベンチマーク結果 (速い順)"
  puts "#{'=' * 80}\n"
  puts "%-4s %-45s %-12s %-15s %s" % ['順位', 'メソッド', '時間(秒)', '件/秒', '相対速度']
  puts "-" * 80

  fastest_time = results.first[:time]
  results.each_with_index do |result, i|
    relative_speed = fastest_time / result[:time]
    rps = result[:records_per_second].round(0).to_s.reverse.gsub(/(\d{3})(?=\d)/, '\\1,').reverse
    puts "%-4d %-45s %-12.2f %-15s %.2fx" % [
      i + 1,
      result[:method],
      result[:time],
      rps,
      relative_speed
    ]
  end

  results
end

# メイン実行
if __FILE__ == $0
  # コマンドライン引数から件数を取得（デフォルトは100万件）
  num_records = (ARGV[0] || 1_000_000).to_i

  results = run_benchmarks(num_records)

  puts "\n#{'=' * 80}"
  puts "推奨事項"
  puts "#{'=' * 80}\n"
  puts "最速: PostgreSQLのCOPYコマンド（activerecord-copyまたはRaw PG COPY）"
  puts "バランス: activerecord-importが使いやすさと速度のバランスが良い"
  puts "Rails標準: insert_allはRails 6+で使用可能で依存なし"
  puts "避けるべき: 個別createは大量データでは非常に遅い"
end
