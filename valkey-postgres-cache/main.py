#!/usr/bin/env python3
"""
パラメータキャッシュシステムのデモアプリケーション

Valkey + PostgreSQL の二層キャッシュ動作を確認します。
"""

import time
from parameter_cache import ParameterCache
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """セパレーターの表示"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)
    print()


def demo_basic_operations():
    """基本操作のデモ"""
    print_separator("1. 基本操作のデモ")

    with ParameterCache() as cache:
        # 既存パラメータの取得（初回はキャッシュミス）
        logger.info("📖 既存パラメータの取得...")
        value = cache.get("app.max_connections")
        print(f"  app.max_connections = {value}")

        # 2回目はキャッシュヒット
        logger.info("📖 同じパラメータを再取得...")
        value = cache.get("app.max_connections")
        print(f"  app.max_connections = {value}")

        # 新規パラメータの設定
        logger.info("✏️  新規パラメータの設定...")
        cache.set(
            key="app.new_feature_flag",
            value="enabled",
            description="新機能のフラグ",
            category="feature",
            ttl=600,
        )

        # 設定したパラメータの取得（キャッシュヒット）
        logger.info("📖 新規パラメータの取得...")
        value = cache.get("app.new_feature_flag")
        print(f"  app.new_feature_flag = {value}")


def demo_cache_performance():
    """キャッシュパフォーマンスのデモ"""
    print_separator("2. キャッシュパフォーマンスの比較")

    with ParameterCache() as cache:
        # キャッシュのクリア
        cache.clear_cache()
        cache.cache_hits = 0
        cache.cache_misses = 0

        # 複数回読み取り
        keys = [
            "app.max_connections",
            "app.timeout_seconds",
            "api.rate_limit",
            "cache.default_ttl",
        ]

        logger.info("📊 初回読み取り（キャッシュミス）...")
        start = time.time()
        for key in keys:
            cache.get(key)
        first_read_time = time.time() - start
        print(f"  初回読み取り時間: {first_read_time:.4f}秒")

        logger.info("📊 2回目読み取り（キャッシュヒット）...")
        start = time.time()
        for key in keys:
            cache.get(key)
        second_read_time = time.time() - start
        print(f"  2回目読み取り時間: {second_read_time:.4f}秒")

        speedup = first_read_time / second_read_time if second_read_time > 0 else 0
        print(f"  高速化倍率: {speedup:.2f}x")

        # 統計表示
        stats = cache.get_cache_stats()
        print(f"\n  キャッシュ統計:")
        print(f"    ヒット数: {stats['cache_hits']}")
        print(f"    ミス数: {stats['cache_misses']}")
        print(f"    ヒット率: {stats['hit_rate_percent']}%")


def demo_category_queries():
    """カテゴリ別クエリのデモ"""
    print_separator("3. カテゴリ別パラメータ取得")

    with ParameterCache() as cache:
        categories = ["system", "api", "feature"]

        for category in categories:
            logger.info(f"📂 カテゴリ: {category}")
            params = cache.get_all_by_category(category)
            print(f"\n  {category} パラメータ ({len(params)}件):")
            for param in params:
                print(f"    - {param['key']}: {param['value']}")


def demo_update_and_delete():
    """更新と削除のデモ"""
    print_separator("4. パラメータの更新と削除")

    with ParameterCache() as cache:
        test_key = "demo.test_parameter"

        # 作成
        logger.info("✏️  テストパラメータの作成...")
        cache.set(
            key=test_key,
            value="initial_value",
            description="デモ用テストパラメータ",
            category="demo",
        )
        value = cache.get(test_key)
        print(f"  作成: {test_key} = {value}")

        # 更新
        logger.info("✏️  テストパラメータの更新...")
        cache.set(key=test_key, value="updated_value", category="demo")
        value = cache.get(test_key)
        print(f"  更新: {test_key} = {value}")

        # 削除
        logger.info("🗑️  テストパラメータの削除...")
        success = cache.delete(test_key)
        print(f"  削除: {success}")

        # 削除確認
        value = cache.get(test_key)
        print(f"  削除後: {test_key} = {value}")


def demo_cache_expiration():
    """キャッシュ有効期限のデモ"""
    print_separator("5. キャッシュTTLのデモ")

    with ParameterCache() as cache:
        test_key = "demo.ttl_test"

        # 短いTTLで設定
        logger.info("✏️  短いTTL（3秒）でパラメータを設定...")
        cache.set(
            key=test_key,
            value="expires_soon",
            description="TTLテスト用",
            category="demo",
            ttl=3,
        )

        # 即座に取得（キャッシュヒット）
        value = cache.get(test_key)
        print(f"  即座に取得: {value} (キャッシュヒット)")

        # 5秒待機
        logger.info("⏱️  5秒待機中...")
        time.sleep(5)

        # 再取得（キャッシュ失効、DBから取得）
        cache.cache_hits = 0
        cache.cache_misses = 0
        value = cache.get(test_key)
        print(f"  5秒後に取得: {value}")

        stats = cache.get_cache_stats()
        if stats["cache_misses"] > 0:
            print("  ✓ キャッシュが失効しDBから再取得されました")
        else:
            print("  ✓ キャッシュがまだ有効です")

        # クリーンアップ
        cache.delete(test_key)


def main():
    """メイン関数"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     Valkey + PostgreSQL 二層キャッシュシステム デモ              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    try:
        # 各デモを実行
        demo_basic_operations()
        demo_cache_performance()
        demo_category_queries()
        demo_update_and_delete()
        demo_cache_expiration()

        print_separator("完了")
        print("✓ すべてのデモが正常に完了しました")
        print()

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    main()
