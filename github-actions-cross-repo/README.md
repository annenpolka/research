# GitHub Actions - 他のリポジトリを参照する方法

## 概要

GitHub Actionsのワークフロー内で他のリポジトリをチェックアウトし、そのコードやファイルを利用する方法を調査・検証するプロジェクトです。

## 動機

複数のリポジトリにまたがるプロジェクトでは、以下のようなユースケースがあります：

- 共通ライブラリやツールを別リポジトリから取得
- モノレポではない複数リポジトリ構成での統合テスト
- ドキュメントや設定ファイルを別リポジトリから参照
- 依存関係のあるプロジェクト間でのビルド・デプロイ

GitHub Actionsでこれらを実現する方法を理解することが重要です。

## 手法

### 1. 基本的な他リポジトリのチェックアウト

`actions/checkout@v5` アクションの `repository` パラメータを使用します。

```yaml
- name: Checkout another repository
  uses: actions/checkout@v5
  with:
    repository: owner/repo-name
    path: other-repo
```

**主要パラメータ:**

- `repository`: チェックアウトするリポジトリ（`owner/repo-name` 形式）
- `path`: チェックアウト先のパス（指定しない場合はワークスペースルート）
- `token`: 認証用トークン（プライベートリポジトリの場合）
- `ref`: チェックアウトするブランチ、タグ、またはコミット

### 2. 複数リポジトリの並行チェックアウト

複数のリポジトリを異なるディレクトリにチェックアウトできます。

```yaml
- name: Checkout main repository
  uses: actions/checkout@v5
  with:
    path: main

- name: Checkout tools repository
  uses: actions/checkout@v5
  with:
    repository: my-org/my-tools
    path: tools

- name: Checkout config repository
  uses: actions/checkout@v5
  with:
    repository: my-org/my-config
    path: config
```

### 3. プライベートリポジトリへのアクセス

プライベートリポジトリにアクセスする場合、デフォルトの `GITHUB_TOKEN` は現在のリポジトリにのみスコープされているため、認証が必要です。

#### 認証方法の選択肢

複数の認証方法があり、それぞれ異なる用途に適しています：

| 方法 | セキュリティ | 推奨度 | 用途 |
|------|-------------|--------|------|
| Deploy Keys (SSH) | 高 | ★★★★★ | 特定リポジトリへのアクセス |
| GitHub App | 高 | ★★★★★ | Organization全体の管理 |
| Fine-grained PAT | 中-高 | ★★★★☆ | 複数リポジトリへのアクセス |
| Classic PAT | 低 | ★★☆☆☆ | テスト用のみ |

**方法1: Deploy Keys (SSH) - 最も推奨**

```yaml
- name: Setup SSH Agent
  uses: webfactory/ssh-agent@v0.9.0
  with:
    ssh-private-key: ${{ secrets.DEPLOY_KEY }}

- name: Checkout private repository
  uses: actions/checkout@v5
  with:
    repository: my-org/private-repo
    ssh-key: ${{ secrets.DEPLOY_KEY }}
    path: private-repo
```

**方法2: GitHub App**

```yaml
- name: Generate GitHub App Token
  id: app_token
  uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}

- name: Checkout private repository
  uses: actions/checkout@v5
  with:
    repository: my-org/private-repo
    token: ${{ steps.app_token.outputs.token }}
    path: private-repo
```

**方法3: Personal Access Token**

```yaml
- name: Checkout private repository
  uses: actions/checkout@v5
  with:
    repository: my-org/private-repo
    token: ${{ secrets.GH_PAT }}
    path: private-repo
```

詳細なセットアップ手順は [AUTHENTICATION.md](./AUTHENTICATION.md) を参照してください

### 4. 特定のブランチやタグのチェックアウト

```yaml
- name: Checkout specific branch
  uses: actions/checkout@v5
  with:
    repository: my-org/my-repo
    ref: develop
    path: develop-branch

- name: Checkout specific tag
  uses: actions/checkout@v5
  with:
    repository: my-org/my-repo
    ref: v1.2.3
    path: release-v1.2.3
```

## 実装例

このプロジェクトには以下の検証用サンプルが含まれています：

### 基本的なチェックアウト

1. **パブリックリポジトリの参照** (`.github/workflows/checkout-public.yml`)
   - 認証なしでパブリックリポジトリをチェックアウト
   - ファイル一覧の表示

2. **複数リポジトリの統合** (`.github/workflows/multi-repo.yml`)
   - 複数のリポジトリを並行チェックアウト
   - ファイルの統合とアーティファクト作成

3. **サブモジュール風の利用** (`.github/workflows/submodule-like.yml`)
   - 外部ライブラリとしてリポジトリを参照
   - 特定バージョンのチェックアウト

### 認証方法別の実装

4. **SSH Deploy Keys** (`.github/workflows/checkout-with-ssh.yml`)
   - Deploy Keysを使用した認証
   - webfactory/ssh-agentの活用
   - 複数リポジトリへのSSHアクセス

5. **GitHub App** (`.github/workflows/checkout-with-github-app.yml`)
   - GitHub Appトークンの生成
   - スコープ付きアクセス
   - Organization管理の例

6. **プライベートリポジトリ** (`.github/workflows/checkout-private-example.yml`)
   - PATを使用した認証
   - エラーハンドリング
   - セットアップ手順の表示

### 実用例

7. **サンプルプロジェクト** (`.github/workflows/sample-project-demo.yml`)
   - 実際のNode.jsプロジェクトでの利用
   - 外部ライブラリの統合
   - レポート生成

## 使い方

### ワークフローのトリガー

各ワークフローファイルは手動実行（`workflow_dispatch`）で実行できます：

1. GitHub の Actions タブに移動
2. 実行したいワークフローを選択
3. "Run workflow" ボタンをクリック

### ローカルでの確認

ワークフローファイルの構文チェック：

```bash
# actionlintをインストール
brew install actionlint  # macOS
# または
go install github.com/rhysd/actionlint/cmd/actionlint@latest

# チェック実行
actionlint .github/workflows/*.yml
```

## 結果

### 主な発見

1. **パブリックリポジトリは簡単にアクセス可能**
   - `repository` パラメータを指定するだけで利用可能
   - 認証トークン不要

2. **プライベートリポジトリにはPATが必須**
   - `GITHUB_TOKEN` は現在のリポジトリにのみスコープされる
   - 他のプライベートリポジトリには専用のPATが必要
   - PATには適切なスコープ（`repo`）が必要

3. **pathパラメータで衝突を回避**
   - 複数リポジトリをチェックアウトする際は `path` 必須
   - 明示的にディレクトリを分けることで管理しやすい

4. **用途に応じた柔軟な活用が可能**
   - 共通ツールの利用
   - 統合テスト
   - ドキュメント生成
   - デプロイスクリプトの共有

### ベストプラクティス

1. **最小権限の原則**
   - PATには必要最小限のスコープのみ付与
   - Fine-grained PAT の使用を検討

2. **キャッシュの活用**
   - 頻繁にチェックアウトするリポジトリは `actions/cache` でキャッシュ

3. **明示的なバージョン管理**
   - `ref` パラメータでタグやコミットハッシュを指定
   - 予期しない変更を防ぐ

4. **セキュリティ考慮**
   - PATをハードコードしない
   - GitHub Secretsを必ず使用
   - 定期的なトークンのローテーション

### 制限事項

1. **GITHUB_TOKENの制限**
   - デフォルトトークンは現在のリポジトリのみ
   - 他のリポジトリへのアクセスには追加設定が必要

2. **レート制限**
   - GitHub APIのレート制限に注意
   - 認証ありで5,000リクエスト/時間

3. **ネットワーク依存**
   - チェックアウトはネットワーク経由
   - 大きなリポジトリは時間がかかる可能性

## 結論

GitHub Actionsで他のリポジトリを参照することは、`actions/checkout` アクションを使用することで簡単に実現できます。

**推奨される使い方:**

- **パブリックリポジトリ**: `repository` と `path` パラメータのみで簡単に利用
- **プライベートリポジトリ**: PATをSecretsに保存し、`token` パラメータで指定
- **複数リポジトリ**: それぞれに `path` を指定して並行チェックアウト

この機能を活用することで、モノレポに移行せずとも、複数リポジトリ間での効率的な CI/CD パイプラインを構築できます。

## ドキュメント

- **[AUTHENTICATION.md](./AUTHENTICATION.md)** - 認証方法の詳細な比較とセットアップ手順
- **[SETUP.md](./SETUP.md)** - ステップバイステップのセットアップガイド
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - よくある問題と解決方法
- **[examples/](./examples/)** - 実用的なユースケース集

## 参考リソース

### GitHub公式ドキュメント
- [actions/checkout - GitHub](https://github.com/actions/checkout)
- [GitHub Actions: Contexts](https://docs.github.com/en/actions/learn-github-actions/contexts)
- [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Creating a GitHub App](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app)

### 関連ツール
- [webfactory/ssh-agent](https://github.com/webfactory/ssh-agent) - SSH鍵管理アクション
- [actions/create-github-app-token](https://github.com/actions/create-github-app-token) - GitHub Appトークン生成
