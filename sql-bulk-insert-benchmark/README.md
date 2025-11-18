# SQL Bulk Insert Performance Benchmark

## 概要

このプロジェクトは、数千万件単位のデータをSQLデータベースに登録する際のパフォーマンスを、PythonとRuby（Rails含む）で比較検証する研究です。

## 動機

大量データのバルクインサートは、データ移行、ETL処理、初期データロードなどで頻繁に必要とされます。言語やライブラリによってパフォーマンスが大きく異なるため、実測データに基づいた選択が重要です。

## 検証対象

### データベース
- PostgreSQL (latest)
- MySQL 8.0

### Python ライブラリ
1. **psycopg2** - PostgreSQL用の最も一般的なアダプタ
   - `execute_values()` - 高速なバッチインサート
   - `execute_batch()` - ラウンドトリップを削減
   - `copy_from()` - COPY コマンドを使用（最速）

2. **psycopg3** - 次世代PostgreSQLアダプタ
   - Pipeline mode - 非同期処理による高速化

3. **SQLAlchemy** - ORMフレームワーク
   - `bulk_insert_mappings()` - バルクインサート
   - Core API による直接挿入

4. **PyMySQL/MySQLdb** - MySQL用アダプタ
   - `executemany()` - バッチインサート
   - LOAD DATA INFILE

### Ruby ライブラリ
1. **activerecord-import** - 最も人気のあるバルクインサートgem
   - PostgreSQL, MySQL対応
   - ON CONFLICT/ON DUPLICATE KEY UPDATE サポート

2. **Rails 6+ native methods**
   - `insert_all` - バルクインサート
   - `upsert_all` - アップサート

3. **activerecord-copy** - PostgreSQL COPY専用
   - 最速のデータロード方法

4. **pg gem (raw)** - 生のPostgreSQL操作
   - COPYコマンド直接実行

5. **mysql2 gem (raw)** - 生のMySQL操作
   - バッチ挿入

## ベンチマーク設定

### データ規模
- 100万件（ウォームアップ）
- 1000万件
- 3000万件

### テストシナリオ
1. **シンプルなテーブル** - 5カラム（ID, 文字列x2, 数値x2）
2. **複雑なテーブル** - 15カラム（様々なデータ型）
3. **インデックスあり/なし**

### 測定項目
- 挿入時間（秒）
- スループット（行/秒）
- メモリ使用量
- CPU使用率

## 環境

- Docker Compose による統一環境
- PostgreSQL 16
- MySQL 8.0
- Python 3.12
- Ruby 3.3
- Rails 7.1

## プロジェクト構成

```
sql-bulk-insert-benchmark/
├── docker/
│   ├── docker-compose.yml
│   ├── postgres/
│   └── mysql/
├── python/
│   ├── requirements.txt
│   ├── benchmark_psycopg2.py
│   ├── benchmark_psycopg3.py
│   ├── benchmark_sqlalchemy.py
│   └── benchmark_mysql.py
├── ruby/
│   ├── Gemfile
│   ├── benchmark_activerecord_import.rb
│   ├── benchmark_pg_copy.rb
│   └── benchmark_mysql.rb
├── rails/
│   └── (Rails application for testing)
├── results/
│   └── benchmark_results.json
└── README.md
```

## 実行方法

### クイックスタート

```bash
# 簡単なテストを実行
./quick_start.sh

# すべてのベンチマークを実行
./run_all_benchmarks.sh

# 結果を分析
python3 analyze_results.py
```

### 個別実行

詳細な実行方法は [USAGE.md](USAGE.md) を参照してください。

```bash
# Docker環境の起動
cd docker
docker compose up -d

# Pythonベンチマーク
docker compose exec python-bench python /app/benchmark_psycopg2.py
docker compose exec python-bench python /app/benchmark_psycopg3.py
docker compose exec python-bench python /app/benchmark_sqlalchemy.py
docker compose exec python-bench python /app/benchmark_mysql.py

# Rubyベンチマーク
docker compose exec ruby-bench ruby /app/benchmark_activerecord.rb
docker compose exec ruby-bench ruby /app/benchmark_pg_copy.rb
docker compose exec ruby-bench ruby /app/benchmark_mysql.rb
```

## 期待される結果

### PostgreSQL - 予想パフォーマンスランキング

1. **COPY FROM (最速)** - 500,000+ records/sec
   - Python: `psycopg2.copy_from()`, `psycopg3.copy()`
   - Ruby: `activerecord-copy`, `pg.copy_data`

2. **execute_values / bulk methods** - 100,000-300,000 records/sec
   - Python: `psycopg2.extras.execute_values()`
   - Ruby: `activerecord-import`, `insert_all`

3. **execute_batch** - 50,000-150,000 records/sec
   - Python: `psycopg2.extras.execute_batch()`
   - Ruby: バッチ化された `insert_all`

4. **ORM標準メソッド（遅い）** - 1,000-10,000 records/sec
   - Python: `session.add()` 個別
   - Ruby: `create()` 個別

### MySQL - 予想パフォーマンスランキング

1. **LOAD DATA INFILE (最速)** - 400,000+ records/sec
   - Python: `LOAD DATA LOCAL INFILE`

2. **Multi-row INSERT** - 80,000-200,000 records/sec
   - Python: `executemany()` バッチ化
   - Ruby: `activerecord-import`, `insert_all`

3. **Prepared statements** - 30,000-80,000 records/sec
   - バッチ化された INSERT

### ベストプラクティスまとめ

#### 最速を求める場合
- PostgreSQL: **COPY コマンド**を使用
- MySQL: **LOAD DATA INFILE** を使用
- ただし、データをファイル形式に変換する必要がある

#### 実用性とのバランス
- PostgreSQL: `psycopg2.extras.execute_values()` または `activerecord-import`
- MySQL: バッチ化された `executemany()` または `activerecord-import`
- ORMとの統合が容易で、十分高速

#### ORM使用時
- Python: `SQLAlchemy.bulk_insert_mappings()`
- Ruby: `insert_all` (Rails 6+) または `activerecord-import` gem
- バリデーションをスキップしてパフォーマンス向上

### 主要な知見

1. **バッチサイズが重要**: 1,000-10,000 件が最適
2. **トランザクション制御**: 大きなトランザクションほど高速だが、リスクも増加
3. **インデックス**: 挿入前に無効化、挿入後に再構築が効果的
4. **COPY/LOAD DATA**: 圧倒的に高速だが、柔軟性は低い
5. **言語差は小さい**: ライブラリの選択の方が重要

## 結果ファイル

ベンチマーク結果は `results/` ディレクトリに保存されます：

- `python_psycopg2_results.json` - psycopg2 ベンチマーク
- `python_psycopg3_results.json` - psycopg3 ベンチマーク
- `python_sqlalchemy_results.json` - SQLAlchemy ベンチマーク
- `python_mysql_results.json` - Python MySQL ベンチマーク
- `ruby_activerecord_results.json` - ActiveRecord ベンチマーク
- `ruby_pg_copy_results.json` - PostgreSQL COPY ベンチマーク
- `ruby_mysql_results.json` - Ruby MySQL ベンチマーク

分析スクリプトを実行すると、`BENCHMARK_RESULTS.md` に詳細なレポートが生成されます。

## 制限事項と注意点

- このベンチマークは **単一スレッド** での実行を想定
- **ネットワークレイテンシ** は考慮していない（同一ホスト想定）
- **本番環境** では追加のチューニングが必要
- 結果は **ハードウェアに依存** します

## 参考文献

- [Psycopg2 Bulk Insert Performance](https://naysan.ca/2020/05/09/pandas-to-postgresql-using-psycopg2-bulk-insert-performance-benchmark/)
- [activerecord-import GitHub](https://github.com/zdennis/activerecord-import)
- [Rails 6 insert_all/upsert_all](https://blog.saeloun.com/2022/07/26/rails-6-insert-all/)
- [Fastest Way to Import Data into Postgres with Rails](https://pganalyze.com/blog/fastest-way-importing-data-into-postgres-with-ruby-rails)
