#!/usr/bin/env python3
"""
日本語→ローマ字変換ライブラリの詳細なベンチマーク

様々な規模のテキストで性能を測定
"""

import time
import statistics
from typing import List, Dict, Tuple
import pykakasi
import cutlet
import romkan


class BenchmarkRunner:
    """ベンチマークテスト実行クラス"""

    def __init__(self):
        self.pykakasi_converter = pykakasi.kakasi()
        self.cutlet_converter = cutlet.Cutlet()

    def generate_test_texts(self) -> Dict[str, str]:
        """様々な規模のテストテキストを生成"""

        short_text = "日本語"

        medium_text = """
        吾輩は猫である。名前はまだ無い。どこで生れたかとんと見当がつかぬ。
        何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
        """

        long_text = """
        日本国憲法は、日本国の最高法規である。1946年11月3日に公布され、
        1947年5月3日に施行された。国民主権、基本的人権の尊重、平和主義を
        基本原理とする。第二次世界大戦後の連合国軍占領下において制定され、
        現行憲法としては世界で最も古い憲法の一つである。

        日本国憲法は103条からなり、前文、第1章から第11章で構成されている。
        前文では、国民主権の原理、平和主義、基本的人権の尊重といった
        日本国憲法の基本原理が示されている。

        第1章は「天皇」について規定しており、天皇は日本国の象徴であり
        日本国民統合の象徴であると定められている。第2章は「戦争の放棄」を
        規定した第9条のみで構成され、いわゆる平和主義を定めている。
        """ * 3

        very_long_text = long_text * 5

        return {
            'short': short_text.strip(),
            'medium': medium_text.strip(),
            'long': long_text.strip(),
            'very_long': very_long_text.strip()
        }

    def benchmark_pykakasi(self, text: str, iterations: int = 10) -> List[float]:
        """pykakasiのベンチマーク"""
        times = []
        for _ in range(iterations):
            start = time.time()
            result = self.pykakasi_converter.convert(text)
            _ = ''.join([item['hepburn'] for item in result])
            elapsed = time.time() - start
            times.append(elapsed * 1000)  # ミリ秒
        return times

    def benchmark_cutlet(self, text: str, iterations: int = 10) -> List[float]:
        """cutletのベンチマーク"""
        times = []
        for _ in range(iterations):
            start = time.time()
            _ = self.cutlet_converter.romaji(text)
            elapsed = time.time() - start
            times.append(elapsed * 1000)  # ミリ秒
        return times

    def run_benchmark(self):
        """ベンチマークの実行"""

        print("=" * 80)
        print("詳細なベンチマークテスト")
        print("=" * 80)

        test_texts = self.generate_test_texts()

        for size_name, text in test_texts.items():
            print(f"\n{'=' * 80}")
            print(f"テキストサイズ: {size_name.upper()}")
            print(f"文字数: {len(text)}文字")
            print(f"{'=' * 80}")

            # 反復回数を調整（長いテキストほど少なく）
            iterations_map = {
                'short': 1000,
                'medium': 100,
                'long': 50,
                'very_long': 10
            }
            iterations = iterations_map[size_name]

            # pykakasi
            print(f"\npykakasi ({iterations}回):")
            pykakasi_times = self.benchmark_pykakasi(text, iterations)
            self.print_stats(pykakasi_times)

            # cutlet
            print(f"\ncutlet ({iterations}回):")
            cutlet_times = self.benchmark_cutlet(text, iterations)
            self.print_stats(cutlet_times)

            # 比較
            pykakasi_avg = statistics.mean(pykakasi_times)
            cutlet_avg = statistics.mean(cutlet_times)
            ratio = cutlet_avg / pykakasi_avg if pykakasi_avg > 0 else 0

            print(f"\n比較:")
            print(f"  pykakasi平均: {pykakasi_avg:.2f}ms")
            print(f"  cutlet平均: {cutlet_avg:.2f}ms")
            print(f"  cutlet/pykakasi比: {ratio:.2f}x")

    def print_stats(self, times: List[float]):
        """統計情報を出力"""
        avg = statistics.mean(times)
        median = statistics.median(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        print(f"  平均: {avg:.2f}ms")
        print(f"  中央値: {median:.2f}ms")
        print(f"  標準偏差: {stdev:.2f}ms")
        print(f"  最小: {min_time:.2f}ms")
        print(f"  最大: {max_time:.2f}ms")


def benchmark_throughput():
    """スループット測定"""

    print("\n" + "=" * 80)
    print("スループット測定")
    print("=" * 80)

    pykakasi_converter = pykakasi.kakasi()
    cutlet_converter = cutlet.Cutlet()

    test_text = "日本語の文章をローマ字に変換する。"
    duration = 1.0  # 1秒間

    # pykakasi
    print(f"\npykakasi ({duration}秒間):")
    start = time.time()
    count = 0
    while time.time() - start < duration:
        result = pykakasi_converter.convert(test_text)
        _ = ''.join([item['hepburn'] for item in result])
        count += 1
    pykakasi_throughput = count / duration

    print(f"  処理回数: {count}回")
    print(f"  スループット: {pykakasi_throughput:.2f}変換/秒")

    # cutlet
    print(f"\ncutlet ({duration}秒間):")
    start = time.time()
    count = 0
    while time.time() - start < duration:
        _ = cutlet_converter.romaji(test_text)
        count += 1
    cutlet_throughput = count / duration

    print(f"  処理回数: {count}回")
    print(f"  スループット: {cutlet_throughput:.2f}変換/秒")

    # 比較
    print(f"\n比較:")
    print(f"  pykakasi: {pykakasi_throughput:.2f}変換/秒")
    print(f"  cutlet: {cutlet_throughput:.2f}変換/秒")
    ratio = pykakasi_throughput / cutlet_throughput if cutlet_throughput > 0 else 0
    print(f"  pykakasi/cutlet比: {ratio:.2f}x")


def benchmark_memory():
    """メモリ使用量の簡易測定"""

    print("\n" + "=" * 80)
    print("初期化コスト測定")
    print("=" * 80)

    # pykakasi初期化
    print("\npykakasi初期化:")
    start = time.time()
    kks = pykakasi.kakasi()
    elapsed = time.time() - start
    print(f"  初期化時間: {elapsed*1000:.2f}ms")

    # cutlet初期化
    print("\ncutlet初期化:")
    start = time.time()
    katsu = cutlet.Cutlet()
    elapsed = time.time() - start
    print(f"  初期化時間: {elapsed*1000:.2f}ms")


def benchmark_special_cases():
    """特殊ケースでのパフォーマンス測定"""

    print("\n" + "=" * 80)
    print("特殊ケースでのパフォーマンス")
    print("=" * 80)

    pykakasi_converter = pykakasi.kakasi()
    cutlet_converter = cutlet.Cutlet()

    special_cases = {
        '短文（漢字のみ）': '日本語',
        '短文（かなのみ）': 'ひらがな',
        '短文（カタカナのみ）': 'カタカナ',
        '短文（混在）': '日本語とEnglish',
        '中文（複雑）': '私の名前は太郎です。東京に住んでいます。',
        '長文（繰り返し）': '日本語' * 100,
    }

    iterations = 100

    for case_name, text in special_cases.items():
        print(f"\n{case_name} ({len(text)}文字):")

        # pykakasi
        times = []
        for _ in range(iterations):
            start = time.time()
            result = pykakasi_converter.convert(text)
            _ = ''.join([item['hepburn'] for item in result])
            elapsed = time.time() - start
            times.append(elapsed * 1000)
        pykakasi_avg = statistics.mean(times)

        # cutlet
        times = []
        for _ in range(iterations):
            start = time.time()
            _ = cutlet_converter.romaji(text)
            elapsed = time.time() - start
            times.append(elapsed * 1000)
        cutlet_avg = statistics.mean(times)

        print(f"  pykakasi: {pykakasi_avg:.3f}ms")
        print(f"  cutlet: {cutlet_avg:.3f}ms")


def main():
    """メイン処理"""

    print("=" * 80)
    print("日本語→ローマ字変換ライブラリの詳細ベンチマーク")
    print("=" * 80)

    # 1. 基本ベンチマーク
    runner = BenchmarkRunner()
    runner.run_benchmark()

    # 2. スループット測定
    benchmark_throughput()

    # 3. 初期化コスト
    benchmark_memory()

    # 4. 特殊ケース
    benchmark_special_cases()

    print("\n" + "=" * 80)
    print("ベンチマーク完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
