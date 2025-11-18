#!/bin/bash
# すべてのベンチマークを実行するマスタースクリプト

set -e

echo "========================================"
echo "SQL Bulk Insert Benchmark Suite"
echo "========================================"
echo ""

# 色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Docker Composeで環境を起動
echo -e "${BLUE}Starting Docker environment...${NC}"
cd docker
docker-compose up -d
echo -e "${GREEN}✓ Docker containers started${NC}"
echo ""

# データベースが起動するまで待機
echo -e "${BLUE}Waiting for databases to be ready...${NC}"
sleep 10

# PostgreSQL接続確認
until docker-compose exec -T postgres pg_isready -U benchmark > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# MySQL接続確認
until docker-compose exec -T mysql mysqladmin ping -h localhost -u benchmark -pbenchmark --silent > /dev/null 2>&1; do
  echo "Waiting for MySQL..."
  sleep 2
done
echo -e "${GREEN}✓ MySQL is ready${NC}"
echo ""

cd ..

# ========================================
# Python ベンチマーク
# ========================================
echo -e "${BLUE}========================================"
echo "Running Python Benchmarks"
echo "========================================${NC}"
echo ""

# Python環境のビルドと実行
echo -e "${BLUE}Building Python environment...${NC}"
cd docker
docker-compose build python-bench
cd ..

echo -e "${BLUE}Running psycopg2 benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T python-bench python /app/benchmark_psycopg2.py || echo -e "${RED}✗ psycopg2 benchmark failed${NC}"
echo ""

echo -e "${BLUE}Running psycopg3 benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T python-bench python /app/benchmark_psycopg3.py || echo -e "${RED}✗ psycopg3 benchmark failed${NC}"
echo ""

echo -e "${BLUE}Running SQLAlchemy benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T python-bench python /app/benchmark_sqlalchemy.py || echo -e "${RED}✗ SQLAlchemy benchmark failed${NC}"
echo ""

echo -e "${BLUE}Running MySQL Python benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T python-bench python /app/benchmark_mysql.py || echo -e "${RED}✗ MySQL Python benchmark failed${NC}"
echo ""

# ========================================
# Ruby ベンチマーク
# ========================================
echo -e "${BLUE}========================================"
echo "Running Ruby Benchmarks"
echo "========================================${NC}"
echo ""

# Ruby環境のビルドと実行
echo -e "${BLUE}Building Ruby environment...${NC}"
cd docker
docker-compose build ruby-bench
cd ..

echo -e "${BLUE}Running ActiveRecord benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T ruby-bench ruby /app/benchmark_activerecord.rb || echo -e "${RED}✗ ActiveRecord benchmark failed${NC}"
echo ""

echo -e "${BLUE}Running PostgreSQL COPY benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T ruby-bench ruby /app/benchmark_pg_copy.rb || echo -e "${RED}✗ PG COPY benchmark failed${NC}"
echo ""

echo -e "${BLUE}Running MySQL Ruby benchmark...${NC}"
docker-compose -f docker/docker-compose.yml exec -T ruby-bench ruby /app/benchmark_mysql.rb || echo -e "${RED}✗ MySQL Ruby benchmark failed${NC}"
echo ""

# ========================================
# 結果の集計
# ========================================
echo -e "${GREEN}========================================"
echo "All Benchmarks Completed!"
echo "========================================${NC}"
echo ""
echo "Results have been saved to the 'results/' directory"
echo ""
echo "To view results:"
echo "  - Python psycopg2: results/python_psycopg2_results.json"
echo "  - Python psycopg3: results/python_psycopg3_results.json"
echo "  - Python SQLAlchemy: results/python_sqlalchemy_results.json"
echo "  - Python MySQL: results/python_mysql_results.json"
echo "  - Ruby ActiveRecord: results/ruby_activerecord_results.json"
echo "  - Ruby PG COPY: results/ruby_pg_copy_results.json"
echo "  - Ruby MySQL: results/ruby_mysql_results.json"
echo ""
echo "To stop the Docker environment:"
echo "  cd docker && docker-compose down"
echo ""
