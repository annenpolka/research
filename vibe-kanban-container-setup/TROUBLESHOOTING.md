# vibe-kanban トラブルシューティングガイド

このドキュメントは、vibe-kanbanのDocker環境で発生する一般的な問題と解決方法をまとめています。

## 目次

- [Dockerイメージに関する問題](#dockerイメージに関する問題)
- [コンテナ起動に関する問題](#コンテナ起動に関する問題)
- [認証に関する問題](#認証に関する問題)
- [ネットワークに関する問題](#ネットワークに関する問題)
- [パフォーマンスに関する問題](#パフォーマンスに関する問題)

---

## Dockerイメージに関する問題

### エラー: "Unable to find image 'vibe-kanban:latest' locally"

**症状:**
```
Unable to find image 'vibe-kanban:latest' locally
docker: Error response from daemon: pull access denied for vibe-kanban, repository does not exist or may require 'docker login'
```

**原因:**
- vibe-kanbanのDockerイメージがDocker Hubに公開されていない
- ローカルでイメージをビルドする必要がある

**解決方法:**

#### 方法1: quick-setup.shを使用（推奨）

```bash
cd vibe-kanban-container-setup
bash quick-setup.sh
```

`quick-setup.sh`は自動的に：
1. イメージの存在をチェック
2. 存在しない場合、GitHubからリポジトリをクローン
3. Dockerイメージをビルド
4. コンテナを起動

#### 方法2: 手動でビルド

```bash
# リポジトリをクローン
git clone --depth 1 https://github.com/BloopAI/vibe-kanban.git
cd vibe-kanban

# Dockerイメージをビルド
docker build -t vibe-kanban:latest .

# イメージの確認
docker images | grep vibe-kanban
```

#### 方法3: run-docker.shを使用

```bash
cd vibe-kanban-container-setup
bash run-docker.sh basic
```

### エラー: Dockerイメージのビルドに失敗

**症状:**
```
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully
```

**原因と解決方法:**

#### 1. ディスク容量不足

```bash
# ディスク容量を確認
df -h

# 不要なDockerリソースを削除
docker system prune -a
```

#### 2. メモリ不足

```bash
# Docker Desktopの設定を確認
# Settings → Resources → Memory を増やす（推奨: 4GB以上）
```

#### 3. ネットワーク接続の問題

```bash
# GitHubへの接続を確認
curl -I https://github.com

# プロキシ設定が必要な場合
docker build --build-arg HTTP_PROXY=http://proxy:port -t vibe-kanban:latest .
```

#### 4. Dockerfileの問題

```bash
# 最新のリポジトリを取得
cd vibe-kanban
git pull origin main

# キャッシュを使わずにビルド
docker build --no-cache -t vibe-kanban:latest .
```

---

## コンテナ起動に関する問題

### エラー: "Bind for 0.0.0.0:3000 failed: port is already allocated"

**症状:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use
```

**解決方法:**

#### 方法1: 既存のコンテナを確認・停止

```bash
# 3000番ポートを使用しているコンテナを確認
docker ps | grep 3000

# 既存のvibe-kanbanコンテナを停止
docker stop vibe-kanban
docker rm vibe-kanban
```

#### 方法2: 別のポートを使用

```bash
# 8080ポートで起動
docker run -d \
  --name vibe-kanban \
  -p 8080:3000 \
  vibe-kanban:latest

# http://localhost:8080 でアクセス
```

#### 方法3: ポートを使用しているプロセスを特定

```bash
# Linuxの場合
sudo lsof -i :3000
sudo netstat -tulpn | grep 3000

# macOSの場合
sudo lsof -i :3000

# プロセスを終了
kill -9 <PID>
```

### エラー: "Error response from daemon: Conflict. The container name '/vibe-kanban' is already in use"

**解決方法:**

```bash
# 既存のコンテナを削除
docker rm vibe-kanban

# または、強制的に削除（実行中でも）
docker rm -f vibe-kanban

# または、別の名前で起動
docker run -d \
  --name vibe-kanban-2 \
  -p 3000:3000 \
  vibe-kanban:latest
```

---

## 認証に関する問題

### Claude Codeの認証が失敗する

**症状:**
- コンテナ内でClaude Codeが認証エラーを返す
- "Unauthorized" や "Invalid credentials" エラー

**解決方法:**

#### 方法1: OAuth Token方式（推奨）

```bash
# 1. トークンを生成
npx @anthropic-ai/claude-code setup-token

# 2. 生成されたトークンを環境変数に設定
export CLAUDE_CODE_OAUTH_TOKEN=<生成されたトークン>

# 3. コンテナを起動
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN \
  vibe-kanban:latest
```

#### 方法2: 設定ファイルマウント方式

```bash
# 1. ホストで一度認証
npx @anthropic-ai/claude-code

# 2. 設定ファイルの存在を確認
ls -la ~/.claude/.credentials.json

# 3. コンテナを起動（設定ファイルをマウント）
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.claude:/root/.claude:ro \
  vibe-kanban:latest
```

**注意:**
- 設定ファイル方式のトークンは約6時間で期限切れになります
- 長期運用にはOAuth Token方式を推奨

### トークンが期限切れになる

**解決方法:**

```bash
# コンテナを停止
docker stop vibe-kanban

# 新しいトークンを生成
npx @anthropic-ai/claude-code setup-token

# 環境変数を更新して再起動
export CLAUDE_CODE_OAUTH_TOKEN=<新しいトークン>
docker start vibe-kanban
```

---

## ネットワークに関する問題

### コンテナからインターネットにアクセスできない

**症状:**
- npmパッケージのインストールに失敗
- APIへのアクセスがタイムアウト

**解決方法:**

#### 1. DNSの確認

```bash
# コンテナ内でDNSを確認
docker exec vibe-kanban ping -c 3 8.8.8.8
docker exec vibe-kanban ping -c 3 google.com

# DNSが解決できない場合、DNSサーバーを指定
docker run -d \
  --name vibe-kanban \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  -p 3000:3000 \
  vibe-kanban:latest
```

#### 2. プロキシ設定

```bash
# プロキシ経由でコンテナを起動
docker run -d \
  --name vibe-kanban \
  -e HTTP_PROXY=http://proxy:port \
  -e HTTPS_PROXY=http://proxy:port \
  -e NO_PROXY=localhost,127.0.0.1 \
  -p 3000:3000 \
  vibe-kanban:latest
```

### ホストからコンテナにアクセスできない

**症状:**
- `http://localhost:3000` にアクセスできない
- "Connection refused" エラー

**解決方法:**

#### 1. コンテナの状態を確認

```bash
# コンテナが起動しているか確認
docker ps -a | grep vibe-kanban

# ログを確認
docker logs vibe-kanban
```

#### 2. ポートマッピングを確認

```bash
# ポートマッピングを確認
docker port vibe-kanban

# 期待される出力: 3000/tcp -> 0.0.0.0:3000
```

#### 3. ファイアウォールを確認

```bash
# Linuxの場合
sudo ufw status
sudo iptables -L -n

# ポート3000を許可
sudo ufw allow 3000
```

---

## パフォーマンスに関する問題

### コンテナが遅い

**解決方法:**

#### 1. リソース制限を緩和

```bash
# メモリとCPUを増やす
docker run -d \
  --name vibe-kanban \
  --memory="2g" \
  --cpus="2.0" \
  -p 3000:3000 \
  vibe-kanban:latest
```

#### 2. Docker Desktopの設定を確認

- Settings → Resources → Advanced
- CPUとメモリを増やす

#### 3. ボリュームマウントのパフォーマンスを改善

```bash
# macOSの場合、cached/delegatedオプションを使用
docker run -d \
  --name vibe-kanban \
  -v ~/projects:/repos:cached \
  -p 3000:3000 \
  vibe-kanban:latest
```

### ビルドが遅い

**解決方法:**

#### 1. BuildKitを有効にする

```bash
# BuildKitを有効にしてビルド
DOCKER_BUILDKIT=1 docker build -t vibe-kanban:latest .
```

#### 2. ビルドキャッシュを活用

```bash
# 前回のビルドキャッシュを利用
docker build -t vibe-kanban:latest .

# 特定のステージまでビルド（開発時）
docker build --target builder -t vibe-kanban:builder .
```

---

## その他の問題

### コンテナのログを確認する方法

```bash
# 最新のログを表示
docker logs vibe-kanban

# リアルタイムでログを表示
docker logs -f vibe-kanban

# 最後の100行を表示
docker logs --tail 100 vibe-kanban

# タイムスタンプ付きで表示
docker logs -t vibe-kanban
```

### コンテナに入って調査する方法

```bash
# シェルでコンテナに入る
docker exec -it vibe-kanban sh

# rootユーザーで入る
docker exec -it --user root vibe-kanban sh
```

### コンテナの完全なクリーンアップ

```bash
# すべてのvibe-kanbanコンテナを停止・削除
docker ps -a | grep vibe-kanban | awk '{print $1}' | xargs docker rm -f

# vibe-kanbanイメージを削除
docker images | grep vibe-kanban | awk '{print $3}' | xargs docker rmi -f

# すべてのDocker リソースをクリーンアップ（注意: 他のコンテナも削除されます）
docker system prune -a --volumes
```

---

## サポート

問題が解決しない場合：

1. **ログを収集**
   ```bash
   docker logs vibe-kanban > vibe-kanban.log 2>&1
   docker inspect vibe-kanban > vibe-kanban-inspect.json
   ```

2. **環境情報を収集**
   ```bash
   docker version
   docker info
   uname -a
   ```

3. **GitHubでIssueを報告**
   - [vibe-kanban Issues](https://github.com/BloopAI/vibe-kanban/issues)
   - 収集したログと環境情報を添付

4. **よくある質問を確認**
   - [README.md](README.md)
   - [ARCHITECTURE.md](ARCHITECTURE.md)
   - [CODING_AGENTS.md](CODING_AGENTS.md)
