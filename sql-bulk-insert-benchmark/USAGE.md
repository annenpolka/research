# 使用方法ガイド

## 必要な環境

- Docker & Docker Compose
- 最低4GBのメモリ
- 10GB以上のディスク空き容量

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd sql-bulk-insert-benchmark
```

### 2. クイックテストの実行（推奨）

まずは小規模なテストで動作を確認：

```bash
./quick_start.sh
```

このスクリプトは：
- Docker環境を起動
- PostgreSQLとMySQLの準備
- 100万件のサンプルベンチマークを実行

### 3. 全ベンチマークの実行

```bash
./run_all_benchmarks.sh
```

実行時間の目安：
- 100万件テスト: 約10-20分
- 1000万件テスト: 約1-3時間
- 3000万件テスト: 数時間

## 個別のベンチマーク実行

### Python - PostgreSQL (psycopg2)

```bash
cd docker
docker compose up -d
docker compose exec python-bench python /app/benchmark_psycopg2.py
```

### Python - PostgreSQL (psycopg3)

```bash
docker compose exec python-bench python /app/benchmark_psycopg3.py
```

### Python - PostgreSQL (SQLAlchemy)

```bash
docker compose exec python-bench python /app/benchmark_sqlalchemy.py
```

### Python - MySQL

```bash
docker compose exec python-bench python /app/benchmark_mysql.py
```

### Ruby - ActiveRecord (PostgreSQL)

```bash
docker compose exec ruby-bench ruby /app/benchmark_activerecord.rb
```

### Ruby - PostgreSQL COPY

```bash
docker compose exec ruby-bench ruby /app/benchmark_pg_copy.rb
```

### Ruby - MySQL

```bash
docker compose exec ruby-bench ruby /app/benchmark_mysql.rb
```

## ベンチマーク結果の確認

### 結果ファイル

すべての結果は `results/` ディレクトリに JSON 形式で保存されます：

```
results/
├── python_psycopg2_results.json
├── python_psycopg3_results.json
├── python_sqlalchemy_results.json
├── python_mysql_results.json
├── ruby_activerecord_results.json
├── ruby_pg_copy_results.json
└── ruby_mysql_results.json
```

### 結果の分析

分析スクリプトを実行：

```bash
python3 analyze_results.py
```

これにより以下が生成されます：
- コンソールに詳細な分析結果を表示
- `BENCHMARK_RESULTS.md` にMarkdown形式のレポート

### 手動での結果確認

```bash
# トップ10のパフォーマンスを確認
cat results/python_psycopg2_results.json | python3 -m json.tool | grep -A5 "records_per_second"

# すべての結果をまとめて確認
cat results/*.json | python3 -m json.tool
```

## カスタマイズ

### テストデータ量の変更

各ベンチマークスクリプトの `test_sizes` 配列を編集：

```python
# Python
test_sizes = [
    100_000,      # 10万件
    1_000_000,    # 100万件
    10_000_000,   # 1000万件
    30_000_000,   # 3000万件（大規模テスト）
]
```

```ruby
# Ruby
test_sizes = [
  100_000,
  1_000_000,
  10_000_000,
]
```

### バッチサイズの調整

各ベンチマーク関数のパラメータを変更：

```python
# Python例
def bench_execute_values(record_count: int, page_size: int = 1000):
    # page_sizeを変更してテスト
```

```ruby
# Ruby例
def bench_insert_all_batched(record_count, batch_size: 1000)
  # batch_sizeを変更してテスト
end
```

### データベース設定の調整

`docker/docker-compose.yml` を編集：

```yaml
# PostgreSQL設定例
postgres:
  command:
    - postgres
    - -c
    - shared_buffers=512MB  # メモリ設定を調整
    - -c
    - work_mem=32MB
```

## トラブルシューティング

### Docker環境が起動しない

```bash
# ログを確認
cd docker
docker compose logs

# コンテナの状態を確認
docker compose ps

# 完全にリセット
docker compose down -v
docker compose up -d
```

### データベース接続エラー

```bash
# PostgreSQL接続確認
docker compose exec postgres pg_isready -U benchmark

# MySQL接続確認
docker compose exec mysql mysqladmin ping -h localhost -u benchmark -pbenchmark
```

### メモリ不足エラー

テストサイズを減らすか、Docker のメモリ設定を増やしてください：

Docker Desktop → Settings → Resources → Memory を 4GB 以上に設定

### 結果ファイルが生成されない

```bash
# resultsディレクトリの権限を確認
ls -la results/

# 手動で作成
mkdir -p results
chmod 777 results
```

## パフォーマンスチューニングのヒント

### PostgreSQL

1. **COPY コマンドを使用** - 最速の方法
2. **execute_values を使用** - バランスの良い方法
3. **トランザクションをまとめる** - コミット頻度を減らす
4. **インデックスを一時的に無効化** - 大量挿入時

### MySQL

1. **LOAD DATA INFILE を使用** - 最速の方法
2. **Multi-row INSERT を使用** - 複数行を1つのINSERTで
3. **innodb_flush_log_at_trx_commit=2** - パフォーマンス優先設定
4. **DISABLE KEYS** - インデックス更新を延期

### 一般的なヒント

1. **バッチサイズの最適化** - 通常1000-10000が最適
2. **バリデーションをスキップ** - 信頼できるデータの場合
3. **並列処理** - 複数のワーカーで分割挿入
4. **一時的にfsync無効化** - 危険だが高速（本番非推奨）

## ベンチマーク後のクリーンアップ

```bash
# Docker環境を停止
cd docker
docker compose down

# データも含めて完全に削除
docker compose down -v

# Docker イメージも削除
docker compose down --rmi all -v
```

## よくある質問

### Q: 本番環境で最速の方法は？

A: PostgreSQLの場合は `COPY`、MySQLの場合は `LOAD DATA INFILE` が最速ですが、
実用性を考慮すると Python の `psycopg2.extras.execute_values` や
Ruby の `activerecord-import` が良いバランスです。

### Q: ORMを使いつつ高速化するには？

A: SQLAlchemy の `bulk_insert_mappings` や Rails の `insert_all` /
`activerecord-import` gem を使用してください。

### Q: トランザクション安全性とパフォーマンスのバランスは？

A: バッチサイズを調整してください。1000-5000件ごとにコミットするのが
一般的なバランスポイントです。

### Q: 他のデータベース（SQLite、SQL Server等）も追加できる？

A: はい。`docker-compose.yml` に新しいサービスを追加し、
対応するベンチマークスクリプトを作成してください。

## 貢献

バグ報告や機能要望は Issue でお願いします。
プルリクエストも歓迎します。

## ライセンス

このベンチマークプロジェクトはMITライセンスです。
