# クイックスタートガイド

## 前提条件

- Docker & Docker Compose がインストールされていること
- Python 3.11+ がインストールされていること

## 5分で始める

### 1. セットアップ

```bash
# リポジトリに移動
cd valkey-postgres-cache

# セットアップスクリプトを実行
./setup.sh
```

### 2. Pythonパッケージのインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. デモの実行

```bash
python main.py
```

## 何が起きているか？

デモアプリケーションは以下を実演します：

1. **基本操作**: パラメータの読み取り、書き込み
2. **キャッシュパフォーマンス**: 初回アクセス vs キャッシュヒット時の速度比較
3. **カテゴリ別クエリ**: パラメータのグループ化と検索
4. **更新と削除**: データの変更管理
5. **TTL（有効期限）**: キャッシュの自動失効

## アーキテクチャの確認

### Valkeyのデータを確認

```bash
# Valkeyに接続
docker compose exec valkey valkey-cli

# すべてのキーを表示
KEYS *

# 特定のキーの値を取得
GET param:app.max_connections

# TTLを確認
TTL param:app.max_connections
```

### PostgreSQLのデータを確認

```bash
# PostgreSQLに接続
docker compose exec postgres psql -U postgres -d params_db

# すべてのパラメータを表示
SELECT * FROM parameters;

# カテゴリ別の統計
SELECT * FROM parameter_stats;

# 終了
\q
```

## カスタマイズ

### パラメータの追加

```python
from parameter_cache import ParameterCache

with ParameterCache() as cache:
    cache.set(
        key="my_app.custom_setting",
        value="my_value",
        description="カスタム設定",
        category="custom",
        ttl=7200  # 2時間
    )
```

### 接続設定の変更

`parameter_cache.py` の `ParameterCache` 初期化時に設定を渡します：

```python
cache = ParameterCache(
    redis_host="localhost",
    redis_port=6379,
    postgres_host="localhost",
    postgres_port=5432,
    default_ttl=3600  # デフォルトTTL: 1時間
)
```

## トラブルシューティング

### Dockerコンテナが起動しない

```bash
# ログを確認
docker compose logs

# コンテナを再起動
docker compose down
docker compose up -d
```

### 接続エラー

```bash
# サービスの状態を確認
docker compose ps

# ポートが使用されているか確認
lsof -i :6379  # Valkey
lsof -i :5432  # PostgreSQL
```

### Pythonパッケージのエラー

```bash
# 依存関係を再インストール
pip install --upgrade -r requirements.txt
```

## 次のステップ

- `parameter_cache.py` のコードを読んでキャッシュロジックを理解する
- `main.py` を参考に独自のユースケースを実装する
- パフォーマンステストを実施してキャッシュの効果を測定する
- 本番環境向けの設定（レプリケーション、セキュリティ）を検討する

## クリーンアップ

```bash
# コンテナとボリュームを削除
docker compose down -v
```
