# プロジェクト構造

このドキュメントは、GitHub Actions Cross-Repository プロジェクトの全体構造を説明します。

## ディレクトリ構成

```
github-actions-cross-repo/
├── README.md                          # プロジェクト概要と主要情報
├── _summary.md                        # 一行サマリー
├── PROJECT_STRUCTURE.md               # このファイル
├── AUTHENTICATION.md                  # 認証方法の詳細な比較
├── SETUP.md                          # セットアップガイド
├── TROUBLESHOOTING.md                # トラブルシューティング
│
├── .github/
│   └── workflows/                    # GitHub Actionsワークフロー
│       ├── checkout-public.yml       # パブリックリポジトリのチェックアウト
│       ├── multi-repo.yml            # 複数リポジトリの統合
│       ├── submodule-like.yml        # サブモジュール風の利用
│       ├── checkout-with-ssh.yml     # SSH Deploy Keysを使用
│       ├── checkout-with-github-app.yml  # GitHub Appを使用
│       ├── checkout-private-example.yml  # プライベートリポジトリの例
│       └── sample-project-demo.yml   # サンプルプロジェクトのデモ
│
├── examples/                         # 実用的なユースケース
│   ├── use-case-1-shared-scripts.md  # 共通スクリプトの利用
│   ├── use-case-2-integration-testing.md  # 統合テスト
│   └── use-case-3-documentation.md   # ドキュメント生成
│
└── sample-project/                   # サンプルNode.jsプロジェクト
    ├── package.json                  # プロジェクト設定
    └── main.js                       # メインスクリプト
```

## ドキュメント概要

### コアドキュメント

| ファイル | 内容 | 対象読者 |
|---------|------|---------|
| README.md | プロジェクト概要、基本的な使い方 | すべてのユーザー |
| AUTHENTICATION.md | 認証方法の詳細な比較とセットアップ | セキュリティを重視するユーザー |
| SETUP.md | ステップバイステップのセットアップ手順 | 初めて使うユーザー |
| TROUBLESHOOTING.md | よくある問題と解決方法 | 問題に直面しているユーザー |

### ワークフローファイル

#### 基本的なチェックアウト

1. **checkout-public.yml**
   - パブリックリポジトリの参照
   - 認証不要
   - 初心者向け

2. **multi-repo.yml**
   - 複数リポジトリの並行チェックアウト
   - ファイルの統合
   - アーティファクトの作成

3. **submodule-like.yml**
   - 外部ライブラリとしての利用
   - 特定バージョンのチェックアウト
   - スクリプトとの統合

#### 認証方法別

4. **checkout-with-ssh.yml**
   - SSH Deploy Keysの使用方法
   - webfactory/ssh-agentの活用
   - 複数リポジトリへのSSHアクセス
   - セキュリティ比較

5. **checkout-with-github-app.yml**
   - GitHub Appトークンの生成
   - スコープ付きアクセス
   - Organization管理
   - 実用例

6. **checkout-private-example.yml**
   - Personal Access Tokenの使用
   - エラーハンドリング
   - セットアップ手順の表示

#### デモ

7. **sample-project-demo.yml**
   - 実際のNode.jsプロジェクト
   - 外部ライブラリの統合
   - レポート生成

### ユースケース例

実際のビジネスシナリオでの活用例を提供：

1. **shared-scripts** - チーム全体で共有するスクリプトの管理
2. **integration-testing** - マイクロサービスの統合テスト
3. **documentation** - 複数リポジトリのドキュメント統合

### サンプルプロジェクト

実際に動作するNode.jsプロジェクトで、以下を実演：

- 外部リポジトリの検出
- パッケージ情報の読み取り
- ディレクトリ構造の検証

## 使用方法のフロー

### 1. 初めて使う場合

```
README.md → SETUP.md → ワークフロー実行
```

### 2. 認証方法を選ぶ場合

```
README.md → AUTHENTICATION.md → 該当するワークフロー
```

### 3. 問題が発生した場合

```
TROUBLESHOOTING.md → README.md → GitHub Issues
```

### 4. 実装例を探す場合

```
examples/ → 該当するワークフロー → 自分のプロジェクトに適用
```

## 各ファイルの詳細

### README.md
- **目的**: プロジェクトの全体像を提供
- **内容**:
  - 概要と動機
  - 基本的な手法
  - 主な発見
  - クイックスタート
- **文字数**: 約 4,500文字

### AUTHENTICATION.md
- **目的**: 認証方法の包括的なガイド
- **内容**:
  - 5つの認証方法の詳細比較
  - セキュリティレベルの評価
  - 各方法のセットアップ手順
  - 実装例の比較
- **文字数**: 約 12,000文字

### SETUP.md
- **目的**: 実践的なセットアップガイド
- **内容**:
  - パブリックリポジトリのセットアップ
  - プライベートリポジトリのセットアップ
  - GitHub Appのセットアップ
  - ベストプラクティス
- **文字数**: 約 8,000文字

### TROUBLESHOOTING.md
- **目的**: 問題解決のリファレンス
- **内容**:
  - 認証エラー
  - パスの問題
  - 権限エラー
  - パフォーマンスの問題
  - デバッグ方法
- **文字数**: 約 8,500文字

## 技術スタック

- **GitHub Actions**: CI/CDプラットフォーム
- **actions/checkout@v4**: リポジトリチェックアウトアクション
- **webfactory/ssh-agent@v0.9.0**: SSH鍵管理
- **actions/create-github-app-token@v1**: GitHub Appトークン生成
- **Node.js 20**: サンプルプロジェクトの実行環境

## 対象ユーザー

### 初級者
- GitHub Actions初めて使う
- シンプルなパブリックリポジトリのチェックアウトから始める
- **推奨**: README.md → checkout-public.yml

### 中級者
- GitHub Actionsの基本は理解している
- プライベートリポジトリへのアクセスが必要
- **推奨**: AUTHENTICATION.md → SETUP.md → checkout-with-ssh.yml

### 上級者
- 複雑なCI/CDパイプラインを構築
- セキュリティとスケーラビリティが重要
- **推奨**: AUTHENTICATION.md → checkout-with-github-app.yml → カスタム実装

### チーム/組織
- 複数のリポジトリを管理
- 統一されたアクセス管理が必要
- **推奨**: GitHub App + examples/

## 拡張性

このプロジェクトは以下のように拡張可能：

1. **新しいユースケースの追加**
   - `examples/` に新しいマークダウンファイルを追加
   - `.github/workflows/` に対応するワークフローを作成

2. **他の認証方法**
   - OAuth Appsのサポート
   - SAML/SSOとの統合

3. **他のCI/CDプラットフォームへの応用**
   - GitLab CI
   - Jenkins
   - CircleCI

## メンテナンス

- ワークフローファイルは定期的にテスト
- GitHub Actionsのバージョンアップに追従
- セキュリティベストプラクティスの更新

## ライセンス

このプロジェクトは研究目的で作成されています。
