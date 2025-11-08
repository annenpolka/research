# ユースケース1: 共通スクリプトの利用

## シナリオ

複数のプロジェクトで共有するビルドスクリプトやデプロイスクリプトを、専用のリポジトリで管理している場合。

## 構成例

```
organization/
├── project-a/          # メインプロジェクト
├── project-b/          # メインプロジェクト
└── shared-scripts/     # 共通スクリプトリポジトリ
    ├── build/
    │   └── build.sh
    ├── deploy/
    │   └── deploy.sh
    └── utils/
        └── common.sh
```

## ワークフロー実装

```yaml
name: Build with Shared Scripts

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout project repository
        uses: actions/checkout@v4

      - name: Checkout shared scripts
        uses: actions/checkout@v4
        with:
          repository: organization/shared-scripts
          token: ${{ secrets.GH_PAT }}
          path: .github/shared-scripts

      - name: Run shared build script
        run: |
          chmod +x .github/shared-scripts/build/build.sh
          .github/shared-scripts/build/build.sh

      - name: Run shared deployment script
        run: |
          chmod +x .github/shared-scripts/deploy/deploy.sh
          .github/shared-scripts/deploy/deploy.sh
```

## メリット

1. **DRY原則**: スクリプトの重複を避ける
2. **一元管理**: 修正を全プロジェクトに即座に反映
3. **バージョン管理**: タグやブランチで特定バージョンを使用可能

## 注意点

- スクリプトの変更が全プロジェクトに影響
- 破壊的変更時は慎重にバージョン管理が必要
- セキュリティ: スクリプトの内容を信頼できることが前提
