"""
psycopg2 を使用したPostgreSQLベンチマーク
"""
import os
import io
import psycopg2
from psycopg2.extras import execute_values, execute_batch
from data_generator import DataGenerator
from benchmark_utils import BenchmarkRunner


# 接続設定
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'benchmark'),
    'password': os.getenv('POSTGRES_PASSWORD', 'benchmark'),
    'database': os.getenv('POSTGRES_DB', 'benchmark')
}


def get_connection():
    """PostgreSQL接続を取得"""
    return psycopg2.connect(**DB_CONFIG)


def cleanup_table(table_name: str = 'simple_records'):
    """テーブルをクリーンアップ"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 1: executemany (基準・最も遅い)
# ========================================
def bench_executemany(record_count: int):
    """executemany を使用した挿入（非推奨・遅い）"""
    cleanup_table()
    conn = get_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    cur.executemany(sql, records)
    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 2: execute_values (推奨)
# ========================================
def bench_execute_values(record_count: int, page_size: int = 1000):
    """execute_values を使用した高速挿入"""
    cleanup_table()
    conn = get_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES %s"

    execute_values(cur, sql, records, page_size=page_size)
    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 3: execute_batch
# ========================================
def bench_execute_batch(record_count: int, page_size: int = 1000):
    """execute_batch を使用した挿入"""
    cleanup_table()
    conn = get_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    execute_batch(cur, sql, records, page_size=page_size)
    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 4: COPY FROM (最速)
# ========================================
def bench_copy_from(record_count: int):
    """COPY FROM を使用した最速挿入"""
    cleanup_table()
    conn = get_connection()
    cur = conn.cursor()

    # CSV形式のデータを生成
    records = DataGenerator.generate_simple_records(record_count)
    csv_data = io.StringIO()
    for r in records:
        csv_data.write(f"{r['name']}\t{r['email']}\t{r['age']}\t{r['score']}\n")
    csv_data.seek(0)

    # COPY FROM実行
    cur.copy_from(
        csv_data,
        'simple_records',
        columns=('name', 'email', 'age', 'score'),
        sep='\t'
    )

    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 5: COPY FROM with CSV module
# ========================================
def bench_copy_from_csv(record_count: int):
    """COPY FROM をCSVモジュールで使用"""
    import csv

    cleanup_table()
    conn = get_connection()
    cur = conn.cursor()

    # CSVライターを使用してデータを生成
    records = DataGenerator.generate_simple_records(record_count)
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    for r in records:
        writer.writerow([r['name'], r['email'], r['age'], r['score']])
    csv_buffer.seek(0)

    # COPY FROM実行
    cur.copy_expert(
        "COPY simple_records (name, email, age, score) FROM STDIN WITH CSV",
        csv_buffer
    )

    conn.commit()
    cur.close()
    conn.close()


# ========================================
# Benchmark 6: execute_values (異なるpage_size)
# ========================================
def bench_execute_values_small_batch(record_count: int):
    """execute_values (page_size=100)"""
    bench_execute_values(record_count, page_size=100)


def bench_execute_values_large_batch(record_count: int):
    """execute_values (page_size=10000)"""
    bench_execute_values(record_count, page_size=10000)


# ========================================
# Benchmark 7: トランザクション制御なし（危険だが高速）
# ========================================
def bench_execute_values_no_transaction(record_count: int):
    """execute_values (autocommit モード)"""
    cleanup_table()
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES %s"

    execute_values(cur, sql, records, page_size=1000)
    cur.close()
    conn.close()


def main():
    """メインベンチマーク実行"""
    runner = BenchmarkRunner(output_file='/results/python_psycopg2_results.json')

    # テスト規模
    test_sizes = [
        100_000,      # 10万件（ウォームアップ）
        1_000_000,    # 100万件
        # 10_000_000,   # 1000万件（時間がかかる場合はコメントアウト）
    ]

    for size in test_sizes:
        print(f"\n{'#'*60}")
        print(f"# Testing with {size:,} records")
        print(f"{'#'*60}")

        # executemanyは遅すぎるので10万件のみ
        if size <= 100_000:
            runner.run_benchmark(
                f"psycopg2_executemany_{size}",
                bench_executemany,
                size
            )

        runner.run_benchmark(
            f"psycopg2_execute_values_{size}",
            bench_execute_values,
            size
        )

        runner.run_benchmark(
            f"psycopg2_execute_values_batch100_{size}",
            bench_execute_values_small_batch,
            size
        )

        runner.run_benchmark(
            f"psycopg2_execute_values_batch10000_{size}",
            bench_execute_values_large_batch,
            size
        )

        runner.run_benchmark(
            f"psycopg2_execute_batch_{size}",
            bench_execute_batch,
            size
        )

        runner.run_benchmark(
            f"psycopg2_copy_from_{size}",
            bench_copy_from,
            size
        )

        runner.run_benchmark(
            f"psycopg2_copy_from_csv_{size}",
            bench_copy_from_csv,
            size
        )

        runner.run_benchmark(
            f"psycopg2_execute_values_autocommit_{size}",
            bench_execute_values_no_transaction,
            size
        )

    # 結果の保存と表示
    runner.save_results()
    runner.print_summary()


if __name__ == '__main__':
    print("PostgreSQL Bulk Insert Benchmark - psycopg2")
    print("=" * 60)
    main()
