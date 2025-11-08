# MailDeck実装ExecPlan

このExecPlanは生きたドキュメントであり、作業が進むたびに`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective`セクションを更新すること。

## Purpose / Big Picture

複数のコーディングエージェントが同時に作業する際、リポジトリへ一切の管理用ファイルを追加せずに、タスク計画（Beads）、非同期連絡とファイル予約（MCP Agent Mail）、リアルタイム観測（Claude Hooks Observability）をまとめて扱える薄い制御レイヤーを提供する。MailDeckを導入すると、エージェントは`maildeck enter <project>`だけで共通タスクグラフに接続し、作業前にファイル予約と観測設定を済ませ、終了時には一括リリースできるようになる。

## Progress

- [x] (2025-11-08 18:45Z) リポジトリ調査とMailDeck要求の整理を完了。
- [ ] MailDeck Hub CLIのプロトタイプを作成（プロジェクト登録/資格情報保存）。
- [ ] MailDeck Hooks設定生成とClaude Code再設定フローを実装。
- [ ] Task Bridgeコマンド（Beads ↔ Agent Mail連携）を実装し、E2E検証を完了。
- [ ] Guard/Checkコマンドと`maildeck check`の自動テストを追加。
- [ ] ドキュメントとAGENTS.md追記テンプレートを更新し、最終動作確認を行う。

## Surprises & Discoveries

- 観測: `mcp_agent_mail`の`guard.install_guard`はプロジェクト内`.git/hooks`に直接書き込むが、設定オプション`--dir` `--project-dir`でアーカイブパスを外部に逃がせる。Evidence: `src/mcp_agent_mail/guard.py`とREADMEの`--dir`解説。
- 観測: `claude-code-hooks`は`.claude`ディレクトリをリポジトリにコピーする手順が推奨されるが、`settings.json`はホーム配下でも読み込めるため、MailDeck側で絶対パスを書けば非侵襲に扱える。Evidence: README「Ensure the observability server is running」節。

## Decision Log

- 決定: MailDeckは各プロジェクトごとに`~/.maildeck/projects/<project>`へ外部ワークスペースを作成し、そこにAgent Mailアーカイブ、Beads DB、Observabilityプロセスをまとめる。理由: リポジトリを無改変に保つ要求／既存ツールは外部署置をサポートしているため。日付: 2025-11-08 (Codex)。
- 決定: すべてのエージェント操作は`maildeck <subcommand>`を経由させ、`bd`やAgent Mailのツールは直接呼ばせない。理由: 予約漏れやHook未設定を防ぐガードになるから。日付: 2025-11-08 (Codex)。

## Outcomes & Retrospective

- 2025-11-08 初版: 調査結果を反映した構想と実装計画を確立。未実装セクションは今後の作業で更新すること。

## Context and Orientation

- このリポジトリは`/Users/annenpolka/junks/research`配下の研究集積所であり、各サブディレクトリが独立プロジェクトになっている。
- 既存調査フォルダ（例: `beads-non-invasive-analysis`）はREADME中心に成果物をまとめるスタイルを採用している。
- MailDeckは新規ディレクトリ`multi-agent-maildeck`内でREADMEと本ExecPlanを持つ。
- 参照OSS:
  - `scratch/external/mcp_agent_mail`: FastMCP HTTPサーバ、Git+SQLiteアーカイブ、file_reservation API。
  - `scratch/external/claude-code-hooks-multi-agent-observability`: Claude Hooks、Bunサーバ、Vueクライアントで構成される観測基盤。
  - `scratch/external/beads`: `bd` CLIと`beads-mcp`サーバで構成されるタスクグラフ管理。

## Plan of Work

1. **Hubプロトタイピング**: `~/\.maildeck`配下にSQLiteメタデータとプロジェクト個別ディレクトリを生成するCLIをRustまたはPythonで実装する。`maildeck attach <project>`はAgent Mail install scriptとBeads initをラップしつつ認証情報を保存する。
2. **Hooks設定生成**: Claude Codeの`settings.json`（ホーム配下）を読み書きし、対象プロジェクトのHookコマンドへ`uv run ~/.maildeck/hooks/send_event.py --source-app <project>@$AGENT_NAME`を自動挿入する。既存設定はバックアップを残す。
3. **Task Bridge**: `maildeck task ready|take|update`が内部で`bd --json`（または`beads-mcp`）を呼び、Issue IDをAgent Mail threadに反映する。`maildeck reserve`は`file_reservation_paths`と`bd update --status in_progress`を同時に行う。
4. **Guard/Check**: `maildeck check`コマンドがBeads/Agent Mail/Observabilityのヘルスチェックを順番に実行し、失敗時に診断を表示する。CIライクな1コマンドに集約する。
5. **Docs & Instructions**: README/AGENTS追記例/トラブルシューティングを整備。環境ごとの差異（例: ポート、APIキー）も明示する。

## Concrete Steps

1. **Hub CLI雛形**
    - 作業ディレクトリ: `multi-agent-maildeck`
    - コマンド例:
        - `uv init maildeck` または `cargo new maildeck-cli`（選択した言語に応じて）
        - `maildeck attach demo --repo /path/to/repo --mail-port 9876`
    - 期待結果: `~/.maildeck/projects/demo`配下に`mail`, `beads`, `observability`フォルダと設定JSONが生成される。
2. **Agent Mail統合**
    - `scripts/install.sh --dir ~/.maildeck/projects/demo/mail --project-dir ~/.maildeck/projects/demo/mail/archive --no-start`
    - `scripts/run_server_with_token.sh --port 9876` をsystemd/launchdではなく`maildeck serve mail`で常駐管理する。
3. **Beads統合**
    - `BEADS_WORKING_DIR=~/.maildeck/projects/demo/beads bd init --quiet`
    - `maildeck task ready`は `BEADS_WORKING_DIR`を自動輸出して`bd ready --json`を実行。
4. **Observability統合**
    - `cp -R scratch/external/claude-code-hooks-multi-agent-observability/apps ~/.maildeck/projects/demo/observability`
    - `./scripts/start-system.sh --server-port 4600 --client-port 5173` を`maildeck serve observability`で包む。
    - `~/.claude/settings.json`を編集するサブコマンドを実装。
5. **Workflowコマンド**
    - `maildeck enter demo`フロー: `hub sqlite`からトークン読み込み → Agent登録 → ファイル予約 → Hook更新。
    - `maildeck release demo`フロー: 予約解除、Beads Issue close、Mail thread投稿。
6. **テストと検証**
    - 単体: CLI各サブコマンドに対する`pytest`/`cargo test`。
    - 結合: `maildeck check demo`で3層すべてのエンドポイントにヘルスリクエストを出す。期待レスポンスを記録。
7. **ドキュメンテーション**
    - README更新、AGENTS追記テンプレート整備、トラブルシュート表（Hookが失敗したときなど）を記載。

## Validation and Acceptance

- MailDeckが提供する4つの主要コマンド（`attach`, `enter`, `reserve`, `release`, `check`）について自動テストを作成し、`maildeck check <project>`を実行して以下の条件を満たすこと。
    - `bd ready --json`が0で完了し、Issueリストを返す。
    - Agent Mail HTTP `/healthz`が200で応答し、`register_agent`と`file_reservation_paths`が成功する。
    - Observabilityサーバ`/events/recent`が空でも200で返り、`/stream`へ接続できる。
    - 1回の`enter`でBeads Issueに`in_progress`、Agent Mail threadに開始メモ、Observabilityには`SessionStart`が記録されることを証明（ログ添付）。

## Idempotence and Recovery

- `maildeck attach`は同一プロジェクト名で再実行しても既存設定を確認し、変更を差分適用する。
- Agent Mail/Beads/Observabilityいずれかの起動に失敗した場合は、Hub SQLiteに状態フラグを記録し、`maildeck check`で再試行できる。
- Claude Hook設定変更はバックアップファイルを残し、`maildeck hooks restore <timestamp>`で復元可能にする。

## Artifacts and Notes

- `~/.maildeck/projects/<project>/config.json`に以下の情報を保持する予定:
    - Agent Mail: `token`, `port`, `archive_path`
    - Beads: `db_path`, `daemon_socket`
    - Observability: `server_port`, `client_port`, `source_app`
- `logs/maildeck-check.log`に毎回の`maildeck check`結果を追記し、CIライクな証跡を残す。

## Interfaces and Dependencies

- **Agent Mail API**: FastMCP HTTPトランスポート（Streamable HTTP）。必要ツール: `ensure_project`, `register_agent`, `file_reservation_paths`, `send_message`, `list_agents`。
- **Beads CLI/MCP**: `bd ready/create/update/close --json` or `mcp__beads__*`関数。`BEADS_WORKING_DIR`環境変数で外部DB指定。
- **Observability Server**: HTTPエンドポイント(`/events`, `/events/recent`, `/events/filter-options`) と WebSocket `/stream`。Hookコマンドは`uv run ~/.maildeck/hooks/send_event.py --source-app <project>@<agent>`形式。
- **Local Services**: `uv`, `bun`, `pnpm` (または`npm`)、`sqlite3`、`git`。

---
更新履歴: 2025-11-08 — 初版作成（Codex）
