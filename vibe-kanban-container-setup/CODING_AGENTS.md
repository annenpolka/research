# コーディングエージェントと認証情報管理

vibe-kanbanで利用する各コーディングエージェントの設定と認証情報の管理方法について解説します。

## ⚠️ 重要な理解（ソースコード確認済み）

**vibe-kanbanは`npx`経由でエージェントCLIを自動実行します。**

- ✅ vibe-kanbanコンテナ内でエージェントCLIが実行される
- ✅ `npx`が自動的にエージェントをダウンロード・実行
- ✅ ユーザーはエージェントを事前インストールする必要が**ない**
- ✅ 認証はAPI key（環境変数）で行う

**例**: Claude Codeの場合
```bash
# vibe-kanbanが内部で実行
npx -y @anthropic-ai/claude-code@2.0.31
```

**つまり**:
- ❌ ホストにエージェントをインストールする必要はない
- ❌ ホスト側で認証する必要はない
- ✅ API keyを環境変数で渡すだけ

詳しいアーキテクチャについては **[ARCHITECTURE.md](ARCHITECTURE.md)** を参照してください。

## 目次

1. [サポートされているコーディングエージェント](#サポートされているコーディングエージェント)
2. [各エージェントの認証方法](#各エージェントの認証方法)
3. [コンテナ環境での認証情報管理](#コンテナ環境での認証情報管理)
4. [セキュアな設定方法](#セキュアな設定方法)
5. [トラブルシューティング](#トラブルシューティング)

---

## サポートされているコーディングエージェント

vibe-kanbanは以下の9種類のAIコーディングエージェントをサポートしています（公式ドキュメント確認済み）：

### 主要エージェント

1. **Claude Code** - Anthropic製のコーディングアシスタント
2. **Gemini CLI** - Google製のコマンドラインAIツール
3. **OpenAI Codex** - OpenAI製のコード生成AI
4. **GitHub Copilot** - GitHubのAIペアプログラマー
5. **Amp Code** - コーディングエージェントツール
6. **Cursor Agent** - Cursor IDEのコマンドラインインターフェース
7. **SST OpenCode** - オープンソースのコーディングAI
8. **Claude Code Router** - 複数モデルを調整する高度なエージェント
9. **Qwen Code** - Qwen製のコーディングAI

### エージェントプロファイル（バリアント）

vibe-kanbanでは、Settings → Agents で各エージェントのプロファイルを管理できます：

- **DEFAULT**: 標準設定
- **PLAN**: 計画・設計用の設定
- **FLASH**: 高速実行用の設定

各バリアントでモデル選択、サンドボックスレベル、承認設定などをカスタマイズ可能。

### 重要な前提条件（Docker実行の場合）

⚠️ **コンテナ環境では、API keyを環境変数で渡す必要があります。**

- ✅ ホスト実行（`npx vibe-kanban`）: ブラウザ認証フローが使える
- ❌ Docker実行: ブラウザ認証は不可、API keyのみ

vibe-kanbanは各エージェントを統合・管理するためのオーケストレーションツールであり、エージェント自体の認証機能は提供していません。

---

## 各エージェントの認証方法

### 1. Claude Code

⚠️ **重要**: Docker環境での認証は複雑です（2025年時点で既知の問題あり）

#### ホスト実行の場合（簡単）

Claude Codeには2つの認証方法があります：

1. **Claude Pro/Max サブスクリプション**（推奨・ブラウザ認証）
2. **Anthropic API キー**（従量課金）

```bash
# ホストで実行する場合
npx @anthropic-ai/claude-code
# ブラウザで認証フローが開きます
```

#### Docker実行の場合（複雑）

**❌ 動かない方法**:

```bash
# これだけでは動きません（GitHub Issue #9699）
docker run -e ANTHROPIC_API_KEY=sk-ant-xxx vibe-kanban
```

**問題点**:
- `ANTHROPIC_API_KEY`を設定しても`/login`を要求される
- 非対話モードで"Invalid API key"エラー

**✅ 動作する方法**:

**方法1: OAuth Token（推奨）**

```bash
# ホストでトークンを生成
npx @anthropic-ai/claude-code setup-token
# トークンがクリップボードにコピーされます

# Docker実行時
docker run -e CLAUDE_CODE_OAUTH_TOKEN=<トークン> vibe-kanban
```

**方法2: 設定ファイルマウント**

```bash
# ホストで一度認証（一度だけ）
npx @anthropic-ai/claude-code
# ~/.claude/settings.json が作成される

# Docker実行時に設定ファイルをマウント
docker run -v ~/.claude:/root/.claude:ro vibe-kanban
```

#### API キーの取得

1. [Anthropic Console](https://console.anthropic.com/)にログイン
2. 「API Keys」セクションに移動
3. 「Create Key」をクリック
4. キーを安全に保存（一度しか表示されません）

#### コスト

- **Claude Pro/Max**: 月額$20（US）/ $24（日本）- ブラウザ認証
- **API使用**: 従量課金
  - Claude 3.5 Sonnet: $3/MTok (input), $15/MTok (output)
  - Claude 3 Opus: $15/MTok (input), $75/MTok (output)

---

### 2. Gemini CLI

#### 認証方法

Gemini CLIは**vibe-kanbanの外で事前に認証**する必要があります。

**認証手順**:

```bash
# Gemini CLIのインストール（npmから）
npm install -g @google/generative-ai-cli

# 認証
gemini-cli auth login

# または、API keyを使用
export GEMINI_API_KEY="your-gemini-api-key"
```

**API キーの取得**:

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. 「Get API Key」をクリック
3. APIキーをコピーして保存

---

### 3. Cursor CLI

#### 認証方法

Cursor CLIには2つの認証方法があります：

**方法A: ブラウザ認証**（推奨）

```bash
cursor-agent login
```

このコマンドを実行すると、ブラウザが開いて認証を求められます。

**方法B: API キー**

```bash
export CURSOR_API_KEY="your-cursor-api-key"
```

**API キーの取得**:

1. [Cursor Settings](https://cursor.sh/settings)にログイン
2. 「API Keys」タブに移動
3. 新しいAPIキーを生成

---

### 4. GitHub Copilot CLI

#### 認証方法

GitHub Copilot CLIは初回実行時に認証を求められます。

**認証手順**:

```bash
# GitHub Copilot CLIのインストール
npm install -g @githubnext/github-copilot-cli

# 初回実行時、/loginコマンドで認証
gh copilot
# プロンプトで /login を実行
```

**ブラウザ認証**:

1. ブラウザが開き、GitHubへのサインインを求められます
2. デバイスコードを入力
3. GitHub Copilot へのアクセスを許可

**前提条件**:

- GitHub Copilot サブスクリプション（個人または組織）
- GitHub CLI (`gh`)がインストールされていること

---

### 5. OpenCode

#### 認証方法

OpenCodeは**vibe-kanbanの外で事前に認証**する必要があります。

詳細は[OpenCode公式ドキュメント](https://opencode.ai/docs)を参照してください。

---

### 6. OpenAI Codex

Codex CLIは2つの認証方法をサポートしています。

#### ホスト実行の場合

**方法A: ChatGPTアカウントログイン（推奨）**

ChatGPT Plus/Pro/Team/Edu/Enterpriseアカウントでログイン可能。

```bash
# ホストで実行する場合
codex login
# ブラウザでChatGPTログインフローが開きます
```

**方法B: API Key**

```bash
# API keyで認証
printenv OPENAI_API_KEY | codex login --with-api-key
```

#### Docker実行の場合

**方法1: 設定ファイルマウント（推奨）**

```bash
# ホストで一度ログイン
codex login
# ~/.codex/auth.json が作成される

# Docker実行時に設定ファイルをマウント
docker run -v ~/.codex:/root/.codex:ro vibe-kanban
```

**認証ファイルの場所**：
- **macOS/Linux**: `~/.codex/auth.json`
- **Windows**: `%USERPROFILE%\.codex\auth.json`

⚠️ **利点**: auth.jsonはホスト非依存で、Claude Codeと違い**長期間有効**。

**方法2: API Key**

```bash
docker run -e OPENAI_API_KEY=sk-your-openai-key vibe-kanban
```

#### API キーの取得

1. [OpenAI Platform](https://platform.openai.com/api-keys)にログイン
2. 「Create new secret key」をクリック
3. キーをコピーして保存

---

## コンテナ環境での認証情報管理

vibe-kanbanをコンテナで実行する際、エージェントの認証情報を安全に渡す必要があります。

⚠️ **重要**: Claude CodeはANTHROPIC_API_KEYだけでは動作しません。OAuth tokenまたは設定ファイルが必要です。

### 方法1: 環境変数ファイル（開発環境向け）

**ステップ1: Claude Code用トークンを生成**

```bash
npx @anthropic-ai/claude-code setup-token
# トークンをコピー
```

**ステップ2: .envファイルを作成**

```bash
# .env
# Claude Code用（OAuth token推奨）
CLAUDE_CODE_OAUTH_TOKEN=<生成されたトークン>

# その他のエージェント用（API keyで動作）
GEMINI_API_KEY=your-gemini-key-here
OPENAI_API_KEY=sk-your-openai-key-here
CURSOR_API_KEY=your-cursor-key-here

# 注意: ANTHROPIC_API_KEYは単独では動作しません
# ANTHROPIC_API_KEY=sk-ant-xxx  # ❌ これだけでは不十分
```

**ステップ3: Dockerで使用**

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --env-file .env \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

**重要**: `.env`ファイルを`.gitignore`に追加して、Gitにコミットしないようにしてください！

```bash
echo ".env" >> .gitignore
```

### 方法1-B: 設定ファイルマウント（短期テスト用）

⚠️ **制限事項**: `~/.claude/.credentials.json`のトークンは**約6時間で期限切れ**。長期運用には方法1のOAuth Token推奨。

```bash
# ステップ1: ホストで一度認証
npx @anthropic-ai/claude-code
# ~/.claude/.credentials.json が作成されます（6時間有効）

# ステップ2: .envファイルを作成（Claude Code除く）
# .env
GEMINI_API_KEY=your-gemini-key-here
OPENAI_API_KEY=sk-your-openai-key-here

# ステップ3: 設定ファイルをマウント
# macOS/Linux/WSL
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --env-file .env \
  -v ~/.claude:/root/.claude:ro \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest

# Windows PowerShell
docker run -d `
  --name vibe-kanban `
  -p 3000:3000 `
  --env-file .env `
  -v ${env:USERPROFILE}\.claude:/root/.claude:ro `
  -v ${env:USERPROFILE}\projects\my-app:/repos/my-app:rw `
  vibe-kanban:latest
```

**認証ファイルの場所**：
- **macOS/Linux/WSL**: `~/.claude/.credentials.json` (OAuth トークン、6時間有効)
- **Windows（PowerShell）**: `$env:USERPROFILE\.claude\.credentials.json`
- **注意**: WSLでは必ずLinux filesystem内（`~/.claude/`）を使用。Windows側（`/mnt/c/`）ではありません。

---

### 方法2: Docker Compose（開発環境向け）

`docker-compose.agents.yml`:

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"

    volumes:
      - ~/projects/my-app:/repos/my-app:rw
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.gitconfig:/home/appuser/.gitconfig:ro

    # 環境変数（.envファイルから読み込み）
    env_file:
      - .env

    # または、直接指定（非推奨：機密情報がファイルに残る）
    # environment:
    #   - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    #   - GEMINI_API_KEY=${GEMINI_API_KEY}
    #   - CURSOR_API_KEY=${CURSOR_API_KEY}
    #   - OPENAI_API_KEY=${OPENAI_API_KEY}

    user: "${UID:-1000}:${GID:-1000}"
```

**実行**:

```bash
# .envファイルを作成（上記参照）
# 起動
docker-compose -f docker-compose.agents.yml up -d
```

---

### 方法3: Docker Secrets（本番環境向け）

Docker SwarmまたはKubernetesを使用する場合、Secretsで管理します。

#### Docker Swarm

```bash
# Swarmの初期化
docker swarm init

# Secretsの作成
echo "sk-ant-your-key-here" | docker secret create anthropic_api_key -
echo "your-gemini-key-here" | docker secret create gemini_api_key -
echo "your-cursor-key-here" | docker secret create cursor_api_key -
echo "sk-your-openai-key-here" | docker secret create openai_api_key -

# サービスの作成
docker service create \
  --name vibe-kanban \
  --secret anthropic_api_key \
  --secret gemini_api_key \
  --secret cursor_api_key \
  --secret openai_api_key \
  --publish 3000:3000 \
  vibe-kanban:latest
```

コンテナ内で、Secretsは`/run/secrets/<secret-name>`に配置されます。

---

### 方法4: Kubernetes Secrets（本番環境向け）

#### Secretの作成

```bash
# コマンドラインから作成
kubectl create secret generic vibe-kanban-agent-keys \
  --from-literal=anthropic-api-key=sk-ant-your-key-here \
  --from-literal=gemini-api-key=your-gemini-key-here \
  --from-literal=cursor-api-key=your-cursor-key-here \
  --from-literal=openai-api-key=sk-your-openai-key-here \
  -n default
```

#### Deploymentでの使用

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vibe-kanban
spec:
  template:
    spec:
      containers:
      - name: vibe-kanban
        image: vibe-kanban:latest
        env:
        # Secretから環境変数として読み込み
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-agent-keys
              key: anthropic-api-key
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-agent-keys
              key: gemini-api-key
        - name: CURSOR_API_KEY
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-agent-keys
              key: cursor-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-agent-keys
              key: openai-api-key
```

---

### 方法5: 認証情報ファイルのマウント（特定のエージェント）

一部のエージェントは、設定ファイルや認証トークンをファイルシステムに保存します。

#### GitHub Copilot CLI

```bash
# ホストで認証
gh copilot

# 認証情報をコンテナにマウント
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.config/github-copilot:/home/appuser/.config/github-copilot:ro \
  vibe-kanban:latest
```

#### Cursor CLI

```bash
# Cursor設定ディレクトリをマウント
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.cursor:/home/appuser/.cursor:ro \
  vibe-kanban:latest
```

---

## セキュアな設定方法

### 認証情報の保護

#### 1. ファイルパーミッション

```bash
# .envファイルを自分だけが読めるようにする
chmod 600 .env

# Secret用ディレクトリを作成
mkdir -p secrets
chmod 700 secrets

# Secretファイルを作成
echo "sk-ant-your-key" > secrets/anthropic_api_key.txt
chmod 600 secrets/anthropic_api_key.txt
```

#### 2. .gitignoreに追加

```bash
# .gitignore
.env
.env.local
.env.*.local
secrets/
*.key
*.token
*_api_key.txt
```

#### 3. 環境変数の検証

```bash
# コンテナ内の環境変数を確認（デバッグ用）
docker exec vibe-kanban env | grep -E "API_KEY|TOKEN"

# 実際の値は表示しない（セキュリティのため）
docker exec vibe-kanban sh -c 'echo "ANTHROPIC_API_KEY is set: $([ -n "$ANTHROPIC_API_KEY" ] && echo Yes || echo No)"'
```

---

### 暗号化されたSecrets管理

#### 1. age（年齢）を使用した暗号化

```bash
# ageのインストール
sudo apt-get install age  # Debian/Ubuntu
brew install age           # macOS

# 鍵ペアの生成
age-keygen -o ~/.age/key.txt

# Secretの暗号化
echo "sk-ant-your-key" | age -r $(age-keygen -y ~/.age/key.txt) > secrets/anthropic_api_key.age

# 復号化してDockerに渡す
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY=$(age -d -i ~/.age/key.txt secrets/anthropic_api_key.age) \
  vibe-kanban:latest
```

#### 2. SOPS（Secrets OPerationS）を使用

```bash
# SOPSのインストール
brew install sops  # macOS
# または https://github.com/mozilla/sops/releases からダウンロード

# .env.encryptedファイルの作成と暗号化
sops -e .env > .env.encrypted

# 復号化して使用
sops -d .env.encrypted > .env.tmp
docker run -d --env-file .env.tmp vibe-kanban:latest
rm .env.tmp  # 使用後は削除
```

---

### セキュリティベストプラクティス

#### チェックリスト

- [ ] API keyを平文でGitにコミットしない
- [ ] .envファイルを.gitignoreに追加
- [ ] ファイルパーミッションを600または700に制限
- [ ] 本番環境ではDocker SecretsまたはKubernetes Secretsを使用
- [ ] 定期的にAPI keyをローテーション
- [ ] 不要になったAPI keyは削除
- [ ] API keyのスコープを最小限に制限
- [ ] ログにAPI keyが出力されないようにする
- [ ] CI/CD環境では環境変数を使用
- [ ] 開発環境と本番環境でAPI keyを分ける

---

## トラブルシューティング

### 問題1: "API key not found" エラー

**症状**:
```
Error: ANTHROPIC_API_KEY environment variable not found
```

**解決**:

```bash
# 環境変数が設定されているか確認
docker exec vibe-kanban sh -c 'echo $ANTHROPIC_API_KEY'

# 設定されていない場合、コンテナを再作成
docker stop vibe-kanban
docker rm vibe-kanban

docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY="sk-ant-your-key" \
  vibe-kanban:latest
```

---

### 問題2: "Invalid API key" エラー

**症状**:
```
Error: Invalid API key provided
```

**原因と解決**:

1. **API keyが間違っている**
   ```bash
   # API keyを再確認
   echo $ANTHROPIC_API_KEY
   ```

2. **API keyが期限切れまたは削除された**
   - [Anthropic Console](https://console.anthropic.com/)で新しいキーを生成

3. **余分な空白や改行が含まれている**
   ```bash
   # trimして設定
   export ANTHROPIC_API_KEY=$(echo "sk-ant-your-key" | tr -d '[:space:]')
   ```

---

### 問題3: 複数エージェントの設定が競合

**症状**:
両方のエージェントが動作しない、または片方しか動作しない

**解決**:

```bash
# すべてのAPI keyを一度に設定
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY="sk-ant-your-key" \
  -e GEMINI_API_KEY="your-gemini-key" \
  -e CURSOR_API_KEY="your-cursor-key" \
  -e OPENAI_API_KEY="sk-your-openai-key" \
  vibe-kanban:latest

# コンテナ内で確認
docker exec vibe-kanban env | grep API_KEY
```

---

### 問題4: GitHub Copilot CLIの認証が保持されない

**症状**:
コンテナを再起動するたびに再認証が必要

**解決**:

```bash
# 認証情報をボリュームとして永続化
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v vibe-github-copilot:/home/appuser/.config/github-copilot \
  vibe-kanban:latest
```

または、ホストの認証情報をマウント:

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.config/github-copilot:/home/appuser/.config/github-copilot:ro \
  vibe-kanban:latest
```

---

### 問題5: "Permission denied" when accessing API key file

**症状**:
```
Error: Permission denied: /run/secrets/anthropic_api_key
```

**解決**:

Docker Secretsを使用している場合、Secretファイルのパーミッションを確認:

```bash
# コンテナ内でSecretファイルを確認
docker exec vibe-kanban ls -la /run/secrets/

# appuserがSecretにアクセスできるようにする
# Dockerfileで調整が必要な場合がある
```

---

## まとめ

### 推奨される設定方法

**開発環境**:
- `.env`ファイルを使用（.gitignoreに追加）
- `--env-file`オプションでDockerに渡す
- ファイルパーミッションを600に設定

**本番環境**:
- Docker SecretsまたはKubernetes Secretsを使用
- 環境変数は実行時に注入
- 定期的なAPI keyのローテーション
- 監査ログの有効化

### クイックスタート

```bash
# 1. .envファイルを作成
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=your-gemini-key-here
CURSOR_API_KEY=your-cursor-key-here
OPENAI_API_KEY=sk-your-openai-key-here
EOF

# 2. パーミッション設定
chmod 600 .env

# 3. コンテナ起動
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --env-file .env \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest

# 4. 動作確認
docker logs vibe-kanban
```

### 参考リンク

- [Claude Code - Managing API Keys](https://support.claude.com/en/articles/12304248-managing-api-key-environment-variables-in-claude-code)
- [Vibe Kanban - Supported Coding Agents](https://www.vibekanban.com/docs/supported-coding-agents)
- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)

---

**これで、vibe-kanbanで複数のコーディングエージェントを安全に使用できます！** 🚀
