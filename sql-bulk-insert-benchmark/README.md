# SQLバルクインサート パフォーマンスベンチマーク

## 概要

このプロジェクトは、PythonとRubyで数千万件単位のデータをSQLデータベース（PostgreSQL）に挿入する際のパフォーマンスを比較するベンチマークです。

## 動機

大量のデータをデータベースに挿入する必要がある場合、適切なライブラリと手法を選択することで、パフォーマンスが10倍以上変わることがあります。このベンチマークは以下を明らかにします：

- Python vs Ruby でのバルクインサート性能
- 各言語での最適なライブラリと手法
- トレードオフ（速度 vs 使いやすさ vs 機能）

## テスト対象

### Python

1. **psycopg2 executemany** - 基本的なバッチインサート
2. **psycopg2 execute_batch** - 最適化されたバッチ実行
3. **psycopg2 execute_values** - VALUES構文での一括挿入
4. **psycopg2 COPY** - PostgreSQLのCOPYコマンド
5. **SQLAlchemy Core insert** - ORM Coreレベルのバッチ挿入
6. **pandas to_sql** - DataFrameからの直接挿入

### Ruby

1. **ActiveRecord create** - 個別レコード作成（ベースライン）
2. **ActiveRecord insert_all** - Rails 6+の標準バルク挿入
3. **activerecord-import** - 人気のバルクインサートgem
4. **activerecord-copy** - PostgreSQL COPYのActiveRecordラッパー
5. **Raw PG execute** - 生のPG gemでのバッチ実行
6. **Raw PG COPY** - 生のPG gemでのCOPY実行

## セットアップ

### 方法1: Docker使用（推奨）

#### 前提条件
- Docker & Docker Compose

#### 実行方法

```bash
# PostgreSQLとベンチマーク環境を起動
docker-compose up -d

# ベンチマークを実行（100万件）
docker-compose exec benchmark ./run_benchmarks_docker.sh 1000000

# または、10万件で素早くテスト
docker-compose exec benchmark ./run_benchmarks_docker.sh 100000

# 1000万件（時間がかかります）
docker-compose exec benchmark ./run_benchmarks_docker.sh 10000000

# 環境を停止
docker-compose down

# データも含めて完全削除
docker-compose down -v
```

#### 個別にベンチマークを実行

```bash
# Pythonのみ
docker-compose exec benchmark python3 python_benchmark.py 1000000

# Rubyのみ
docker-compose exec benchmark ruby ruby_benchmark.rb 1000000
```

### 方法2: ローカル環境

#### 前提条件
- PostgreSQL 12+
- Python 3.8+
- Ruby 3.0+
- Bundler

#### 1. PostgreSQLを起動

```bash
# Dockerを使用する場合
docker-compose up -d postgres

# またはローカルのPostgreSQLサービスを起動
```

#### 2. Python依存関係をインストール

```bash
pip install -r requirements.txt
```

#### 3. Ruby依存関係をインストール

```bash
bundle install
```

#### 4. ベンチマーク実行

```bash
# Pythonベンチマーク
python3 python_benchmark.py 1000000

# Rubyベンチマーク
ruby ruby_benchmark.rb 1000000
```

## ベンチマーク結果

### テスト環境

- CPU: (実行後に記載)
- メモリ: (実行後に記載)
- PostgreSQL: 16
- Python: 3.x
- Ruby: 3.x

### 100万件挿入

#### Python結果

(ベンチマーク実行後に記載)

#### Ruby結果

(ベンチマーク実行後に記載)

### 1000万件挿入

#### Python結果

(ベンチマーク実行後に記載)

#### Ruby結果

(ベンチマーク実行後に記載)

## 主な発見

### 文献調査からの予想

既存のベンチマーク調査から、以下のような結果が期待されます：

#### Python
- **COPY**: 最速 - 100万件を数秒で挿入可能（3.4M rows/min報告あり）
- **execute_values**: 2番目に高速 - COPYの60-80%の速度
- **execute_batch**: execute_valuesより若干遅い
- **executemany**: 基本手法の15倍以上遅い
- **SQLAlchemy**: バッチサイズ調整で実用的な速度
- **pandas**: 便利だがやや低速（1M件で約72秒の報告）

#### Ruby
- **COPY（activerecord-copy/Raw PG）**: 最速 - 100万件を約1.5分で挿入
- **activerecord-import**: 実用的 - 100万件を約5分で挿入（15倍高速化）
- **insert_all**: Rails標準で依存なし、importと同等の性能
- **Raw PG execute**: バッチサイズに依存
- **個別create**: 最も遅い - 100万件で1時間以上

### 言語間比較の予想
- PostgreSQLのCOPYを使用する限り、言語による性能差は小さい
- Pythonの方がライブラリの最適化が進んでいる可能性
- Rubyは使いやすさを重視したgemが多い

### 実測結果

(実際にベンチマーク実行後に記載)

## 推奨事項

### Pythonでの推奨

- **最速が必要**: `psycopg2`の`COPY`コマンドを使用
- **バランス重視**: `execute_values`が速度と使いやすさのバランスが良い
- **ORM必須**: SQLAlchemy Coreの`insert`をバッチサイズ指定で使用
- **データ分析**: pandasパイプラインなら`to_sql`が便利

### Rubyでの推奨

- **最速が必要**: `activerecord-copy`または`Raw PG COPY`を使用
- **バランス重視**: `activerecord-import`が最も人気で使いやすい
- **Rails標準**: Rails 6+なら依存なしで`insert_all`が使える
- **避けるべき**: 個別の`create`は大量データでは非常に遅い

## 結論

### 速度が最優先の場合
両言語とも**PostgreSQLのCOPYコマンド**を使用することで、圧倒的な性能を得られます。
- Python: `psycopg2`の`copy_from`
- Ruby: `activerecord-copy`または`pg`の`copy_data`

### 実用的なバランス
開発効率と性能のバランスを考慮する場合：
- Python: `execute_values` - シンプルで高速
- Ruby: `activerecord-import` - Rails開発者に馴染みやすく、十分に高速

### フレームワーク内での推奨
- **SQLAlchemy**: Core APIの`insert`をバッチで使用
- **Rails**: Rails 6+なら`insert_all`、それ以前なら`activerecord-import`

### 避けるべきパターン
- 個別の`INSERT`文を大量に実行
- トランザクション制御なし
- バッチサイズの調整なし

### パフォーマンスチューニングのポイント
1. **バッチサイズ**: 10,000件が一般的に最適
2. **トランザクション**: 大きなトランザクション単位でコミット
3. **インデックス**: 挿入前に削除、挿入後に再作成を検討
4. **接続プール**: 適切な接続数の設定
5. **PostgreSQL設定**: `shared_buffers`, `work_mem`等の最適化

## 参考資料

- [psycopg2 documentation](https://www.psycopg.org/)
- [SQLAlchemy documentation](https://www.sqlalchemy.org/)
- [activerecord-import](https://github.com/zdennis/activerecord-import)
- [activerecord-copy](https://github.com/NicholasTD07/activerecord-copy)
- [PostgreSQL COPY documentation](https://www.postgresql.org/docs/current/sql-copy.html)
