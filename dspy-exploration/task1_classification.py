"""
Task 1: テキスト分類（感情分析）

DSPyを使ってテキストの感情を分類するシステムを構築します。
このタスクでは、DSPyの基本的なSignatureとModuleの使い方を学びます。
"""

import dspy
from typing import Literal

# DSPyのSignature（入力と出力の定義）
class SentimentClassification(dspy.Signature):
    """テキストの感情を分類する"""

    text: str = dspy.InputField(desc="分類したいテキスト")
    sentiment: Literal["positive", "negative", "neutral"] = dspy.OutputField(
        desc="テキストの感情（positive, negative, neutralのいずれか）"
    )

# DSPyのModule（ロジックの定義）
class SentimentClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        # PredictモジュールでSignatureを使用
        self.classify = dspy.Predict(SentimentClassification)

    def forward(self, text: str):
        result = self.classify(text=text)
        return result

def main():
    print("=" * 60)
    print("Task 1: テキスト分類（感情分析）")
    print("=" * 60)

    # LMの設定（実際のAPIがない場合のデモ用）
    # 実際に使う場合は、OpenAI API keyなどを設定
    try:
        # 環境変数にOPENAI_API_KEYが設定されていれば使用
        lm = dspy.LM('openai/gpt-3.5-turbo', max_tokens=100)
        dspy.configure(lm=lm)
        use_real_lm = True
        print("OpenAI APIを使用します\n")
    except Exception as e:
        print(f"Note: OpenAI APIが利用できません: {e}")
        print("デモモードで実行します（実際のLM呼び出しなし）\n")
        use_real_lm = False

    # モデルのインスタンス化
    classifier = SentimentClassifier()

    # テストデータ
    test_texts = [
        "I love this product! It's amazing!",
        "This is terrible and I hate it.",
        "It's okay, nothing special.",
        "今日は素晴らしい一日でした！",
        "最悪な体験だった。"
    ]

    print("\n分類結果:\n")
    if use_real_lm:
        for text in test_texts:
            try:
                result = classifier(text=text)
                print(f"テキスト: {text}")
                print(f"感情: {result.sentiment}")
                print("-" * 40)
            except Exception as e:
                print(f"テキスト: {text}")
                print(f"エラー: {e}")
                print("-" * 40)
    else:
        print("デモ用のコード構造を表示:")
        print("- SentimentClassification Signature定義済み")
        print("- SentimentClassifier Module定義済み")
        print("\n実際に実行するには、OpenAI API keyを設定してください:")
        print("export OPENAI_API_KEY='your-api-key'")
        print("\n期待される出力例:")
        for text in test_texts[:3]:
            print(f"\nテキスト: {text}")
            if "love" in text or "amazing" in text:
                print(f"感情: positive")
            elif "terrible" in text or "hate" in text:
                print(f"感情: negative")
            else:
                print(f"感情: neutral")
            print("-" * 40)

    print("\n" + "=" * 60)
    print("分析:")
    print("=" * 60)
    print("""
DSPyのSignatureとModuleの基本的な使い方:

1. Signature: タスクの入力と出力を定義
   - InputField: 入力パラメータ
   - OutputField: 期待される出力

2. Module: 実際のロジックを実装
   - dspy.Predict: 基本的な予測モジュール
   - forward(): 実行時に呼ばれるメソッド

3. メリット:
   - 型安全な定義
   - 明確なインターフェース
   - 再利用可能なコンポーネント
    """)

if __name__ == "__main__":
    main()
