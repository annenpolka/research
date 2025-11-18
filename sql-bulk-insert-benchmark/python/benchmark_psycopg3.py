"""
psycopg3 を使用したPostgreSQLベンチマーク
"""
import os
import io
import psycopg
from data_generator import DataGenerator
from benchmark_utils import BenchmarkRunner


# 接続設定
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'benchmark'),
    'password': os.getenv('POSTGRES_PASSWORD', 'benchmark'),
    'dbname': os.getenv('POSTGRES_DB', 'benchmark')
}


def get_connection():
    """PostgreSQL接続を取得"""
    conn_string = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} user={DB_CONFIG['user']} password={DB_CONFIG['password']} dbname={DB_CONFIG['dbname']}"
    return psycopg.connect(conn_string)


def cleanup_table(table_name: str = 'simple_records'):
    """テーブルをクリーンアップ"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            conn.commit()


# ========================================
# Benchmark 1: executemany (psycopg3)
# ========================================
def bench_executemany(record_count: int):
    """psycopg3 executemany（内部でpipeline使用）"""
    cleanup_table()

    with get_connection() as conn:
        with conn.cursor() as cur:
            records = DataGenerator.generate_simple_tuples(record_count)
            sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

            cur.executemany(sql, records)
            conn.commit()


# ========================================
# Benchmark 2: Pipeline mode
# ========================================
def bench_pipeline(record_count: int):
    """Pipeline mode を使用した挿入"""
    cleanup_table()

    with get_connection() as conn:
        records = DataGenerator.generate_simple_tuples(record_count)
        sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

        with conn.pipeline():
            with conn.cursor() as cur:
                for record in records:
                    cur.execute(sql, record)
        conn.commit()


# ========================================
# Benchmark 3: COPY FROM (psycopg3)
# ========================================
def bench_copy(record_count: int):
    """COPY を使用した挿入"""
    cleanup_table()

    with get_connection() as conn:
        records = DataGenerator.generate_simple_records(record_count)

        # バイナリCOPY用のデータを準備
        with conn.cursor() as cur:
            with cur.copy("COPY simple_records (name, email, age, score) FROM STDIN") as copy:
                for r in records:
                    copy.write_row((r['name'], r['email'], r['age'], r['score']))
        conn.commit()


# ========================================
# Benchmark 4: COPY with CSV
# ========================================
def bench_copy_csv(record_count: int):
    """COPY (CSV形式) を使用した挿入"""
    cleanup_table()

    with get_connection() as conn:
        records = DataGenerator.generate_simple_records(record_count)
        csv_data = io.StringIO()
        for r in records:
            csv_data.write(f"{r['name']},{r['email']},{r['age']},{r['score']}\n")
        csv_data.seek(0)

        with conn.cursor() as cur:
            with cur.copy("COPY simple_records (name, email, age, score) FROM STDIN WITH CSV") as copy:
                while True:
                    data = csv_data.read(8192)
                    if not data:
                        break
                    copy.write(data)
        conn.commit()


# ========================================
# Benchmark 5: execute_batch equivalent
# ========================================
def bench_execute_many_batched(record_count: int, batch_size: int = 1000):
    """executemany with batching"""
    cleanup_table()

    with get_connection() as conn:
        with conn.cursor() as cur:
            records = DataGenerator.generate_simple_tuples(record_count)
            sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

            # バッチ処理
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                cur.executemany(sql, batch)
            conn.commit()


def main():
    """メインベンチマーク実行"""
    runner = BenchmarkRunner(output_file='/results/python_psycopg3_results.json')

    test_sizes = [
        100_000,
        1_000_000,
        # 10_000_000,
    ]

    for size in test_sizes:
        print(f"\n{'#'*60}")
        print(f"# Testing with {size:,} records")
        print(f"{'#'*60}")

        runner.run_benchmark(
            f"psycopg3_executemany_{size}",
            bench_executemany,
            size
        )

        # Pipeline は遅いので小規模のみ
        if size <= 100_000:
            runner.run_benchmark(
                f"psycopg3_pipeline_{size}",
                bench_pipeline,
                size
            )

        runner.run_benchmark(
            f"psycopg3_copy_{size}",
            bench_copy,
            size
        )

        runner.run_benchmark(
            f"psycopg3_copy_csv_{size}",
            bench_copy_csv,
            size
        )

        runner.run_benchmark(
            f"psycopg3_executemany_batched_{size}",
            bench_execute_many_batched,
            size
        )

    runner.save_results()
    runner.print_summary()


if __name__ == '__main__':
    print("PostgreSQL Bulk Insert Benchmark - psycopg3")
    print("=" * 60)
    main()
