# 認証方法の比較ガイド

GitHub Actionsで他のプライベートリポジトリにアクセスする際の認証方法を詳しく比較します。

## 認証方法の一覧

| 方法 | セキュリティ | 設定の複雑さ | 推奨度 | 用途 |
|------|-------------|-------------|--------|------|
| Deploy Keys (SSH) | 高（リポジトリ単位） | 中 | ★★★★★ | 特定リポジトリへのアクセス |
| GitHub App | 高（細かい権限設定） | 高 | ★★★★★ | Organization全体の管理 |
| Fine-grained PAT | 中-高 | 低 | ★★★★☆ | 複数リポジトリへのアクセス |
| Classic PAT | 低（全リポジトリ） | 低 | ★★☆☆☆ | 簡単な検証・テスト用 |
| GITHUB_TOKEN | - | - | ☆☆☆☆☆ | 同一リポジトリのみ |

---

## 1. Deploy Keys (SSH) - 最も推奨

### 概要

Deploy Keysは**リポジトリ特定のSSH鍵**で、最もセキュアな方法です。

### メリット

- ✅ リポジトリ単位でアクセス制御
- ✅ アカウント全体へのアクセスが不要
- ✅ Read-only または Read-write を選択可能
- ✅ 鍵の無効化が容易

### デメリット

- ⚠️ リポジトリごとに鍵を作成する必要がある
- ⚠️ 設定手順がやや複雑

### セットアップ手順

#### ステップ1: SSH鍵ペアの生成

```bash
# SSH鍵を生成（パスフレーズなし）
ssh-keygen -t ed25519 -C "github-actions-deploy-key" -f deploy_key -N ""

# 2つのファイルが生成される:
# - deploy_key (秘密鍵)
# - deploy_key.pub (公開鍵)
```

#### ステップ2: 公開鍵をリポジトリに登録

1. **アクセス先のリポジトリ**の Settings → Deploy keys に移動
2. "Add deploy key" をクリック
3. 設定:
   - **Title**: `GitHub Actions - [使用元リポジトリ名]`
   - **Key**: `deploy_key.pub` の内容を貼り付け
   - **Allow write access**: 必要な場合のみチェック
4. "Add key" をクリック

#### ステップ3: 秘密鍵をSecretsに登録

1. **使用元のリポジトリ**の Settings → Secrets → Actions に移動
2. "New repository secret" をクリック
3. 設定:
   - **Name**: `DEPLOY_KEY_PRIVATE_REPO`
   - **Value**: `deploy_key` ファイルの内容全体を貼り付け

#### ステップ4: ワークフローの実装

**方法A: webfactory/ssh-agent を使用（推奨）**

```yaml
name: Checkout with Deploy Key (ssh-agent)

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest

    steps:
      - name: Setup SSH Agent
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.DEPLOY_KEY_PRIVATE_REPO }}

      - name: Checkout private repository
        uses: actions/checkout@v4
        with:
          repository: owner/private-repo
          ssh-key: ${{ secrets.DEPLOY_KEY_PRIVATE_REPO }}
          path: private-repo
```

**方法B: 手動SSH設定**

```yaml
name: Checkout with Deploy Key (Manual)

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest

    steps:
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.DEPLOY_KEY_PRIVATE_REPO }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan github.com >> ~/.ssh/known_hosts

      - name: Checkout private repository via SSH
        run: |
          git clone git@github.com:owner/private-repo.git private-repo

      - name: Verify checkout
        run: ls -la private-repo/
```

### 複数リポジトリへのアクセス

```yaml
- name: Setup multiple SSH keys
  uses: webfactory/ssh-agent@v0.9.0
  with:
    ssh-private-key: |
      ${{ secrets.DEPLOY_KEY_REPO_A }}
      ${{ secrets.DEPLOY_KEY_REPO_B }}
      ${{ secrets.DEPLOY_KEY_REPO_C }}

- name: Checkout repository A
  uses: actions/checkout@v4
  with:
    repository: owner/repo-a
    ssh-key: ${{ secrets.DEPLOY_KEY_REPO_A }}
    path: repo-a

- name: Checkout repository B
  uses: actions/checkout@v4
  with:
    repository: owner/repo-b
    ssh-key: ${{ secrets.DEPLOY_KEY_REPO_B }}
    path: repo-b
```

---

## 2. GitHub App - Enterprise向け

### 概要

GitHub Appを使用した認証は、**Organizationレベルでの管理に最適**です。

### メリット

- ✅ 細かい権限設定（リポジトリ、権限レベル）
- ✅ アカウントに紐づかない
- ✅ 監査ログが詳細
- ✅ レート制限が高い
- ✅ 自動的にトークンが期限切れ

### デメリット

- ⚠️ セットアップが複雑
- ⚠️ Organization管理者権限が必要

### セットアップ手順

#### ステップ1: GitHub Appの作成

1. GitHub → Settings → Developer settings → GitHub Apps
2. "New GitHub App" をクリック
3. 基本情報を入力:
   - **GitHub App name**: `Cross-Repo Actions`
   - **Homepage URL**: リポジトリURL
   - **Webhook**: Active のチェックを外す
4. Permissions設定:
   - Repository permissions:
     - Contents: Read (またはRead and write)
     - Metadata: Read-only (自動)
5. "Create GitHub App" をクリック

#### ステップ2: Private Keyの生成とApp IDの取得

1. 作成したGitHub Appのページで:
   - **App ID** をメモ
   - "Generate a private key" をクリック
   - ダウンロードされた `.pem` ファイルを保存

#### ステップ3: GitHub Appのインストール

1. GitHub Appの設定ページで "Install App" タブ
2. Organizationを選択
3. アクセスを許可するリポジトリを選択
   - "All repositories" または "Only select repositories"

#### ステップ4: Secretsの設定

リポジトリのSecretsに追加:

```
APP_ID: <GitHub AppのID>
APP_PRIVATE_KEY: <.pemファイルの内容全体>
```

#### ステップ5: ワークフローの実装

```yaml
name: Checkout with GitHub App

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest

    steps:
      - name: Generate token from GitHub App
        id: generate_token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}
          # 特定のリポジトリのみアクセスする場合
          repositories: |
            private-repo-1
            private-repo-2

      - name: Checkout private repository
        uses: actions/checkout@v4
        with:
          repository: owner/private-repo
          token: ${{ steps.generate_token.outputs.token }}
          path: private-repo

      - name: Use the generated token
        env:
          GH_TOKEN: ${{ steps.generate_token.outputs.token }}
        run: |
          # GitHub CLIも使える
          gh repo view owner/private-repo
```

---

## 3. Fine-grained Personal Access Token

### 概要

2022年に導入された、より安全なPATです。

### メリット

- ✅ リポジトリ単位でアクセス制御
- ✅ 権限の細かい設定が可能
- ✅ Organization管理者の承認が可能
- ✅ 有効期限の設定が必須

### デメリット

- ⚠️ 個人アカウントに紐づく
- ⚠️ Organization設定によっては使用不可

### セットアップ手順

#### ステップ1: Fine-grained PATの作成

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. "Generate new token" をクリック
3. 設定:
   - **Token name**: `GitHub Actions Cross Repo`
   - **Expiration**: 適切な期限（最大1年）
   - **Repository access**:
     - "Only select repositories" を選択
     - アクセスが必要なリポジトリを選択
   - **Permissions**:
     - Repository permissions:
       - Contents: Read-only
       - Metadata: Read-only (自動選択)
4. "Generate token" をクリック
5. トークンをコピー

#### ステップ2: Secretsに追加

```
Name: GH_FINE_GRAINED_PAT
Value: <生成されたトークン>
```

#### ステップ3: ワークフローの実装

```yaml
name: Checkout with Fine-grained PAT

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout private repository
        uses: actions/checkout@v4
        with:
          repository: owner/private-repo
          token: ${{ secrets.GH_FINE_GRAINED_PAT }}
          path: private-repo
```

---

## 4. Classic Personal Access Token

### 概要

従来のPATで、全リポジトリへのアクセス権を持ちます。

### メリット

- ✅ セットアップが最も簡単
- ✅ すぐに使い始められる

### デメリット

- ❌ アカウントの全リポジトリにアクセス可能
- ❌ 権限が粗い（repo スコープ = 全権限）
- ❌ セキュリティリスクが高い
- ❌ 有効期限設定が任意

### 推奨用途

- 個人プロジェクト
- 一時的な検証
- プロトタイピング

### セットアップ

詳細は [SETUP.md](./SETUP.md) を参照してください。

---

## 5. デフォルトのGITHUB_TOKEN

### 制限事項

`GITHUB_TOKEN` は**現在のリポジトリにのみアクセス可能**で、他のリポジトリへのアクセスには使用できません。

```yaml
# ❌ これは動作しない
- uses: actions/checkout@v4
  with:
    repository: owner/other-repo
    token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 推奨される選択ガイド

### 個人プロジェクト・小規模

```
1. Deploy Keys (SSH)         - 最もセキュア
2. Fine-grained PAT          - 簡単でセキュア
3. Classic PAT               - 最も簡単（テスト用）
```

### Organization・チームプロジェクト

```
1. GitHub App                - 最も柔軟で監査可能
2. Deploy Keys (SSH)         - リポジトリ特定のアクセス
3. Fine-grained PAT          - 個人ベースのアクセス
```

### エンタープライズ

```
1. GitHub App                - 推奨
2. Deploy Keys (SSH)         - リポジトリごとの厳格な管理
```

---

## セキュリティ比較

### アクセススコープ

```
最も限定的 ←―――――――――――――→ 最も広範囲

Deploy Key    GitHub App    Fine-grained    Classic PAT
(1リポジトリ) (選択可能)    PAT(選択可能)  (全リポジトリ)
```

### セキュリティレベル

```
最も安全 ←―――――――――――――→ 最も危険

Deploy Key    GitHub App    Fine-grained    Classic PAT
```

### 推奨度

```
本番環境:    Deploy Keys または GitHub App
開発環境:    Fine-grained PAT
テスト用:    Classic PAT
```

---

## 実装例の比較

同じ結果を異なる方法で実現する例:

### 要件
- `owner/repo-a` (メインリポジトリ)
- `owner/repo-b` (プライベート、参照したい)

### パターン1: Deploy Key

```yaml
steps:
  - uses: webfactory/ssh-agent@v0.9.0
    with:
      ssh-private-key: ${{ secrets.DEPLOY_KEY_REPO_B }}

  - uses: actions/checkout@v4
    with:
      repository: owner/repo-b
      ssh-key: ${{ secrets.DEPLOY_KEY_REPO_B }}
      path: repo-b
```

### パターン2: GitHub App

```yaml
steps:
  - uses: actions/create-github-app-token@v1
    id: app_token
    with:
      app-id: ${{ secrets.APP_ID }}
      private-key: ${{ secrets.APP_PRIVATE_KEY }}
      repositories: repo-b

  - uses: actions/checkout@v4
    with:
      repository: owner/repo-b
      token: ${{ steps.app_token.outputs.token }}
      path: repo-b
```

### パターン3: Fine-grained PAT

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      repository: owner/repo-b
      token: ${{ secrets.FINE_GRAINED_PAT }}
      path: repo-b
```

### パターン4: Classic PAT

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      repository: owner/repo-b
      token: ${{ secrets.CLASSIC_PAT }}
      path: repo-b
```

---

## まとめ

| シナリオ | 推奨方法 |
|---------|---------|
| 1つのリポジトリにアクセス | Deploy Key (SSH) |
| 複数リポジトリ（個人） | Fine-grained PAT |
| 複数リポジトリ（チーム） | GitHub App |
| Organization全体の管理 | GitHub App |
| 一時的なテスト | Classic PAT |

**最も重要**: Classic PATは本番環境で使用せず、より安全な代替手段を選択してください。
