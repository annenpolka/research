# vibe-kanban アーキテクチャ（正確版）

vibe-kanbanの実際のアーキテクチャとコーディングエージェントの実行方法について、公式ドキュメントとソースコードに基づいて正確に解説します。

## 📌 2つの実行方法

### 1️⃣ ホスト実行（公式推奨）

```bash
npx vibe-kanban
```

- vibe-kanbanもエージェントも**ホストで実行**
- ブラウザ認証フローが使える（Claude Pro/Max、Google認証など）
- 公式ドキュメントはこちらを前提
- 開発環境やローカル使用に最適

### 2️⃣ Docker実行（本ドキュメントの対象）

```bash
docker run vibe-kanban
```

- vibe-kanbanもエージェントも**コンテナ内で実行**
- API keyが必要（ブラウザ認証は不可）
- 本番環境、リモートデプロイ、隔離環境に最適
- セキュリティとポータビリティを重視

**どちらの場合も「vibe-kanbanがnpx経由でエージェントを実行」という点は同じです。**

## ⚠️ 重要な理解（Docker実行の場合）

**vibe-kanbanは`npx`経由でエージェントCLIを自動実行します**

- ✅ vibe-kanbanコンテナ内でエージェントCLIが実行される
- ✅ npxが自動的にエージェントをダウンロード・実行
- ✅ ユーザーはエージェントを事前インストールする必要が**ない**
- ✅ 認証はAPI key（環境変数）で行う
- ❌ ブラウザ認証フローは使用不可

## アーキテクチャ概要

### 実際の構成（ソースコード確認済み）

```
┌──────────────────────────────────────────────────┐
│  vibe-kanbanコンテナ                               │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  vibe-kanban (Rust + TypeScript)           │ │
│  │  ├─ Web UI (カンバンボード)                  │ │
│  │  ├─ REST API (Axum)                        │ │
│  │  └─ Executors (エージェント実行エンジン)      │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                  │
│               │ npx実行                          │
│               ▼                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  npx (Node Package Executor)               │ │
│  │  - 自動ダウンロード                          │ │
│  │  - キャッシュ管理                            │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                  │
│               │ダウンロード・実行                 │
│               ▼                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  エージェントCLI（自動ダウンロード）          │ │
│  │  ├─ @anthropic-ai/claude-code@2.0.31       │ │
│  │  ├─ @google/gemini-cli@0.8.1               │ │
│  │  ├─ cursor-agent                           │ │
│  │  └─ その他のエージェント                     │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  環境変数（認証情報）                              │
│  - ANTHROPIC_API_KEY                            │
│  - GEMINI_API_KEY                               │
│  - OPENAI_API_KEY                               │
│  - CURSOR_API_KEY                               │
└──────────────────────────────────────────────────┘
         ↕
┌──────────────────────────────────────────────────┐
│  ホストマシン                                       │
│  - プロジェクトファイル（ボリュームマウント）         │
│  - Git リポジトリ                                 │
└──────────────────────────────────────────────────┘
```

## ソースコードの証拠

### Claude Code実行（crates/executors/src/executors/claude.rs）

```rust
fn base_command(_profile: &CodingAgentProfile) -> String {
    "npx -y @anthropic-ai/claude-code@2.0.31".to_string()
}
```

- `npx -y`: 自動承認フラグ（インストール確認なし）
- `@anthropic-ai/claude-code@2.0.31`: npmパッケージ名とバージョン
- コンテナ内で実行され、自動的にダウンロード

### Gemini CLI実行（crates/executors/src/executors/gemini.rs）

```rust
fn base_command(_profile: &CodingAgentProfile) -> String {
    "npx -y @google/gemini-cli@0.8.1".to_string()
}
```

### その他のエージェント

同様のパターンで各エージェントが実装されています：
- **Copilot**: GitHub Copilot CLI
- **Cursor**: Cursor Agent CLI
- **OpenCode**: OpenCode CLI
- **Codex**: OpenAI Codex
- **Amp**: Amp CLI

## 実行フロー

### 1. ユーザーがタスクを作成

vibe-kanban Web UIでタスクを作成し、エージェントを選択

### 2. vibe-kanbanがコマンド実行

Rustコード（CommandBuilder）がnpxコマンドを構築：

```rust
CommandBuilder::new()
    .params(vec!["-p".to_string()])
    .extend_params(additional_params)
    .build()
```

### 3. npxが自動ダウンロード

```bash
npx -y @anthropic-ai/claude-code@2.0.31 -p /repos/project --output-format=stream-json
```

- npxがパッケージをキャッシュから確認
- なければnpmレジストリからダウンロード
- ダウンロード後、即座に実行

### 4. エージェントCLIが実行

- stdin/stdout/stderrがパイプで接続
- JSON形式でストリーミング通信
- リアルタイムでログ出力

### 5. 認証

環境変数から認証情報を読み取り：

```bash
ANTHROPIC_API_KEY=sk-ant-xxx npx -y @anthropic-ai/claude-code@2.0.31
```

## なぜこの設計なのか

### メリット

1. **ユーザーの手間が不要**
   - エージェントの事前インストール不要
   - npxが自動的に管理

2. **バージョン管理が容易**
   - コードでバージョン指定
   - 常に正しいバージョンが実行される

3. **環境の一貫性**
   - コンテナ内で完結
   - 依存関係の問題が発生しにくい

4. **更新が簡単**
   - ソースコードのバージョン番号を変更するだけ
   - ユーザー側の作業不要

### デメリット

1. **初回実行が遅い**
   - npxがパッケージをダウンロード
   - キャッシュ後は高速

2. **ブラウザ認証が使えない**
   - API keyのみで認証
   - Claude Pro/Maxサブスクリプションは利用不可

3. **ネットワーク依存**
   - npmレジストリへのアクセスが必要
   - オフライン環境では使用困難

## 認証方法（Docker実行の場合）

⚠️ **重要**: Docker環境でのエージェント認証は、ホスト実行より複雑です。

### Claude Codeの場合（複雑）

Claude Codeの認証は2025年時点で複数の既知の問題があります。

#### ❌ 動かない方法

```bash
# これだけでは動きません（GitHub Issue #9699, #551）
docker run -e ANTHROPIC_API_KEY=sk-ant-xxx vibe-kanban
```

**問題**：
- API keyを設定しても`/login`を要求される
- 非対話モードで"Invalid API key"エラー
- Docker/CI環境での認証が未完成

#### ✅ 動作する方法

**方法1: OAuth Token（推奨）**

```bash
# ホストで長期トークンを生成
npx @anthropic-ai/claude-code setup-token
# トークンがコピーされます

# Docker実行時にトークンを渡す
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<生成されたトークン> \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

**方法2: 設定ファイルマウント（短期利用のみ）**

⚠️ **制限事項**: `~/.claude/.credentials.json`のトークンは**約6時間で期限切れ**になります。長期運用にはOAuth Token方式を使用してください。

```bash
# ホストで認証（一度だけ）
npx @anthropic-ai/claude-code
# ~/.claude/.credentials.json が作成される（6時間有効）

# Docker実行時に設定ファイルをマウント
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/.claude:/root/.claude:ro \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

**認証ファイルの場所**：
- `~/.claude/.credentials.json` - OAuth トークン（6時間有効）
- `~/.claude/settings.json` - ユーザー設定（認証情報なし）

**方法3: API key + 設定ファイル併用（実験的・非推奨）**

```bash
# ANTHROPIC_API_KEYと設定ファイルを両方渡す
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY=sk-ant-xxx \
  -v ~/.claude:/root/.claude:rw \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

### Gemini CLIの場合（比較的シンプル）

```bash
docker run -d \
  -e GEMINI_API_KEY=your-gemini-key \
  vibe-kanban:latest
```

Google AI Studio で取得したAPI keyを使用。Claude Codeより認証はシンプル。

### OpenAI Codexの場合

```bash
docker run -d \
  -e OPENAI_API_KEY=sk-your-openai-key \
  vibe-kanban:latest
```

OpenAI Platform で取得したAPI keyを使用。

### GitHub Copilotの場合（設定ファイル必要の可能性）

```bash
# 方法1: GitHub Token
docker run -d \
  -e GITHUB_TOKEN=ghp_xxx \
  vibe-kanban:latest

# 方法2: 設定ファイルマウント（より確実）
docker run -d \
  -v ~/.config/github-copilot:/root/.config/github-copilot:ro \
  vibe-kanban:latest
```

GitHub Copilot CLIは設定ファイルに依存する場合があります。

### 複数エージェントを同時に使う場合

```bash
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=<トークン> \
  -e GEMINI_API_KEY=your-gemini-key \
  -e OPENAI_API_KEY=sk-your-openai-key \
  -v ~/.claude:/root/.claude:ro \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

## 必要な環境

### vibe-kanbanコンテナ内

既にDockerfileに含まれています：

- ✅ Node.js 24
- ✅ npm/npx
- ✅ Rust runtime
- ✅ 必要な依存ライブラリ

### ホスト側

必要なのはプロジェクトファイルのみ：

```bash
docker run -d \
  -v ~/projects/my-app:/repos/my-app:rw \
  vibe-kanban:latest
```

## トラブルシューティング

### エージェントが実行されない

**症状**:
```
Error: Command not found: npx
```

**原因**: Dockerfileが正しくビルドされていない

**解決**:
```bash
docker build -t vibe-kanban:latest .
```

### API key not found

**症状**:
```
Error: ANTHROPIC_API_KEY environment variable not found
```

**解決**:
```bash
docker run -e ANTHROPIC_API_KEY=sk-ant-your-key vibe-kanban:latest
```

### npx download fails

**症状**:
```
Error: Failed to download @anthropic-ai/claude-code
```

**原因**: ネットワーク接続またはnpmレジストリの問題

**解決**:
```bash
# コンテナ内で手動確認
docker exec -it vibe-kanban npx -y @anthropic-ai/claude-code@2.0.31 --version
```

### Permission denied on /repos

**症状**:
```
Error: Permission denied: /repos/my-project
```

**解決**:
```bash
docker run --user $(id -u):$(id -g) \
  -v ~/projects:/repos:rw \
  vibe-kanban:latest
```

## 🌳 git worktreeによるタスク隔離（重要機能）

vibe-kanbanの最も重要な機能の一つは、**各タスクが独立したgit worktreeで実行される**ことです。

### git worktreeとは

Git worktreeは、同じリポジトリの複数のworking directoryを同時に持つ機能です。

```
my-project/
├── .git/                    # メインリポジトリ
├── main/                    # メインブランチ（通常の作業）
├── .worktrees/
│   ├── task-123/            # タスク123専用worktree
│   ├── task-456/            # タスク456専用worktree
│   └── task-789/            # タスク789専用worktree
```

### vibe-kanbanでの利用

1. **各タスクは専用のgit worktreeで実行**
   - タスク間のコンフリクトを防止
   - 同時に複数のタスクを並列実行可能

2. **コンテキスト隔離**
   - あるタスクのAIが別タスクのファイルを参照しない
   - エージェントのコンテキストが純粋に保たれる

3. **安全なレビューとマージ**
   - 各タスクの変更をgit diffで確認
   - 成功したタスクのみをワンクリックでメインブランチにマージ

4. **複数エージェントの同時実行**
   - 同じプロジェクトで複数のエージェントを並列実行
   - 各エージェントは独立したworktreeで動作

### メリット

✅ **タスク間の干渉なし**
- タスクAの変更がタスクBに影響しない
- 複数の機能を同時開発可能

✅ **安全な実験**
- 失敗したタスクは破棄するだけ
- メインブランチは常にクリーンな状態

✅ **並列実行の効率化**
- Claude CodeとGemini CLIを同時に異なるタスクで実行
- リソースを最大限活用

✅ **明確なレビュープロセス**
- タスクごとにdiffを確認
- 意図しない変更を防止

### 環境変数

```bash
# デバッグ用：worktreeの自動クリーンアップを無効化
-e DISABLE_WORKTREE_ORPHAN_CLEANUP=true
```

この設定により、タスク完了後もworktreeが残り、手動で検証できます。

## まとめ

### 重要なポイント

1. **vibe-kanbanがnpx経由でエージェントを実行**
   - コンテナ内で完結
   - 自動ダウンロード・実行

2. **ユーザーはエージェントをインストール不要**
   - npxが自動管理
   - バージョンもコードで管理

3. **Docker環境での認証は複雑**
   - Claude Code: OAuth tokenまたは設定ファイルマウント推奨
   - Gemini/OpenAI: API keyで比較的シンプル
   - ブラウザ認証は不可

4. **git worktreeによるタスク隔離**
   - 各タスクは独立したworktreeで実行
   - 並列実行とコンテキスト隔離を実現

5. **ホスト側に必要なのはプロジェクトファイルのみ**
   - ボリュームマウント
   - エージェント自体は不要

### クイックスタート（Claude Code + Gemini CLI）

```bash
# 1. Claude Code用のOAuth tokenを生成
npx @anthropic-ai/claude-code setup-token
# トークンをコピー

# 2. API keyを準備
export CLAUDE_CODE_OAUTH_TOKEN=<生成されたトークン>
export GEMINI_API_KEY=your-gemini-key

# 3. vibe-kanbanを起動
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN \
  -e GEMINI_API_KEY \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest

# 4. ブラウザでアクセス
# http://localhost:3000

# 5. タスクを作成してエージェントを選択
# エージェントCLIは自動的にダウンロード・実行される
```

**代替案**: 設定ファイルマウント方式（短期テスト用）

⚠️ **注意**: トークンは約6時間で期限切れ。本番運用には上記のOAuth Token方式を推奨。

```bash
# 1. ホストで一度認証（一度だけ）
npx @anthropic-ai/claude-code
# ~/.claude/.credentials.json が作成される（6時間有効）

# 2. vibe-kanbanを起動（設定ファイルをマウント）
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -e GEMINI_API_KEY=your-gemini-key \
  -v ~/.claude:/root/.claude:ro \
  -v ~/projects/my-app:/repos/my-app:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

これで正しいアーキテクチャの理解ができました！ 🎯
