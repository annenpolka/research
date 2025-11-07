# vibe-kanbanコンテナ実行ガイド

## 概要

[vibe-kanban](https://github.com/BloopAI/vibe-kanban)を隔離されたコンテナ環境で安全に実行する方法を調査し、実装例を提供します。

vibe-kanbanは、Claude Code、Gemini CLI、Codex、Ampなどの複数のAIコーディングエージェントを管理するカンバンボードツールです。

## 調査結果

### 既存のDocker対応状況

**良いニュース**: vibe-kanbanは既にDockerfileを含んでおり、コンテナ化に対応しています。

#### 技術スタック
- **バックエンド**: Rust (55.6%)
- **フロントエンド**: TypeScript/JavaScript (42.8%)
- **Node.js**: ≥18
- **pnpm**: ≥8

#### 既存のDockerfile構成

マルチステージビルドを採用しており、効率的かつセキュアな構成になっています：

**ビルドステージ** (`node:24-alpine`):
- Rust環境のセットアップ
- pnpmを使用した依存関係のインストール
- フロントエンドビルド
- Rustバックエンドをリリースモードでビルド

**ランタイムステージ** (`alpine:latest`):
- 非rootユーザー（appuser）での実行
- ポート3000で稼働
- ヘルスチェック機能付き
- tiniを使用したプロセス管理

### 環境変数

実行時に設定可能な主要な環境変数：

- `BACKEND_PORT`: バックエンドポート（デフォルト: 自動割り当て）
- `FRONTEND_PORT`: フロントエンドポート（デフォルト: 3000）
- `HOST`: ホストアドレス（デフォルト: 127.0.0.1）
- `GITHUB_CLIENT_ID`: GitHub OAuth認証（ビルド時）
- `POSTHOG_API_KEY`: PostHog分析（ビルド時）

### コーディングエージェントの設定

vibe-kanbanは複数のAIコーディングエージェント（Claude Code、Gemini CLI、Cursor CLI、GitHub Copilot CLI、OpenAI Codex等）を統合管理します。

⚠️ **重要**: 各エージェントはvibe-kanbanを起動する前に個別に認証が必要です。

詳細な設定方法とAPI keyの管理については、**[CODING_AGENTS.md](CODING_AGENTS.md)** を参照してください。主なトピック：

- サポートされているコーディングエージェント一覧
- 各エージェントの認証方法（API key、ブラウザ認証等）
- コンテナ環境での認証情報の安全な管理
- Docker Secrets / Kubernetes Secrets の使用
- セキュリティベストプラクティス
- トラブルシューティング

**クイックスタート**:

```bash
# 1. .envファイルを作成
cp .env.agents.example .env

# 2. API keyを設定（エディタで編集）
vi .env

# 3. パーミッション設定
chmod 600 .env

# 4. コンテナ起動
docker-compose -f docker-compose.agents.yml up -d

# 5. 設定確認
./check-agents.sh
```

### ホストからの認証情報の引き継ぎ

vibe-kanbanをコンテナで実行する際、SSH鍵やGit認証情報など、ホストの認証情報を安全に引き継ぐ必要がある場合があります。

詳細な実装方法とベストプラクティスについては、**[CREDENTIALS.md](CREDENTIALS.md)** を参照してください。主なトピック：

- SSHキーの引き継ぎ（SSHエージェントフォワーディング推奨）
- Git認証情報の管理
- GitHub OAuth設定
- Docker Secrets / Kubernetes Secrets の使用
- セキュリティベストプラクティス

### コンテナ内でプロジェクトを扱う方法

⚠️ **重要**: 単にコンテナを起動しただけでは、実際のプロジェクトファイルにアクセスできません。

vibe-kanbanで実際の開発作業を行うには、ホストのプロジェクトディレクトリをコンテナの`/repos`にマウントする必要があります。

詳細な実装方法とトラブルシューティングについては、**[PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md)** を参照してください。主なトピック：

- プロジェクトディレクトリのマウント方法
- ファイルパーミッション問題の解決（UID/GID）
- 複数プロジェクトの管理
- リモートプロジェクトへのSSHアクセス
- Docker-in-Docker (DinD) の設定
- 実用的な設定例とトラブルシューティング

**クイックスタート**:

```bash
# 便利スクリプトを使用
./start-with-project.sh ~/projects/my-app

# または手動で
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  -v ~/projects/my-app:/repos/my-app:rw \
  -v ~/.ssh/config:/home/appuser/.ssh/config:ro \
  -v ~/.gitconfig:/home/appuser/.gitconfig:ro \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

## 隔離されたコンテナでの実行方法

### 方法1: 既存のDockerfileを使用

```bash
# リポジトリのクローン
git clone https://github.com/BloopAI/vibe-kanban.git
cd vibe-kanban

# Dockerイメージのビルド
docker build -t vibe-kanban:latest .

# コンテナの実行
docker run -d \
  --name vibe-kanban \
  -p 3000:3000 \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /repos \
  vibe-kanban:latest
```

### 方法2: セキュリティ強化版Docker Compose

より強固な隔離環境を実現するためのdocker-compose.ymlを用意しました（このリポジトリの`docker-compose.yml`を参照）。

主な強化ポイント：
- リソース制限（CPU、メモリ）
- ネットワーク隔離
- 読み取り専用ファイルシステム
- 一時ファイル用のtmpfs
- セキュリティオプション（no-new-privileges）
- ヘルスチェック

```bash
# このディレクトリでDocker Composeを使用
docker-compose up -d
```

### 方法3: より厳格なセキュリティポリシー

完全に隔離された環境で実行する場合は、以下の追加設定を検討してください：

#### gVisorを使用したランタイム隔離

```bash
# gVisorのインストール（Ubuntu/Debian）
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null
sudo apt-get update && sudo apt-get install -y runsc

# gVisorランタイムでコンテナを実行
docker run -d \
  --name vibe-kanban-gvisor \
  --runtime=runsc \
  -p 3000:3000 \
  vibe-kanban:latest
```

#### AppArmorまたはSELinuxプロファイル

AppArmorプロファイル（このリポジトリの`apparmor-profile`を参照）を適用することで、さらなるセキュリティ強化が可能です。

```bash
# AppArmorプロファイルの適用
sudo apparmor_parser -r -W apparmor-profile
docker run -d \
  --name vibe-kanban-apparmor \
  --security-opt="apparmor=docker-vibe-kanban" \
  -p 3000:3000 \
  vibe-kanban:latest
```

### 方法4: Kubernetes/Podでの実行

本番環境やより高度なオーケストレーションが必要な場合は、Kubernetesマニフェストも用意しました（このリポジトリの`kubernetes/`ディレクトリを参照）。

```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## セキュリティ考慮事項

### ネットワーク隔離

- デフォルトでは、コンテナは外部ネットワークにアクセス可能です
- 完全に隔離する場合は `--network none` オプションを使用
- 必要なサービスのみと通信する場合は、カスタムDockerネットワークを作成

### ファイルシステム

- `--read-only` フラグで読み取り専用ファイルシステム
- 必要な書き込み可能領域は `tmpfs` でマウント
- ボリュームマウントは最小限に

### 権限管理

- 既存のDockerfileは非rootユーザー（appuser）で実行
- `--cap-drop=ALL` で不要なケーパビリティを削除
- `--security-opt=no-new-privileges` で権限昇格を防止

### リソース制限

```bash
docker run -d \
  --name vibe-kanban \
  --memory="512m" \
  --cpus="1.0" \
  --pids-limit 100 \
  -p 3000:3000 \
  vibe-kanban:latest
```

## 検証とテスト

### ヘルスチェック

既存のDockerfileにはヘルスチェックが組み込まれています：

```bash
# ヘルスステータスの確認
docker inspect --format='{{.State.Health.Status}}' vibe-kanban
```

### アクセステスト

```bash
# ローカルからのアクセス
curl http://localhost:3000

# またはブラウザで
# http://localhost:3000
```

### ログの確認

```bash
# コンテナログの表示
docker logs vibe-kanban

# リアルタイムでログを追跡
docker logs -f vibe-kanban
```

## トラブルシューティング

### ポートが既に使用されている

```bash
# 別のポートにマッピング
docker run -d -p 8080:3000 vibe-kanban:latest
```

### 権限エラー

```bash
# ボリュームの権限を確認
docker run -d \
  -v /path/to/repos:/repos:rw \
  --user $(id -u):$(id -g) \
  vibe-kanban:latest
```

### メモリ不足

```bash
# メモリ制限を増やす
docker run -d --memory="1g" vibe-kanban:latest
```

## 結論

vibe-kanbanは既にDocker対応しており、隔離されたコンテナ環境での実行が可能です。既存のDockerfileを使用した基本的な実行から、gVisorやAppArmorを使用した高度なセキュリティ設定まで、複数の選択肢があります。

### 推奨事項

1. **開発環境**: 既存のDockerfileをそのまま使用
2. **テスト環境**: Docker Composeでリソース制限を設定
3. **本番環境**: Kubernetes + gVisor + セキュリティポリシー

### 今後の改善点

- ネットワークポリシーのさらなる強化
- シークレット管理の実装（Docker secrets、Kubernetes secrets）
- 定期的なセキュリティスキャン（Trivy、Clairなど）
- コンテナイメージの最小化（distrolessイメージの検討）

## 参考資料

- [vibe-kanban GitHub](https://github.com/BloopAI/vibe-kanban)
- [vibe-kanban公式ドキュメント](https://vibekanban.com/docs)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [gVisor Documentation](https://gvisor.dev/)
