# ユースケース3: ドキュメント自動生成

## シナリオ

複数のリポジトリのドキュメントを集約して、統合ドキュメントサイトを生成したい場合。

## 構成例

```
organization/
├── docs-site/          # ドキュメントサイトリポジトリ
├── backend-api/        # バックエンドAPI
├── frontend-app/       # フロントエンドアプリ
└── mobile-app/         # モバイルアプリ
```

## ワークフロー実装

```yaml
name: Build Documentation Site

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 毎日実行
  workflow_dispatch:

jobs:
  build-docs:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout docs site
        uses: actions/checkout@v4
        with:
          path: docs

      - name: Checkout backend API
        uses: actions/checkout@v4
        with:
          repository: organization/backend-api
          token: ${{ secrets.GH_PAT }}
          path: sources/backend

      - name: Checkout frontend app
        uses: actions/checkout@v4
        with:
          repository: organization/frontend-app
          token: ${{ secrets.GH_PAT }}
          path: sources/frontend

      - name: Checkout mobile app
        uses: actions/checkout@v4
        with:
          repository: organization/mobile-app
          token: ${{ secrets.GH_PAT }}
          path: sources/mobile

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Collect API documentation
        run: |
          mkdir -p docs/content/api

          # Extract OpenAPI specs
          if [ -f sources/backend/openapi.yml ]; then
            cp sources/backend/openapi.yml docs/content/api/
          fi

          # Extract JSDoc comments
          cd sources/backend
          npm install
          npm run docs:generate
          cp -r docs/api/* ../../docs/content/api/

      - name: Collect README files
        run: |
          mkdir -p docs/content/readmes

          cp sources/backend/README.md docs/content/readmes/backend.md
          cp sources/frontend/README.md docs/content/readmes/frontend.md
          cp sources/mobile/README.md docs/content/readmes/mobile.md

      - name: Generate changelog
        run: |
          mkdir -p docs/content/changelog

          for repo in backend frontend mobile; do
            cd sources/$repo
            git log --pretty=format:"- %s (%h)" -n 20 > ../../docs/content/changelog/$repo.md
            cd ../..
          done

      - name: Build documentation site
        run: |
          cd docs
          npm install
          npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/dist
```

## メリット

1. **一元化**: 全プロジェクトのドキュメントを1箇所に集約
2. **自動更新**: 各リポジトリの変更を自動的に反映
3. **一貫性**: 統一されたフォーマットでドキュメント提供

## 応用例

### プロジェクトのREADMEを自動更新

```yaml
name: Update Main README

on:
  schedule:
    - cron: '0 0 * * 0'  # 毎週実行

jobs:
  update-readme:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout main repo
        uses: actions/checkout@v4

      - name: Collect project information
        run: |
          # 複数のリポジトリから情報を収集

          declare -a repos=("project-a" "project-b" "project-c")

          echo "# Our Projects" > PROJECTS.md
          echo "" >> PROJECTS.md

          for repo in "${repos[@]}"; do
            # Clone each repository
            git clone https://github.com/organization/$repo temp/$repo

            # Extract information
            echo "## $repo" >> PROJECTS.md
            head -n 5 temp/$repo/README.md | tail -n +2 >> PROJECTS.md
            echo "" >> PROJECTS.md

            # Cleanup
            rm -rf temp/$repo
          done

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add PROJECTS.md
          git commit -m "Auto-update project list" || echo "No changes"
          git push
```

### API仕様の変更を検出して通知

```yaml
name: API Spec Change Detection

on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと

jobs:
  check-api-changes:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout tracking repo
        uses: actions/checkout@v4

      - name: Checkout API repo
        uses: actions/checkout@v4
        with:
          repository: organization/api-repo
          token: ${{ secrets.GH_PAT }}
          path: api

      - name: Compare OpenAPI specs
        run: |
          if [ -f last-openapi.yml ]; then
            if ! diff -q last-openapi.yml api/openapi.yml; then
              echo "API_CHANGED=true" >> $GITHUB_ENV
              echo "API specification has changed!"
            fi
          fi

          cp api/openapi.yml last-openapi.yml

      - name: Notify on changes
        if: env.API_CHANGED == 'true'
        uses: 8398a7/action-slack@v3
        with:
          status: custom
          custom_payload: |
            {
              text: "API specification has been updated!"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

      - name: Commit updated spec
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add last-openapi.yml
          git commit -m "Update tracked API spec" || echo "No changes"
          git push
```
