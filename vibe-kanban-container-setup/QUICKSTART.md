# vibe-kanban クイックスタートガイド

このガイドは、vibe-kanbanを使って実際の開発プロジェクトで作業を始めるための最短ルートです。

## ⚠️ 重要な前提

**vibe-kanbanはエージェント管理ツールです。コーディングエージェント本体は含まれません。**

エージェント（Claude Code、Gemini CLI等）は**ホスト側で**インストール・認証する必要があります。

詳しくは **[ARCHITECTURE.md](ARCHITECTURE.md)** を参照してください。

## 前提条件

- Docker がインストールされていること
- Git がインストールされていること
- プロジェクトディレクトリが存在すること
- **（オプション）使用したいAIエージェントがホストにインストール・認証されていること**
  - Claude Code: `npm install -g @anthropic-ai/claude-cli && claude auth login`
  - Gemini CLI: `npm install -g @google/generative-ai-cli && gemini-cli auth login`
  - その他のエージェントについては [CODING_AGENTS.md](CODING_AGENTS.md) を参照

## 5分で始める

### ステップ1: vibe-kanbanイメージのビルド

```bash
# vibe-kanbanリポジトリをクローン
git clone https://github.com/BloopAI/vibe-kanban.git
cd vibe-kanban

# Dockerイメージをビルド
docker build -t vibe-kanban:latest .
```

または、Docker Composeで自動ビルド:

```bash
cd /path/to/vibe-kanban-container-setup
docker-compose -f docker-compose.dev.yml build
```

### ステップ2: プロジェクトで起動

**方法A: 便利スクリプトを使用（推奨）**

```bash
cd /path/to/vibe-kanban-container-setup
./start-with-project.sh ~/projects/my-app
```

**方法B: Docker Compose を使用**

```bash
# 環境変数を設定
export UID=$(id -u)
export GID=$(id -g)
export PROJECT_PATH=~/projects/my-app

# 起動
docker-compose -f docker-compose.dev.yml up -d
```

**方法C: Docker run コマンド**

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

### ステップ3: ブラウザでアクセス

```
http://localhost:3000
```

### ステップ4: プロジェクトで作業

vibe-kanbanのUIから、`/repos/my-app`（または指定したプロジェクト名）のパスでプロジェクトが利用可能です。

## よく使うコマンド

```bash
# ログを表示
docker logs -f vibe-kanban

# コンテナ内でシェルを起動
docker exec -it vibe-kanban sh

# コンテナを停止
docker stop vibe-kanban

# コンテナを削除
docker rm vibe-kanban

# 停止して削除
docker stop vibe-kanban && docker rm vibe-kanban

# Docker Composeで停止
docker-compose -f docker-compose.dev.yml down
```

## 複数のプロジェクトを扱う

### docker-compose.dev.ymlを編集

```yaml
volumes:
  - ~/projects/project-a:/repos/project-a:rw
  - ~/projects/project-b:/repos/project-b:rw
  - ~/projects/project-c:/repos/project-c:rw
```

または、プロジェクトディレクトリ全体をマウント:

```yaml
volumes:
  - ~/projects:/repos:rw
```

## トラブルシューティング

### 問題1: Permission denied

**症状**: ファイルの読み書きができない

**解決**:

```bash
# UID/GIDを確認
id

# 正しいUID/GIDで起動
docker run --user $(id -u):$(id -g) ...
```

### 問題2: プロジェクトが見つからない

**症状**: `/repos/my-project` が存在しない

**解決**:

```bash
# マウントを確認
docker inspect vibe-kanban | grep -A 10 Mounts

# コンテナ内を確認
docker exec vibe-kanban ls -la /repos
```

### 問題3: SSH認証が失敗する

**症状**: `Permission denied (publickey)`

**解決**:

```bash
# SSHエージェントを起動
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# SSH_AUTH_SOCKを確認
echo $SSH_AUTH_SOCK

# コンテナに渡す
docker run \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  ...
```

### 問題4: Gitの設定が反映されない

**症状**: Git コミット時にエラー

**解決**:

```bash
# Git設定をマウント
-v ~/.gitconfig:/home/appuser/.gitconfig:ro

# または、コンテナ内で設定
docker exec vibe-kanban git config --global user.name "Your Name"
docker exec vibe-kanban git config --global user.email "you@example.com"
```

## セキュリティ設定

開発環境でもセキュリティを強化したい場合:

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  --user $(id -u):$(id -g) \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --memory="2g" \
  --cpus="2.0" \
  --pids-limit 200 \
  --tmpfs /tmp:size=200M \
  vibe-kanban:latest
```

## 次のステップ

詳細な設定とカスタマイズについては、以下のドキュメントを参照してください:

- **[PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md)** - プロジェクト管理の詳細
- **[CREDENTIALS.md](CREDENTIALS.md)** - 認証情報の管理
- **[README.md](README.md)** - 包括的なガイド

## ヘルプとサポート

問題が解決しない場合:

1. ログを確認: `docker logs vibe-kanban`
2. セキュリティチェックを実行: `./security-check.sh vibe-kanban`
3. コンテナの状態を確認: `docker inspect vibe-kanban`
4. [vibe-kanban公式ドキュメント](https://vibekanban.com/docs)を参照

---

**おめでとうございます！** これで vibe-kanban を使った開発を始められます 🎉
