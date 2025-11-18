"""
ベンチマークユーティリティ
"""
import time
import json
import psutil
import os
from typing import Dict, Any, Callable
from datetime import datetime
from contextlib import contextmanager


class BenchmarkTimer:
    """ベンチマーク計測用タイマー"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.start_memory = None
        self.end_memory = None
        self.memory_used = None

    def __enter__(self):
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.end_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.duration = self.end_time - self.start_time
        self.memory_used = self.end_memory - self.start_memory

    def get_results(self, record_count: int) -> Dict[str, Any]:
        """結果を辞書形式で取得"""
        return {
            'name': self.name,
            'duration_seconds': round(self.duration, 3),
            'records_per_second': round(record_count / self.duration, 2) if self.duration > 0 else 0,
            'memory_used_mb': round(self.memory_used, 2),
            'record_count': record_count,
            'timestamp': datetime.now().isoformat()
        }


class BenchmarkRunner:
    """ベンチマーク実行管理クラス"""

    def __init__(self, output_file: str = '/results/benchmark_results.json'):
        self.output_file = output_file
        self.results = []

    def run_benchmark(self, name: str, func: Callable, record_count: int, **kwargs):
        """
        ベンチマークを実行

        Args:
            name: ベンチマーク名
            func: 実行する関数
            record_count: レコード数
            **kwargs: 関数に渡す追加引数
        """
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"Records: {record_count:,}")
        print(f"{'='*60}")

        with BenchmarkTimer(name) as timer:
            try:
                func(record_count, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                print(f"ERROR: {error}")

        result = timer.get_results(record_count)
        result['success'] = success
        result['error'] = error

        if success:
            print(f"✓ Completed in {result['duration_seconds']}s")
            print(f"  Throughput: {result['records_per_second']:,.2f} records/sec")
            print(f"  Memory used: {result['memory_used_mb']:.2f} MB")
        else:
            print(f"✗ Failed: {error}")

        self.results.append(result)
        return result

    def save_results(self):
        """結果をJSONファイルに保存"""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        # 既存の結果を読み込み
        existing_results = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r') as f:
                    existing_results = json.load(f)
            except:
                pass

        # 新しい結果を追加
        existing_results.extend(self.results)

        # 保存
        with open(self.output_file, 'w') as f:
            json.dump(existing_results, f, indent=2)

        print(f"\n✓ Results saved to {self.output_file}")

    def print_summary(self):
        """結果のサマリーを表示"""
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}")

        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]

        print(f"\nTotal benchmarks: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        if successful:
            print(f"\n{'Method':<40} {'Records/sec':>15}")
            print('-' * 60)
            sorted_results = sorted(successful, key=lambda x: x['records_per_second'], reverse=True)
            for r in sorted_results:
                print(f"{r['name']:<40} {r['records_per_second']:>15,.2f}")


@contextmanager
def database_connection(conn):
    """データベース接続のコンテキストマネージャー"""
    try:
        yield conn
    finally:
        if hasattr(conn, 'rollback'):
            conn.rollback()
        if hasattr(conn, 'close'):
            conn.close()
