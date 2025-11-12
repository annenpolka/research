#!/usr/bin/env ruby
require 'net/http'
require 'json'
require 'uri'

# テストデータ
test_cases = [
  {
    name: "基本的な型のテスト",
    data: {
      integer_value: 42,
      float_value: 3.14,
      string_value: "hello",
      boolean_true: true,
      boolean_false: false,
      null_value: nil
    }
  },
  {
    name: "数値の境界値テスト",
    data: {
      zero: 0,
      negative: -100,
      large_integer: 9999999999,
      small_float: 0.0001,
      negative_float: -3.14
    }
  },
  {
    name: "配列のテスト",
    data: {
      integer_array: [1, 2, 3, 4, 5],
      mixed_array: [1, "two", 3.0, true, nil],
      nested_array: [[1, 2], [3, 4]]
    }
  },
  {
    name: "ネストしたハッシュのテスト",
    data: {
      user: {
        name: "John",
        age: 30,
        active: true,
        settings: {
          theme: "dark",
          notifications: false
        }
      }
    }
  },
  {
    name: "複雑なネストのテスト",
    data: {
      items: [
        { id: 1, price: 100.5, available: true },
        { id: 2, price: 200.0, available: false }
      ]
    }
  }
]

def send_request(data, server_url)
  uri = URI.parse("#{server_url}/test_params")
  http = Net::HTTP.new(uri.host, uri.port)

  request = Net::HTTP::Post.new(uri.path)
  request["Content-Type"] = "application/json"
  request.body = data.to_json

  response = http.request(request)
  JSON.parse(response.body)
end

def print_analysis(test_case, result)
  puts "\n" + "=" * 80
  puts "テストケース: #{test_case[:name]}"
  puts "=" * 80

  puts "\n【送信したデータ】"
  puts JSON.pretty_generate(test_case[:data])

  puts "\n【受信したパラメータ】"
  puts JSON.pretty_generate(result['received_params'])

  puts "\n【型の分析】"
  print_type_analysis(result['type_analysis'])
end

def print_type_analysis(analysis, indent = 0)
  prefix = "  " * indent

  case analysis
  when Hash
    if analysis.key?('value')
      # 終端の値
      puts "#{prefix}値: #{analysis['value'].inspect}"
      puts "#{prefix}Rubyクラス: #{analysis['class']}"
      puts "#{prefix}型: #{analysis['type']}"
      puts "#{prefix}文字列?: #{analysis['is_string']}"
      puts "#{prefix}数値?: #{analysis['is_numeric']}"
      puts "#{prefix}真偽値?: #{analysis['is_boolean']}"
      puts "#{prefix}nil?: #{analysis['is_nil']}"
    else
      # ハッシュのネスト
      analysis.each do |key, value|
        puts "#{prefix}#{key}:"
        print_type_analysis(value, indent + 1)
      end
    end
  when Array
    analysis.each_with_index do |item, i|
      puts "#{prefix}[#{i}]:"
      print_type_analysis(item, indent + 1)
    end
  end
end

# メイン処理
server_url = ARGV[0] || "http://localhost:3000"

puts "Railsサーバーに接続中: #{server_url}"
puts "JSONパラメータの型保持テストを開始します..."

test_cases.each do |test_case|
  begin
    result = send_request(test_case[:data], server_url)
    print_analysis(test_case, result)
  rescue => e
    puts "\nエラーが発生しました: #{e.message}"
    puts e.backtrace.join("\n")
  end
end

puts "\n" + "=" * 80
puts "すべてのテストが完了しました"
puts "=" * 80
