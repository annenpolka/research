#!/bin/bash

# SQLバルクインサートベンチマーク実行スクリプト（Docker内部用）

set -e

echo "================================================================================"
echo "SQLバルクインサートベンチマーク (Docker環境)"
echo "================================================================================"
echo ""

# コマンドライン引数から件数を取得（デフォルトは100万件）
NUM_RECORDS=${1:-1000000}

echo "テスト件数: $(echo $NUM_RECORDS | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')件"
echo ""

# PostgreSQL接続確認
echo "PostgreSQLの接続を確認中..."
until pg_isready -h $PGHOST -U $PGUSER -d $PGDATABASE &> /dev/null; do
    echo "  PostgreSQLの起動を待機中..."
    sleep 2
done
echo "PostgreSQL接続OK"
echo ""

# Pythonベンチマーク
echo "================================================================================"
echo "Pythonベンチマーク開始"
echo "================================================================================"
echo ""

python3 python_benchmark.py $NUM_RECORDS 2>&1 | tee results_python_${NUM_RECORDS}.txt

echo ""
echo ""

# Rubyベンチマーク
echo "================================================================================"
echo "Rubyベンチマーク開始"
echo "================================================================================"
echo ""

ruby ruby_benchmark.rb $NUM_RECORDS 2>&1 | tee results_ruby_${NUM_RECORDS}.txt

echo ""
echo ""
echo "================================================================================"
echo "ベンチマーク完了"
echo "================================================================================"
echo ""
echo "結果ファイル:"
echo "  - results_python_${NUM_RECORDS}.txt"
echo "  - results_ruby_${NUM_RECORDS}.txt"
echo ""
