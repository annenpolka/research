# vibe-kanban SSH接続セットアップガイド

## 概要

このガイドでは、vibe-kanbanコンテナからリモートサーバーやGitリポジトリにSSH接続する方法を説明します。

## SSH接続が必要な場面

vibe-kanbanで以下の操作を行う際にSSH接続が必要になります：

- **リモートGitリポジトリへのアクセス** (git@github.com:user/repo.git)
- **リモートサーバーへのデプロイ**
- **SSH経由でのファイル転送** (scp, rsync)
- **コンテナ内からのリモートサーバー操作**

## 方法の比較

| 方法 | セキュリティ | 設定の簡単さ | 推奨度 | 用途 |
|------|--------------|--------------|--------|------|
| **方法1: SSHエージェントフォワーディング** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 🏆 最推奨 | 本番・開発 |
| **方法2: SSH設定のみマウント** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 👍 推奨 | 開発環境 |
| **方法3: SSH鍵をマウント** | ⭐⭐ | ⭐⭐⭐⭐ | ⚠️ 注意 | テスト用のみ |

---

## 方法1: SSHエージェントフォワーディング（最推奨）

### 特徴

✅ **メリット**:
- 秘密鍵がコンテナにコピーされない（最もセキュア）
- ホストのSSHエージェントを通じて認証
- コンテナが侵害されても鍵は漏洩しない

❌ **デメリット**:
- SSHエージェントの起動が必要
- 設定が少し複雑

### セットアップ手順

#### 1. SSHエージェントの起動と鍵の追加

```bash
# SSHエージェントを起動
eval $(ssh-agent -s)

# SSH鍵を追加
ssh-add ~/.ssh/id_rsa

# 追加された鍵を確認
ssh-add -l
```

**出力例**:
```
Agent pid 12345
Identity added: /home/user/.ssh/id_rsa (user@hostname)
2048 SHA256:xxx... /home/user/.ssh/id_rsa (RSA)
```

#### 2. SSH_AUTH_SOCK環境変数の確認

```bash
echo $SSH_AUTH_SOCK
```

**出力例**:
```
/tmp/ssh-XXXXXX/agent.12345
```

この値が空でないことを確認してください。

#### 3. コンテナの起動（SSHエージェント付き）

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

#### 4. 動作確認

```bash
# コンテナ内でSSH接続をテスト
docker exec vibe-kanban ssh -T git@github.com
```

**成功時の出力例**:
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 便利スクリプトの使用

`start-with-project.sh` は自動的にSSHエージェントフォワーディングを設定します：

```bash
./start-with-project.sh ~/projects/my-app
```

このスクリプトは：
- `SSH_AUTH_SOCK`が設定されているか確認
- 自動的にSSHエージェントをマウント
- SSH設定とknown_hostsもマウント

---

## 方法2: SSH設定のみマウント（推奨）

### 特徴

✅ **メリット**:
- 設定が簡単
- known_hostsとconfigが使える
- SSHエージェントと組み合わせて使用可能

❌ **デメリット**:
- SSH鍵は別途管理が必要
- エージェントフォワーディングと併用するのが一般的

### セットアップ手順

#### 1. SSH設定ファイルの確認

```bash
# SSH設定ファイルが存在するか確認
ls -la ~/.ssh/

# 主要なファイル:
# - config: SSH接続設定
# - known_hosts: 接続済みホストの公開鍵
```

#### 2. コンテナの起動（SSH設定のみ）

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

**重要**: この方法は通常、SSHエージェントフォワーディング（方法1）と組み合わせて使用します。

---

## 方法3: SSH鍵をマウント（テスト用のみ）

### 特徴

⚠️ **セキュリティ警告**:
- 秘密鍵がコンテナ内に公開される
- コンテナが侵害された場合、鍵が漏洩するリスク
- **本番環境では絶対に使用しないでください**

✅ **メリット**:
- 設定が最も簡単
- SSHエージェント不要

❌ **デメリット**:
- セキュリティリスクが高い
- 鍵のパーミッション問題が発生しやすい

### セットアップ手順（テスト環境のみ）

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh:/home/appuser/.ssh:ro \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

**注意**:
- `:ro` (read-only) フラグを必ず付ける
- テスト用の鍵を使用する
- 本番環境の鍵は絶対に使用しない

---

## トラブルシューティング

### 問題1: Permission denied (publickey)

**症状**:
```
Permission denied (publickey).
fatal: Could not read from remote repository.
```

**解決策**:

#### A. SSHエージェントが起動しているか確認

```bash
# ホスト側
echo $SSH_AUTH_SOCK
ssh-add -l

# コンテナ内
docker exec vibe-kanban sh -c 'echo $SSH_AUTH_SOCK'
docker exec vibe-kanban ssh-add -l
```

#### B. SSH鍵が追加されているか確認

```bash
ssh-add -l

# 鍵がない場合は追加
ssh-add ~/.ssh/id_rsa
```

#### C. GitHub/GitLabの公開鍵を確認

```bash
# GitHubに公開鍵が登録されているか確認
cat ~/.ssh/id_rsa.pub

# GitHubの設定ページで確認
# https://github.com/settings/keys
```

### 問題2: Permissions are too open

**症状**:
```
Permissions 0644 for '/home/appuser/.ssh/id_rsa' are too open.
```

**原因**: SSH鍵のパーミッションが緩すぎる

**解決策**:

#### 方法A: ホスト側でパーミッション修正

```bash
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

#### 方法B: Docker Secretsを使用（本番環境）

```bash
# Swarmモードでシークレットを作成
docker secret create ssh_private_key ~/.ssh/id_rsa

# サービスで使用
docker service create \
  --name vibe-kanban \
  --secret ssh_private_key \
  --publish 3000:3000 \
  vibe-kanban:latest
```

### 問題3: Host key verification failed

**症状**:
```
Host key verification failed.
fatal: Could not read from remote repository.
```

**原因**: known_hostsにホストの公開鍵が登録されていない

**解決策**:

#### 方法A: ホスト側で接続してknown_hostsに追加

```bash
# 一度接続してknown_hostsに追加
ssh -T git@github.com
```

#### 方法B: known_hostsをマウント

```bash
docker run -d \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  ...
```

#### 方法C: StrictHostKeyCheckingを無効化（テスト用のみ）

⚠️ **セキュリティ警告**: 本番環境では使用しないでください

```bash
# ~/.ssh/config に追加
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
```

### 問題4: SSH_AUTH_SOCKが設定されていない

**症状**:
```
Could not open a connection to your authentication agent.
```

**解決策**:

```bash
# SSHエージェントを起動
eval $(ssh-agent -s)

# SSH鍵を追加
ssh-add ~/.ssh/id_rsa

# 環境変数を確認
echo $SSH_AUTH_SOCK
```

---

## 実践例

### 例1: GitHubリポジトリをクローン

```bash
# 1. SSHエージェントのセットアップ
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# 2. コンテナ起動
./start-with-project.sh ~/projects

# 3. コンテナ内でGitリポジトリをクローン
docker exec -it vibe-kanban sh
cd /repos
git clone git@github.com:user/repo.git
```

### 例2: リモートサーバーにSSH接続

```bash
# 1. SSH設定ファイルを作成
cat > ~/.ssh/config <<EOF
Host myserver
    HostName 192.168.1.100
    User myuser
    Port 22
    IdentityFile ~/.ssh/id_rsa
EOF

# 2. コンテナ起動（SSH設定をマウント）
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro \
  -v $SSH_AUTH_SOCK:/ssh-agent \
  -e SSH_AUTH_SOCK=/ssh-agent \
  vibe-kanban:latest

# 3. コンテナ内からSSH接続
docker exec -it vibe-kanban ssh myserver
```

### 例3: 複数のGitホストを使用

```bash
# ~/.ssh/config
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/id_rsa_gitlab

Host bitbucket.org
    HostName bitbucket.org
    User git
    IdentityFile ~/.ssh/id_rsa_bitbucket
```

```bash
# 各鍵をSSHエージェントに追加
ssh-add ~/.ssh/id_rsa_github
ssh-add ~/.ssh/id_rsa_gitlab
ssh-add ~/.ssh/id_rsa_bitbucket

# コンテナ起動
./start-with-project.sh ~/projects
```

---

## セキュリティベストプラクティス

### 1. SSH鍵の管理

```bash
# 専用の鍵を作成（パスフレーズ付き推奨）
ssh-keygen -t ed25519 -C "vibe-kanban@example.com" -f ~/.ssh/id_ed25519_vibe

# 鍵のパーミッションを設定
chmod 600 ~/.ssh/id_ed25519_vibe
chmod 644 ~/.ssh/id_ed25519_vibe.pub
```

### 2. SSHエージェントのタイムアウト設定

```bash
# 1時間後にエージェントから鍵を削除
ssh-add -t 3600 ~/.ssh/id_rsa
```

### 3. 読み取り専用マウント

```bash
# 必ずread-only (:ro) でマウント
-v ~/.ssh/config:/home/appuser/.ssh/config:ro
-v ~/.ssh/known_hosts:/home/appuser/.ssh/known_hosts:ro
```

### 4. Docker Secretsの使用（本番環境）

詳細は **[CREDENTIALS.md](CREDENTIALS.md)** を参照してください。

---

## よくある質問（FAQ）

### Q1: SSHエージェントとSSH鍵マウントの違いは？

**A**:

| 項目 | SSHエージェント | SSH鍵マウント |
|------|----------------|---------------|
| 秘密鍵の場所 | ホストのみ | コンテナ内にも存在 |
| セキュリティ | 高い | 低い |
| 設定の複雑さ | やや複雑 | 簡単 |

**推奨**: SSHエージェントフォワーディングを使用してください。

### Q2: パスフレーズ付き鍵の使用方法は？

**A**: SSHエージェントに追加する際にパスフレーズを入力します：

```bash
ssh-add ~/.ssh/id_rsa
# Enter passphrase for /home/user/.ssh/id_rsa:
```

一度追加すれば、コンテナからの接続時にパスフレーズは不要です。

### Q3: 複数のプロジェクトで異なる鍵を使いたい

**A**: `~/.ssh/config` で鍵を指定します：

```
Host project-a-github
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_project_a

Host project-b-github
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_project_b
```

### Q4: WSL2でSSHエージェントが動かない

**A**: WSL2では、Windows側のSSHエージェントを使用できます：

```bash
# WSL2でWindows側のSSHエージェントを使用
export SSH_AUTH_SOCK=/mnt/c/Users/YourName/.ssh/ssh-agent.sock
```

または、WSL2でSSHエージェントを起動：

```bash
# .bashrc または .zshrc に追加
eval $(ssh-agent -s) > /dev/null
ssh-add ~/.ssh/id_rsa 2>/dev/null
```

---

## まとめ

### 推奨設定（開発環境）

```bash
# 1. SSHエージェントのセットアップ
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# 2. 便利スクリプトで起動
./start-with-project.sh ~/projects/my-app

# 3. 動作確認
docker exec vibe-kanban ssh -T git@github.com
```

### 推奨設定（本番環境）

- Docker Swarm SecretsまたはKubernetes Secretsを使用
- SSHエージェントフォワーディングのみ
- 読み取り専用マウント
- 詳細は **[CREDENTIALS.md](CREDENTIALS.md)** を参照

---

## 関連ドキュメント

- **[CREDENTIALS.md](CREDENTIALS.md)** - 認証情報の包括的な管理ガイド
- **[QUICKSTART.md](QUICKSTART.md)** - 5分で始めるクイックスタート
- **[PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md)** - プロジェクト管理の詳細
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - トラブルシューティング

---

**これでvibe-kanbanでSSH接続が使えるようになりました！** 🎉
