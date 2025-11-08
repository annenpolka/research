# 正しいインストール方法

## ⚠️ 重要な訂正

以前のドキュメントで `claude-code plugin install` というコマンドを記載していましたが、これは**誤り**です。

## Claude Codeの正しい使い方

### 1. Claude Codeのインストール

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# または npm経由（Node.js 18+必要）
npm install -g @anthropic-ai/claude-code

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

### 2. 動作確認

```bash
claude doctor
```

### 3. Claude Codeの起動

```bash
claude
```

これでClaude Codeの対話セッションが開始されます。

## Swarm Coordinatorプラグインのインストール

### 方法1: マーケットプレイス経由（推奨）

Claude Codeを起動後、**Claude内で**以下を実行：

```
/plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
```

次に、プラグインをインストール：

```
/plugin install swarm-coordinator
```

または対話的に：

```
/plugin
```

→ "Browse Plugins" を選択 → "swarm-coordinator" を選択

### 方法2: GitHub URL直接指定

Claude Code内で：

```
/plugin marketplace add annenpolka/research
```

その後：

```
/plugin install swarm-coordinator@annenpolka
```

### 方法3: ローカルインストール（開発用）

```bash
# リポジトリをクローン
git clone https://github.com/annenpolka/research.git
cd research/multi-agent-coordinator/plugin-v2
```

Claude Codeを起動（このディレクトリ内で）：

```bash
claude
```

Claude内で：

```
/plugin marketplace add .
/plugin install swarm-coordinator
```

## プラグイン管理コマンド

Claude Code内で使用できるコマンド：

```
/plugin                              # 対話的メニュー
/plugin marketplace list             # マーケットプレイス一覧
/plugin marketplace add <url>        # マーケットプレイス追加
/plugin marketplace remove <name>    # マーケットプレイス削除
/plugin install <name>               # プラグインインストール
/plugin enable <name>                # プラグイン有効化
/plugin disable <name>               # プラグイン無効化
/plugin uninstall <name>             # プラグインアンインストール
/help                                # 全コマンド確認
```

## 使用例

### ステップ1: Claude Code起動

```bash
$ claude
```

### ステップ2: マーケットプレイス追加

```
Claude> /plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json

✓ Marketplace added successfully
```

### ステップ3: プラグインインストール

```
Claude> /plugin install swarm-coordinator

✓ Installing swarm-coordinator...
✓ Plugin installed successfully
```

### ステップ4: 確認

```
Claude> /help

Available commands:
  /plugin                    Plugin management
  /help                      Show this help
  ...
  (swarm-coordinator skills are now available)
```

### ステップ5: 使用開始

```
Claude> Check the swarm state

[Claudeが自動的にswarm-coordinatorスキルを使用]

## 🤖 Active Agents (0)
No active agents.

## 📋 Tasks
...
```

## トラブルシューティング

### "command not found: claude"

Claude Codeがインストールされていません：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

その後、新しいターミナルを開くか：

```bash
source ~/.bashrc  # または ~/.zshrc
```

### "/plugin: unknown command"

古いバージョンのClaude Codeを使用している可能性があります：

```bash
# npmでインストールした場合
npm update -g @anthropic-ai/claude-code

# ネイティブインストールの場合
curl -fsSL https://claude.ai/install.sh | bash
```

### "Marketplace not found"

URL が正しいか確認：

```bash
curl -I https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
```

HTTP 200が返ってくれば正常です。

### プラグインが動作しない

1. Pythonバージョン確認：
   ```bash
   python3 --version  # 3.7以上必要
   ```

2. スクリプトの実行権限確認：
   ```bash
   ls -la ~/.claude/plugins/swarm-coordinator/skills/swarm-coordinator/scripts/
   # すべて実行可能（-rwxr-xr-x）であることを確認
   ```

3. Claude Codeを再起動：
   ```
   /exit
   ```
   その後、`claude` で再起動

## チーム向けセットアップ

プロジェクトの `.claude/settings.json` に追加：

```json
{
  "marketplaces": [
    {
      "url": "https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json",
      "name": "swarm-coordinator-marketplace"
    }
  ],
  "plugins": {
    "swarm-coordinator": {
      "enabled": true,
      "settings": {
        "lockTimeoutMinutes": 5,
        "maxAgents": 10
      }
    }
  }
}
```

チームメンバーがプロジェクトを開くと、自動的にマーケットプレイスが追加され、プラグインが利用可能になります。

## まとめ

**誤り:**
```bash
claude-code plugin install swarm-coordinator  # ❌ このコマンドは存在しない
```

**正しい方法:**
```bash
claude                                         # ✅ Claude Codeを起動
```

Claude内で：
```
/plugin marketplace add <URL>                  # ✅ マーケットプレイス追加
/plugin install swarm-coordinator              # ✅ プラグインインストール
```

詳細は公式ドキュメントを参照：
- https://code.claude.com/docs/en/getting-started
- https://code.claude.com/docs/en/plugin-marketplaces
