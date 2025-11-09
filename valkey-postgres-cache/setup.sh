#!/bin/bash
# Valkey + PostgreSQL キャッシュシステムのセットアップスクリプト

set -e

echo "=========================================="
echo "Valkey + PostgreSQL セットアップ"
echo "=========================================="
echo ""

# Docker Composeの起動
echo "📦 Dockerコンテナを起動中..."
docker compose up -d

echo ""
echo "⏳ サービスの起動を待機中..."
sleep 5

# ヘルスチェック
echo ""
echo "🔍 サービスのヘルスチェック..."

# Valkeyのチェック
if docker compose exec -T valkey valkey-cli ping > /dev/null 2>&1; then
    echo "✓ Valkey: 起動完了"
else
    echo "✗ Valkey: 起動失敗"
    exit 1
fi

# PostgreSQLのチェック
if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✓ PostgreSQL: 起動完了"
else
    echo "✗ PostgreSQL: 起動失敗"
    exit 1
fi

echo ""
echo "✅ セットアップ完了!"
echo ""
echo "次のコマンドでデモを実行できます:"
echo "  python main.py"
echo ""
echo "サービスの状態確認:"
echo "  docker compose ps"
echo ""
echo "ログの確認:"
echo "  docker compose logs -f"
echo ""
echo "停止する場合:"
echo "  docker compose down"
echo ""
