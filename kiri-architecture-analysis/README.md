# KIRI アーキテクチャ分析

## 概要

**KIRI (KIRI MCP Server)** は、LLM向けにGitリポジトリから知的にコードコンテキストを抽出するModel Context Protocol (MCP)サーバーです。リポジトリをDuckDBにインデックス化し、セマンティック検索ツールを提供することで、LLMが関連するコードスニペットを効率的に検索できるようにします。

- **リポジトリ**: https://github.com/CAPHTECH/kiri
- **バージョン**: 0.9.6
- **ライセンス**: MIT
- **技術スタック**: TypeScript, DuckDB, tree-sitter, Node.js

## 主要機能

1. **MCPネイティブ**: Claude Desktop、Codex CLIなどのMCPクライアントとシームレスに統合
2. **スマートコンテキスト**: タスク目標に基づいて最小限の関連コード断片を抽出（95%の精度）
3. **高速**: ほとんどのクエリで1秒未満のレスポンスタイム
4. **セマンティック検索**: 複数単語クエリ、依存関係分析、BM25ランキング
5. **自動同期**: ウォッチモードでファイル変更時に自動再インデックス化
6. **信頼性の高い設計**: オプション拡張なしでも動作するdegrade-firstアーキテクチャ

## システムアーキテクチャ

### 全体構成

```
┌─────────────────┐         ┌──────────────────────┐         ┌────────────┐
│   MCP Client    │ <────>  │   KIRI MCP Server    │ <────>  │   DuckDB   │
│ (Claude, Codex) │  stdio  │   (JSON-RPC 2.0)     │         │  Database  │
└─────────────────┘         └──────────────────────┘         └────────────┘
                                       │
                                       ▼
                             ┌──────────────────┐
                             │     Indexer      │
                             │  Git Scanner     │
                             │  AST Parser      │
                             │  FTS Indexing    │
                             └──────────────────┘
```

### 階層化アーキテクチャ

KIRIは以下の5つの主要層で構成されています：

#### 1. Client/Proxy層 (`src/client/`)

**役割**: MCPクライアントとデーモン間の透過的なブリッジ

**主要コンポーネント**:
- **proxy.ts**: Stdio ↔ Unixソケットのブリッジ
  - 自動デーモン起動
  - バージョン互換性チェック
  - 接続リトライロジック
- **cli.ts**: コマンドライン引数パース
- **start-daemon.ts**: デーモンライフサイクル管理

**データフロー**:
```
MCP Client → stdin → Proxy → Unix Socket → Daemon
                                               ↓
MCP Client ← stdout ← Proxy ← Unix Socket ← Daemon
```

**特徴**:
- Major/minorバージョン不一致時の自動デーモン再起動
- 最大3回のリトライ（指数バックオフ）
- バージョン不一致の検出と自動修復

#### 2. Daemon層 (`src/daemon/`)

**役割**: データベースごとに単一のバックグラウンドプロセスを維持

**主要コンポーネント**:
- **daemon.ts**: メインデーモンプロセス
  - DuckDB接続管理
  - ウォッチモード統合
  - グレースフルシャットダウン
- **socket.ts**: Unixソケット/Windows名前付きパイプサーバー
- **lifecycle.ts**: PIDファイル、ロック、アイドルタイムアウト管理

**特徴**:
- 単一データベースごとに1デーモン（スタートアップロックで保証）
- 複数クライアント接続をソケット経由で処理
- ウォッチモード時はアイドルタイムアウトを無効化
- デフォルト5分のアイドルタイムアウト（設定可能）

#### 3. Server層 (`src/server/`)

**役割**: MCP JSON-RPC 2.0ツールの実装とリクエスト処理

**主要コンポーネント**:
- **main.ts**: HTTPサーバー（開発用）とstdioサーバー（MCP用）
- **stdio.ts**: Stdio JSON-RPCサーバー
- **rpc.ts**: JSON-RPC 2.0リクエスト処理
- **handlers.ts**: 5つのMCPツールの実装
- **runtime.ts**: サーバーランタイム（DB、メトリクス、セキュリティ）
- **scoring.ts**: ファイルランキングとブーストプロファイル

**提供されるMCPツール**:

1. **context_bundle**: タスク目標に基づいて関連コードコンテキストを抽出
2. **files_search**: 全文検索（BM25ランキング）
3. **snippets_get**: シンボル境界に整列したコードスニペット取得
4. **deps_closure**: 依存関係グラフ分析（inbound/outbound）
5. **semantic_rerank**: セマンティック類似度による候補の再ランキング

**スコアリングシステム**:
- **default**: 実装ファイル優先（src/）、ドキュメント・設定ファイルにペナルティ
- **docs**: ドキュメントファイル優先（.md, .yaml）
- **none**: ピュアBM25スコア

#### 4. Indexer層 (`src/indexer/`)

**役割**: Gitリポジトリのスキャンとコード構造の抽出

**主要コンポーネント**:
- **codeintel.ts**: AST解析とシンボル抽出
  - TypeScript: TypeScript Compiler API
  - Swift: tree-sitter-swift
  - PHP: tree-sitter-php（純粋PHPとHTML混在の両方）
  - Java: tree-sitter-java
  - Dart: Dart Analysis Server
- **git.ts**: Git操作とファイルスキャン
- **watch.ts**: ファイル変更監視（chokidar）
- **schema.ts**: DuckDBスキーマ管理
- **dart/**: Dart Analysis Server統合
  - **client.ts**: Analysis Serverクライアントプール
  - **analyze.ts**: シンボル抽出
  - **sdk.ts**: Dart SDK自動検出

**サポート言語**:
| 言語 | 拡張子 | シンボル種別 | パーサー |
|------|--------|--------------|----------|
| TypeScript | .ts, .tsx | class, interface, enum, function, method | TypeScript Compiler API |
| Swift | .swift | class, struct, protocol, enum, extension, func | tree-sitter-swift |
| PHP | .php | class, interface, trait, function, method | tree-sitter-php |
| Java | .java | class, interface, enum, annotation, method | tree-sitter-java |
| Dart | .dart | class, mixin, enum, extension, function | Dart Analysis Server |

**ウォッチモード機能**:
- デバウンス（デフォルト500ms、設定可能）
- インクリメンタルインデックス化（変更ファイルのみ）
- バックグラウンド動作（クエリを中断しない）
- `.gitignore`とdenylist統合

#### 5. Shared/Database層 (`src/shared/`)

**役割**: 共通ユーティリティとデータベースアクセス

**主要コンポーネント**:
- **duckdb.ts**: DuckDBクライアントラッパー
  - 自動.gitignore作成
  - パラメータ検証
  - トランザクション管理
- **embedding.ts**: ベクトル埋め込み生成（オプション）
- **tokenizer.ts**: トークン化戦略
  - phrase-aware: kebab-case/snake_caseをフレーズとして扱う
  - legacy: 従来の単語単位トークン化
  - hybrid: 両方の組み合わせ
- **security/**: セキュリティ設定とマスキング
  - `.env*`, `*.pem`, `secrets/**`の除外
  - センシティブ値のマスキング（`***`）

### データモデル

KIRIはGitライクなblob/tree分離モデルを使用：

#### コアテーブル

```sql
-- リポジトリメタデータ
repo (id, root, default_branch, indexed_at)

-- コミット履歴
commit (repo_id, hash, author_name, message, ...)

-- 内容ハッシュで一意化されたバイナリラージオブジェクト
blob (hash, size_bytes, line_count, content)

-- コミット時点でのpath → blobマッピング
tree (repo_id, commit_hash, path, blob_hash, ext, lang, ...)

-- HEAD時点の便宜表（高速検索用）
file (repo_id, path, blob_hash, ext, lang, ...)

-- AST抽出シンボル
symbol (repo_id, path, symbol_id, name, kind, range_start_line, ...)

-- import/require依存関係
dependency (repo_id, src_path, dst_kind, dst, rel)

-- コードスニペット（シンボル境界に整列）
snippet (repo_id, path, snippet_id, start_line, end_line, symbol_id)

-- オプション：ベクトル埋め込み
snippet_embedding (repo_id, path, snippet_id, vec)
```

#### データモデルの特徴

1. **Blob/Tree分離**:
   - ファイルリネーム時に内容を重複保存しない
   - 内容ハッシュ（SHA-1/SHA-256）で一意化
   - Gitの内部モデルと同様のアプローチ

2. **シンボル境界スニペット**:
   - 関数/クラス境界に整列
   - 文脈を保持した意味のあるコード断片
   - tree-sitterまたはDart Analysis Serverで抽出

3. **依存関係グラフ**:
   - Import/require/include関係を正規化
   - Inbound（誰が私をインポートしているか）とoutbound（私が誰をインポートしているか）クエリをサポート
   - パッケージとパス依存関係の区別

4. **オプションVSS（ベクトル類似検索）**:
   - DuckDB vss拡張が利用可能な場合のみ
   - Degrade運転時はBM25のみに依存

## デプロイメントアーキテクチャ

### プロセスモデル

```
┌─────────────────────────────────────────────┐
│              User Machine                    │
│                                              │
│  ┌──────────────┐                            │
│  │ MCP Client   │                            │
│  │ (Claude/     │                            │
│  │  Codex CLI)  │                            │
│  └──────┬───────┘                            │
│         │ stdio                              │
│  ┌──────▼────────┐                           │
│  │  kiri proxy   │                           │
│  └──────┬────────┘                           │
│         │ Unix socket / Named pipe           │
│  ┌──────▼────────────────────────────┐       │
│  │  kiri-daemon                      │       │
│  │  - DuckDB connection              │       │
│  │  - Watch mode (optional)          │       │
│  │  - Multiple client connections    │       │
│  └───────────────────────────────────┘       │
│                                              │
└─────────────────────────────────────────────┘
```

### ファイル構造

```
project-root/
├── .kiri/
│   ├── index.duckdb              # メインデータベース
│   ├── index.duckdb.wal          # Write-Ahead Log
│   ├── index.duckdb.pid          # デーモンPID
│   ├── index.duckdb.daemon.log   # デーモンログ
│   ├── index.duckdb.socket       # Unixソケット（macOS/Linux）
│   ├── denylist.yml              # カスタム除外パターン
│   └── .gitignore                # 自動生成（DB成果物を無視）
```

## セキュリティアーキテクチャ

### 多層防御

1. **インデックス時フィルタリング**:
   - `.gitignore`パターンの尊重
   - カスタムdenylistサポート（`.kiri/denylist.yml`）
   - センシティブファイルパターンの自動除外

2. **センシティブパターン**:
   ```yaml
   - .env*
   - *.pem
   - *.key
   - secrets/**
   - credentials.json
   ```

3. **レスポンスマスキング**:
   - APIキー、トークン、パスワードを`***`でマスク
   - 正規表現ベースの検出

4. **設定ロックファイル**:
   - セキュリティ設定の改ざん防止
   - SHA-256ハッシュ検証

## パフォーマンス最適化

### インデックス化

- **インクリメンタル更新**: ウォッチモードで変更ファイルのみ再インデックス化（10-100x高速化）
- **並列処理**: 複数ファイルの同時AST解析
- **Dart Analysis Serverプール**: メモリ効率的なクライアント管理（最大8同時）

### クエリ最適化

- **BM25ランキング**: DuckDB FTS拡張使用時
- **インデックス戦略**:
  - `idx_file_lang`: 言語フィルタ
  - `idx_symbol_name`: シンボル検索
  - `idx_dep_src`: 依存関係トラバーサル

### トークン削減

- **コンパクトモード**（v0.8.0+デフォルト）: プレビューなしでメタデータのみ返却
  - トークン使用量を95%削減（55K → 2.5K）
  - `compact: false`で完全プレビューモードに戻せる

### パフォーマンス目標

| メトリック | 目標 | 現状 |
|-----------|------|------|
| Time to First Result | ≤ 1.0s | ✅ 0.8s |
| Precision @ 10 | ≥ 0.7 | ✅ 0.75 |
| Token Reduction (compact) | ≥ 90% | ✅ 95% |

## 拡張性とスケーラビリティ

### リポジトリサイズ処理

| リポジトリサイズ | ファイル数 | DB サイズ | インデックス時間 | 推奨設定 |
|-----------------|-----------|-----------|----------------|----------|
| Small | <1,000 | 1-10 MB | <30秒 | デフォルト |
| Medium | 1,000-10,000 | 10-100 MB | 1-4分 | timeout=240s |
| Large | >10,000 | 100-500 MB | 4-8分 | timeout=480s |

### タイムアウト設定

**Claude Code** (`~/.claude/mcp.json`):
```json
{
  "mcpServers": {
    "kiri": {
      "env": {
        "KIRI_DAEMON_READY_TIMEOUT": "480"
      }
    }
  }
}
```

**Codex CLI** (`~/.config/codex/mcp.toml`):
```toml
[mcp_servers.kiri]
startup_timeout_sec = 480
```

### Dart Analysis Server設定

大規模Dartプロジェクト用の環境変数：

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `DART_ANALYSIS_MAX_CLIENTS` | 8 | 最大同時Analysis Serverプロセス数 |
| `DART_ANALYSIS_CLIENT_WAIT_MS` | 10000 | 利用可能スロット待機時間 |
| `DART_ANALYSIS_IDLE_MS` | 60000 | 未使用サーバー破棄までのアイドル時間 |

## 開発者向け情報

### プロジェクト構造

```
kiri/
├── src/
│   ├── indexer/      # Git走査、AST解析、スキーマ管理
│   │   ├── dart/     # Dart Analysis Server統合
│   │   └── pipeline/ # インデックス化パイプライン
│   ├── server/       # MCPサーバー、JSON-RPCハンドラ
│   │   ├── observability/ # メトリクス、トレーシング
│   │   └── fallbacks/     # デグレード制御
│   ├── client/       # CLIユーティリティ、デーモン管理
│   ├── daemon/       # デーモンプロセス
│   └── shared/       # DuckDBクライアント、ユーティリティ
│       ├── security/ # セキュリティ設定
│       └── utils/    # ロックファイル、ソケット
├── tests/            # テストファイル（src/をミラー）
├── docs/             # アーキテクチャドキュメント
├── config/           # YAML設定スキーマ
├── sql/              # SQLスキーマ定義
└── examples/         # 使用例
```

### ビルドとテスト

```bash
# 依存関係インストール
pnpm install

# ビルド
pnpm run build

# テスト実行
pnpm run test

# Lint + Test
pnpm run check

# 開発サーバー（HTTP:8765）
pnpm run dev
```

### コマンドリファレンス

```bash
# MCPモード（stdio）
kiri --repo <path> --db <db-path>

# HTTPモード（テスト用）
kiri --repo <path> --db <db-path> --port 8765

# ウォッチモード有効化
kiri --repo <path> --db <db-path> --watch

# 強制再インデックス化
kiri --repo <path> --db <db-path> --reindex

# デグレード許可（FTS/VSS拡張なしで動作）
kiri --repo <path> --db <db-path> --allow-degrade
```

## 設計原則

1. **Degrade-First**: オプション拡張なしでも動作する設計
2. **Security-First**: センシティブデータのフィルタリングとマスキング
3. **Performance-First**: サブ秒レスポンス、トークン削減
4. **Reliability-First**: グレースフルデグレード、エラー回復
5. **Developer-First**: 明確なAPI、包括的なドキュメント

## 技術的な意思決定

### なぜDuckDBを選んだのか？

- **埋め込み可能**: 外部DBサーバー不要
- **分析に最適化**: 複雑なクエリに高速
- **拡張可能**: FTS、VSS拡張のサポート
- **SQLインターフェース**: 標準的で習得が容易

### なぜtree-sitterを選んだのか？

- **高速**: 増分解析
- **言語に依存しない**: 統一されたAPI
- **堅牢**: 構文エラーに耐性
- **メンテナンス**: 活発なコミュニティ

### なぜデーモンアーキテクチャを選んだのか？

- **起動時間**: DuckDB接続を再利用
- **メモリ効率**: データベースを一度だけロード
- **ウォッチモード**: バックグラウンド再インデックス化
- **マルチクライアント**: 複数の同時接続

## 既知の制限事項

1. **言語サポート**: 現在5言語（TypeScript, Swift, PHP, Java, Dart）のみAST解析対応
2. **モノレポ**: 非常に大きなモノレポ（>50,000ファイル）は初期インデックス化に時間がかかる可能性
3. **リアルタイム同期**: ウォッチモードはデバウンスされており、即座ではない
4. **ベクトル検索**: オプションのvss拡張が必要（すべての環境で利用可能とは限らない）

## 今後のロードマップ

計画されている機能（docs/roadmap.mdより）：

- [ ] 追加言語サポート（Rust, Go, Python）
- [ ] 改善されたデバウンスアルゴリズム（適応型）
- [ ] ブランチ間の差分検索
- [ ] コミット履歴検索
- [ ] より高度なセマンティック検索
- [ ] LSP統合

## 結論

KIRIは、LLMにコードコンテキストを提供するための洗練された、本番環境対応のシステムです。その階層化アーキテクチャ、degrade-first設計、セキュリティ重視のアプローチにより、高速で信頼性が高く、多様な開発環境で使いやすいツールとなっています。

デーモンアーキテクチャとインクリメンタルインデックス化により、優れたパフォーマンス特性を実現し、包括的な言語サポートとMCPネイティブ統合により、現代の開発ワークフローにおいて非常に価値のあるツールとなっています。

## 参考リンク

- [公式ドキュメント](https://github.com/CAPHTECH/kiri/tree/main/docs)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [DuckDB](https://duckdb.org/)
- [tree-sitter](https://tree-sitter.github.io/)
