# ホストから認証情報を引き継ぐ方法

vibe-kanbanをコンテナで実行する際に、ホストシステムの認証情報を安全に引き継ぐ方法を説明します。

## 目次

1. [SSHキーの引き継ぎ](#sshキーの引き継ぎ)
2. [Git認証情報](#git認証情報)
3. [GitHub OAuth](#github-oauth)
4. [環境変数](#環境変数)
5. [Docker Secrets](#docker-secrets)
6. [Kubernetes Secrets](#kubernetes-secrets)
7. [セキュリティベストプラクティス](#セキュリティベストプラクティス)

---

## SSHキーの引き継ぎ

vibe-kanbanはリモートサーバーとのSSH接続をサポートしています。ホストのSSHキーをコンテナに安全にマウントする方法を説明します。

### 方法1: SSHエージェントフォワーディング

最もセキュアな方法です。SSHキーをコンテナにコピーせず、ホストのSSHエージェントを経由して認証します。

```bash
# SSHエージェントが起動していることを確認
eval $(ssh-agent -s)

# SSHキーを追加
ssh-add ~/.ssh/id_rsa

# SSHエージェントソケットをマウントしてコンテナを実行
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  vibe-kanban:latest
```

### 方法2: SSHキーをボリュームマウント（読み取り専用）

SSHキーを読み取り専用でマウントします。

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.ssh:/home/appuser/.ssh:ro \
  vibe-kanban:latest
```

**注意**: この方法は秘密鍵をコンテナに公開するため、コンテナが侵害された場合にリスクがあります。

### 方法3: SSH設定のみをマウント（鍵は別管理）

SSH設定ファイルのみをマウントし、鍵はDocker Secretsで管理します。

```bash
# Docker Secretsを作成
docker secret create ssh_private_key ~/.ssh/id_rsa

# コンテナ実行時にシークレットを使用
docker service create \
  --name vibe-kanban \
  --secret ssh_private_key \
  --publish 3000:3000 \
  vibe-kanban:latest
```

### Docker Composeでの設定例

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"
    volumes:
      # SSH設定（known_hosts、config）
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
      # SSHエージェント
      - $SSH_AUTH_SOCK:/ssh-agent
    environment:
      - SSH_AUTH_SOCK=/ssh-agent
```

---

## Git認証情報

Gitリポジトリへのアクセスに必要な認証情報を引き継ぎます。

### Gitクレデンシャルヘルパー

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  -v ~/.git-credentials:/home/appuser/.git-credentials:ro \
  vibe-kanban:latest
```

### Git設定のみ（HTTPSトークン使用）

```bash
# Gitトークンを環境変数で渡す
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e GIT_USERNAME=your-username \
  -e GIT_TOKEN=ghp_your_token_here \
  vibe-kanban:latest
```

コンテナ内でGitを設定するスクリプト例：

```bash
#!/bin/bash
# entrypoint.sh

if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
  git config --global credential.helper store
  echo "https://${GIT_USERNAME}:${GIT_TOKEN}@github.com" > ~/.git-credentials
fi

exec "$@"
```

---

## GitHub OAuth

vibe-kanbanはGitHub OAuthをサポートしています。

### 環境変数での設定

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e GITHUB_CLIENT_ID=your_client_id \
  -e GITHUB_CLIENT_SECRET=your_client_secret \
  vibe-kanban:latest
```

### .envファイルを使用

```bash
# .env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
POSTHOG_API_KEY=your_posthog_key
```

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --env-file .env \
  vibe-kanban:latest
```

**重要**: `.env`ファイルをGitにコミットしないでください。`.gitignore`に追加してください。

---

## 環境変数

### 環境変数ファイルの構造

`credentials.env`:

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# PostHog Analytics
POSTHOG_API_KEY=your_posthog_key

# Git認証
GIT_USERNAME=your_username
GIT_TOKEN=ghp_your_token

# その他
API_KEY=your_api_key
```

### セキュアな環境変数の読み込み

```bash
# 環境変数ファイルの権限を制限
chmod 600 credentials.env

# コンテナ実行時に読み込み
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --env-file credentials.env \
  vibe-kanban:latest
```

---

## Docker Secrets

本番環境では、Docker Secretsを使用して認証情報を管理します。

### Swarmモードでの使用

```bash
# Swarmの初期化（まだの場合）
docker swarm init

# シークレットの作成
echo "your_github_client_id" | docker secret create github_client_id -
echo "your_github_client_secret" | docker secret create github_client_secret -
echo "your_posthog_api_key" | docker secret create posthog_api_key -

# サービスの作成
docker service create \
  --name vibe-kanban \
  --secret github_client_id \
  --secret github_client_secret \
  --secret posthog_api_key \
  --publish 3000:3000 \
  vibe-kanban:latest
```

### Docker Composeでの使用

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"
    secrets:
      - github_client_id
      - github_client_secret
      - posthog_api_key
    environment:
      - GITHUB_CLIENT_ID_FILE=/run/secrets/github_client_id
      - GITHUB_CLIENT_SECRET_FILE=/run/secrets/github_client_secret
      - POSTHOG_API_KEY_FILE=/run/secrets/posthog_api_key

secrets:
  github_client_id:
    file: ./secrets/github_client_id.txt
  github_client_secret:
    file: ./secrets/github_client_secret.txt
  posthog_api_key:
    file: ./secrets/posthog_api_key.txt
```

アプリケーション側でシークレットファイルを読み込むコード例：

```javascript
// secrets.js
const fs = require('fs');

function loadSecret(envVar, filePath) {
  if (process.env[envVar]) {
    return process.env[envVar];
  }

  if (process.env[envVar + '_FILE']) {
    const secretPath = process.env[envVar + '_FILE'];
    return fs.readFileSync(secretPath, 'utf8').trim();
  }

  return null;
}

module.exports = {
  githubClientId: loadSecret('GITHUB_CLIENT_ID', '/run/secrets/github_client_id'),
  githubClientSecret: loadSecret('GITHUB_CLIENT_SECRET', '/run/secrets/github_client_secret'),
  posthogApiKey: loadSecret('POSTHOG_API_KEY', '/run/secrets/posthog_api_key')
};
```

---

## Kubernetes Secrets

Kubernetesでの認証情報管理方法です。

### Secretの作成

```bash
# コマンドラインから作成
kubectl create secret generic vibe-kanban-secrets \
  --from-literal=github-client-id=your_client_id \
  --from-literal=github-client-secret=your_client_secret \
  --from-literal=posthog-api-key=your_api_key \
  -n default

# ファイルから作成
kubectl create secret generic vibe-kanban-ssh-key \
  --from-file=id_rsa=~/.ssh/id_rsa \
  --from-file=id_rsa.pub=~/.ssh/id_rsa.pub \
  -n default

# Git認証情報
kubectl create secret generic vibe-kanban-git-creds \
  --from-file=.gitconfig=~/.gitconfig \
  --from-literal=git-token=ghp_your_token \
  -n default
```

### Deployment での使用

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
        - name: GITHUB_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-secrets
              key: github-client-id
        - name: GITHUB_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-secrets
              key: github-client-secret
        - name: POSTHOG_API_KEY
          valueFrom:
            secretKeyRef:
              name: vibe-kanban-secrets
              key: posthog-api-key

        volumeMounts:
        # SSHキーをボリュームとしてマウント
        - name: ssh-key
          mountPath: /home/appuser/.ssh
          readOnly: true
        # Git設定
        - name: git-config
          mountPath: /home/appuser/.gitconfig
          subPath: .gitconfig
          readOnly: true

      volumes:
      - name: ssh-key
        secret:
          secretName: vibe-kanban-ssh-key
          defaultMode: 0400  # 読み取り専用
      - name: git-config
        secret:
          secretName: vibe-kanban-git-creds
```

### 外部シークレット管理ツールとの連携

より高度なシークレット管理には、以下のツールを検討してください：

#### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vibe-kanban-external-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: vibe-kanban-secrets
    creationPolicy: Owner
  data:
  - secretKey: github-client-id
    remoteRef:
      key: vibe-kanban/github-client-id
  - secretKey: github-client-secret
    remoteRef:
      key: vibe-kanban/github-client-secret
```

#### Sealed Secrets

```bash
# Sealed Secretの作成
kubectl create secret generic vibe-kanban-secrets \
  --from-literal=github-client-id=your_client_id \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# 適用
kubectl apply -f sealed-secret.yaml
```

---

## セキュリティベストプラクティス

### 1. 最小権限の原則

```bash
# 読み取り専用でマウント
-v ~/.ssh:/home/appuser/.ssh:ro

# 必要なファイルのみマウント
-v ~/.ssh/config:/home/appuser/.ssh/config:ro
-v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
```

### 2. 認証情報のライフサイクル管理

```bash
# 短命なトークンを使用
# GitHub: Personal Access Tokenに有効期限を設定
# AWS: 一時的な認証情報（STS）を使用

# 定期的にローテーション
# Kubernetes CronJobで自動更新
```

### 3. 監査ログ

```bash
# Docker監査
docker events --filter 'type=container' --format '{{json .}}'

# Kubernetesの監査ログを有効化
# kube-apiserver設定で audit policy を設定
```

### 4. シークレットの暗号化

```bash
# Dockerでの暗号化（LUKS）
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb docker-secrets
mkfs.ext4 /dev/mapper/docker-secrets
mount /dev/mapper/docker-secrets /var/lib/docker/secrets

# Kubernetesでの暗号化
# kube-apiserver設定
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml
```

`encryption-config.yaml`:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-secret>
    - identity: {}
```

### 5. ネットワーク隔離

```bash
# 認証情報を持つコンテナは隔離されたネットワークで実行
docker network create --internal secure-network

docker run -d \
  --name vibe-kanban \
  --network secure-network \
  -p 3000:3000 \
  vibe-kanban:latest
```

### 6. イメージスキャン

```bash
# 認証情報が誤ってイメージに含まれていないかチェック
trivy image vibe-kanban:latest --scanners secret

# GitLeaksでスキャン
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source /path
```

### 7. 環境変数の検証

```bash
# .envファイルに認証情報が含まれていないか確認
grep -r "password\|secret\|key\|token" .env

# Gitにコミットされていないか確認
git log --all --full-history -- .env
```

### 8. 実行時のチェック

```bash
# コンテナ内の認証情報を確認
docker exec vibe-kanban env | grep -i "secret\|password\|key"

# ファイルシステムをチェック
docker exec vibe-kanban find /home -name "*key*" -o -name "*credentials*"
```

---

## 実装例

### 完全な例: セキュアな認証情報管理

`docker-compose.secure.yml`:

```yaml
version: '3.8'

services:
  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3000:3000"

    # 環境変数（機密性の低い設定）
    environment:
      - PORT=3000
      - HOST=0.0.0.0

    # Docker Secrets（機密性の高い情報）
    secrets:
      - github_client_id
      - github_client_secret
      - posthog_api_key
      - ssh_private_key

    # ボリュームマウント（設定ファイルのみ）
    volumes:
      - ~/.ssh/config:/home/appuser/.ssh/config:ro
      - ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
      - ~/.gitconfig:/home/appuser/.gitconfig:ro

    # セキュリティ設定
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true

    # ネットワーク隔離
    networks:
      - secure-network

secrets:
  github_client_id:
    file: ./secrets/github_client_id.txt
  github_client_secret:
    file: ./secrets/github_client_secret.txt
  posthog_api_key:
    file: ./secrets/posthog_api_key.txt
  ssh_private_key:
    file: ~/.ssh/id_rsa

networks:
  secure-network:
    driver: bridge
    internal: false  # 外部アクセスが必要な場合
```

### スタートアップスクリプト

`entrypoint.sh`:

```bash
#!/bin/sh
set -e

# Docker Secretsから環境変数を設定
if [ -f /run/secrets/github_client_id ]; then
  export GITHUB_CLIENT_ID=$(cat /run/secrets/github_client_id)
fi

if [ -f /run/secrets/github_client_secret ]; then
  export GITHUB_CLIENT_SECRET=$(cat /run/secrets/github_client_secret)
fi

if [ -f /run/secrets/posthog_api_key ]; then
  export POSTHOG_API_KEY=$(cat /run/secrets/posthog_api_key)
fi

# SSHキーのパーミッション設定
if [ -f /run/secrets/ssh_private_key ]; then
  mkdir -p ~/.ssh
  cp /run/secrets/ssh_private_key ~/.ssh/id_rsa
  chmod 600 ~/.ssh/id_rsa
fi

# アプリケーションの起動
exec "$@"
```

---

## トラブルシューティング

### SSHキーの権限エラー

```bash
# エラー: Permissions 0644 for '/home/appuser/.ssh/id_rsa' are too open
# 解決: マウント時に適切な権限を設定

docker run -d \
  --name vibe-kanban \
  -v ~/.ssh/id_rsa:/home/appuser/.ssh/id_rsa:ro \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest

# または、entrypoint.shで権限を修正
chmod 600 ~/.ssh/id_rsa
```

### 環境変数が認識されない

```bash
# デバッグ: コンテナ内の環境変数を確認
docker exec vibe-kanban env

# 環境変数が設定されているか確認
docker inspect vibe-kanban | jq '.[0].Config.Env'
```

### シークレットが読み込めない

```bash
# Kubernetes: シークレットが存在するか確認
kubectl get secrets -n default

# シークレットの内容を確認（デバッグ用）
kubectl get secret vibe-kanban-secrets -o yaml | grep -A 10 data

# マウントが正しいか確認
kubectl describe pod <pod-name>
```

---

## まとめ

認証情報を安全に引き継ぐための重要なポイント：

1. **SSHエージェントフォワーディング**を優先的に使用
2. 秘密鍵は**読み取り専用**でマウント
3. 本番環境では**Docker Secrets**または**Kubernetes Secrets**を使用
4. 環境変数ファイル（.env）は**Gitにコミットしない**
5. **最小権限の原則**を適用
6. 定期的に認証情報を**ローテーション**
7. **監査ログ**を有効化
8. **イメージスキャン**で認証情報の漏洩をチェック

これらのベストプラクティスに従うことで、vibe-kanbanを安全にコンテナ環境で運用できます。
