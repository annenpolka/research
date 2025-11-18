"""
MySQL用Pythonベンチマーク
"""
import os
import pymysql
import MySQLdb
from data_generator import DataGenerator
from benchmark_utils import BenchmarkRunner


# 接続設定
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'benchmark'),
    'password': os.getenv('MYSQL_PASSWORD', 'benchmark'),
    'database': os.getenv('MYSQL_DB', 'benchmark')
}


def get_pymysql_connection():
    """PyMySQL接続を取得"""
    return pymysql.connect(**DB_CONFIG)


def get_mysqldb_connection():
    """MySQLdb接続を取得"""
    return MySQLdb.connect(**DB_CONFIG)


def cleanup_table(table_name: str = 'simple_records'):
    """テーブルをクリーンアップ"""
    conn = get_pymysql_connection()
    cur = conn.cursor()
    cur.execute(f"TRUNCATE TABLE {table_name}")
    conn.commit()
    cur.close()
    conn.close()


# ========================================
# PyMySQL Benchmarks
# ========================================

def bench_pymysql_execute(record_count: int):
    """PyMySQL: 1件ずつexecute（遅い）"""
    cleanup_table()
    conn = get_pymysql_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    for record in records:
        cur.execute(sql, record)

    conn.commit()
    cur.close()
    conn.close()


def bench_pymysql_executemany(record_count: int):
    """PyMySQL: executemany"""
    cleanup_table()
    conn = get_pymysql_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    cur.executemany(sql, records)
    conn.commit()
    cur.close()
    conn.close()


def bench_pymysql_executemany_batched(record_count: int, batch_size: int = 1000):
    """PyMySQL: executemany with batching"""
    cleanup_table()
    conn = get_pymysql_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)

    conn.commit()
    cur.close()
    conn.close()


def bench_pymysql_multi_value(record_count: int, batch_size: int = 1000):
    """PyMySQL: Multi-value INSERT"""
    cleanup_table()
    conn = get_pymysql_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        placeholders = ','.join(['(%s, %s, %s, %s)'] * len(batch))
        sql = f"INSERT INTO simple_records (name, email, age, score) VALUES {placeholders}"

        # フラット化
        flat_values = []
        for r in batch:
            flat_values.extend(r)

        cur.execute(sql, flat_values)

    conn.commit()
    cur.close()
    conn.close()


# ========================================
# MySQLdb Benchmarks
# ========================================

def bench_mysqldb_execute(record_count: int):
    """MySQLdb: 1件ずつexecute（遅い）"""
    cleanup_table()
    conn = get_mysqldb_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    for record in records:
        cur.execute(sql, record)

    conn.commit()
    cur.close()
    conn.close()


def bench_mysqldb_executemany(record_count: int):
    """MySQLdb: executemany"""
    cleanup_table()
    conn = get_mysqldb_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    cur.executemany(sql, records)
    conn.commit()
    cur.close()
    conn.close()


def bench_mysqldb_executemany_batched(record_count: int, batch_size: int = 1000):
    """MySQLdb: executemany with batching"""
    cleanup_table()
    conn = get_mysqldb_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = "INSERT INTO simple_records (name, email, age, score) VALUES (%s, %s, %s, %s)"

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)

    conn.commit()
    cur.close()
    conn.close()


def bench_mysqldb_multi_value(record_count: int, batch_size: int = 1000):
    """MySQLdb: Multi-value INSERT"""
    cleanup_table()
    conn = get_mysqldb_connection()
    cur = conn.cursor()

    records = DataGenerator.generate_simple_tuples(record_count)

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        placeholders = ','.join(['(%s, %s, %s, %s)'] * len(batch))
        sql = f"INSERT INTO simple_records (name, email, age, score) VALUES {placeholders}"

        flat_values = []
        for r in batch:
            flat_values.extend(r)

        cur.execute(sql, flat_values)

    conn.commit()
    cur.close()
    conn.close()


# ========================================
# LOAD DATA INFILE (最速 - ファイル経由)
# ========================================

def bench_load_data_infile(record_count: int):
    """LOAD DATA LOCAL INFILE を使用（最速）"""
    import tempfile
    import csv

    cleanup_table()

    # 一時CSVファイル作成
    records = DataGenerator.generate_simple_records(record_count)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        for r in records:
            writer.writerow([r['name'], r['email'], r['age'], r['score']])
        temp_file = f.name

    try:
        conn = get_pymysql_connection()
        cur = conn.cursor()

        sql = f"""
        LOAD DATA LOCAL INFILE '{temp_file}'
        INTO TABLE simple_records
        FIELDS TERMINATED BY ','
        LINES TERMINATED BY '\n'
        (name, email, age, score)
        """

        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    finally:
        import os
        os.unlink(temp_file)


def main():
    """メインベンチマーク実行"""
    runner = BenchmarkRunner(output_file='/results/python_mysql_results.json')

    test_sizes = [
        100_000,
        1_000_000,
        # 10_000_000,
    ]

    for size in test_sizes:
        print(f"\n{'#'*60}")
        print(f"# Testing with {size:,} records")
        print(f"{'#'*60}")

        # 1件ずつは遅すぎるので10万件のみ
        if size <= 100_000:
            runner.run_benchmark(
                f"pymysql_execute_{size}",
                bench_pymysql_execute,
                size
            )
            runner.run_benchmark(
                f"mysqldb_execute_{size}",
                bench_mysqldb_execute,
                size
            )

        # PyMySQL
        runner.run_benchmark(
            f"pymysql_executemany_{size}",
            bench_pymysql_executemany,
            size
        )

        runner.run_benchmark(
            f"pymysql_executemany_batched_{size}",
            bench_pymysql_executemany_batched,
            size
        )

        runner.run_benchmark(
            f"pymysql_multi_value_{size}",
            bench_pymysql_multi_value,
            size
        )

        # MySQLdb
        runner.run_benchmark(
            f"mysqldb_executemany_{size}",
            bench_mysqldb_executemany,
            size
        )

        runner.run_benchmark(
            f"mysqldb_executemany_batched_{size}",
            bench_mysqldb_executemany_batched,
            size
        )

        runner.run_benchmark(
            f"mysqldb_multi_value_{size}",
            bench_mysqldb_multi_value,
            size
        )

        # LOAD DATA INFILE
        runner.run_benchmark(
            f"load_data_infile_{size}",
            bench_load_data_infile,
            size
        )

    runner.save_results()
    runner.print_summary()


if __name__ == '__main__':
    print("MySQL Bulk Insert Benchmark")
    print("=" * 60)
    main()
