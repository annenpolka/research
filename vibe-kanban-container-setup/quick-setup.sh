#!/bin/bash
set -e

# vibe-kanban Quick Setup Script
# このスクリプトはvibe-kanbanをDocker環境で素早くセットアップします

echo "🚀 vibe-kanban Quick Setup"
echo ""

# プロジェクトディレクトリを聞く（/dev/ttyから直接読み込み）
read -p "📁 プロジェクトディレクトリのパスを入力 (例: ~/projects/my-app): " PROJECT_DIR < /dev/tty

# チルダを展開
PROJECT_DIR=$(echo "$PROJECT_DIR" | sed "s|^~|$HOME|")

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ エラー: ディレクトリが存在しません: $PROJECT_DIR"
    exit 1
fi

echo ""
echo "🔐 認証方法を選択してください:"
echo "1) OAuth Token方式（推奨・長期運用向け）"
echo "2) 設定ファイルマウント方式（簡単・短期テスト用、6時間で期限切れ）"
read -p "選択 (1/2): " AUTH_METHOD < /dev/tty

if [ "$AUTH_METHOD" = "1" ]; then
    echo ""
    echo "📋 手順:"
    echo "1. 以下のコマンドを実行してトークンを生成してください:"
    echo "   npx @anthropic-ai/claude-code setup-token"
    echo ""
    read -p "トークンを生成しましたか？ (y/n): " CONFIRM < /dev/tty

    if [ "$CONFIRM" != "y" ]; then
        echo "❌ セットアップを中止します"
        exit 1
    fi

    read -p "🔑 CLAUDE_CODE_OAUTH_TOKEN を入力: " CLAUDE_TOKEN < /dev/tty

    echo ""
    read -p "🔑 GEMINI_API_KEY を入力（Enterでスキップ）: " GEMINI_KEY < /dev/tty

    echo ""
    echo "📝 OpenAI Codex認証方法を選択:"
    echo "1) ChatGPTアカウントログイン（事前に 'codex login' 実行済み）"
    echo "2) API key"
    echo "3) スキップ"
    read -p "選択 (1/2/3): " CODEX_METHOD < /dev/tty

    OPENAI_KEY=""
    CODEX_MOUNT=""
    if [ "$CODEX_METHOD" = "1" ]; then
        if [ -f "$HOME/.codex/auth.json" ]; then
            CODEX_MOUNT="-v $HOME/.codex:/root/.codex:ro"
            echo "✅ ~/.codex/auth.json を使用します"
        else
            echo "❌ エラー: ~/.codex/auth.json が見つかりません"
            echo "   'codex login' を実行してください"
            exit 1
        fi
    elif [ "$CODEX_METHOD" = "2" ]; then
        read -p "🔑 OPENAI_API_KEY を入力: " OPENAI_KEY < /dev/tty
    fi

    # Docker実行
    echo ""
    echo "🐳 vibe-kanbanを起動中..."

    docker run -d \
        --name vibe-kanban \
        -p 3000:3000 \
        -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_TOKEN" \
        ${GEMINI_KEY:+-e GEMINI_API_KEY="$GEMINI_KEY"} \
        ${OPENAI_KEY:+-e OPENAI_API_KEY="$OPENAI_KEY"} \
        $CODEX_MOUNT \
        -v "$PROJECT_DIR:/repos/$(basename $PROJECT_DIR):rw" \
        --user "$(id -u):$(id -g)" \
        vibe-kanban:latest

elif [ "$AUTH_METHOD" = "2" ]; then
    echo ""
    echo "📋 手順:"
    echo "1. 以下のコマンドでClaude Codeで認証してください:"
    echo "   npx @anthropic-ai/claude-code"
    echo ""
    read -p "認証を完了しましたか？ (y/n): " CONFIRM < /dev/tty

    if [ "$CONFIRM" != "y" ]; then
        echo "❌ セットアップを中止します"
        exit 1
    fi

    if [ ! -f "$HOME/.claude/.credentials.json" ]; then
        echo "❌ エラー: ~/.claude/.credentials.json が見つかりません"
        exit 1
    fi

    echo ""
    read -p "🔑 GEMINI_API_KEY を入力（Enterでスキップ）: " GEMINI_KEY < /dev/tty

    echo ""
    echo "📝 OpenAI Codex認証方法を選択:"
    echo "1) ChatGPTアカウントログイン（事前に 'codex login' 実行済み）"
    echo "2) API key"
    echo "3) スキップ"
    read -p "選択 (1/2/3): " CODEX_METHOD < /dev/tty

    OPENAI_KEY=""
    CODEX_MOUNT=""
    if [ "$CODEX_METHOD" = "1" ]; then
        if [ -f "$HOME/.codex/auth.json" ]; then
            CODEX_MOUNT="-v $HOME/.codex:/root/.codex:ro"
            echo "✅ ~/.codex/auth.json を使用します"
        else
            echo "❌ エラー: ~/.codex/auth.json が見つかりません"
            echo "   'codex login' を実行してください"
            exit 1
        fi
    elif [ "$CODEX_METHOD" = "2" ]; then
        read -p "🔑 OPENAI_API_KEY を入力: " OPENAI_KEY < /dev/tty
    fi

    # Docker実行
    echo ""
    echo "🐳 vibe-kanbanを起動中..."

    docker run -d \
        --name vibe-kanban \
        -p 3000:3000 \
        ${GEMINI_KEY:+-e GEMINI_API_KEY="$GEMINI_KEY"} \
        ${OPENAI_KEY:+-e OPENAI_API_KEY="$OPENAI_KEY"} \
        $CODEX_MOUNT \
        -v "$HOME/.claude:/root/.claude:ro" \
        -v "$PROJECT_DIR:/repos/$(basename $PROJECT_DIR):rw" \
        --user "$(id -u):$(id -g)" \
        vibe-kanban:latest

    echo ""
    echo "⚠️  注意: この方法のトークンは約6時間で期限切れになります"
else
    echo "❌ 無効な選択です"
    exit 1
fi

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "📖 次のステップ:"
echo "1. ブラウザで http://localhost:3000 にアクセス"
echo "2. プロジェクトを選択: $(basename $PROJECT_DIR)"
echo "3. タスクを作成してエージェントを選択"
echo ""
echo "🛠️  コンテナ操作:"
echo "  ログ確認: docker logs vibe-kanban"
echo "  停止:     docker stop vibe-kanban"
echo "  削除:     docker rm vibe-kanban"
echo "  再起動:   docker restart vibe-kanban"
