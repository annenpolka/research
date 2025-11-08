"""
Task 3: Chain-of-Thought推論

DSPyを使って、複雑な推論タスクを段階的に解決するシステムを構築します。
マルチステップ推論、数学的問題解決などに応用できます。
"""

import dspy

# 数学問題のSignature
class MathProblem(dspy.Signature):
    """数学的な問題を解く"""

    problem: str = dspy.InputField(desc="数学的な問題")
    answer: str = dspy.OutputField(desc="問題の答え")

# マルチステップ推論のSignature
class MultiStepReasoning(dspy.Signature):
    """複雑な問題を複数のステップで解決する"""

    problem: str = dspy.InputField(desc="解決すべき問題")
    step1: str = dspy.OutputField(desc="ステップ1: 問題の理解と分解")
    step2: str = dspy.OutputField(desc="ステップ2: 関連情報の抽出")
    step3: str = dspy.OutputField(desc="ステップ3: 推論と計算")
    final_answer: str = dspy.OutputField(desc="最終的な答え")

# シンプルな数学ソルバー
class SimpleMathSolver(dspy.Module):
    def __init__(self):
        super().__init__()
        self.solve = dspy.Predict(MathProblem)

    def forward(self, problem: str):
        return self.solve(problem=problem)

# Chain-of-Thought数学ソルバー
class CoTMathSolver(dspy.Module):
    def __init__(self):
        super().__init__()
        self.solve = dspy.ChainOfThought(MathProblem)

    def forward(self, problem: str):
        return self.solve(problem=problem)

# マルチステップ推論ソルバー
class MultiStepSolver(dspy.Module):
    def __init__(self):
        super().__init__()
        self.solve = dspy.ChainOfThought(MultiStepReasoning)

    def forward(self, problem: str):
        return self.solve(problem=problem)

# 複雑なマルチホップ推論
class MultiHopQA(dspy.Module):
    """複数の推論ステップを経て答えを導く"""

    def __init__(self):
        super().__init__()
        # 最初の推論ステップ
        self.hop1 = dspy.ChainOfThought("question -> intermediate_answer")
        # 2番目の推論ステップ
        self.hop2 = dspy.ChainOfThought("question, context -> final_answer")

    def forward(self, question: str):
        # 最初のホップ
        hop1_result = self.hop1(question=question)
        # 2番目のホップ（最初の結果を使用）
        hop2_result = self.hop2(
            question=question,
            context=hop1_result.intermediate_answer
        )
        return hop2_result

def main():
    print("=" * 60)
    print("Task 3: Chain-of-Thought推論")
    print("=" * 60)

    # LMの設定
    try:
        lm = dspy.LM('openai/gpt-3.5-turbo', max_tokens=300)
        dspy.configure(lm=lm)
        use_real_lm = True
        print("OpenAI APIを使用します\n")
    except Exception as e:
        print(f"Note: OpenAI APIが利用できません: {e}")
        print("デモモードで実行します\n")
        use_real_lm = False

    # テスト問題
    math_problems = [
        "田中さんは5個のりんごを持っていました。その後、3個のりんごをもらいました。今、田中さんは何個のりんごを持っていますか？",
        "長方形の縦が8cm、横が5cmの場合、面積は何平方センチメートルですか？",
        "100から7を3回引くといくつになりますか？"
    ]

    complex_problems = [
        "AさんはBさんより3歳年上です。BさんはCさんの2倍の年齢です。Cさんが10歳の場合、Aさんは何歳ですか？",
        "ある店では、りんご1個が120円、みかん1個が80円です。りんご3個とみかん5個を買うと、合計いくらになりますか？"
    ]

    # シンプルな解法
    print("\n[1] シンプルなソルバー")
    print("-" * 60)
    simple_solver = SimpleMathSolver()

    for i, problem in enumerate(math_problems[:2], 1):
        print(f"\n問題 {i}: {problem}")
        if use_real_lm:
            try:
                result = simple_solver(problem=problem)
                print(f"答え: {result.answer}")
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print("答え: [実際のLMを使用する場合に表示されます]")
        print("-" * 40)

    # Chain-of-Thought解法
    print("\n\n[2] Chain-of-Thoughtソルバー")
    print("-" * 60)
    cot_solver = CoTMathSolver()

    for i, problem in enumerate(math_problems[:2], 1):
        print(f"\n問題 {i}: {problem}")
        if use_real_lm:
            try:
                result = cot_solver(problem=problem)
                if hasattr(result, 'reasoning'):
                    print(f"推論: {result.reasoning}")
                print(f"答え: {result.answer}")
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print("推論: [実際のLMを使用する場合に表示されます]")
            print("答え: [実際のLMを使用する場合に表示されます]")
        print("-" * 40)

    # マルチステップ解法
    print("\n\n[3] マルチステップソルバー")
    print("-" * 60)
    multistep_solver = MultiStepSolver()

    for i, problem in enumerate(complex_problems, 1):
        print(f"\n複雑な問題 {i}: {problem}")
        if use_real_lm:
            try:
                result = multistep_solver(problem=problem)
                if hasattr(result, 'step1'):
                    print(f"ステップ1: {result.step1}")
                if hasattr(result, 'step2'):
                    print(f"ステップ2: {result.step2}")
                if hasattr(result, 'step3'):
                    print(f"ステップ3: {result.step3}")
                print(f"最終回答: {result.final_answer}")
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print("ステップ1: [実際のLMを使用する場合に表示されます]")
            print("ステップ2: [実際のLMを使用する場合に表示されます]")
            print("ステップ3: [実際のLMを使用する場合に表示されます]")
            print("最終回答: [実際のLMを使用する場合に表示されます]")
        print("-" * 40)

    print("\n" + "=" * 60)
    print("分析:")
    print("=" * 60)
    print("""
DSPyでのChain-of-Thought推論:

1. シンプルなソルバー:
   - dspy.Predict を使用
   - 1ステップで直接答えを生成
   - 簡単な問題に適している

2. Chain-of-Thoughtソルバー:
   - dspy.ChainOfThought を使用
   - 推論ステップが自動的に追加される
   - 中程度の複雑さの問題に適している

3. マルチステップソルバー:
   - 明示的に複数のステップを定義
   - 構造化された推論プロセス
   - 複雑な問題解決に適している

4. メリット:
   - 推論プロセスの透明性
   - デバッグの容易さ
   - 段階的な問題解決
   - エラーの特定が簡単

5. 応用例:
   - 数学問題解決
   - ロジックパズル
   - 複雑な意思決定支援
   - マルチステップ推論タスク

6. DSPy特有の利点:
   - プログラム的な推論構造
   - 最適化可能（コンパイラで改善可能）
   - 再利用可能なモジュール
   - 型安全性
    """)

if __name__ == "__main__":
    main()
