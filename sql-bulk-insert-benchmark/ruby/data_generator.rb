# データ生成ユーティリティ
require 'securerandom'

class DataGenerator
  # シンプルなレコードを生成
  def self.generate_simple_record
    {
      name: random_string(20),
      email: "#{random_string(10)}@example.com",
      age: rand(18..80),
      score: rand(0.0..100.0).round(2)
    }
  end

  # シンプルなレコードを複数生成
  def self.generate_simple_records(count)
    Array.new(count) { generate_simple_record }
  end

  # 複雑なレコードを生成
  def self.generate_complex_record
    {
      uuid: SecureRandom.uuid,
      name: random_string(30),
      email: "#{random_string(15)}@example.com",
      age: rand(18..80),
      score: rand(0.0..100.0).round(2),
      balance: rand(-10000.0..100000.0).round(2),
      is_active: [true, false].sample,
      category: ['A', 'B', 'C', 'D', 'E'].sample,
      description: random_string(200),
      metadata: { key1: 'value1', key2: rand(1..1000) }.to_json,
      tags: Array.new(rand(1..5)) { "tag#{rand(100)}" }.to_json,
      last_login_at: Time.now - rand(0..365).days,
      ip_address: "#{rand(1..255)}.#{rand(1..255)}.#{rand(1..255)}.#{rand(1..255)}"
    }
  end

  # 複雑なレコードを複数生成
  def self.generate_complex_records(count)
    Array.new(count) { generate_complex_record }
  end

  # CSV形式の文字列を生成（COPY用）
  def self.generate_csv_data(count)
    records = generate_simple_records(count)
    records.map { |r| "#{r[:name]}\t#{r[:email]}\t#{r[:age]}\t#{r[:score]}" }.join("\n")
  end

  private

  def self.random_string(length)
    (0...length).map { ('a'..'z').to_a[rand(26)] }.join
  end
end

# テスト
if __FILE__ == $0
  puts "Simple record: #{DataGenerator.generate_simple_record.inspect}"
  puts "Complex record: #{DataGenerator.generate_complex_record.inspect}"
  puts "Generated #{DataGenerator.generate_simple_records(10).size} simple records"
end
