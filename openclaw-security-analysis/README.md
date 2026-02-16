# OpenClaw セキュリティ機構分析

## 概要

[openclaw/openclaw](https://github.com/openclaw/openclaw) のセキュリティ機構を包括的に分析したレポート。OpenClawは、複数のメッセージングチャネル（WhatsApp、Telegram、Slack、Discord等）をAIモデルに接続するパーソナルAIアシスタントプラットフォームである。TypeScript/Node.jsで構築されている。

## セキュリティアーキテクチャの全体像

OpenClawのセキュリティは以下の7つの層で構成されている:

```
┌──────────────────────────────────────────────────────┐
│  1. ネットワーク境界制御（バインド/CORS/オリジン検証）   │
├──────────────────────────────────────────────────────┤
│  2. 認証（トークン/パスワード/Tailscale/Trusted Proxy）│
├──────────────────────────────────────────────────────┤
│  3. レート制限（スライディングウィンドウ方式）           │
├──────────────────────────────────────────────────────┤
│  4. 認可・ツールポリシー（危険ツール制御/昇格実行）      │
├──────────────────────────────────────────────────────┤
│  5. 入力検証・サニタイゼーション（プロンプト注入防御）    │
├──────────────────────────────────────────────────────┤
│  6. ファイルシステム・設定保護（権限/秘匿情報墨消し）    │
├──────────────────────────────────────────────────────┤
│  7. セキュリティ監査システム（自動チェック・30項目以上）  │
└──────────────────────────────────────────────────────┘
```

---

## 1. ネットワーク境界制御

### Gatewayバインドモード

**ファイル**: `src/gateway/auth.ts`, `src/gateway/net.ts`

| モード | 説明 | リスクレベル |
|--------|------|-------------|
| `loopback` (デフォルト) | 127.0.0.1/::1のみ | 最も安全 |
| `lan` | LANインターフェース | 中リスク |
| Tailscale `serve` | tailnet内のみ | 低リスク |
| Tailscale `funnel` | 公開インターネット | 高リスク |

デフォルトでloopbackのみにバインドし、外部公開を意図的に困難にしている設計。

### CORS / オリジン検証

**ファイル**: `src/gateway/origin-check.ts`

```typescript
// ブラウザOriginの3段階検証:
// 1. 明示的な許可リストとの照合
// 2. リクエストHostヘッダーとの一致確認
// 3. ループバックアドレス同士の接続許可
export function checkBrowserOrigin(params: {
  requestHost?: string;
  origin?: string;
  allowedOrigins?: string[];
}): OriginCheckResult
```

### セキュリティヘッダー

**ファイル**: `src/gateway/control-ui.ts`

Control UIのHTTPレスポンスに以下のヘッダーを付与:

- `X-Frame-Options: DENY` — クリックジャッキング防止
- `Content-Security-Policy: frame-ancestors 'none'` — iframe埋め込み防止
- `X-Content-Type-Options: nosniff` — MIMEタイプスニッフィング防止
- `Cache-Control: no-cache` — 機密コンテンツのキャッシュ防止

---

## 2. 認証

### マルチモード認証システム

**ファイル**: `src/gateway/auth.ts`

OpenClawは6つの認証方式をサポートする:

| 方式 | 実装 | 用途 |
|------|------|------|
| **トークン認証** | Bearer token (Authorization ヘッダー) | API/WebSocket接続 |
| **パスワード認証** | タイミングセーフ比較 | 簡易認証 |
| **Tailscale認証** | Whois検証 + ユーザー照合 | tailnet内認証 |
| **デバイストークン** | デバイスID + スコープ + 署名 | モバイル/デスクトップアプリ |
| **Trusted Proxy** | リバースプロキシ委任 (Pomerium, Caddy, nginx) | エンタープライズ環境 |
| **自動生成トークン** | `crypto.randomBytes(24)` | ブラウザControl UI |

### タイミングセーフな秘密比較

**ファイル**: `src/security/secret-equal.ts`

```typescript
import { timingSafeEqual } from "node:crypto";

export function safeEqualSecret(provided: string, expected: string): boolean {
  const providedBuffer = Buffer.from(provided);
  const expectedBuffer = Buffer.from(expected);
  if (providedBuffer.length !== expectedBuffer.length) {
    return false;  // 長さ漏洩は許容（トークンは固定長想定）
  }
  return timingSafeEqual(providedBuffer, expectedBuffer);
}
```

Node.jsの`crypto.timingSafeEqual()`を使用し、タイミングサイドチャネル攻撃を防止する。

### Tailscale認証の多段検証

```
1. Tailscaleヘッダーからユーザー情報を取得
2. リクエストがTailscaleプロキシ経由であることを確認（ループバック + プロキシヘッダー）
3. X-Forwarded-ForからクライアントIPを抽出
4. Tailscale Whois APIでIPからユーザーを照会
5. ヘッダーのログイン名とWhois結果を照合（大文字小文字無視）
```

### Trusted Proxy認証

```
1. リクエスト元IPが trustedProxies リストに含まれるか確認
2. requiredHeaders が全て存在するか検証
3. userHeader からユーザー名を抽出
4. allowUsers リストでユーザーのアクセス権を確認
```

---

## 3. レート制限

**ファイル**: `src/gateway/auth-rate-limit.ts`

### スライディングウィンドウ方式

```
デフォルト設定:
- maxAttempts: 10     (最大失敗試行回数)
- windowMs: 60,000    (1分のスライディングウィンドウ)
- lockoutMs: 300,000  (5分のロックアウト)
- exemptLoopback: true (ローカル接続は除外)
```

### 設計特徴

- **スコープ分離**: shared-secret認証とdevice-token認証で独立カウンタ
- **IP単位追跡**: `{scope}:{ip}` のキーで個別追跡
- **ループバック免除**: ローカルCLIセッションがロックアウトされない保護
- **自動プルーニング**: 60秒ごとに期限切れエントリをクリーンアップ（メモリリーク防止）
- **成功時リセット**: 認証成功時にそのIPのカウンタをリセット

```
認証フロー:
[リクエスト] → [ループバック?] → Yes → 認証処理（レート制限なし）
                    ↓ No
              [ロックアウト中?] → Yes → 拒否（retryAfterMs付き）
                    ↓ No
              [ウィンドウ内の試行回数確認]
                    ↓
              [制限超過?] → Yes → ロックアウト開始 → 拒否
                    ↓ No
              [認証処理] → 成功 → カウンタリセット
                         → 失敗 → 試行記録
```

---

## 4. 認可・ツールポリシー

### 危険ツールの制御

**ファイル**: `src/security/dangerous-tools.ts`

#### Gateway HTTP経由で禁止されるツール

```typescript
export const DEFAULT_GATEWAY_HTTP_TOOL_DENY = [
  "sessions_spawn",    // セッション生成 → リモートコード実行のリスク
  "sessions_send",     // セッション間メッセージ注入
  "gateway",           // ゲートウェイ制御プレーン操作
  "whatsapp_login",    // インタラクティブセットアップ（HTTPでは動作しない）
];
```

#### ACP (Automation Control Plane) で承認必須のツール

```typescript
export const DANGEROUS_ACP_TOOL_NAMES = [
  "exec", "spawn", "shell",       // コマンド実行
  "sessions_spawn", "sessions_send", // セッション操作
  "gateway",                        // 制御プレーン
  "fs_write", "fs_delete", "fs_move", // ファイルシステム変更
  "apply_patch",                    // パッチ適用
];
```

### ノードコマンド拒否リスト

**ファイル**: `src/gateway/node-command-policy.ts`

プラットフォーム別に危険なコマンドを制御:
- `camera.snap` — カメラアクセス
- `screen.record` — 画面録画
- `contacts.add` — 連絡先変更
- `sms.send` — SMS送信
- `calendar.add` — カレンダー変更

### 昇格実行モード

**ファイル**: `src/security/audit.ts:531-563`

- チャネル別の許可リスト (`tools.elevated.allowFrom`)
- ワイルドカード `*` 使用時は critical 警告
- 25エントリ超のリストは warn 警告

### ファイルシステムハードニング

**SECURITY.md** に記載:
- `tools.exec.applyPatch.workspaceOnly: true` — パッチ適用をワークスペース内に制限
- `tools.fs.workspaceOnly: true` — ファイル操作をワークスペース内に制限

---

## 5. 入力検証・サニタイゼーション

### プロンプトインジェクション検出

**ファイル**: `src/security/external-content.ts`

外部からの入力に対して、11パターンの正規表現で疑わしい内容を検出:

```typescript
const SUSPICIOUS_PATTERNS = [
  /ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)/i,
  /disregard\s+(all\s+)?(previous|prior|above)/i,
  /forget\s+(everything|all|your)\s+(instructions?|rules?|guidelines?)/i,
  /you\s+are\s+now\s+(a|an)\s+/i,
  /new\s+instructions?:/i,
  /system\s*:?\s*(prompt|override|command)/i,
  /\bexec\b.*command\s*=/i,
  /elevated\s*=\s*true/i,
  /rm\s+-rf/i,
  /delete\s+all\s+(emails?|files?|data)/i,
  /<\/?system>/i,
  /\]\s*\n\s*\[?(system|assistant|user)\]?:/i,
];
```

### 外部コンテンツの安全なラッピング

外部ソース（email, webhook, API, browser, web_search, web_fetch）からのコンテンツは:

1. **境界マーカーで囲む**: `<<<EXTERNAL_UNTRUSTED_CONTENT>>>` / `<<<END_EXTERNAL_UNTRUSTED_CONTENT>>>`
2. **セキュリティ警告を付与**: LLMに対してコンテンツが外部の信頼できないソースであることを明示
3. **マーカー注入を防止**: コンテンツ内のマーカー文字列を `[[MARKER_SANITIZED]]` に置換

### Unicode ホモグリフ対策

**ファイル**: `src/security/external-content.ts:87-125`

フルウィドス文字やUnicodeの角括弧ホモグリフをASCII等価に正規化し、Unicodeを利用したマーカー偽装を防止:

```
対処する文字例:
- ＜/＞ (全角) → </>
- 〈/〉 (CJK角括弧) → </>
- ‹/› (引用符) → </>
- ⟨/⟩ (数学記号) → </>
- ﹤/﹥ (Small Form) → </>
```

---

## 6. ファイルシステム・設定保護

### ファイルパーミッション監査

**ファイル**: `src/security/audit-fs.ts`

POSIXとWindowsの両方でファイル権限を検査:

| チェック対象 | 推奨パーミッション | 問題時の深刻度 |
|-------------|-------------------|---------------|
| 状態ディレクトリ (world-writable) | 0o700 | critical |
| 状態ディレクトリ (group-writable) | 0o700 | warn |
| 設定ファイル (world-writable/group-writable) | 0o600 | critical |
| 設定ファイル (world-readable) | 0o600 | critical |
| 設定ファイル (group-readable) | 0o600 | warn |
| シンボリックリンク検出 | — | warn |

Windows環境では `icacls` を使用したACL検査にも対応。

### 秘匿情報の墨消し (Redaction)

**ファイル**: `src/config/redact-snapshot.ts`

設定ファイル内の機密値を `__OPENCLAW_REDACTED__` に置換する多層システム:

1. **スキーマヒントベース**: `ConfigUiHints` のsensitiveフラグに基づく正確な墨消し
2. **推測ベース**: ヒントがない場合、パス名のパターンマッチングで検出
3. **ラウンドトリップ安全**: Web UIでの設定編集→保存時に、元の値を自動復元
4. **Raw JSON5テキスト墨消し**: パース済みオブジェクトだけでなく、ソーステキストも墨消し
5. **環境変数プレースホルダー保持**: `${ENV_VAR}` 形式は墨消し対象外

### 同期フォルダリスク検出

iCloud, Dropbox, Google Drive, OneDriveの管理下にある状態/設定ディレクトリを検出し警告。

---

## 7. セキュリティ監査システム

**ファイル**: `src/security/audit.ts`

`openclaw security audit` コマンドで実行可能な包括的な自動監査。`--deep` オプションでGateway接続テストも実施。

### 監査チェック項目一覧

| カテゴリ | チェックID | 深刻度 | 内容 |
|---------|-----------|--------|------|
| Gateway | `gateway.bind_no_auth` | critical | loopback以外でauth未設定 |
| Gateway | `gateway.loopback_no_auth` | critical | loopbackでもauth未設定（プロキシ経由で露出の可能性） |
| Gateway | `gateway.tailscale_funnel` | critical | Funnel有効（公開インターネット露出） |
| Gateway | `gateway.tailscale_serve` | info | Serve有効（tailnet内のみ） |
| Gateway | `gateway.token_too_short` | warn | トークンが24文字未満 |
| Gateway | `gateway.auth_no_rate_limit` | warn | 非loopbackでレート制限なし |
| Gateway | `gateway.tools_invoke_http.dangerous_allow` | critical/warn | 危険ツールのHTTP許可 |
| Gateway | `gateway.trusted_proxies_missing` | warn | リバースプロキシヘッダー未信頼 |
| Control UI | `gateway.control_ui.insecure_auth` | critical | HTTP上のトークン認証を許可 |
| Control UI | `gateway.control_ui.device_auth_disabled` | critical | デバイス認証の無効化 |
| Trusted Proxy | `gateway.trusted_proxy_auth` | critical | Trusted Proxy有効（設定確認要） |
| Trusted Proxy | `gateway.trusted_proxy_no_proxies` | critical | プロキシIP未設定 |
| Trusted Proxy | `gateway.trusted_proxy_no_user_header` | critical | userHeader未設定 |
| Trusted Proxy | `gateway.trusted_proxy_no_allowlist` | warn | ユーザー制限なし |
| Browser | `browser.control_no_auth` | critical | ブラウザ制御にauth未設定 |
| Browser | `browser.remote_cdp_http` | warn | リモートCDPがHTTP |
| FS | `fs.state_dir.perms_world_writable` | critical | 状態ディレクトリがworld-writable |
| FS | `fs.config.perms_world_readable` | critical | 設定ファイルがworld-readable |
| Logging | `logging.redact_off` | warn | ツール出力の墨消しが無効 |
| Elevated | `tools.elevated.allowFrom.*.wildcard` | critical | 昇格許可リストにワイルドカード |
| Deep | `gateway.probe_failed` | warn | Gateway接続テスト失敗 |
| Config | secrets in config | warn | 設定ファイル内の埋め込み秘密 |
| Model | model hygiene | warn | レガシー/弱いモデルの使用 |
| Sync | synced folder | warn | クラウド同期フォルダの使用 |
| Sandbox | docker noop | warn | Dockerサンドボックスが無効 |
| Hooks | hooks hardening | warn | フックのハードニング不足 |

---

## Docker セキュリティ

**ファイル**: `Dockerfile`, `SECURITY.md`

推奨されるセキュアなDocker実行:

```bash
docker run --read-only --cap-drop=ALL \
  -v openclaw-data:/app/data \
  openclaw/openclaw:latest
```

- 非rootユーザー (`node`) での実行
- `--read-only` でファイルシステム保護
- `--cap-drop=ALL` で不要な権限を削除

---

## CI/CDセキュリティ

- **detect-secrets**: `.detect-secrets.cfg` / `.secrets.baseline` による自動秘密検出
- **pre-commit hooks**: `git-hooks/` でコミット前の検証
- **Dependabot**: 依存関係の自動更新
- **GitHub Security Advisories (GHSA)**: 脆弱性の管理

---

## 結論

OpenClawのセキュリティ設計は「デフォルトで安全 (Secure by Default)」の原則に基づいている:

1. **最小権限**: デフォルトでloopbackバインド、危険ツールはHTTP経由で禁止
2. **多層防御**: ネットワーク境界→認証→レート制限→認可→入力検証→FS保護→監査の7層
3. **タイミング攻撃対策**: `crypto.timingSafeEqual()` による定数時間比較
4. **プロンプトインジェクション対策**: 外部コンテンツの境界マーカー + Unicode正規化
5. **設定の安全な管理**: 秘匿情報の自動墨消しとラウンドトリップ安全な復元
6. **自動監査**: 30項目以上のセキュリティチェックを `openclaw security audit` で一括実行

ただし、`SECURITY.md` に明記されているように、プロンプトインジェクション攻撃はスコープ外とされており、検出はログ目的のみで、コンテンツ自体は処理される設計である。
