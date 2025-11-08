#!/usr/bin/env python3
"""
romkan と jaconv を使用した日本語からローマ字への変換テスト
注: これらは主にかな→ローマ字の変換を行い、漢字変換には対応していない
"""
import romkan
import jaconv
import time


def test_romkan():
    """romkanの基本的な使用例とテスト（かな→ローマ字のみ）"""

    print("=" * 80)
    print("romkan テスト（かな→ローマ字変換）")
    print("=" * 80)

    # かなのみのテストケース
    kana_test_cases = [
        "ひらがな",
        "カタカナ",
        "こんにちは",
        "ありがとう",
        "さようなら",
        "おはよう",
        "すみません",
    ]

    print("\nひらがな/カタカナからローマ字への変換:")
    results = []

    for text in kana_test_cases:
        start_time = time.time()
        romaji = romkan.to_roma(text)
        elapsed_time = time.time() - start_time

        print(f"  {text} → {romaji} ({elapsed_time*1000:.2f}ms)")

        results.append({
            'input': text,
            'romaji': romaji,
            'time': elapsed_time
        })

    # 漢字を含むケース（変換されないことを確認）
    print("\n漢字を含むテキスト（漢字は変換されない）:")
    kanji_test_cases = [
        "日本語",
        "東京タワー",
        "こんにちは世界",
    ]

    for text in kanji_test_cases:
        romaji = romkan.to_roma(text)
        print(f"  {text} → {romaji}")

    return results


def test_romkan_advanced():
    """romkanの高度な機能のテスト"""

    print("\n" + "=" * 80)
    print("romkan 高度な機能テスト")
    print("=" * 80)

    # ローマ字からひらがなへの逆変換
    print("\nローマ字からひらがなへの変換:")
    romaji_test_cases = [
        "konnichiha",
        "arigatou",
        "sayounara",
        "ohayou",
    ]

    for text in romaji_test_cases:
        hiragana = romkan.to_hiragana(text)
        katakana = romkan.to_katakana(text)
        print(f"  {text} → ひらがな: {hiragana}, カタカナ: {katakana}")

    # 複雑な音のテスト
    print("\n複雑な音のテスト:")
    complex_cases = [
        "きゃ",  # 拗音
        "しゃ",
        "ちゃ",
        "にゃ",
        "きょう",  # 長音
        "とうきょう",
        "きっぷ",  # 促音
        "がっこう",
    ]

    for text in complex_cases:
        romaji = romkan.to_roma(text)
        print(f"  {text} → {romaji}")


def test_jaconv():
    """jaconvの基本的な使用例とテスト（文字変換）"""

    print("\n" + "=" * 80)
    print("jaconv テスト（文字変換）")
    print("=" * 80)

    # テストケース
    test_cases = [
        "ひらがな",
        "カタカナ",
        "ＡＢＣ１２３",  # 全角英数字
        "こんにちは世界",
        "全角カタカナ",
        "半角ｶﾀｶﾅ",
    ]

    print("\n様々な文字変換:")

    for text in test_cases:
        print(f"\n入力: {text}")

        # ひらがな→カタカナ
        kata = jaconv.hira2kata(text)
        print(f"  ひら→カタ: {kata}")

        # カタカナ→ひらがな
        hira = jaconv.kata2hira(text)
        print(f"  カタ→ひら: {hira}")

        # 全角→半角
        han = jaconv.z2h(text)
        print(f"  全角→半角: {han}")

        # 半角→全角
        zen = jaconv.h2z(text)
        print(f"  半角→全角: {zen}")


def test_jaconv_advanced():
    """jaconvの高度な機能のテスト"""

    print("\n" + "=" * 80)
    print("jaconv 高度な機能テスト")
    print("=" * 80)

    # 様々な変換オプション
    test_text = "ＡＢＣ１２３abc123"

    print(f"\n入力: {test_text}")
    print(f"全角→半角（数字のみ）: {jaconv.z2h(test_text, digit=True, ascii=False)}")
    print(f"全角→半角（英字のみ）: {jaconv.z2h(test_text, digit=False, ascii=True)}")
    print(f"全角→半角（全て）: {jaconv.z2h(test_text, digit=True, ascii=True)}")

    # カタカナの半角全角変換
    kata_text = "カタカナ"
    print(f"\n入力: {kata_text}")
    print(f"カタカナ→半角カタカナ: {jaconv.z2h(kata_text, kana=True)}")

    half_kata_text = "ｶﾀｶﾅ"
    print(f"\n入力: {half_kata_text}")
    print(f"半角カタカナ→全角カタカナ: {jaconv.h2z(half_kata_text, kana=True)}")


def test_combined_approach():
    """pykakasiとromkanを組み合わせたアプローチ"""

    print("\n" + "=" * 80)
    print("組み合わせアプローチテスト（pykakasi + romkan）")
    print("=" * 80)

    try:
        import pykakasi

        kks = pykakasi.kakasi()

        test_cases = [
            "日本語",
            "東京タワー",
            "こんにちは世界",
        ]

        print("\n1. pykakasiで漢字→かな")
        print("2. romkanでかな→ローマ字")

        for text in test_cases:
            # ステップ1: pykakasiで漢字→ひらがな
            result = kks.convert(text)
            hiragana = ''.join([item['hira'] for item in result])

            # ステップ2: romkanでひらがな→ローマ字
            romaji_romkan = romkan.to_roma(hiragana)

            # 比較: pykakasiの直接ローマ字化
            romaji_pykakasi = ''.join([item['hepburn'] for item in result])

            print(f"\n入力: {text}")
            print(f"  中間（ひらがな）: {hiragana}")
            print(f"  pykakasi→romkan: {romaji_romkan}")
            print(f"  pykakasi直接: {romaji_pykakasi}")

    except ImportError:
        print("pykakasiがインストールされていません")


if __name__ == "__main__":
    test_romkan()
    test_romkan_advanced()
    test_jaconv()
    test_jaconv_advanced()
    test_combined_approach()

    print("\n" + "=" * 80)
    print("romkan & jaconv テスト完了")
    print("=" * 80)
