# dev-manager-mcp 分析レポート

## 概要

**dev-manager-mcp** は、[BloopAI](https://github.com/bloopai) が開発した MCP (Model Context Protocol) サーバーで、開発サーバーを管理するためのデーモンです。

**リポジトリ**: https://github.com/bloopai/dev-manager-mcp

## 目的・ユースケース

このツールは以下の問題を解決します：

1. **複数の開発サーバーの並行実行**: AIコーディングツール（Claude Code, Cursor等）が自動テストツール（Playwright, Chrome DevTools MCP等）と連携する際に、複数の開発サーバーを同時に起動する必要がある
2. **ポート衝突の回避**: 同じポートを使おうとして開発サーバーが起動できない問題を自動的に解決
3. **アイドルセッションの自動クリーンアップ**: 120秒（デフォルト）のアイドル後に自動的にサーバーを停止

## アーキテクチャ

```
┌──────────────────────────────────────────────────────────────┐
│                     dev-manager-mcp                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────────────────────────┐    │
│  │   Daemon    │     │          STDIO Proxy            │    │
│  │  (HTTP/SSE) │◀───▶│  (MCPクライアント用ブリッジ)     │    │
│  │  Port 3009  │     │                                 │    │
│  └──────┬──────┘     └─────────────────────────────────┘    │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Manager                           │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │PortAllocator│  │ SessionMap  │  │  Sweeper   │  │    │
│  │  │  (3010〜)   │  │ (HashMap)   │  │ (5s周期)   │  │    │
│  │  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  ServerEntry                          │   │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │  Child  │  │  LogBuffer  │  │  LogBuffer      │  │   │
│  │  │ Process │  │  (stdout)   │  │  (stderr)       │  │   │
│  │  └─────────┘  │  512KB max  │  │  512KB max      │  │   │
│  │               └─────────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. main.rs - エントリーポイント

2つの実行モードを提供：

| モード | コマンド | 説明 |
|--------|----------|------|
| `daemon` | `dev-manager-mcp daemon` | HTTP/SSEサーバーとして起動（デフォルト） |
| `stdio` | `dev-manager-mcp stdio` | STDIOプロキシとしてデーモンに接続 |

### 2. lib.rs - 主要ロジック

- **run_daemon()**: SSEサーバーを起動し、MCPクライアントからの接続を受け付け
- **run_stdio_proxy()**: STDIO↔SSE間のブリッジを提供
- **inject_cwd_if_start_tool()**: `start`ツール呼び出し時にクライアントのCWDを自動注入

### 3. manager.rs - セッション管理

```rust
// 主要な機能
impl Manager {
    pub fn new(idle_timeout: Duration) -> Self;
    pub async fn start(&self, command: String, cwd: Option<String>) -> Value;
    pub async fn stop(&self, session_key: String) -> Value;
    pub fn status(&self, session_key: Option<String>) -> Value;
    pub fn tail(&self, session_key: String) -> Value;
}
```

**セッションキー**: 4文字の英数字（例: "A3X9", "K7M2"）
- 36^4 = 1,679,616通りの組み合わせ
- アクティブなセッション間でユニーク

**スイーパー**（バックグラウンドタスク）:
- 5秒ごとに実行
- アイドルタイムアウト（デフォルト120秒）を超えたセッションを停止
- 終了後600秒経過したセッションを完全に削除

### 4. service.rs - MCPツール定義

`rmcp` クレートのマクロを使用してMCPツールを定義：

```rust
#[tool_router]
impl DevManagerService {
    #[tool(description = "Start a development server...")]
    async fn start(&self, ...) -> Result<CallToolResult, ErrorData>;

    #[tool(description = "Stop a running development server session.")]
    async fn stop(&self, ...) -> Result<CallToolResult, ErrorData>;

    #[tool(description = "Get status of one or all development server sessions.")]
    async fn status(&self, ...) -> Result<CallToolResult, ErrorData>;

    #[tool(description = "Get stdout/stderr logs for a development server session.")]
    async fn tail(&self, ...) -> Result<CallToolResult, ErrorData>;
}
```

### 5. port_allocator.rs - ポート管理

- 開始ポート: 3010
- シーケンシャルに割り当て
- 解放されたポートはフリーリストで再利用
- `TcpListener::bind()` で利用可能性をプローブ

### 6. log_buffer.rs - ログバッファ

- 最大512KB（`MAX_BYTES`）のリングバッファ
- 最大100行（`MAX_TAIL_LINES`）を返却
- 古いログは自動的に破棄

### 7. server_entry.rs - プロセス管理

- Unixでは `setsid()` でセッションリーダーとして起動
- 停止時は `SIGTERM` → 5秒待機 → `SIGKILL`
- Windowsでは `taskkill /T /F` を使用
- stdout/stderrを非同期でキャプチャ

## MCPツール

### start
開発サーバーを起動。

```json
// 入力
{
  "command": "npm run dev",
  "cwd": "/path/to/project"  // オプション、STDIOモードではクライアントCWDをデフォルト使用
}

// 出力
{
  "status": "started",
  "port": 3010,
  "session_key": "A3X9"
}
```

### stop
セッションを停止。

```json
// 入力
{ "session_key": "A3X9" }

// 出力
{ "status": "stopped", "session_key": "A3X9" }
```

### status
セッション状態を取得。

```json
// 入力（全セッション）
{}

// 入力（特定セッション）
{ "session_key": "A3X9" }

// 出力
{
  "sessions": [
    { "session_key": "A3X9", "port": 3010, "running": true }
  ]
}
```

### tail
ログを取得。

```json
// 入力
{ "session_key": "A3X9" }

// 出力
{
  "session_key": "A3X9",
  "stdout": "Server started on port 3010...",
  "stderr": ""
}
```

## 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Rust (Edition 2021) |
| 非同期ランタイム | Tokio |
| MCPプロトコル | rmcp 0.8 |
| CLI | clap 4 |
| シリアライズ | serde + serde_json |
| スキーマ生成 | schemars |
| npmラッパー | Node.js (adm-zip) |

## 配布形態

### npx経由（推奨）
```bash
# デーモン起動
npx -y dev-manager-mcp

# MCPクライアント設定
{
  "mcpServers": {
    "dev-manager": {
      "command": "npx",
      "args": ["dev-manager-mcp", "stdio"]
    }
  }
}
```

### バイナリビルド
```bash
cargo build --release
./target/release/dev-manager-mcp daemon
```

## 対応プラットフォーム

- Linux x64 / ARM64
- Windows x64 / ARM64
- macOS x64 (Intel) / ARM64 (Apple Silicon)

## ユースケース例

1. **Playwright + 開発サーバー**
   - Claude Codeが`npm run dev`を起動
   - Playwright MCPが同じサーバーにアクセスしてE2Eテスト

2. **マルチプロジェクト開発**
   - フロントエンド（port 3010）とバックエンド（port 3011）を同時起動
   - 異なるセッションで独立管理

3. **Chrome DevTools MCP連携**
   - 開発サーバーを起動
   - Chrome DevTools MCPでデバッグ

## 設計上の特徴

1. **共有状態**: 複数のMCPクライアントが同じデーモンに接続し、セッションを共有可能
2. **自動クリーンアップ**: アイドルタイムアウトでリソースを自動解放
3. **PORT環境変数**: 起動コマンドに`PORT`環境変数を自動設定
4. **プロセスグループ管理**: Unixでは`setsid()`でプロセスグループを作成し、子プロセスも一括停止

## 制限事項

- デーモンは単一マシンで動作（ネットワーク分散なし）
- セッションキーは永続化されない（デーモン再起動で消失）
- ログバッファは512KBに制限

## 結論

dev-manager-mcpは、AIコーディングツールが開発サーバーを管理するためのシンプルで実用的なMCPサーバーです。ポート衝突を自動回避し、アイドルセッションを自動クリーンアップする機能により、複数の開発サーバーを安全に並行運用できます。
