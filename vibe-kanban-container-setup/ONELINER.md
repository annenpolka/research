# vibe-kanban ワンライナーセットアップ

さくっとセットアップするためのコマンド集。

## 🚀 超速セットアップ（対話式）

```bash
curl -fsSL https://raw.githubusercontent.com/annenpolka/research/main/vibe-kanban-container-setup/quick-setup.sh | bash
```

または、ローカルにダウンロードして実行：

```bash
bash quick-setup.sh
```

## ⚡ 完全ワンライナー

### Claude Code のみ（OAuth Token方式）

**前提**: 事前に`npx @anthropic-ai/claude-code setup-token`でトークンを取得

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<YOUR_TOKEN> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ http://localhost:3000にアクセスしてください"
```

### Claude Code + Gemini CLI

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<YOUR_CLAUDE_TOKEN> \
  -e GEMINI_API_KEY=<YOUR_GEMINI_KEY> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ http://localhost:3000にアクセスしてください"
```

### 全部入り（Claude + Gemini + OpenAI Codex）

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<YOUR_CLAUDE_TOKEN> \
  -e GEMINI_API_KEY=<YOUR_GEMINI_KEY> \
  -e OPENAI_API_KEY=<YOUR_OPENAI_KEY> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ 3つのエージェントが利用可能です - http://localhost:3000"
```

### 全部ログイン方式（Claude + Codex）+ Gemini

**前提**:
- `npx @anthropic-ai/claude-code` で認証（6時間有効）
- `codex login` でChatGPTログイン

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e GEMINI_API_KEY=<YOUR_GEMINI_KEY> \
  -v ~/.claude:/root/.claude:ro \
  -v ~/.codex:/root/.codex:ro \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ ChatGPTアカウントでClaude & Codex使用可能 - http://localhost:3000"
```

⚠️ **注意**:
- Claude: トークンは約6時間で期限切れ
- Codex: auth.jsonはホスト非依存で長期間有効

### 設定ファイルマウント方式（短期テスト用・Claude のみ）

**前提**: 事前に`npx @anthropic-ai/claude-code`で認証（6時間有効）

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e GEMINI_API_KEY=<YOUR_GEMINI_KEY> \
  -e OPENAI_API_KEY=<YOUR_OPENAI_KEY> \
  -v ~/.claude:/root/.claude:ro \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "⚠️  Claudeトークンは6時間で期限切れ | ✅ 起動完了！ http://localhost:3000"
```

## 🔧 環境変数ファイル使用（.env）

### ステップ1: .envファイルを作成

```bash
cat > .env <<EOF
CLAUDE_CODE_OAUTH_TOKEN=<YOUR_CLAUDE_TOKEN>
GEMINI_API_KEY=<YOUR_GEMINI_KEY>
OPENAI_API_KEY=<YOUR_OPENAI_KEY>
EOF
```

### ステップ2: ワンライナー起動

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  --env-file .env \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ http://localhost:3000"
```

## 🐳 Docker Compose（最速）

### ステップ1: docker-compose.ymlを作成

```bash
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"
    env_file:
      - .env
    volumes:
      - ~/projects/my-app:/repos/my-app:rw
    user: "${UID:-1000}:${GID:-1000}"
EOF
```

### ステップ2: ワンライナー起動

```bash
UID=$(id -u) GID=$(id -g) docker-compose up -d && \
echo "✅ 起動完了！ http://localhost:3000"
```

## 📋 トークン取得ワンライナー

### Claude Code OAuth Token

```bash
npx @anthropic-ai/claude-code setup-token && \
echo "トークンがクリップボードにコピーされました。上記のコマンドに貼り付けてください。"
```

### Gemini API Key

```bash
echo "Google AI Studio (https://makersuite.google.com/app/apikey) でAPI keyを取得してください"
```

### OpenAI API Key

```bash
echo "OpenAI Platform (https://platform.openai.com/api-keys) でAPI keyを取得してください"
```

## 🛠️ よく使うコマンド

### すぐに起動・停止・削除

```bash
# 起動確認
docker ps | grep vibe-kanban

# ログ確認（リアルタイム）
docker logs -f vibe-kanban

# 停止
docker stop vibe-kanban

# 削除
docker rm vibe-kanban

# 停止して削除
docker stop vibe-kanban && docker rm vibe-kanban

# 再起動
docker restart vibe-kanban

# すべてをクリーンアップ
docker stop vibe-kanban && docker rm vibe-kanban && docker volume prune -f
```

### トラブルシューティング

```bash
# コンテナ内に入る
docker exec -it vibe-kanban /bin/sh

# 環境変数を確認
docker exec vibe-kanban env | grep -E "CLAUDE|GEMINI|OPENAI"

# npxが動作するか確認
docker exec vibe-kanban npx --version

# Claude Codeが実行できるか確認
docker exec vibe-kanban npx -y @anthropic-ai/claude-code --version
```

## 💡 プロTips

### 複数プロジェクトを同時にマウント

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<TOKEN> \
  -v ~/projects/app1:/repos/app1:rw \
  -v ~/projects/app2:/repos/app2:rw \
  -v ~/projects/app3:/repos/app3:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

### カスタムポート

```bash
docker run -d --name vibe-kanban -p 8080:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<TOKEN> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest && \
echo "✅ 起動完了！ http://localhost:8080"
```

### メモリ制限

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  --memory="4g" --memory-swap="4g" \
  -e CLAUDE_CODE_OAUTH_TOKEN=<TOKEN> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

### 自動再起動

```bash
docker run -d --name vibe-kanban -p 3000:3000 \
  --restart=unless-stopped \
  -e CLAUDE_CODE_OAUTH_TOKEN=<TOKEN> \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

## 🔄 アップデート

```bash
# 最新イメージを取得
docker pull vibe-kanban:latest

# 既存コンテナを停止・削除
docker stop vibe-kanban && docker rm vibe-kanban

# 新しいバージョンで起動（設定は同じ）
docker run -d --name vibe-kanban -p 3000:3000 \
  --env-file .env \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```
