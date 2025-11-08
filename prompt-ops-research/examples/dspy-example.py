"""
DSPyを使用したプロンプト自動最適化の例

このスクリプトは、カスタマーサポートチャットボットのプロンプトを
DSPyのMIPROv2オプティマイザーを使って自動的に改善します。

必要なパッケージ:
pip install dspy-ai anthropic
"""

import dspy
from dspy.teleprompt import MIPROv2
from typing import List

# ===========================
# 1. モデル設定
# ===========================

# Claude Sonnet 4.5を使用
claude = dspy.Claude(model="claude-sonnet-4.5")
dspy.settings.configure(lm=claude)


# ===========================
# 2. タスク定義（Signature）
# ===========================

class CustomerSupport(dspy.Signature):
    """カスタマー問い合わせに対して親切で正確に回答する"""

    question = dspy.InputField(desc="カスタマーからの質問")
    context = dspy.InputField(desc="製品情報とFAQデータ")
    answer = dspy.OutputField(desc="親切で正確な回答（日本語）")


# ===========================
# 3. モジュール（プログラム）
# ===========================

class SupportBot(dspy.Module):
    """カスタマーサポートボットのメインモジュール"""

    def __init__(self):
        super().__init__()
        # Chain-of-Thoughtを使用して推論プロセスを明示
        self.generate_answer = dspy.ChainOfThought(CustomerSupport)

    def forward(self, question, context):
        """問い合わせに回答"""
        return self.generate_answer(question=question, context=context)


# ===========================
# 4. トレーニングデータ
# ===========================

def create_training_data() -> List[dspy.Example]:
    """トレーニング用のサンプルデータを作成"""

    examples = [
        dspy.Example(
            question="返品ポリシーを教えてください",
            context="返品: 商品到着後30日以内、未使用・未開封の場合のみ可能。返送料はお客様負担。",
            answer="商品到着後30日以内であれば、未使用・未開封の商品に限り返品が可能です。返送料はお客様にご負担いただきます。",
        ).with_inputs("question", "context"),
        dspy.Example(
            question="配送にどのくらいかかりますか？",
            context="配送: 通常配送は3-5営業日、速達配送は1-2営業日。離島は追加で2-3日。",
            answer="通常配送の場合は3-5営業日、速達配送は1-2営業日でお届けします。離島への配送は、さらに2-3日かかる場合がございます。",
        ).with_inputs("question", "context"),
        dspy.Example(
            question="保証期間は？",
            context="保証: すべての製品に1年間のメーカー保証。延長保証（2年間）も購入可能（+5,000円）。",
            answer="すべての製品に1年間のメーカー保証が付いています。また、追加で5,000円お支払いいただくことで、2年間の延長保証もご利用いただけます。",
        ).with_inputs("question", "context"),
        dspy.Example(
            question="支払い方法は何がありますか？",
            context="支払い: クレジットカード（Visa/MasterCard/JCB/AMEX）、銀行振込、コンビニ払い、代金引換。",
            answer="クレジットカード（Visa、MasterCard、JCB、American Express）、銀行振込、コンビニ払い、代金引換をご利用いただけます。",
        ).with_inputs("question", "context"),
        dspy.Example(
            question="会員登録の特典は？",
            context="会員特典: 購入時5%ポイント還元、送料無料（5,000円以上）、誕生日クーポン1,000円分、セール先行案内。",
            answer="会員登録いただくと、購入時に5%のポイント還元、5,000円以上のご購入で送料無料、誕生日に1,000円分のクーポン、セールの先行案内など、様々な特典をご利用いただけます。",
        ).with_inputs("question", "context"),
        dspy.Example(
            question="在庫切れの商品はいつ入荷しますか？",
            context="在庫: 在庫切れ商品は通常2-4週間で入荷。入荷通知メール登録可能。",
            answer="在庫切れの商品は、通常2-4週間で入荷予定です。商品ページから入荷通知メールにご登録いただくと、入荷時に自動でお知らせいたします。",
        ).with_inputs("question", "context"),
    ]

    return examples


# ===========================
# 5. 評価指標
# ===========================

def accuracy_metric(example, pred, trace=None) -> float:
    """
    回答の品質を評価
    - キーワードマッチング
    - 丁寧さのチェック
    - 適切な長さ
    """
    score = 0.0

    # 基本: 期待される回答の主要な単語が含まれているか
    expected_keywords = example.answer.lower().split()
    predicted_keywords = pred.answer.lower().split()

    # キーワードマッチング（最大50点）
    matches = sum(1 for word in expected_keywords if word in predicted_keywords)
    score += (matches / len(expected_keywords)) * 0.5

    # 丁寧さチェック（最大25点）
    polite_words = ["ます", "ください", "いただけ", "ございます"]
    if any(word in pred.answer for word in polite_words):
        score += 0.25

    # 適切な長さ（最大25点）
    length_ratio = len(pred.answer) / len(example.answer)
    if 0.7 <= length_ratio <= 1.5:
        score += 0.25

    return score


# ===========================
# 6. 最適化実行
# ===========================

def optimize_prompt():
    """プロンプトを自動最適化"""

    print("=" * 60)
    print("DSPy プロンプト最適化開始")
    print("=" * 60)

    # トレーニングデータ準備
    trainset = create_training_data()
    print(f"\n✓ トレーニングデータ: {len(trainset)}件")

    # 初期ボット
    initial_bot = SupportBot()

    # 最適化前のパフォーマンス測定
    print("\n--- 最適化前の評価 ---")
    initial_scores = []
    for example in trainset[:3]:  # 最初の3つでテスト
        pred = initial_bot(question=example.question, context=example.context)
        score = accuracy_metric(example, pred)
        initial_scores.append(score)
        print(f"Q: {example.question}")
        print(f"A: {pred.answer}")
        print(f"Score: {score:.2f}\n")

    avg_initial_score = sum(initial_scores) / len(initial_scores)
    print(f"平均スコア（最適化前）: {avg_initial_score:.2f}")

    # オプティマイザー設定
    print("\n--- MIPROv2オプティマイザー起動 ---")
    optimizer = MIPROv2(
        metric=accuracy_metric,
        num_candidates=5,  # 生成する候補プロンプト数
        init_temperature=1.0,
    )

    # 最適化実行
    print("最適化実行中...")
    optimized_bot = optimizer.compile(
        SupportBot(), trainset=trainset, num_trials=10  # 試行回数
    )

    # 最適化後のパフォーマンス測定
    print("\n--- 最適化後の評価 ---")
    optimized_scores = []
    for example in trainset[:3]:
        pred = optimized_bot(question=example.question, context=example.context)
        score = accuracy_metric(example, pred)
        optimized_scores.append(score)
        print(f"Q: {example.question}")
        print(f"A: {pred.answer}")
        print(f"Score: {score:.2f}\n")

    avg_optimized_score = sum(optimized_scores) / len(optimized_scores)
    print(f"平均スコア（最適化後）: {avg_optimized_score:.2f}")

    # 改善率
    improvement = ((avg_optimized_score - avg_initial_score) / avg_initial_score) * 100
    print(f"\n✓ 改善率: {improvement:+.1f}%")

    print("\n" + "=" * 60)
    print("最適化完了！")
    print("=" * 60)

    return optimized_bot


# ===========================
# 7. 使用例
# ===========================

def demo_usage(bot: SupportBot):
    """最適化されたボットの使用例"""

    print("\n\n" + "=" * 60)
    print("最適化されたボットの使用例")
    print("=" * 60)

    test_cases = [
        {
            "question": "キャンセルはできますか？",
            "context": "キャンセル: 発送前なら無料でキャンセル可能。発送後はキャンセル不可、返品対応。",
        },
        {
            "question": "ポイントの有効期限は？",
            "context": "ポイント: 最終購入日から1年間有効。期限前に使用すれば延長。",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n【テストケース {i}】")
        print(f"質問: {case['question']}")

        result = bot(question=case["question"], context=case["context"])

        print(f"回答: {result.answer}")
        print("-" * 60)


# ===========================
# メイン実行
# ===========================

if __name__ == "__main__":
    # 最適化実行
    optimized_bot = optimize_prompt()

    # デモ
    demo_usage(optimized_bot)

    # 保存（オプション）
    # optimized_bot.save("optimized_support_bot.json")
    print("\n✓ 最適化されたボットを使用できます")
