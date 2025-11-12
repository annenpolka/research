# Rails JSON Params Handling

## 概要

Railsでjsonを受け取った時、paramsで値は保持されるのか、文字列に変換されるのか、検証する研究プロジェクト。

## 動機

RailsのActionController::Parametersが、JSONリクエストで送信された値をどのように扱うかを理解することは重要です。特に以下の点を明らかにします：

- 数値（Integer, Float）は数値型のまま保持されるか、文字列に変換されるか
- ブール値（true, false）は保持されるか
- null値はどのように扱われるか
- ネストした配列やハッシュはどうなるか

## 手法

1. シンプルなRails APIアプリケーションを作成
2. 様々な型のJSONパラメータを受け取るエンドポイントを実装
3. 受け取ったparamsの型を検証するテストスクリプトを実行
4. 結果を記録

テスト環境：
- Rails 8.1.1
- Ruby 3.3.6
- Content-Type: application/json

## 結果

### 検証結果サマリー

**Railsはparamsで値の型を保持します。文字列に変換されません。**

### 詳細な検証結果

#### 1. 基本的な型の保持

| JSON型 | 送信値 | Rubyクラス | 型保持 |
|--------|--------|-----------|--------|
| integer | 42 | Integer | ✅ |
| float | 3.14 | Float | ✅ |
| string | "hello" | String | ✅ |
| boolean (true) | true | TrueClass | ✅ |
| boolean (false) | false | FalseClass | ✅ |
| null | null | NilClass | ✅ |

#### 2. 数値の境界値テスト

| 値の種類 | 送信値 | Rubyクラス | 型保持 |
|---------|--------|-----------|--------|
| ゼロ | 0 | Integer | ✅ |
| 負の整数 | -100 | Integer | ✅ |
| 大きな整数 | 9999999999 | Integer | ✅ |
| 小数 | 0.0001 | Float | ✅ |
| 負の小数 | -3.14 | Float | ✅ |

#### 3. 配列の型保持

- **整数配列**: `[1, 2, 3, 4, 5]` → すべてInteger型で保持 ✅
- **混合型配列**: `[1, "two", 3.0, true, null]` → それぞれの型が保持される ✅
  - ただし、配列内のnullは除外される（Railsの仕様）
- **ネストした配列**: `[[1, 2], [3, 4]]` → 構造と型が保持される ✅

#### 4. ハッシュのネストと型保持

複雑にネストしたハッシュでも、すべての階層で型が保持されることを確認：

```json
{
  "user": {
    "name": "John",        // String
    "age": 30,             // Integer
    "active": true,        // TrueClass
    "settings": {
      "theme": "dark",     // String
      "notifications": false  // FalseClass
    }
  }
}
```

すべての値が期待通りの型で保持される ✅

#### 5. 配列とハッシュの複雑な組み合わせ

```json
{
  "items": [
    {"id": 1, "price": 100.5, "available": true},
    {"id": 2, "price": 200.0, "available": false}
  ]
}
```

配列内のハッシュの各フィールドも正しく型が保持される ✅

### 重要な発見

1. **数値は文字列に変換されない**
   - `params[:price]` で受け取った100.5は、Float型のまま保持される
   - `params[:id]` で受け取った1は、Integer型のまま保持される

2. **真偽値は文字列に変換されない**
   - `params[:active]` で受け取ったtrueは、TrueClassのまま保持される
   - 文字列の"true"/"false"にはならない

3. **nullはnilとして保持される**
   - ただし、配列内のnullは除外される（Railsの仕様）

4. **ネストした構造も型を保持**
   - どれだけ深くネストしても、各値の型は保持される

## 使い方

### サーバーの起動

```bash
cd rails-json-params-handling
bundle install
bin/rails server
```

### テストスクリプトの実行

```bash
ruby test_json_params.rb http://localhost:3000
```

### 手動でテスト

```bash
curl -X POST http://localhost:3000/test_params \
  -H "Content-Type: application/json" \
  -d '{"number": 42, "text": "hello", "flag": true}'
```

## 結論

**RailsはContent-Type: application/jsonで送信されたパラメータの型を保持します。**

これは以下を意味します：

1. **APIの設計が簡潔になる**
   - クライアントから送信された数値や真偽値を、サーバー側で文字列から変換する必要がない
   - Strong Parametersでそのまま型チェックできる

2. **型の安全性が向上**
   - `params[:age].to_i` のような変換が不要
   - 数値として送信されたものは数値として扱える

3. **注意点**
   - これはContent-Type: application/jsonの場合のみ
   - フォームデータ（application/x-www-form-urlencoded）の場合は、すべて文字列として扱われる
   - 配列内のnullは除外される

### 実用上の推奨事項

- JSON APIを構築する場合、型の変換を意識する必要は少ない
- ただし、入力値の検証（バリデーション）は依然として重要
- Strong Parametersで適切な型を指定することで、より安全なAPIになる

## ファイル構成

- `app/controllers/params_test_controller.rb` - テスト用コントローラー
- `test_json_params.rb` - 検証用Rubyスクリプト
- `README.md` - このファイル
