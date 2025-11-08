#!/usr/bin/env python3
"""
pykakasi を使用した日本語からローマ字への変換テスト
"""
import pykakasi
import time


def test_pykakasi():
    """pykakasiの基本的な使用例とテスト"""

    # pykakasiの初期化
    kks = pykakasi.kakasi()

    # テストケース
    test_cases = [
        "日本語",
        "東京タワー",
        "こんにちは世界",
        "私の名前は太郎です",
        "お茶の水",
        "漢字とひらがなとカタカナが混ざった文章",
        "日本国憲法第九条",
        "富士山は美しい",
        "ローマ字変換",
        "株式会社アントレプレナー",
    ]

    print("=" * 80)
    print("pykakasi テスト")
    print("=" * 80)

    results = []

    for text in test_cases:
        start_time = time.time()
        result = kks.convert(text)
        elapsed_time = time.time() - start_time

        # 結果の整形
        romaji = ''.join([item['hepburn'] for item in result])
        hiragana = ''.join([item['hira'] for item in result])

        print(f"\n入力: {text}")
        print(f"ローマ字: {romaji}")
        print(f"ひらがな: {hiragana}")
        print(f"処理時間: {elapsed_time*1000:.2f}ms")
        print(f"詳細: {result}")

        results.append({
            'input': text,
            'romaji': romaji,
            'hiragana': hiragana,
            'time': elapsed_time,
            'details': result
        })

    return results


def test_pykakasi_advanced():
    """pykakasiの高度な機能のテスト"""

    print("\n" + "=" * 80)
    print("pykakasi 高度な機能テスト")
    print("=" * 80)

    kks = pykakasi.kakasi()

    # 長文テスト
    long_text = """
    吾輩は猫である。名前はまだ無い。
    どこで生れたかとんと見当がつかぬ。
    何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
    """

    print(f"\n長文テスト:")
    print(f"入力: {long_text.strip()}")

    start_time = time.time()
    result = kks.convert(long_text.strip())
    elapsed_time = time.time() - start_time

    romaji = ''.join([item['hepburn'] for item in result])
    print(f"ローマ字: {romaji}")
    print(f"処理時間: {elapsed_time*1000:.2f}ms")

    # 記号や数字を含むテスト
    special_cases = [
        "123番地",
        "メールアドレス: test@example.com",
        "価格：1,000円",
        "2024年1月1日",
    ]

    print(f"\n特殊ケーステスト:")
    for text in special_cases:
        result = kks.convert(text)
        romaji = ''.join([item['hepburn'] for item in result])
        print(f"  {text} → {romaji}")


if __name__ == "__main__":
    results = test_pykakasi()
    test_pykakasi_advanced()

    print("\n" + "=" * 80)
    print("pykakasi テスト完了")
    print("=" * 80)
