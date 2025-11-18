"""
SQLAlchemy を使用したベンチマーク
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from data_generator import DataGenerator
from benchmark_utils import BenchmarkRunner


# 接続設定
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'benchmark')}:{os.getenv('POSTGRES_PASSWORD', 'benchmark')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DB', 'benchmark')}"

Base = declarative_base()


class SimpleRecord(Base):
    """Simple Recordsモデル"""
    __tablename__ = 'simple_records'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    score = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


def get_engine():
    """SQLAlchemyエンジンを取得"""
    return create_engine(POSTGRES_URL, echo=False)


def cleanup_table():
    """テーブルをクリーンアップ"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE simple_records RESTART IDENTITY CASCADE"))
        conn.commit()
    engine.dispose()


# ========================================
# Benchmark 1: ORM add + flush (最も遅い)
# ========================================
def bench_orm_add(record_count: int):
    """ORMのadd()メソッドを使用（非推奨・遅い）"""
    cleanup_table()
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    records = DataGenerator.generate_simple_records(record_count)
    for r in records:
        record = SimpleRecord(**r)
        session.add(record)

    session.commit()
    session.close()
    engine.dispose()


# ========================================
# Benchmark 2: bulk_save_objects
# ========================================
def bench_bulk_save_objects(record_count: int):
    """bulk_save_objects を使用"""
    cleanup_table()
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    records = DataGenerator.generate_simple_records(record_count)
    objects = [SimpleRecord(**r) for r in records]

    session.bulk_save_objects(objects)
    session.commit()
    session.close()
    engine.dispose()


# ========================================
# Benchmark 3: bulk_insert_mappings (推奨)
# ========================================
def bench_bulk_insert_mappings(record_count: int):
    """bulk_insert_mappings を使用（推奨）"""
    cleanup_table()
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    records = DataGenerator.generate_simple_records(record_count)
    session.bulk_insert_mappings(SimpleRecord, records)

    session.commit()
    session.close()
    engine.dispose()


# ========================================
# Benchmark 4: bulk_insert_mappings with batching
# ========================================
def bench_bulk_insert_mappings_batched(record_count: int, batch_size: int = 10000):
    """bulk_insert_mappings をバッチ処理で使用"""
    cleanup_table()
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    records = DataGenerator.generate_simple_records(record_count)

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        session.bulk_insert_mappings(SimpleRecord, batch)

    session.commit()
    session.close()
    engine.dispose()


# ========================================
# Benchmark 5: Core API (最速のSQLAlchemy方法)
# ========================================
def bench_core_insert(record_count: int):
    """Core API を使用した直接挿入"""
    cleanup_table()
    engine = get_engine()

    records = DataGenerator.generate_simple_records(record_count)

    with engine.connect() as conn:
        conn.execute(
            SimpleRecord.__table__.insert(),
            records
        )
        conn.commit()

    engine.dispose()


# ========================================
# Benchmark 6: Core API with batching
# ========================================
def bench_core_insert_batched(record_count: int, batch_size: int = 10000):
    """Core API をバッチ処理で使用"""
    cleanup_table()
    engine = get_engine()

    records = DataGenerator.generate_simple_records(record_count)

    with engine.connect() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            conn.execute(
                SimpleRecord.__table__.insert(),
                batch
            )
        conn.commit()

    engine.dispose()


# ========================================
# Benchmark 7: Raw SQL with executemany
# ========================================
def bench_raw_sql(record_count: int):
    """生SQLを使用"""
    cleanup_table()
    engine = get_engine()

    records = DataGenerator.generate_simple_tuples(record_count)
    sql = text("INSERT INTO simple_records (name, email, age, score) VALUES (:name, :email, :age, :score)")

    with engine.connect() as conn:
        # タプルを辞書に変換
        dict_records = [{'name': r[0], 'email': r[1], 'age': r[2], 'score': r[3]} for r in records]
        for r in dict_records:
            conn.execute(sql, r)
        conn.commit()

    engine.dispose()


def main():
    """メインベンチマーク実行"""
    runner = BenchmarkRunner(output_file='/results/python_sqlalchemy_results.json')

    test_sizes = [
        100_000,
        1_000_000,
        # 10_000_000,
    ]

    for size in test_sizes:
        print(f"\n{'#'*60}")
        print(f"# Testing with {size:,} records")
        print(f"{'#'*60}")

        # ORM addは遅すぎるので10万件のみ
        if size <= 100_000:
            runner.run_benchmark(
                f"sqlalchemy_orm_add_{size}",
                bench_orm_add,
                size
            )

        runner.run_benchmark(
            f"sqlalchemy_bulk_save_objects_{size}",
            bench_bulk_save_objects,
            size
        )

        runner.run_benchmark(
            f"sqlalchemy_bulk_insert_mappings_{size}",
            bench_bulk_insert_mappings,
            size
        )

        runner.run_benchmark(
            f"sqlalchemy_bulk_insert_mappings_batched_{size}",
            bench_bulk_insert_mappings_batched,
            size
        )

        runner.run_benchmark(
            f"sqlalchemy_core_insert_{size}",
            bench_core_insert,
            size
        )

        runner.run_benchmark(
            f"sqlalchemy_core_insert_batched_{size}",
            bench_core_insert_batched,
            size
        )

    runner.save_results()
    runner.print_summary()


if __name__ == '__main__':
    print("PostgreSQL Bulk Insert Benchmark - SQLAlchemy")
    print("=" * 60)
    main()
