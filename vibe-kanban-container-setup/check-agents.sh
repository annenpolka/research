#!/bin/bash
# コーディングエージェントの設定を確認するスクリプト

set -e

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== vibe-kanban Coding Agents Configuration Checker ===${NC}\n"

# コンテナ名の取得
CONTAINER_NAME="${1:-vibe-kanban}"

# コンテナの存在確認
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}エラー: コンテナ '${CONTAINER_NAME}' が実行されていません${NC}"
    echo "使用方法: $0 [container-name]"
    exit 1
fi

echo -e "${YELLOW}対象コンテナ: ${CONTAINER_NAME}${NC}\n"

# ===========================
# エージェント設定チェック
# ===========================

check_passed=0
check_failed=0
check_warning=0

check_agent() {
    local agent_name=$1
    local env_var=$2
    local optional=${3:-false}

    echo -e "${BLUE}[チェック] $agent_name${NC}"

    # 環境変数が設定されているか確認
    if docker exec "$CONTAINER_NAME" sh -c "[ -n \"\$$env_var\" ]" 2>/dev/null; then
        # 値の最初の10文字のみ表示（セキュリティのため）
        local value=$(docker exec "$CONTAINER_NAME" sh -c "echo \$$env_var" | head -c 10)
        echo -e "${GREEN}✓${NC} $env_var が設定されています (${value}...)"
        ((check_passed++))
    else
        if [ "$optional" = "true" ]; then
            echo -e "${YELLOW}⚠${NC} $env_var が設定されていません（オプション）"
            ((check_warning++))
        else
            echo -e "${RED}✗${NC} $env_var が設定されていません"
            ((check_failed++))
        fi
    fi
    echo ""
}

# 各エージェントをチェック
check_agent "Claude Code (Anthropic)" "ANTHROPIC_API_KEY" "true"
check_agent "Gemini CLI (Google)" "GEMINI_API_KEY" "true"
check_agent "Cursor CLI" "CURSOR_API_KEY" "true"
check_agent "OpenAI Codex" "OPENAI_API_KEY" "true"

# GitHub Copilot CLI（設定ファイルベース）
echo -e "${BLUE}[チェック] GitHub Copilot CLI${NC}"
if docker exec "$CONTAINER_NAME" sh -c "[ -d /home/appuser/.config/github-copilot ]" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} GitHub Copilot 設定ディレクトリが存在します"
    ((check_passed++))
else
    echo -e "${YELLOW}⚠${NC} GitHub Copilot 設定ディレクトリが見つかりません（オプション）"
    echo "  ホストで認証後、ボリュームマウントが必要です"
    ((check_warning++))
fi
echo ""

# Cursor設定ディレクトリ
echo -e "${BLUE}[チェック] Cursor CLI 設定ディレクトリ${NC}"
if docker exec "$CONTAINER_NAME" sh -c "[ -d /home/appuser/.cursor ]" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Cursor 設定ディレクトリが存在します"
    ((check_passed++))
else
    echo -e "${YELLOW}⚠${NC} Cursor 設定ディレクトリが見つかりません（オプション）"
    echo "  CURSOR_API_KEYまたはボリュームマウントを使用してください"
    ((check_warning++))
fi
echo ""

# ===========================
# 追加チェック
# ===========================

echo -e "${BLUE}=== 追加チェック ===${NC}\n"

# SSH設定
echo -e "${BLUE}[チェック] SSH設定${NC}"
if docker exec "$CONTAINER_NAME" sh -c "[ -f /home/appuser/.ssh/config ]" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SSH設定ファイルが存在します"
    ((check_passed++))
else
    echo -e "${YELLOW}⚠${NC} SSH設定ファイルが見つかりません"
    echo "  リモートサーバーにアクセスする場合は設定が必要です"
    ((check_warning++))
fi
echo ""

# Git設定
echo -e "${BLUE}[チェック] Git設定${NC}"
if docker exec "$CONTAINER_NAME" sh -c "[ -f /home/appuser/.gitconfig ]" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Git設定ファイルが存在します"
    # Git user.name を確認
    local git_name=$(docker exec "$CONTAINER_NAME" git config --global user.name 2>/dev/null || echo "")
    if [ -n "$git_name" ]; then
        echo -e "  ユーザー名: $git_name"
    fi
    ((check_passed++))
else
    echo -e "${YELLOW}⚠${NC} Git設定ファイルが見つかりません"
    echo "  Gitコミットを行う場合は設定が必要です"
    ((check_warning++))
fi
echo ""

# SSHエージェント
echo -e "${BLUE}[チェック] SSHエージェント${NC}"
if docker exec "$CONTAINER_NAME" sh -c "[ -n \"\$SSH_AUTH_SOCK\" ]" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SSH_AUTH_SOCK が設定されています"
    ((check_passed++))
else
    echo -e "${YELLOW}⚠${NC} SSH_AUTH_SOCK が設定されていません"
    echo "  SSH鍵認証が必要な場合は、SSHエージェントフォワーディングを設定してください"
    ((check_warning++))
fi
echo ""

# ===========================
# セキュリティチェック
# ===========================

echo -e "${BLUE}=== セキュリティチェック ===${NC}\n"

# .envファイルのパーミッション確認
if [ -f ".env" ]; then
    echo -e "${BLUE}[チェック] .env ファイルパーミッション${NC}"
    local perms=$(stat -c "%a" .env 2>/dev/null || stat -f "%OLp" .env 2>/dev/null)
    if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
        echo -e "${GREEN}✓${NC} .env のパーミッションは適切です ($perms)"
        ((check_passed++))
    else
        echo -e "${RED}✗${NC} .env のパーミッションが緩すぎます ($perms)"
        echo "  推奨: chmod 600 .env"
        ((check_failed++))
    fi
    echo ""
fi

# .gitignoreに.envが含まれているか確認
if [ -f ".gitignore" ]; then
    echo -e "${BLUE}[チェック] .gitignore 設定${NC}"
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo -e "${GREEN}✓${NC} .env が .gitignore に追加されています"
        ((check_passed++))
    else
        echo -e "${RED}✗${NC} .env が .gitignore に追加されていません"
        echo "  推奨: echo '.env' >> .gitignore"
        ((check_failed++))
    fi
    echo ""
fi

# ===========================
# 結果サマリー
# ===========================

echo -e "${BLUE}===========================${NC}"
echo -e "${BLUE}チェック結果${NC}"
echo -e "${BLUE}===========================${NC}"
echo -e "${GREEN}合格: ${check_passed}${NC}"
echo -e "${YELLOW}警告: ${check_warning}${NC}"
echo -e "${RED}失敗: ${check_failed}${NC}"
echo ""

if [ $check_failed -eq 0 ] && [ $check_warning -eq 0 ]; then
    echo -e "${GREEN}✓ すべてのチェックに合格しました！${NC}"
    echo ""
    echo -e "${YELLOW}使用可能なエージェント:${NC}"
    docker exec "$CONTAINER_NAME" sh -c '
        echo "- Claude Code: $([ -n "$ANTHROPIC_API_KEY" ] && echo "設定済み" || echo "未設定")"
        echo "- Gemini CLI: $([ -n "$GEMINI_API_KEY" ] && echo "設定済み" || echo "未設定")"
        echo "- Cursor CLI: $([ -n "$CURSOR_API_KEY" ] && echo "設定済み" || echo "未設定")"
        echo "- OpenAI Codex: $([ -n "$OPENAI_API_KEY" ] && echo "設定済み" || echo "未設定")"
    ' 2>/dev/null
    exit 0
elif [ $check_failed -eq 0 ]; then
    echo -e "${YELLOW}⚠ 警告があります。機能によっては制限される可能性があります。${NC}"
    exit 0
else
    echo -e "${RED}✗ 重要な設定が不足しています。上記の推奨事項を確認してください。${NC}"
    exit 1
fi
