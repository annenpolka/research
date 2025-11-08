# MailDeck: 非侵襲マルチエージェント制御レイヤー

## 目的

`MailDeck`は、複数のコーディングエージェントが同一コードベースや姉妹リポジトリで同時作業するときの「薄い制御層」を提供する構想である。リポジトリには一切の管理用ファイルを追加せず、代わりにエージェント向け指示と外部ハブを活用して、以下の3点を同時に満たす設計を目指す。

1. **連絡と意図の可視化** — [`mcp_agent_mail`](scratch/external/mcp_agent_mail) のメッセージ/リソース/ファイル予約APIをHTTP FastMCPサーバとして常駐させ、各エージェントの編集面積と決定ログを「メール」としてGit監査できる。
2. **タスクグラフの単一真実源** — [`beads`](scratch/external/beads) の`bd ready/create/update`および`beads-mcp`サーバを用い、マルチワーカーに強いハッシュ型Issue IDでもって長期計画を共有する。
3. **リアルタイム観測** — [`claude-code-hooks-multi-agent-observability`](scratch/external/claude-code-hooks-multi-agent-observability) の `.claude/hooks/send_event.py` → Bunサーバ → VueクライアントというHookパイプラインをプロジェクト外に設置し、各セッションのPreToolUse/PostToolUse/UserPrompt/StopなどをWebSocketで俯瞰する。

## 調査ハイライト

### MCP Agent Mail
- `scripts/automatically_detect_all_installed_coding_agents_and_install_mcp_agent_mail_in_all.sh` がローカルに存在するCodex/Claude/Gemini CLIを走査し、FastMCP HTTPサーバとBearerトークンを自動登録する。
- `src/mcp_agent_mail/app.py` ではツール群をクラスタ単位（identity/messaging/file_reservations 等）で定義し、SQLAlchemy + Gitアーカイブ (`ProjectArchive`) へ同時書き込みする構造を持つ。
- `storage.write_message_bundle` が Markdown メール、添付ファイル、`archive_write_lock` を用いたGitコミットを同時に生成するため、すべての通信が人間可読な監査線になる。
- `guard.install_guard` でプロジェクトにpre-commitガードを仕込める一方、`--project-dir`や`--dir`引数を指定すればコードベースの外側（例: `~/.maildeck/{project}`）にアーカイブを保管できる。

### Claude Code Hooks Observability
- `.claude/hooks/send_event.py` が`uv`経由で任意イベントをHTTP POST (`/events`) しつつ`--add-chat`で会話抜粋も添付できる。
- `apps/server/src/index.ts` はBunサーバで、SQLite (`apps/server/src/db.ts`) に書き込みつつWebSocket `/stream` へ即時配信、`/events/filter-options`でフィルタ値を提供する。HITL(WebSocket応答)も備えている。
- `.claude/settings.json` にフックを列挙するだけでマルチエージェント複数セッションが識別可能（`source-app`と`session_id`）。パスは絶対化できるためリポジトリ外の共通`.claude`ツリーからも呼び出せる。

### Beads
- READMEが強調する`bd init --quiet`はフック自動インストールを伴うが、`beads-mcp`サーバを単独で起動し`BEADS_WORKING_DIR`環境変数でデータベース位置を外部ディレクトリへ切り離せる。
- v0.20.1のハッシュID（`bd-a1b2`形式）により複数クローン/ブランチ/エージェントでも衝突しづらい。`bd migrate`で旧DBも昇格可能。
- `docs/MULTI_REPO_AGENTS.md` と `AGENTS.md` は「単一MCPサーバ → プロジェクト別デーモン自動起動」パターンを推奨しており、MailDeckの外部ハブ構成と親和性が高い。

## MailDeckコンセプト

MailDeckは「三層構造のシグナル」を1本の薄い操作手順にまとめる。

1. **Task Graph Layer** — Beadsを`~/maildeck/workspaces/<project>/beads`に配置し、`maildeck task <cmd>`が内部で`bd --json`を呼び出してIssueをフェッチ/更新する。エージェントは手元リポジトリを汚さずにタスク指針を得る。
2. **Message & Intent Layer** — `maildeck mesh`が`mcp_agent_mail`サーバの`ensure_project`/`register_agent`/`file_reservation_paths`をまとめ、各エージェント起動時にID付与とファイル予約を自動化する。
3. **Telemetry Layer** — `maildeck tap`がClaude Code Hook設定をグローバル`~/.claude-maildeck/settings.json`に書き込み、`source-app`を「project:agent」形式で付与。BunサーバのイベントがMailDeck UIに集約され、Mail threadsとIssue ID(`bd-xxxx`)を突合する。

MailDeckは「テストのように薄い」ことを目指し、各層を`maildeck check`1コマンドで検証できる:

```
maildeck check <project>
  ↳ bd ready --json           # タスク取得
  ↳ curl /mcp/mail/health     # Agent Mail サーバ応答
  ↳ curl /observability/ping  # Hookサーバ応答
  ↳ maildeck leases verify    # file_reservationとGit差分の突合
```

## コンポーネント案

- **MailDeck Hub**: `~/.maildeck/hub.sqlite`で各プロジェクトのエイリアス、Agent Mailトークン、Beads DBパス、Observabilityエンドポイントを管理。`maildeck attach`が1回実行されれば以後はハブが資格情報を配布する。
- **MailDeck Hooks**: Claude CodeのPre/PostToolUse等に1本の`uv run ~/.maildeck/hooks/send_event.py --source-app <project>@$AGENT_NAME`を登録するだけの薄い設定生成器。既存`.claude`をコピーせず、設定JSON（人間ホームディレクトリに置かれる）だけを書き換える。
- **MailDeck Task Bridge**: `maildeck reserve bd-a1b2 src/api/**`のようなコマンドが、Beads Issue IDとAgent Mail file_reservationをまとめて更新し、Reservation結果をMail threadへ自動投稿する。
- **MailDeck Guard**: Agent Mailの`guard.install_guard`を直接使わず、`pre-commit`をグローバルGitテンプレートで仕込み、GuardはMailDeck Hubが生成する仮想ワークツリーにだけ配置。プロジェクトリポジトリは無改変。

## 予想されるワークフロー

1. **初期化 (人間が1度だけ)**
    - `maildeck attach <project-name> --repo /path/to/repo --mail-port 9876 --beads-dir ~/.maildeck/workspaces/<project>/beads` を実行。
    - コマンドは `scripts/install.sh` (Agent Mail) を `--dir ~/.maildeck/projects/<project>/mail` オプション付きで呼び出し、`bd init --quiet` を影響外ディレクトリで実行。
    - Hookサーバ (`./scripts/start-system.sh`) を `~/.maildeck/projects/<project>/observability` に起動し、Vite/Bunをpnpmで常駐。
2. **エージェント起動前指示**
    - `AGENTS.md`に「BEFORE ANYTHING ELSE: run \\`maildeck enter <project>\\`」を追記。エージェントはこのコマンドで:
        1. `bd ready --json` からIssueを選択 → 選択IDをMail threadに記録。
        2. `register_agent`でIdentity確保 → `file_reservation_paths`で対象ディレクトリをロック。
        3. Claude Code hooksの`source-app`を `project/agent` に上書き。
3. **作業中**
    - コマンド類は`maildeck task create|update`、`maildeck mesh send --thread bd-xxxx`のような薄いラッパーを通すことで非侵襲に既存CLIを利用。
    - Observability UIはMail thread ID(`thread_id=bd-xxxx`)をキーにフィルタ可能。
4. **終了時**
    - `maildeck release`がBeads Issueを`done`にし、Agent Mail threadへ完了コメントを残し、Hooksのセッションを`Stop`イベントで閉じる。

## AGENTS.mdへの追記例（非侵襲）

```
BEFORE ANYTHING ELSE: run `maildeck enter <project>` in your shell.
This will:
1. Attach you to the shared Beads graph (no repo files are created).
2. Register or resume your MCP Agent Mail identity and respect existing file leases.
3. Reconfigure Claude Code hooks for telemetry so observability stays live.
Never run bd or the Agent Mail tools directly; always go through maildeck so the project stays clean.
```

## 今後の作業

- `EXEC_PLAN.md` にMailDeck実装の詳細な手順と検証方法を記載した（日本語）。
- 次のステップは ExecPlan の Milestone 1（Hub初期化CLIのプロトタイプ）から着手すること。
