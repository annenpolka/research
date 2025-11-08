#!/bin/bash
# PreToolUse Hook: 本番環境ファイルへの変更をブロック
#
# 設定方法:
# ~/.config/claude-code/settings.json に以下を追加:
# {
#   "hooks": {
#     "PreToolUse": {
#       "command": "~/.claude/hooks/protect-prod.sh",
#       "matchers": [
#         {"event": "Edit|Write|Bash", "file_path": ".*/production/.*"}
#       ]
#     }
#   }
# }

event="$1"
file_path="$2"

# 本番環境パスのパターン（必要に応じてカスタマイズ）
PROTECTED_PATHS=(
    "production/"
    "prod/"
    ".env.production"
    "config/production.yml"
    "k8s/production/"
)

# 保護されたパスかチェック
is_protected=false
for pattern in "${PROTECTED_PATHS[@]}"; do
    if [[ "$file_path" == *"$pattern"* ]]; then
        is_protected=true
        break
    fi
done

# 保護されたファイルへの変更をブロック
if [ "$is_protected" = true ]; then
    echo "❌ BLOCKED: Cannot modify production files!"
    echo ""
    echo "File: $file_path"
    echo "Event: $event"
    echo ""
    echo "Reason: This file is in a protected production directory."
    echo "Please:"
    echo "  1. Make changes in a development/staging environment first"
    echo "  2. Test thoroughly"
    echo "  3. Use proper deployment procedures for production"
    echo ""
    exit 1  # 非ゼロで終了してツール実行をブロック
fi

exit 0
