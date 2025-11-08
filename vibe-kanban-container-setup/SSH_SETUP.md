# vibe-kanban SSH接続セットアップガイド

## 概要

このガイドでは、vibe-kanbanでのSSH接続について2つの用途を説明します：

1. **コンテナからのSSH接続** - GitリポジトリやリモートサーバーへのSSH接続
2. **エディタ統合でのSSH接続** - ローカルVSCodeからリモートサーバー上のプロジェクトへの接続

## SSH接続が必要な場面

vibe-kanbanで以下の操作を行う際にSSH接続が必要になります：

### 1. コンテナからのSSH接続

- **リモートGitリポジトリへのアクセス** (git@github.com:user/repo.git)
- **リモートサーバーへのデプロイ**
- **SSH経由でのファイル転送** (scp, rsync)
- **コンテナ内からのリモートサーバー操作**

### 2. エディタ統合でのSSH接続

- **VSCode Remote-SSH** - ローカルVSCodeでリモートサーバー上のプロジェクトを編集
- **リモート開発環境** - vibe-kanbanがリモートVPS/クラウドインスタンスで動作している場合

## 方法の比較（コンテナからのSSH接続）

**注**: この比較表は「コンテナからのSSH接続」用です。エディタ統合については[こちら](#エディタ統合でのリモートssh接続)を参照してください。

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

## エディタ統合でのリモートSSH接続

vibe-kanbanはVSCode Remote-SSHとの統合をサポートしており、リモートサーバー上で動作するvibe-kanbanのプロジェクトをローカルのVSCodeで編集できます。

### ユースケース

この機能は以下の場合に便利です：

- **リモートVPSでvibe-kanbanを実行** - クラウド上のサーバーでvibe-kanbanを動かし、ローカルから編集
- **強力なリモートマシンを使用** - GPU搭載サーバーなど、ローカルより高性能な環境で開発
- **チーム開発** - 共有サーバー上のプロジェクトを複数人で編集

### 前提条件

#### 1. ホストマシン（ローカルPC）

```bash
# VSCode Remote-SSH拡張機能をインストール
# VSCodeで: Ctrl+Shift+X → "Remote - SSH" を検索してインストール
```

#### 2. リモートサーバー

```bash
# SSHサーバーが起動していることを確認
sudo systemctl status sshd

# vibe-kanbanが起動していること
docker ps | grep vibe-kanban
```

#### 3. SSH鍵の設定

```bash
# ローカルPCからリモートサーバーへのSSH接続を設定

# 1. SSH鍵を生成（まだない場合）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 公開鍵をリモートサーバーにコピー
ssh-copy-id user@remote-server.com

# 3. 接続テスト
ssh user@remote-server.com
```

### vibe-kanbanでの設定

#### ステップ1: Global Settingsを開く

1. vibe-kanban UIで、サイドバーの⚙️アイコンをクリック
2. または、右上のメニューから「Settings」を選択

#### ステップ2: Remote SSH設定を入力

**Remote SSH Host**:
- サーバーのホスト名またはIPアドレスを入力
- 例: `example.com`, `192.168.1.100`, `my-vps.cloud.com`

**Remote SSH User**:
- SSH接続に使用するユーザー名を入力
- 例: `ubuntu`, `user`, `root`

**設定例**:
```
Remote SSH Host: vps.example.com
Remote SSH User: ubuntu
```

#### ステップ3: プロジェクトをVSCodeで開く

1. vibe-kanban UIでプロジェクトを選択
2. "Open in VSCode"ボタンをクリック
3. VSCodeが自動的に起動し、以下のようなURLを使用してリモート接続：
   ```
   vscode://vscode-remote/ssh-remote+ubuntu@vps.example.com/repos/my-project
   ```

### トラブルシューティング（エディタ統合）

#### 問題1: VSCodeが起動しない

**症状**: "Open in VSCode"をクリックしても何も起こらない

**解決策**:

```bash
# 1. VSCodeがインストールされているか確認
code --version

# 2. Remote-SSH拡張機能がインストールされているか確認
# VSCodeで: Ctrl+Shift+X → "Remote - SSH"

# 3. プロトコルハンドラーが登録されているか確認（Linux）
xdg-mime query default x-scheme-handler/vscode
```

#### 問題2: SSH接続が失敗する

**症状**: VSCodeがリモートサーバーに接続できない

**解決策**:

```bash
# 1. SSHの設定を確認
cat ~/.ssh/config

# 2. Host設定を追加
cat >> ~/.ssh/config <<EOF
Host vps.example.com
    HostName vps.example.com
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
EOF

# 3. 接続テスト
ssh ubuntu@vps.example.com
```

#### 問題3: プロジェクトパスが見つからない

**症状**: VSCodeで"Folder does not exist"エラー

**原因**: vibe-kanbanのGlobal Settingsで設定したホスト/ユーザーと、実際のリモートサーバーのパスが一致していない

**解決策**:

```bash
# リモートサーバーで、vibe-kanbanコンテナのマウントパスを確認
docker inspect vibe-kanban | grep -A 5 Mounts

# 例: /repos/my-project が正しいパスか確認
docker exec vibe-kanban ls -la /repos/
```

### SSH設定の例

#### 例1: 標準的なVPS設定

**~/.ssh/config**:
```
Host my-vps
    HostName 203.0.113.42
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
```

**vibe-kanban Global Settings**:
```
Remote SSH Host: my-vps
Remote SSH User: ubuntu
```

#### 例2: カスタムポートとジャンプホスト

**~/.ssh/config**:
```
Host jumphost
    HostName bastion.example.com
    User admin
    IdentityFile ~/.ssh/id_rsa

Host internal-server
    HostName 10.0.1.100
    User developer
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ProxyJump jumphost
```

**vibe-kanban Global Settings**:
```
Remote SSH Host: internal-server
Remote SSH User: developer
```

#### 例3: 複数の環境

**~/.ssh/config**:
```
Host dev-vibe
    HostName dev.vibe.example.com
    User devuser
    IdentityFile ~/.ssh/id_dev

Host staging-vibe
    HostName staging.vibe.example.com
    User staginguser
    IdentityFile ~/.ssh/id_staging

Host prod-vibe
    HostName prod.vibe.example.com
    User produser
    IdentityFile ~/.ssh/id_prod
```

開発環境、ステージング環境、本番環境ごとにvibe-kanbanの設定を切り替えます。

### セキュリティ上の注意

#### Remote SSH接続のベストプラクティス

1. **専用SSH鍵を使用**
   ```bash
   # vibe-kanban専用の鍵を作成
   ssh-keygen -t ed25519 -C "vibe-kanban-remote" -f ~/.ssh/id_vibe_remote
   ```

2. **SSH設定でセキュリティを強化**
   ```
   Host vibe-remote
       HostName vps.example.com
       User ubuntu
       IdentityFile ~/.ssh/id_vibe_remote
       IdentitiesOnly yes
       ForwardAgent no  # 不要な場合は無効化
       StrictHostKeyChecking yes
   ```

3. **ファイアウォールでSSHポートを保護**
   ```bash
   # 特定のIPからのみSSH接続を許可
   sudo ufw allow from 203.0.113.0/24 to any port 22
   ```

4. **SSH鍵ベースの認証のみ許可**
   ```bash
   # /etc/ssh/sshd_config
   PasswordAuthentication no
   PubkeyAuthentication yes
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

### Q5: エディタ統合でのSSH接続とコンテナからのSSH接続の違いは？

**A**:

| 項目 | コンテナからのSSH接続 | エディタ統合でのSSH接続 |
|------|---------------------|----------------------|
| **目的** | Gitリポジトリやリモートサーバーへのアクセス | ローカルVSCodeでリモートプロジェクトを編集 |
| **接続元** | vibe-kanbanコンテナ内 | ローカルPC上のVSCode |
| **接続先** | GitHub/GitLab/リモートサーバー | vibe-kanbanが動作するリモートサーバー |
| **設定場所** | Docker run/compose設定 | vibe-kanban Global Settings |
| **使用例** | `git clone git@github.com:user/repo.git` | "Open in VSCode"ボタンでリモート編集 |

**具体例**:

- **コンテナからのSSH接続**: vibe-kanbanコンテナ → GitHub (Gitリポジトリのpush/pull)
- **エディタ統合SSH接続**: ローカルVSCode → リモートVPSのvibe-kanban (ファイル編集)

---

## まとめ

### コンテナからのSSH接続（推奨設定）

#### 開発環境

```bash
# 1. SSHエージェントのセットアップ
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# 2. 便利スクリプトで起動
./start-with-project.sh ~/projects/my-app

# 3. 動作確認
docker exec vibe-kanban ssh -T git@github.com
```

#### 本番環境

- Docker Swarm SecretsまたはKubernetes Secretsを使用
- SSHエージェントフォワーディングのみ
- 読み取り専用マウント
- 詳細は **[CREDENTIALS.md](CREDENTIALS.md)** を参照

### エディタ統合でのSSH接続（推奨設定）

#### ローカルPCでの準備

```bash
# 1. VSCode Remote-SSH拡張機能をインストール
# VSCodeで: Ctrl+Shift+X → "Remote - SSH"

# 2. SSH鍵の設定
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-copy-id user@remote-server.com

# 3. ~/.ssh/config に設定を追加
cat >> ~/.ssh/config <<EOF
Host my-vps
    HostName vps.example.com
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
EOF
```

#### vibe-kanban設定

1. vibe-kanban UIで⚙️Settings を開く
2. Remote SSH設定を入力:
   - **Remote SSH Host**: `my-vps` (または `vps.example.com`)
   - **Remote SSH User**: `ubuntu`
3. プロジェクトで"Open in VSCode"をクリック

### 2つのSSH接続の使い分け

- **コンテナからのSSH接続**: Gitリポジトリへのpush/pull、デプロイ操作に使用
- **エディタ統合SSH接続**: リモートサーバー上のvibe-kanbanプロジェクトをローカルVSCodeで編集

---

## 関連ドキュメント

### このプロジェクトのドキュメント

- **[CREDENTIALS.md](CREDENTIALS.md)** - 認証情報の包括的な管理ガイド
- **[QUICKSTART.md](QUICKSTART.md)** - 5分で始めるクイックスタート
- **[PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md)** - プロジェクト管理の詳細
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - トラブルシューティング

### vibe-kanban公式ドキュメント

- **[Global Settings](https://www.vibekanban.com/docs/configuration-customisation/global-settings)** - Remote SSH設定を含むグローバル設定
- **[vibe-kanban Documentation](https://vibekanban.com/docs)** - 公式ドキュメントトップページ

---

**これでvibe-kanbanでSSH接続が使えるようになりました！** 🎉
