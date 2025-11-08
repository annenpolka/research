# Devcontainer Coding Agent Test

## 概要

このプロジェクトは、Development Container（devcontainer）環境でAIコーディングエージェントを動作させるための検証プロジェクトです。Claude Code、GitHub Copilot、その他のAIコーディングアシスタントが、devcontainer環境内で正常に機能するかを体系的にテストします。

## 動機

開発環境の標準化とポータビリティを実現するdevcontainerは、チーム開発において重要な役割を果たしています。しかし、AIコーディングエージェントがこのような隔離された環境で正常に動作するかは、実際に検証する必要があります。

このプロジェクトの目的は：

1. **互換性の検証**: devcontainer環境でコーディングエージェントが正常に動作するか
2. **機能の確認**: ファイル操作、パッケージインストール、テスト実行などが可能か
3. **制限事項の特定**: devcontainer環境特有の制約や問題点の発見
4. **ベストプラクティスの確立**: エージェントを効果的に使用するための設定やワークフロー

## プロジェクト構成

```
devcontainer-coding-agent-test/
├── .devcontainer/
│   ├── devcontainer.json       # Devcontainerの設定
│   └── post-create.sh          # コンテナ作成後の初期化スクリプト
├── test-projects/
│   ├── buggy-calculator.py     # バグ修正タスク用のサンプルコード
│   ├── refactor-me.js          # リファクタリングタスク用のサンプルコード
│   ├── test_calculator.py      # 計算機のテストケース
│   ├── package.json            # Node.js プロジェクト設定
│   └── requirements.txt        # Python 依存関係
├── agent-verification.sh       # エージェント環境検証スクリプト
├── AGENT_TASKS.md             # エージェント用テストタスク一覧
└── README.md                   # このファイル
```

## セットアップ

### 前提条件

- Docker Desktop がインストールされている
- Visual Studio Code がインストールされている
- VS Code の "Dev Containers" 拡張機能がインストールされている

### 起動手順

1. **リポジトリをクローン**:
   ```bash
   git clone <repository-url>
   cd devcontainer-coding-agent-test
   ```

2. **VS Code で開く**:
   ```bash
   code .
   ```

3. **Devcontainer で再オープン**:
   - VS Code のコマンドパレット（Ctrl+Shift+P / Cmd+Shift+P）を開く
   - "Dev Containers: Reopen in Container" を選択
   - コンテナのビルドと起動を待つ

4. **環境の検証**:
   ```bash
   bash agent-verification.sh
   ```

## Devcontainer 環境の詳細

### インストールされているツール

- **開発言語**:
  - Python 3.11 (pip, pytest, black, flake8, mypy)
  - Node.js LTS (npm, eslint, prettier, typescript)

- **ユーティリティ**:
  - Git
  - Docker-in-Docker
  - ripgrep (高速検索)
  - bat (cat の代替)
  - jq (JSON プロセッサ)
  - tmux, vim

- **VS Code 拡張機能**:
  - Python 関連ツール
  - ESLint, Prettier
  - GitHub Copilot (オプション)
  - Continue (オプション)

### 環境変数

- `AGENT_TEST_ENV=devcontainer`: エージェントが devcontainer 内で動作していることを示す

## テストタスク

詳細は [AGENT_TASKS.md](AGENT_TASKS.md) を参照してください。

### 基本タスク

1. **Task 1: バグ修正** - `buggy-calculator.py` のバグを特定して修正
2. **Task 2: リファクタリング** - `refactor-me.js` のコード品質を改善

### 中級タスク

3. **Task 3: テスト生成** - リファクタリングしたコードのユニットテストを作成
4. **Task 4: ドキュメント生成** - API ドキュメントとユーザーガイドを作成

### 上級タスク

5. **Task 5: 機能追加** - TDD で新機能を実装
6. **Task 6: パフォーマンス最適化** - 再帰関数の最適化
7. **Task 7: エラーハンドリング** - 包括的なバリデーションとエラー処理

### 統合タスク

8. **Task 8: CI/CD セットアップ** - GitHub Actions の設定
9. **Task 9: コード品質ツール** - リンターとフォーマッターの設定

## 使い方

### エージェントでテストを実行する場合

1. Devcontainer を起動
2. コーディングエージェント（Claude Code など）を起動
3. `AGENT_TASKS.md` のタスクを順番に実行
4. 各タスクの結果を記録

### 手動でテストを実行する場合

```bash
# Python テストの実行
cd test-projects
pip install -r requirements.txt
pytest test_calculator.py -v

# JavaScript コードの実行
npm install
node refactor-me.js
```

## 検証項目

このプロジェクトでは、以下の機能を検証します：

### ファイル操作
- [x] ファイルの読み取り
- [x] ファイルの作成
- [x] ファイルの編集
- [x] ファイルの削除

### コマンド実行
- [x] Shell コマンドの実行
- [x] Python スクリプトの実行
- [x] Node.js スクリプトの実行

### パッケージ管理
- [x] pip でのパッケージインストール
- [x] npm でのパッケージインストール

### 開発ツール
- [x] テストランナーの実行
- [x] リンターの実行
- [x] フォーマッターの実行

### Git 操作
- [x] Git の基本操作（add, commit）
- [x] ブランチ操作
- [x] マージ操作

## 既知の制限事項

1. **ネットワーク**: devcontainer 内からのネットワークアクセスは、ホストの設定に依存します
2. **パフォーマンス**: ファイル I/O はホストシステムより遅い場合があります
3. **Docker-in-Docker**: 一部の操作では追加の権限設定が必要な場合があります

## トラブルシューティング

### コンテナが起動しない

1. Docker Desktop が起動しているか確認
2. `.devcontainer/devcontainer.json` の設定を確認
3. Docker のリソース制限を確認

### パッケージがインストールできない

1. インターネット接続を確認
2. プロキシ設定が必要か確認
3. `post-create.sh` のログを確認

### エージェントがファイルにアクセスできない

1. ファイルパーミッションを確認
2. パスが正しいか確認（コンテナ内のパス）
3. マウント設定を確認

## 結果と知見

### 成功した項目

✅ **基本的なファイル操作**: すべてのファイル操作が正常に動作
✅ **パッケージインストール**: Python と Node.js のパッケージインストールが可能
✅ **テスト実行**: pytest と Jest の実行が可能
✅ **Git 操作**: 基本的な Git コマンドが動作

### 課題と改善点

⚠️ **パフォーマンス**: 大規模なファイル操作では遅延が発生する可能性
⚠️ **設定の複雑さ**: 初回セットアップに時間がかかる
⚠️ **依存関係の管理**: 複数の言語環境を同時に管理する必要がある

### 推奨事項

1. **段階的な導入**: まず小規模なプロジェクトで試す
2. **明確なタスク定義**: エージェントに対して明確な指示を与える
3. **定期的な検証**: devcontainer の設定を定期的に見直す
4. **ドキュメント化**: プロジェクト固有の設定やワークフローを文書化する

## Claude Code での使用例

```bash
# Claude Code を起動
claude

# エージェントに指示
"test-projects/buggy-calculator.py のバグを修正してください"

# テストを実行
"pytest test_calculator.py を実行して結果を確認してください"

# リファクタリング
"refactor-me.js をモダンな JavaScript に書き直してください"
```

## 貢献

このプロジェクトは実験的な研究プロジェクトです。以下のような貢献を歓迎します：

- 新しいテストタスクの追加
- Devcontainer 設定の改善
- 他のコーディングエージェントでの検証結果
- バグ報告や改善提案

## ライセンス

MIT License

## 参考資料

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Devcontainer Specification](https://containers.dev/)
- [Claude Code Documentation](https://claude.ai/)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)

## まとめ

Devcontainer 環境でコーディングエージェントを使用することは、以下の利点があります：

1. **環境の一貫性**: チーム全体で同じ開発環境を共有
2. **隔離性**: ホストシステムを汚さない
3. **再現性**: 環境を簡単に再構築可能
4. **移植性**: 異なるマシン間で環境を移動可能

このプロジェクトの検証により、devcontainer 環境でもコーディングエージェントが効果的に機能することが確認できました。適切な設定とタスク定義により、AI アシスタントを活用した効率的な開発が可能です。
