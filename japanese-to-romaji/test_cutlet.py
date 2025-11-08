#!/usr/bin/env python3
"""
cutlet を使用した日本語からローマ字への変換テスト
cutletはMeCabベースで、より正確な形態素解析を行う
"""
import cutlet
import time


def test_cutlet():
    """cutletの基本的な使用例とテスト"""

    # cutletの初期化（デフォルトはヘボン式）
    katsu = cutlet.Cutlet()

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
    print("cutlet テスト (Hepburn式)")
    print("=" * 80)

    results = []

    for text in test_cases:
        start_time = time.time()
        romaji = katsu.romaji(text)
        elapsed_time = time.time() - start_time

        print(f"\n入力: {text}")
        print(f"ローマ字: {romaji}")
        print(f"処理時間: {elapsed_time*1000:.2f}ms")

        results.append({
            'input': text,
            'romaji': romaji,
            'time': elapsed_time
        })

    return results


def test_cutlet_systems():
    """cutletの異なるローマ字化システムのテスト"""

    print("\n" + "=" * 80)
    print("cutlet ローマ字化システムの比較")
    print("=" * 80)

    test_text = "日本語の文章をローマ字に変換する"

    systems = ['hepburn', 'kunrei', 'nihon']

    for system in systems:
        katsu = cutlet.Cutlet(system)
        romaji = katsu.romaji(test_text)
        print(f"\n{system.upper()}式: {romaji}")


def test_cutlet_advanced():
    """cutletの高度な機能のテスト"""

    print("\n" + "=" * 80)
    print("cutlet 高度な機能テスト")
    print("=" * 80)

    # use_foreign_spelling: 外来語を元の綴りで表示
    katsu_foreign = cutlet.Cutlet(use_foreign_spelling=True)
    katsu_normal = cutlet.Cutlet(use_foreign_spelling=False)

    foreign_words = [
        "コーヒー",
        "カフェ",
        "レストラン",
        "ハンバーガー",
        "カツレツ",
    ]

    print("\n外来語スペリングの比較:")
    for word in foreign_words:
        normal = katsu_normal.romaji(word)
        foreign = katsu_foreign.romaji(word)
        print(f"  {word}:")
        print(f"    通常: {normal}")
        print(f"    外来語: {foreign}")

    # 長文テスト
    katsu = cutlet.Cutlet()
    long_text = """
    吾輩は猫である。名前はまだ無い。
    どこで生れたかとんと見当がつかぬ。
    何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
    """

    print(f"\n長文テスト:")
    print(f"入力: {long_text.strip()}")

    start_time = time.time()
    romaji = katsu.romaji(long_text.strip())
    elapsed_time = time.time() - start_time

    print(f"ローマ字: {romaji}")
    print(f"処理時間: {elapsed_time*1000:.2f}ms")

    # 特殊ケース
    special_cases = [
        "123番地",
        "メールアドレス: test@example.com",
        "価格：1,000円",
        "2024年1月1日",
    ]

    print(f"\n特殊ケーステスト:")
    for text in special_cases:
        romaji = katsu.romaji(text)
        print(f"  {text} → {romaji}")


def test_cutlet_options():
    """cutletの各種オプションのテスト"""

    print("\n" + "=" * 80)
    print("cutlet オプション比較")
    print("=" * 80)

    test_text = "東京タワーは高い"

    # ensure_ascii: ASCIIのみ出力
    print("\nensure_ascii オプション:")
    katsu_ascii = cutlet.Cutlet(ensure_ascii=True)
    katsu_normal = cutlet.Cutlet(ensure_ascii=False)
    print(f"  ASCII強制: {katsu_ascii.romaji(test_text)}")
    print(f"  通常: {katsu_normal.romaji(test_text)}")


if __name__ == "__main__":
    results = test_cutlet()
    test_cutlet_systems()
    test_cutlet_advanced()
    test_cutlet_options()

    print("\n" + "=" * 80)
    print("cutlet テスト完了")
    print("=" * 80)
