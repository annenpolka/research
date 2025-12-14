# ck 検索プロセス - 詳細フロー図

## セマンティック検索のデータフロー

### Phase 1: インデックス準備

```
User Query: "error handling"
         │
         ├──────────────────────────────────────────┐
         ↓                                          ↓
   [Auto-index check]                        [Manual index]
         │                                          │
         ↓                                          ↓
   find_nearest_index_root()              ck --index <path>
         │                                          │
         ├─→ .ck/ exists? ─NO→ create index        │
         │                                          │
         ├─→ files changed? ─YES→ update index     │
         │                                          │
         └──────────────────────────────────────────┘
                            ↓
                   Index ready (.ck/)
```

### Phase 2: 埋め込み収集

```
.ck/ Directory Structure:
├── manifest.json
│   ├── embedding_model: "nomic-embed-text-v1.5"
│   ├── embedding_dimensions: 768
│   └── files: HashMap<PathBuf, FileMetadata>
│
├── src/
│   ├── main.rs.ck
│   │   └── IndexEntry {
│   │         metadata: { hash, mtime, size },
│   │         chunks: [
│   │           ChunkEntry {
│   │             span: { line_start: 1, line_end: 10 },
│   │             embedding: [0.123, -0.456, ...],  // 768次元
│   │             chunk_type: "Function",
│   │             breadcrumb: "main::error_handler",
│   │             chunk_hash: "blake3..."
│   │           },
│   │           ...
│   │         ]
│   │       }
│   │
│   └── lib.rs.ck
│       └── IndexEntry { ... }
│
└── utils/
    └── helpers.rs.ck
        └── IndexEntry { ... }

Loading Process:
────────────────
WalkDir::new(".ck/")
    │
    ├─→ Find: src/main.rs.ck
    │   ├─→ load_index_entry()
    │   ├─→ reconstruct_original_path()
    │   │   └─→ "src/main.rs"
    │   └─→ Extract chunks with embeddings
    │       └─→ file_chunks.push((PathBuf, ChunkEntry))
    │
    ├─→ Find: src/lib.rs.ck
    │   └─→ ... (same process)
    │
    └─→ Find: utils/helpers.rs.ck
        └─→ ... (same process)
            ↓
    file_chunks: Vec<(PathBuf, ChunkEntry)>
```

### Phase 3: クエリ埋め込み生成

```
Query: "error handling"
         │
         ├─→ resolve_model_from_root()
         │   ├─→ Read manifest.json
         │   │   └─→ embedding_model: "nomic-embed-text-v1.5"
         │   │
         │   └─→ Validate model consistency
         │       ├─→ CLI --model matches manifest? ✓
         │       └─→ Dimensions match? ✓
         │
         ├─→ create_embedder(model_name)
         │   ├─→ Load FastEmbed model
         │   │   ├─→ Cache: ~/.cache/ck/models/
         │   │   └─→ Load ONNX runtime
         │   │
         │   └─→ Embedder ready
         │
         └─→ embedder.embed(["error handling"])
             ├─→ Tokenize
             │   └─→ [101, 7561, 11753, 102]  // BERT tokens
             │
             ├─→ Forward pass through model
             │   └─→ [batch_size=1, seq_len, hidden_dim]
             │
             └─→ Pooling (mean/CLS)
                 └─→ query_embedding: Vec<f32>  // 768次元
                     [0.234, -0.567, 0.891, ...]
```

### Phase 4: 類似度計算

```
For each chunk in file_chunks:
─────────────────────────────
Chunk 1: src/main.rs (lines 15-25)
    embedding: [0.123, -0.456, 0.789, ...]  // 768次元
    ↓
    cosine_similarity(query_embedding, chunk.embedding)
    │
    ├─→ dot_product = Σ(q[i] * c[i])
    │   = (0.234 * 0.123) + (-0.567 * -0.456) + ...
    │   = 145.678
    │
    ├─→ norm_q = sqrt(Σ(q[i]²))
    │   = sqrt(0.234² + 0.567² + ...)
    │   = 12.345
    │
    ├─→ norm_c = sqrt(Σ(c[i]²))
    │   = sqrt(0.123² + 0.456² + ...)
    │   = 11.234
    │
    └─→ similarity = dot_product / (norm_q * norm_c)
        = 145.678 / (12.345 * 11.234)
        = 0.834  ← High similarity!

Chunk 2: src/lib.rs (lines 42-58)
    embedding: [0.567, 0.234, -0.123, ...]
    ↓
    cosine_similarity(...)
    = 0.612  ← Medium similarity

Chunk 3: utils/helpers.rs (lines 10-20)
    embedding: [-0.234, 0.123, 0.456, ...]
    ↓
    cosine_similarity(...)
    = 0.234  ← Low similarity

Results:
────────
similarities: Vec<(f32, PathBuf, ChunkEntry)>
[
    (0.834, "src/main.rs", Chunk1),
    (0.612, "src/lib.rs", Chunk2),
    (0.234, "utils/helpers.rs", Chunk3),
    ...
]
```

### Phase 5: フィルタリングとランキング

```
Sort by similarity (descending):
────────────────────────────────
similarities.sort_by(|a, b| b.0.cmp(&a.0))
    ↓
[
    (0.834, "src/main.rs", lines 15-25),    ← Rank 1
    (0.612, "src/lib.rs", lines 42-58),     ← Rank 2
    (0.234, "utils/helpers.rs", lines 10-20) ← Rank 3
]

Apply Filters:
──────────────
1. Threshold Filter (--threshold 0.7)
   ├─→ 0.834 >= 0.7 ✓ Keep
   ├─→ 0.612 >= 0.7 ✗ Track as closest_below_threshold
   └─→ 0.234 >= 0.7 ✗ Drop

2. Top-K Filter (--topk 5)
   └─→ Take top 5 results

3. Path Filter (if specified)
   ├─→ File: only "src/main.rs"
   └─→ Directory: only files in "src/"

Filtered Results:
─────────────────
[
    (0.834, "src/main.rs", lines 15-25)
]
```

### Phase 6: コンテンツ抽出

```
For each result:
────────────────
Result: (0.834, "src/main.rs", Chunk {span: {line_start: 15, line_end: 25}})
    ↓
extract_content_from_span("src/main.rs", span)
    │
    ├─→ Open file for reading
    │   └─→ BufReader::new(File::open(...))
    │
    ├─→ Skip lines 1-14
    │   └─→ reader.lines().enumerate()
    │
    ├─→ Read lines 15-25
    │   └─→ Collect into Vec<String>
    │
    └─→ Join with newlines
        └─→ content: String
            ```
            fn handle_error(err: Error) -> Result<()> {
                match err {
                    Error::NotFound => log::warn!("Not found"),
                    Error::PermissionDenied => log::error!("Access denied"),
                    _ => log::error!("Unknown error: {:?}", err),
                }
                Ok(())
            }
            ```

Preview Generation:
───────────────────
if options.full_section:
    preview = content  // Full function
else:
    preview = content.lines().take(3).join("\n")
    // First 3 lines only

Result Construction:
────────────────────
SearchResult {
    file: PathBuf("src/main.rs"),
    span: Span {
        line_start: 15,
        line_end: 25,
        byte_start: 456,
        byte_end: 678,
    },
    score: 0.834,
    preview: "fn handle_error(err: Error) -> Result<()> {...}",
    lang: Language::Rust,
    symbol: None,
    chunk_hash: Some("blake3..."),
    index_epoch: None,
}
```

### Phase 7: リランキング（オプション）

```
if options.rerank:
──────────────────
Results: [
    SearchResult { score: 0.834, preview: "fn handle_error..." },
    SearchResult { score: 0.789, preview: "fn process_error..." },
    SearchResult { score: 0.756, preview: "fn log_error..." },
]
    ↓
Create Reranker:
────────────────
reranker = create_reranker("jina-reranker-v1-base-en")
    │
    └─→ Load reranker model (cross-encoder)
        ├─→ Different from bi-encoder embedders
        └─→ Takes (query, document) pairs

Rerank Process:
───────────────
reranker.rerank(
    query: "error handling",
    documents: [
        "fn handle_error...",
        "fn process_error...",
        "fn log_error...",
    ]
)
    ↓
For each (query, doc) pair:
────────────────────────────
├─→ Tokenize: [CLS] query [SEP] document [SEP]
├─→ Forward pass through cross-encoder
├─→ Get relevance score (0-1)
└─→ RerankerResult { document, score, index }

Reranked Results:
─────────────────
[
    { document: "fn handle_error...", score: 0.923, index: 0 },
    { document: "fn log_error...", score: 0.867, index: 2 },  ← Moved up!
    { document: "fn process_error...", score: 0.845, index: 1 },
]

Update Scores:
──────────────
results[0].score = 0.923
results[2].score = 0.867
results[1].score = 0.845

Sort Again:
───────────
results.sort_by(|a, b| b.score.cmp(&a.score))
```

### Phase 8: 結果返却

```
Final Results:
──────────────
SearchResults {
    matches: [
        SearchResult {
            file: "src/main.rs",
            span: { line_start: 15, line_end: 25 },
            score: 0.923,  // Reranked score
            preview: "fn handle_error(err: Error) -> Result<()> {...}",
            lang: Rust,
            ...
        },
        SearchResult {
            file: "src/error.rs",
            span: { line_start: 8, line_end: 12 },
            score: 0.867,
            preview: "fn log_error(msg: &str) {...}",
            lang: Rust,
            ...
        },
    ],
    closest_below_threshold: Some(
        SearchResult {
            file: "src/lib.rs",
            span: { line_start: 42, line_end: 58 },
            score: 0.612,  // Below threshold (0.7)
            preview: "fn process_error...",
            ...
        }
    ),
}
    ↓
Output Formatting:
──────────────────
if --json / --jsonl:
    └─→ JSON serialization
else if --scores:
    └─→ [0.923] src/main.rs:15: fn handle_error...
else:
    └─→ src/main.rs:15: fn handle_error...
```

## ハイブリッド検索の RRF フロー

```
Hybrid Search Flow:
───────────────────
Query: "async timeout"
    │
    ├─→ Regex Search
    │   ├─→ Pattern: "async.*timeout|timeout.*async"
    │   └─→ Results:
    │       1. src/network.rs:45 (rank 1)
    │       2. src/timeout.rs:12 (rank 2)
    │       3. src/main.rs:78 (rank 3)
    │
    ├─→ Semantic Search
    │   ├─→ Embedding: query → vector
    │   └─→ Results:
    │       1. src/timeout.rs:12 (rank 1)  ← Same file, different rank
    │       2. src/async.rs:34 (rank 2)    ← New file
    │       3. src/network.rs:45 (rank 3)  ← Same file, different rank
    │
    └─→ Reciprocal Rank Fusion (RRF)
        │
        ├─→ Combine by unique key: "file:line"
        │
        │   src/network.rs:45
        │   ├─→ Regex rank: 1
        │   ├─→ Semantic rank: 3
        │   └─→ RRF = 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323
        │
        │   src/timeout.rs:12
        │   ├─→ Regex rank: 2
        │   ├─→ Semantic rank: 1
        │   └─→ RRF = 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325 ← Highest!
        │
        │   src/main.rs:78
        │   ├─→ Regex rank: 3
        │   ├─→ Semantic rank: none
        │   └─→ RRF = 1/(60+3) = 0.0159
        │
        │   src/async.rs:34
        │   ├─→ Regex rank: none
        │   ├─→ Semantic rank: 2
        │   └─→ RRF = 1/(60+2) = 0.0161
        │
        └─→ Final ranking:
            1. src/timeout.rs:12 (RRF: 0.0325)  ← Best of both worlds!
            2. src/network.rs:45 (RRF: 0.0323)
            3. src/async.rs:34 (RRF: 0.0161)
            4. src/main.rs:78 (RRF: 0.0159)
```

## インデックス化の詳細フロー

```
Incremental Indexing:
─────────────────────
File: src/main.rs (modified)
    │
    ├─→ Read existing .ck/src/main.rs.ck
    │   └─→ old_index_entry: IndexEntry
    │
    ├─→ Chunk new content
    │   └─→ new_chunks: Vec<Chunk>
    │
    └─→ For each new_chunk:
        ├─→ Compute chunk_hash
        │   └─→ blake3(text + leading_trivia + trailing_trivia)
        │
        ├─→ Find matching old_chunk by span
        │
        │   ├─→ Match found?
        │   │   ├─→ Hashes equal?
        │   │   │   ├─→ YES: Reuse embedding ✓ (cache hit)
        │   │   │   └─→ NO: Generate new embedding (cache miss)
        │   │   │
        │   │   └─→ No match: Generate new embedding (new chunk)
        │   │
        │   └─→ ChunkEntry {
        │         span,
        │         embedding: Option<Vec<f32>>,
        │         chunk_hash: String,
        │         ...
        │       }
        │
        └─→ Save to .ck/src/main.rs.ck

Cache Hit Rate Example:
───────────────────────
File with 10 chunks:
├─→ 8 chunks unchanged → Reuse embeddings (80% hit rate)
└─→ 2 chunks modified → Generate new embeddings (20% miss rate)
```

## まとめ

このドキュメントでは、ckのセマンティック検索が以下のフェーズで動作することを詳細に説明しました:

1. **インデックス準備**: 自動更新チェックと増分インデックス化
2. **埋め込み収集**: サイドカーファイルからの効率的な読み込み
3. **クエリ埋め込み**: FastEmbedによるベクトル化
4. **類似度計算**: コサイン類似度による関連性評価
5. **フィルタリング**: 閾値、top-k、パスフィルタ
6. **コンテンツ抽出**: ストリーミング読み込みによる効率化
7. **リランキング**: クロスエンコーダーによる精度向上
8. **結果返却**: 構造化された検索結果

各フェーズは最適化され、大規模コードベースでも高速に動作します。
