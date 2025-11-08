# セットアップガイド

このドキュメントでは、GitHub Actionsで他のリポジトリを参照するための具体的なセットアップ手順を説明します。

## 前提条件

- GitHubアカウント
- リポジトリへの適切なアクセス権限
- GitHub Actionsが有効化されていること

## パブリックリポジトリのセットアップ

パブリックリポジトリは追加設定なしで参照できます。

### ステップ1: ワークフローファイルの作成

`.github/workflows/checkout-example.yml` を作成:

```yaml
name: Checkout Public Repo

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: owner/public-repo
          path: external-repo
```

### ステップ2: ワークフローの実行

- GitHubリポジトリのActionsタブに移動
- ワークフローが自動的に実行されるのを確認

## プライベートリポジトリのセットアップ

プライベートリポジトリにアクセスするには、Personal Access Token (PAT) が必要です。

### ステップ1: Personal Access Token (PAT) の作成

1. **GitHubの設定ページに移動**
   - https://github.com/settings/tokens

2. **新しいトークンを生成**
   - "Generate new token" → "Generate new token (classic)" をクリック
   - または Fine-grained token を選択（推奨）

3. **トークンの設定**
   - **Note**: `GitHub Actions Cross Repo Access` など分かりやすい名前
   - **Expiration**: 適切な有効期限を設定
   - **Scopes**:
     - Classic token: `repo` にチェック
     - Fine-grained token:
       - Repository access: 必要なリポジトリを選択
       - Permissions: `Contents` → `Read-only`

4. **トークンをコピー**
   - 生成されたトークンをコピー（このページを離れると二度と表示されません）

### ステップ2: リポジトリシークレットの設定

1. **リポジトリの設定ページに移動**
   - リポジトリページ → Settings → Secrets and variables → Actions

2. **新しいシークレットを追加**
   - "New repository secret" をクリック
   - **Name**: `GH_PAT`
   - **Value**: ステップ1でコピーしたトークンを貼り付け
   - "Add secret" をクリック

### ステップ3: ワークフローファイルの作成

`.github/workflows/checkout-private.yml` を作成:

```yaml
name: Checkout Private Repo

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: owner/private-repo
          token: ${{ secrets.GH_PAT }}
          path: private-repo
```

### ステップ4: ワークフローの実行確認

- ワークフローが正常に実行されることを確認
- エラーが発生する場合は、トラブルシューティングを参照

## GitHub Appを使用したセットアップ（推奨）

GitHub Appを使用すると、より安全で細かい権限管理が可能です。

### ステップ1: GitHub Appの作成

1. **Organization設定に移動**
   - Organization → Settings → Developer settings → GitHub Apps
   - "New GitHub App" をクリック

2. **App情報を入力**
   - **GitHub App name**: `Cross Repo Actions`
   - **Homepage URL**: リポジトリURL
   - **Webhook**: Activeのチェックを外す

3. **Permissions設定**
   - Repository permissions:
     - Contents: Read-only
     - Metadata: Read-only

4. **Where can this GitHub App be installed?**
   - "Only on this account" を選択

5. **Create GitHub App**

### ステップ2: Private Keyの生成

1. 作成したGitHub Appの設定ページに移動
2. "Generate a private key" をクリック
3. ダウンロードされた `.pem` ファイルを保存

### ステップ3: GitHub Appのインストール

1. GitHub Appの設定ページで "Install App" をクリック
2. 対象のOrganizationを選択
3. アクセスを許可するリポジトリを選択

### ステップ4: シークレットの設定

リポジトリのSecretsに以下を追加:

- `APP_ID`: GitHub AppのID
- `APP_PRIVATE_KEY`: `.pem` ファイルの内容全体

### ステップ5: ワークフローファイルの作成

```yaml
name: Checkout with GitHub App

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest
    steps:
      - name: Generate token
        id: generate_token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      - name: Checkout private repo
        uses: actions/checkout@v4
        with:
          repository: owner/private-repo
          token: ${{ steps.generate_token.outputs.token }}
          path: private-repo
```

## 複数リポジトリのセットアップ例

```yaml
name: Multi Repo Setup

on: [push]

jobs:
  multi-checkout:
    runs-on: ubuntu-latest
    steps:
      # Main repository
      - name: Checkout main
        uses: actions/checkout@v4
        with:
          path: main

      # Public repository
      - name: Checkout public library
        uses: actions/checkout@v4
        with:
          repository: owner/public-lib
          path: libs/public

      # Private repository
      - name: Checkout private tools
        uses: actions/checkout@v4
        with:
          repository: owner/private-tools
          token: ${{ secrets.GH_PAT }}
          path: tools/private

      # Specific version
      - name: Checkout specific version
        uses: actions/checkout@v4
        with:
          repository: owner/versioned-repo
          ref: v1.2.3
          path: libs/versioned

      - name: Use all repositories
        run: |
          ls -la main/
          ls -la libs/public/
          ls -la tools/private/
          ls -la libs/versioned/
```

## セキュリティベストプラクティス

### 1. 最小権限の原則

PATには必要最小限の権限のみを付与:

- ✓ Fine-grained tokenを使用
- ✓ 必要なリポジトリのみにアクセス許可
- ✓ Read-only権限で十分な場合は書き込み権限を付与しない

### 2. トークンの管理

- ✓ GitHubのSecretsを使用（ハードコード禁止）
- ✓ 定期的なローテーション（90日ごとなど）
- ✓ 使用していないトークンは削除

### 3. 監査とモニタリング

- ✓ トークンの使用状況を定期的に確認
- ✓ 不審なアクセスがないか監視
- ✓ GitHub App使用時はインストールログを確認

## 次のステップ

1. [ユースケース集](./examples/)を参照して実装パターンを学ぶ
2. [トラブルシューティングガイド](./TROUBLESHOOTING.md)で問題解決方法を確認
3. 実際のプロジェクトで実装してテスト

## 参考リソース

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [actions/checkout](https://github.com/actions/checkout)
- [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Creating a GitHub App](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app)
