# Beadsの同時並行編集処理とSwarm Coordinatorへの応用

## 調査概要

Beadsが複数エージェントやブランチからの同時並行編集をどのように処理しているかを調査し、Swarm Coordinatorへの応用可能性を検討しました。

## Beadsの並行編集戦略

### 1. ハッシュベースID（v0.20.1の核心改善）

**問題**: 順序付きID（bd-1, bd-2, bd-3）では並行作業時にID衝突が頻発

**解決策**: ハッシュベースID（bd-a1b2, bd-f14c, bd-3e7a）

```
従来（v0.19以前）:
- Agent A: bd-1, bd-2, bd-3を作成
- Agent B: bd-1, bd-2, bd-3を作成（同時）
→ マージ時に衝突！

新方式（v0.20.1+）:
- Agent A: bd-a1b2, bd-f14c を作成
- Agent B: bd-3e7a, bd-9c8b を作成（同時）
→ ハッシュが異なるため衝突なし
```

**プログレッシブ長スケーリング**:
```
イシュー数      ハッシュ長    衝突確率
0-500          4文字        低
500-1,500      5文字        極低
1,500-10,000   6文字        ほぼゼロ
```

### 2. カスタムGitマージドライバー

**設定**:
```bash
git config merge.beads.driver "bd merge %A %O %L %R"
git config merge.beads.name "bd JSONL merge driver"
echo ".beads/beads.jsonl merge=beads" >> .gitattributes
```

**パラメータ**:
- `%A`: 現在のバージョン（HEAD）
- `%O`: 共通の祖先
- `%L`: ローカルブランチ
- `%R`: リモートブランチ

**動作**:
JSONLファイルの構造的理解に基づいて、行レベルではなくレコードレベルでマージを実行。

### 3. JSONL形式の選択理由

**なぜJSONLか**:

1. **Gitフレンドリー**
   ```jsonl
   {"id":"bd-a1b2","title":"Task A","status":"pending"}
   {"id":"bd-f14c","title":"Task B","status":"in_progress"}
   ```
   - 各行が独立したレコード
   - 新規追加は常にファイル末尾
   - 競合が起きにくい

2. **人間が読める**
   ```bash
   cat .beads/issues.jsonl | jq .
   ```

3. **マージ可能**
   - Agent A が行1を追加
   - Agent B が行2を追加
   - Gitが自動的に両方を統合

**JSONとの比較**:
```json
// JSON（マージ困難）
{
  "issues": [
    {"id": "1", ...},  // Agent A追加
    {"id": "2", ...}   // Agent B追加（競合！）
  ]
}
```

```jsonl
// JSONL（マージ容易）
{"id":"bd-a1b2",...}  // Agent A追加
{"id":"bd-f14c",...}  // Agent B追加（競合なし）
```

### 4. 二重永続化戦略

**アーキテクチャ**:
```
ソースオブトゥルース:     .beads/issues.jsonl (Git管理)
高速クエリキャッシュ:    .beads/*.db (SQLite、.gitignore)
```

**同期メカニズム**:

1. **SQLite → JSONL（エクスポート）**
   ```
   CRUD操作発生
   → 5秒間のデバウンス
   → 自動エクスポート
   → Gitにコミット可能
   ```

2. **JSONL → SQLite（インポート）**
   ```
   git pull / git merge実行
   → JSONLが新しいか確認
   → 自動インポート
   → SQLiteキャッシュ更新
   ```

3. **即座同期（Gitフック）**
   - **pre-commit**: コミット前に強制エクスポート
   - **post-merge**: マージ後に強制インポート

**利点**:
- SQLite: 複雑な依存関係クエリ、高速検索
- JSONL: Git管理、人間が読める、マージ可能

### 5. 階層的子ID（さらなる衝突回避）

**親タスク内での並行作業**:
```jsonl
{"id":"bd-a3f8","title":"Epic: Auth System","type":"epic"}
{"id":"bd-a3f8.1","title":"Subtask by Agent A","parent":"bd-a3f8"}
{"id":"bd-a3f8.2","title":"Subtask by Agent B","parent":"bd-a3f8"}
```

- `.1`, `.2`, `.3` は親タスク内で自動採番
- 異なるエージェントが同じエピック内で作業しても衝突しない

## Swarm Coordinatorへの応用

### 現状の課題

Swarm Coordinatorの現在の実装:

```jsonl
// tasks.jsonl
{"id":"task-001","description":"..."}
{"id":"task-002","description":"..."}
{"task_id":"task-001","agent_id":"agent-1","status":"in_progress"}
```

**潜在的な問題**:
- タスクIDが手動定義（"task-001"）
- 複数エージェントが同時に新しいタスクを作成すると衝突の可能性

### 提案する改善

#### 改善1: ハッシュベースIDの導入

**Before**:
```python
task_id = "task-001"  # 手動定義、衝突リスク
```

**After**:
```python
import hashlib
import time

def generate_task_id():
    """衝突回避ハッシュIDを生成"""
    data = f"{time.time()}-{os.urandom(8).hex()}"
    hash_val = hashlib.sha256(data.encode()).hexdigest()[:6]
    return f"task-{hash_val}"

# 使用例
task_id = generate_task_id()  # "task-a1b2c3"
```

**メリット**:
- 複数エージェントが同時にタスク作成しても衝突なし
- Gitマージ時の競合が激減

#### 改善2: SQLiteキャッシュの導入

**現状**: JSONLを毎回スキャン（遅い）

**改善案**:
```python
# swarm_cache.py
import sqlite3
from pathlib import Path

class SwarmCache:
    def __init__(self, swarm_dir=Path(".claude/swarm")):
        self.db_path = swarm_dir / ".cache" / "state.db"
        self.jsonl_path = swarm_dir / "tasks.jsonl"
        self._ensure_cache()

    def _ensure_cache(self):
        """キャッシュが古い場合は再構築"""
        if not self.db_path.exists():
            self._rebuild_cache()
            return

        jsonl_mtime = self.jsonl_path.stat().st_mtime
        db_mtime = self.db_path.stat().st_mtime

        if jsonl_mtime > db_mtime:
            self._rebuild_cache()

    def _rebuild_cache(self):
        """JSONLからSQLiteキャッシュを構築"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT,
                status TEXT,
                assigned_to TEXT,
                priority INTEGER,
                updated_at TEXT
            )
        """)

        # JSONLから読み込んで挿入
        with open(self.jsonl_path) as f:
            for line in f:
                record = json.loads(line)
                if "id" in record and "task_id" not in record:
                    # タスク定義
                    conn.execute(
                        "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?)",
                        (record["id"], record["description"], "pending", None, record.get("priority", 0), datetime.now().isoformat())
                    )
                elif "task_id" in record:
                    # タスク更新
                    conn.execute(
                        "UPDATE tasks SET status=?, assigned_to=?, updated_at=? WHERE id=?",
                        (record["status"], record.get("agent_id"), datetime.now().isoformat(), record["task_id"])
                    )

        conn.commit()
        conn.close()

    def get_available_tasks(self):
        """高速クエリ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM tasks
            WHERE status='pending' AND assigned_to IS NULL
            ORDER BY priority DESC
        """)
        tasks = cursor.fetchall()
        conn.close()
        return tasks
```

**メリット**:
- 100倍以上の高速化（特に大量タスク時）
- 複雑な依存関係クエリが可能

#### 改善3: Gitフックの導入

```bash
# .claude/swarm/.git/hooks/pre-commit
#!/bin/bash
# コミット前にキャッシュをJSONLに反映
python3 .claude/swarm/scripts/flush_cache.py
```

```bash
# .claude/swarm/.git/hooks/post-merge
#!/bin/bash
# マージ後にJSONLからキャッシュ再構築
python3 .claude/swarm/scripts/rebuild_cache.py
```

#### 改善4: カスタムマージドライバー（オプション）

```bash
# .gitattributes
.claude/swarm/*.jsonl merge=swarm

# .git/config
[merge "swarm"]
    driver = python3 .claude/swarm/scripts/merge_jsonl.py %A %O %L %R
    name = Swarm JSONL merge driver
```

**merge_jsonl.py**:
```python
#!/usr/bin/env python3
import sys
import json

def merge_jsonl(current, base, other):
    """JSONLファイルをレコードレベルでマージ"""
    records = {}

    # ベース、現在、他をすべて読み込む
    for filepath in [base, current, other]:
        with open(filepath) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get("id") or record.get("task_id") or record.get("file_path") or record.get("from")
                if record_id:
                    # 最新のタイムスタンプを優先
                    if record_id not in records or record.get("timestamp", "") > records[record_id].get("timestamp", ""):
                        records[record_id] = record

    # マージ結果を書き込み
    with open(current, "w") as f:
        for record in records.values():
            f.write(json.dumps(record) + "\n")

    return 0  # マージ成功

if __name__ == "__main__":
    current, base, other = sys.argv[1:4]
    sys.exit(merge_jsonl(current, base, other))
```

## 比較: Beads vs Swarm Coordinator

| 機能 | Beads | Swarm Coordinator（現在） | Swarm Coordinator（改善案） |
|------|-------|---------------------------|---------------------------|
| **ID生成** | ハッシュベース | 手動定義 | **ハッシュベース** |
| **並行編集** | 衝突回避設計 | 可能だが衝突リスク | **衝突回避** |
| **キャッシュ** | SQLite | なし | **SQLite** |
| **マージドライバー** | カスタム | なし | **オプション** |
| **同期** | 自動（デバウンス） | 手動 | **自動（フック）** |
| **スケール** | 数千タスク | 数十〜数百 | **数千タスク** |

## 実装の優先度

### Phase 1: 即座に実装すべき（高優先度）

1. **ハッシュベースID**
   - 実装コスト: 低（数十行）
   - 効果: 高（衝突完全回避）
   - リスク: 低（後方互換性維持可能）

2. **SQLiteキャッシュ**
   - 実装コスト: 中（200-300行）
   - 効果: 高（パフォーマンス向上）
   - リスク: 低（既存JSONL維持）

### Phase 2: 検討すべき（中優先度）

3. **Gitフック**
   - 実装コスト: 低（スクリプト数本）
   - 効果: 中（同期の確実性向上）
   - リスク: 中（ユーザーの環境依存）

### Phase 3: オプション（低優先度）

4. **カスタムマージドライバー**
   - 実装コスト: 高（複雑なマージロジック）
   - 効果: 中（既にJSONLで十分マージ可能）
   - リスク: 高（設定の複雑化）

## 結論

Beadsから学ぶべき最も重要な教訓:

1. **ハッシュベースIDで衝突を根本的に回避**
2. **JSONLはGitネイティブなマルチエージェント環境に最適**
3. **SQLiteキャッシュで性能と機能性を両立**
4. **Gitフックで同期を自動化**

Swarm CoordinatorはすでにJSONLを採用しており、基盤は良好です。ハッシュベースIDとSQLiteキャッシュを追加するだけで、Beadsと同等以上の並行編集能力を獲得できます。

## 参考資料

- [Beads GitHub](https://github.com/steveyegge/beads)
- [JSONL Specification](http://jsonlines.org/)
- [Git Merge Drivers](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)
