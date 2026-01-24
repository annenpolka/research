# Clawdbot 調査レポート

## 概要

**Clawdbot**は、**個人用AIアスタント**をセルフホストして運用するためのオープンソースツールです。WhatsApp、Telegram、Slack、Discord、Signal、iMessageなど、普段使っている**複数のメッセージングチャンネル**からAIアシスタントと会話できます。

- リポジトリ: https://github.com/clawdbot/clawdbot
- ドキュメント: https://docs.clawd.bot
- ライセンス: MIT

## 主な機能

### 1. マルチチャンネルメッセージング統合

以下のプラットフォームに対応:

| カテゴリ | プラットフォーム |
|---------|-----------------|
| コア | WhatsApp (Baileys)、Telegram (grammY)、Slack (Bolt)、Discord (discord.js)、Signal (signal-cli)、iMessage |
| 拡張 | Microsoft Teams、Matrix、BlueBubbles、Zalo、Mattermost、Nextcloud Talk、Nostr |

### 2. Gateway (コントロールプレーン)

- ローカルで動作するWebSocketベースの制御サーバー
- セッション管理、チャンネル接続、ツール実行、イベント処理を一元管理
- デフォルトポート: 18789

### 3. 音声機能

- **Voice Wake**: 常時オンの音声認識（macOS/iOS/Android）
- **Talk Mode**: 連続会話モード
- ElevenLabs TTSとの統合

### 4. ブラウザ制御

- Chromium/Chromeの専用インスタンスをCDP (Chrome DevTools Protocol) 経由で操作
- スナップショット取得、アクション実行、ファイルアップロード

### 5. Canvas (A2UI)

- エージェント駆動のビジュアルワークスペース
- リアルタイムでUIを描画・操作可能

### 6. ノード機能

- カメラスナップ/クリップ、画面録画
- 位置情報取得、通知送信
- macOSの`system.run`/`system.notify`

### 7. 自動化

- **Cron**: スケジュール実行
- **Webhooks**: 外部サービス連携
- **Gmail Pub/Sub**: メール通知トリガー

## スキル（プラグイン）一覧

50以上のスキルが同梱:

| カテゴリ | スキル |
|---------|--------|
| パスワード管理 | 1password |
| ノート | Apple Notes, Bear Notes, Notion, Obsidian |
| タスク管理 | Apple Reminders, Things, Trello |
| 開発 | GitHub, coding-agent, tmux |
| メディア | Spotify Player, OpenAI Whisper, video-frames, camsnap, peekaboo |
| スマートホーム | OpenHue, Sonos CLI |
| AI連携 | Gemini, OpenAI Image Gen |
| コミュニケーション | Discord, Slack, iMessage |
| その他 | Weather, local-places, food-order, model-usage |

## コンパニオンアプリ

| プラットフォーム | 機能 |
|-----------------|------|
| macOS | メニューバーアプリ（Gateway制御、Voice Wake、PTT、WebChat） |
| iOS | Canvas、Voice Wake、カメラ、画面録画、Bonjour pairing |
| Android | Canvas、Talk Mode、カメラ、SMS連携 |

## 対応AIモデル

- **Anthropic Claude** (Pro/Max推奨、特にOpus 4.5)
- **OpenAI** (ChatGPT/Codex)
- OAuth認証またはAPIキーで接続

## インストール方法

```bash
# Node.js 22以上が必要
npm install -g clawdbot@latest

# ウィザードでセットアップ（デーモンもインストール）
clawdbot onboard --install-daemon

# Gateway起動
clawdbot gateway --port 18789 --verbose

# メッセージ送信
clawdbot message send --to +1234567890 --message "Hello from Clawdbot"

# エージェントに話しかける
clawdbot agent --message "Ship checklist" --thinking high
```

## セキュリティ機能

- **DMペアリング**: 不明な送信者からのメッセージはペアリングコードで認証
- **許可リスト**: チャンネルごとにアクセス許可を設定
- **Tailscale連携**: Serve/Funnelでセキュアなリモートアクセス

## アーキテクチャ

```
WhatsApp / Telegram / Slack / Discord / Signal / iMessage / ...
               │
               ▼
┌───────────────────────────────┐
│            Gateway            │
│       (control plane)         │
│     ws://127.0.0.1:18789      │
└──────────────┬────────────────┘
               │
               ├─ Pi agent (RPC)
               ├─ CLI (clawdbot …)
               ├─ WebChat UI
               ├─ macOS app
               └─ iOS / Android nodes
```

## 技術スタック

- **ランタイム**: Node.js 22+
- **言語**: TypeScript (ESM)
- **エージェント**: Pi Agent (RPC mode) by @mariozechner
- **UI**: Lit, mini-lit
- **パッケージマネージャ**: pnpm
- **テスト**: Vitest
- **Lint/Format**: oxlint, oxfmt

## ユースケース

1. **個人用AIアシスタント**: WhatsAppやTelegramからAIに質問・指示
2. **自動化**: CronでスケジュールしたタスクをAIが実行
3. **スマートホーム制御**: 音声でライトやスピーカーを操作
4. **開発支援**: GitHubと連携してIssue管理やコーディング支援
5. **マルチデバイス連携**: macOS/iOS/AndroidでCanvas共有

## 特徴的な点

- Claude Codeのような開発支援AIとは異なり、**日常生活のあらゆるメッセージングチャンネルからAIにアクセス**することに重点
- **ローカルファースト**: 自分のデバイスで動作、データは自分で管理
- **拡張性**: スキルシステムとプラグインSDKで機能追加可能
- **マルチエージェント**: 複数のセッション間でエージェント連携（sessions_* tools）

## 関連リンク

- [GitHub](https://github.com/clawdbot/clawdbot)
- [ドキュメント](https://docs.clawd.bot)
- [Discord](https://discord.gg/clawd)
- [ClawdHub (スキルレジストリ)](https://ClawdHub.com)
