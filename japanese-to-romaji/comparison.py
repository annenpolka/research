#!/usr/bin/env python3
"""
日本語→ローマ字変換ライブラリの包括的な比較

比較対象:
- pykakasi: 自己完結型、独自辞書
- cutlet: MeCabベース、高精度
- romkan: かな→ローマ字のみ（漢字非対応）
- jaconv: 文字変換（漢字→ローマ字には非対応）
"""

import time
import statistics
from typing import Dict, List, Tuple
import pykakasi
import cutlet
import romkan
import jaconv


class RomajiConverter:
    """各ライブラリのラッパークラス"""

    def __init__(self):
        self.pykakasi_converter = pykakasi.kakasi()
        self.cutlet_converter = cutlet.Cutlet()
        self.cutlet_foreign = cutlet.Cutlet(use_foreign_spelling=True)

    def convert_pykakasi(self, text: str) -> Tuple[str, float]:
        """pykakasiを使用した変換"""
        start = time.time()
        result = self.pykakasi_converter.convert(text)
        romaji = ''.join([item['hepburn'] for item in result])
        elapsed = time.time() - start
        return romaji, elapsed

    def convert_cutlet(self, text: str) -> Tuple[str, float]:
        """cutletを使用した変換"""
        start = time.time()
        romaji = self.cutlet_converter.romaji(text)
        elapsed = time.time() - start
        return romaji, elapsed

    def convert_cutlet_foreign(self, text: str) -> Tuple[str, float]:
        """cutlet（外来語スペリング使用）を使用した変換"""
        start = time.time()
        romaji = self.cutlet_foreign.romaji(text)
        elapsed = time.time() - start
        return romaji, elapsed

    def convert_romkan(self, text: str) -> Tuple[str, float]:
        """romkanを使用した変換（かなのみ）"""
        start = time.time()
        romaji = romkan.to_roma(text)
        elapsed = time.time() - start
        return romaji, elapsed


def print_comparison_table(test_cases: List[str], converter: RomajiConverter):
    """比較テーブルを出力"""

    print("\n" + "=" * 120)
    print("変換結果の比較")
    print("=" * 120)

    # ヘッダー
    print(f"{'入力':<25} | {'pykakasi':<30} | {'cutlet':<30} | {'romkan':<30}")
    print("-" * 120)

    for text in test_cases:
        # 各ライブラリで変換
        pykakasi_result, _ = converter.convert_pykakasi(text)
        cutlet_result, _ = converter.convert_cutlet(text)
        romkan_result, _ = converter.convert_romkan(text)

        # 長い結果は切り詰める
        pykakasi_display = (pykakasi_result[:27] + '...') if len(pykakasi_result) > 30 else pykakasi_result
        cutlet_display = (cutlet_result[:27] + '...') if len(cutlet_result) > 30 else cutlet_result
        romkan_display = (romkan_result[:27] + '...') if len(romkan_result) > 30 else romkan_result

        print(f"{text:<25} | {pykakasi_display:<30} | {cutlet_display:<30} | {romkan_display:<30}")


def benchmark_performance(test_cases: List[str], converter: RomajiConverter, iterations: int = 100):
    """パフォーマンスベンチマーク"""

    print("\n" + "=" * 80)
    print(f"パフォーマンスベンチマーク（各テストケース×{iterations}回）")
    print("=" * 80)

    results = {
        'pykakasi': [],
        'cutlet': [],
        'cutlet_foreign': [],
        'romkan': []
    }

    for text in test_cases:
        # pykakasi
        times = []
        for _ in range(iterations):
            _, elapsed = converter.convert_pykakasi(text)
            times.append(elapsed * 1000)  # ミリ秒に変換
        results['pykakasi'].extend(times)

        # cutlet
        times = []
        for _ in range(iterations):
            _, elapsed = converter.convert_cutlet(text)
            times.append(elapsed * 1000)
        results['cutlet'].extend(times)

        # cutlet (foreign)
        times = []
        for _ in range(iterations):
            _, elapsed = converter.convert_cutlet_foreign(text)
            times.append(elapsed * 1000)
        results['cutlet_foreign'].extend(times)

        # romkan
        times = []
        for _ in range(iterations):
            _, elapsed = converter.convert_romkan(text)
            times.append(elapsed * 1000)
        results['romkan'].extend(times)

    # 統計情報を出力
    print(f"\n{'ライブラリ':<20} | {'平均':<12} | {'中央値':<12} | {'最小':<12} | {'最大':<12}")
    print("-" * 80)

    for lib_name, times in results.items():
        avg = statistics.mean(times)
        median = statistics.median(times)
        min_time = min(times)
        max_time = max(times)

        print(f"{lib_name:<20} | {avg:>10.2f}ms | {median:>10.2f}ms | {min_time:>10.2f}ms | {max_time:>10.2f}ms")


def analyze_features():
    """各ライブラリの機能比較"""

    print("\n" + "=" * 80)
    print("機能比較")
    print("=" * 80)

    features = {
        'ライブラリ': ['pykakasi', 'cutlet', 'romkan', 'jaconv'],
        '漢字対応': ['○', '○', '×', '×'],
        'かな対応': ['○', '○', '○', '○'],
        'ローマ字システム': ['Hepburn/Kunrei/Passport', 'Hepburn/Kunrei/Nihon', 'Hepburn', '-'],
        '外来語スペリング': ['×', '○', '×', '×'],
        '逆変換(ローマ字→かな)': ['×', '×', '○', '×'],
        '形態素解析': ['独自辞書', 'MeCab', '×', '×'],
        '依存関係': ['なし', 'MeCab辞書必要', 'なし', 'なし'],
        'インストールの容易さ': ['簡単', '中程度', '簡単', '簡単'],
    }

    # ヘッダー
    max_width = max(len(k) for k in features.keys())
    print(f"{'項目':<{max_width}} | {'pykakasi':<15} | {'cutlet':<20} | {'romkan':<15} | {'jaconv':<15}")
    print("-" * 100)

    # 各行を出力
    feature_keys = list(features.keys())
    for i in range(len(features[feature_keys[0]])):
        row = []
        for key in feature_keys:
            if i < len(features[key]):
                row.append(features[key][i])

        if len(row) == 4:
            print(f"{feature_keys[0]:<{max_width}} | {row[0]:<15} | {row[1]:<20} | {row[2]:<15} | {row[3]:<15}")


def test_accuracy():
    """精度テスト - 特殊なケースでの比較"""

    print("\n" + "=" * 80)
    print("精度テスト - 特殊なケース")
    print("=" * 80)

    converter = RomajiConverter()

    special_cases = [
        ("促音", "きっぷ"),
        ("長音", "とうきょう"),
        ("拗音", "きょう"),
        ("撥音", "さんぽ"),
        ("助詞「は」", "私は学生です"),
        ("助詞「へ」", "学校へ行く"),
        ("助詞「を」", "本を読む"),
        ("外来語", "コーヒー"),
        ("混在", "漢字とカタカナとひらがな"),
    ]

    print(f"\n{'ケース':<15} | {'入力':<20} | {'pykakasi':<25} | {'cutlet':<25}")
    print("-" * 90)

    for case_name, text in special_cases:
        pykakasi_result, _ = converter.convert_pykakasi(text)
        cutlet_result, _ = converter.convert_cutlet(text)

        print(f"{case_name:<15} | {text:<20} | {pykakasi_result:<25} | {cutlet_result:<25}")


def test_edge_cases():
    """エッジケースのテスト"""

    print("\n" + "=" * 80)
    print("エッジケーステスト")
    print("=" * 80)

    converter = RomajiConverter()

    edge_cases = [
        ("空文字", ""),
        ("スペースのみ", "   "),
        ("数字のみ", "12345"),
        ("英字のみ", "ABC"),
        ("記号のみ", "!@#$%"),
        ("混合1", "ABC123あいう"),
        ("混合2", "test@example.com"),
        ("絵文字", "こんにちは😀"),
    ]

    print(f"\n{'ケース':<15} | {'入力':<25} | {'pykakasi':<30} | {'cutlet':<30}")
    print("-" * 105)

    for case_name, text in edge_cases:
        try:
            pykakasi_result, _ = converter.convert_pykakasi(text)
        except Exception as e:
            pykakasi_result = f"ERROR: {str(e)[:20]}"

        try:
            cutlet_result, _ = converter.convert_cutlet(text)
        except Exception as e:
            cutlet_result = f"ERROR: {str(e)[:20]}"

        display_text = (text[:22] + '...') if len(text) > 25 else text
        print(f"{case_name:<15} | {display_text:<25} | {pykakasi_result:<30} | {cutlet_result:<30}")


def main():
    """メイン処理"""

    print("=" * 80)
    print("日本語→ローマ字変換ライブラリの包括的な比較")
    print("=" * 80)

    # テストケース
    test_cases = [
        "日本語",
        "東京タワー",
        "こんにちは世界",
        "私の名前は太郎です",
        "お茶の水",
        "富士山は美しい",
        "株式会社",
    ]

    # コンバーターの初期化
    converter = RomajiConverter()

    # 1. 変換結果の比較
    print_comparison_table(test_cases, converter)

    # 2. 機能比較
    analyze_features()

    # 3. 精度テスト
    test_accuracy()

    # 4. エッジケーステスト
    test_edge_cases()

    # 5. パフォーマンスベンチマーク
    benchmark_performance(test_cases, converter, iterations=100)

    # 6. 推奨事項
    print("\n" + "=" * 80)
    print("推奨事項")
    print("=" * 80)
    print("""
1. **pykakasi**:
   - 推奨用途: 一般的な用途、簡単なセットアップが必要な場合
   - 利点: インストールが簡単、依存関係なし、複数のローマ字システム対応
   - 欠点: 形態素解析の精度がcutletより低い可能性

2. **cutlet**:
   - 推奨用途: 高精度が必要な場合、外来語を正確に処理したい場合
   - 利点: MeCabベースで高精度、外来語スペリング対応、複数システム対応
   - 欠点: MeCab辞書のセットアップが必要、やや複雑

3. **romkan**:
   - 推奨用途: かな→ローマ字のみの変換、逆変換も必要な場合
   - 利点: 軽量、ローマ字→かなの逆変換が可能
   - 欠点: 漢字非対応

4. **jaconv**:
   - 推奨用途: 文字種変換（ひらがな⇔カタカナ、全角⇔半角）
   - 利点: 文字変換に特化、高速
   - 欠点: ローマ字変換機能なし

**総合評価**:
- シンプルさ重視: pykakasi
- 精度重視: cutlet
- かな変換のみ: romkan
- 前処理用: jaconv
    """)


if __name__ == "__main__":
    main()
