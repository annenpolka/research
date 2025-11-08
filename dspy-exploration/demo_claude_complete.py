"""
完全なDSPy + Claude統合デモ

このスクリプトは、DSPyとClaude Sonnet 4を組み合わせた
実用的な例を示します。
"""

import dspy
import os
from typing import List, Optional

print("=" * 70)
print("DSPy + Claude Sonnet 4 完全デモ")
print("=" * 70)

# API key確認
has_api_key = bool(os.getenv('ANTHROPIC_API_KEY'))

if has_api_key:
    print("\n✓ ANTHROPIC_API_KEYが設定されています")
    print("  実際のClaudeモデルで実行します\n")
else:
    print("\n⚠ ANTHROPIC_API_KEYが設定されていません")
    print("  コード構造のデモのみ実行します")
    print("  実際に使用するには: export ANTHROPIC_API_KEY='your-key'\n")

print("=" * 70)
print("例1: 基本的なテキスト処理")
print("=" * 70)

# Signature定義
class TextAnalysis(dspy.Signature):
    """テキストを分析して構造化された情報を抽出"""

    text: str = dspy.InputField(desc="分析対象のテキスト")
    summary: str = dspy.OutputField(desc="簡潔な要約")
    key_points: str = dspy.OutputField(desc="主要なポイント（箇条書き）")
    sentiment: str = dspy.OutputField(desc="感情（positive/negative/neutral）")

# Module定義
class TextAnalyzer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(TextAnalysis)

    def forward(self, text: str):
        return self.analyze(text=text)

if has_api_key:
    # Claude Sonnet 4を使用
    lm = dspy.LM('anthropic/claude-sonnet-4-20250514', max_tokens=500)
    dspy.configure(lm=lm)

    analyzer = TextAnalyzer()

    sample_text = """
    DSPyは、スタンフォード大学で開発された革新的なフレームワークです。
    従来のプロンプトエンジニアリングとは異なり、プログラム的にLMの動作を定義し、
    自動的に最適化することができます。これにより、開発者はより保守しやすく、
    スケーラブルなAIアプリケーションを構築できます。
    """

    print("\n入力テキスト:")
    print(sample_text.strip())
    print("\n分析中...")

    try:
        result = analyzer(text=sample_text)
        print("\n【分析結果】")
        print(f"\n要約:\n{result.summary}")
        print(f"\n主要ポイント:\n{result.key_points}")
        print(f"\n感情: {result.sentiment}")
    except Exception as e:
        print(f"\nエラー: {e}")
else:
    print("\n【コード構造】")
    print("✓ TextAnalysis Signature定義")
    print("  - 入力: text")
    print("  - 出力: summary, key_points, sentiment")
    print("\n✓ TextAnalyzer Module実装")
    print("  - ChainOfThoughtで推論を強化")

print("\n" + "=" * 70)
print("例2: マルチステップ推論")
print("=" * 70)

class Problem(dspy.Signature):
    """問題を理解して解決策を提案"""

    problem_description: str = dspy.InputField(desc="問題の説明")
    problem_analysis: str = dspy.OutputField(desc="問題の分析")
    root_causes: str = dspy.OutputField(desc="根本原因の特定")
    solutions: str = dspy.OutputField(desc="解決策の提案")
    action_plan: str = dspy.OutputField(desc="実行プラン")

class ProblemSolver(dspy.Module):
    def __init__(self):
        super().__init__()
        # マルチステップ推論
        self.solve = dspy.ChainOfThought(Problem)

    def forward(self, problem_description: str):
        return self.solve(problem_description=problem_description)

if has_api_key:
    solver = ProblemSolver()

    problem = """
    Webアプリケーションのレスポンスタイムが徐々に遅くなっている。
    初期は100msだったのが、現在は500ms以上かかることがある。
    ユーザー数は3ヶ月で2倍になった。
    """

    print("\n問題:")
    print(problem.strip())
    print("\n解決中...")

    try:
        result = solver(problem_description=problem)
        print("\n【解決策】")
        print(f"\n問題分析:\n{result.problem_analysis}")
        print(f"\n根本原因:\n{result.root_causes}")
        print(f"\n解決策:\n{result.solutions}")
        print(f"\n実行プラン:\n{result.action_plan}")
    except Exception as e:
        print(f"\nエラー: {e}")
else:
    print("\n【コード構造】")
    print("✓ Problem Signature定義")
    print("  - 複数の出力フィールドで段階的に推論")
    print("\n✓ ProblemSolver Module")
    print("  - ChainOfThoughtで複雑な問題を解決")

print("\n" + "=" * 70)
print("例3: モデルの使い分け（コスト最適化）")
print("=" * 70)

print("""
タスクの複雑さに応じてモデルを使い分けることで、
コストとパフォーマンスを最適化できます。
""")

print("\n【戦略】")
print("- シンプルなタスク: Claude Haiku（高速・低コスト）")
print("- 中程度のタスク: Claude Sonnet（バランス型）")
print("- 複雑なタスク: Claude Opus/Sonnet 4（高性能）")

if has_api_key:
    # 高速モデル
    fast_lm = dspy.LM('anthropic/claude-3-haiku-20240307', max_tokens=100)
    # 高性能モデル
    powerful_lm = dspy.LM('anthropic/claude-sonnet-4-20250514', max_tokens=500)

    # シンプルな分類タスク
    class SimpleClassify(dspy.Signature):
        """シンプルな分類"""
        text: str = dspy.InputField()
        category: str = dspy.OutputField(desc="カテゴリー: tech/business/other")

    print("\n【シンプルなタスク - Haikuを使用】")
    with dspy.context(lm=fast_lm):
        classifier = dspy.Predict(SimpleClassify)
        try:
            result = classifier(text="新しいPythonライブラリがリリースされました")
            print(f"分類結果: {result.category}")
        except Exception as e:
            print(f"エラー: {e}")

    print("\n【複雑なタスク - Sonnet 4を使用】")
    with dspy.context(lm=powerful_lm):
        solver = ProblemSolver()
        # 複雑な推論を実行
        print("複雑な問題解決を実行中...")
else:
    print("\n【コード例】")
    print("""
    # モデルの定義
    fast_lm = dspy.LM('anthropic/claude-3-haiku-20240307')
    powerful_lm = dspy.LM('anthropic/claude-sonnet-4-20250514')

    # タスクに応じて使い分け
    with dspy.context(lm=fast_lm):
        # シンプルなタスク
        result1 = simple_task()

    with dspy.context(lm=powerful_lm):
        # 複雑なタスク
        result2 = complex_task()
    """)

print("\n" + "=" * 70)
print("例4: 最適化（BootstrapFewShot）")
print("=" * 70)

print("""
DSPyの自動最適化機能を使用して、プロンプトを改善できます。
Claudeを教師モデルとして使用することで、高品質な最適化が可能です。
""")

print("\n【最適化プロセス】")
print("""
1. トレーニングデータを準備
2. 評価メトリクスを定義
3. BootstrapFewShotで最適化
4. 最適化されたモデルで予測

コード例:
```python
# トレーニングデータ
trainset = [
    dspy.Example(input="...", output="...").with_inputs("input"),
    # ... more examples
]

# 評価メトリクス
def metric(example, prediction, trace=None):
    return example.output == prediction.output

# 最適化
optimizer = dspy.BootstrapFewShot(
    metric=metric,
    max_bootstrapped_demos=4
)

# Claudeモデルで最適化
lm = dspy.LM('anthropic/claude-sonnet-4-20250514')
dspy.configure(lm=lm)

# 最適化実行
optimized_program = optimizer.compile(
    student=my_program,
    trainset=trainset
)
```
""")

print("\n" + "=" * 70)
print("まとめと次のステップ")
print("=" * 70)

print("""
このデモで示した内容:

✅ DSPy + Claude Sonnetの基本的な統合
✅ Signature/Moduleによる構造化されたLMプログラミング
✅ ChainOfThoughtによる推論の強化
✅ モデルの使い分けによるコスト最適化
✅ 自動最適化の概要

実用的な応用例:

1. 📝 ドキュメント分析・要約
   - 長文の理解（200K+トークン）
   - 構造化された出力

2. 🔍 質問応答システム
   - RAGパイプライン
   - マルチホップ推論

3. 🤖 自律エージェント
   - ReActパターン
   - MCP統合によるツール使用

4. 💡 問題解決支援
   - 段階的な分析
   - 実行可能な提案

次の探索:
- MCP統合による実用的なツール使用
- カスタム最適化器の開発
- 本番環境でのパフォーマンステスト
- マルチモーダル機能の活用
""")

if not has_api_key:
    print("\n" + "=" * 70)
    print("実際に試すには:")
    print("=" * 70)
    print("""
    1. Anthropic APIキーを取得
       https://console.anthropic.com/

    2. 環境変数を設定
       export ANTHROPIC_API_KEY='your-api-key'

    3. このスクリプトを再実行
       python demo_claude_complete.py
    """)

print("\n" + "=" * 70)

if __name__ == "__main__":
    pass
