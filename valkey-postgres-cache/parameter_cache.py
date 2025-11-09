"""
Valkey + PostgreSQL 二層キャッシュシステム

このモジュールは、Valkeyをキャッシュ層、PostgreSQLを永続化層として使用し、
アプリケーションパラメータの効率的な管理を実現します。
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParameterCache:
    """Valkey + PostgreSQL 二層キャッシュマネージャー"""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_db: str = "params_db",
        postgres_user: str = "postgres",
        postgres_password: str = "postgres",
        default_ttl: int = 3600,
    ):
        """
        初期化

        Args:
            redis_host: Valkeyホスト
            redis_port: Valkeyポート
            postgres_host: PostgreSQLホスト
            postgres_port: PostgreSQLポート
            postgres_db: データベース名
            postgres_user: データベースユーザー
            postgres_password: データベースパスワード
            default_ttl: デフォルトキャッシュTTL（秒）
        """
        self.default_ttl = default_ttl
        self.cache_hits = 0
        self.cache_misses = 0

        # Valkey接続
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self.redis_client.ping()
            logger.info("✓ Valkey connected")
        except Exception as e:
            logger.error(f"✗ Valkey connection failed: {e}")
            raise

        # PostgreSQL接続
        try:
            self.db_conn = psycopg2.connect(
                host=postgres_host,
                port=postgres_port,
                database=postgres_db,
                user=postgres_user,
                password=postgres_password,
            )
            logger.info("✓ PostgreSQL connected")
        except Exception as e:
            logger.error(f"✗ PostgreSQL connection failed: {e}")
            raise

    def _make_cache_key(self, key: str) -> str:
        """キャッシュキーの作成"""
        return f"param:{key}"

    def get(self, key: str) -> Optional[str]:
        """
        パラメータの取得（キャッシュファーストアプローチ）

        Args:
            key: パラメータキー

        Returns:
            パラメータ値（存在しない場合はNone）
        """
        cache_key = self._make_cache_key(key)

        # 1. Valkeyキャッシュをチェック
        try:
            cached_value = self.redis_client.get(cache_key)
            if cached_value is not None:
                self.cache_hits += 1
                logger.info(f"✓ Cache HIT: {key}")
                return cached_value
        except Exception as e:
            logger.warning(f"Valkey get error: {e}, falling back to DB")

        # 2. キャッシュミス: PostgreSQLから取得
        self.cache_misses += 1
        logger.info(f"✗ Cache MISS: {key}, fetching from DB")

        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT value FROM parameters WHERE key = %s", (key,)
                )
                result = cursor.fetchone()

                if result:
                    value = result["value"]
                    # 3. Valkeyにキャッシュ
                    try:
                        self.redis_client.setex(
                            cache_key, self.default_ttl, value
                        )
                        logger.info(f"✓ Cached in Valkey: {key}")
                    except Exception as e:
                        logger.warning(f"Valkey set error: {e}")

                    return value

                return None
        except Exception as e:
            logger.error(f"Database get error: {e}")
            raise

    def set(
        self,
        key: str,
        value: str,
        description: str = "",
        category: str = "general",
        data_type: str = "string",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        パラメータの設定（Write-Through戦略）

        Args:
            key: パラメータキー
            value: パラメータ値
            description: 説明
            category: カテゴリ
            data_type: データ型
            ttl: キャッシュTTL（Noneの場合はdefault_ttlを使用）

        Returns:
            成功した場合True
        """
        cache_key = self._make_cache_key(key)
        ttl = ttl or self.default_ttl

        try:
            # 1. PostgreSQLに書き込み
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO parameters (key, value, description, category, data_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        data_type = EXCLUDED.data_type,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (key, value, description, category, data_type),
                )
            self.db_conn.commit()
            logger.info(f"✓ Saved to DB: {key}")

            # 2. Valkeyキャッシュを更新
            try:
                self.redis_client.setex(cache_key, ttl, value)
                logger.info(f"✓ Updated cache: {key}")
            except Exception as e:
                logger.warning(f"Valkey set error: {e}")

            return True
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Database set error: {e}")
            raise

    def delete(self, key: str) -> bool:
        """
        パラメータの削除

        Args:
            key: パラメータキー

        Returns:
            成功した場合True
        """
        cache_key = self._make_cache_key(key)

        try:
            # 1. PostgreSQLから削除
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM parameters WHERE key = %s", (key,))
                deleted = cursor.rowcount > 0
            self.db_conn.commit()

            if deleted:
                logger.info(f"✓ Deleted from DB: {key}")

                # 2. Valkeyキャッシュを削除
                try:
                    self.redis_client.delete(cache_key)
                    logger.info(f"✓ Deleted from cache: {key}")
                except Exception as e:
                    logger.warning(f"Valkey delete error: {e}")

                return True
            else:
                logger.info(f"Key not found: {key}")
                return False
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Database delete error: {e}")
            raise

    def get_all_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        カテゴリ別にすべてのパラメータを取得

        Args:
            category: カテゴリ名

        Returns:
            パラメータのリスト
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM parameters WHERE category = %s ORDER BY key",
                    (category,),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise

    def clear_cache(self, pattern: str = "param:*") -> int:
        """
        キャッシュのクリア

        Args:
            pattern: 削除するキーのパターン

        Returns:
            削除されたキーの数
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"✓ Cleared {deleted} cache entries")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計の取得

        Returns:
            統計情報
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (
            (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        try:
            cache_keys = len(self.redis_client.keys("param:*"))
        except Exception:
            cache_keys = -1

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cached_keys": cache_keys,
        }

    def close(self):
        """接続のクローズ"""
        try:
            self.db_conn.close()
            self.redis_client.close()
            logger.info("✓ Connections closed")
        except Exception as e:
            logger.error(f"Close error: {e}")

    def __enter__(self):
        """コンテキストマネージャーのエントリ"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.close()
