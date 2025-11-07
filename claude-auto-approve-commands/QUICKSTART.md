# クイックスタートガイド

Claude Codeでコマンドの自動許可を5分で設定する方法。

## 最短設定（3ステップ）

### 1. 設定ファイルを作成

プロジェクトのルートで：

```bash
mkdir -p .claude
```

`.claude/settings.json`を作成：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep"
    ]
  }
}
```

### 2. 確認

```bash
cat .claude/settings.json
```

JSONが正しいか確認（カンマ、括弧など）。

### 3. Claude Codeを再起動

設定が有効になります。これで`Read`、`Glob`、`Grep`ツールは自動承認されます。

## よく使う設定例

### 開発用（安全な読み取りのみ）

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep",
      "Bash(ls *)",
      "Bash(pwd)",
      "Bash(git status)"
    ]
  }
}
```

### 積極的な開発用（書き込みも含む）

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep",
      "Bash(git *)",
      "Bash(npm *)"
    ],
    "deny": [
      "Read(.env*)",
      "Write(.env*)",
      "Bash(rm -rf *)"
    ]
  }
}
```

### 実験環境用（すべて許可）⚠️

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

**警告**: これはすべての確認をスキップします。個人の実験環境でのみ使用してください。

## プロジェクトタイプ別の推奨設定

### Python

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(*.py)",
      "Edit(*.py)",
      "Bash(pytest *)",
      "Bash(python -m *)",
      "Bash(pip install *)"
    ]
  }
}
```

### Node.js/TypeScript

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**)",
      "Edit(src/**)",
      "Bash(npm *)",
      "Bash(yarn *)",
      "Bash(git status)",
      "Bash(git diff *)"
    ]
  }
}
```

### Rust

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**)",
      "Edit(src/**)",
      "Bash(cargo *)",
      "Bash(rustc *)",
      "Bash(git *)"
    ]
  }
}
```

### Go

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(*.go)",
      "Edit(*.go)",
      "Bash(go *)",
      "Bash(git *)"
    ]
  }
}
```

## ユーザーレベルの設定（全プロジェクト共通）

すべてのプロジェクトに適用する場合：

```bash
mkdir -p ~/.claude
```

`~/.claude/settings.json`を作成：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep"
    ]
  }
}
```

プロジェクト固有の設定は`.claude/settings.json`で上書きできます。

## トラブルシューティング

### 設定が効かない

```bash
# JSON構文チェック
python -m json.tool .claude/settings.json

# または jqを使用
jq . .claude/settings.json
```

### 一時的にバイパス（コマンドライン）

```bash
claude-code --allowedTools "Read,Write,Bash(git *)"
```

### 設定の優先順位を確認

1. コマンドラインフラグ（最優先）
2. `.claude/settings.local.json`（個人用）
3. `.claude/settings.json`（プロジェクト用）
4. `~/.claude/settings.json`（ユーザーレベル）

## 次のステップ

- [詳細なREADME](README.md)を読む
- [セキュリティベストプラクティス](README.md#セキュリティのベストプラクティス)を確認
- [高度なフック設定](README.md#方法3-pretooluse-フック高度)を学ぶ

## ヒント

- 最初は保守的に設定（読み取りのみ）
- 徐々に許可を追加
- `deny`リストで危険なコマンドをブロック
- プロジェクトごとに`.gitignore`に`.claude/settings.local.json`を追加
