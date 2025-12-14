# Semtools 検索プロセス調査

## 概要

このプロジェクトは、[run-llama/semtools](https://github.com/run-llama/semtools)のセマンティック検索機能の内部実装を調査し、その検索プロセスを詳細に説明するものです。

## 動機

Semtoolsは、コマンドラインから高速にセマンティック検索を実行できる強力なツールですが、その内部実装の詳細はドキュメントでは明確ではありません。このプロジェクトでは、ソースコードを詳細に分析し、検索プロセスがどのように機能するかを理解することを目的としています。

## Semtoolsとは

Semtoolsは、Rustで構築された高性能なCLIツール集で、以下の機能を提供します：

- **parse**: ドキュメント（PDF、DOCXなど）をLlamaParseを使用してMarkdown形式に変換
- **search**: 多言語エンベディングを使用したローカルセマンティック検索
- **ask**: ドキュメントコレクションに対して質問に答えるAIエージェント
- **workspace**: 大規模コレクションに対する検索を高速化するワークスペース管理

## 技術スタック

### 主要な依存関係

- **model2vec-rs**: 高速エンベディング生成ライブラリ
- **minishlab/potion-multilingual-128M**: 多言語対応の128次元静的エンベディングモデル
- **simsimd**: 効率的な類似度計算（コサイン類似度）
- **LanceDB**: ベクトルストレージとANN（近似最近傍）検索用のデータベース

## 検索プロセスの詳細

Semtoolsの検索機能には2つのモードがあります：

### 1. 基本検索モード（ワークスペースなし）

**ファイル**: `src/search/mod.rs`, `src/bin/search.rs`

#### 処理フロー

1. **モデルのロード**
   ```rust
   StaticModel::from_pretrained("minishlab/potion-multilingual-128M", ...)
   ```
   - Hugging Faceから事前学習済みモデルをダウンロード・ロード
   - 128次元のベクトル空間を使用

2. **ドキュメントの準備** (`create_document_from_content`)
   - ファイルを行単位で分割
   - オプション: 大文字小文字を無視する場合は小文字に変換
   - 各行をモデルでエンコード:
     ```rust
     model.encode_with_args(&lines_for_embedding, Some(2048), 16384)
     ```

3. **クエリのエンコード**
   ```rust
   let query_embedding = model.encode_single(query)
   ```

4. **類似度検索** (`search_documents`)
   - 各ドキュメントの各行のエンベディングとクエリエンベディングのコサイン距離を計算:
     ```rust
     let distance = f32::cosine(query_embedding, line_embedding)
     ```
   - 距離が閾値未満の結果を収集
   - コンテキスト行を含める（前後n行）:
     ```rust
     let bottom_range = max(0, idx.saturating_sub(config.n_lines));
     let top_range = min(doc.lines.len(), idx + config.n_lines + 1);
     ```

5. **結果のランキングと返却**
   - 距離でソート（小さいほど類似）
   - `max_distance`が指定されている場合：閾値未満のすべての結果を返す
   - そうでない場合：`top_k`件の結果のみを返す

#### SearchConfig パラメータ

- `n_lines`: マッチした行の前後に含めるコンテキスト行数（デフォルト: 3）
- `top_k`: 返す結果の最大数（デフォルト: 3）
- `max_distance`: 距離の閾値（指定された場合、top_kは無視される）
- `ignore_case`: 大文字小文字を無視するか（デフォルト: false）

### 2. ワークスペースモード（高速化）

**ファイル**: `src/workspace/store.rs`, `src/workspace/mod.rs`

ワークスペースモードは、大規模なドキュメントコレクションに対する検索を高速化します。

#### 処理フロー

1. **ワークスペースの初期化**
   ```bash
   workspace use my-workspace
   export SEMTOOLS_WORKSPACE=my-workspace
   ```
   - ワークスペースは `~/.semtools/workspaces/<name>` に保存される
   - LanceDBデータベースが `documents.lance` として作成される

2. **ドキュメント状態の分析** (`analyze_document_states`)
   - 各ファイルのメタデータ（サイズ、更新時刻、エンベディングバージョン）を確認
   - ファイルを3つの状態に分類:
     - **New**: ワークスペースに存在しないファイル
     - **Changed**: メタデータが変更されたファイル
     - **Unchanged**: 変更されていないファイル

3. **エンベディングの更新**
   - 新規または変更されたファイルのみエンベディングを生成
   - 行単位でエンベディングを生成し、LanceDBに保存:
     ```rust
     LineEmbedding {
         path: filename,
         line_number: idx,
         embedding: vector,
     }
     ```

4. **LanceDBへの保存** (`upsert_line_embeddings`)
   - 行エンベディングを `line_embeddings` テーブルに保存
   - スキーマ:
     - `id`: 行の一意識別子（path + line_numberのハッシュ）
     - `path`: ファイルパス
     - `line_number`: 行番号（0始まり）
     - `vector`: 128次元のf32ベクトル

5. **ベクトルインデックスの作成** (`ensure_line_vector_index`)
   - LanceDBがベクトル列にIVF_PQインデックスを自動作成
   - 256行以上必要（それ未満の場合はブルートフォース検索）
   - インデックスがあると検索が高速化される

6. **検索の実行** (`search_line_embeddings`)
   - LanceDBのベクトル検索機能を使用:
     ```rust
     tbl.query()
        .only_if(filter_expr)  // ファイルパスでフィルタリング
        .nearest_to(query_vec)  // ANN検索
        .distance_type(DistanceType::Cosine)
        .limit(top_k)
     ```
   - 結果を距離でソート
   - 上位k件を返す

#### ワークスペースの利点

1. **増分更新**: 変更されたファイルのみ再エンベディング
2. **永続化**: エンベディングがディスクに保存され、再利用可能
3. **高速検索**: LanceDBのベクトルインデックスによるANN検索
4. **大規模対応**: 数千〜数万のドキュメントでも高速

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                     Search CLI (search.rs)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴────────────┐
                │                        │
        ┌───────▼───────┐        ┌──────▼─────────┐
        │ Basic Mode    │        │ Workspace Mode │
        │ (In-Memory)   │        │  (Persistent)  │
        └───────┬───────┘        └──────┬─────────┘
                │                       │
        ┌───────▼──────────┐    ┌──────▼──────────┐
        │ search_files     │    │ Workspace::open │
        │ - Load files     │    │ - Load config   │
        │ - Create docs    │    │ - Open LanceDB  │
        └───────┬──────────┘    └──────┬──────────┘
                │                       │
        ┌───────▼──────────┐    ┌──────▼──────────────────────┐
        │ create_document_ │    │ analyze_document_states     │
        │ from_content     │    │ - Check metadata            │
        │ - Split lines    │    │ - Classify: New/Changed/    │
        │ - Encode lines   │    │   Unchanged                 │
        └───────┬──────────┘    └──────┬──────────────────────┘
                │                       │
        ┌───────▼──────────┐    ┌──────▼──────────────────────┐
        │ search_documents │    │ upsert_line_embeddings      │
        │ - Cosine dist.   │    │ - Generate embeddings       │
        │ - Filter by      │    │ - Save to LanceDB           │
        │   threshold      │    │ - Create/update index       │
        │ - Sort & rank    │    └──────┬──────────────────────┘
        └───────┬──────────┘            │
                │                ┌──────▼──────────────────────┐
                │                │ search_line_embeddings      │
                │                │ - ANN search via LanceDB    │
                │                │ - Filter by paths           │
                │                │ - Cosine distance           │
                │                │ - Sort & return top-k       │
                │                └──────┬──────────────────────┘
                │                       │
        ┌───────▼───────────────────────▼──────────────────────┐
        │           Print Results (with context lines)         │
        └──────────────────────────────────────────────────────┘
```

## データフロー

### Basic Mode

```
Input Files → Split into Lines → Encode with model2vec
                                         ↓
Query → Encode → Compute Cosine Distance with all lines
                                         ↓
                        Filter by threshold/top-k → Results
```

### Workspace Mode

```
Input Files → Check metadata in LanceDB
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
   Changed/New              Unchanged
        ↓                         ↓
   Re-encode lines          Skip encoding
        ↓                         ↓
   Save to LanceDB ───────────────┘
                     ↓
Query → Encode → ANN Search in LanceDB → Results
```

## コード例

### 基本検索

```rust
// ファイルから検索
let results = search_files(
    &vec!["file1.txt", "file2.txt"],
    "some query",
    &model,
    &SearchConfig {
        n_lines: 3,
        top_k: 5,
        max_distance: Some(0.5),
        ignore_case: false,
    }
)?;

// 結果を表示
for result in results {
    println!("{} (distance: {})", result.filename, result.distance);
    for (i, line) in result.lines.iter().enumerate() {
        println!("  {}: {}", result.start + i, line);
    }
}
```

### ワークスペース検索

```rust
// ワークスペースモード
let workspace = Workspace::open()?;
let store = Store::open(&workspace.config.root_dir).await?;

let ranked_lines = search_with_workspace(
    &files,
    "query",
    &model,
    &config
).await?;

// 結果にはpath、line_number、distanceが含まれる
for line in ranked_lines {
    println!("{} line {}: {}", line.path, line.line_number, line.distance);
}
```

## パフォーマンス特性

### 基本モード

- **利点**: シンプル、セットアップ不要
- **欠点**: 毎回すべてのファイルをエンコードする必要がある
- **適用場面**:
  - 小規模なファイル（数十〜数百）
  - 一度きりの検索
  - stdinからの入力

### ワークスペースモード

- **利点**:
  - 初回以降は変更されたファイルのみ再エンベディング
  - LanceDBのベクトルインデックスによる高速検索
  - 大規模コレクションでもスケール
- **欠点**:
  - 初回セットアップに時間がかかる
  - ディスクスペースが必要
- **適用場面**:
  - 大規模なファイルコレクション（数千〜数万）
  - 繰り返し検索を行う
  - プロジェクト全体の検索

## 主要な最適化技術

1. **Static Embeddings (model2vec)**
   - 事前計算されたモデルで高速
   - GPUが不要
   - 小さなモデルサイズ（128次元）

2. **Line-level Granularity**
   - 文書全体ではなく、行単位でエンベディング
   - より正確なマッチング
   - コンテキスト行で周辺情報を提供

3. **Incremental Updates**
   - ファイルメタデータでの変更検出
   - 変更されたファイルのみ更新

4. **Vector Indexing**
   - LanceDBのIVF_PQインデックス
   - O(n)からO(log n)への検索高速化

5. **Batch Processing**
   - 複数の行を一度にエンコード
   - 効率的なメモリ使用

## 結論

Semtoolsは、以下の技術を組み合わせることで、高速で正確なセマンティック検索を実現しています：

- **model2vec**: 軽量で高速な静的エンベディング
- **行単位の粒度**: より正確なマッチングと柔軟なコンテキスト
- **LanceDB**: 効率的なベクトルストレージとANN検索
- **インクリメンタル更新**: 大規模コレクションでのパフォーマンス最適化

ワークスペース機能により、開発者は数千のファイルに対して高速にセマンティック検索を実行できます。これは、大規模なコードベースやドキュメントコレクションを扱う際に特に有用です。

## 参考リンク

- [Semtools GitHub](https://github.com/run-llama/semtools)
- [model2vec-rs](https://github.com/MinishLab/model2vec-rs)
- [minishlab/potion-multilingual-128M](https://huggingface.co/minishlab/potion-multilingual-128M)
- [LanceDB](https://lancedb.com/)
- [simsimd](https://github.com/ashvardanian/simsimd)
