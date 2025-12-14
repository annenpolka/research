# ck モデル対応調査

## 概要

このドキュメントは、BeaconBay/ckプロジェクトがサポートしている埋め込みモデルについての調査結果をまとめたものです。

**ckとは：** ローカルファーストのセマンティック・ハイブリッドコード検索ツール。「意味で検索するgrep」として、キーワードではなく概念に基づいてコードを発見できます。

## 調査結果：対応モデル

ckは**4つの埋め込みモデル**をサポートしています。すべてローカルで動作し、外部サービスへのネットワーク呼び出しは不要です。

### モデル名のハードコーディング状況

**結論：モデル名はハードコードされています**

ソースコード分析の結果、以下が判明しました：

#### 実装の詳細（`ck-models/src/lib.rs`）

```rust
// ModelConfig構造体で各モデルの仕様を定義
pub struct ModelConfig {
    pub name: String,           // モデルの正式名称
    pub provider: String,       // プロバイダー（fastembed等）
    pub dimensions: usize,      // 埋め込みベクトルの次元数
    pub max_tokens: usize,      // 処理可能な最大トークン数
    pub description: String,    // モデルの説明文
}

// HashMap<String, ModelConfig>でモデルを管理
models.insert("bge-small".to_string(), ModelConfig { ... });
models.insert("minilm".to_string(), ModelConfig { ... });
models.insert("nomic-v1.5".to_string(), ModelConfig { ... });
models.insert("jina-code".to_string(), ModelConfig { ... });
```

#### FastEmbed連携（`ck-embed/src/lib.rs`）

モデル名は**マッチ式で固定的に定義**されています：

```rust
match model_name {
    "BAAI/bge-small-en-v1.5" => EmbeddingModel::BGESmallENV15,
    "nomic-embed-text-v1.5" => EmbeddingModel::NomicEmbedTextV15,
    "jina-embeddings-v2-base-code" => EmbeddingModel::JinaEmbeddingsV2BaseCode,
    _ => EmbeddingModel::NomicEmbedTextV15  // デフォルトフォールバック
}
```

#### 設定の柔軟性

**部分的に設定可能**です：

1. **JSONファイルからの読み込み**: `ModelRegistry::load(path)` メソッドでJSONから設定を読み込める
2. **プロジェクト単位の設定**: `ProjectConfig` で使用モデルを指定できる
3. **制限事項**: 新しいモデルを追加するには**ソースコードの変更が必要**

#### カスタムモデル追加の難易度

**高い**。以下の変更が必要：
- `ck-models/src/lib.rs` の HashMap にモデルを追加
- `ck-embed/src/lib.rs` のマッチ式に新しいパターンを追加
- FastEmbed の `EmbeddingModel` enum に対応する値を確認
- 再コンパイルが必要

現時点では、ユーザーが独自のモデルを動的に追加する仕組みは提供されていません。

### 1. BGE-Small（デフォルト）

**技術仕様：**
- モデル名：BAAI/bge-small-en-v1.5
- チャンクサイズ：400トークン
- モデル容量：512トークン
- 次元数：384
- ファイルサイズ：約80MB

**パフォーマンス（100万LOCベース）：**
- インデックス時間：約2分
- ディスク使用量：約200MB
- 検索速度：400～600ms

**特徴：**
- ✅ 最速のインデックス作成
- ✅ 小さいダウンロードサイズ
- ✅ 低メモリ使用量
- ❌ 大規模関数は分割される
- ❌ 小さいコンテキストウィンドウ

**推奨用途：** 小規模コードベース、迅速な反復作業

### 2. Nomic V1.5

**技術仕様：**
- チャンクサイズ：1024トークン
- モデル容量：8192トークン
- 次元数：768
- ファイルサイズ：約500MB

**パフォーマンス（100万LOCベース）：**
- インデックス時間：約4分
- ディスク使用量：約400MB
- 検索速度：400～600ms

**特徴：**
- ✅ 大規模コンテキストウィンドウ（8K）
- ✅ ドキュメント処理に優れる
- ✅ 強いセマンティック理解
- ❌ インデックス速度がやや遅い
- ❌ 大きなダウンロードサイズ

**推奨用途：** 大規模プロジェクト、ドキュメント豊富なコード

### 3. Jina Code

**技術仕様：**
- チャンクサイズ：1024トークン
- モデル容量：8192トークン
- 次元数：768
- ファイルサイズ：約500MB

**パフォーマンス（100万LOCベース）：**
- インデックス時間：約4分
- ディスク使用量：約400MB
- 検索速度：400～600ms

**特徴：**
- ✅ コード専門化モデル
- ✅ プログラミング言語理解に最適化
- ✅ 大規模コンテキスト（8K）
- ❌ インデックス速度がやや遅い
- ❌ 大きなダウンロードサイズ

**推奨用途：** コード固有の検索、APIシグネチャ、リファクタリング

### 4. MiniLM（補助モデル）

**技術仕様：**
- モデル名：sentence-transformers/all-MiniLM-L6-v2
- モデル容量：256トークン
- 次元数：384
- ファイルサイズ：小型

**特徴：**
- ✅ 軽量な英語埋め込みモデル
- ✅ 非常に高速
- ❌ コンテキストウィンドウが最小（256トークン）
- ❌ コード特化ではない

**推奨用途：** 非常に小規模なプロジェクト、実験用途

**注：** ドキュメントには3つのモデルのみ記載されていますが、ソースコードには4つ目のモデル（minilm）も定義されています。

## モデルの使用方法

### インデックス作成時にモデルを指定

```bash
ck --index --model bge-small .
ck --index --model minilm .
ck --index --model nomic-v1.5 .
ck --index --model jina-code .
```

### モデル切り替え

```bash
# 通常の切り替え（データ保持）
ck --switch-model nomic-v1.5 .

# 強制的に再構築
ck --switch-model nomic-v1.5 --force .
```

### インデックス状態確認

```bash
ck --status .
```

### クリーンアップと再構築

```bash
ck --clean .
```

## 技術的詳細

### FastEmbedとの統合

ckは[FastEmbed](https://github.com/qdrant/fastembed)を使用しており、FastEmbedがサポートする幅広いモデルにアクセス可能です。

**FastEmbedの特徴：**
- 高速で正確な埋め込み生成
- 複数のモデルタイプをサポート（dense, sparse, late interaction, image, reranking）
- 完全にローカルで動作

### キャッシング戦略

- **トークン計数：** HuggingFace tokenizersを使用
- **ハッシュアルゴリズム：** blake3ベースの内容認識キャッシング
- **モデル整合性保護：** モデル切り替え時の埋め込み破損を防止
- **キャッシュ保存先：**
  - Linux/macOS: `~/.cache/ck/models/`
  - Windows: プラットフォーム固有のディレクトリ

### 自動デルタインデックス

- チャンクレベルのキャッシング
- スマートファイルフィルタリング（.gitignore、.ckignore対応）
- 内容認識による変更検出

## 対応プログラミング言語

- Python
- JavaScript/TypeScript
- Rust
- Go
- Ruby
- Haskell
- C#
- Zig
- テキストフォーマット（Markdown, JSON, YAML等）

## MCP（Model Context Protocol）統合

ckはMCPサーバー機能を提供し、Claude Desktop、Cursor等のAIクライアントと統合可能です。

**利用可能なMCPツール：**
- `semantic_search` - セマンティック検索
- `regex_search` - 正規表現検索
- `hybrid_search` - ハイブリッド検索（Reciprocal Rank Fusion使用）
- `index_status` - インデックス状態確認
- `reindex` - 再インデックス
- `health_check` - ヘルスチェック

## ユーザーインターフェース

### 1. インタラクティブTUI
- 複数の検索モード
- シンタックスハイライト
- プレビューオプション
- エディタ統合

### 2. CLI
- 従来のgrep互換コマンドライン
- スクリプトや自動化に適している

### 3. JSONL/JSON出力
- 構造化されたデータフォーマット
- AIエージェントとの統合向け

## インストール

```bash
cargo install ck-search
```

将来的にはhomebrewとaptパッケージもサポート予定。

## 結論

### 主な発見

1. **4つのモデルをサポート**：ckは用途に応じた埋め込みモデルを提供
   - 超軽量・実験用：MiniLM
   - 小規模・高速：BGE-Small（デフォルト）
   - 大規模・ドキュメント重視：Nomic V1.5
   - コード専門：Jina Code

2. **モデル名はハードコード**：ソースコード内でモデルが固定定義されており、カスタムモデルの追加には再コンパイルが必要

3. **完全なローカル実行**：全モデルがローカルで動作し、プライバシーとセキュリティを確保

4. **部分的な設定の柔軟性**：JSONファイルからモデル設定を読み込めるが、新規モデル追加はソースコード変更が必要

5. **FastEmbed統合**：FastEmbedベースの実装だが、FastEmbedの全モデルが使えるわけではない

6. **MCP対応**：最新のAIワークフローとの統合が容易

### 推奨事項

**用途別のモデル選択：**
- 個人プロジェクト、迅速なプロトタイピング → **BGE-Small**
- 大規模企業コードベース、ドキュメント充実 → **Nomic V1.5**
- コード固有の高度な検索、リファクタリング → **Jina Code**

**パフォーマンス最適化：**
- 初回のインデックス作成には時間がかかるが、デルタインデックスにより更新は高速
- モデルは一度ダウンロードされれば永続的にキャッシュされる
- プロジェクトサイズに応じてモデルを選択することでバランスを最適化

## 参考資料

- [GitHub - BeaconBay/ck](https://github.com/BeaconBay/ck)
- [ck公式ドキュメント](https://beaconbay.github.io/ck/)
- [FastEmbed](https://github.com/qdrant/fastembed)
- [FastEmbed Supported Models](https://qdrant.github.io/fastembed/examples/Supported_Models/)

## メタ情報

- **調査日：** 2025-12-14
- **ck バージョン：** 最新版（2025年時点、mainブランチ）
- **調査方法：**
  - 公式ドキュメント分析
  - GitHub READMEレビュー
  - **ソースコード分析**（`ck-models/src/lib.rs`、`ck-embed/src/lib.rs`）
  - Web検索
