# ユースケース2: マイクロサービス統合テスト

## シナリオ

マイクロサービスアーキテクチャで、複数のサービスを組み合わせた統合テストを実行したい場合。

## 構成例

```
organization/
├── service-api/        # APIサービス
├── service-auth/       # 認証サービス
├── service-db/         # データベースサービス
└── service-frontend/   # フロントエンドアプリ
```

## ワークフロー実装

```yaml
name: Integration Testing

on: [push, pull_request]

jobs:
  integration-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout frontend service
        uses: actions/checkout@v4
        with:
          path: frontend

      - name: Checkout API service
        uses: actions/checkout@v4
        with:
          repository: organization/service-api
          token: ${{ secrets.GH_PAT }}
          path: api

      - name: Checkout auth service
        uses: actions/checkout@v4
        with:
          repository: organization/service-auth
          token: ${{ secrets.GH_PAT }}
          path: auth

      - name: Setup services with Docker Compose
        run: |
          cat > docker-compose.yml << 'EOF'
          version: '3.8'
          services:
            api:
              build: ./api
              ports:
                - "3000:3000"
            auth:
              build: ./auth
              ports:
                - "3001:3001"
            frontend:
              build: ./frontend
              ports:
                - "8080:8080"
              depends_on:
                - api
                - auth
          EOF

      - name: Start all services
        run: docker-compose up -d

      - name: Wait for services to be ready
        run: |
          sleep 10
          curl -f http://localhost:3000/health || exit 1
          curl -f http://localhost:3001/health || exit 1

      - name: Run integration tests
        run: |
          cd frontend
          npm install
          npm run test:integration

      - name: Cleanup
        if: always()
        run: docker-compose down
```

## メリット

1. **実環境に近いテスト**: 複数サービスの連携を検証
2. **早期発見**: インターフェース変更による問題を検出
3. **CI/CD統合**: 自動化されたテストパイプライン

## 応用例

### 特定のバージョンを組み合わせてテスト

```yaml
- name: Checkout API v1.2.3
  uses: actions/checkout@v4
  with:
    repository: organization/service-api
    ref: v1.2.3
    token: ${{ secrets.GH_PAT }}
    path: api

- name: Checkout Auth develop branch
  uses: actions/checkout@v4
  with:
    repository: organization/service-auth
    ref: develop
    token: ${{ secrets.GH_PAT }}
    path: auth
```

### マトリックス戦略で複数バージョンをテスト

```yaml
strategy:
  matrix:
    api-version: [v1.2.0, v1.3.0, main]

steps:
  - name: Checkout API ${{ matrix.api-version }}
    uses: actions/checkout@v4
    with:
      repository: organization/service-api
      ref: ${{ matrix.api-version }}
      token: ${{ secrets.GH_PAT }}
      path: api
```
