# Quick Start Guide

## セットアップ（5分）

### 1. プロジェクトへの導入

```bash
# プロジェクトルートで実行
cd your-project

# Swarmディレクトリ作成
mkdir -p .claude/swarm
mkdir -p .claude/hooks
mkdir -p .claude/mcp-servers/swarm-coordinator

# サンプルファイルをコピー
# (このリポジトリの examples/ からコピー)
cp path/to/examples/hooks/coordination.py .claude/hooks/
cp path/to/examples/config/hooks.json .claude/hooks/
cp -r path/to/examples/mcp-server/* .claude/mcp-servers/swarm-coordinator/

# MCP設定
cat > .claude/.mcp.json <<EOF
{
  "mcpServers": {
    "swarm-coordinator": {
      "command": "node",
      "args": [".claude/mcp-servers/swarm-coordinator/dist/index.js"]
    }
  }
}
EOF
```

### 2. MCPサーバーのビルド

```bash
cd .claude/mcp-servers/swarm-coordinator
npm install
npm run build
cd ../../../
```

### 3. タスク定義（オプション）

```bash
cat > .claude/swarm/tasks.jsonl <<EOF
{"id":"task-001","description":"リファクタリング: auth モジュール","status":"pending","dependencies":[],"priority":10,"files":["src/auth/**"]}
{"id":"task-002","description":"新機能: ダッシュボード UI","status":"pending","dependencies":[],"priority":8,"files":["src/dashboard/**"]}
EOF
```

### 4. .gitignore 更新

```bash
cat >> .gitignore <<EOF

# Swarm Coordinator
.claude/swarm/.cache/
.claude/swarm/.session
EOF
```

## 使用方法

### シナリオ 1: 単一エージェント（通常使用）

```bash
# 通常通りClaude Codeを使用
claude-code

# フックが自動的に動作し、セッション情報を記録
# ファイル編集時に自動ロック管理
```

### シナリオ 2: 複数エージェント並行実行

#### ターミナル 1: バックエンド担当

```bash
# エージェント名を指定
export CLAUDE_AGENT_NAME="BackendTeam"
claude-code

# プロンプト:
# "task-001 (auth APIの実装) を担当します。
#  swarm_claim_task でタスクをクレームしてください"
```

#### ターミナル 2: フロントエンド担当

```bash
export CLAUDE_AGENT_NAME="FrontendTeam"
claude-code

# プロンプト:
# "task-002 (ダッシュボードUI) を担当します。
#  swarm_claim_task でタスクをクレームしてください"
```

#### ターミナル 3: テスト担当

```bash
export CLAUDE_AGENT_NAME="QATeam"
claude-code

# プロンプト:
# "BackendTeamとFrontendTeamの作業完了を待ち、
#  統合テストを実装してください。
#  swarm_get_state で進捗を確認できます"
```

### エージェント間通信の例

#### BackendTeam からのメッセージ送信

```
User: Auth APIが完成しました。FrontendTeamに通知してください。

Agent: [swarm_send_message ツールを使用]
  - recipient: "FrontendTeam"
  - subject: "Auth API Ready"
  - body: "認証エンドポイントが利用可能です。/api/auth/login と /api/auth/logout を使用できます。"

✓ Message sent to FrontendTeam
```

#### FrontendTeam でのメッセージ受信

```
Agent: [自動的に swarm_get_messages を確認]

📬 1 message(s):

**From**: BackendTeam
**Subject**: Auth API Ready
**Time**: 2025-11-08 14:30:00
**Priority**: normal

認証エンドポイントが利用可能です。/api/auth/login と /api/auth/logout を使用できます。

---
```

### ファイルロックの動作例

#### エージェントA: src/config.ts を編集中

```
Agent A: [Edit tool を使用 → PreToolUse フックが発火]
✓ Acquired lock on src/config.ts

[編集実行]

[PostToolUse フックでロック解放]
✓ Lock released on src/config.ts
```

#### エージェントB: 同じファイルにアクセス試行

```
Agent B: [Edit tool を使用 → PreToolUse フックが発火]

⚠️  File **src/config.ts** is locked by agent **agent-a1b2c3d4**

**Reason**: editing via Edit
**Time remaining**: ~3 minutes

**Suggestions**:
1. Work on a different file
2. Message agent-a1b2c3d4 to coordinate: `swarm_send_message`
3. Wait for lock to expire

[編集がブロックされる]
```

### 状態確認

```bash
# いつでもSwarm全体の状態を確認可能
swarm_get_state
```

出力例:

```
## 🤖 Active Agents (3)

- **BackendTeam** (started: 2025-11-08 14:00:00)
- **FrontendTeam** (started: 2025-11-08 14:05:00)
- **QATeam** (started: 2025-11-08 14:10:00)

## 📋 Tasks

- Pending: 1
- In Progress: 2
- Completed: 1

**In Progress**:
- task-001 (by BackendTeam): リファクタリング: auth モジュール
- task-002 (by FrontendTeam): 新機能: ダッシュボード UI

## 🔒 Active File Locks (2)

- **src/auth/api.ts**
  - Holder: BackendTeam
  - Reason: editing via Edit
  - Expires in: 4 min

- **src/dashboard/index.tsx**
  - Holder: FrontendTeam
  - Reason: editing via Write
  - Expires in: 3 min
```

## トラブルシューティング

### ロックが解放されない

```bash
# ロックは5分で自動解放されます
# または、エージェントを終了すると自動的に全ロック解放
```

### エージェントIDが不明

```bash
# .claude/swarm/.session ファイルを確認
cat .claude/swarm/.session

# または環境変数で明示的に指定
export CLAUDE_AGENT_NAME="MyAgent"
```

### MCPサーバーが起動しない

```bash
# ビルド確認
cd .claude/mcp-servers/swarm-coordinator
npm run build

# 手動起動テスト
node dist/index.js
# Ctrl+C で終了

# ログ確認
# Claude Code起動時に .claude/logs/ を確認
```

### タスクが表示されない

```bash
# tasks.jsonl ファイルを確認
cat .claude/swarm/tasks.jsonl

# フォーマットが正しいか検証（各行が有効なJSON）
cat .claude/swarm/tasks.jsonl | jq .
```

## ベストプラクティス

### 1. エージェント名の命名

明確で分かりやすい名前を使用：

- ✅ "BackendAPI", "FrontendUI", "TestRunner"
- ✅ "Refactoring", "Documentation", "BugFix"
- ❌ "agent-123", "temp", "test"

### 2. タスク設計

- **粒度**: 1-3時間で完了可能なサイズ
- **依存関係**: 明示的に定義
- **ファイルスコープ**: 明確なファイルパターンを指定

### 3. メッセージング

- **件名**: 簡潔で内容が分かるように
- **優先度**: 緊急時のみ "high" を使用
- **ブロードキャスト**: 全体に関わる情報のみ

### 4. ファイルロック

- **細かい編集**: 小さな変更は素早く完了してロック解放
- **大規模リファクタリング**: 事前に他エージェントに通知
- **競合予測**: 同じモジュールを触る可能性がある場合は調整

## 高度な使用例

### カスタムタスク優先度アルゴリズム

```typescript
// mcp-server/src/index.ts を編集
function calculateTaskScore(task: Task, agentId: string): number {
  let score = task.priority || 0;

  // エージェントの専門性を考慮
  if (agentId.includes("Backend") && task.files.some(f => f.includes("api"))) {
    score += 5;
  }

  // 依存関係が少ないタスクを優先
  score -= task.dependencies.length * 2;

  return score;
}
```

### 自動タスク完了検出

```python
# .claude/hooks/post-tool-use.py に追加
def auto_complete_task(agent_id: str, file_path: str):
    """ファイル編集後、タスクが完了したか自動判定"""
    tasks = load_current_tasks(agent_id)

    for task in tasks:
        if task["status"] != "in_progress":
            continue

        # タスクの対象ファイルがすべて編集済みか確認
        if all_files_modified(task["files"]):
            # 自動完了提案
            suggest_task_completion(task["id"])
```

### Webダッシュボード統合

```bash
# 簡易ダッシュボードを起動（オプション）
python3 -m http.server 3030 --directory .claude/swarm
# http://localhost:3030 でJSONLファイルを閲覧可能

# またはリアルタイム可視化（要実装）
# claude-code-hooks-multi-agent-observability を参考に
```

## 次のステップ

1. **実際のプロジェクトで試す**: 小規模なリファクタリングから開始
2. **フィードバック**: 使用感を記録し、改善点を特定
3. **カスタマイズ**: プロジェクト固有のニーズに合わせてフック・MCPを拡張
4. **スケール**: 3人以上のエージェント、長期プロジェクトで検証

---

**問題や質問があれば**: プロジェクトの Issues で報告してください。
