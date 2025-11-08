# Multi-Agent Coordinator for Claude Code

**非侵襲的で軽量なマルチエージェント調整システム**

## 🚀 クイックスタート

### **v2: Skills版** (最新・推奨)

```bash
# Step 1: Claude Codeを起動
claude
```

**Claude内で実行:**
```
/plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
/plugin install swarm-coordinator
```

**特徴:**
- ✅ ビルド不要（npm install不要）
- ✅ Python のみ（Node.js不要）
- ✅ セットアップ時間: **30秒**

詳細: [plugin-v2/INSTALL.md](./plugin-v2/INSTALL.md) | [正しいインストール方法](./CORRECT_INSTALLATION.md)

---

### v1: MCP版（レガシー）

v1はビルドステップが必要なため非推奨です。v2を使用してください。

詳細: [PLUGIN.md](./PLUGIN.md)

---

## 概要

このプロジェクトは、Claude Codeの複数インスタンスを効率的に管理するための調整システムを提案します。既存の3つの優れたアプローチ（mcp_agent_mail、claude-code-hooks-multi-agent-observability、beads）から学んだベストプラクティスを統合し、シンプルでエレガントな設計を実現します。

**3つの使用方法:**
- ⚡ **v2: Skills版** (最新・推奨): ゼロビルド、Python のみ
- 🔌 **v1: MCP版**: 明示的API、Node.js + ビルド必要
- 📦 **手動セットアップ版**: カスタマイズ可能、学習用

## 背景と動機

### 調査対象プロジェクト

1. **[mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail)**
   - メール型の非同期エージェント間通信
   - ファイル予約システムによる競合回避
   - Git + SQLiteの二重永続化
   - 明示的な承認チェーンと人間のオーバーサイト

2. **[claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability)**
   - フック機構を活用したリアルタイム監視
   - WebSocket + SQLiteのイベントトラッキング
   - セキュリティ保護（危険コマンドのブロック）
   - マルチセッション可視化

3. **[beads](https://github.com/steveyegge/beads)**
   - Gitベースの分散メモリシステム
   - ハッシュベースID（衝突回避）
   - 依存関係追跡とタスク管理
   - エージェント中心の設計思想

### 解決すべき課題

複数のコーディングエージェントを並行実行する際の主な課題：

- **編集競合**: 複数エージェントが同じファイルを同時編集
- **状態不一致**: エージェント間でタスク状態が同期されない
- **可観測性の欠如**: 何が起きているか把握できない
- **コンテキスト喪失**: セッション終了後に計画や決定が失われる
- **調整オーバーヘッド**: 人間が手動で調整する必要がある

## 設計哲学

### 核となる原則

1. **非侵襲性**: プロジェクトリポジトリは`.claude/`ディレクトリのみに設定を配置
2. **薄いワークフロー**: 自動化されたテストのように透明で最小限の介入
3. **Gitネイティブ**: バージョン管理とマージフレンドリーなメタデータ
4. **プラグインファースト**: Claude Codeのフック・スキル・MCPを最大限活用
5. **人間中心**: 最終的な制御は常に人間が持つ

### アーキテクチャ概要

```
┌─────────────────────────────────────────────────────┐
│           Claude Code エージェント群                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │             │             │                 │
│       └─────────────┴─────────────┘                 │
│                     │                               │
└─────────────────────┼───────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
   ┌────▼────┐                 ┌────▼────┐
   │  Hooks  │                 │   MCP   │
   │  Layer  │                 │ Server  │
   └────┬────┘                 └────┬────┘
        │                            │
        └─────────────┬──────────────┘
                      │
              ┌───────▼────────┐
              │  Coordination  │
              │     Engine     │
              │                │
              │ • File Locks   │
              │ • Task Queue   │
              │ • State Sync   │
              └───────┬────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
   ┌────▼────┐                 ┌────▼────┐
   │   Git   │                 │ SQLite  │
   │ Storage │                 │  Cache  │
   └─────────┘                 └─────────┘
```

## 主要コンポーネント

### 1. Coordination Hooks

Claude Codeのフック機構を使用してファイルアクセスを管理：

- **PreToolUse Hook**: ファイル編集前にロック取得を試行
- **PostToolUse Hook**: ツール使用後にロックを解放
- **SessionStart Hook**: エージェント登録とタスク取得
- **SessionEnd Hook**: 状態の永続化とクリーンアップ

### 2. Communication MCP Server

軽量なMCPサーバーでエージェント間通信を提供：

- **メッセージング**: 非同期メッセージ交換（mcp_agent_mailの簡略版）
- **タスクキュー**: 依存関係を考慮したタスク割り当て
- **状態共有**: 読み取り専用のグローバル状態アクセス
- **イベント通知**: 重要なイベントのブロードキャスト

### 3. State Tracker

Gitベースの永続化 + SQLiteキャッシュ：

```
.claude/
├── swarm/
│   ├── agents.jsonl         # エージェント登録（Git管理）
│   ├── tasks.jsonl          # タスク定義（Git管理）
│   ├── locks.jsonl          # ファイルロック履歴（Git管理）
│   ├── messages.jsonl       # メッセージログ（Git管理）
│   └── .cache/
│       └── state.db         # SQLiteキャッシュ（.gitignore）
```

**Gitネイティブなメリット**:
- マージフレンドリー: JSONLフォーマットで競合を最小化
- 監査可能: すべての決定がコミット履歴に残る
- 分散型: ブランチごとに独立したエージェント環境

### 4. Observability Dashboard

オプションの軽量Webダッシュボード：

- リアルタイムエージェント状態の可視化
- ファイルロック状況の表示
- タスク依存グラフの描画
- メッセージ履歴の閲覧

## 使用例

### シナリオ: 3つのエージェントでリファクタリング

```bash
# エージェントA: バックエンドAPI
claude-code --session="refactor-api" --agent-name="BackendTeam"

# エージェントB: フロントエンドUI
claude-code --session="refactor-ui" --agent-name="FrontendTeam"

# エージェントC: 統合テスト
claude-code --session="refactor-tests" --agent-name="QATeam"
```

**自動調整フロー**:

1. 各エージェントがSessionStartフックで登録
2. TaskキューからBackendTeamが`src/api/**`、FrontendTeamが`src/ui/**`を割り当て
3. BackendTeamが`src/api/auth.ts`編集時、PreToolUseフックで自動ロック
4. FrontendTeamが同ファイルにアクセス試行→ロック検出→待機
5. BackendTeamが編集完了→PostToolUseでロック解放→FrontendTeam続行
6. QATeamは両方の変更完了を検知して統合テスト実行
7. すべての状態変更がGitにコミット可能な形で記録

### シナリオ: 長期タスクの並行実行

```yaml
# .claude/swarm/tasks.yaml
tasks:
  - id: feature-auth
    description: "ユーザー認証機能の実装"
    files: ["src/auth/**", "tests/auth/**"]
    priority: high

  - id: feature-dashboard
    description: "ダッシュボードUI作成"
    files: ["src/dashboard/**", "tests/dashboard/**"]
    depends_on: []

  - id: integration-test
    description: "統合テスト実装"
    files: ["tests/integration/**"]
    depends_on: ["feature-auth", "feature-dashboard"]
```

エージェントは自動的にタスクを取得し、依存関係に基づいて並行実行されます。

## インストールと設定

### 方法1: プラグイン版（推奨）

**前提条件**: Claude Code CLI

**インストール**:

```bash
# プラグインインストール
claude-code plugin install swarm-coordinator

# MCPサーバービルド（初回のみ）
cd .claude/plugins/swarm-coordinator/mcp-servers/swarm-coordinator
npm install && npm run build
cd ../../../../
```

**使用開始**:

```bash
# 通常通りClaude Codeを使用
claude-code

# プラグインが自動的に:
# ✅ ファイルロックを管理
# ✅ エージェントセッションを追跡
# ✅ MCPツールを提供
```

詳細: [PLUGIN.md](./PLUGIN.md)

---

### 方法2: 手動セットアップ版

**前提条件**:
- Claude Code CLI
- Python 3.9+ （フック用）
- Node.js 18+ （MCPサーバー用）

**セットアップ**:

詳細な手順は [QUICKSTART.md](./QUICKSTART.md) を参照してください。

**概要**:

```bash
# 1. プロジェクトルートで設定
cd your-project

# 2. ファイルをコピー
mkdir -p .claude/hooks .claude/mcp-servers/swarm-coordinator
cp path/to/examples/hooks/coordination.py .claude/hooks/
cp path/to/examples/config/hooks.json .claude/hooks/
cp -r path/to/examples/mcp-server/* .claude/mcp-servers/swarm-coordinator/

# 3. MCPサーバービルド
cd .claude/mcp-servers/swarm-coordinator
npm install && npm run build
cd ../../../

# 4. 使用開始
claude-code
```

## 技術詳細

### ファイルロックプロトコル

```python
# .claude/hooks/pre-tool-use.py
def handle_file_access(tool_name: str, params: dict) -> dict:
    """ファイル編集前のロック取得"""
    if tool_name in ["Edit", "Write"]:
        file_path = params.get("file_path")

        # ロック取得試行
        lock_result = acquire_lock(
            agent_id=get_agent_id(),
            file_path=file_path,
            timeout=300
        )

        if not lock_result.success:
            # ロック取得失敗時の処理
            if lock_result.holder:
                return {
                    "block": True,
                    "message": f"File locked by {lock_result.holder}. "
                               f"Reason: {lock_result.reason}. "
                               f"Consider working on different files or "
                               f"coordinating via message."
                }

        # ロック取得成功 - 処理続行
        return {"block": False}

    return {"block": False}
```

### タスク割り当てアルゴリズム

```typescript
// mcp-server/src/task-queue.ts
function assignTask(agentId: string): Task | null {
  // 1. エージェントの現在のタスクを確認
  const currentTasks = getAgentTasks(agentId);

  // 2. 実行可能なタスク（依存関係解決済み）を取得
  const readyTasks = tasks.filter(t =>
    t.status === 'pending' &&
    t.dependencies.every(d => isCompleted(d))
  );

  // 3. 優先度とエージェント適性でソート
  const sorted = readyTasks.sort((a, b) => {
    const scoreA = calculateScore(a, agentId);
    const scoreB = calculateScore(b, agentId);
    return scoreB - scoreA;
  });

  // 4. 最適なタスクを割り当て
  return sorted[0] || null;
}
```

### メッセージングプロトコル

```jsonl
// .claude/swarm/messages.jsonl (append-only)
{"id":"msg-1","from":"BackendTeam","to":"FrontendTeam","body":"Auth API完成。/api/auth エンドポイント使用可能","timestamp":"2025-11-08T10:30:00Z"}
{"id":"msg-2","from":"FrontendTeam","to":"BackendTeam","body":"確認。ログインフォーム実装開始","timestamp":"2025-11-08T10:35:00Z"}
```

MCPツールでアクセス:

```typescript
// エージェントから呼び出し
const messages = await mcp.call("swarm_get_messages", {
  recipient: "FrontendTeam",
  unread_only: true
});
```

## ベンチマークと評価

### 比較: 既存アプローチとの違い

| 特性 | mcp_agent_mail | beads | claude-hooks-obs | **Swarm Coordinator** |
|------|----------------|-------|------------------|----------------------|
| **複雑さ** | 高（フルメールシステム） | 中（CLIツール） | 低（監視のみ） | **低（最小限）** |
| **侵襲性** | 中（専用ディレクトリ） | 低（.beads/） | 無（外部監視） | **最小（.claude/）** |
| **学習曲線** | 急（新概念多数） | 中（Git理解必要） | 緩（インストールのみ） | **緩（透過的）** |
| **エージェント通信** | ✓ 豊富 | △ 間接的 | ✗ 無 | **✓ シンプル** |
| **ファイル競合** | ✓ 予約システム | △ Gitマージ | ✗ 無 | **✓ 自動ロック** |
| **可観測性** | △ WebUI | △ CLI | ✓ 豊富 | **✓ オプション** |
| **Claude統合** | MCP | MCP | Hooks | **Hooks + MCP** |

### パフォーマンス特性

- **オーバーヘッド**: フックごとに ~10-20ms（ロック確認）
- **同期コスト**: Gitコミット不要（JSONLはappend-only）
- **スケーラビリティ**: 5-10エージェントまで検証済み
- **ストレージ**: 1日あたり ~1-5MB（メッセージ・ロック履歴）

## ロードマップ

### Phase 1: MVP（現在）
- ✓ 基本的なファイルロック機構
- ✓ シンプルなタスクキュー
- ✓ Gitベース永続化

### Phase 2: 強化
- [ ] WebSocket通知（リアルタイムロック更新）
- [ ] インテリジェントタスク割り当て（AI分析）
- [ ] 自動競合解決提案

### Phase 3: エコシステム
- [ ] Claude Codeプラグインマーケットプレイス公開
- [ ] 他のエージェントフレームワークとの統合
- [ ] パフォーマンスメトリクス収集

## 貢献とフィードバック

このプロジェクトは実験的な研究です。以下の点についてフィードバック歓迎：

- 実際のマルチエージェント開発での使用感
- パフォーマンスボトルネックの特定
- 新しいユースケースの提案
- 既存ツールとの統合アイデア

## ライセンス

MIT License

## 謝辞

このプロジェクトは以下の優れた研究から多大な影響を受けています：

- **mcp_agent_mail** - メール型調整とファイル予約の概念
- **beads** - Gitベース分散メモリの設計哲学
- **claude-code-hooks-multi-agent-observability** - フックベース監視の実装

---

**Note**: このシステムは研究プロトタイプです。本番環境での使用前に十分なテストを行ってください。
