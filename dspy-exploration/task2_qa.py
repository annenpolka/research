"""
Task 2: 質問応答システム

DSPyを使って、コンテキストに基づいて質問に答えるシステムを構築します。
Retrieval-Augmented Generation (RAG) の基本形です。
"""

import dspy

# 質問応答のSignature
class QA(dspy.Signature):
    """コンテキストに基づいて質問に答える"""

    context: str = dspy.InputField(desc="背景情報や関連情報")
    question: str = dspy.InputField(desc="答えるべき質問")
    answer: str = dspy.OutputField(desc="質問に対する答え")

# Chain-of-Thought付きの質問応答
class QAWithReasoning(dspy.Signature):
    """段階的に推論しながら質問に答える"""

    context: str = dspy.InputField(desc="背景情報や関連情報")
    question: str = dspy.InputField(desc="答えるべき質問")
    reasoning: str = dspy.OutputField(desc="推論プロセス")
    answer: str = dspy.OutputField(desc="質問に対する答え")

# シンプルなQAモジュール
class SimpleQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.Predict(QA)

    def forward(self, context: str, question: str):
        return self.generate_answer(context=context, question=question)

# Chain-of-Thought QAモジュール
class CoTQA(dspy.Module):
    def __init__(self):
        super().__init__()
        # ChainOfThoughtを使うと、推論ステップが自動的に追加される
        self.generate_answer = dspy.ChainOfThought(QA)

    def forward(self, context: str, question: str):
        return self.generate_answer(context=context, question=question)

def main():
    print("=" * 60)
    print("Task 2: 質問応答システム")
    print("=" * 60)

    # LMの設定
    try:
        lm = dspy.LM('openai/gpt-3.5-turbo', max_tokens=200)
        dspy.configure(lm=lm)
        use_real_lm = True
        print("OpenAI APIを使用します\n")
    except Exception as e:
        print(f"Note: OpenAI APIが利用できません: {e}")
        print("デモモードで実行します\n")
        use_real_lm = False

    # テストデータ
    test_cases = [
        {
            "context": """
            DSPy（Declarative Self-improving Language Programs）は、
            スタンフォード大学で開発された言語モデルのプログラミングフレームワークです。
            従来の手動プロンプティングとは異なり、プロンプトをプログラム的に最適化します。
            """,
            "question": "DSPyは誰が開発しましたか？"
        },
        {
            "context": """
            富士山は日本最高峰の山で、標高は3,776メートルです。
            静岡県と山梨県にまたがる活火山で、日本の象徴として知られています。
            2013年にユネスコの世界文化遺産に登録されました。
            """,
            "question": "富士山の標高は何メートルですか？"
        },
        {
            "context": """
            Pythonは1991年にGuido van Rossumによって開発されたプログラミング言語です。
            読みやすく書きやすい構文が特徴で、AI開発やデータサイエンスで広く使われています。
            """,
            "question": "Pythonはいつ開発されましたか？"
        }
    ]

    # シンプルなQAモデル
    print("\n[1] シンプルなQAモデル")
    print("-" * 60)
    simple_qa = SimpleQA()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nケース {i}:")
        print(f"質問: {test_case['question']}")

        if use_real_lm:
            try:
                result = simple_qa(
                    context=test_case['context'],
                    question=test_case['question']
                )
                print(f"答え: {result.answer}")
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print("答え: [実際のLMを使用する場合に表示されます]")
        print("-" * 40)

    # Chain-of-Thought QAモデル
    print("\n\n[2] Chain-of-Thought QAモデル")
    print("-" * 60)
    cot_qa = CoTQA()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nケース {i}:")
        print(f"質問: {test_case['question']}")

        if use_real_lm:
            try:
                result = cot_qa(
                    context=test_case['context'],
                    question=test_case['question']
                )
                if hasattr(result, 'reasoning'):
                    print(f"推論: {result.reasoning}")
                print(f"答え: {result.answer}")
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print("推論: [実際のLMを使用する場合に表示されます]")
            print("答え: [実際のLMを使用する場合に表示されます]")
        print("-" * 40)

    print("\n" + "=" * 60)
    print("分析:")
    print("=" * 60)
    print("""
DSPyでの質問応答システムの構築:

1. シンプルなQA:
   - dspy.Predict を使用
   - 直接的な質問応答
   - 最もシンプルな実装

2. Chain-of-Thought QA:
   - dspy.ChainOfThought を使用
   - 推論ステップを自動的に追加
   - より複雑な質問に対応可能

3. メリット:
   - 簡潔なコード
   - 型安全性
   - 推論プロセスの可視化
   - 最適化の余地（コンパイル機能）

4. 実用例:
   - ドキュメント検索システム
   - カスタマーサポートボット
   - 知識ベースQA
    """)

if __name__ == "__main__":
    main()
