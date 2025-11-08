# コード詳細分析

## improve-prompt.py の完全解析

### スクリプト構造

```python
#!/usr/bin/env python3
"""
Claude Code Prompt Improver Hook
Intercepts user prompts and evaluates if they need enrichment before execution.
Uses main session context for intelligent, non-pedantic evaluation.
"""
```

#### 1. 入力処理（L10-17）

```python
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

prompt = input_data.get("prompt", "")
```

**機能**:
- stdinからJSON形式の入力を読み込み
- エラーハンドリング付き
- promptフィールドを抽出

#### 2. エスケープ処理（L19-20）

```python
escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
```

**機能**:
- バックスラッシュと引用符をエスケープ
- ラッパー内に安全に埋め込むため
- SQLインジェクションのような問題を防ぐ

#### 3. 出力関数（L22-30）

```python
def output_json(text):
    """Output text in UserPromptSubmit JSON format"""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text
        }
    }
    print(json.dumps(output))
```

**機能**:
- Claude Code公式仕様に準拠したJSON出力
- hookSpecificOutput構造を使用
- additionalContextフィールドにテキストを設定

#### 4. バイパスロジック（L32-50）

```python
# Check for bypass conditions
if prompt.startswith("*"):
    clean_prompt = prompt[1:].strip()
    output_json(clean_prompt)
    sys.exit(0)

if prompt.startswith("/"):
    output_json(prompt)
    sys.exit(0)

if prompt.startswith("#"):
    output_json(prompt)
    sys.exit(0)
```

**機能**:
- `*`: 評価をスキップ、プレフィックスを削除
- `/`: スラッシュコマンド、そのまま通過
- `#`: メモ化、そのまま通過

#### 5. 評価ラッパー（L52-79）

```python
wrapped_prompt = f"""PROMPT EVALUATION

Original user request: "{escaped_prompt}"

EVALUATE: Is this prompt clear enough to execute, or does it need enrichment?

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have sufficient context OR can infer intent

ONLY ASK if genuinely vague (e.g., "fix the bug" with no context):
- CRITICAL (NON-NEGOTIABLE) RULES:
  - Trust user intent by default. Check conversation history before doing research.
  - Do not rely on base knowledge.
  - Never skip Phase 1. Research before asking.
  - Don't announce evaluation - just proceed or ask.

- PHASE 1 - RESEARCH (DO NOT SKIP):
  1. Preface with brief note: "Prompt Improver Hook is seeking clarification because [specific reason: ambiguous scope/missing context/unclear requirements/etc]"
  2. Create research plan with TodoWrite: Ask yourself "What do I need to research to clarify this vague request?" Research WHAT NEEDS CLARIFICATION, not just the project. Use available tools: Task/Explore for codebase, WebSearch for online research (current info, common approaches, best practices, typical architectures), Read/Grep as needed
  3. Execute research
  4. Use research findings (not your training) to formulate grounded questions with specific options
  5. Mark completed

- PHASE 2 - ASK (ONLY AFTER PHASE 1):
  1. Use AskUserQuestion tool with max 1-6 questions offering specific options from your research
  2. Use the answers to execute the original user request
"""
```

**構造**:
1. **元のリクエスト**: ユーザーの入力を保持
2. **評価基準**: いつ進めるか、いつ質問するか
3. **クリティカルルール**: 評価の原則
4. **Phase 1**: リサーチフェーズの詳細手順
5. **Phase 2**: 質問フェーズの詳細手順

#### 6. 最終出力（L81-82）

```python
output_json(wrapped_prompt)
sys.exit(0)
```

## 評価ラッパーの詳細分析

### PROCEED IMMEDIATELY条件

```
- Detailed/specific OR you have sufficient context OR can infer intent
```

**意味**:
- 詳細で具体的なプロンプト
- 会話履歴から十分なコンテキストがある
- 意図を推測できる

### ONLY ASK条件

```
if genuinely vague (e.g., "fix the bug" with no context)
```

**例**:
- ✅ 質問必要: "fix the bug"（どのバグ？）
- ✅ 質問必要: "add tests"（どこに？何を？）
- ❌ 質問不要: "Fix TypeError in Map.tsx line 127"（具体的）
- ❌ 質問不要: （会話履歴でバグが特定されている場合）

### CRITICAL RULES

#### 1. Trust user intent by default

```
Check conversation history before doing research
```

**目的**: 冗長な探索を避ける

#### 2. Do not rely on base knowledge

```
Use research findings (not your training) to formulate grounded questions
```

**目的**: プロジェクト固有の質問を作成

#### 3. Never skip Phase 1

```
Research before asking
```

**目的**: 質問が具体的で有用であることを保証

#### 4. Don't announce evaluation

```
just proceed or ask
```

**目的**: ユーザーエクスペリエンスをスムーズに

## Phase 1 - Research の詳細

### ステップ1: Preface

```
"Prompt Improver Hook is seeking clarification because [specific reason: ambiguous scope/missing context/unclear requirements/etc]"
```

**目的**: ユーザーに何が起こっているかを伝える

### ステップ2: Research Plan

```
Create research plan with TodoWrite: Ask yourself "What do I need to research to clarify this vague request?"
```

**ツール**:
- Task/Explore: コードベース探索
- WebSearch: オンラインリサーチ
- Read/Grep: 必要に応じて

### ステップ3: Execute Research

```
Execute research
```

**目的**: 実際の情報を収集

### ステップ4: Formulate Questions

```
Use research findings (not your training) to formulate grounded questions with specific options
```

**重要**: 訓練データではなく、リサーチ結果を使用

### ステップ5: Mark Completed

```
Mark completed
```

**目的**: TodoWriteで進捗を追跡

## Phase 2 - Ask の詳細

### ステップ1: AskUserQuestion

```
Use AskUserQuestion tool with max 1-6 questions offering specific options from your research
```

**特徴**:
- 最大1-6個の質問
- リサーチから得た具体的なオプション
- AskUserQuestionツールを使用

### ステップ2: Execute Original Request

```
Use the answers to execute the original user request
```

**目的**: 回答を使って元のリクエストを実行

## トークン分析

### ラッパーサイズ

```bash
# 評価ラッパーのトークン数を推定
wc -w <<< "PROMPT EVALUATION..."
```

**推定**: 約250-300トークン

### セッション全体のオーバーヘッド

- **10メッセージ**: 約3,000トークン（1.5%）
- **30メッセージ**: 約9,000トークン（4.5%）
- **100メッセージ**: 約30,000トークン（15%）

**結論**: 短いセッションでは非常に効率的、長いセッションでも許容範囲

## エラーハンドリング

### JSON解析エラー

```python
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)
```

**動作**:
- stderrにエラーメッセージ
- 終了コード1で終了

### プロンプトが空の場合

```python
prompt = input_data.get("prompt", "")
```

**動作**:
- デフォルトで空文字列
- 評価ラッパーに空のプロンプトが含まれる

## セキュリティ考慮事項

### エスケープ処理

```python
escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
```

**保護対象**:
- 引用符によるインジェクション
- バックスラッシュによるエスケープシーケンス

### コマンドインジェクション

**分析**:
- ユーザー入力は直接実行されない
- JSON文字列として処理される
- ✅ 安全

## パフォーマンス分析

### 時間複雑度

1. **JSON読み込み**: O(n) - n = 入力サイズ
2. **エスケープ処理**: O(m) - m = プロンプト長
3. **バイパスチェック**: O(1)
4. **ラッパー構築**: O(1)
5. **JSON書き込み**: O(k) - k = 出力サイズ

**全体**: O(n + m + k) ≈ O(n)（線形時間）

### 空間複雂度

- **入力データ**: O(n)
- **エスケープ済みプロンプト**: O(m)
- **ラッパー**: O(1)（固定サイズ）
- **出力**: O(k)

**全体**: O(n + m + k)

### 実行時間

```bash
# ベンチマーク（簡易）
time echo '{"prompt": "fix the bug"}' | python3 improve-prompt.py
```

**予想**: < 100ms（ほぼ瞬時）

## 比較: 他のアプローチ

### サブエージェント vs. メインセッション

| アプローチ | メリット | デメリット |
|---|---|---|
| サブエージェント | 独立した実行環境 | 会話履歴なし、冗長 |
| メインセッション | 会話履歴あり、効率的 | 透明性が必要 |

**選択**: メインセッション ✅

### プリプロセス vs. ポストプロセス

| タイミング | メリット | デメリット |
|---|---|---|
| プリプロセス（UserPromptSubmit） | プロンプト改善 | 介入が見える |
| ポストプロセス（AfterToolCall） | エラー修正 | 後手に回る |

**選択**: プリプロセス ✅

## 拡張可能性

### カスタムバイパスプレフィックス

現在:
```python
if prompt.startswith("*"):
if prompt.startswith("/"):
if prompt.startswith("#"):
```

拡張案:
```python
BYPASS_PREFIXES = {"*", "/", "#", "!"}  # 設定ファイルから読み込み
if prompt[0] in BYPASS_PREFIXES:
```

### カスタム評価基準

現在: ハードコードされた評価ラッパー

拡張案:
```python
# .claude/prompt-improver-config.json から読み込み
config = load_config()
wrapped_prompt = config["evaluation_template"].format(
    escaped_prompt=escaped_prompt
)
```

### 質問数のカスタマイズ

現在: 最大1-6個（ハードコード）

拡張案:
```python
# 設定から読み込み
max_questions = config.get("max_questions", 6)
wrapped_prompt = f"...max {max_questions} questions..."
```

## まとめ

**コードの特徴**:
- シンプル: 83行
- 効率的: 線形時間複雑度
- 安全: 適切なエスケープ処理
- 柔軟: バイパス機能
- 拡張可能: カスタマイズの余地

**推奨事項**:
- そのまま使用可能
- カスタマイズは設定ファイル経由が望ましい
- エラーハンドリングは十分
- セキュリティ問題なし
