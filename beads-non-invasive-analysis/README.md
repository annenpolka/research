# Beads非侵襲性分析

## 概要

このプロジェクトは、[steveyegge/beads](https://github.com/steveyegge/beads) リポジトリがリポジトリや指示ファイル（AGENTS.md等）に対して非侵襲的な方法をサポートしているかをコードレベルで調査したものです。

## 🚀 クイックスタート

**一発でbeadsをローカルセットアップしたい場合は、このスクリプトを実行してください：**

```bash
./setup-beads-local.sh
```

このスクリプトは以下を自動的に実行します：
- beadsの初期化（`bd init --skip-merge-driver --quiet`）
- `.git/info/exclude` への `.beads/` の追加
- `.gitattributes` のクリーンアップ
- セットアップの検証
- **ユーザー設定（~/.claude/AGENTS.md）への設定追記**（重複チェック付き）

**特徴：**
- ✅ リポジトリのファイル構造に変更なし
- ✅ コミット対象が増えない
- ✅ 完全にローカルのみで動作
- ✅ 非侵襲的な設計
- ✅ ユーザーのグローバル設定に自動追記（重複なし）

## 調査日

2025-11-07

## 調査対象

- リポジトリ: <https://github.com/steveyegge/beads>
- 言語: Go
- 主要コンポーネント:
  - `cmd/bd/init.go` - 初期化処理
  - `cmd/bd/config.go` - 設定管理
  - `internal/configfile/configfile.go` - 設定ファイル処理
  - README.md、AGENTS.md - ドキュメント

## 結論

**Beadsは部分的に非侵襲的だが、gitフックとマージドライバーのインストールにより、一定の侵襲性を持つ。**

### 非侵襲的な点（⭕）

1. **最小限のセットアップ**
   - `bd init`のみでセットアップ完了
   - 外部サーバーや複雑な設定管理システム不要
   - すべてのデータは`.beads/`ディレクトリ内に格納

2. **既存ファイル構造の保護**
   - 既存のソースコードやドキュメントを変更しない
   - プロジェクトルートに新しいファイルを作成しない（`.beads/`ディレクトリ以外）
   - AGENTS.mdやCLAUDE.mdを自動的に変更しない

3. **バージョン管理との統合**
   - gitを使用してデータを同期
   - `.beads/issues.jsonl`のみをコミット対象とし、SQLiteキャッシュ（`.db`ファイル）は`.gitignore`で除外
   - 既存のgitワークフローに追加される形で動作

4. **非破壊的な動作**
   - 既存のgitフックはバックアップされる（`.backup`サフィックス付き）
   - 既存の設定ファイルを上書きせず、自動移行メカニズムを提供

### 侵襲的な点（❌）

1. **Gitフックのインストール**
   - `pre-commit`フック: コミット前に`bd sync --flush-only`を実行してJSONLに変更を反映
   - `post-merge`フック: マージ後に`bd import`でJSONLの更新をデータベースに同期
   - 既存フックがある場合はバックアップされるが、デフォルトでインストールされる

2. **`.gitattributes`の変更**
   - カスタムマージドライバーを設定するため、`.gitattributes`に以下を追加:

     ```gitattributes
     .beads/beads.jsonl merge=beads
     ```

   - リポジトリ全体のgit設定に影響

3. **git configの変更**
   - ローカルまたはグローバルgit設定にマージドライバーを追加:

     ```bash
     git config merge.beads.driver "bd merge %A %O %L %R"
     git config merge.beads.name "bd JSONL merge driver"
     ```

### 軽減オプション（⚠️）

以下のオプションで侵襲性を軽減可能:

- `--skip-merge-driver`: マージドライバーのセットアップをスキップ
- `--quiet`: 自動インストールモード（エージェント向け、対話なし）
- `--branch <name>`: 専用ブランチでbeadsメタデータを管理（保護されたブランチ対応）

**注意**: `--skip-hooks`や`--no-hooks`オプションは存在せず、gitフックのインストールを完全にスキップする方法は提供されていません。

## AGENTS.mdへの統合方法

### ドキュメントでの推奨方法

READMEとAGENTS.mdによると、以下の手順が推奨されています:

1. **人間の開発者が実行**

   ```bash
   bd init
   ```

2. **AGENTS.mdに以下を追加**（手動）

   ```text
   BEFORE ANYTHING ELSE: run 'bd onboard' and follow the instructions
   ```

3. **エージェントが実行**

   ```bash
   bd onboard
   ```

   - 統合ガイドを受け取る
   - ワークフロー文書が自動生成される

### コードレベルの実装

- **`init.go`はAGENTS.mdを直接変更しない**
- 自動変更のメカニズムは実装されていない
- ユーザーが手動でAGENTS.mdに指示を追加することを前提としている

これは、意図的に「非侵襲的」な設計を採用していると言える。

### 完全ローカル運用モードの場合の推奨追記

`.beads/`をgitignoreに追加して完全ローカル運用する場合、AGENTS.mdには以下のように記載することを推奨します：

#### パターン1: 簡潔版（推奨）

```markdown
## Beads Issue Tracker（ローカルのみ）

このプロジェクトでは、beads issue trackerを完全ローカルモードで使用しています。

### 初回セットアップ（エージェント向け）

beadsがまだ初期化されていない場合:

1. 初期化: `bd init --skip-merge-driver --quiet`
2. 除外設定: `echo ".beads/" >> .git/info/exclude`
3. クリーンアップ: `[ -f .gitattributes ] && rm .gitattributes`
4. 確認: `git status` で `.beads/` が表示されないことを確認
5. 使用開始: `bd create "タスク名" -p 1 --json`

### 基本コマンド

- タスク作成: `bd create "タスク名" -p <優先度> --json`
- 準備完了タスク: `bd ready --json`
- タスク更新: `bd update bd-<ID> --status in_progress --json`
- タスク完了: `bd close bd-<ID> --reason "Completed" --json`
- 一覧表示: `bd list --json`

### 重要事項

- **ローカルのみ**: `.beads/`は`.git/info/exclude`により除外され、コミット対象外
- **同期なし**: このマシンでのみデータが保持されます
- **git操作**: 通常通りコミット・プッシュできます（beadsは影響なし）
- **リポジトリへの影響**: なし（完全に非侵襲的）
```

#### パターン2: 詳細版

```markdown
## Beads Issue Tracker（完全ローカル運用）

このプロジェクトでは、beads issue trackerを使用していますが、**完全にローカルのみ**で動作します。

### セットアップ状態

- ✅ `.beads/`ディレクトリは`.git/info/exclude`により除外されています
- ✅ コミット対象には含まれません
- ✅ リポジトリのファイル構造に一切変更なし
- ✅ 他のマシンや他のエージェントとは同期されません

### エージェント向け初期化手順

beadsが初期化されていない場合、以下を実行:

```bash
# 1. 初期化（静かモード）
bd init --skip-merge-driver --quiet

# 2. .git/info/excludeに追加
echo ".beads/" >> .git/info/exclude

# 3. .gitattributesをクリーンアップ（存在する場合）
[ -f .gitattributes ] && rm .gitattributes

# 4. gitで無視されているか確認
git status | grep -q ".beads" && echo "WARNING: .beads/ is tracked!" || echo "OK: .beads/ is ignored"
```

### ワークフロー

**タスク管理のベストプラクティス:**

1. **セッション開始時**

   ```bash
   bd ready --json  # 準備完了のタスクを確認
   ```

2. **作業中**

   ```bash
   bd create "実装: 機能X" -p 1 --deps discovered-from:bd-Y --json
   bd update bd-Z --status in_progress --json
   ```

3. **タスク完了時**

   ```bash
   bd close bd-Z --reason "実装完了、テスト済み" --json
   ```

4. **セッション終了時**
   - 通常のgit操作のみ（`bd sync`は不要）
   - `.beads/`は自動的に除外される

### 制限事項

- ❌ 他のマシンとの同期不可
- ❌ チームメンバーとの共有不可
- ❌ マシン変更時はデータ消失
- ✅ ただし、このプロジェクトは単一マシン・単一エージェント想定のため問題なし

### トラブルシューティング

`.beads/`がgitに追加されてしまった場合:

```bash
git rm -r --cached .beads/
echo ".beads/" >> .gitignore
git add .gitignore
git commit -m "Ensure .beads/ is ignored"
```

#### パターン3: 最小版

AGENTS.mdが既に詳細なガイドを含んでいる場合、最小限の追記で済ませる:

```markdown
## Beads Issue Tracker

このプロジェクトではbeadsをローカルのみで使用しています。

初期化されていない場合:
```bash
bd init --skip-merge-driver --quiet
echo ".beads/" >> .git/info/exclude
[ -f .gitattributes ] && rm .gitattributes
```

基本コマンド: `bd create "タスク" --json` / `bd ready --json` / `bd list --json`

注意: `.beads/`は`.git/info/exclude`により除外され、コミット対象外です。

### 推奨

- **新規プロジェクト**: パターン1（簡潔版）
- **複雑なワークフロー**: パターン2（詳細版）
- **既存AGENTS.md**: パターン3（最小版）を追記

### 完全に追記しない選択肢

AGENTS.mdに一切追記せず、必要に応じてエージェントに口頭（チャット）で指示する方法もあります:

**メリット:**

- ✅ AGENTS.mdへの変更ゼロ（完全非侵襲）
- ✅ 柔軟性が高い

**デメリット:**

- ❌ エージェントがbeadsの存在を知らない
- ❌ 毎回説明が必要

この方法は、「試験的にbeadsを使ってみたい」場合に適しています。

### `bd onboard`が出力する内容

**重要**: `bd onboard`は**AGENTS.mdに直接書き込みを行いません**。代わりに、標準出力に以下の内容を表示し、ユーザーが手動でコピー&ペーストすることを想定しています。

<details>
<summary><b>bd onboardの完全な出力内容（クリックして展開）</b></summary>

```markdown
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
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
6. **Commit together**: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### MCP Server (Recommended)

If using Claude or MCP-compatible clients, install the beads MCP server:

```bash
pip install beads-mcp
```

Add to MCP config (e.g., `~/.config/claude/config.json`):

```json
{
  "beads": {
    "command": "beads-mcp",
    "args": []
  }
}
```

Then use `mcp__beads__*` functions instead of CLI commands.

### Managing AI-Generated Planning Documents

AI assistants often create planning and design documents during development:

- PLAN.md, IMPLEMENTATION.md, ARCHITECTURE.md
- DESIGN.md, CODEBASE_SUMMARY.md, INTEGRATION_PLAN.md
- TESTING_GUIDE.md, TECHNICAL_DESIGN.md, and similar files

**Best Practice: Use a dedicated directory for these ephemeral files**

**Recommended approach:**

- Create a `history/` directory in the project root
- Store ALL AI-generated planning/design docs in `history/`
- Keep the repository root clean and focused on permanent project files
- Only access `history/` when explicitly asked to review past planning

**Example .gitignore entry (optional):**

```gitignore
# AI planning documents (ephemeral)
history/
```

**Benefits:**

- ✅ Clean repository root
- ✅ Clear separation between ephemeral and permanent documentation
- ✅ Easy to exclude from version control if desired
- ✅ Preserves planning history for archeological research
- ✅ Reduces noise when browsing the project

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Store AI planning docs in `history/` directory
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT clutter repo root with planning documents

For more details, see README.md and QUICKSTART.md.

</details>

### 完全ローカル運用時の調整点

上記の`bd onboard`出力内容は、git同期を前提としています。完全ローカル運用（`.beads/`をgitignore）の場合、以下のセクションは**不要または調整が必要**です:

#### 削除/調整すべき箇所

1. **"Commit together"の記述（ステップ6）**

   ```markdown
   6. **Commit together**: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state
   ```

   → **削除**: `.beads/`はgitignoreされているため不要

2. **"Auto-Sync"セクション全体**

   ```markdown
   ### Auto-Sync

   bd automatically syncs with git:
   - Exports to `.beads/issues.jsonl` after changes (5s debounce)
   - Imports from JSONL when newer (e.g., after `git pull`)
   - No manual export/import needed!
   ```

   → **削除または注記追加**: 「このプロジェクトではローカルのみで使用しており、git同期は行いません」

3. **"Why bd?"の"Git-friendly"**

   ```markdown
   - Git-friendly: Auto-syncs to JSONL for version control
   ```

   → **調整**: 「ローカルで動作し、gitには影響しません」

### 完全ローカル運用向けの簡略版

`bd onboard`の出力をそのまま使わず、前述の**パターン1（簡潔版）**を推奨します。理由：

- ✅ ローカル運用に最適化された内容
- ✅ 不要な同期関連の説明がない
- ✅ 簡潔で理解しやすい
- ✅ 実際の使用方法に焦点を当てている

**結論**: `bd onboard`は非侵襲的（ファイルを直接変更しない）ですが、その出力内容はgit同期を前提としているため、完全ローカル運用の場合は**使用せず、独自の簡略版を作成することを推奨**します。

### オリジナルをベースにした完全ローカル運用版

`bd onboard`の出力内容を最大限尊重しつつ、完全ローカル運用向けに調整したバージョン：

<details>
<summary><b>完全ローカル運用版（クリックして展開）</b></summary>

```markdown
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

**NOTE**: このプロジェクトでは、beadsを**完全ローカルモード**で使用しています。`.beads/`ディレクトリはgitignoreされており、コミット対象外です。

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

beadsは完全にローカルで動作します：

- `.beads/`ディレクトリはgitignoreされています
- コミット時に`.beads/issues.jsonl`を含める必要はありません
- git操作は通常通り行えます（beadsは影響しません）
- データはこのマシンでのみ保持されます

### Initial Setup (for Agents)

beadsがまだ初期化されていない場合:

```bash
# 1. Initialize beads
bd init --skip-merge-driver --quiet

# 2. Verify .beads/ is in .gitignore
grep ".beads/" .gitignore

# 3. Confirm git is ignoring it
git status | grep -q ".beads" && echo "WARNING: .beads/ is tracked!" || echo "OK: .beads/ is ignored"
```

### MCP Server (Recommended)

If using Claude or MCP-compatible clients, install the beads MCP server:

```bash
pip install beads-mcp
```

Add to MCP config (e.g., `~/.config/claude/config.json`):

```json
{
  "beads": {
    "command": "beads-mcp",
    "args": []
  }
}
```

Then use `mcp__beads__*` functions instead of CLI commands.

### Managing AI-Generated Planning Documents

AI assistants often create planning and design documents during development:

- PLAN.md, IMPLEMENTATION.md, ARCHITECTURE.md
- DESIGN.md, CODEBASE_SUMMARY.md, INTEGRATION_PLAN.md
- TESTING_GUIDE.md, TECHNICAL_DESIGN.md, and similar files

**Best Practice: Use a dedicated directory for these ephemeral files**

**Recommended approach:**

- Create a `history/` directory in the project root
- Store ALL AI-generated planning/design docs in `history/`
- Keep the repository root clean and focused on permanent project files
- Only access `history/` when explicitly asked to review past planning

**Example .gitignore entry (optional):**

```gitignore
# AI planning documents (ephemeral)
history/
```

**Benefits:**

- ✅ Clean repository root
- ✅ Clear separation between ephemeral and permanent documentation
- ✅ Easy to exclude from version control if desired
- ✅ Preserves planning history for archeological research
- ✅ Reduces noise when browsing the project

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Store AI planning docs in `history/` directory
- ✅ Remember: `.beads/` is local-only, not committed to git
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT clutter repo root with planning documents
- ❌ Do NOT try to commit `.beads/` files to git

### Limitations of Local-Only Mode

- ❌ Data is not synced across machines
- ❌ Cannot share issues with team members
- ❌ Data will be lost if machine is changed (manual backup required)
- ✅ However, this project is designed for single-machine, single-agent use

### Troubleshooting

If `.beads/` accidentally gets added to git:

```bash
git rm -r --cached .beads/
echo ".beads/" >> .gitignore
git add .gitignore
git commit -m "Ensure .beads/ is ignored"
```

For more details about beads functionality, see the official README.md and QUICKSTART.md.

```

</details>

### 変更点の詳細

オリジナルの`bd onboard`出力からの主な変更点：

1. **冒頭に注記追加**
   ```markdown
   **NOTE**: このプロジェクトでは、beadsを**完全ローカルモード**で使用しています。
   ```

2. **"Why bd?"セクションの調整**
   - "Git-friendly: Auto-syncs to JSONL for version control" → "Local-first: ローカルで動作し、gitには影響しません"

3. **"Workflow for AI Agents"のステップ6を削除**
   - "Commit together" → 削除（不要）

4. **"Auto-Sync"セクション全体を置き換え**
   - 新セクション："Local-Only Operation"に変更
   - ローカル運用の特徴を明記

5. **"Initial Setup"セクション追加**
   - エージェント向けの初期化手順
   - .gitignore確認コマンド

6. **"Important Rules"に追加**
   - "Remember: `.beads/` is local-only, not committed to git"
   - "Do NOT try to commit `.beads/` files to git"

7. **"Limitations of Local-Only Mode"セクション追加**
   - 完全ローカル運用の制限事項を明記

8. **"Troubleshooting"セクション追加**
   - `.beads/`が誤ってgitに追加された場合の対処法

### 保持した内容

以下のセクションはオリジナルから**変更なし**で保持：

- ✅ Issue Types
- ✅ Priorities
- ✅ MCP Server設定
- ✅ Managing AI-Generated Planning Documents
- ✅ Quick Startコマンド
- ✅ Important Rulesの大部分

この調整版は、オリジナルの構成と内容を最大限尊重しつつ、完全ローカル運用に必要な変更のみを加えています。

## 初期化プロセスの詳細

### `bd init`が実行すること

1. **ディレクトリとファイルの作成**
   - `.beads/` ディレクトリ（パーミッション: 0750）
   - `.beads/beads.db` - SQLiteデータベース
   - `.beads/issues.jsonl` - バージョン管理対象のイシューデータ
   - `.beads/metadata.json` - バージョンとリポジトリ識別子
   - `.beads/.gitignore` - データベースファイルとランタイムファイルを除外

2. **Gitフックのインストール**
   - `pre-commit`: 変更のフラッシュとJSONLのステージング
   - `post-merge`: マージ後のインポート
   - 既存フックは`.backup`サフィックスでバックアップ

3. **Gitマージドライバーの設定**
   - `.gitattributes`へのエントリ追加
   - git configの更新

4. **既存イシューのインポート**
   - gitから既存の問題を自動的にインポート

### `.beads/.gitignore`の内容

```gitignore
# SQLite artifacts ignored
*.db
*.db-journal
*.db-wal
*.db-shm

# Runtime files ignored
daemon.lock
daemon.log
daemon.pid
bd.sock

# These are explicitly tracked
!*.jsonl
!metadata.json
!config.json
```

この設計により、一時的なデータベースファイルはバージョン管理から除外され、JSONLファイルのみがコミット対象となる。

## 設定ファイルの管理

### 保存場所

- プロジェクトごとに`.beads/metadata.json`に保存
- 形式: JSON
- パーミッション: 0600（所有者のみ読み書き可能）

### 構造

```json
{
  "Database": "beads.db",
  "Version": "...",
  "JSONLExport": "beads.jsonl"
}
```

### 設定の変更

以下のコマンドで設定を管理:

```bash
bd config set <key> <value>  # 値を設定
bd config get <key>          # 値を取得
bd config list               # 全設定を表示
bd config unset <key>        # 値を削除
```

### レガシー移行

- 旧形式の`config.json`が存在する場合、自動的に`metadata.json`に移行
- 移行後、旧ファイルは削除される（ベストエフォート）

## Gitフックの実装詳細

### Pre-commit フック

```bash
#!/bin/sh
# bd (beads) pre-commit hook

if ! command -v bd >/dev/null 2>&1; then
    exit 0
fi

if [ ! -d ".beads" ]; then
    exit 0
fi

# Flush pending changes to JSONL
bd sync --flush-only

# Stage the updated JSONL file
git add .beads/issues.jsonl
```

**目的**: レース条件を防止し、コミット前にすべての保留中の変更がJSONLに反映されることを保証

### Post-merge フック

```bash
#!/bin/sh
# bd (beads) post-merge hook

if ! command -v bd >/dev/null 2>&1; then
    exit 0
fi

if [ ! -d ".beads" ]; then
    exit 0
fi

# Import updated JSONL after merge
bd import -i .beads/issues.jsonl || true
```

**目的**: マージ後にJSONLの更新内容をローカルデータベースに同期

**注意**: エラーが発生してもマージ自体は失敗させない（`|| true`）

## エージェント統合の設計思想

### コード内のコメントから

`init.go`内に以下のコメントが存在:

```go
// Do this BEFORE quiet mode return so hooks get installed for agents
```

これは、エージェントの自動化を明示的に想定した設計であることを示している。

### 推奨されるエージェントワークフロー

1. **初期化**（`--quiet`モード）

   ```bash
   bd init --quiet
   ```

   - 対話なしで自動セットアップ
   - gitフックとマージドライバーを自動インストール

2. **作業の確認**

   ```bash
   bd ready --json
   ```

   - ブロッカーのない「準備完了」の作業を取得

3. **イシューの作成**

   ```bash
   bd create "Issue title" -t bug -p 1 --deps discovered-from:bd-100 --json
   ```

   - 依存関係を設定してコンテキストを維持

4. **作業の更新**

   ```bash
   bd update bd-42 --status in_progress --json
   bd close bd-42 --reason "Completed" --json
   ```

5. **セッション終了**

   ```bash
   bd sync
   ```

   - 即座にJSONLにエクスポート、コミット、プル、インポート、プッシュ
   - 30秒のデバウンスを待たずに強制フラッシュ

### MCP Server（推奨）

Claude等のクライアント向けにMCPサーバーが提供されている:

```bash
pip install beads-mcp
```

**利点**:

- ネイティブな関数呼び出し（`mcp__beads__create()`等）
- シェルコマンドの代わりにプログラマティックなAPI
- 自動ワークスペース検出
- 構造化されたJSONレスポンス
- 複数リポジトリの自動ルーティング

## 非侵襲性の評価

### 「非侵襲的」の定義

beadsが「非侵襲的」と謳う根拠:

1. **ゼロセットアップ**: `bd init`だけで動作開始
2. **外部依存なし**: サーバーや設定管理システム不要
3. **プロジェクト構造の保護**: 既存コードやドキュメントを変更しない
4. **段階的な採用**: 既存プロジェクトに「追加」される形で統合

### 実際の侵襲性

しかし、コードレベルの調査により、以下の侵襲性が確認された:

1. **Gitフックの強制インストール**
   - スキップオプションが存在しない
   - 既存フックをバックアップするが、上書きする

2. **Gitリポジトリ設定の変更**
   - `.gitattributes`への追加
   - git configへの追加

3. **Gitワークフローへの影響**
   - すべてのコミットで`bd sync`が実行される
   - すべてのマージで`bd import`が実行される

### 結論

beadsは**相対的に非侵襲的**である。以下の観点から:

- **プロジェクト構造**: 影響なし（`.beads/`のみ）
- **ソースコード**: 影響なし
- **ドキュメント**: 自動変更なし（AGENTS.mdは手動追加）
- **Gitワークフロー**: ⚠️ フックとマージドライバーにより影響あり

しかし、gitフックの強制インストールは、一部のプロジェクトや開発者にとって受け入れられない可能性がある。

## 推奨事項

### ユースケース別の評価

#### ✅ beadsが適している場合

- 新規プロジェクト
- エージェント駆動の開発が中心
- gitフックの使用に抵抗がない
- 長期的なタスク管理が必要

#### ⚠️ 慎重に検討すべき場合

- 厳格なgitワークフローがある既存プロジェクト
- カスタムgitフックを既に使用している
- CI/CDパイプラインとの統合が必要
- 複数の開発者がいる大規模プロジェクト

#### ❌ beadsが適していない場合

- gitフックの使用が禁止されている
- 読み取り専用のリポジトリ
- `.beads/`ディレクトリをコミットできない環境
- 外部ツールへの依存を最小限にしたい

### 改善提案

beadsがより非侵襲的になるための提案:

1. **`--no-hooks`オプションの追加**
   - gitフックのインストールを完全にスキップ
   - ユーザーが手動で`bd sync`を実行する選択肢を提供

2. **段階的なオンボーディング**
   - 初回は最小限のセットアップ
   - gitフックやマージドライバーは後から追加可能

3. **AGENTS.md自動更新のオプション**
   - `--update-agents-md`フラグで自動追加
   - デフォルトは手動のまま

## 参考資料

- [Beads GitHubリポジトリ](https://github.com/steveyegge/beads)
- [README.md](https://raw.githubusercontent.com/steveyegge/beads/main/README.md)
- [AGENTS.md](https://raw.githubusercontent.com/steveyegge/beads/main/AGENTS.md)
- [cmd/bd/init.go](https://github.com/steveyegge/beads/blob/main/cmd/bd/init.go)
- [cmd/bd/config.go](https://github.com/steveyegge/beads/blob/main/cmd/bd/config.go)
- [internal/configfile/configfile.go](https://github.com/steveyegge/beads/blob/main/internal/configfile/configfile.go)

## 調査方法

このプロジェクトでは、以下の方法でbeadsの非侵襲性を調査しました:

1. **ドキュメント分析**
   - README.md、AGENTS.mdの精読
   - 「non-invasive」「setup」「configuration」に関する記述の抽出

2. **コードレビュー**
   - `cmd/bd/init.go`の完全な解析
   - `cmd/bd/config.go`の設定管理ロジックの確認
   - `internal/configfile/configfile.go`の設定ファイル処理の確認

3. **動作分析**
   - 初期化プロセスのステップ特定
   - 作成されるファイルとディレクトリのリスト化
   - Gitへの影響の評価

4. **フラグとオプションの調査**
   - コマンドラインフラグの完全なリスト作成
   - 各フラグの動作と影響範囲の確認

## 元のリポジトリにコミット対象を増やさずに使う方法

### 🎯 完全ローカル運用モード

beadsは本来git同期を前提とした設計ですが、以下の方法で**完全にローカルのみ**で使用できます。

#### 方法1A: `.git/info/exclude`を使用（最も非侵襲的）⭐

**完全に非侵襲的**な方法です。リポジトリのファイル構造に一切変更を加えません。

**手順:**

1. **beadsを初期化**

   ```bash
   bd init --skip-merge-driver
   ```

2. **`.git/info/exclude`に追加**

   ```bash
   echo ".beads/" >> .git/info/exclude
   ```

3. **`.gitattributes`を削除**（作成されている場合）

   ```bash
   rm .gitattributes
   ```

4. **動作確認**

   ```bash
   git status  # .beads/が表示されないことを確認
   ```

**メリット:**

- ✅ `.beads/`配下のすべてのファイルがgitから除外される
- ✅ **コミット対象が一切増えない**（`.gitignore`も不要）
- ✅ **リポジトリのファイル構造に一切変更なし**
- ✅ gitフックが存在していても、`git add .beads/issues.jsonl`が失敗するだけで、コミット自体は成功する（ソフトフェイル設計）
- ✅ 既存のリポジトリに完全に影響なし
- ✅ `.gitignore`をコミットする必要がない

**デメリット:**

- ❌ 複数マシン間でbeadsデータを同期できない
- ❌ チームメンバーとイシューを共有できない
- ❌ マシンを変更するとデータが失われる
- ⚠️ `.git/info/exclude`は各マシンで個別に設定が必要

**注意:**

- `.git/info/exclude`は、`.gitignore`と同じ構文を使用しますが、リポジトリにコミットされません
- ローカルマシンのみで有効です
- 他のマシンやクローンには引き継がれません

#### 方法1B: `.gitignore`に追加（シンプル）

`.git/info/exclude`が使えない場合や、設定を残したい場合の方法です。

**手順:**

1. **beadsを初期化**

   ```bash
   bd init --skip-merge-driver
   ```

2. **プロジェクトのルート`.gitignore`に追加**

   ```bash
   echo ".beads/" >> .gitignore
   ```

3. **`.gitattributes`を削除**（作成されている場合）

   ```bash
   git rm .gitattributes  # または手動で.beadsエントリを削除
   ```

4. **`.gitignore`をコミット**

   ```bash
   git add .gitignore
   git commit -m "Add .beads/ to gitignore for local-only beads usage"
   ```

5. **動作確認**

   ```bash
   git status  # .beads/が表示されないことを確認
   ```

**メリット:**

- ✅ `.beads/`配下のすべてのファイルがgitから除外される
- ✅ コミット対象が増えない（`.gitignore`自体は1回のみ）
- ✅ gitフックが存在していても、`git add .beads/issues.jsonl`が失敗するだけで、コミット自体は成功する（ソフトフェイル設計）
- ✅ 既存のリポジトリに一切影響なし
- ✅ 設定が他のマシンやクローンにも引き継がれる

**デメリット:**

- ❌ 複数マシン間でbeadsデータを同期できない
- ❌ チームメンバーとイシューを共有できない
- ❌ マシンを変更するとデータが失われる
- ⚠️ `.gitignore`をコミットする必要がある（1ファイル増加）

#### 方法2: 自動同期を無効化

gitフックは残したまま、自動同期だけを無効化する方法です。

**手順:**

1. **すべてのコマンドで`--no-auto-flush`フラグを使用**

   ```bash
   bd --no-auto-flush create "Issue title"
   bd --no-auto-flush update bd-1 --status in_progress
   bd --no-auto-flush list
   ```

2. **デーモンを停止**（自動同期を行わない）

   ```bash
   bd daemon --stop
   ```

3. **手動同期が必要な場合のみ実行**

   ```bash
   bd sync --flush-only  # JSONLにエクスポートのみ（git操作なし）
   ```

**メリット:**

- ✅ 必要に応じて手動で同期できる
- ✅ 通常はローカルのみで動作
- ✅ 柔軟性が高い

**デメリット:**

- ❌ すべてのコマンドでフラグを指定する必要がある
- ❌ デーモン再起動時に注意が必要

#### 方法3: Gitフックを削除

初期化後にgitフックを手動で削除する方法です。

**手順:**

1. **beadsを初期化**

   ```bash
   bd init --skip-merge-driver
   ```

2. **gitフックを削除**

   ```bash
   rm .git/hooks/pre-commit
   rm .git/hooks/post-merge
   ```

3. **バックアップされた既存フックを復元**（存在する場合）

   ```bash
   [ -f .git/hooks/pre-commit.backup ] && mv .git/hooks/pre-commit.backup .git/hooks/pre-commit
   [ -f .git/hooks/post-merge.backup ] && mv .git/hooks/post-merge.backup .git/hooks/post-merge
   ```

**メリット:**

- ✅ gitワークフローへの影響が完全に排除される
- ✅ 既存のフックが復元される
- ✅ 通常のコマンドをそのまま使用可能（フラグ不要）

**デメリット:**

- ❌ 自動エクスポート/インポートが行われない
- ❌ 手動で`bd sync`を実行する必要がある

#### 推奨: 方法1A（.git/info/excludeを使用）⭐

**最も推奨される方法は「方法1A」です。**

理由:

1. **完全非侵襲**: リポジトリのファイル構造に一切変更を加えない
2. **シンプル**: 1行追加するだけ（`.git/info/exclude`へ）
3. **効果的**: コミット対象が一切増えない（`.gitignore`も不要）
4. **安全**: gitフックのソフトフェイル設計により、エラーが出てもコミットは成功
5. **可逆的**: `.git/info/exclude`から削除すればいつでも同期モードに戻せる

**方法1Bとの使い分け:**

- **単一マシン専用**: 方法1A（`.git/info/exclude`）
- **複数マシンで同じ設定**: 方法1B（`.gitignore`）
- **チームで設定共有**: 方法1B（`.gitignore`）

### Gitフックのエラーハンドリング

beadsのgitフックは、以下のようにソフトフェイル設計になっています：

**Pre-commitフック:**

```bash
git add .beads/issues.jsonl 2>/dev/null || true
```

- `.beads/issues.jsonl`が存在しない、または追加できない場合でも、コミットは成功する
- エラー出力は抑制される（`2>/dev/null`）

**Post-mergeフック:**

```bash
bd import -i .beads/issues.jsonl || true
```

- インポート失敗時も警告のみで、マージは失敗しない
- コード内コメント: "don't fail the merge, just warn"

この設計により、`.beads/`をgitignoreに追加しても、gitフックが存在していても問題なく動作します。

### 実際の使用例

#### 方法1A: .git/info/excludeを使用（推奨）

```bash
# 初期セットアップ
bd init --skip-merge-driver
echo ".beads/" >> .git/info/exclude
[ -f .gitattributes ] && rm .gitattributes

# 動作確認
git status  # .beads/が表示されないことを確認

# 通常使用（すべてローカルのみ）
bd create "Implement feature X" -p 1
bd list --json
bd update bd-1 --status in_progress
bd close bd-1 --reason "Completed"

# git操作は通常通り（.beads/は含まれない、リポジトリに変更なし）
git status  # クリーンな状態
git add .
git commit -m "Add feature X"
git push
```

#### 方法1B: .gitignoreを使用

```bash
# 初期セットアップ
bd init --skip-merge-driver
echo ".beads/" >> .gitignore
git add .gitignore
git commit -m "Add beads to gitignore for local-only usage"

# 通常使用（すべてローカルのみ）
bd create "Implement feature X" -p 1
bd list --json
bd update bd-1 --status in_progress
bd close bd-1 --reason "Completed"

# git操作は通常通り（.beads/は含まれない）
git status  # .beads/は表示されない
git add .
git commit -m "Add feature X"
git push
```

**注意点:**

- `.beads/`内のデータは完全にローカルのみ
- マシンを変更する際は、`.beads/`ディレクトリを手動でコピーする必要がある
- バックアップ戦略を別途検討すること
- 方法1Aの場合、新しいマシンでは`.git/info/exclude`の再設定が必要

### 同期機能の比較

| 機能 | デフォルト | 方法1A(.git/info/exclude) | 方法1B(.gitignore) | 方法2(--no-auto-flush) | 方法3(フック削除) |
|------|-----------|---------------------------|-------------------|----------------------|------------------|
| **コミット対象** | `.beads/issues.jsonl` | **なし** | なし | なし | なし |
| **リポジトリへの変更** | `.beads/issues.jsonl`<br>`.gitattributes` | **なし** | `.gitignore`のみ | なし | なし |
| **自動エクスポート** | ✅ | ✅（失敗） | ✅（失敗） | ❌ | ✅（失敗） |
| **手動同期** | ✅ | ⚠️（ローカルのみ） | ⚠️（ローカルのみ） | ✅ | ⚠️（要フック再インストール） |
| **複数マシン同期** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **設定の引き継ぎ** | ✅ | ❌（マシン毎に設定） | ✅（.gitignore経由） | ❌ | ❌ |
| **gitフック影響** | あり | あり（無害） | あり（無害） | あり | なし |
| **非侵襲性** | 低 | **最高** | 高 | 中 | 高 |

### 各方法の評価

#### 🥇 方法1A: .git/info/exclude（推奨）

**最も非侵襲的**。リポジトリのファイル構造に一切変更を加えない。

- ✅ コミット対象: 0ファイル増加
- ✅ リポジトリへの変更: なし
- ✅ 完全にローカル
- ⚠️ 各マシンで設定が必要

**適用シーン**: 単一マシンでの研究・開発、試験的な使用

#### 🥈 方法1B: .gitignore

非侵襲的だが、`.gitignore`を1回コミットする必要あり。

- ✅ コミット対象: `.gitignore`のみ（1回）
- ✅ 設定が他のマシンに引き継がれる
- ⚠️ `.gitignore`の変更が必要

**適用シーン**: 複数マシンでの同じ設定、チームでの設定共有

#### 🥉 方法2: --no-auto-flush

柔軟だが、すべてのコマンドでフラグ指定が必要。

- ⚠️ 運用が複雑
- ✅ 完全な制御が可能

**適用シーン**: 高度な制御が必要な場合

#### 方法3: フック削除

gitワークフローへの影響を完全排除できるが、手動同期が必要。

- ⚠️ 自動同期なし
- ✅ gitワークフローへの影響なし

**適用シーン**: gitフックを使いたくない場合

## まとめ

beadsは、AIエージェント向けのイシュートラッキングシステムとして、多くの点で非侵襲的な設計を採用しています。特に、プロジェクト構造やソースコードへの影響を最小限に抑え、すべてのデータを`.beads/`ディレクトリ内に格納する設計は評価できます。

しかし、gitフックとマージドライバーの強制インストールにより、既存のgitワークフローに影響を与える点は注意が必要です。この侵襲性は、beadsの自動同期機能を実現するために不可欠ですが、すべてのプロジェクトやチームに受け入れられるとは限りません。

**ただし、`.beads/`全体を`.gitignore`に追加することで、元のリポジトリにコミット対象を一切増やさずにbeadsを使用できます。** この方法により、完全にローカルのみでbeadsの機能を活用しながら、既存プロジェクトへの影響をゼロに抑えることが可能です。

AGENTS.mdへの統合については、自動変更を行わず、ユーザーが手動で追加する設計を採用しており、この点も非侵襲的と言えます。

総合的には、**beadsは相対的に非侵襲的であり、適切な設定により完全に非侵襲的な運用も可能**と結論づけられます。
