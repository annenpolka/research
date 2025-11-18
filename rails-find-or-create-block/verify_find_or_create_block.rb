#!/usr/bin/env ruby
# frozen_string_literal: true

require 'bundler/inline'

gemfile do
  source 'https://rubygems.org'
  gem 'activerecord', '~> 7.0'
  gem 'sqlite3', '~> 1.4'
end

require 'active_record'
require 'logger'

# データベース接続設定
ActiveRecord::Base.establish_connection(
  adapter: 'sqlite3',
  database: ':memory:'
)

# ログを有効化（SQLクエリを見るため）
ActiveRecord::Base.logger = Logger.new(STDOUT)
ActiveRecord::Base.logger.level = Logger::INFO

# スキーマ定義
ActiveRecord::Schema.define do
  create_table :users, force: true do |t|
    t.string :email, null: false
    t.string :name
    t.integer :login_count, default: 0
    t.timestamps
  end

  add_index :users, :email, unique: true
end

# モデル定義
class User < ActiveRecord::Base
  validates :email, presence: true, uniqueness: true
end

# テストヘルパー
def separator(title)
  puts "\n" + "=" * 80
  puts "  #{title}"
  puts "=" * 80 + "\n"
end

def test_case(description)
  puts "\n--- #{description} ---"
  yield
  puts ""
end

# ブロック実行をトラッキングする変数
block_executed = false

separator("テスト1: 新規レコード作成時のブロック実行")

test_case("find_or_create_by! でブロックを渡して新規作成") do
  block_executed = false

  user = User.find_or_create_by!(email: 'alice@example.com') do |u|
    puts "  ✓ ブロックが実行されました！"
    block_executed = true
    u.name = 'Alice'
    u.login_count = 1
  end

  puts "  結果: ブロック実行 = #{block_executed}"
  puts "  ユーザー: #{user.attributes.inspect}"
  puts "  新規レコード？ = #{user.id == User.find_by(email: 'alice@example.com').id}"
end

separator("テスト2: 既存レコード検索時のブロック実行")

test_case("同じemailで再度find_or_create_by!を実行（既存レコードを検索）") do
  block_executed = false

  user = User.find_or_create_by!(email: 'alice@example.com') do |u|
    puts "  ✓ ブロックが実行されました！"
    block_executed = true
    u.name = 'Alice Modified'
    u.login_count = 999
  end

  puts "  結果: ブロック実行 = #{block_executed}"
  puts "  ユーザー: #{user.attributes.inspect}"
  puts "  nameが変更されたか？ = #{user.name == 'Alice Modified'}"
  puts "  login_countが変更されたか？ = #{user.login_count == 999}"
end

separator("テスト3: find_or_create_by (バン無し) の動作")

test_case("find_or_create_by でブロックを渡して新規作成") do
  block_executed = false

  user = User.find_or_create_by(email: 'bob@example.com') do |u|
    puts "  ✓ ブロックが実行されました！"
    block_executed = true
    u.name = 'Bob'
    u.login_count = 5
  end

  puts "  結果: ブロック実行 = #{block_executed}"
  puts "  ユーザー: #{user.attributes.inspect}"
end

test_case("同じemailで再度find_or_create_byを実行（既存レコードを検索）") do
  block_executed = false

  user = User.find_or_create_by(email: 'bob@example.com') do |u|
    puts "  ✓ ブロックが実行されました！"
    block_executed = true
    u.name = 'Bob Modified'
    u.login_count = 888
  end

  puts "  結果: ブロック実行 = #{block_executed}"
  puts "  ユーザー: #{user.attributes.inspect}"
  puts "  nameが変更されたか？ = #{user.name == 'Bob Modified'}"
  puts "  login_countが変更されたか？ = #{user.login_count == 888}"
end

separator("テスト4: ブロック内で設定した属性の永続化")

test_case("新規作成時にブロックで設定した属性は自動的に保存されるか？") do
  user = User.find_or_create_by!(email: 'charlie@example.com') do |u|
    u.name = 'Charlie'
    u.login_count = 10
  end

  # データベースから再取得して確認
  reloaded = User.find_by(email: 'charlie@example.com')
  puts "  保存されたname: #{reloaded.name}"
  puts "  保存されたlogin_count: #{reloaded.login_count}"
  puts "  ブロックで設定した値が保存された？ = #{reloaded.name == 'Charlie' && reloaded.login_count == 10}"
end

separator("テスト5: バリデーションエラー時の動作")

test_case("find_or_create_by! でバリデーションエラーが発生する場合") do
  begin
    user = User.find_or_create_by!(email: nil) do |u|
      puts "  ✓ ブロックが実行されました！"
      u.name = 'Invalid User'
    end
  rescue ActiveRecord::RecordInvalid => e
    puts "  例外が発生: #{e.message}"
    puts "  find_or_create_by! はバリデーションエラー時に例外を投げる"
  end
end

test_case("find_or_create_by (バン無し) でバリデーションエラーが発生する場合") do
  user = User.find_or_create_by(email: nil) do |u|
    puts "  ✓ ブロックが実行されました！"
    u.name = 'Invalid User'
  end

  puts "  戻り値: #{user.inspect}"
  puts "  保存済み？ = #{user.persisted?}"
  puts "  エラー: #{user.errors.full_messages}"
  puts "  find_or_create_by は例外を投げず、保存されていないオブジェクトを返す"
end

separator("まとめ: 最終的なデータベースの状態")

puts "全ユーザー一覧:"
User.all.each do |user|
  puts "  - #{user.email}: #{user.name} (login_count: #{user.login_count})"
end

separator("結論")

puts <<~CONCLUSION

  1. **新規レコード作成時**: ブロックは実行され、その中で設定した属性は保存される

  2. **既存レコード検索時**: ブロックは実行されない（これが重要！）

  3. **バン付き/バン無しの違い**:
     - find_or_create_by!: バリデーションエラー時に例外を投げる
     - find_or_create_by: バリデーションエラー時に未保存のオブジェクトを返す

  4. **ブロックの用途**:
     - 新規レコード作成時のデフォルト値設定に使用する
     - 既存レコードには影響しない（ブロックが実行されないため）

  5. **注意点**:
     - 既存レコードに対して何か処理をしたい場合は、ブロックに頼らず
       find_or_create_by の戻り値に対して明示的に処理を行う必要がある

CONCLUSION
