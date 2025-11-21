# mgrep - セマンティック検索ツールの調査

## 概要

[mgrep](https://github.com/mixedbread-ai/mgrep) は、Mixedbread AIが開発した次世代のコード検索ツールです。従来の`grep`コマンドの機能を拡張し、自然言語によるセマンティック検索を可能にします。

## プロジェクトの目的

このプロジェクトは、mgrepがどのようなツールで、どのような技術を使用しているかを調査することを目的としています。

## 主な特徴

### 1. セマンティック検索
- **自然言語クエリ**: 正確なパターンマッチングではなく、意図を理解した検索が可能
- **多言語・マルチモーダル対応**: コード、テキスト、PDF、画像に対応（将来的にオーディオ・ビデオも）
- **コンテキスト認識**: ファイルの意味を理解してより関連性の高い結果を返す

### 2. リアルタイムインデックス作成
- `mgrep watch` コマンドでリポジトリを継続的にインデックス化
- `.gitignore` を尊重し、不要なファイルを除外
- ファイル変更を自動検知してインデックスを更新

### 3. AIエージェント統合
- **Claude Code統合**: `mgrep install-claude-code` で簡単にインストール
- **トークン効率**: 従来のgrep方式と比較してトークン使用量を約50%削減
- **エージェント向け設計**: 静かな出力、適切なデフォルト設定

### 4. 従来のgrepとの共存
mgrepは従来のgrepを置き換えるものではなく、補完するツールとして設計されています：

| grep/ripgrep を使用 | mgrep を使用 |
|---------------------|--------------|
| 正確なマッチング | 意図ベースの検索 |
| シンボルトレース、リファクタリング、正規表現 | コード探索、機能発見、オンボーディング |

## 技術スタック

### プログラミング言語とフレームワーク
- **TypeScript**: メインの実装言語
- **Node.js**: ランタイム環境
- **Commander.js**: CLIフレームワーク

### 主な依存関係
- `@mixedbread/sdk`: Mixedbread Search APIのSDK
- `better-auth`: 認証システム
- `@clack/prompts`: 対話型プロンプト
- `chalk`: ターミナル出力の装飾
- `ignore`: .gitignoreパターンの処理

### アーキテクチャ

```
mgrep/
├── src/
│   ├── commands/          # CLIコマンド実装
│   │   ├── login.ts      # 認証
│   │   ├── logout.ts
│   │   ├── search.ts     # 検索機能
│   │   └── watch.ts      # ファイル監視・インデックス化
│   ├── install/
│   │   └── claude-code.ts # Claude Code統合
│   ├── lib/              # ユーティリティ
│   ├── index.ts          # エントリーポイント
│   ├── token.ts          # トークン管理
│   └── utils.ts
├── plugins/
│   └── mgrep/
│       ├── skills/       # Claude Codeスキル定義
│       └── hooks/        # フック実装
└── guides/               # ドキュメント
```

## 主要コマンド

### 検索 (デフォルトコマンド)
```bash
mgrep "where do we set up auth?"
mgrep "How are chunks defined?" src/models
mgrep -m 10 "What is the maximum number of concurrent workers?"
mgrep -a "What code parsers are available?"  # AI生成の回答付き
```

### インデックス作成
```bash
cd path/to/repo
mgrep watch  # リポジトリをインデックス化し、変更を監視
```

### 認証
```bash
mgrep login   # ブラウザベースの認証
mgrep logout
```

### Claude Code統合
```bash
mgrep install-claude-code
```

## Mixedbread Search との統合

mgrepは裏側で [Mixedbread Search](https://www.mixedbread.com/blog/mixedbread-search) を使用しています：

- **ファイルの埋め込み**: 各ファイルがMixedbread Storeにアップロードされる
- **リランキング**: 検索結果の関連性を高めるためのリランキング機能
- **クラウドバックアップ**: ストアはクラウドに保存され、チーム間で共有可能
- **コンテキスト情報**: ファイルパス、行範囲、ページ番号などのメタデータ付き

## パフォーマンス

Mixedbreadが実施した50タスクのベンチマークによると：
- **トークン削減**: 従来のgrep方式と比較して約50%のトークン削減
- **品質維持**: 同等以上の検索品質を維持
- **効率性**: セマンティック検索で関連スニペットを素早く特定し、AIが推論に集中できる

## 設定オプション

### 環境変数
- `MXBAI_API_KEY`: APIキーによる認証（CI/CD向け）
- `MXBAI_STORE`: デフォルトストア名の上書き（デフォルト: `mgrep`）

### 除外ルール
- `.gitignore`: 自動的に尊重される
- `.mgrepignore`: mgrepに特有の除外ルールを定義可能

## Claude Code統合の詳細

### スキル定義
mgrepはClaude Codeのスキルとして統合され、自動的に使用されます：
- セマンティック検索が常に利用可能
- 自然言語でのクエリを推奨
- grepよりも優れた結果を提供

### 推奨される使用方法
```bash
# Good
mgrep "What code parsers are available?"
mgrep "How are chunks defined?" src/models

# Bad
mgrep "parser"  # クエリが不明確
```

## 開発環境

```bash
pnpm install
pnpm build        # または pnpm dev で開発モード
pnpm format       # Biomeによるフォーマットとリント
pnpm typecheck    # 型チェック
```

## ライセンス

Apache-2.0

## 発見と考察

### 強み
1. **自然言語理解**: 開発者が「何を探しているか」を説明できる
2. **AIエージェント最適化**: トークン効率が高く、AIとの統合がスムーズ
3. **既存ツールとの共存**: grepを置き換えるのではなく補完する設計
4. **マルチモーダル**: コードだけでなく、画像やPDFにも対応

### 課題
1. **クラウド依存**: Mixedbread Searchのクラウドサービスに依存
2. **ネットワーク要件**: オフライン環境では使用不可
3. **プライバシー考慮**: コードがクラウドにアップロードされる
4. **学習曲線**: 効果的なクエリの書き方を学ぶ必要がある

### ユースケース
- **大規模コードベースの探索**: 不明なコードベースの理解を加速
- **オンボーディング**: 新しいチームメンバーがコードを素早く理解
- **AIペアプログラミング**: Claude Codeなどのエージェントとの効率的な連携
- **ドキュメント検索**: コードとドキュメントの横断的な検索

## 結論

mgrepは、従来のgrepツールに「意図理解」を加えた革新的なツールです。特にAIエージェントとの統合において、トークン効率と検索品質の両面で優れた結果を示しています。プライバシーとクラウド依存性の考慮は必要ですが、適切なユースケースにおいては開発体験を大幅に向上させる可能性があります。

## 参考リンク

- [GitHub Repository](https://github.com/mixedbread-ai/mgrep)
- [Mixedbread Search](https://www.mixedbread.com/blog/mixedbread-search)
- [NPM Package](https://www.npmjs.com/package/@mixedbread/mgrep)
- [Demo Playground](https://demo.mgrep.mixedbread.com)
