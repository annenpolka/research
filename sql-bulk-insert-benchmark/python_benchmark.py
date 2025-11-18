#!/usr/bin/env python3
"""
SQLバルクインサートベンチマーク - Python版

数千万件のデータをPostgreSQLに挿入する際の
様々なライブラリと手法のパフォーマンス比較
"""

import time
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Table, MetaData
from sqlalchemy.orm import sessionmaker
import pandas as pd
import io
from datetime import datetime
import random
import string
import os

# データベース接続情報（環境変数から取得、デフォルト値はローカル用）
DB_CONFIG = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': int(os.environ.get('PGPORT', 5432)),
    'database': os.environ.get('PGDATABASE', 'benchmark_db'),
    'user': os.environ.get('PGUSER', 'benchmark_user'),
    'password': os.environ.get('PGPASSWORD', 'benchmark_pass')
}

def get_connection():
    """PostgreSQL接続を取得"""
    return psycopg2.connect(**DB_CONFIG)

def get_sqlalchemy_engine():
    """SQLAlchemyエンジンを取得"""
    url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(url)

def create_table(conn, table_name):
    """テーブルを作成"""
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        cur.execute(f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                score FLOAT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
    conn.commit()

def generate_data(num_records):
    """テストデータを生成"""
    data = []
    for i in range(num_records):
        data.append((
            random.randint(1, 1000000),  # user_id
            f"user_{''.join(random.choices(string.ascii_lowercase, k=10))}",  # username
            f"user{i}@example.com",  # email
            random.uniform(0, 100),  # score
            datetime.now()  # created_at
        ))
    return data

def benchmark_psycopg2_executemany(num_records):
    """psycopg2のexecutemanyを使用したベンチマーク"""
    conn = get_connection()
    table_name = "benchmark_executemany"

    try:
        create_table(conn, table_name)
        data = generate_data(num_records)

        start_time = time.time()

        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {table_name} (user_id, username, email, score, created_at) VALUES (%s, %s, %s, %s, %s)",
                data
            )

        conn.commit()
        elapsed_time = time.time() - start_time

        return {
            'method': 'psycopg2 executemany',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        conn.close()

def benchmark_psycopg2_execute_batch(num_records, page_size=10000):
    """psycopg2のexecute_batchを使用したベンチマーク"""
    conn = get_connection()
    table_name = "benchmark_execute_batch"

    try:
        create_table(conn, table_name)
        data = generate_data(num_records)

        start_time = time.time()

        with conn.cursor() as cur:
            execute_batch(
                cur,
                f"INSERT INTO {table_name} (user_id, username, email, score, created_at) VALUES (%s, %s, %s, %s, %s)",
                data,
                page_size=page_size
            )

        conn.commit()
        elapsed_time = time.time() - start_time

        return {
            'method': f'psycopg2 execute_batch (page_size={page_size})',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        conn.close()

def benchmark_psycopg2_execute_values(num_records, page_size=10000):
    """psycopg2のexecute_valuesを使用したベンチマーク"""
    conn = get_connection()
    table_name = "benchmark_execute_values"

    try:
        create_table(conn, table_name)
        data = generate_data(num_records)

        start_time = time.time()

        with conn.cursor() as cur:
            execute_values(
                cur,
                f"INSERT INTO {table_name} (user_id, username, email, score, created_at) VALUES %s",
                data,
                page_size=page_size
            )

        conn.commit()
        elapsed_time = time.time() - start_time

        return {
            'method': f'psycopg2 execute_values (page_size={page_size})',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        conn.close()

def benchmark_psycopg2_copy(num_records):
    """psycopg2のCOPYを使用したベンチマーク"""
    conn = get_connection()
    table_name = "benchmark_copy"

    try:
        create_table(conn, table_name)
        data = generate_data(num_records)

        start_time = time.time()

        # データをCSV形式の文字列バッファに変換
        buffer = io.StringIO()
        for row in data:
            # データを\t区切りで結合
            buffer.write('\t'.join(str(x) for x in row) + '\n')
        buffer.seek(0)

        with conn.cursor() as cur:
            cur.copy_from(
                buffer,
                table_name,
                columns=('user_id', 'username', 'email', 'score', 'created_at'),
                sep='\t'
            )

        conn.commit()
        elapsed_time = time.time() - start_time

        return {
            'method': 'psycopg2 COPY',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        conn.close()

def benchmark_sqlalchemy_bulk_insert(num_records):
    """SQLAlchemyのbulk_insert_mappingsを使用したベンチマーク"""
    engine = get_sqlalchemy_engine()
    table_name = "benchmark_sqlalchemy_bulk"

    try:
        # テーブル作成
        conn = get_connection()
        create_table(conn, table_name)
        conn.close()

        # データ生成
        raw_data = generate_data(num_records)
        data = [
            {
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'score': row[3],
                'created_at': row[4]
            }
            for row in raw_data
        ]

        start_time = time.time()

        Session = sessionmaker(bind=engine)
        session = Session()

        # メタデータからテーブル情報を取得
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables[table_name]

        # bulk_insert_mappingsを使用
        session.bulk_insert_mappings(type(table_name, (), {}), data)
        session.commit()
        session.close()

        elapsed_time = time.time() - start_time

        return {
            'method': 'SQLAlchemy bulk_insert_mappings',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        engine.dispose()

def benchmark_sqlalchemy_core_insert(num_records, batch_size=10000):
    """SQLAlchemy CoreのinsertでバッチINSERT"""
    engine = get_sqlalchemy_engine()
    table_name = "benchmark_sqlalchemy_core"

    try:
        # テーブル作成
        conn_pg = get_connection()
        create_table(conn_pg, table_name)
        conn_pg.close()

        # データ生成
        raw_data = generate_data(num_records)
        data = [
            {
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'score': row[3],
                'created_at': row[4]
            }
            for row in raw_data
        ]

        start_time = time.time()

        # メタデータからテーブル情報を取得
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables[table_name]

        with engine.begin() as conn:
            # バッチでINSERT
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                conn.execute(table.insert(), batch)

        elapsed_time = time.time() - start_time

        return {
            'method': f'SQLAlchemy Core insert (batch={batch_size})',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        engine.dispose()

def benchmark_pandas_to_sql(num_records, chunksize=10000):
    """pandasのto_sqlを使用したベンチマーク"""
    engine = get_sqlalchemy_engine()
    table_name = "benchmark_pandas"

    try:
        # テーブル作成
        conn = get_connection()
        create_table(conn, table_name)
        conn.close()

        # データ生成
        raw_data = generate_data(num_records)
        df = pd.DataFrame(raw_data, columns=['user_id', 'username', 'email', 'score', 'created_at'])

        start_time = time.time()

        df.to_sql(
            table_name,
            engine,
            if_exists='append',
            index=False,
            chunksize=chunksize,
            method='multi'
        )

        elapsed_time = time.time() - start_time

        return {
            'method': f'pandas to_sql (chunksize={chunksize})',
            'records': num_records,
            'time': elapsed_time,
            'records_per_second': num_records / elapsed_time
        }
    finally:
        engine.dispose()

def run_benchmarks(num_records):
    """すべてのベンチマークを実行"""
    print(f"\n{'='*80}")
    print(f"Python SQLバルクインサートベンチマーク - {num_records:,}件")
    print(f"{'='*80}\n")

    results = []

    # 小規模データではすべてのメソッドをテスト
    if num_records <= 1000000:
        print("1. psycopg2 executemany をテスト中...")
        try:
            result = benchmark_psycopg2_executemany(num_records)
            results.append(result)
            print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
        except Exception as e:
            print(f"   エラー: {e}\n")

    print("2. psycopg2 execute_batch をテスト中...")
    try:
        result = benchmark_psycopg2_execute_batch(num_records)
        results.append(result)
        print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
    except Exception as e:
        print(f"   エラー: {e}\n")

    print("3. psycopg2 execute_values をテスト中...")
    try:
        result = benchmark_psycopg2_execute_values(num_records)
        results.append(result)
        print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
    except Exception as e:
        print(f"   エラー: {e}\n")

    print("4. psycopg2 COPY をテスト中...")
    try:
        result = benchmark_psycopg2_copy(num_records)
        results.append(result)
        print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
    except Exception as e:
        print(f"   エラー: {e}\n")

    print("5. SQLAlchemy Core insert をテスト中...")
    try:
        result = benchmark_sqlalchemy_core_insert(num_records)
        results.append(result)
        print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
    except Exception as e:
        print(f"   エラー: {e}\n")

    print("6. pandas to_sql をテスト中...")
    try:
        result = benchmark_pandas_to_sql(num_records)
        results.append(result)
        print(f"   完了: {result['time']:.2f}秒, {result['records_per_second']:,.0f}件/秒\n")
    except Exception as e:
        print(f"   エラー: {e}\n")

    # 結果を速度順にソート
    results.sort(key=lambda x: x['time'])

    print(f"\n{'='*80}")
    print("ベンチマーク結果 (速い順)")
    print(f"{'='*80}\n")
    print(f"{'順位':<4} {'メソッド':<45} {'時間(秒)':<12} {'件/秒':<15} {'相対速度'}")
    print(f"{'-'*80}")

    fastest_time = results[0]['time']
    for i, result in enumerate(results, 1):
        relative_speed = fastest_time / result['time']
        print(f"{i:<4} {result['method']:<45} {result['time']:<12.2f} {result['records_per_second']:<15,.0f} {relative_speed:.2f}x")

    return results

if __name__ == "__main__":
    import sys

    # コマンドライン引数から件数を取得（デフォルトは100万件）
    num_records = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000

    results = run_benchmarks(num_records)

    print(f"\n{'='*80}")
    print("推奨事項")
    print(f"{'='*80}\n")
    print("最速: psycopg2のCOPYコマンドが圧倒的に高速")
    print("バランス: execute_valuesが使いやすさと速度のバランスが良い")
    print("SQLAlchemy: ORMの抽象化が必要な場合はCore insertを推奨")
    print("pandas: データ分析パイプラインではto_sqlが便利だが、やや低速")
