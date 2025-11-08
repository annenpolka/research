#!/bin/bash
# PreToolUse Hook: Claude Codeがファイルを変更する前に自動でGitバックアップを作成
#
# 設定方法:
# ~/.config/claude-code/settings.json に以下を追加:
# {
#   "hooks": {
#     "PreToolUse": {
#       "command": "~/.claude/hooks/git-backup.sh",
#       "matchers": [
#         {"event": "Edit|Write"}
#       ]
#     }
#   }
# }

event="$1"
file_path="$2"

# EditまたはWriteイベントの場合
if [[ "$event" =~ (Edit|Write) ]]; then
    # Gitリポジトリかチェック
    if git rev-parse --is-inside-work-tree &> /dev/null; then
        # 変更があるかチェック
        if ! git diff-index --quiet HEAD -- 2> /dev/null; then
            timestamp=$(date +"%Y-%m-%d %H:%M:%S")
            backup_branch="claude-backup-$(date +%s)"

            echo "🔄 Creating Git backup before changes to: $file_path"

            # 現在のブランチ名を取得
            current_branch=$(git rev-parse --abbrev-ref HEAD)

            # ステージングエリアに追加
            git add -A

            # 一時コミット作成（--no-verifyでフックをスキップ）
            git commit -m "AUTO-BACKUP [$timestamp]: Before Claude changes to $file_path" --no-verify

            if [ $? -eq 0 ]; then
                commit_hash=$(git rev-parse --short HEAD)
                echo "✅ Created backup commit: $commit_hash"
                echo "   To rollback: git reset --soft HEAD~1"
            else
                echo "⚠️ No changes to commit"
            fi
        else
            echo "ℹ️ No uncommitted changes, skipping backup"
        fi
    else
        echo "ℹ️ Not a Git repository, skipping backup"
    fi
fi

exit 0
