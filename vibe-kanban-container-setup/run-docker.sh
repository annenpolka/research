#!/bin/bash
# vibe-kanbanをDockerで実行するスクリプト

set -e

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== vibe-kanban Docker実行スクリプト ===${NC}\n"

# オプション解析
MODE="${1:-basic}"

case "$MODE" in
  basic)
    echo -e "${YELLOW}基本モードで実行します${NC}"

    # Dockerイメージの確認
    if ! docker image inspect vibe-kanban:latest >/dev/null 2>&1; then
      echo "リポジトリのクローン..."
      if [ ! -d "vibe-kanban" ]; then
        if ! git clone https://github.com/BloopAI/vibe-kanban.git; then
          echo -e "${RED}❌ エラー: リポジトリのクローンに失敗しました${NC}"
          exit 1
        fi
      fi
      cd vibe-kanban

      echo -e "\n${YELLOW}Dockerイメージをビルド中...${NC}"
      if ! docker build -t vibe-kanban:latest .; then
        echo -e "${RED}❌ エラー: Dockerイメージのビルドに失敗しました${NC}"
        exit 1
      fi
    else
      echo -e "${GREEN}✓ vibe-kanban:latestイメージが見つかりました${NC}"
    fi

    echo -e "\n${YELLOW}コンテナを起動中...${NC}"
    docker run -d \
      --name vibe-kanban \
      -p 3000:3000 \
      vibe-kanban:latest

    echo -e "\n${GREEN}✓ vibe-kanbanが起動しました！${NC}"
    echo "アクセスURL: http://localhost:3000"
    ;;

  secure)
    echo -e "${YELLOW}セキュアモードで実行します${NC}"

    # Dockerイメージの確認
    if ! docker image inspect vibe-kanban:latest >/dev/null 2>&1; then
      echo "リポジトリのクローン..."
      if [ ! -d "vibe-kanban" ]; then
        if ! git clone https://github.com/BloopAI/vibe-kanban.git; then
          echo -e "${RED}❌ エラー: リポジトリのクローンに失敗しました${NC}"
          exit 1
        fi
      fi
      cd vibe-kanban

      echo -e "\n${YELLOW}Dockerイメージをビルド中...${NC}"
      if ! docker build -t vibe-kanban:latest .; then
        echo -e "${RED}❌ エラー: Dockerイメージのビルドに失敗しました${NC}"
        exit 1
      fi
    else
      echo -e "${GREEN}✓ vibe-kanban:latestイメージが見つかりました${NC}"
    fi

    echo -e "\n${YELLOW}セキュアな設定でコンテナを起動中...${NC}"
    docker run -d \
      --name vibe-kanban-secure \
      -p 3000:3000 \
      --read-only \
      --tmpfs /tmp:size=100M,mode=1777 \
      --tmpfs /repos:size=500M,mode=1777 \
      --cap-drop=ALL \
      --security-opt=no-new-privileges:true \
      --pids-limit 100 \
      --memory="512m" \
      --cpus="1.0" \
      vibe-kanban:latest

    echo -e "\n${GREEN}✓ vibe-kanban（セキュアモード）が起動しました！${NC}"
    echo "アクセスURL: http://localhost:3000"
    ;;

  compose)
    echo -e "${YELLOW}Docker Composeで実行します${NC}"
    if [ ! -f "../docker-compose.yml" ]; then
      echo -e "${RED}エラー: docker-compose.ymlが見つかりません${NC}"
      exit 1
    fi

    echo -e "\n${YELLOW}Docker Composeでコンテナを起動中...${NC}"
    cd ..
    docker-compose up -d

    echo -e "\n${GREEN}✓ vibe-kanban（Docker Compose）が起動しました！${NC}"
    echo "アクセスURL: http://localhost:3000"
    ;;

  hardened)
    echo -e "${YELLOW}強化版Dockerfileで実行します${NC}"

    if [ ! -f "../Dockerfile.hardened" ]; then
      echo -e "${RED}❌ エラー: Dockerfile.hardenedが見つかりません${NC}"
      echo "   vibe-kanban-container-setupディレクトリで実行してください"
      exit 1
    fi

    # Dockerイメージの確認
    if ! docker image inspect vibe-kanban:hardened >/dev/null 2>&1; then
      echo "リポジトリのクローン..."
      if [ ! -d "vibe-kanban" ]; then
        if ! git clone https://github.com/BloopAI/vibe-kanban.git; then
          echo -e "${RED}❌ エラー: リポジトリのクローンに失敗しました${NC}"
          exit 1
        fi
      fi
      cd vibe-kanban

      echo -e "\n${YELLOW}強化版Dockerイメージをビルド中...${NC}"
      if ! docker build -f ../Dockerfile.hardened -t vibe-kanban:hardened .; then
        echo -e "${RED}❌ エラー: Dockerイメージのビルドに失敗しました${NC}"
        exit 1
      fi
    else
      echo -e "${GREEN}✓ vibe-kanban:hardenedイメージが見つかりました${NC}"
    fi

    echo -e "\n${YELLOW}強化版コンテナを起動中...${NC}"
    docker run -d \
      --name vibe-kanban-hardened \
      -p 3000:3000 \
      --read-only \
      --tmpfs /tmp:size=100M,mode=1777 \
      --tmpfs /repos:size=500M,mode=1777 \
      --cap-drop=ALL \
      --security-opt=no-new-privileges:true \
      --pids-limit 100 \
      --memory="512m" \
      --cpus="1.0" \
      vibe-kanban:hardened

    echo -e "\n${GREEN}✓ vibe-kanban（強化版）が起動しました！${NC}"
    echo "アクセスURL: http://localhost:3000"
    ;;

  stop)
    echo -e "${YELLOW}コンテナを停止しています...${NC}"
    docker stop vibe-kanban vibe-kanban-secure vibe-kanban-hardened 2>/dev/null || true
    docker rm vibe-kanban vibe-kanban-secure vibe-kanban-hardened 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    echo -e "${GREEN}✓ コンテナを停止しました${NC}"
    ;;

  logs)
    echo -e "${YELLOW}コンテナのログを表示します${NC}"
    CONTAINER=$(docker ps -q -f name=vibe-kanban | head -n 1)
    if [ -z "$CONTAINER" ]; then
      echo -e "${RED}エラー: 実行中のvibe-kanbanコンテナが見つかりません${NC}"
      exit 1
    fi
    docker logs -f "$CONTAINER"
    ;;

  status)
    echo -e "${YELLOW}コンテナの状態を確認します${NC}\n"
    docker ps -a -f name=vibe-kanban
    echo ""

    CONTAINER=$(docker ps -q -f name=vibe-kanban | head -n 1)
    if [ -n "$CONTAINER" ]; then
      echo -e "${YELLOW}ヘルスステータス:${NC}"
      docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "ヘルスチェックなし"
    fi
    ;;

  *)
    echo -e "${RED}エラー: 不明なモード '$MODE'${NC}\n"
    echo "使用方法: $0 [mode]"
    echo ""
    echo "利用可能なモード:"
    echo "  basic     - 基本的なDocker実行（デフォルト）"
    echo "  secure    - セキュリティ強化版で実行"
    echo "  compose   - Docker Composeで実行"
    echo "  hardened  - 強化版Dockerfileで実行"
    echo "  stop      - すべてのコンテナを停止"
    echo "  logs      - コンテナのログを表示"
    echo "  status    - コンテナの状態を確認"
    exit 1
    ;;
esac

echo -e "\n${YELLOW}ヒント:${NC}"
echo "  状態確認: $0 status"
echo "  ログ表示: $0 logs"
echo "  停止: $0 stop"
