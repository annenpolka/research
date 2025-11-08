# Swarm Coordinator - Claude Code Plugin

**1コマンドでインストール、即座に使えるマルチエージェント調整システム**

## プラグインとして使う利点

従来の手動セットアップと比較：

| 項目 | 手動セットアップ | **プラグイン** |
|------|------------------|----------------|
| **インストール** | 5-10分（複数ステップ） | **10秒（1コマンド）** |
| **セットアップ** | ファイルコピー、npm build | **自動** |
| **更新** | 手動でgit pull、再ビルド | **`/plugin update`** |
| **チーム共有** | 手順書を共有 | **.claude/settings.json** |
| **削除** | 手動でファイル削除 | **`/plugin uninstall`** |

## インストール

### 方法1: Marketplace経由（推奨）

```bash
# プロジェクトルートで
claude-code

# Claude内で
/plugin install swarm-coordinator
```

### 方法2: GitHubから直接

```bash
# ローカルにクローン
git clone https://github.com/annenpolka/research.git
cd research/multi-agent-coordinator/plugin

# インストール
claude-code plugin install .
```

### 方法3: チーム設定（自動インストール）

プロジェクトの `.claude/settings.json` に追加：

```json
{
  "plugins": [
    {
      "source": "https://github.com/annenpolka/research/tree/main/multi-agent-coordinator/plugin",
      "name": "swarm-coordinator"
    }
  ]
}
```

チームメンバーがプロジェクトを開くと自動的にインストールされます。

## 初回セットアップ（プラグインインストール後）

プラグインがインストールされると、自動的に以下が設定されます：

- ✅ フック（session-start, pre-tool-use, post-tool-use, session-end）
- ✅ MCPサーバー（swarm-coordinator）
- ✅ Swarmディレクトリ（.claude/swarm/）

唯一の手動ステップ：

```bash
# MCPサーバーのビルド（初回のみ）
cd .claude/plugins/swarm-coordinator/mcp-servers/swarm-coordinator
npm install
npm run build
```

**注**: 将来的にはプラグインのpostinstallスクリプトで自動化予定。

## 使い方

### シングルエージェント（通常使用）

```bash
# 通常通りClaude Codeを起動
claude-code

# プラグインが自動的に動作
# - ファイル編集時に自動ロック
# - セッション情報を記録
```

### マルチエージェント（並行実行）

#### ターミナル1: エージェントA

```bash
export CLAUDE_AGENT_NAME="AgentA"
claude-code
```

Claude内で：
```
タスクをクレームしてください
> swarm_claim_task
```

#### ターミナル2: エージェントB

```bash
export CLAUDE_AGENT_NAME="AgentB"
claude-code
```

#### エージェント間通信

```
AgentBにメッセージを送ってください
> swarm_send_message
  - recipient: AgentB
  - subject: API完成
  - body: 認証エンドポイントが使用可能です
```

#### 状態確認

```
Swarm全体の状態を確認
> swarm_get_state
```

## 利用可能なツール

プラグインは以下のMCPツールを提供：

1. **swarm_send_message** - エージェント間メッセージング
2. **swarm_get_messages** - 受信メッセージ取得
3. **swarm_claim_task** - タスクをクレーム
4. **swarm_complete_task** - タスク完了報告
5. **swarm_get_state** - Swarm状態クエリ

## タスク定義（オプション）

`.claude/swarm/tasks.jsonl` にタスクを定義：

```jsonl
{"id":"task-001","description":"認証API実装","status":"pending","dependencies":[],"priority":10,"files":["src/auth/**"]}
{"id":"task-002","description":"ダッシュボードUI","status":"pending","dependencies":[],"priority":8,"files":["src/dashboard/**"]}
```

## 設定のカスタマイズ

プラグイン設定は `.claude/plugins/swarm-coordinator/config.json` で変更可能：

```json
{
  "lockTimeoutMinutes": 5,
  "maxAgents": 10,
  "enableObservability": false
}
```

## プラグインの更新

```bash
# 最新バージョンに更新
/plugin update swarm-coordinator

# または
claude-code plugin update swarm-coordinator
```

## アンインストール

```bash
# プラグインを削除
/plugin uninstall swarm-coordinator

# Swarmデータも削除する場合
rm -rf .claude/swarm
```

## トラブルシューティング

### MCPサーバーが起動しない

```bash
# ビルド確認
cd .claude/plugins/swarm-coordinator/mcp-servers/swarm-coordinator
npm run build

# ログ確認
cat .claude/logs/mcp-swarm-coordinator.log
```

### フックが動作しない

```bash
# フック設定確認
cat .claude/hooks/hooks.json

# Python依存関係確認
python3 -c "import json; print('OK')"
```

### プラグインが見つからない

```bash
# インストール済みプラグイン一覧
/plugin list

# プラグインディレクトリ確認
ls -la .claude/plugins/
```

## プラグイン開発者向け

### ディレクトリ構造

```
plugin/
├── .claude-plugin/
│   └── plugin.json          # マニフェスト
├── hooks/
│   └── coordination.py      # フックスクリプト
├── mcp-servers/
│   └── swarm-coordinator/
│       ├── src/
│       │   └── index.ts     # MCPサーバー実装
│       ├── package.json
│       └── tsconfig.json
└── README.md
```

### ローカルテスト

```bash
# プラグインディレクトリで
claude-code plugin install .

# テストプロジェクトで確認
cd /path/to/test-project
claude-code
```

### Marketplace公開

1. `.claude-plugin/marketplace.json` 作成
2. GitHubリポジトリにプッシュ
3. MarketplaceにPR送信

```json
{
  "name": "My Marketplace",
  "plugins": [
    {
      "name": "swarm-coordinator",
      "source": "https://github.com/your-org/your-repo/tree/main/plugin",
      "category": "productivity",
      "tags": ["multi-agent", "coordination"]
    }
  ]
}
```

## 比較: 手動 vs プラグイン

### 手動セットアップ

```bash
# ステップ1: ファイルコピー
mkdir -p .claude/hooks
cp coordination.py .claude/hooks/
cp hooks.json .claude/hooks/

# ステップ2: MCPサーバーセットアップ
mkdir -p .claude/mcp-servers/swarm-coordinator
cp -r mcp-server/* .claude/mcp-servers/swarm-coordinator/
cd .claude/mcp-servers/swarm-coordinator
npm install
npm run build

# ステップ3: MCP設定
cat > .claude/.mcp.json <<EOF
{...}
EOF

# ステップ4: .gitignore更新
echo ".claude/swarm/.cache/" >> .gitignore

# 合計: 5-10分
```

### プラグインインストール

```bash
# たった1コマンド
claude-code plugin install swarm-coordinator

# MCPビルド（初回のみ、将来は自動化）
cd .claude/plugins/swarm-coordinator/mcp-servers/swarm-coordinator
npm install && npm run build

# 合計: 30秒 + ビルド時間
```

## よくある質問

**Q: 既存プロジェクトに影響しますか？**
A: いいえ。`.claude/`ディレクトリのみ使用し、プロジェクトコードには一切変更を加えません。

**Q: 他のプラグインと競合しますか？**
A: フックとMCPサーバー名が重複しない限り問題ありません。

**Q: パフォーマンスへの影響は？**
A: ツール呼び出しごとに10-20msのオーバーヘッド（ほぼ無視できるレベル）。

**Q: セキュリティは？**
A: フックはPythonスクリプト、MCPはNode.jsサーバーとして実行。信頼できるソースからのみインストールしてください。

**Q: オフラインで動作しますか？**
A: はい。すべてローカルで動作します。

## コミュニティとサポート

- **Issues**: [GitHub Issues](https://github.com/annenpolka/research/issues)
- **ドキュメント**: [README.md](./README.md)
- **設計詳細**: [DESIGN.md](./DESIGN.md)
- **比較分析**: [COMPARISON.md](./COMPARISON.md)

## ライセンス

MIT License

---

**プラグイン化により、Swarm Coordinatorは誰でも簡単に使えるツールになりました。**
