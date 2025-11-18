#!/bin/bash

# SQLバルクインサートベンチマーク実行スクリプト

set -e

echo "================================================================================"
echo "SQLバルクインサートベンチマーク"
echo "================================================================================"
echo ""

# コマンドライン引数から件数を取得（デフォルトは100万件）
NUM_RECORDS=${1:-1000000}

echo "テスト件数: $(echo $NUM_RECORDS | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')件"
echo ""

# PostgreSQLが起動しているか確認
echo "PostgreSQLの接続を確認中..."
if ! docker-compose ps | grep -q "Up"; then
    echo "PostgreSQLを起動中..."
    docker-compose up -d
    echo "PostgreSQLの起動を待機中..."
    sleep 5
fi

echo "PostgreSQL接続OK"
echo ""

# Pythonベンチマーク
echo "================================================================================"
echo "Pythonベンチマーク開始"
echo "================================================================================"
echo ""

if command -v python3 &> /dev/null; then
    python3 python_benchmark.py $NUM_RECORDS 2>&1 | tee results_python_${NUM_RECORDS}.txt
else
    echo "Python3が見つかりません。Pythonベンチマークをスキップします。"
fi

echo ""
echo ""

# Rubyベンチマーク
echo "================================================================================"
echo "Rubyベンチマーク開始"
echo "================================================================================"
echo ""

if command -v ruby &> /dev/null; then
    ruby ruby_benchmark.rb $NUM_RECORDS 2>&1 | tee results_ruby_${NUM_RECORDS}.txt
else
    echo "Rubyが見つかりません。Rubyベンチマークをスキップします。"
fi

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
