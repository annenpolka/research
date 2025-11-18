"""
データ生成ユーティリティ
"""
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


class DataGenerator:
    """テストデータを生成するクラス"""

    @staticmethod
    def generate_simple_record() -> Dict[str, Any]:
        """シンプルなレコードを1件生成"""
        return {
            'name': ''.join(random.choices(string.ascii_letters, k=20)),
            'email': f"{''.join(random.choices(string.ascii_lowercase, k=10))}@example.com",
            'age': random.randint(18, 80),
            'score': round(random.uniform(0, 100), 2),
        }

    @staticmethod
    def generate_simple_records(count: int) -> List[Dict[str, Any]]:
        """シンプルなレコードを複数生成"""
        return [DataGenerator.generate_simple_record() for _ in range(count)]

    @staticmethod
    def generate_complex_record() -> Dict[str, Any]:
        """複雑なレコードを1件生成"""
        tags = [f"tag{i}" for i in random.sample(range(100), k=random.randint(1, 5))]
        return {
            'uuid': str(uuid.uuid4()),
            'name': ''.join(random.choices(string.ascii_letters, k=30)),
            'email': f"{''.join(random.choices(string.ascii_lowercase, k=15))}@example.com",
            'age': random.randint(18, 80),
            'score': round(random.uniform(0, 100), 2),
            'balance': round(random.uniform(-10000, 100000), 2),
            'is_active': random.choice([True, False]),
            'category': random.choice(['A', 'B', 'C', 'D', 'E']),
            'description': ''.join(random.choices(string.ascii_letters + ' ', k=200)),
            'metadata': {'key1': 'value1', 'key2': random.randint(1, 1000)},
            'tags': tags,
            'last_login_at': datetime.now() - timedelta(days=random.randint(0, 365)),
            'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        }

    @staticmethod
    def generate_complex_records(count: int) -> List[Dict[str, Any]]:
        """複雑なレコードを複数生成"""
        return [DataGenerator.generate_complex_record() for _ in range(count)]

    @staticmethod
    def generate_simple_tuples(count: int) -> List[tuple]:
        """シンプルなレコードをタプル形式で生成（execute_values用）"""
        records = DataGenerator.generate_simple_records(count)
        return [(r['name'], r['email'], r['age'], r['score']) for r in records]

    @staticmethod
    def generate_csv_data(count: int) -> str:
        """CSV形式のデータを生成（COPY用）"""
        records = DataGenerator.generate_simple_records(count)
        lines = []
        for r in records:
            lines.append(f"{r['name']},{r['email']},{r['age']},{r['score']}")
        return '\n'.join(lines)


if __name__ == '__main__':
    # テスト
    gen = DataGenerator()
    print("Simple record:", gen.generate_simple_record())
    print("Complex record:", gen.generate_complex_record())
    print(f"Generated {len(gen.generate_simple_records(10))} simple records")
