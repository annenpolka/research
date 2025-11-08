"""
Task 4: DSPyの最適化機能

DSPyの真の強みは、プロンプトとパラメータを自動的に最適化できることです。
このタスクでは、BootstrapFewShotなどの最適化手法を示します。
"""

import dspy
from typing import List

# 数値計算の正確性を評価するためのSignature
class MathQA(dspy.Signature):
    """数学的な質問に答える"""

    question: str = dspy.InputField(desc="数学の問題")
    answer: str = dspy.OutputField(desc="計算結果（数値のみ）")

# 基本的なQAモジュール
class BasicMathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.Predict(MathQA)

    def forward(self, question: str):
        return self.generate_answer(question=question)

# Chain-of-ThoughtベースのQAモジュール
class CoTMathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThought(MathQA)

    def forward(self, question: str):
        return self.generate_answer(question=question)

def create_training_set():
    """トレーニング用のデータセット作成"""
    return [
        dspy.Example(
            question="3 + 5は？",
            answer="8"
        ).with_inputs("question"),
        dspy.Example(
            question="10 - 4は？",
            answer="6"
        ).with_inputs("question"),
        dspy.Example(
            question="6 × 7は？",
            answer="42"
        ).with_inputs("question"),
        dspy.Example(
            question="15 ÷ 3は？",
            answer="5"
        ).with_inputs("question"),
        dspy.Example(
            question="2 + 3 × 4は？",
            answer="14"
        ).with_inputs("question"),
    ]

def create_test_set():
    """テスト用のデータセット作成"""
    return [
        dspy.Example(
            question="7 + 8は？",
            answer="15"
        ).with_inputs("question"),
        dspy.Example(
            question="20 - 12は？",
            answer="8"
        ).with_inputs("question"),
        dspy.Example(
            question="5 × 9は？",
            answer="45"
        ).with_inputs("question"),
    ]

def validate_answer(example, pred, trace=None):
    """答えが正しいかを検証"""
    # 予測された答えから数値を抽出
    try:
        predicted = ''.join(filter(str.isdigit, str(pred.answer)))
        expected = ''.join(filter(str.isdigit, example.answer))
        return predicted == expected
    except:
        return False

def main():
    print("=" * 60)
    print("Task 4: DSPyの最適化機能")
    print("=" * 60)

    print("""
DSPyの最適化機能の概要:

1. BootstrapFewShot:
   - 少数の例から学習してプロンプトを改善
   - 自動的に良い例を選択

2. MIPROv2:
   - メトリック駆動の指示最適化
   - 複数の候補から最良のプロンプトを選択

3. BootstrapFinetune:
   - LMのファインチューニング用データ生成
   - 高品質な教師データの自動作成

コード構造の例:
    """)

    print("\n# トレーニングデータの準備")
    print("trainset = create_training_set()")

    print("\n# 基本モデルの作成")
    print("basic_model = BasicMathQA()")

    print("\n# 最適化器の設定（例: BootstrapFewShot）")
    print("optimizer = dspy.BootstrapFewShot(")
    print("    metric=validate_answer,")
    print("    max_bootstrapped_demos=4,")
    print("    max_labeled_demos=4")
    print(")")

    print("\n# モデルの最適化（コンパイル）")
    print("optimized_model = optimizer.compile(")
    print("    student=basic_model,")
    print("    trainset=trainset")
    print(")")

    print("\n# 最適化されたモデルで予測")
    print("prediction = optimized_model(question='新しい質問')")

    print("\n" + "=" * 60)
    print("最適化のメリット:")
    print("=" * 60)
    print("""
1. 自動プロンプトエンジニアリング:
   - 手動でのプロンプト調整が不要
   - データから最適なプロンプトを学習

2. Few-shot学習の自動化:
   - 最も効果的な例を自動選択
   - 例の順序も最適化

3. 再現性:
   - プログラム的に定義されているため再現可能
   - バージョン管理が容易

4. スケーラビリティ:
   - 大規模なタスクにも対応
   - 複数のモジュールを組み合わせ可能

5. 評価とイテレーション:
   - メトリクスベースの評価
   - 継続的な改善が可能
    """)

    print("\n" + "=" * 60)
    print("実際の使用例:")
    print("=" * 60)
    print("""
# 実際に使用する場合の完全な例:

import dspy

# LMの設定
lm = dspy.LM('openai/gpt-3.5-turbo')
dspy.configure(lm=lm)

# トレーニングデータ
trainset = [
    dspy.Example(question="3+5は？", answer="8").with_inputs("question"),
    # ... more examples
]

# モデル定義
class MathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought("question -> answer")

    def forward(self, question):
        return self.generate(question=question)

# 最適化
optimizer = dspy.BootstrapFewShot(metric=validate_answer)
optimized = optimizer.compile(MathQA(), trainset=trainset)

# 予測
result = optimized(question="7+8は？")
print(result.answer)
    """)

    print("\n" + "=" * 60)
    print("DSPyが解決する問題:")
    print("=" * 60)
    print("""
従来のアプローチの課題:
1. プロンプトエンジニアリングに時間がかかる
2. Few-shot例の選択が難しい
3. モデル間の移植が困難
4. 再現性の確保が難しい

DSPyのソリューション:
1. 自動最適化により時間を節約
2. データ駆動で例を選択
3. モジュール化により移植が容易
4. プログラム的定義で再現性を確保
    """)

if __name__ == "__main__":
    main()
