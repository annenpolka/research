# DSPy Exploration

## 概要

DSPy（Declarative Self-improving Language Programs）は、言語モデルのプロンプトをプログラム的に最適化するフレームワークです。このプロジェクトでは、DSPyの基本的な機能を探索し、いくつかの典型的なタスクで実験を行います。

## 動機

- DSPyがどのようにプロンプトエンジニアリングを自動化するかを理解する
- 従来の手動プロンプティングとの比較
- 異なるタスクでのDSPyの有効性を評価

## 実装した課題

### 基本機能（タスク1-4）
1. **テキスト分類** (`task1_classification.py`): 感情分析タスク
2. **質問応答** (`task2_qa.py`): コンテキストベースのQAシステム
3. **Chain-of-Thought推論** (`task3_cot.py`): 数学問題解決
4. **最適化機能** (`task4_optimization.py`): DSPyの自動最適化デモ

### Claude統合（タスク5-7）
5. **Claude統合** (`task5_claude_integration.py`): Anthropic Claude + DSPyの統合
6. **MCP統合** (`task6_mcp_integration.py`): Model Context Protocolとの連携
7. **実用パターン** (`task7_practical_patterns.py`): 5つの実用的な設計パターン

### デモ
- **基本デモ** (`demo_simple.py`): DSPyの基本構造の解説
- **Claude完全デモ** (`demo_claude_complete.py`): Claude Sonnet 4との統合デモ

## 環境

- Python 3.x
- DSPy (`dspy-ai`)
- LMプロバイダー（以下のいずれか）:
  - OpenAI API（オプション）
  - Anthropic API（推奨、Claude統合向け）

## 使い方

### 1. インストール

```bash
pip install dspy-ai
```

### 2. 基本デモの実行（API不要）

```bash
# DSPyの基本構造を理解するデモ
python demo_simple.py
```

### 3. タスクの実行（API必要）

実際のLMを使用する場合は、環境変数を設定してください：

#### OpenAIを使用する場合:
```bash
export OPENAI_API_KEY='your-api-key'

# 各タスクの実行
python task1_classification.py  # テキスト分類
python task2_qa.py              # 質問応答
python task3_cot.py             # Chain-of-Thought推論
python task4_optimization.py    # 最適化機能
```

#### Anthropic Claude を使用する場合（推奨）:
```bash
export ANTHROPIC_API_KEY='your-api-key'

# Claude統合のデモ
python task5_claude_integration.py  # Claude統合の基本
python demo_claude_complete.py      # 完全な実装例

# 基本タスクもClaudeで実行可能（コードを少し修正）
python task1_classification.py
python task2_qa.py
python task3_cot.py
```

#### MCPとの統合:
```bash
# MCP統合の概要を確認
python task6_mcp_integration.py

# 実用的なパターンを学ぶ
python task7_practical_patterns.py
```

## 結果

### 実装の概要

全てのタスクでDSPyの基本パターンを実装しました：

1. **Signature定義**: タスクの入力・出力を型安全に定義
2. **Module実装**: ロジックを再利用可能なモジュールとして実装
3. **Chain-of-Thought**: 推論ステップを自動的に追加
4. **最適化**: プロンプトの自動最適化機能のデモ

### DSPyの主要な利点

#### 1. プログラム的な定義
```python
class SentimentClassification(dspy.Signature):
    """テキストの感情を分類する"""
    text: str = dspy.InputField(desc="分類したいテキスト")
    sentiment: str = dspy.OutputField(desc="感情ラベル")
```
- 明確な型定義
- ドキュメントが組み込まれている
- 再利用可能

#### 2. モジュール性
```python
class SentimentClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.Predict(SentimentClassification)

    def forward(self, text: str):
        return self.classify(text=text)
```
- コンポーネントの再利用
- テストが容易
- 保守性が高い

#### 3. 自動最適化
```python
optimizer = dspy.BootstrapFewShot(metric=validate_answer)
optimized_model = optimizer.compile(model, trainset=trainset)
```
- プロンプトエンジニアリングの自動化
- データ駆動の改善
- Few-shot学習の最適化

### 各タスクの特徴

#### Task 1: テキスト分類
- **目的**: 感情分析（positive/negative/neutral）
- **手法**: `dspy.Predict` と `dspy.Signature`
- **学び**: DSPyの基本的な構造を理解

#### Task 2: 質問応答
- **目的**: コンテキストに基づいた質問応答
- **手法**: `dspy.ChainOfThought` で推論ステップを追加
- **学び**: 複数の推論パターンの比較

#### Task 3: Chain-of-Thought推論
- **目的**: 数学問題の段階的解決
- **手法**: マルチステップ推論、明示的なステップ定義
- **学び**: 複雑な推論プロセスの構造化

#### Task 4: 最適化機能
- **目的**: DSPyの自動最適化機能の理解
- **手法**: `BootstrapFewShot` などの最適化手法
- **学び**: プロンプト最適化の自動化

#### Task 5: Claude統合
- **目的**: Anthropic ClaudeとDSPyの統合方法
- **手法**: `dspy.LM('anthropic/claude-sonnet-4...')` による設定
- **学び**:
  - 複数のClaudeモデル（Sonnet 4, Opus, Haiku）の使い分け
  - 長いコンテキスト（200K+トークン）の活用
  - 教師-生徒モデルパターンでのコスト最適化

#### Task 6: MCP統合
- **目的**: Model Context ProtocolとDSPyの連携
- **手法**: ReActエージェント + MCPツール
- **学び**:
  - Claude Desktop互換の設定
  - 標準化されたツール接続
  - ファイルシステム、DB、Gitなどとの統合

#### Task 7: 実用パターン
- **目的**: プロダクション環境での設計パターン
- **手法**: 5つの実用的アーキテクチャ
- **学び**:
  - RAGシステム
  - マルチエージェントシステム
  - Self-Improvingシステム
  - ツール統合エージェント
  - ハイブリッドシステム

## DSPy + Claude統合の主要な発見

### 技術スタック
```
┌──────────────────┐
│  Claude Code SDK │  ← ユーザーインターフェース
└────────┬─────────┘
         │
┌────────▼─────────┐
│  DSPy Framework  │  ← プログラム的LM制御、最適化
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Claude Models   │  ← 高品質な推論エンジン
│  (Sonnet 4/Opus) │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  MCP Protocol    │  ← ツール統合レイヤー
└──────────────────┘
```

### Claudeモデルの使い分け戦略

| タスク | 推奨モデル | 理由 |
|--------|-----------|------|
| 複雑な推論・分析 | Claude Sonnet 4 | 最高の性能、最新機能 |
| 重要な意思決定 | Claude Opus 3.5 | 深い推論能力 |
| バランス型 | Claude Sonnet 3.5 | コストと性能のバランス |
| 高速処理・分類 | Claude Haiku 3 | 高速・低コスト |

### 最適化パターン

```python
# パターン1: 教師-生徒モデル
teacher = dspy.LM('anthropic/claude-sonnet-4-20250514')  # 高性能
student = dspy.LM('anthropic/claude-3-haiku-20240307')   # 低コスト

# パターン2: タスク別モデル選択
with dspy.context(lm=claude_sonnet4):
    complex_result = complex_reasoning(hard_problem)

with dspy.context(lm=claude_haiku):
    simple_result = simple_classification(easy_task)
```

## 結論

### DSPyが解決する問題

従来のLMプログラミングの課題：
- ❌ 手動プロンプトエンジニアリングは時間がかかる
- ❌ Few-shot例の選択が困難
- ❌ 再現性の確保が難しい
- ❌ モデル間の移植が大変

DSPyのアプローチ：
- ✅ プログラム的な定義により再利用可能
- ✅ 自動最適化でプロンプトを改善
- ✅ 型安全性によりエラーを早期発見
- ✅ モジュール性により保守が容易

### DSPy + Claudeの組み合わせの特別な利点

1. **長いコンテキスト**: Claudeの200K+トークンをDSPyで効率的に活用
2. **優れた推論**: ClaudeのCoT能力をDSPyのChainOfThoughtで最大化
3. **柔軟なモデル選択**: タスクに応じてSonnet 4/Opus/Haikuを使い分け
4. **コスト最適化**: 教師-生徒パターンで高品質・低コストを両立
5. **MCP統合**: Claude DesktopとDSPyエージェントの seamlessな連携
6. **多言語対応**: Claudeの日本語能力をDSPyで構造化

### 適用分野

DSPyは以下のタスクに特に有効：

1. **質問応答システム**: RAG、ドキュメント検索
2. **テキスト分類**: 感情分析、トピック分類
3. **情報抽出**: 構造化データの抽出
4. **推論タスク**: 数学、論理パズル
5. **マルチステップ処理**: エージェント型システム

### 今後の展開

1. **実データでの評価**: 実際のデータセットで性能評価
2. **最適化の実験**: 異なる最適化手法の比較
3. **複雑なパイプライン**: 複数モジュールの組み合わせ
4. **本番環境への適用**: 実用的なユースケースでの検証

### 推奨事項

- **小規模から始める**: シンプルなタスクでDSPyの基本を理解
- **段階的に複雑化**: モジュールを組み合わせて複雑なシステムを構築
- **最適化を活用**: 手動プロンプティングより自動最適化を優先
- **評価を重視**: メトリクスベースで継続的に改善

## 参考資料

### DSPy関連
- [DSPy GitHub](https://github.com/stanfordnlp/dspy)
- [DSPy Documentation](https://dspy.ai/)
- [DSPy Language Models Guide](https://dspy.ai/learn/programming/language_models/)
- DSPy論文: "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines"

### Anthropic Claude関連
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Models Overview](https://docs.anthropic.com/en/docs/models-overview)
- [Claude API Pricing](https://www.anthropic.com/pricing)

### Model Context Protocol (MCP)
- [MCP Documentation](https://docs.claude.com/en/docs/mcp)
- [MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)
- [DSPy + MCP Integration Example](https://github.com/ThanabordeeN/dspy-mcp-intregration)
- [How to build AI Agents with MCP](https://clickhouse.com/blog/how-to-build-ai-agents-mcp-12-frameworks)

### 実装例とチュートリアル
- [DSPy + MCP: From Brittle Prompts to Bulletproof AI Tools](https://medium.com/@richardhightower/dspy-meets-mcp-from-brittle-prompts-to-bulletproof-ai-tools-f3217698567d)
- [Programming, Not Prompting: A Hands-on Guide to DSPy](https://miptgirl.medium.com/programming-not-prompting-a-hands-on-guide-to-dspy-04ea2d966e6d)
- [DSPy + GEPA: 0→1 Builder's Guide](https://www.versalist.com/guides/dspy-start-programming-llms)
