"""
Task 5: DSPy + Anthropic Claude統合

DSPyでAnthropicのClaudeモデルを使用する方法を探索します。
Claude Sonnet 4などの最新モデルとの統合パターンを示します。
"""

import dspy
import os

print("=" * 60)
print("Task 5: DSPy + Anthropic Claude統合")
print("=" * 60)

print("\n## 1. 基本的なClaude統合")
print("-" * 60)

print("""
DSPyはAnthropicのClaudeモデルを完全にサポートしています。
LiteLLMを通じて、すべてのClaudeモデルを使用できます。

### サポートされているモデル:
- Claude Sonnet 4 (最新)
- Claude Opus 3.5
- Claude Sonnet 3.5
- Claude Haiku 3
- その他のClaudeモデル

### 基本的なセットアップ:
""")

print("\n```python")
print("import dspy")
print()
print("# 方法1: 環境変数を使用")
print("# export ANTHROPIC_API_KEY='your-api-key'")
print("lm = dspy.LM('anthropic/claude-sonnet-4-20250514')")
print("dspy.configure(lm=lm)")
print()
print("# 方法2: API keyを直接指定")
print("lm = dspy.LM(")
print("    'anthropic/claude-3-5-sonnet-20241022',")
print("    api_key='your-api-key',")
print("    max_tokens=1000")
print(")")
print("dspy.configure(lm=lm)")
print("```")

print("\n\n## 2. Claude特有の機能を活用")
print("-" * 60)

print("""
Claudeの強みを活かしたDSPyの使い方:

1. **長いコンテキスト**: Claude 3は200K+トークンのコンテキストをサポート
2. **構造化出力**: JSONなどの構造化データ生成に優れている
3. **思考の連鎖**: 複雑な推論タスクに強い
4. **多言語対応**: 日本語を含む多言語処理が得意
""")

print("\n```python")
print("# 長文コンテキスト処理の例")
print("class LongDocumentQA(dspy.Signature):")
print('    """長い文書から情報を抽出"""')
print("    document: str = dspy.InputField(desc='長い文書（数万トークン）')")
print("    question: str = dspy.InputField(desc='質問')")
print("    answer: str = dspy.OutputField(desc='文書から抽出した答え')")
print()
print("class DocumentAnalyzer(dspy.Module):")
print("    def __init__(self):")
print("        super().__init__()")
print("        self.qa = dspy.ChainOfThought(LongDocumentQA)")
print("    ")
print("    def forward(self, document: str, question: str):")
print("        return self.qa(document=document, question=question)")
print("```")

print("\n\n## 3. 異なるClaudeモデルの比較")
print("-" * 60)

models_comparison = [
    {
        "name": "Claude Sonnet 4",
        "model_id": "anthropic/claude-sonnet-4-20250514",
        "use_case": "最新・最も高性能、複雑なタスク",
        "context": "200K+",
        "speed": "中速"
    },
    {
        "name": "Claude Opus 3.5",
        "model_id": "anthropic/claude-3-5-opus-20241022",
        "use_case": "最高の性能、難しい推論タスク",
        "context": "200K",
        "speed": "やや遅い"
    },
    {
        "name": "Claude Sonnet 3.5",
        "model_id": "anthropic/claude-3-5-sonnet-20241022",
        "use_case": "バランスの良い性能とコスト",
        "context": "200K",
        "speed": "中速"
    },
    {
        "name": "Claude Haiku 3",
        "model_id": "anthropic/claude-3-haiku-20240307",
        "use_case": "高速・低コスト、シンプルなタスク",
        "context": "200K",
        "speed": "高速"
    }
]

for model in models_comparison:
    print(f"\n### {model['name']}")
    print(f"  Model ID: {model['model_id']}")
    print(f"  用途: {model['use_case']}")
    print(f"  コンテキスト: {model['context']}トークン")
    print(f"  速度: {model['speed']}")

print("\n\n## 4. DSPy最適化器でClaudeを使用")
print("-" * 60)

print("""
DSPyの自動最適化機能でClaudeを使用できます。
特にMIPROv2最適化器でClaude Sonnet 4を教師モデルとして使用すると効果的です。

```python
import dspy

# 教師モデル（高性能）としてClaude Sonnet 4を使用
teacher_lm = dspy.LM('anthropic/claude-sonnet-4-20250514')

# 生徒モデル（低コスト）としてClaude Haikuを使用
student_lm = dspy.LM('anthropic/claude-3-haiku-20240307')

# 生徒モデルで実行するプログラム
program = MyDSPyProgram()

# 最適化器の設定
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=my_metric_function,
    teacher_settings=dict(lm=teacher_lm),
)

# 最適化実行
with dspy.context(lm=student_lm):
    optimized_program = optimizer.compile(
        program,
        trainset=my_training_data,
        num_trials=10
    )

# 最適化されたプログラムで予測
result = optimized_program(input_data)
```

この方法により:
- 高性能なClaude Sonnet 4の知識を活用
- 実行時は低コストなHaikuで運用
- 自動的にプロンプトを最適化
""")

print("\n\n## 5. Claudeの思考プロセスを活用")
print("-" * 60)

print("""
ClaudeはChain-of-Thoughtに優れているため、
DSPyのChainOfThoughtと相性が良いです。

```python
class ComplexReasoning(dspy.Signature):
    '''複雑な推論タスク'''
    problem: str = dspy.InputField()
    reasoning: str = dspy.OutputField(desc='段階的な思考プロセス')
    answer: str = dspy.OutputField(desc='最終的な答え')

class ReasoningModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # ChainOfThoughtでClaudeの推論能力を最大限活用
        self.reason = dspy.ChainOfThought(ComplexReasoning)

    def forward(self, problem: str):
        return self.reason(problem=problem)

# Claude Sonnet 4で実行
lm = dspy.LM('anthropic/claude-sonnet-4-20250514', max_tokens=2000)
dspy.configure(lm=lm)

reasoner = ReasoningModule()
result = reasoner(problem='複雑な問題...')
print(result.reasoning)  # 詳細な思考プロセス
print(result.answer)     # 最終的な答え
```
""")

print("\n\n## 6. コンテキスト管理の活用")
print("-" * 60)

print("""
DSPyのコンテキスト管理機能で、異なるClaudeモデルを
タスクに応じて使い分けることができます。

```python
# 複雑なタスク用の高性能モデル
complex_lm = dspy.LM('anthropic/claude-sonnet-4-20250514')

# シンプルなタスク用の高速モデル
simple_lm = dspy.LM('anthropic/claude-3-haiku-20240307')

# タスクに応じてモデルを切り替え
with dspy.context(lm=complex_lm):
    # 複雑な推論タスク
    complex_result = complex_module(difficult_input)

with dspy.context(lm=simple_lm):
    # シンプルな分類タスク
    simple_result = classification_module(easy_input)
```

これにより:
- コストとパフォーマンスのバランスを最適化
- タスクの複雑さに応じたモデル選択
- 効率的なリソース使用
""")

print("\n\n## 7. 実際の使用例")
print("-" * 60)

# 実際にClaudeが利用可能か確認
if os.getenv('ANTHROPIC_API_KEY'):
    print("\nANTHROPIC_API_KEYが設定されています。")
    print("実際にClaudeを使用したデモを実行します...\n")

    try:
        # Claude Haikuで簡単な例を実行
        lm = dspy.LM('anthropic/claude-3-haiku-20240307', max_tokens=100)
        dspy.configure(lm=lm)

        # シンプルな分類タスク
        class SimpleClassify(dspy.Signature):
            """テキストを分類"""
            text: str = dspy.InputField()
            category: str = dspy.OutputField(desc="カテゴリー")

        classifier = dspy.Predict(SimpleClassify)

        test_texts = [
            "今日は天気が良いですね。",
            "新しいPythonライブラリをインストールしました。",
            "美味しいラーメンを食べました。"
        ]

        for text in test_texts:
            result = classifier(text=text)
            print(f"テキスト: {text}")
            print(f"カテゴリー: {result.category}")
            print("-" * 40)

    except Exception as e:
        print(f"エラー: {e}")
        print("\nAPI keyの確認が必要です。")
else:
    print("\nANTHROPIC_API_KEYが設定されていません。")
    print("\n実際に使用するには:")
    print("export ANTHROPIC_API_KEY='your-api-key'")

print("\n\n" + "=" * 60)
print("まとめ")
print("=" * 60)

print("""
DSPy + Anthropic Claudeの統合により:

✅ 最新のClaudeモデル（Sonnet 4など）を使用可能
✅ 長いコンテキスト（200K+トークン）を活用
✅ 優れた推論能力をChain-of-Thoughtで活用
✅ 自動最適化でプロンプトを改善
✅ モデルの使い分けでコスト最適化
✅ 構造化出力に優れたClaudeの強みを活用

次のステップ:
1. MCP（Model Context Protocol）との統合
2. Claude Code SDKとの連携
3. ツール使用（ReAct Agent）の実装
4. 実データでの評価とベンチマーク
""")

if __name__ == "__main__":
    pass
