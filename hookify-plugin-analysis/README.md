# Hookify Plugin 分析レポート

## 概要

**Hookify**は、Claude Codeの公式プラグインで、会話パターンの分析や明示的な指示から、望まない動作を防ぐためのカスタムフックを簡単に作成できるツールです。

- **リポジトリ**: https://github.com/anthropics/claude-code/tree/main/plugins/hookify
- **作者**: Daisy Hollman (Anthropic)
- **バージョン**: 0.1.0

## ディレクトリ構造

```
hookify/
├── .claude-plugin/
│   └── plugin.json          # プラグインメタデータ
├── agents/
│   └── conversation-analyzer.md  # 会話分析用サブエージェント定義
├── commands/
│   ├── hookify.md            # /hookify メインコマンド
│   ├── configure.md          # /hookify:configure
│   ├── list.md               # /hookify:list
│   └── help.md               # /hookify:help
├── core/
│   ├── config_loader.py      # ルールファイルの読み込み・パース
│   └── rule_engine.py        # ルール評価エンジン
├── examples/
│   ├── dangerous-rm.local.md # rm -rf ブロック例
│   ├── console-log-warning.local.md # console.log 警告例
│   ├── sensitive-files-warning.local.md # 機密ファイル警告例
│   └── require-tests-stop.local.md # テスト必須停止例
├── hooks/
│   ├── hooks.json            # Claude Code hookイベント登録
│   ├── pretooluse.py         # ツール実行前フック
│   ├── posttooluse.py        # ツール実行後フック
│   ├── stop.py               # 停止時フック
│   └── userpromptsubmit.py   # プロンプト送信時フック
├── matchers/
│   └── __init__.py
├── skills/
│   └── writing-rules/
│       └── SKILL.md          # ルール記述スキル定義
├── utils/
│   └── __init__.py
└── README.md
```

## 主要機能

### 1. 簡単なルール作成

`.claude/hookify.{name}.local.md` というMarkdownファイルでルールを定義:

```markdown
---
name: block-dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf
action: block
---

⚠️ **Dangerous rm command detected!**
This command could delete important files.
```

### 2. 対応イベントタイプ

| イベント | 説明 | トリガー対象 |
|----------|------|--------------|
| `bash` | Bashコマンド実行 | Bashツール |
| `file` | ファイル編集 | Edit, Write, MultiEdit |
| `stop` | セッション終了時 | 完了チェック用 |
| `prompt` | ユーザー入力時 | プロンプト送信 |
| `all` | 全イベント | 上記すべて |

### 3. アクションタイプ

- **`warn`**: 警告メッセージを表示するが、操作は許可（デフォルト）
- **`block`**: 操作を完全にブロック

### 4. 条件マッチング

**シンプル形式（単一パターン）:**
```yaml
event: bash
pattern: rm\s+-rf
```

**高度な形式（複数条件、AND結合）:**
```yaml
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.env$
  - field: new_text
    operator: contains
    pattern: API_KEY
```

### 5. オペレータ一覧

| オペレータ | 説明 |
|------------|------|
| `regex_match` | 正規表現マッチ（最も一般的） |
| `contains` | 部分文字列を含む |
| `equals` | 完全一致 |
| `not_contains` | 部分文字列を含まない |
| `starts_with` | 指定文字列で始まる |
| `ends_with` | 指定文字列で終わる |

### 6. フィールド参照

**bash イベント:**
- `command`: 実行されるコマンド

**file イベント:**
- `file_path`: ファイルパス
- `new_text` / `new_string`: 新しいテキスト
- `old_text` / `old_string`: 古いテキスト
- `content`: ファイル全体

**prompt イベント:**
- `user_prompt`: ユーザーの入力テキスト

**stop イベント:**
- `transcript`: セッション全体のトランスクリプト
- `reason`: 停止理由

## コマンド

### `/hookify [説明]`

引数付きで実行すると、その指示に基づいてルールを作成:
```
/hookify Don't use console.log in TypeScript files
```

引数なしで実行すると、会話を分析して問題のある動作を検出:
```
/hookify
```

### `/hookify:list`

現在のすべてのルールを一覧表示

### `/hookify:configure`

インタラクティブにルールの有効/無効を切り替え

### `/hookify:help`

ヘルプを表示

## アーキテクチャ

### フック実行フロー

```
Claude Code イベント発生
       ↓
hooks.json でイベントハンドラを検索
       ↓
Python スクリプト実行（pretooluse.py など）
       ↓
config_loader.py でルールを読み込み
       ↓
rule_engine.py でルール評価
       ↓
JSON レスポンス返却
       ↓
Claude Code がメッセージ表示/操作ブロック
```

### コア実装

**config_loader.py:**
- `.claude/hookify.*.local.md` ファイルを glob で検出
- YAML frontmatter をパース（標準ライブラリのみ、外部依存なし）
- `Rule` と `Condition` データクラスに変換

**rule_engine.py:**
- 複数ルールを評価し、マッチするものを集約
- ブロックルールは警告ルールより優先
- 正規表現は `@lru_cache` でキャッシュ（最大128パターン）
- マッチしたすべてのルールのメッセージを結合して返却

### 会話分析エージェント

`conversation-analyzer` エージェントは以下を検出:
- 明示的な修正リクエスト（"Don't use X", "Stop doing Y"）
- フラストレーション反応（"Why did you do X?"）
- 修正や取り消し操作
- 繰り返される問題

## 実用例

### 危険なコマンドをブロック

```markdown
---
name: block-destructive-ops
enabled: true
event: bash
pattern: rm\s+-rf|dd\s+if=|mkfs|format
action: block
---

🛑 **Destructive operation detected!**
This command can cause data loss.
```

### デバッグコードを警告

```markdown
---
name: warn-debug-code
enabled: true
event: file
pattern: console\.log\(|debugger;|print\(
action: warn
---

🐛 **Debug code detected**
Remove debugging statements before committing.
```

### 機密ファイル編集を警告

```markdown
---
name: warn-sensitive-files
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.env$|\.env\.|credentials|secrets
---

🔐 **Sensitive file detected**
Ensure credentials are not hardcoded.
```

### テスト実行を必須化

```markdown
---
name: require-tests-run
enabled: false
event: stop
action: block
conditions:
  - field: transcript
    operator: not_contains
    pattern: npm test|pytest|cargo test
---

**Tests not detected!**
Please run tests before stopping.
```

## 技術的特徴

1. **ホットリロード**: ルールファイルは毎回動的に読み込まれるため、再起動不要
2. **外部依存ゼロ**: Python標準ライブラリのみ使用
3. **エラー耐性**: フックエラー時も操作を許可（exit 0）
4. **正規表現キャッシュ**: LRUキャッシュで高速化
5. **スキル統合**: ルール記述のスキル定義でClaude自身が学習可能

## 制限事項

- 条件は AND 結合のみ（OR は正規表現の `|` で代用）
- YAML パーサーはシンプル実装のため、複雑なネストに制限あり
- 現時点では JSON フォーマット未対応

## 今後の拡張予定（README記載）

- 重要度レベル（error/warning/info）
- ルールテンプレートライブラリ
- インタラクティブパターンビルダー
- フックテストユーティリティ
- JSON フォーマットサポート

## まとめ

Hookifyは、Claude Codeでの危険な操作や望まないパターンを防ぐための軽量で強力なガードレールシステムです。Markdownベースの設定ファイルにより、プログラミング知識がなくてもカスタムルールを作成できます。
