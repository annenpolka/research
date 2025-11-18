#!/bin/bash
# クイックスタートスクリプト - 小規模なテストを実行

set -e

echo "========================================"
echo "SQL Bulk Insert - Quick Start Test"
echo "========================================"
echo ""

# Docker環境を起動
echo "Starting Docker environment..."
cd docker
docker-compose up -d
echo ""

echo "Waiting for databases..."
sleep 10

# PostgreSQL接続確認
until docker-compose exec -T postgres pg_isready -U benchmark > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
echo "✓ PostgreSQL is ready"

# MySQL接続確認
until docker-compose exec -T mysql mysqladmin ping -h localhost -u benchmark -pbenchmark --silent > /dev/null 2>&1; do
  echo "Waiting for MySQL..."
  sleep 2
done
echo "✓ MySQL is ready"
echo ""

cd ..

# Python環境のビルド
echo "Building Python environment..."
cd docker
docker-compose build python-bench
cd ..
echo ""

# 1つのクイックテストを実行（100万件のみ）
echo "Running quick test with psycopg2 (1M records)..."
docker-compose -f docker/docker-compose.yml exec -T python-bench python -c "
import sys
sys.path.insert(0, '/app')
from benchmark_psycopg2 import *
from benchmark_utils import BenchmarkRunner

runner = BenchmarkRunner(output_file='/results/quick_test_results.json')

# 100万件のみテスト
runner.run_benchmark('psycopg2_execute_values_1M', bench_execute_values, 1_000_000)
runner.run_benchmark('psycopg2_copy_from_1M', bench_copy_from, 1_000_000)

runner.save_results()
runner.print_summary()
"

echo ""
echo "========================================"
echo "Quick test completed!"
echo "========================================"
echo ""
echo "To run all benchmarks: ./run_all_benchmarks.sh"
echo "To stop Docker: cd docker && docker-compose down"
echo ""
