#!/bin/bash

# Beads完全ローカル運用セットアップスクリプト
# このスクリプトは、beadsを非侵襲的にセットアップします
# - リポジトリのファイル構造に変更なし
# - コミット対象が増えない
# - .git/info/excludeを使用

set -e  # エラーで停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ヘッダー表示
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Beads完全ローカル運用セットアップ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. beadsがインストールされているか確認
echo -e "${YELLOW}[1/6]${NC} beadsのインストールを確認中..."
if ! command -v bd >/dev/null 2>&1; then
    echo -e "${RED}✗ エラー: beads (bd) がインストールされていません${NC}"
    echo ""
    echo "beadsをインストールしてください："
    echo "  go install github.com/steveyegge/beads/cmd/bd@latest"
    echo ""
    echo "または："
    echo "  brew install steveyegge/tap/beads"
    exit 1
fi
echo -e "${GREEN}✓ beads がインストールされています${NC}"

# 2. gitリポジトリかどうか確認
echo -e "${YELLOW}[2/6]${NC} gitリポジトリを確認中..."
if [ ! -d ".git" ]; then
    echo -e "${RED}✗ エラー: このディレクトリはgitリポジトリではありません${NC}"
    echo "gitリポジトリのルートで実行してください"
    exit 1
fi
echo -e "${GREEN}✓ gitリポジトリです${NC}"

# 3. beadsを初期化
echo -e "${YELLOW}[3/6]${NC} beadsを初期化中..."
if [ -d ".beads" ]; then
    echo -e "${BLUE}ℹ .beads/ ディレクトリは既に存在します（スキップ）${NC}"
else
    echo "  実行: bd init --skip-merge-driver --quiet"
    if bd init --skip-merge-driver --quiet; then
        echo -e "${GREEN}✓ beads を初期化しました${NC}"
    else
        echo -e "${RED}✗ beads の初期化に失敗しました${NC}"
        exit 1
    fi
fi

# 4. .git/info/excludeに追加
echo -e "${YELLOW}[4/6]${NC} .git/info/exclude に .beads/ を追加中..."
if grep -q "^\.beads/$" .git/info/exclude 2>/dev/null; then
    echo -e "${BLUE}ℹ .git/info/exclude には既に .beads/ が含まれています（スキップ）${NC}"
else
    echo ".beads/" >> .git/info/exclude
    echo -e "${GREEN}✓ .git/info/exclude に .beads/ を追加しました${NC}"
fi

# 5. .gitattributesをクリーンアップ
echo -e "${YELLOW}[5/6]${NC} .gitattributes をクリーンアップ中..."
if [ -f ".gitattributes" ]; then
    if grep -q "\.beads/.*merge=beads" .gitattributes 2>/dev/null; then
        echo "  .gitattributes からbeadsエントリを削除します..."
        sed -i.bak '/\.beads\/.*merge=beads/d' .gitattributes
        rm -f .gitattributes.bak

        # .gitattributesが空になったら削除
        if [ ! -s ".gitattributes" ]; then
            rm .gitattributes
            echo -e "${GREEN}✓ 空の .gitattributes を削除しました${NC}"
        else
            echo -e "${GREEN}✓ .gitattributes からbeadsエントリを削除しました${NC}"
        fi
    else
        echo -e "${BLUE}ℹ .gitattributes にbeadsエントリはありません（スキップ）${NC}"
    fi
else
    echo -e "${BLUE}ℹ .gitattributes は存在しません（スキップ）${NC}"
fi

# 6. 動作確認
echo -e "${YELLOW}[6/7]${NC} セットアップを検証中..."
if git status --porcelain | grep -q "^?? \.beads/"; then
    echo -e "${RED}✗ 警告: .beads/ がgitで追跡されています${NC}"
    echo "以下を実行して修正してください："
    echo "  echo '.beads/' >> .git/info/exclude"
    exit 1
fi
echo -e "${GREEN}✓ .beads/ はgitで無視されています${NC}"

# 7. ユーザー設定（~/.claude/CLAUDE.md）に設定を追記
echo -e "${YELLOW}[7/7]${NC} ユーザー設定にbeads設定を追記中..."
CLAUDE_CONFIG_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_CONFIG_DIR/CLAUDE.md"

# ~/.claudeディレクトリがなければ作成
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    mkdir -p "$CLAUDE_CONFIG_DIR"
    echo -e "${GREEN}✓ $CLAUDE_CONFIG_DIR を作成しました${NC}"
fi

# CLAUDE.mdに追記すべき内容
BEADS_SECTION_MARKER="## Issue Tracking with bd (beads)"

# 既に設定が存在するかチェック
if [ -f "$CLAUDE_MD" ] && grep -q "$BEADS_SECTION_MARKER" "$CLAUDE_MD"; then
    echo -e "${BLUE}ℹ ~/.claude/CLAUDE.md には既にbeads設定が含まれています（スキップ）${NC}"
else
    # CLAUDE.mdに追記
    cat >> "$CLAUDE_MD" << 'EOF'

## Issue Tracking with bd (beads)

**IMPORTANT**: Projects may use **bd (beads)** for issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods in projects that have beads configured.

**NOTE**: Beadsは**完全ローカルモード**で使用されます。`.beads/`ディレクトリはgitignoreされており、コミット対象外です。

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Local-first: ローカルで動作し、gitには影響しません
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**
```bash
bd ready --json
```

**Create new issues:**
```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**
```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**
```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Local-Only Operation

Beadsは完全にローカルで動作します：

- `.beads/`ディレクトリはgitignoreされています
- コミット時に`.beads/issues.jsonl`を含める必要はありません
- git操作は通常通り行えます（beadsは影響しません）
- データはこのマシンでのみ保持されます

### Initial Setup (for Agents)

Beadsがまだ初期化されていない場合:

```bash
# 1. Initialize beads
bd init --skip-merge-driver --quiet

# 2. Add to .git/info/exclude
echo ".beads/" >> .git/info/exclude

# 3. Verify .beads/ is ignored
git status | grep -q ".beads" && echo "WARNING: .beads/ is tracked!" || echo "OK: .beads/ is ignored"
```

### Important Rules

- ✅ Use bd for ALL task tracking (if project has .beads/ directory)
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Remember: `.beads/` is local-only, not committed to git
- ❌ Do NOT create markdown TODO lists in projects with beads
- ❌ Do NOT use external issue trackers in projects with beads
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT try to commit `.beads/` files to git

### Limitations of Local-Only Mode

- ❌ Data is not synced across machines
- ❌ Cannot share issues with team members
- ❌ Data will be lost if machine is changed (manual backup required)
- ✅ However, projects are designed for single-machine, single-agent use

### Troubleshooting

If `.beads/` accidentally gets added to git:

```bash
git rm -r --cached .beads/
echo ".beads/" >> .git/info/exclude
git status
```

EOF

    echo -e "${GREEN}✓ ~/.claude/CLAUDE.md にbeads設定を追記しました${NC}"
fi

# 成功メッセージ
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  セットアップが完了しました！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}基本的な使い方：${NC}"
echo ""
echo "  # タスクを作成"
echo "  bd create \"タスクの説明\" -p 1 --json"
echo ""
echo "  # 準備完了のタスクを表示"
echo "  bd ready --json"
echo ""
echo "  # タスク一覧を表示"
echo "  bd list --json"
echo ""
echo "  # タスクのステータスを更新"
echo "  bd update bd-1 --status in_progress --json"
echo ""
echo "  # タスクを完了"
echo "  bd close bd-1 --reason \"完了\" --json"
echo ""
echo -e "${BLUE}重要事項：${NC}"
echo "  ✓ .beads/ は完全にローカルのみで使用されます"
echo "  ✓ コミット対象には含まれません"
echo "  ✓ リポジトリのファイル構造に変更はありません"
echo "  ✓ git操作は通常通り行えます"
echo ""
echo -e "${YELLOW}注意：${NC}"
echo "  • データはこのマシンでのみ保持されます"
echo "  • 他のマシンとは同期されません"
echo "  • マシン変更時は .beads/ を手動でバックアップしてください"
echo ""
