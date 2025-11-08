"""
AutoPromptを使用したプロンプト最適化の例

このスクリプトは、コンテンツモデレーションタスクのプロンプトを
AutoPromptフレームワークを使って自動的に改善します。

必要なパッケージ:
pip install auto-prompt langchain-anthropic
"""

from auto_prompt import PromptOptimizer
from langchain_anthropic import ChatAnthropic
from typing import List, Dict

# ===========================
# 1. 初期プロンプト設定
# ===========================

INITIAL_PROMPT = """以下のコンテンツを分析し、不適切な要素があれば特定してください。

分類カテゴリ:
- safe: 問題なし
- hate_speech: ヘイトスピーチや差別的表現
- violence: 暴力的な表現
- sexual: 性的なコンテンツ
- spam: スパムや詐欺

コンテンツ: {content}

JSON形式で回答してください:
{{"category": "分類結果", "confidence": 0.0-1.0, "reason": "判断理由"}}
"""


# ===========================
# 2. トレーニングデータ
# ===========================

def create_training_samples() -> List[Dict]:
    """トレーニング用のサンプルデータ"""

    return [
        # Safe examples
        {
            "content": "この製品は本当に素晴らしいです。おすすめします！",
            "label": "safe",
            "confidence": 0.95,
        },
        {
            "content": "今日は天気が良いですね。散歩に行きましょう。",
            "label": "safe",
            "confidence": 0.99,
        },
        # Spam examples
        {
            "content": "今すぐクリック！100万円が当たるチャンス！！！",
            "label": "spam",
            "confidence": 0.90,
        },
        {
            "content": "🎉無料で稼げます🎉 LINEに登録するだけ💰",
            "label": "spam",
            "confidence": 0.85,
        },
        # Hate speech examples
        {
            "content": "あの民族は劣っている。追い出すべきだ。",
            "label": "hate_speech",
            "confidence": 0.98,
        },
        # Violence examples
        {
            "content": "暴力で解決しよう。殴ってやる。",
            "label": "violence",
            "confidence": 0.92,
        },
        # Sexual examples
        {
            "content": "18歳未満閲覧禁止 [露骨な性的描写]",
            "label": "sexual",
            "confidence": 0.88,
        },
        # Edge cases (難しい例)
        {
            "content": "この映画には暴力シーンが含まれています。R15指定です。",
            "label": "safe",  # 情報提供なので安全
            "confidence": 0.70,
        },
        {
            "content": "彼は私を憎んでいるようです。悲しいです。",
            "label": "safe",  # 感情表現なので安全
            "confidence": 0.75,
        },
        {
            "content": "期間限定セール開催中！最大50%オフ",
            "label": "safe",  # 正当な広告
            "confidence": 0.80,
        },
    ]


# ===========================
# 3. 評価関数
# ===========================

def evaluate_prediction(sample: Dict, prediction: str) -> float:
    """
    予測結果を評価

    Args:
        sample: 期待されるラベル情報
        prediction: モデルの予測結果

    Returns:
        スコア (0.0 - 1.0)
    """
    import json

    try:
        pred_data = json.loads(prediction)
        predicted_category = pred_data.get("category", "").lower()
        expected_category = sample["label"].lower()

        # 完全一致
        if predicted_category == expected_category:
            return 1.0

        # 部分一致（safe vs それ以外の区別が正しいか）
        expected_is_safe = expected_category == "safe"
        predicted_is_safe = predicted_category == "safe"

        if expected_is_safe == predicted_is_safe:
            return 0.5  # 方向性は合っているが分類が違う

        return 0.0  # 完全に間違い

    except (json.JSONDecodeError, KeyError):
        return 0.0  # パースエラー


# ===========================
# 4. 最適化実行
# ===========================

def optimize_moderation_prompt():
    """モデレーションプロンプトを最適化"""

    print("=" * 70)
    print("AutoPrompt: コンテンツモデレーションプロンプト最適化")
    print("=" * 70)

    # LLMモデル設定
    llm = ChatAnthropic(model="claude-sonnet-4.5", temperature=0.0)

    # オプティマイザー設定
    optimizer = PromptOptimizer(
        llm=llm,
        task_description="""
        コンテンツモデレーションタスク。
        ユーザー投稿コンテンツを5つのカテゴリ（safe, hate_speech, violence, sexual, spam）
        に分類します。特にエッジケース（境界的な例）で高精度が求められます。
        """,
        initial_prompt=INITIAL_PROMPT,
        max_iterations=10,  # 最適化の反復回数
        budget_usd=1.0,  # 最大コスト
    )

    # トレーニングサンプル
    samples = create_training_samples()
    print(f"\n✓ トレーニングサンプル: {len(samples)}件")

    # 最適化前の評価
    print("\n--- 最適化前の評価 ---")
    initial_scores = []

    for sample in samples[:5]:  # 最初の5つで評価
        prompt = INITIAL_PROMPT.format(content=sample["content"])
        response = llm.predict(prompt)

        score = evaluate_prediction(sample, response)
        initial_scores.append(score)

        print(f"\nコンテンツ: {sample['content'][:50]}...")
        print(f"期待: {sample['label']}")
        print(f"予測: {response[:100]}...")
        print(f"スコア: {score:.2f}")

    avg_initial_score = sum(initial_scores) / len(initial_scores)
    print(f"\n平均スコア（最適化前）: {avg_initial_score:.2%}")

    # 最適化実行
    print("\n--- 最適化実行中 ---")
    print("(境界ケースの生成、アノテーション、プロンプト改善を繰り返します)")

    result = optimizer.optimize(
        samples=samples, evaluation_fn=evaluate_prediction, verbose=True
    )

    # 結果表示
    print("\n" + "=" * 70)
    print("最適化完了！")
    print("=" * 70)

    print(f"\n【改善されたプロンプト】")
    print("-" * 70)
    print(result.optimized_prompt)
    print("-" * 70)

    print(f"\n【パフォーマンス比較】")
    print(f"最適化前の精度: {result.initial_accuracy:.2%}")
    print(f"最適化後の精度: {result.final_accuracy:.2%}")
    improvement = (
        (result.final_accuracy - result.initial_accuracy) / result.initial_accuracy
    ) * 100
    print(f"改善率: {improvement:+.1f}%")

    print(f"\n【コスト】")
    print(f"合計コスト: ${result.total_cost:.2f}")
    print(f"反復回数: {result.iterations}")

    print(f"\n【生成されたベンチマークデータセット】")
    print(f"挑戦的なテストケース: {len(result.benchmark_dataset)}件")
    for i, case in enumerate(result.benchmark_dataset[:3], 1):
        print(f"  {i}. {case['content'][:60]}...")

    return result


# ===========================
# 5. 使用例
# ===========================

def demo_optimized_prompt(optimized_prompt: str):
    """最適化されたプロンプトの使用例"""

    print("\n\n" + "=" * 70)
    print("最適化されたプロンプトの使用例")
    print("=" * 70)

    llm = ChatAnthropic(model="claude-sonnet-4.5", temperature=0.0)

    test_cases = [
        "あなたは素晴らしい人ですね！",
        "今すぐ登録で1億円💰 クリック👆",
        "特定の人種を攻撃する内容...",
        "歴史の授業で戦争について学びました。",
    ]

    for i, content in enumerate(test_cases, 1):
        print(f"\n【テストケース {i}】")
        print(f"コンテンツ: {content}")

        prompt = optimized_prompt.format(content=content)
        response = llm.predict(prompt)

        print(f"判定結果: {response}")
        print("-" * 70)


# ===========================
# メイン実行
# ===========================

if __name__ == "__main__":
    # 最適化実行
    result = optimize_moderation_prompt()

    # デモ
    demo_optimized_prompt(result.optimized_prompt)

    # 保存（オプション）
    with open("optimized_moderation_prompt.txt", "w", encoding="utf-8") as f:
        f.write(result.optimized_prompt)

    print("\n✓ 最適化されたプロンプトを 'optimized_moderation_prompt.txt' に保存しました")
