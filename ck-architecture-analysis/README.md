# ck (Semantic Code Search) - 内部構造と検索プロセス分析

## プロジェクト概要

**ck (seek)** は、Rust製のセマンティックコード検索ツールです。従来のgrepのようなキーワード検索に加えて、意味論的な理解に基づいたコード検索を提供します。「error handling」と検索すると、その正確な単語が含まれていなくても、try/catchブロック、エラーリターン、例外処理コードなどを発見できます。

- **リポジトリ**: https://github.com/BeaconBay/ck
- **バージョン**: 0.7.1
- **言語**: Rust (Edition 2024)
- **最小Rustバージョン**: 1.88.0

## アーキテクチャ概要

ckは、モジュール化されたRust workspaceとして構築されています:

```
ck/
├── ck-cli/          # CLIインターフェースとMCPサーバー
├── ck-tui/          # ターミナルユーザーインターフェース (ratatui)
├── ck-core/         # 共通型、設定、ユーティリティ
├── ck-engine/       # 検索エンジン (regex, semantic, hybrid)
├── ck-index/        # ファイルインデックス、ハッシング、サイドカー管理
├── ck-embed/        # テキスト埋め込みプロバイダー (FastEmbed, API)
├── ck-ann/          # 近似最近傍検索インデックス
├── ck-chunk/        # テキストセグメンテーション、言語対応パーサー
└── ck-models/       # モデルレジストリと設定管理
```

## 主要コンポーネント

### 1. ck-core: 共通型とユーティリティ

共通のデータ構造と設定を提供:

- **SearchOptions**: 検索パラメータ（クエリ、パス、モード、閾値など）
- **SearchResult**: 検索結果（ファイル、スパン、スコア、プレビュー）
- **Span**: コード内の位置情報（バイトオフセット、行番号）
- **Language**: サポート対象言語の列挙型
- **FileMetadata**: ファイルメタデータ（ハッシュ、タイムスタンプ、サイズ）

### 2. ck-chunk: テキストセグメンテーション

コードをセマンティックに意味のあるチャンクに分割:

**主要機能**:
- Tree-sitterベースのASTパーシング
- 関数、クラス、メソッドレベルでのチャンク化
- モデル固有のトークン制限を考慮

**サポート言語**:
- Python, JavaScript/TypeScript, Rust, Go, Ruby, Haskell, C#, Zig

**チャンク設定** (`get_model_chunk_config`):
```rust
// 小型モデル (bge-small-en-v1.5)
target_tokens: 400, overlap: 80 (20%)

// 大型コンテキストモデル (nomic-v1.5, jina-code)
target_tokens: 1024, overlap: 200 (20%)
```

**チャンク構造**:
```rust
pub struct Chunk {
    pub span: Span,              // ファイル内の位置
    pub text: String,            // チャンクのテキスト
    pub chunk_type: ChunkType,   // Function, Class, Method, etc.
    pub stride_info: Option<...>,
    pub metadata: ChunkMetadata, // ancestry, breadcrumb, trivia
}
```

### 3. ck-embed: テキスト埋め込み

テキストをベクトル埋め込みに変換:

**埋め込みモデル**:
- **bge-small** (デフォルト): 400トークンチャンク、高速インデックス化
- **nomic-v1.5**: 1024トークンチャンク、8Kモデル容量
- **jina-code**: 1024トークンチャンク、コード特化型

**主要機能**:
- FastEmbed統合（ローカル実行、オフライン対応）
- HuggingFaceトークナイザーによる正確なトークンカウント
- リランキングサポート（jina-reranker, bge-reranker）

### 4. ck-index: インデックス管理

効率的なインデックス構造とキャッシング:

**インデックス構造**:
```
project/
├── src/
├── docs/
└── .ck/                    # セマンティックインデックス
    ├── manifest.json       # インデックスメタデータ
    ├── embeddings.json     # （従来形式）
    ├── ann_index.bin       # （従来形式）
    ├── tantivy_index/      # 字句検索インデックス
    └── [sidecar files]/    # ファイルごとの .ck ファイル
```

**サイドカーファイル (.ck)**:
各ソースファイルに対応するサイドカーファイルが `.ck/` ディレクトリに作成されます:

```rust
pub struct IndexEntry {
    pub metadata: FileMetadata,  // ハッシュ、タイムスタンプ、サイズ
    pub chunks: Vec<ChunkEntry>, // チャンクと埋め込み
}

pub struct ChunkEntry {
    pub span: Span,
    pub embedding: Option<Vec<f32>>,
    pub chunk_type: Option<String>,
    pub breadcrumb: Option<String>,
    pub ancestry: Option<Vec<String>>,
    pub chunk_hash: Option<String>,  // 増分インデックス用
    // ... その他のメタデータ
}
```

**増分インデックス化** (Chunk-Level Caching):
- Blake3ハッシュベースの変更検出
- チャンクレベルでの埋め込み再利用（80-90%キャッシュヒット率）
- `chunk_hash = blake3(text + leading_trivia + trailing_trivia)`
- モデル一貫性チェック（埋め込みの破損を防止）

### 5. ck-engine: 検索エンジン

4つの検索モードを実装:

#### A. Regex検索 (`regex_search`)

従来のgrep互換検索:

**処理フロー**:
1. パターンをRegexにコンパイル（大文字小文字、固定文字列、単語境界オプション）
2. ファイル収集（再帰的、.gitignore/.ckignore尊重）
3. 並列検索（Rayon使用）
4. バイトオフセットと行番号の正確な計算
5. コンテキスト行の抽出（-A, -B, -C オプション）

**最適化**:
- ストリーミング検索（シンプルケース）
- インメモリ検索（コンテキストやセクション抽出が必要な場合）
- 異なる改行コード対応（\n, \r\n, \r）

#### B. Lexical検索 (`lexical_search`)

Tantivyベースの全文検索:

**処理フロー**:
1. Tantivyインデックス作成/オープン
2. クエリパース
3. BM25スコアリング
4. スコア正規化（0-1範囲）
5. 閾値フィルタリング

#### C. Semantic検索 (`semantic_search_v3`)

ベクトル埋め込みベースの意味論的検索:

**処理フロー**:
```
1. インデックスルート検出
   └─ 最も近い .ck ディレクトリを検索

2. サイドカーファイルからの埋め込みロード
   ├─ .ck/*.ck ファイルをウォーク
   ├─ IndexEntry を逆シリアライズ
   ├─ 元のファイルパスを再構築
   └─ embedding を持つチャンクを収集

3. クエリ埋め込み生成
   ├─ モデル解決（manifest.json から）
   ├─ Embedder 作成
   └─ クエリをベクトル化

4. 類似度計算
   ├─ コサイン類似度計算
   │   cosine_sim = dot(a, b) / (||a|| * ||b||)
   └─ スコアでソート（降順）

5. フィルタリングと結果抽出
   ├─ 閾値フィルタリング
   ├─ top_k 制限
   ├─ パスフィルター適用
   ├─ スパンからコンテンツ抽出
   └─ SearchResult 構築

6. （オプション）リランキング
   ├─ リランカーモデルロード (jina/bge)
   ├─ クエリとドキュメントでリランク
   └─ スコア更新とソート
```

**コサイン類似度実装**:
```rust
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot_product / (norm_a * norm_b)
    }
}
```

**パス再構築**:
サイドカーファイルパスから元のファイルパスを復元:
```
.ck/src/main.rs.ck → src/main.rs
```

#### D. Hybrid検索 (`hybrid_search`)

RegexとSemanticを組み合わせた検索:

**処理フロー**:
1. Regex検索実行
2. Semantic検索実行
3. Reciprocal Rank Fusion (RRF) でスコア統合
4. 閾値フィルタリング
5. top_k 制限

**RRFスコアリング**:
```rust
// k = 60 (論文の標準値)
RRFscore(d) = Σ(r∈R) 1/(k + r(d))

// 例:
// Regex順位: 3位, Semantic順位: 5位
// RRF = 1/(60+3) + 1/(60+5) = 0.0159 + 0.0154 = 0.0313
```

## 検索プロセスの詳細フロー

### セマンティック検索の完全フロー

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ユーザークエリ: "error handling"                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. インデックス自動更新チェック                              │
│    - find_nearest_index_root()                              │
│    - manifest.json 確認                                     │
│    - 必要に応じて ensure_index_updated() 実行               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 埋め込みロード (semantic_search_v3)                       │
│    WalkDir .ck/ ディレクトリ                                │
│    ├─ *.ck ファイルを検出                                   │
│    ├─ load_index_entry() で IndexEntry 読み込み            │
│    ├─ reconstruct_original_path() でパス復元                │
│    └─ embedding を持つチャンクを file_chunks に収集         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. モデル解決とロード                                        │
│    - resolve_model_from_root()                              │
│    - manifest.json から embedding_model 読み込み            │
│    - create_embedder() で FastEmbed インスタンス化          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. クエリ埋め込み生成                                        │
│    embedder.embed(&["error handling"])                      │
│    → Vec<f32> (次元: 384 for bge-small, 768 for nomic)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 類似度計算                                                │
│    for each (file_path, chunk) in file_chunks:             │
│        similarity = cosine_similarity(                      │
│            query_embedding,                                 │
│            chunk.embedding                                  │
│        )                                                    │
│        similarities.push((similarity, file_path, chunk))   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. ソートとフィルタリング                                    │
│    - similarities.sort_by(スコア降順)                        │
│    - threshold フィルタリング (例: >= 0.7)                   │
│    - top_k 制限適用 (例: 上位10件)                          │
│    - path フィルタ (ディレクトリ/ファイル指定時)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. コンテンツ抽出                                            │
│    for each (similarity, file_path, chunk):                │
│        content = extract_content_from_span(                 │
│            file_path,                                       │
│            chunk.span  // line_start, line_end             │
│        )                                                    │
│        // ファイルから該当行をストリーミング読み込み         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. SearchResult 構築                                        │
│    SearchResult {                                           │
│        file: PathBuf,                                       │
│        span: Span { line_start, line_end, ... },           │
│        score: f32,  // 0.0 - 1.0                           │
│        preview: String,  // 抽出したコード                  │
│        lang: Language,                                      │
│        ...                                                  │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. （オプション）リランキング                               │
│     if options.rerank:                                      │
│         reranker.rerank(query, [result.preview, ...])      │
│         // スコア更新と再ソート                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 11. 結果返却                                                │
│     SearchResults {                                         │
│         matches: Vec<SearchResult>,                         │
│         closest_below_threshold: Option<SearchResult>,      │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
```

### インデックス化プロセス

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ファイル収集                                              │
│    - WalkBuilder (respect .gitignore, .ckignore)           │
│    - is_text_file() でバイナリ除外                          │
│    - exclude_patterns 適用                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 各ファイルのチャンク化                                    │
│    chunk_text(content, language)                            │
│    ├─ Tree-sitter パース (言語別)                           │
│    ├─ AST走査で関数/クラス抽出                              │
│    ├─ トークン制限チェック                                  │
│    └─ Chunk 構造体生成                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 増分インデックス判定                                      │
│    既存 .ck ファイル読み込み                                │
│    for each chunk:                                          │
│        new_hash = blake3(text + trivia)                     │
│        if new_hash == old_chunk.chunk_hash:                │
│            embedding を再利用 (キャッシュヒット)            │
│        else:                                                │
│            新規埋め込み生成が必要                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 埋め込み生成                                              │
│    embedder.embed([chunk.text, ...])                        │
│    ├─ バッチ処理で効率化                                    │
│    ├─ 進捗コールバック                                      │
│    └─ Vec<Vec<f32>> 取得                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. サイドカーファイル保存                                    │
│    IndexEntry {                                             │
│        metadata: FileMetadata { hash, mtime, size },       │
│        chunks: Vec<ChunkEntry {                            │
│            span, embedding, chunk_type,                     │
│            breadcrumb, ancestry, chunk_hash, ...           │
│        }>                                                   │
│    }                                                        │
│    → .ck/path/to/file.ext.ck に保存 (JSON)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. マニフェスト更新                                          │
│    manifest.json 更新:                                      │
│    - files: HashMap<PathBuf, FileMetadata>                 │
│    - embedding_model: String                                │
│    - embedding_dimensions: usize                            │
│    - chunk_hash_version: u32                                │
│    - updated: timestamp                                     │
└─────────────────────────────────────────────────────────────┘
```

## 主要な最適化技術

### 1. チャンクレベル増分インデックス化

従来のファイルレベルではなく、チャンクレベルでの変更検出:

**利点**:
- 80-90%のキャッシュヒット率（典型的なコード変更時）
- ファイルの一部変更時も大部分の埋め込みを再利用
- Blake3ハッシュによる高速変更検出

**ハッシュ計算**:
```rust
chunk_hash = blake3(
    chunk.text +
    chunk.leading_trivia +  // コメント、空白
    chunk.trailing_trivia
)
```

ドキュメントコメントや空白の変更も正しく検出します。

### 2. ストリーミングファイル読み込み

**extract_lines_from_file()**: 必要な行だけを読み込み
```rust
// 行3-5だけを抽出（1ベースインデックス）
let content = extract_lines_from_file(path, 3, 5)?;
// → "Line 3\nLine 4\nLine 5"
```

**メモリ効率**:
- 大きなファイルでも全体をロードしない
- BufReader でストリーミング読み込み
- 必要な行を超えたら即座に停止

### 3. 並列処理

**Rayonを使用した並列検索**:
```rust
let results: Vec<Vec<SearchResult>> = files
    .par_iter()  // 並列イテレータ
    .filter_map(|file| search_file(regex, file, options))
    .collect();
```

### 4. スマートファイルフィルタリング

**複数レイヤーの除外**:
1. `.gitignore` - バージョン管理除外
2. `.ckignore` - 検索除外（画像、動画、設定ファイルなど）
3. `--exclude` パターン - カスタム除外
4. バイナリ自動検出（ripgrep スタイル）

## パフォーマンス特性

**実際のコードベースでのテスト結果**:

- **インデックス化**: ~1M LOC を2分未満
- **増分インデックス**: 80-90%キャッシュヒット率
- **検索**: 典型的なコードベースで500ms未満
- **インデックスサイズ**: ソースコードの約2倍（圧縮あり）
- **メモリ**: 大規模リポジトリでも効率的なストリーミング

## 技術スタック

### 主要な依存関係

```toml
# 検索とインデックス化
tantivy = "0.24"          # 全文検索エンジン
tree-sitter = "0.25"      # AST パーサー
regex = "1.10"            # 正規表現

# 埋め込みとML
fastembed = "5.1"         # FastEmbed統合
onnxruntime               # (FastEmbedが使用)

# 並列処理とファイル処理
rayon = "1.8"             # データ並列処理
walkdir = "2.4"           # ディレクトリ走査
ignore = "0.4"            # .gitignore サポート

# ハッシングとシリアライゼーション
blake3 = "1.5"            # 高速ハッシュ関数
serde = "1.0"             # シリアライゼーション
bincode = "1.3"           # バイナリエンコーディング

# CLI とTUI
clap = "4.4"              # CLI パーサー
ratatui                   # TUI フレームワーク
```

## まとめ

ckの検索プロセスは、以下の要素が統合されています:

1. **モジュール化されたアーキテクチャ**: 各コンポーネントが明確な責務を持つ
2. **効率的なインデックス化**: チャンクレベルの増分更新とキャッシング
3. **柔軟な検索モード**: Regex, Lexical, Semantic, Hybrid
4. **最適化された実装**: 並列処理、ストリーミング、スマートフィルタリング
5. **オフライン動作**: 完全にローカルで動作、ネットワーク不要

この設計により、大規模なコードベースでも高速で正確なセマンティック検索が可能になっています。
