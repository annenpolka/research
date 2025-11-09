# cc-sessionsモード動作の詳細調査

## 概要

このプロジェクトは、[cc-sessions](https://github.com/GWUDCAP/cc-sessions)のDAIC（Discussion-Alignment-Implementation-Check）メソドロジーにおけるモード動作とその実現方法を調査した研究です。

## cc-sessionsとは

cc-sessionsは、Claude Codeのための構造化されたAIペアプログラミングワークフレームです。Claudeがコードを書く前に議論し、承認を得ることを強制する仕組みを提供します。

## モードの種類

cc-sessionsには2つの主要なモードがあります：

### 1. Discussion Mode（ディスカッションモード）
- **内部値**: `Mode.NO = "discussion"`
- **デフォルト状態**: システムはこのモードで起動
- **制限事項**: Edit、Write、MultiEdit、NotebookEditなどの書き込みツールがブロックされる
- **許可される操作**: 読み取り専用コマンド、調査、議論
- **目的**: Claudeにアプローチの議論、理由の説明、具体的なTodoリストの提案を強制

### 2. Implementation Mode（実装モード）
- **内部値**: `Mode.GO = "implementation"`
- **アクティベーション**: ユーザーがトリガーフレーズを使用した時のみ
- **許可される操作**: 承認されたTodoリストに基づくコード編集
- **制限事項**: 承認されたTodoリスト以外の作業は許可されない
- **自動復帰**: すべてのTodoが完了すると自動的にDiscussion Modeに戻る

## モードの実現方法

### アーキテクチャ

モード管理は主に以下の4つのフックファイルで実装されています：

#### 1. `shared_state.py` - 状態管理の中核

**主要コンポーネント**:

```python
# モード定義（137-139行目）
class Mode(str, Enum):
    NO = "discussion"
    GO = "implementation"

# 状態ファイル（36行目）
STATE_FILE = PROJECT_ROOT / "sessions" / "sessions-state.json"

# 状態編集のためのロック機構（882-888行目）
@contextmanager
def edit_state() -> Iterator[SessionsState]:
    with _lock(LOCK_DIR):
        state = load_state()
        try: yield state
        except Exception: raise
        else: _the_ol_in_out(STATE_FILE, state.to_dict())
```

**特徴**:
- 統一されたJSONベースの状態管理（`sessions-state.json`）
- ファイルロックによるアトミックな更新
- `Mode` enumによる型安全なモード管理
- 設定可能なトリガーフレーズシステム

#### 2. `sessions_enforce.py` - PreToolUse Hook（DAIC実施）

**主要機能**:

```python
# Discussion modeでの書き込みツールのブロック（308-314行目）
if STATE.mode is Mode.NO and not STATE.flags.bypass_mode:
    if CONFIG.blocked_actions.is_tool_blocked(tool_name):
        print(f"[DAIC: Tool Blocked] You're in discussion mode. "
              f"The {tool_name} tool is not allowed. You need to seek alignment first.",
              file=sys.stderr)
        sys.exit(2)  # Block with feedback
```

**Bashコマンドの読み取り専用チェック**（204-263行目）:
- 70以上の読み取り専用コマンドのホワイトリスト（`READONLY_FIRST`）
- リダイレクション検出（`>`、`>>`、`2>&1`など）
- `sed -i`、`awk`のファイル出力、`find -delete`などの書き込み操作の検出
- パイプラインの各セグメントを個別に解析
- カスタマイズ可能なパターン（ユーザーが独自のコマンドを追加可能）

**Todo変更の検出とブロック**（316-376行目）:
- アクティブなTodoリストと新しい提案を比較
- 変更が検出された場合、詳細なdiffを表示
- "SHAME RITUAL"形式での応答を要求
- Todoをクリアし、Discussion Modeに戻す

**CI環境の検出**（115-125行目）:
- GitHub Actionsなどでは自動的にDAICをバイパス

#### 3. `user_messages.py` - UserPromptSubmit Hook（モード遷移）

**トリガーフレーズの検出**（66-78行目）:

```python
def phrase_matches(phrase, text):
    """大文字のフレーズは大文字小文字を区別、それ以外は区別しない"""
    if phrase.isupper():
        return phrase in text
    else:
        return phrase.lower() in text.lower()

implementation_phrase_detected = any(
    phrase_matches(phrase, prompt)
    for phrase in CONFIG.trigger_phrases.implementation_mode
)
```

**デフォルトのトリガーフレーズ**（`shared_state.py` 157-163行目）:
- Implementation Mode: `["yert"]`
- Discussion Mode: `["SILENCE"]`（緊急停止用）
- Task Creation: `["mek:"]`
- Task Startup: `["start^"]`
- Task Completion: `["finito"]`
- Context Compaction: `["squish"]`

**Implementation Modeへの遷移**（180-191行目）:

```python
if not is_api_command and STATE.mode is Mode.NO and implementation_phrase_detected:
    with edit_state() as s:
        s.mode = Mode.GO
        STATE = s
    context += """[DAIC: Implementation Mode Activated]
CRITICAL RULES:
- Convert your proposed todos to TodoWrite EXACTLY as written
- Do NOT add new todos - only implement approved items
- Do NOT remove todos - complete them or return to discussion
- Check off each todo as you complete it
- When all todos are complete, you'll auto-return to discussion
"""
```

**緊急停止**（194-206行目）:
- Discussion Modeトリガーは任意のモードで機能
- すべてのアクティブなTodoをクリア
- 即座にDiscussion Modeに戻る

**プロトコルシステム**:
- Task Creation、Startup、Completion、Context Compactionの各プロトコル
- 各プロトコルは特定のTodoリストとガイダンスを自動ロード
- テンプレート変数でユーザー設定に基づいて動的に適応

#### 4. `post_tool_use.py` - PostToolUse Hook（自動復帰）

**Todo完了の検出と自動モード復帰**（98-147行目）:

```python
if STATE.mode is Mode.GO and tool_name == "TodoWrite" and STATE.todos.all_complete():
    print("[DAIC: Todos Complete] All todos completed.\n\n", file=sys.stderr)

    # プロトコル完了時の処理
    if STATE.active_protocol is SessionsProtocol.COMPLETE:
        with edit_state() as s:
            s.mode = Mode.NO
            s.active_protocol = None
            s.current_task.clear_task()
            s.todos.active = []
            STATE = s

    # スタッシュされたTodoの復元または Discussion Modeへ復帰
    if STATE.todos.stashed:
        # 以前のTodoを復元
        with edit_state() as s:
            num_restored = s.todos.restore_stashed()
            s.api.todos_clear = True
            STATE = s
    else:
        # Discussion Modeに戻る
        with edit_state() as s:
            s.todos.active = []
            s.mode = Mode.NO
            STATE = s
```

**その他の機能**:
- `cd`コマンド後のディレクトリ位置リマインダー（77-83行目）
- サブエージェント完了後のクリーンアップ（85-96行目）
- タスクファイル編集の自動検出と状態更新（163-203行目）

### 状態の永続化

モード状態は `sessions/sessions-state.json` に保存されます：

```json
{
  "mode": "discussion",  // または "implementation"
  "current_task": { ... },
  "todos": {
    "active": [...],
    "stashed": [...]
  },
  "active_protocol": null,
  "flags": { ... },
  "metadata": { ... },
  "api": { ... }
}
```

### 設定のカスタマイズ

ユーザーは `sessions/sessions-config.json` で動作をカスタマイズできます：

```json
{
  "trigger_phrases": {
    "implementation_mode": ["yert", "make it so", "run that"],
    "discussion_mode": ["SILENCE"],
    "task_creation": ["mek:"],
    ...
  },
  "blocked_actions": {
    "implementation_only_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
    "bash_read_patterns": [],
    "bash_write_patterns": [],
    "extrasafe": true
  },
  "features": {
    "branch_enforcement": true,
    "auto_ultrathink": true,
    "context_warnings": {
      "warn_85": true,
      "warn_90": true
    }
  },
  ...
}
```

## モード遷移のフロー図

```
起動
  ↓
┌─────────────────────────────────┐
│   Discussion Mode (Mode.NO)     │
│   - 書き込みツールがブロック    │
│   - 読み取り・調査が許可        │
│   - Todoリストの提案            │
└─────────────────────────────────┘
         ↓ トリガーフレーズ検出
         ↓ (user_messages.py)
┌─────────────────────────────────┐
│ Implementation Mode (Mode.GO)   │
│   - TodoWriteで承認済みTodoを   │
│     正確に記録                  │
│   - 承認されたTodoのみ実行      │
│   - Todo変更はブロック          │
└─────────────────────────────────┘
         ↓ すべてのTodo完了
         ↓ (post_tool_use.py)
         ↓ またはSILENCE (緊急停止)
         ↓
┌─────────────────────────────────┐
│   Discussion Modeに自動復帰     │
└─────────────────────────────────┘
```

## 主要な設計パターン

### 1. Hook-based Architecture
- **PreToolUse Hook** (`sessions_enforce.py`): ツール実行前に検証
- **UserPromptSubmit Hook** (`user_messages.py`): ユーザー入力でモード切り替え
- **PostToolUse Hook** (`post_tool_use.py`): ツール実行後に状態更新

### 2. State Management
- ファイルベースのJSON状態（`sessions-state.json`）
- ファイルロックによるアトミック操作
- コンテキストマネージャーパターン（`edit_state()`）
- 1秒タイムアウトの強制削除によるデッドロック防止

### 3. Todo-based Boundaries
- 承認されたTodoリストが実行境界を定義
- Todo変更の検出とdiff表示
- "SHAME RITUAL"形式での違反報告
- Todoクリアで再承認を強制

### 4. Configuration-driven Behavior
- すべての動作が `sessions-config.json` でカスタマイズ可能
- トリガーフレーズ、ブロックツール、Git設定など
- テンプレート変数によるプロトコルの動的適応

### 5. Natural Language Protocols
- トリガーフレーズによる完全なワークフロー自動化
- `mek:`（作成）、`start^:`（開始）、`finito`（完了）、`squish`（圧縮）
- 各プロトコルは特定のTodoとガイダンスを自動ロード
- ユーザー設定に基づいて適応

## セキュリティと安全性の特徴

### 1. 多層防御
- PreToolUseでツール実行をブロック
- UserPromptSubmitで明示的な承認を要求
- PostToolUseで境界外の動作を検出

### 2. コマンド解析の詳細
- シェルコマンドのパイプライン分割
- リダイレクション検出（`>`、`>>`、`2>&1`など）
- インプレース編集の検出（`sed -i`）
- `find -delete`、`xargs rm`などの危険な組み合わせ

### 3. Todo変更のブロック
- アクティブなTodoと新しい提案の厳密な比較
- 変更が検出された場合の詳細なdiff表示
- 状態のクリアと再承認の強制

### 4. CI環境の自動バイパス
- GitHub Actionsでの自動テストを妨げない
- `GITHUB_ACTIONS`、`CI`などの環境変数を検出

## 興味深い実装の詳細

### 1. 大文字小文字の区別によるトリガー制御
```python
def phrase_matches(phrase, text):
    """大文字のフレーズは大文字小文字を区別"""
    if phrase.isupper():
        return phrase in text
    else:
        return phrase.lower() in text.lower()
```

この設計により、緊急停止用のトリガー（`SILENCE`）は誤発火を防ぐために大文字小文字を厳密に区別します。

### 2. スタッシュ/復元メカニズム
プロトコル（Task Creation、Context Compactionなど）の実行中、現在のTodoを一時的にスタッシュし、プロトコル完了後に復元できます。これにより、作業の中断と再開がシームレスに行えます。

### 3. ウィンドウ化されたAPIパーミッション
特定のコマンド（`sessions todos clear`）は、特定のコンテキストでのみ有効化され、他のツール使用後に自動的に無効化されます。これにより、誤操作を防ぎます。

### 4. ディレクトリタスクのサポート
複数のサブタスクを持つ大規模プロジェクトをサポート。サブタスクは親タスクのブランチに留まり、すべて完了するまでマージされません。

### 5. コンテキスト使用量の監視
トランスクリプトファイルを解析してトークン使用量を追跡：
- 85%で警告
- 90%で緊急警告
- モデル別の実用的な上限（Opus: 160k、Sonnet: 800k）

## ファイル構造

```
cc-sessions/
├── cc_sessions/
│   ├── python/
│   │   └── hooks/
│   │       ├── shared_state.py         # 状態管理、Mode enum、設定
│   │       ├── sessions_enforce.py     # PreToolUse: DAIC実施
│   │       ├── user_messages.py        # UserPromptSubmit: モード遷移
│   │       ├── post_tool_use.py        # PostToolUse: 自動復帰
│   │       ├── session_start.py        # セッション初期化
│   │       ├── subagent_hooks.py       # サブエージェント保護
│   │       └── kickstart_session_start.py  # オンボーディング
│   │   ├── api/                        # Sessions API実装
│   │   │   ├── router.py
│   │   │   ├── state_commands.py
│   │   │   ├── config_commands.py
│   │   │   └── ...
│   │   └── statusline.py               # ステータスライン統合
│   ├── javascript/                     # Node.js実装（完全な機能パリティ）
│   ├── protocols/                      # ワークフロープロトコル
│   │   ├── task-creation/
│   │   ├── task-startup/
│   │   ├── task-completion/
│   │   └── context-compaction/
│   └── agents/                         # 専用エージェント
├── sessions/
│   ├── sessions-state.json             # ランタイム状態（git無視）
│   ├── sessions-config.json            # ユーザー設定
│   └── tasks/                          # タスクファイル
└── README.md
```

## 結論

cc-sessionsのモードシステムは、以下を実現する洗練された実装です：

1. **強制的なアライメント**: Claudeは常に実装前に議論し承認を得る必要がある
2. **明確な境界**: 承認されたTodoリストが正確に何を実装できるかを定義
3. **自動化された規律**: モード遷移とプロトコルローディングが自動化
4. **安全性**: 多層防御と詳細なコマンド解析
5. **柔軟性**: すべての動作がカスタマイズ可能
6. **透明性**: すべての状態変更が明示的に通知される

このシステムは、AIペアプログラミングにおける「サプライズ」や「スコープクリープ」の問題を解決し、構造化され予測可能な開発ワークフローを提供します。

## 学び

この調査から得られた主な学び：

1. **Hookベースのアーキテクチャの力**: PreToolUse、UserPromptSubmit、PostToolUseフックを組み合わせることで、完全なワークフロー制御が可能
2. **状態管理の重要性**: ファイルベースのJSON状態とロック機構により、複雑な状態遷移を確実に管理
3. **自然言語インターフェース**: トリガーフレーズによる直感的なモード切り替えとプロトコルアクティベーション
4. **Todo駆動の境界**: 承認されたTodoリストが実装スコープを明確に定義
5. **設定駆動の柔軟性**: すべての動作がカスタマイズ可能で、ユーザーのワークフローに適応

## 参考資料

- [cc-sessions GitHub Repository](https://github.com/GWUDCAP/cc-sessions)
- [クローンされたリポジトリ](./cc-sessions/)
- 主要ファイル:
  - [shared_state.py](./cc-sessions/cc_sessions/python/hooks/shared_state.py)
  - [sessions_enforce.py](./cc-sessions/cc_sessions/python/hooks/sessions_enforce.py)
  - [user_messages.py](./cc-sessions/cc_sessions/python/hooks/user_messages.py)
  - [post_tool_use.py](./cc-sessions/cc_sessions/python/hooks/post_tool_use.py)
