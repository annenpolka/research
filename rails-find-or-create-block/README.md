# Rails find_or_create_by! ブロック実行検証

## 概要

ActiveRecordの`find_or_create_by!`メソッドにブロックを渡した場合、既存レコードを見つけた時とレコードを新規作成する時で、ブロックの実行動作がどう異なるかを実験的に検証します。

## 研究質問

1. 既存レコードが見つかった場合、ブロックは実行されるか？
2. 新規レコードを作成する場合、ブロックは実行されるか？
3. `find_or_create_by`（バン無し）と`find_or_create_by!`（バン付き）で動作に違いはあるか？
4. ブロック内で属性を設定した場合、既存レコードに影響するか？

## 動機

`find_or_create_by!`はRailsアプリケーションでよく使用されるパターンですが、ブロックを渡した際の動作が直感的でない可能性があります。この動作を明確にすることで、バグを防ぎ、コードの意図を明確にできます。

## 手法

1. SQLiteを使用したスタンドアロンのRubyスクリプトを作成
2. ActiveRecordを使用してテーブルとモデルを定義
3. 以下のシナリオをテスト：
   - 新規レコード作成時のブロック実行
   - 既存レコード検索時のブロック実行
   - ブロック内での属性設定の影響
   - バン付き/バン無しメソッドの比較

## 結果

### テスト1: 新規レコード作成時のブロック実行

```ruby
User.find_or_create_by!(email: 'alice@example.com') do |u|
  u.name = 'Alice'
  u.login_count = 1
end
```

- ✅ **ブロックは実行された**
- ✅ ブロック内で設定した属性（name, login_count）は保存された
- 結果: `{email: "alice@example.com", name: "Alice", login_count: 1}`

### テスト2: 既存レコード検索時のブロック実行

```ruby
# 同じemailで再度実行
User.find_or_create_by!(email: 'alice@example.com') do |u|
  u.name = 'Alice Modified'
  u.login_count = 999
end
```

- ❌ **ブロックは実行されなかった**
- ❌ name, login_countは変更されなかった
- 結果: `{email: "alice@example.com", name: "Alice", login_count: 1}` （元のまま）

### テスト3: バン付き/バン無しの比較

**共通点:**
- どちらも既存レコードが見つかった場合、ブロックは実行されない

**相違点:**
- `find_or_create_by!`: バリデーションエラー時に `ActiveRecord::RecordInvalid` 例外を投げる
- `find_or_create_by`: バリデーションエラー時に未保存のオブジェクトを返す（例外なし）

### テスト4: バリデーションエラー時の動作

バリデーションエラーが発生する場合でも、ブロックは実行されます。ただし：

- `find_or_create_by!`: 例外を投げる
- `find_or_create_by`: `persisted?` が `false` のオブジェクトを返す

## 使い方

```bash
# 依存関係のインストール
gem install activerecord sqlite3

# 実験の実行
ruby verify_find_or_create_block.rb
```

## 結論

### 主要な発見

1. **既存レコードが見つかった場合、ブロックは実行されない**
   - これが最も重要なポイント
   - ブロックは「新規レコード作成時のみ」実行される

2. **新規レコード作成時、ブロックは実行され属性が保存される**
   - ブロック内で設定した値はデータベースに永続化される
   - デフォルト値を設定する用途に適している

3. **バン付き/バン無しの違いはエラーハンドリングのみ**
   - ブロック実行の動作は同じ
   - バリデーションエラー時の挙動のみ異なる

### ベストプラクティス

#### ❌ 避けるべきパターン

```ruby
# 既存レコードに対してブロックが実行されることを期待している（実行されない！）
user = User.find_or_create_by!(email: email) do |u|
  u.login_count += 1  # 既存ユーザーの場合、これは実行されない
end
```

#### ✅ 推奨パターン

```ruby
# 新規作成時のデフォルト値設定
user = User.find_or_create_by!(email: email) do |u|
  u.name = 'Guest'
  u.login_count = 0
end

# 既存/新規に関わらず処理が必要な場合は、戻り値に対して明示的に処理
user.login_count += 1
user.save!
```

または

```ruby
# 既存レコードかどうかで処理を分岐
user = User.find_or_initialize_by(email: email)
if user.new_record?
  user.name = 'Guest'
  user.login_count = 0
else
  user.login_count += 1
end
user.save!
```

### 実用的な影響

この動作を理解していないと、以下のようなバグが発生する可能性があります：

- 既存ユーザーのログインカウントが更新されない
- 既存レコードの属性更新が意図せず失敗する
- デフォルト値の設定が新規作成時のみに限定されることを見落とす

**結論:** `find_or_create_by!`のブロックは「新規レコード作成時の初期化処理」として使用し、既存レコードへの操作には使用しないこと。
