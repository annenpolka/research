# Claude Code コマンド自動許可設定ガイド

このプロジェクトは、Claude Codeで特定のコマンドやツールを自動的に許可する方法を調査・実装した結果をまとめています。

## 概要

Claude Codeには、ユーザーの確認なしに特定のツールやコマンドを自動実行するための複数の方法があります：

1. **allowedToolsリスト** - シンプルで推奨される方法
2. **defaultMode設定** - すべてのツールをバイパス（要注意）
3. **PreToolUseフック** - 高度な条件付き制御

## 方法1: allowedToolsリスト（推奨）

最もシンプルで安全な方法です。許可するツールを明示的にリストアップします。

### 設定ファイル: `.claude/settings.json`

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep",
      "Bash(ls :*)",
      "Bash(pwd)",
      "Bash(git status)",
      "Bash(git diff :*)",
      "Bash(git log :*)",
      "Bash(npm run :*)",
      "Bash(pytest :*)",
      "Write",
      "Edit"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Bash(rm -rf :*)",
      "Bash(dd :*)"
    ]
  }
}
```

### パターンの書き方

- **基本ツール**: `"Read"`, `"Write"`, `"Edit"`, `"Glob"`, `"Grep"`
- **Bashコマンド**: `"Bash(git status)"` - 特定のコマンドのみ
- **ワイルドカード**: `"Bash(git :*)"` - git関連のすべてのコマンド
- **ファイルパターン**: `"Read(*.md)"` - 特定の拡張子のみ
- **ディレクトリ**: `"Read(docs/**)"` - docsディレクトリ配下すべて

### 利点

- 設定が簡単で読みやすい
- スクリプトが不要
- チームで共有しやすい
- セキュリティリスクが明確

## 方法2: defaultModeでバイパス

すべての許可確認をスキップします。**開発環境でのみ使用してください**。

### 設定ファイル: `.claude/settings.json`

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

### 警告

- すべてのツールが自動実行される
- セキュリティリスクが高い
- 本番環境では使用しないこと
- 個人の実験環境での使用を推奨

### コマンドラインフラグ

一時的にバイパスする場合：

```bash
claude-code --dangerously-skip-permissions
```

または特定のツールのみ：

```bash
claude-code --allowedTools "Read,Write,Bash(git :*)"
```

## 方法3: PreToolUseフック（高度）

条件に基づいて動的に許可/拒否を決定します。

### 設定ファイル: `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/conditional-approve.sh"
          }
        ]
      }
    ]
  }
}
```

### フックスクリプト: `.claude/hooks/conditional-approve.sh`

```bash
#!/bin/bash
# Conditional auto-approve hook

TOOL_NAME="${CLAUDE_TOOL_NAME}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT}"

# 読み取り専用コマンドを自動許可
if echo "${TOOL_INPUT}" | grep -qE "^(ls|pwd|git status|git diff|git log)"; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "permissionDecisionReason": "Safe read-only command"
  }
}
EOF
    exit 0
fi

# それ以外は確認を求める
cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "ask",
    "permissionDecisionReason": "Command requires confirmation"
  }
}
EOF
exit 0
```

### 許可決定の種類

- **allow**: 自動許可（確認なし）
- **ask**: ユーザーに確認を求める
- **deny**: 拒否（実行させない）

### 利点

- 複雑な条件ロジックが可能
- コマンドの引数を検査できる
- 動的な決定ができる
- ログや監査が可能

### 欠点

- シェルスクリプトの知識が必要
- デバッグが難しい
- 保守が複雑

## 設定ファイルの優先順位

Claude Codeは以下の順序で設定を読み込みます（後のものが優先）：

1. **ユーザーレベル**: `~/.claude/settings.json`
   - すべてのプロジェクトに適用
   - 個人の好みや汎用的な設定

2. **プロジェクトレベル**: `.claude/settings.json`
   - プロジェクト固有の設定
   - Gitにコミットしてチームで共有

3. **ローカルプロジェクト**: `.claude/settings.local.json`
   - 個人的なオーバーライド
   - Gitignoreに追加（共有しない）

4. **コマンドラインフラグ**
   - セッション固有の設定
   - 一時的な使用

## 実用例

### 例1: リサーチプロジェクト

研究環境では読み取り操作を自由に、書き込みは制限：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Glob",
      "Grep",
      "Bash(ls :*)",
      "Bash(find :*)",
      "Bash(cat :*)",
      "Bash(git :*)"
    ]
  }
}
```

### 例2: Web開発プロジェクト

npm/yarn/gitコマンドを自動許可：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**)",
      "Edit(src/**)",
      "Bash(npm :*)",
      "Bash(yarn :*)",
      "Bash(git status)",
      "Bash(git diff :*)",
      "Bash(git add :*)",
      "Bash(git commit :*)"
    ],
    "deny": [
      "Write(.env*)",
      "Edit(.env*)",
      "Bash(rm :*)",
      "Bash(git push --force :*)"
    ]
  }
}
```

### 例3: Python開発

pytest、pip、仮想環境を許可：

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(*.py)",
      "Edit(*.py)",
      "Bash(pytest :*)",
      "Bash(python -m :*)",
      "Bash(pip install :*)",
      "Bash(source :*)"
    ]
  }
}
```

## セキュリティのベストプラクティス

### 推奨事項

1. **最小権限の原則**: 必要最小限のツールのみ許可
2. **denyリストの活用**: 危険なコマンドを明示的にブロック
3. **機密情報の保護**: .envファイルなどへのアクセスを拒否
4. **パターンの制限**: ワイルドカードは慎重に使用
5. **定期的な見直し**: 設定を定期的にレビュー

### 危険なコマンド例（必ずdenyに追加）

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf :*)",
      "Bash(dd :*)",
      "Bash(mkfs :*)",
      "Bash(format :*)",
      "Bash(git push --force :*)",
      "Bash(sudo :*)",
      "Read(.env*)",
      "Read(**/secrets/**)",
      "Read(**/.git/config)",
      "Write(.env*)"
    ]
  }
}
```

## トラブルシューティング

### 設定が適用されない

1. JSONの構文を確認（カンマ、括弧など）
2. ファイルパスが正しいか確認
3. Claude Codeを再起動
4. 設定ファイルの権限を確認

### フックが実行されない

1. スクリプトに実行権限があるか確認: `chmod +x .claude/hooks/*.sh`
2. シェバン（`#!/bin/bash`）が正しいか確認
3. パスが絶対パスか相対パスか確認
4. ログ出力でデバッグ（stderr使用）

### JSON検証

設定ファイルの構文チェック：

```bash
# jqでJSON検証
cat .claude/settings.json | jq .

# または
python -m json.tool .claude/settings.json
```

## 参考リンク

- [Claude Code 公式ドキュメント](https://code.claude.com/docs/)
- [Hooks リファレンス](https://code.claude.com/docs/en/hooks.md)
- [IAM・権限管理](https://code.claude.com/docs/en/iam.md)
- [Settings ガイド](https://code.claude.com/docs/en/settings.md)

## まとめ

| 方法 | 難易度 | 柔軟性 | セキュリティ | 推奨度 |
|------|--------|--------|--------------|--------|
| allowedTools | 低 | 中 | 高 | ⭐⭐⭐⭐⭐ |
| defaultMode | 低 | 低 | 低 | ⭐ (開発のみ) |
| PreToolUseフック | 高 | 高 | 中〜高 | ⭐⭐⭐ (高度な用途) |

**ほとんどの場合、`allowedTools`を使用することを強く推奨します。**

シンプルで、安全で、メンテナンスしやすいです。
