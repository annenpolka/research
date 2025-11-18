#!/usr/bin/env python3
"""
ベンチマーク結果を分析して表示するスクリプト
"""
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any


class BenchmarkAnalyzer:
    """ベンチマーク結果の分析クラス"""

    def __init__(self, results_dir: str = 'results'):
        self.results_dir = Path(results_dir)
        self.all_results = []
        self.load_all_results()

    def load_all_results(self):
        """すべての結果ファイルを読み込む"""
        if not self.results_dir.exists():
            print(f"Results directory '{self.results_dir}' does not exist")
            return

        for json_file in self.results_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    results = json.load(f)
                    if isinstance(results, list):
                        self.all_results.extend(results)
                    else:
                        self.all_results.append(results)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

    def get_successful_results(self) -> List[Dict[str, Any]]:
        """成功した結果のみを取得"""
        return [r for r in self.all_results if r.get('success', False)]

    def group_by_language(self) -> Dict[str, List[Dict[str, Any]]]:
        """言語別にグループ化"""
        grouped = defaultdict(list)
        for result in self.get_successful_results():
            name = result['name']
            if 'psycopg' in name or 'sqlalchemy' in name or 'python' in name or 'pymysql' in name or 'mysqldb' in name or 'load_data' in name:
                grouped['Python'].append(result)
            elif 'activerecord' in name or 'pg_copy' in name or 'mysql' in name.lower():
                # MySQLの場合はさらに判定
                if 'mysql' in name and 'python' not in name:
                    grouped['Ruby'].append(result)
                elif 'activerecord' in name or 'pg_copy' in name:
                    grouped['Ruby'].append(result)
                else:
                    grouped['Python'].append(result)
        return grouped

    def group_by_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """データベース別にグループ化"""
        grouped = defaultdict(list)
        for result in self.get_successful_results():
            name = result['name'].lower()
            if 'mysql' in name:
                grouped['MySQL'].append(result)
            else:
                grouped['PostgreSQL'].append(result)
        return grouped

    def get_top_performers(self, n: int = 10) -> List[Dict[str, Any]]:
        """トップN件のパフォーマンスを取得"""
        successful = self.get_successful_results()
        sorted_results = sorted(successful, key=lambda x: x['records_per_second'], reverse=True)
        return sorted_results[:n]

    def get_bottom_performers(self, n: int = 10) -> List[Dict[str, Any]]:
        """ワーストN件のパフォーマンスを取得"""
        successful = self.get_successful_results()
        sorted_results = sorted(successful, key=lambda x: x['records_per_second'])
        return sorted_results[:n]

    def compare_same_record_count(self, record_count: int) -> List[Dict[str, Any]]:
        """同じレコード数の結果を比較"""
        return [r for r in self.get_successful_results() if r['record_count'] == record_count]

    def print_summary(self):
        """サマリーを表示"""
        successful = self.get_successful_results()
        failed = [r for r in self.all_results if not r.get('success', False)]

        print("="*80)
        print("BENCHMARK ANALYSIS SUMMARY")
        print("="*80)
        print()
        print(f"Total benchmarks: {len(self.all_results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print()

        if failed:
            print("Failed benchmarks:")
            for r in failed:
                print(f"  - {r['name']}: {r.get('error', 'Unknown error')}")
            print()

    def print_top_performers(self, n: int = 10):
        """トップパフォーマーを表示"""
        top = self.get_top_performers(n)

        print("="*80)
        print(f"TOP {n} FASTEST METHODS")
        print("="*80)
        print()
        print(f"{'Rank':<6} {'Method':<50} {'Records/sec':>15} {'Records':>12}")
        print("-"*80)

        for i, result in enumerate(top, 1):
            name = result['name'][:50]
            rps = f"{result['records_per_second']:,.0f}"
            records = f"{result['record_count']:,}"
            print(f"{i:<6} {name:<50} {rps:>15} {records:>12}")
        print()

    def print_language_comparison(self):
        """言語別比較を表示"""
        grouped = self.group_by_language()

        print("="*80)
        print("LANGUAGE COMPARISON")
        print("="*80)
        print()

        for lang, results in sorted(grouped.items()):
            avg_rps = sum(r['records_per_second'] for r in results) / len(results)
            max_rps = max(r['records_per_second'] for r in results)
            min_rps = min(r['records_per_second'] for r in results)

            print(f"{lang}:")
            print(f"  Benchmarks: {len(results)}")
            print(f"  Average throughput: {avg_rps:,.0f} records/sec")
            print(f"  Max throughput: {max_rps:,.0f} records/sec")
            print(f"  Min throughput: {min_rps:,.0f} records/sec")
            print()

    def print_database_comparison(self):
        """データベース別比較を表示"""
        grouped = self.group_by_database()

        print("="*80)
        print("DATABASE COMPARISON")
        print("="*80)
        print()

        for db, results in sorted(grouped.items()):
            avg_rps = sum(r['records_per_second'] for r in results) / len(results)
            max_rps = max(r['records_per_second'] for r in results)

            print(f"{db}:")
            print(f"  Benchmarks: {len(results)}")
            print(f"  Average throughput: {avg_rps:,.0f} records/sec")
            print(f"  Best method: {max(results, key=lambda x: x['records_per_second'])['name']}")
            print(f"  Best throughput: {max_rps:,.0f} records/sec")
            print()

    def print_record_count_comparison(self):
        """レコード数別の比較"""
        by_count = defaultdict(list)
        for result in self.get_successful_results():
            by_count[result['record_count']].append(result)

        print("="*80)
        print("COMPARISON BY RECORD COUNT")
        print("="*80)
        print()

        for count in sorted(by_count.keys()):
            results = by_count[count]
            best = max(results, key=lambda x: x['records_per_second'])

            print(f"{count:,} records:")
            print(f"  Benchmarks run: {len(results)}")
            print(f"  Best method: {best['name']}")
            print(f"  Best throughput: {best['records_per_second']:,.0f} records/sec")
            print(f"  Time taken: {best['duration_seconds']:.2f}s")
            print()

    def export_markdown_report(self, output_file: str = 'BENCHMARK_RESULTS.md'):
        """Markdown形式のレポートを出力"""
        with open(output_file, 'w') as f:
            f.write("# SQL Bulk Insert Benchmark Results\n\n")

            # サマリー
            successful = self.get_successful_results()
            f.write("## Summary\n\n")
            f.write(f"- Total benchmarks: {len(self.all_results)}\n")
            f.write(f"- Successful: {len(successful)}\n")
            f.write(f"- Failed: {len(self.all_results) - len(successful)}\n\n")

            # トップパフォーマー
            f.write("## Top 20 Fastest Methods\n\n")
            f.write("| Rank | Method | Records/sec | Record Count | Duration (s) |\n")
            f.write("|------|--------|-------------|--------------|---------------|\n")

            for i, result in enumerate(self.get_top_performers(20), 1):
                f.write(f"| {i} | {result['name']} | {result['records_per_second']:,.0f} | "
                       f"{result['record_count']:,} | {result['duration_seconds']:.2f} |\n")

            f.write("\n")

            # 言語別比較
            f.write("## Language Comparison\n\n")
            grouped = self.group_by_language()
            for lang, results in sorted(grouped.items()):
                avg_rps = sum(r['records_per_second'] for r in results) / len(results)
                f.write(f"### {lang}\n\n")
                f.write(f"- Benchmarks: {len(results)}\n")
                f.write(f"- Average throughput: {avg_rps:,.0f} records/sec\n")
                f.write(f"- Max throughput: {max(r['records_per_second'] for r in results):,.0f} records/sec\n\n")

            # データベース別比較
            f.write("## Database Comparison\n\n")
            db_grouped = self.group_by_database()
            for db, results in sorted(db_grouped.items()):
                best = max(results, key=lambda x: x['records_per_second'])
                f.write(f"### {db}\n\n")
                f.write(f"- Best method: `{best['name']}`\n")
                f.write(f"- Best throughput: {best['records_per_second']:,.0f} records/sec\n\n")

        print(f"✓ Markdown report saved to {output_file}")


def main():
    """メイン実行"""
    analyzer = BenchmarkAnalyzer('results')

    if not analyzer.all_results:
        print("No benchmark results found. Please run benchmarks first.")
        return

    # 各種分析を表示
    analyzer.print_summary()
    analyzer.print_top_performers(20)
    analyzer.print_language_comparison()
    analyzer.print_database_comparison()
    analyzer.print_record_count_comparison()

    # Markdownレポートを出力
    analyzer.export_markdown_report('sql-bulk-insert-benchmark/BENCHMARK_RESULTS.md')


if __name__ == '__main__':
    main()
