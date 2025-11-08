# Claude Code Prompt Improver - 分析レポート

## 概要

**プロジェクト**: [claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver)
**作者**: severity1
**ライセンス**: MIT
**バージョン**: 0.3.2 (2025-11-05時点)

Claude Code Prompt Improverは、曖昧なユーザープロンプトを自動的に改善するためのUserPromptSubmitフックです。プロンプトの実行前に評価を行い、必要に応じてコンテキストに基づいた具体的な質問を提示することで、初回実行での成功率を向上させます。

## 主な機能

### 1. **プロンプト評価と自動改善**
- ユーザーが入力したプロンプトを実行前に評価
- 曖昧な場合は、コードベースやウェブリサーチに基づいた1-6個の具体的な質問を提示
- 会話履歴を活用して冗長な探索を回避
- 明確なプロンプトはそのまま通過（ほとんどの場合は介入しない）

### 2. **バイパス機能**
プロンプトの先頭に特定の記号を付けることで、評価をスキップできます：

| プレフィックス | 機能 | 例 |
|---|---|---|
| `*` | 評価をスキップ | `* add dark mode` |
| `/` | スラッシュコマンド | `/help` |
| `#` | メモ化（バイパス） | `# remember to use rg over grep` |

### 3. **2段階アプローチ**

#### **Phase 1 - Research（リサーチ）**
1. 簡潔な説明を提示（なぜ明確化が必要か）
2. TodoWriteでリサーチ計画を作成
3. 適切なツールを使用してリサーチを実行
   - Task/Explore: コードベース探索
   - WebSearch: オンラインリサーチ
   - Read/Grep: 必要に応じて
4. リサーチ結果（訓練データではなく）に基づいて具体的な質問を作成
5. 完了をマーク

#### **Phase 2 - Ask（質問）**
1. AskUserQuestionツールで1-6個の質問を提示
2. 回答を使用して元のリクエストを実行

## アーキテクチャ

### フックの仕組み

```
ユーザー入力 → improve-prompt.py → 評価ラッパー → Claude Code → 評価 → リサーチ → 質問 → 実行
```

#### **improve-prompt.py の役割**
1. stdinからJSON形式でプロンプトを受け取る
2. バイパス条件をチェック（`*`, `/`, `#`）
3. 評価指示でプロンプトをラップ（約300トークン）
4. JSON形式でstdoutに出力

#### **メインセッションでの評価**
サブエージェントではなく、メインセッションで評価を行う理由：
- 会話履歴にアクセス可能
- 冗長な探索を回避
- より透明性が高い
- 全体的に効率的

### コード構造

```
claude-code-prompt-improver/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ
├── .dev-marketplace/
│   └── .claude-plugin/
│       └── marketplace.json      # 開発用マーケットプレイス設定
├── assets/
│   └── demo.gif                 # デモ動画
├── hooks/
│   └── hooks.json               # フック設定
├── scripts/
│   └── improve-prompt.py        # メインスクリプト（83行）
├── CHANGELOG.md                 # 変更履歴
├── LICENSE                      # MITライセンス
└── README.md                    # ドキュメント
```

## 実装の詳細

### improve-prompt.py の解析

**入力フォーマット**:
```json
{
  "prompt": "fix the bug"
}
```

**出力フォーマット**:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "PROMPT EVALUATION\n\nOriginal user request: \"fix the bug\"\n..."
  }
}
```

**主要なロジック**:
1. JSON入力の読み込みとバリデーション
2. バイパス条件のチェック
3. エスケープ処理（引用符とバックスラッシュ）
4. 評価ラッパーの構築
5. JSON出力

### hooks.json の設定

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Improves user prompts by adding clarifying questions",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/improve-prompt.py",
            "description": "Run the prompt improvement script"
          }
        ]
      }
    ]
  }
}
```

## インストール方法

### オプション1: マーケットプレイス経由（推奨）

```bash
# マーケットプレイスを追加
claude plugin marketplace add severity1/claude-code-marketplace

# プラグインをインストール
claude plugin install prompt-improver@claude-code-marketplace

# Claude Codeを再起動し、/pluginコマンドで確認
```

### オプション2: ローカルインストール（開発向け）

```bash
# リポジトリをクローン
git clone https://github.com/severity1/claude-code-prompt-improver.git
cd claude-code-prompt-improver

# ローカルマーケットプレイスを追加
claude plugin marketplace add /absolute/path/to/claude-code-prompt-improver/.dev-marketplace/.claude-plugin/marketplace.json

# プラグインをインストール
claude plugin install prompt-improver@local-dev

# Claude Codeを再起動
```

### オプション3: 手動インストール

```bash
# スクリプトをコピー
cp scripts/improve-prompt.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/improve-prompt.py

# ~/.claude/settings.jsonを編集
# （hooks設定を追加）
```

## テスト結果

### テスト1: 通常のプロンプト

**入力**:
```bash
echo '{"prompt": "fix the bug"}' | python3 scripts/improve-prompt.py
```

**出力**:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "PROMPT EVALUATION\n\nOriginal user request: \"fix the bug\"\n..."
  }
}
```

✅ **結果**: 評価ラッパーが正常に追加されました

### テスト2: バイパス機能

**入力**:
```bash
echo '{"prompt": "* add dark mode"}' | python3 scripts/improve-prompt.py
```

**出力**:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "add dark mode"
  }
}
```

✅ **結果**: `*`プレフィックスが削除され、プロンプトがそのまま通過しました

## パフォーマンス分析

### トークンオーバーヘッド

- **ラップされたプロンプトあたり**: 約300トークン
- **30メッセージセッション**: 約9,000トークン（200kコンテキストの約4.5%）
- **トレードオフ**: わずかなオーバーヘッドで、初回実行の成功率が向上

### 効率性の考慮事項

**利点**:
- 会話履歴を活用して冗長な探索を回避
- 本当に曖昧な場合のみ介入
- 最大1-6個の質問に制限（焦点を絞る）

**考慮点**:
- 各プロンプトに300トークンのオーバーヘッド
- リサーチフェーズで追加のツール呼び出しが必要
- 質問応答による若干の遅延

## 設計哲学

1. **最小限の介入**: ほとんどのプロンプトは変更されずに通過
2. **ユーザー意図を信頼**: 本当に不明確な場合のみ質問
3. **会話履歴の活用**: 冗長な探索を回避
4. **焦点を絞った質問**: 最大1-6個（複雑なシナリオに十分、かつ焦点を維持）
5. **透明性**: 評価は会話に表示される

## 変更履歴のハイライト

### v0.3.2 (2025-11-05)
- プラグインフック登録の修正
- JSON出力フォーマットへの切り替え
- マーケットプレイスインストールのサポート

### v0.3.0 (2025-10-20)
- 動的リサーチプランニング（TodoWrite経由）
- 構造化されたリサーチと質問フェーズ
- 1-6個の質問をサポート（1-2個から増加）
- リサーチ結果に基づく質問の明示的な要件

### v0.1.0 (2025-10-18)
- メインセッション評価アプローチ（サブエージェント不使用）
- バイパスプレフィックス（`*`, `/`, `#`）
- AskUserQuestionツールの統合

## 評価

### 強み

1. **シンプルで効果的**: 83行のPythonスクリプトで実装
2. **柔軟性**: 3つのバイパスオプション
3. **コンテキスト認識**: 会話履歴を活用
4. **透明性**: 評価プロセスが見える
5. **低オーバーヘッド**: 約4.5%のトークン使用
6. **段階的アプローチ**: リサーチ → 質問 → 実行

### 改善の余地

1. **カスタマイズ性**: 評価基準の調整機能が限定的
2. **言語サポート**: 英語ベースの指示（多言語対応は未確認）
3. **学習機能**: ユーザーのパターンを学習しない
4. **設定オプション**: 質問数の上限などを設定できない

### 使用例

**良い使用ケース**:
- 曖昧なバグ修正リクエスト（「fix the error」など）
- 不明確な機能追加（「add tests」など）
- コンテキストが必要なタスク

**不要な使用ケース**:
- 詳細で具体的なプロンプト
- スラッシュコマンド
- 会話履歴から意図が明確な場合

## 結論

Claude Code Prompt Improverは、シンプルながら強力なツールです。わずか83行のPythonコードで、Claude Codeのユーザーエクスペリエンスを大幅に向上させます。

**主な発見**:

1. **アーキテクチャの選択**: メインセッションでの評価は、サブエージェントよりも効率的
2. **段階的アプローチ**: リサーチフェーズと質問フェーズの分離が効果的
3. **バイパス機能**: ユーザーに制御を与える柔軟性
4. **低コスト**: 4.5%のトークンオーバーヘッドで大きな価値

**推奨事項**:

- Claude Codeユーザーにとって試す価値がある
- 特に、曖昧なプロンプトを頻繁に使用するユーザーに有益
- 開発者は、自分のワークフローに合わせてカスタマイズ可能
- プラグインシステムの良い例として参考になる

## 参考リンク

- GitHub: https://github.com/severity1/claude-code-prompt-improver
- マーケットプレイス: severity1/claude-code-marketplace
- Claude Code要件: v2.0.22以上（AskUserQuestionツール対応）

## テスト環境

- Python: 3.x
- OS: Linux 4.4.0
- テスト日: 2025-11-08
- リポジトリコミット: 最新（v0.3.2）
