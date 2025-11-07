#!/bin/bash
# プロジェクトを指定してvibe-kanbanを起動する便利スクリプト

set -e

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== vibe-kanban Project Launcher ===${NC}\n"

# 使用方法
usage() {
    echo "使用方法: $0 <project-path> [container-name]"
    echo ""
    echo "例:"
    echo "  $0 ~/projects/my-app"
    echo "  $0 /path/to/project my-vibe"
    echo "  $0 . current-project"
    exit 1
}

# 引数チェック
if [ $# -lt 1 ]; then
    usage
fi

PROJECT_PATH="$1"
CONTAINER_NAME="${2:-vibe-kanban}"

# プロジェクトパスの検証
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}エラー: プロジェクトディレクトリが見つかりません: $PROJECT_PATH${NC}"
    exit 1
fi

# 絶対パスに変換
PROJECT_PATH=$(cd "$PROJECT_PATH" && pwd)
PROJECT_NAME=$(basename "$PROJECT_PATH")

echo -e "${YELLOW}プロジェクト: ${NC}$PROJECT_PATH"
echo -e "${YELLOW}コンテナ名: ${NC}$CONTAINER_NAME"
echo -e "${YELLOW}マウント先: ${NC}/repos/$PROJECT_NAME"
echo ""

# 既存のコンテナをチェック
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}既存のコンテナが見つかりました。削除しますか? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        echo -e "${GREEN}✓ 既存のコンテナを削除しました${NC}\n"
    else
        echo -e "${RED}既存のコンテナが存在するため、終了します${NC}"
        exit 1
    fi
fi

# SSHエージェントの確認
if [ -z "$SSH_AUTH_SOCK" ]; then
    echo -e "${YELLOW}警告: SSH_AUTH_SOCKが設定されていません${NC}"
    echo -e "${YELLOW}SSH認証が必要な場合は、ssh-agentを起動してください:${NC}"
    echo "  eval \$(ssh-agent -s)"
    echo "  ssh-add ~/.ssh/id_rsa"
    echo ""
fi

# UID/GIDの取得
HOST_UID=$(id -u)
HOST_GID=$(id -g)

echo -e "${YELLOW}UID/GID: ${NC}${HOST_UID}:${HOST_GID}"
echo ""

# コンテナの起動
echo -e "${GREEN}コンテナを起動中...${NC}"

docker run -d \
  --name "$CONTAINER_NAME" \
  -p 3000:3000 \
  \
  `# プロジェクトのマウント` \
  -v "${PROJECT_PATH}:/repos/${PROJECT_NAME}:rw" \
  \
  `# SSH設定（読み取り専用）` \
  -v "${HOME}/.ssh/config:/home/appuser/.ssh/config:ro" \
  -v "${HOME}/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro" \
  \
  `# Git設定（読み取り専用）` \
  -v "${HOME}/.gitconfig:/home/appuser/.gitconfig:ro" \
  \
  `# SSHエージェント（利用可能な場合）` \
  ${SSH_AUTH_SOCK:+-v "${SSH_AUTH_SOCK}:/ssh-agent"} \
  ${SSH_AUTH_SOCK:+-e "SSH_AUTH_SOCK=/ssh-agent"} \
  \
  `# 環境変数` \
  -e "PORT=3000" \
  -e "HOST=0.0.0.0" \
  \
  `# ホストのUID/GIDを使用` \
  --user "${HOST_UID}:${HOST_GID}" \
  \
  `# セキュリティ設定` \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --pids-limit 200 \
  \
  `# リソース制限` \
  --memory="2g" \
  --cpus="2.0" \
  \
  `# 一時ファイル` \
  --tmpfs /tmp:size=200M,mode=1777 \
  \
  vibe-kanban:latest

# 起動確認
echo ""
echo -e "${GREEN}✓ コンテナが起動しました！${NC}"
echo ""

# ヘルスチェック待機
echo -e "${YELLOW}ヘルスチェックを待機中...${NC}"
sleep 5

for i in {1..12}; do
    if docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ ヘルスチェック成功${NC}"
        break
    elif [ $i -eq 12 ]; then
        echo -e "${YELLOW}⚠ ヘルスチェックがタイムアウトしました（コンテナは起動しています）${NC}"
    else
        echo -n "."
        sleep 5
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}vibe-kanbanが起動しました！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}アクセスURL:${NC} http://localhost:3000"
echo -e "${YELLOW}プロジェクト:${NC} /repos/${PROJECT_NAME}"
echo ""
echo -e "${YELLOW}便利なコマンド:${NC}"
echo "  ログを表示: docker logs -f $CONTAINER_NAME"
echo "  コンテナ内でシェルを起動: docker exec -it $CONTAINER_NAME sh"
echo "  停止: docker stop $CONTAINER_NAME"
echo "  削除: docker rm $CONTAINER_NAME"
echo "  停止＆削除: docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo ""
