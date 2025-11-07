# Beads非侵襲性分析

## 概要

このプロジェクトは、[steveyegge/beads](https://github.com/steveyegge/beads) リポジトリがリポジトリや指示ファイル（AGENTS.md等）に対して非侵襲的な方法をサポートしているかをコードレベルで調査したものです。

## 調査日

2025-11-07

## 調査対象

- リポジトリ: https://github.com/steveyegge/beads
- 言語: Go
- 主要コンポーネント:
  - `cmd/bd/init.go` - 初期化処理
  - `cmd/bd/config.go` - 設定管理
  - `internal/configfile/configfile.go` - 設定ファイル処理
  - README.md、AGENTS.md - ドキュメント

## 結論

**Beadsは部分的に非侵襲的だが、gitフックとマージドライバーのインストールにより、一定の侵襲性を持つ。**

### 非侵襲的な点（⭕）

1. **最小限のセットアップ**
   - `bd init`のみでセットアップ完了
   - 外部サーバーや複雑な設定管理システム不要
   - すべてのデータは`.beads/`ディレクトリ内に格納

2. **既存ファイル構造の保護**
   - 既存のソースコードやドキュメントを変更しない
   - プロジェクトルートに新しいファイルを作成しない（`.beads/`ディレクトリ以外）
   - AGENTS.mdやCLAUDE.mdを自動的に変更しない

3. **バージョン管理との統合**
   - gitを使用してデータを同期
   - `.beads/issues.jsonl`のみをコミット対象とし、SQLiteキャッシュ（`.db`ファイル）は`.gitignore`で除外
   - 既存のgitワークフローに追加される形で動作

4. **非破壊的な動作**
   - 既存のgitフックはバックアップされる（`.backup`サフィックス付き）
   - 既存の設定ファイルを上書きせず、自動移行メカニズムを提供

### 侵襲的な点（❌）

1. **Gitフックのインストール**
   - `pre-commit`フック: コミット前に`bd sync --flush-only`を実行してJSONLに変更を反映
   - `post-merge`フック: マージ後に`bd import`でJSONLの更新をデータベースに同期
   - 既存フックがある場合はバックアップされるが、デフォルトでインストールされる

2. **`.gitattributes`の変更**
   - カスタムマージドライバーを設定するため、`.gitattributes`に以下を追加:
     ```
     .beads/beads.jsonl merge=beads
     ```
   - リポジトリ全体のgit設定に影響

3. **git configの変更**
   - ローカルまたはグローバルgit設定にマージドライバーを追加:
     ```
     git config merge.beads.driver "bd merge %A %O %L %R"
     git config merge.beads.name "bd JSONL merge driver"
     ```

### 軽減オプション（⚠️）

以下のオプションで侵襲性を軽減可能:

- `--skip-merge-driver`: マージドライバーのセットアップをスキップ
- `--quiet`: 自動インストールモード（エージェント向け、対話なし）
- `--branch <name>`: 専用ブランチでbeadsメタデータを管理（保護されたブランチ対応）

**注意**: `--skip-hooks`や`--no-hooks`オプションは存在せず、gitフックのインストールを完全にスキップする方法は提供されていません。

## AGENTS.mdへの統合方法

### ドキュメントでの推奨方法

READMEとAGENTS.mdによると、以下の手順が推奨されています:

1. **人間の開発者が実行**
   ```bash
   bd init
   ```

2. **AGENTS.mdに以下を追加**（手動）
   ```
   BEFORE ANYTHING ELSE: run 'bd onboard' and follow the instructions
   ```

3. **エージェントが実行**
   ```bash
   bd onboard
   ```
   - 統合ガイドを受け取る
   - ワークフロー文書が自動生成される

### コードレベルの実装

- **`init.go`はAGENTS.mdを直接変更しない**
- 自動変更のメカニズムは実装されていない
- ユーザーが手動でAGENTS.mdに指示を追加することを前提としている

これは、意図的に「非侵襲的」な設計を採用していると言える。

## 初期化プロセスの詳細

### `bd init`が実行すること

1. **ディレクトリとファイルの作成**
   - `.beads/` ディレクトリ（パーミッション: 0750）
   - `.beads/beads.db` - SQLiteデータベース
   - `.beads/issues.jsonl` - バージョン管理対象のイシューデータ
   - `.beads/metadata.json` - バージョンとリポジトリ識別子
   - `.beads/.gitignore` - データベースファイルとランタイムファイルを除外

2. **Gitフックのインストール**
   - `pre-commit`: 変更のフラッシュとJSONLのステージング
   - `post-merge`: マージ後のインポート
   - 既存フックは`.backup`サフィックスでバックアップ

3. **Gitマージドライバーの設定**
   - `.gitattributes`へのエントリ追加
   - git configの更新

4. **既存イシューのインポート**
   - gitから既存の問題を自動的にインポート

### `.beads/.gitignore`の内容

```gitignore
# SQLite artifacts ignored
*.db
*.db-journal
*.db-wal
*.db-shm

# Runtime files ignored
daemon.lock
daemon.log
daemon.pid
bd.sock

# These are explicitly tracked
!*.jsonl
!metadata.json
!config.json
```

この設計により、一時的なデータベースファイルはバージョン管理から除外され、JSONLファイルのみがコミット対象となる。

## 設定ファイルの管理

### 保存場所

- プロジェクトごとに`.beads/metadata.json`に保存
- 形式: JSON
- パーミッション: 0600（所有者のみ読み書き可能）

### 構造

```json
{
  "Database": "beads.db",
  "Version": "...",
  "JSONLExport": "beads.jsonl"
}
```

### 設定の変更

以下のコマンドで設定を管理:

```bash
bd config set <key> <value>  # 値を設定
bd config get <key>          # 値を取得
bd config list               # 全設定を表示
bd config unset <key>        # 値を削除
```

### レガシー移行

- 旧形式の`config.json`が存在する場合、自動的に`metadata.json`に移行
- 移行後、旧ファイルは削除される（ベストエフォート）

## Gitフックの実装詳細

### Pre-commit フック

```bash
#!/bin/sh
# bd (beads) pre-commit hook

if ! command -v bd >/dev/null 2>&1; then
    exit 0
fi

if [ ! -d ".beads" ]; then
    exit 0
fi

# Flush pending changes to JSONL
bd sync --flush-only

# Stage the updated JSONL file
git add .beads/issues.jsonl
```

**目的**: レース条件を防止し、コミット前にすべての保留中の変更がJSONLに反映されることを保証

### Post-merge フック

```bash
#!/bin/sh
# bd (beads) post-merge hook

if ! command -v bd >/dev/null 2>&1; then
    exit 0
fi

if [ ! -d ".beads" ]; then
    exit 0
fi

# Import updated JSONL after merge
bd import -i .beads/issues.jsonl || true
```

**目的**: マージ後にJSONLの更新内容をローカルデータベースに同期

**注意**: エラーが発生してもマージ自体は失敗させない（`|| true`）

## エージェント統合の設計思想

### コード内のコメントから

`init.go`内に以下のコメントが存在:

```go
// Do this BEFORE quiet mode return so hooks get installed for agents
```

これは、エージェントの自動化を明示的に想定した設計であることを示している。

### 推奨されるエージェントワークフロー

1. **初期化**（`--quiet`モード）
   ```bash
   bd init --quiet
   ```
   - 対話なしで自動セットアップ
   - gitフックとマージドライバーを自動インストール

2. **作業の確認**
   ```bash
   bd ready --json
   ```
   - ブロッカーのない「準備完了」の作業を取得

3. **イシューの作成**
   ```bash
   bd create "Issue title" -t bug -p 1 --deps discovered-from:bd-100 --json
   ```
   - 依存関係を設定してコンテキストを維持

4. **作業の更新**
   ```bash
   bd update bd-42 --status in_progress --json
   bd close bd-42 --reason "Completed" --json
   ```

5. **セッション終了**
   ```bash
   bd sync
   ```
   - 即座にJSONLにエクスポート、コミット、プル、インポート、プッシュ
   - 30秒のデバウンスを待たずに強制フラッシュ

### MCP Server（推奨）

Claude等のクライアント向けにMCPサーバーが提供されている:

```bash
pip install beads-mcp
```

**利点**:
- ネイティブな関数呼び出し（`mcp__beads__create()`等）
- シェルコマンドの代わりにプログラマティックなAPI
- 自動ワークスペース検出
- 構造化されたJSONレスポンス
- 複数リポジトリの自動ルーティング

## 非侵襲性の評価

### 「非侵襲的」の定義

beadsが「非侵襲的」と謳う根拠:

1. **ゼロセットアップ**: `bd init`だけで動作開始
2. **外部依存なし**: サーバーや設定管理システム不要
3. **プロジェクト構造の保護**: 既存コードやドキュメントを変更しない
4. **段階的な採用**: 既存プロジェクトに「追加」される形で統合

### 実際の侵襲性

しかし、コードレベルの調査により、以下の侵襲性が確認された:

1. **Gitフックの強制インストール**
   - スキップオプションが存在しない
   - 既存フックをバックアップするが、上書きする

2. **Gitリポジトリ設定の変更**
   - `.gitattributes`への追加
   - git configへの追加

3. **Gitワークフローへの影響**
   - すべてのコミットで`bd sync`が実行される
   - すべてのマージで`bd import`が実行される

### 結論

beadsは**相対的に非侵襲的**である。以下の観点から:

- **プロジェクト構造**: 影響なし（`.beads/`のみ）
- **ソースコード**: 影響なし
- **ドキュメント**: 自動変更なし（AGENTS.mdは手動追加）
- **Gitワークフロー**: ⚠️ フックとマージドライバーにより影響あり

しかし、gitフックの強制インストールは、一部のプロジェクトや開発者にとって受け入れられない可能性がある。

## 推奨事項

### ユースケース別の評価

#### ✅ beadsが適している場合

- 新規プロジェクト
- エージェント駆動の開発が中心
- gitフックの使用に抵抗がない
- 長期的なタスク管理が必要

#### ⚠️ 慎重に検討すべき場合

- 厳格なgitワークフローがある既存プロジェクト
- カスタムgitフックを既に使用している
- CI/CDパイプラインとの統合が必要
- 複数の開発者がいる大規模プロジェクト

#### ❌ beadsが適していない場合

- gitフックの使用が禁止されている
- 読み取り専用のリポジトリ
- `.beads/`ディレクトリをコミットできない環境
- 外部ツールへの依存を最小限にしたい

### 改善提案

beadsがより非侵襲的になるための提案:

1. **`--no-hooks`オプションの追加**
   - gitフックのインストールを完全にスキップ
   - ユーザーが手動で`bd sync`を実行する選択肢を提供

2. **段階的なオンボーディング**
   - 初回は最小限のセットアップ
   - gitフックやマージドライバーは後から追加可能

3. **AGENTS.md自動更新のオプション**
   - `--update-agents-md`フラグで自動追加
   - デフォルトは手動のまま

## 参考資料

- [Beads GitHubリポジトリ](https://github.com/steveyegge/beads)
- [README.md](https://raw.githubusercontent.com/steveyegge/beads/main/README.md)
- [AGENTS.md](https://raw.githubusercontent.com/steveyegge/beads/main/AGENTS.md)
- [cmd/bd/init.go](https://github.com/steveyegge/beads/blob/main/cmd/bd/init.go)
- [cmd/bd/config.go](https://github.com/steveyegge/beads/blob/main/cmd/bd/config.go)
- [internal/configfile/configfile.go](https://github.com/steveyegge/beads/blob/main/internal/configfile/configfile.go)

## 調査方法

このプロジェクトでは、以下の方法でbeadsの非侵襲性を調査しました:

1. **ドキュメント分析**
   - README.md、AGENTS.mdの精読
   - 「non-invasive」「setup」「configuration」に関する記述の抽出

2. **コードレビュー**
   - `cmd/bd/init.go`の完全な解析
   - `cmd/bd/config.go`の設定管理ロジックの確認
   - `internal/configfile/configfile.go`の設定ファイル処理の確認

3. **動作分析**
   - 初期化プロセスのステップ特定
   - 作成されるファイルとディレクトリのリスト化
   - Gitへの影響の評価

4. **フラグとオプションの調査**
   - コマンドラインフラグの完全なリスト作成
   - 各フラグの動作と影響範囲の確認

## まとめ

beadsは、AIエージェント向けのイシュートラッキングシステムとして、多くの点で非侵襲的な設計を採用しています。特に、プロジェクト構造やソースコードへの影響を最小限に抑え、すべてのデータを`.beads/`ディレクトリ内に格納する設計は評価できます。

しかし、gitフックとマージドライバーの強制インストールにより、既存のgitワークフローに影響を与える点は注意が必要です。この侵襲性は、beadsの自動同期機能を実現するために不可欠ですが、すべてのプロジェクトやチームに受け入れられるとは限りません。

AGENTS.mdへの統合については、自動変更を行わず、ユーザーが手動で追加する設計を採用しており、この点は非侵襲的と言えます。

総合的には、**beadsは相対的に非侵襲的だが、gitフックの使用により一定の侵襲性を持つ**と結論づけられます。
