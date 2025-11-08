#!/bin/bash
# PostToolUse Hook: TypeScript/TSXファイルの自動フォーマット
#
# 設定方法:
# ~/.config/claude-code/settings.json に以下を追加:
# {
#   "hooks": {
#     "PostToolUse": {
#       "command": "~/.claude/hooks/format-ts.sh",
#       "matchers": [
#         {"event": "Edit|Write", "file_path": ".*\\.(ts|tsx)$"}
#       ]
#     }
#   }
# }

file_path="$1"
event="$2"

# イベントがEditまたはWriteで、ファイルがts/tsxの場合
if [[ "$event" =~ (Edit|Write) ]] && [[ "$file_path" =~ \.(ts|tsx)$ ]]; then
    echo "📝 Formatting TypeScript file: $file_path"

    # Prettierが利用可能かチェック
    if command -v prettier &> /dev/null; then
        prettier --write "$file_path" 2>&1

        if [ $? -eq 0 ]; then
            echo "✅ Formatted successfully with Prettier"
        else
            echo "⚠️ Prettier encountered an error"
        fi
    else
        echo "⚠️ Prettier not found. Install with: npm install -g prettier"
    fi

    # ESLintで自動修正も実行（オプション）
    if command -v eslint &> /dev/null; then
        eslint --fix "$file_path" 2>&1

        if [ $? -eq 0 ]; then
            echo "✅ Linted successfully with ESLint"
        else
            echo "⚠️ ESLint found issues that couldn't be auto-fixed"
        fi
    fi
fi

exit 0
