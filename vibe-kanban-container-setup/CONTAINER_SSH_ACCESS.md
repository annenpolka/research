# vibe-kanbanコンテナへのアクセス方法

## 概要

vibe-kanbanコンテナ内部にアクセスする方法について説明します。

**重要**: 通常、Dockerコンテナに直接SSH接続する必要はありません。`docker exec`の使用を強く推奨します。

## 推奨方法: `docker exec`を使用

### シェルでコンテナに入る

```bash
# アルパインベースなので sh を使用
docker exec -it vibe-kanban sh

# コンテナ内で自由にコマンド実行
# pwd
# ls -la
# cd /repos
# git status
```

### 特定のコマンドを実行

```bash
# リポジトリ一覧を確認
docker exec vibe-kanban ls -la /repos

# Gitステータスを確認
docker exec vibe-kanban git -C /repos/my-project status

# プロセス一覧
docker exec vibe-kanban ps aux

# 環境変数を確認
docker exec vibe-kanban env
```

### ユーザーを指定して実行

```bash
# rootユーザーとして実行
docker exec -u root -it vibe-kanban sh

# 特定のユーザーとして実行
docker exec -u appuser -it vibe-kanban sh
```

---

## SSH接続する方法（非推奨）

⚠️ **警告**: 以下の方法は推奨されません。セキュリティリスクがあり、Docker Composeの自動再起動で設定が失われます。

### なぜSSH接続が非推奨か

1. **セキュリティリスク**: コンテナにSSHサーバーを追加すると攻撃対象が増える
2. **コンテナの原則に反する**: 1コンテナ1プロセスの原則に反する
3. **メンテナンスコスト**: SSH鍵管理、ポート管理が複雑化
4. **`docker exec`で十分**: ほとんどのユースケースは`docker exec`で対応可能

### それでもSSH接続したい場合

#### 方法A: カスタムDockerfileを作成

```dockerfile
# Dockerfile.ssh
FROM vibe-kanban:latest

# SSHサーバーのインストール
RUN apk add --no-cache openssh-server

# SSHディレクトリの作成
RUN mkdir -p /run/sshd && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# SSH設定
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config && \
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config

# SSH鍵の追加（ビルド時に自分の公開鍵を配置）
# COPY id_rsa.pub /root/.ssh/authorized_keys
# RUN chmod 600 /root/.ssh/authorized_keys

# SSH用のポートを公開
EXPOSE 22

# エントリーポイントを変更してSSHサーバーを起動
COPY entrypoint-ssh.sh /entrypoint-ssh.sh
RUN chmod +x /entrypoint-ssh.sh

ENTRYPOINT ["/entrypoint-ssh.sh"]
```

**entrypoint-ssh.sh**:
```bash
#!/bin/sh
set -e

# SSH鍵の生成（初回のみ）
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# SSHサーバーを起動
/usr/sbin/sshd

# 元のアプリケーションを起動
exec /original-entrypoint "$@"
```

#### 方法B: 実行中のコンテナにSSHサーバーを追加

```bash
# コンテナ内でSSHサーバーをインストール
docker exec -u root vibe-kanban apk add --no-cache openssh-server

# SSH設定
docker exec -u root vibe-kanban mkdir -p /run/sshd
docker exec -u root vibe-kanban mkdir -p /root/.ssh
docker exec -u root vibe-kanban chmod 700 /root/.ssh

# 公開鍵を追加
docker cp ~/.ssh/id_rsa.pub vibe-kanban:/root/.ssh/authorized_keys
docker exec -u root vibe-kanban chmod 600 /root/.ssh/authorized_keys

# SSH設定ファイルを編集
docker exec -u root vibe-kanban sh -c 'echo "PermitRootLogin yes" >> /etc/ssh/sshd_config'
docker exec -u root vibe-kanban sh -c 'echo "PasswordAuthentication no" >> /etc/ssh/sshd_config'

# SSH鍵を生成
docker exec -u root vibe-kanban ssh-keygen -A

# SSHサーバーを起動
docker exec -u root -d vibe-kanban /usr/sbin/sshd

# SSHポートをホストにマッピング（コンテナを再起動）
docker stop vibe-kanban
docker commit vibe-kanban vibe-kanban:ssh
docker rm vibe-kanban
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -p 2222:22 \
  vibe-kanban:ssh
```

#### SSH接続

```bash
# ホストからSSH接続
ssh -p 2222 root@localhost

# リモートからSSH接続
ssh -p 2222 root@your-server-ip
```

---

## 実用的なユースケース

### 1. ログの確認

```bash
# docker exec を使用（推奨）
docker logs -f vibe-kanban

# コンテナ内のログファイルを確認
docker exec vibe-kanban cat /var/log/app.log
```

### 2. デバッグ

```bash
# インタラクティブシェル
docker exec -it vibe-kanban sh

# コンテナ内で:
ps aux
top
netstat -tlnp
```

### 3. ファイルの編集

```bash
# ホストからコンテナにファイルをコピー
docker cp local-file.txt vibe-kanban:/path/to/file.txt

# コンテナからホストにファイルをコピー
docker cp vibe-kanban:/path/to/file.txt ./local-file.txt

# viエディタでファイルを編集
docker exec -it vibe-kanban vi /path/to/file.txt
```

### 4. パッケージのインストール

```bash
# 一時的にパッケージをインストール
docker exec -u root vibe-kanban apk add --no-cache curl

# インストールしたパッケージを使用
docker exec vibe-kanban curl http://example.com
```

### 5. プロセスの監視

```bash
# プロセス一覧
docker exec vibe-kanban ps aux

# リアルタイム監視
docker exec -it vibe-kanban top

# ネットワーク接続
docker exec vibe-kanban netstat -tlnp
```

---

## VS Code Dev Containers（代替方法）

SSH接続ではなく、VS Code Dev Containersを使用する方法もあります：

### 前提条件

1. VS Codeに「Dev Containers」拡張機能をインストール
2. Dockerが起動していること

### 手順

1. **VS Codeでコマンドパレットを開く**: `Ctrl+Shift+P`
2. **"Dev Containers: Attach to Running Container..."** を選択
3. **vibe-kanbanコンテナを選択**
4. 新しいVS Codeウィンドウでコンテナ内が開く

### メリット

- ✅ SSH設定不要
- ✅ VS Codeの全機能が使える
- ✅ ファイルブラウザ、ターミナル、デバッガーが統合
- ✅ セキュア

```bash
# または、VS Code CLIから直接接続
code --remote attached-container+vibe-kanban
```

---

## Docker Composeでの管理コマンド

```bash
# コンテナに入る
docker-compose exec vibe-kanban sh

# 特定のコマンドを実行
docker-compose exec vibe-kanban ls -la /repos

# ログを確認
docker-compose logs -f vibe-kanban

# コンテナを再起動
docker-compose restart vibe-kanban
```

---

## トラブルシューティング

### 問題1: `docker exec`が動かない

**症状**: "Error: No such container"

**解決策**:

```bash
# コンテナが起動しているか確認
docker ps

# 停止中のコンテナも含めて確認
docker ps -a

# コンテナ名を確認して再実行
docker exec -it <実際のコンテナ名> sh
```

### 問題2: 権限エラー

**症状**: "Permission denied"

**解決策**:

```bash
# rootユーザーとして実行
docker exec -u root -it vibe-kanban sh

# コンテナ内でユーザーを確認
docker exec vibe-kanban whoami
```

### 問題3: コンテナ内にviやnanoがない

**症状**: エディタがインストールされていない

**解決策**:

```bash
# viをインストール
docker exec -u root vibe-kanban apk add --no-cache vim

# または、ホストで編集してコピー
vi local-file.txt
docker cp local-file.txt vibe-kanban:/path/to/file.txt
```

---

## まとめ

### 推奨される方法

| ユースケース | 推奨方法 | コマンド例 |
|-------------|---------|-----------|
| **シェルに入る** | `docker exec -it` | `docker exec -it vibe-kanban sh` |
| **コマンド実行** | `docker exec` | `docker exec vibe-kanban ls /repos` |
| **ログ確認** | `docker logs` | `docker logs -f vibe-kanban` |
| **ファイル転送** | `docker cp` | `docker cp file.txt vibe-kanban:/path` |
| **VS Codeで編集** | Dev Containers拡張 | VS Codeから接続 |

### SSH接続が必要な場合

ほとんどのケースで`docker exec`で十分ですが、どうしてもSSH接続が必要な場合：

1. **開発環境**: VS Code Dev Containersを使用
2. **本番環境**: SSH bastion経由でDockerホストに接続後、`docker exec`を使用
3. **特殊なケース**: カスタムDockerfileでSSHサーバーを追加（非推奨）

### ベストプラクティス

- ✅ `docker exec`を優先的に使用
- ✅ ログは`docker logs`で確認
- ✅ ファイル操作は`docker cp`を使用
- ✅ VS Code使用時はDev Containers拡張を活用
- ❌ コンテナにSSHサーバーを追加しない
- ❌ コンテナ内で複数プロセスを起動しない

---

## 関連ドキュメント

- **[SSH_SETUP.md](SSH_SETUP.md)** - コンテナからのSSH接続、エディタ統合SSH接続
- **[QUICKSTART.md](QUICKSTART.md)** - vibe-kanbanのクイックスタート
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - トラブルシューティング

---

**`docker exec`でほとんどのケースに対応できます！** 🐳
