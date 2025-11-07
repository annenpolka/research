# 設定例コレクション

プロジェクトタイプ別の設定例です。自分のプロジェクトの`.claude/settings.json`にコピーして使用してください。

## ファイル一覧

### `minimal.json`
- **用途**: 最小限の設定、読み取りのみ
- **許可**: Read, Glob, Grep
- **推奨**: 初めて使う場合、調査作業

### `research-readonly.json`
- **用途**: リサーチプロジェクト、コード分析
- **許可**: 読み取り専用のツールとコマンド
- **拒否**: すべての書き込み操作
- **推奨**: コードベースの調査、ドキュメント作成

### `web-development.json`
- **用途**: Web開発（React, Vue, Angularなど）
- **許可**: src/testsディレクトリの編集、npm/yarn/pnpm、git操作
- **拒否**: 環境変数ファイル、危険なコマンド
- **推奨**: フロントエンド/フルスタック開発

### `python-ml.json`
- **用途**: Python開発、機械学習プロジェクト
- **許可**: Pythonファイル、Jupyterノートブック、pip、pytest
- **拒否**: 認証情報、環境変数
- **推奨**: データサイエンス、ML/AI開発

### `bypass-all.json`
- **用途**: すべての確認をスキップ ⚠️
- **警告**: セキュリティリスクあり
- **推奨**: 個人の実験環境のみ、本番では使用しないこと

## 使い方

1. 自分のプロジェクトに合った設定を選ぶ
2. プロジェクトルートに`.claude`ディレクトリを作成
   ```bash
   mkdir -p .claude
   ```
3. 設定ファイルをコピー
   ```bash
   cp examples/web-development.json .claude/settings.json
   ```
4. 必要に応じてカスタマイズ
5. Claude Codeを再起動

## カスタマイズのヒント

### パターンの組み合わせ

複数のテンプレートを組み合わせることができます：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep",
      "Write(src/**)",
      "Bash(npm *)",
      "Bash(git *)"
    ]
  }
}
```

### ディレクトリ制限

特定のディレクトリのみ許可：

```json
{
  "permissions": {
    "allowedTools": [
      "Write(src/**)",
      "Write(tests/**)"
    ],
    "deny": [
      "Write(dist/**)",
      "Write(build/**)"
    ]
  }
}
```

### コマンド制限

Bashコマンドを細かく制御：

```json
{
  "permissions": {
    "allowedTools": [
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Bash(git push --force *)",
      "Bash(git reset --hard *)"
    ]
  }
}
```

## 追加リソース

- [メインREADME](../README.md) - 詳細な説明
- [クイックスタート](../QUICKSTART.md) - 5分で始める
- [Claude Code公式ドキュメント](https://code.claude.com/docs/)
