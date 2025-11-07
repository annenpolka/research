# コンテナ内でプロジェクトを扱う方法

vibe-kanbanをコンテナで実行しながら、実際のプロジェクトファイルを操作するための実用的なガイドです。

## 目次

1. [基本概念](#基本概念)
2. [単一プロジェクトのマウント](#単一プロジェクトのマウント)
3. [複数プロジェクトの管理](#複数プロジェクトの管理)
4. [ファイルパーミッション問題の解決](#ファイルパーミッション問題の解決)
5. [リモートプロジェクト](#リモートプロジェクト)
6. [Docker-in-Docker (DinD)](#docker-in-docker-dind)
7. [実用例](#実用例)
8. [トラブルシューティング](#トラブルシューティング)

---

## 基本概念

### /reposディレクトリ

vibe-kanbanは `/repos` ディレクトリをワークディレクトリとして使用します。このディレクトリに：

- ホストのプロジェクトをマウント
- AIエージェントがファイル操作を実行
- リポジトリのクローンや管理が行われる

### マウント方法の選択肢

1. **バインドマウント**: ホストのディレクトリを直接マウント（推奨）
2. **名前付きボリューム**: Docker管理のボリュームを使用
3. **リモートアクセス**: SSH経由でリモートサーバーのプロジェクトにアクセス

---

## 単一プロジェクトのマウント

### 基本的なマウント

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v /path/to/your/project:/repos/my-project:rw \
  vibe-kanban:latest
```

### セキュアなマウント

読み取り専用ルートファイルシステムを維持しながらプロジェクトをマウント：

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --read-only \
  --tmpfs /tmp:size=100M,mode=1777 \
  -v /path/to/your/project:/repos/my-project:rw \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  vibe-kanban:latest
```

**注意**: `/repos`自体は書き込み可能にする必要があります（tmpfsでマウントする場合以外）。

### Docker Composeでの設定

`docker-compose.project.yml`:

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"

    volumes:
      # プロジェクトディレクトリ
      - ~/projects/my-app:/repos/my-app:rw

      # SSH設定（読み取り専用）
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro

      # Git設定（読み取り専用）
      - ~/.gitconfig:/home/appuser/.gitconfig:ro

    environment:
      - PORT=3000
      - HOST=0.0.0.0

    # ユーザーIDを一致させる（後述）
    user: "${UID:-1000}:${GID:-1000}"
```

実行:

```bash
# UID/GIDを自動設定
export UID=$(id -u)
export GID=$(id -g)
docker-compose -f docker-compose.project.yml up -d
```

---

## 複数プロジェクトの管理

### 複数プロジェクトを同時にマウント

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/project-a:/repos/project-a:rw \
  -v ~/projects/project-b:/repos/project-b:rw \
  -v ~/projects/project-c:/repos/project-c:rw \
  vibe-kanban:latest
```

### プロジェクトディレクトリ全体をマウント

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

**注意**: セキュリティ上、必要なプロジェクトのみをマウントすることを推奨します。

### Docker Composeでの複数プロジェクト

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"

    volumes:
      # 複数のプロジェクト
      - ~/projects/web-app:/repos/web-app:rw
      - ~/projects/api-server:/repos/api-server:rw
      - ~/projects/mobile-app:/repos/mobile-app:rw

      # または全体をマウント（注意して使用）
      # - ~/projects:/repos:rw

      # 認証情報
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
      - ~/.gitconfig:/home/appuser/.gitconfig:ro

    user: "${UID:-1000}:${GID:-1000}"
```

---

## ファイルパーミッション問題の解決

コンテナ内のユーザーとホストのユーザーのUID/GIDが異なる場合、パーミッション問題が発生します。

### 問題の症状

```
Permission denied: cannot write to /repos/my-project
Permission denied: cannot read /repos/my-project/.git
```

### 解決方法1: ホストのUID/GIDを使用（推奨）

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

**利点**: ホストとコンテナで同じUID/GIDを使用
**欠点**: コンテナ内のappuserが使えない（rootグループに依存）

### 解決方法2: カスタムDockerfileでUID/GIDを調整

`Dockerfile.custom-uid`:

```dockerfile
FROM vibe-kanban:latest

# ビルド時にUID/GIDを指定
ARG UID=1000
ARG GID=1000

USER root

# 既存のappuserのUID/GIDを変更
RUN usermod -u ${UID} appuser && \
    groupmod -g ${GID} appgroup && \
    chown -R appuser:appgroup /app /repos

USER appuser
```

ビルドと実行:

```bash
# ホストのUID/GIDでビルド
docker build \
  --build-arg UID=$(id -u) \
  --build-arg GID=$(id -g) \
  -f Dockerfile.custom-uid \
  -t vibe-kanban:custom .

# 実行
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  vibe-kanban:custom
```

### 解決方法3: entrypointスクリプトで動的に調整

`entrypoint-fixuid.sh`:

```bash
#!/bin/bash
set -e

# ホストのUID/GIDを環境変数から取得
HOST_UID=${HOST_UID:-1000}
HOST_GID=${HOST_GID:-1000}

# コンテナ内のユーザーのUID/GIDを調整（rootの場合のみ）
if [ "$(id -u)" = "0" ]; then
  # appuserのUID/GIDを変更
  usermod -u ${HOST_UID} appuser 2>/dev/null || true
  groupmod -g ${HOST_GID} appgroup 2>/dev/null || true

  # /reposの所有権を更新
  chown -R appuser:appgroup /repos

  # appuserとして実行を継続
  exec su-exec appuser "$@"
else
  # 既に非rootユーザーの場合はそのまま実行
  exec "$@"
fi
```

使用例:

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -e HOST_UID=$(id -u) \
  -e HOST_GID=$(id -g) \
  vibe-kanban:latest
```

### 解決方法4: ACL（Access Control List）を使用

Linux環境で、より柔軟なパーミッション管理：

```bash
# ホスト側でACLを設定
sudo setfacl -R -m u:1000:rwx ~/projects/my-app
sudo setfacl -R -d -m u:1000:rwx ~/projects/my-app

# コンテナ実行
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  vibe-kanban:latest
```

---

## リモートプロジェクト

### SSH経由でリモートサーバーのプロジェクトにアクセス

vibe-kanbanはリモートサーバーとのSSH連携をサポートしています。

#### 前提条件

1. リモートサーバーへのSSHアクセス（パスワードなしの鍵認証）
2. SSHエージェントフォワーディングの設定

#### 設定例

```bash
# SSHエージェントの起動
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# SSHエージェントをコンテナに渡す
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  vibe-kanban:latest
```

#### SSH設定ファイル例

`~/.ssh/config`:

```
Host remote-dev
  HostName dev.example.com
  User developer
  Port 22
  IdentityFile ~/.ssh/id_rsa
  ForwardAgent yes

Host remote-prod
  HostName prod.example.com
  User deploy
  Port 2222
  IdentityFile ~/.ssh/id_rsa_prod
```

#### vibe-kanban内でのリモートアクセス

コンテナ内から:

```bash
# リモートサーバーにSSH
ssh remote-dev

# リモートのリポジトリをクローン
cd /repos
git clone ssh://remote-dev/path/to/repo.git
```

---

## Docker-in-Docker (DinD)

AIエージェントがDockerコマンドを実行する必要がある場合（例：コンテナビルド、テスト実行）。

### 方法1: Docker Socketをマウント（簡単だが危険）

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/projects/my-app:/repos/my-app:rw \
  vibe-kanban:latest
```

**警告**: Docker socketをマウントすると、コンテナがホストのDockerデーモンに完全アクセスできるため、セキュリティリスクが高い。

### 方法2: DinD（より安全）

```yaml
version: '3.8'

services:
  docker-dind:
    image: docker:dind
    privileged: true
    environment:
      - DOCKER_TLS_CERTDIR=/certs
    volumes:
      - docker-certs:/certs/client
      - docker-data:/var/lib/docker
    networks:
      - vibe-network

  vibe-kanban:
    image: vibe-kanban:latest
    depends_on:
      - docker-dind
    ports:
      - "3000:3000"
    environment:
      - DOCKER_HOST=tcp://docker-dind:2376
      - DOCKER_TLS_VERIFY=1
      - DOCKER_CERT_PATH=/certs/client
    volumes:
      - docker-certs:/certs/client:ro
      - ~/projects/my-app:/repos/my-app:rw
    networks:
      - vibe-network

volumes:
  docker-certs:
  docker-data:

networks:
  vibe-network:
    driver: bridge
```

### 方法3: Dockerコマンドなしで動作させる

可能であれば、Dockerに依存しない方法を優先：

- テストランナーを直接実行（npm test、pytest等）
- ビルドツールを直接使用（webpack、cargo build等）
- CI/CDパイプラインで別途処理

---

## 実用例

### 例1: ウェブアプリ開発

```bash
#!/bin/bash
# start-vibe-for-webapp.sh

PROJECT_DIR=~/projects/my-webapp

docker run -d \
  --name vibe-kanban-webapp \
  -p 3000:3000 \
  -v ${PROJECT_DIR}:/repos/my-webapp:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  --user $(id -u):$(id -g) \
  --memory="1g" \
  --cpus="2.0" \
  vibe-kanban:latest

echo "vibe-kanban started for ${PROJECT_DIR}"
echo "Access: http://localhost:3000"
```

### 例2: 複数マイクロサービスの開発

`docker-compose.microservices.yml`:

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"

    volumes:
      # 複数のマイクロサービス
      - ~/projects/auth-service:/repos/auth-service:rw
      - ~/projects/api-gateway:/repos/api-gateway:rw
      - ~/projects/user-service:/repos/user-service:rw
      - ~/projects/notification-service:/repos/notification-service:rw

      # 共有ライブラリ
      - ~/projects/shared-lib:/repos/shared-lib:rw

      # 認証情報
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
      - ~/.gitconfig:/home/appuser/.gitconfig:ro
      - ${SSH_AUTH_SOCK}:/ssh-agent

    environment:
      - SSH_AUTH_SOCK=/ssh-agent
      - PORT=3000
      - HOST=0.0.0.0

    user: "${UID:-1000}:${GID:-1000}"

    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 例3: セキュアな開発環境

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "127.0.0.1:3000:3000"  # ローカルホストのみ

    volumes:
      # プロジェクト（特定のブランチのみ）
      - ~/projects/secure-app:/repos/secure-app:rw

      # SSH（読み取り専用）
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro

      # Git設定（読み取り専用）
      - ~/.gitconfig:/home/appuser/.gitconfig:ro

    environment:
      - PORT=3000
      - HOST=0.0.0.0

    user: "${UID:-1000}:${GID:-1000}"

    # セキュリティ強化
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true

    tmpfs:
      - /tmp:size=100M,mode=1777

    # リソース制限
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

    # ネットワーク隔離
    networks:
      - secure-network

networks:
  secure-network:
    driver: bridge
    internal: false  # GitHubなどへのアクセスが必要
```

---

## トラブルシューティング

### 問題1: ファイルが読み書きできない

**症状**:
```
Permission denied: '/repos/my-project/file.txt'
```

**解決**:

```bash
# UID/GIDを確認
id

# コンテナのユーザーを調整
docker run --user $(id -u):$(id -g) ...

# または、ホストのパーミッションを確認
ls -la ~/projects/my-project
chmod -R u+rw ~/projects/my-project
```

### 問題2: Gitコミットができない

**症状**:
```
*** Please tell me who you are.
```

**解決**:

```bash
# Git設定をマウント
docker run -v ~/.gitconfig:/home/appuser/.gitconfig:ro ...

# または、コンテナ内で設定
docker exec vibe-kanban git config --global user.name "Your Name"
docker exec vibe-kanban git config --global user.email "you@example.com"
```

### 問題3: SSHキーが認識されない

**症状**:
```
Permission denied (publickey).
```

**解決**:

```bash
# SSHエージェントを確認
ssh-add -l

# エージェントをコンテナに渡す
docker run \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  ...

# SSHキーのパーミッションを確認
chmod 600 ~/.ssh/id_rsa
```

### 問題4: プロジェクトが見つからない

**症状**:
```
No such file or directory: '/repos/my-project'
```

**解決**:

```bash
# マウントパスを確認
docker inspect vibe-kanban | grep -A 10 Mounts

# コンテナ内を確認
docker exec vibe-kanban ls -la /repos

# 正しいパスでマウント
docker run -v $(pwd)/my-project:/repos/my-project:rw ...
```

### 問題5: ディスク容量不足

**症状**:
```
No space left on device
```

**解決**:

```bash
# Dockerの使用状況を確認
docker system df

# 不要なコンテナ・イメージ・ボリュームを削除
docker system prune -a --volumes

# tmpfsのサイズを調整
docker run --tmpfs /tmp:size=500M ...
```

### 問題6: パフォーマンスが遅い

**症状**:
ファイル操作が極端に遅い（特にMac/Windows）

**解決**:

```bash
# MacでのDocker Desktop設定
# VirtioFS を有効化（Settings > Experimental Features）

# docker-compose.ymlでcached/delegatedを使用
volumes:
  - ~/projects/my-app:/repos/my-app:cached  # Macで推奨

# または、named volumeを使用
volumes:
  project-data:/repos/my-app

volumes:
  project-data:
```

### 問題7: ファイル変更が検知されない

**症状**:
ホストでファイルを編集してもコンテナが検知しない

**解決**:

これはファイルシステムのイベント通知の問題です。

```yaml
# docker-compose.yml
volumes:
  - ~/projects/my-app:/repos/my-app:rw,consistent  # consistency設定

# または、ポーリングを使用（アプリケーション側の設定）
# 例: webpack.config.js
watchOptions: {
  poll: 1000
}
```

---

## まとめ

### 推奨設定

**開発環境**:
- ホストのUID/GIDを使用（`--user $(id -u):$(id -g)`）
- 必要なプロジェクトのみをマウント
- SSH/Git設定を読み取り専用でマウント
- SSHエージェントフォワーディングを使用

**本番環境**:
- 読み取り専用ルートファイルシステム
- リソース制限を設定
- ネットワークポリシーを適用
- SecretsでGitHub/API認証を管理

### セキュリティチェックリスト

- [ ] 必要最小限のプロジェクトのみマウント
- [ ] SSH鍵は読み取り専用でマウント
- [ ] Docker socketのマウントは避ける
- [ ] UID/GIDを適切に設定
- [ ] tmpfsを使用して一時ファイルを隔離
- [ ] リソース制限を設定
- [ ] 定期的に`security-check.sh`を実行

### クイックスタート

```bash
# 1. プロジェクトディレクトリに移動
cd ~/projects/my-app

# 2. vibe-kanbanを起動
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v $(pwd):/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest

# 3. ブラウザでアクセス
# http://localhost:3000

# 4. 作業完了後、停止・削除
docker stop vibe-kanban
docker rm vibe-kanban
```

これで、vibe-kanbanを使って実際のプロジェクトで作業できるようになります！
