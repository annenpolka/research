# Valkey & PostgreSQL 二層キャッシュシステム

## 概要

このプロジェクトは、Valkey（Redisフォーク）をキャッシュ層、PostgreSQLを永続化層として使用する二層キャッシュアーキテクチャのサンプル実装です。アプリケーションパラメータの効率的な管理と高速アクセスを実現します。

## 動機

- **パフォーマンス**: 頻繁にアクセスされるパラメータをメモリキャッシュに保存し、データベースアクセスを削減
- **スケーラビリティ**: キャッシュ層により、データベースへの負荷を軽減
- **一貫性**: PostgreSQLによる永続化とACIDプロパティの保証
- **可用性**: Valkeyの高速な読み取りとPostgreSQLの信頼性を組み合わせ

## アーキテクチャ

```
┌─────────────┐
│ Application │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
┌──────▼─────┐ ┌────▼────────┐
│   Valkey   │ │ PostgreSQL  │
│  (Cache)   │ │ (Database)  │
└────────────┘ └─────────────┘
```

### データフロー

1. **読み取り (READ)**:
   - まずValkeyキャッシュをチェック
   - キャッシュヒット: Valkeyから値を返す
   - キャッシュミス: PostgreSQLから読み取り → Valkeyにキャッシュ → 値を返す

2. **書き込み (WRITE)**:
   - PostgreSQLに書き込み
   - 成功したらValkeyキャッシュを更新
   - Write-Through戦略を採用

3. **削除 (DELETE)**:
   - PostgreSQLから削除
   - Valkeyキャッシュも削除

## 機能

- パラメータのCRUD操作
- 自動キャッシュ管理（TTL設定可能）
- キャッシュヒット率の追跡
- エラーハンドリングとフォールバック
- 型安全なパラメータ管理

## 技術スタック

- **Valkey**: 7.2 (インメモリキャッシュ)
- **PostgreSQL**: 16 (リレーショナルデータベース)
- **Python**: 3.11+ (アプリケーション層)
- **Docker Compose**: インフラストラクチャ管理

## 使い方

### 1. 環境のセットアップ

```bash
# Dockerコンテナの起動
docker compose up -d

# 依存関係のインストール
pip install -r requirements.txt

# データベースの初期化
python init_db.py
```

### 2. サンプルの実行

```bash
# パラメータキャッシュのデモ
python main.py
```

### 3. 動作確認

```bash
# Valkeyキャッシュの確認
docker compose exec valkey valkey-cli keys "*"

# PostgreSQLデータの確認
docker compose exec postgres psql -U postgres -d params_db -c "SELECT * FROM parameters;"
```

## 主要な実装

### パラメータマネージャー

```python
class ParameterCache:
    """Valkey + PostgreSQL 二層キャッシュ"""

    def get(self, key: str) -> Optional[str]:
        # 1. Valkeyキャッシュをチェック
        # 2. キャッシュミス時はPostgreSQLから読み取り
        # 3. 結果をキャッシュに保存

    def set(self, key: str, value: str, ttl: int = 3600):
        # 1. PostgreSQLに書き込み
        # 2. Valkeyキャッシュを更新

    def delete(self, key: str):
        # 両方から削除
```

## パフォーマンス特性

| 操作 | キャッシュヒット | キャッシュミス |
|------|----------------|--------------|
| 読み取り | ~0.1ms (Valkey) | ~5-10ms (Postgres + Valkey) |
| 書き込み | ~5-10ms (Postgres + Valkey) | - |
| 削除 | ~5-10ms (両方) | - |

## ベストプラクティス

1. **TTL設定**: データの更新頻度に応じて適切なTTLを設定
2. **キー命名**: 名前空間を使用（例: `app:config:max_users`）
3. **エラーハンドリング**: Valkeyダウン時はPostgreSQLにフォールバック
4. **監視**: キャッシュヒット率を監視し、最適化

## 制限事項

- 実験的なサンプル実装
- 本番環境での使用前に追加の検証が必要
- 大規模データセットでのスケーラビリティテストは未実施

## 今後の改善

- [ ] キャッシュウォーミング戦略
- [ ] 複数のキャッシュ戦略のサポート（LRU, LFU）
- [ ] 分散キャッシュの無効化
- [ ] メトリクス収集とダッシュボード
- [ ] ベンチマークツールの追加

## ライセンス

MIT License - 実験・学習目的
