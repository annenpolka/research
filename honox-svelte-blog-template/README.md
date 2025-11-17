# HonoX + Svelte Blog Template

HonoXとSvelteを組み合わせたモダンなブログテンプレートです。高速で軽量、そしてシンプルな構成を目指しています。

## 概要

このプロジェクトは、HonoXをバックエンドAPI、SvelteをフロントエンドUIとして使用したブログアプリケーションのテンプレートです。Viteを使用して開発環境を構築し、効率的な開発体験を提供します。

## 動機

- **HonoX**: Cloudflare Workersなどのエッジランタイムで動作する超高速Webフレームワーク
- **Svelte**: コンパイル時に最適化される軽量フロントエンドフレームワーク
- **Vite**: 高速な開発サーバーとビルドツール

これら3つの技術を組み合わせることで、軽量で高速、かつ開発体験の優れたブログアプリケーションを実現します。

## 特徴

- ⚡️ **超高速**: HonoXとSvelteの組み合わせによる高速なレンダリング
- 📝 **マークダウン対応**: markedライブラリを使用したマークダウン記事の表示
- 🏷️ **タグフィルタリング**: タグによる記事の絞り込み機能
- 🎨 **レスポンシブデザイン**: モバイルからデスクトップまで対応
- 🌓 **ダークモード対応**: システム設定に応じた自動切り替え
- 🔄 **ハッシュルーティング**: シンプルなクライアントサイドルーティング

## 技術スタック

### フロントエンド
- **Svelte 4**: リアクティブUIフレームワーク
- **TypeScript**: 型安全な開発
- **Vite**: 開発サーバーとビルドツール
- **marked**: マークダウンパーサー

### バックエンド
- **Hono**: 高速Webフレームワーク
- **TypeScript**: 型安全なAPI開発

## プロジェクト構造

```
honox-svelte-blog-template/
├── src/
│   ├── lib/                    # Svelteコンポーネント
│   │   ├── Header.svelte       # ヘッダーコンポーネント
│   │   ├── PostList.svelte     # 記事一覧コンポーネント
│   │   ├── PostDetail.svelte   # 記事詳細コンポーネント
│   │   └── TagFilter.svelte    # タグフィルターコンポーネント
│   ├── App.svelte              # ルートコンポーネント
│   ├── main.ts                 # エントリーポイント
│   ├── app.css                 # グローバルスタイル
│   └── vite-env.d.ts           # 型定義
├── server.ts                   # HonoXサーバー
├── vite.config.ts              # Vite設定
├── svelte.config.js            # Svelte設定
├── tsconfig.json               # TypeScript設定
├── package.json                # 依存関係
└── index.html                  # HTMLエントリーポイント
```

## インストール

```bash
cd honox-svelte-blog-template
npm install
```

## 使い方

### 開発モード

2つのターミナルを開いて、それぞれ以下のコマンドを実行します：

**ターミナル1: バックエンドサーバー（Hono）**
```bash
npx tsx server.ts
```
→ `http://localhost:3000` でAPIサーバーが起動

**ターミナル2: フロントエンド開発サーバー（Vite）**
```bash
npm run dev
```
→ `http://localhost:5173` で開発サーバーが起動

ブラウザで `http://localhost:5173` を開くと、ブログアプリケーションが表示されます。

### 本番ビルド

```bash
npm run build
```

ビルドされたファイルは `dist/` ディレクトリに出力されます。

### プレビュー

```bash
npm run preview
```

## API エンドポイント

バックエンドAPIは以下のエンドポイントを提供します：

- `GET /api/posts` - すべての記事を取得
- `GET /api/posts/:slug` - 特定の記事を取得
- `GET /api/tags` - すべてのタグを取得
- `GET /api/posts/tag/:tag` - 特定のタグの記事を取得

## 機能説明

### 記事一覧表示
- すべての記事をカード形式で表示
- 各カードには、タイトル、日付、著者、抜粋、タグが表示される
- カードをクリックすると記事詳細ページに遷移

### 記事詳細表示
- マークダウン形式の記事コンテンツをHTMLに変換して表示
- シンタックスハイライト対応のコードブロック表示
- 「戻る」ボタンで記事一覧に戻る

### タグフィルタリング
- サイドバーにタグ一覧を表示
- タグをクリックすると、そのタグが付いた記事のみを表示
- 「すべて」ボタンでフィルターを解除

### ルーティング
- ハッシュベースのシンプルなルーティング
- `#post/{slug}` - 記事詳細ページ
- `#tag/{tag}` - タグフィルターページ
- `#` または空 - 記事一覧ページ

## カスタマイズ

### 記事の追加

`server.ts` の `posts` 配列に新しい記事オブジェクトを追加します：

```typescript
{
  id: 4,
  title: '新しい記事のタイトル',
  slug: 'new-article-slug',
  excerpt: '記事の要約文',
  content: `# 記事のタイトル\n\nマークダウン形式のコンテンツ...`,
  date: '2024-02-01',
  author: '著者名',
  tags: ['タグ1', 'タグ2']
}
```

### スタイルのカスタマイズ

- `src/app.css`: グローバルスタイル
- 各 `.svelte` ファイルの `<style>` セクション: コンポーネント固有のスタイル

## 実装の詳細

### HonoXとSvelteの統合

このプロジェクトでは、以下のアーキテクチャを採用しています：

1. **分離されたフロントエンドとバックエンド**
   - フロントエンド: Vite + Svelte (ポート5173)
   - バックエンド: Hono (ポート3000)

2. **開発時のプロキシ設定**
   - Viteのプロキシ機能を使用して、`/api` へのリクエストをHonoサーバーに転送
   - `vite.config.ts` で設定

3. **CORS対応**
   - HonoサーバーでCORSミドルウェアを有効化
   - クロスオリジンリクエストを許可

### Svelteのリアクティビティ

Svelteの強力なリアクティビティシステムを活用：

```svelte
<script>
  let selectedTag: string | null = null

  // selectedTagが変更されると自動的にfetchPostsが実行される
  $: if (selectedTag !== undefined) {
    fetchPosts()
  }
</script>
```

### マークダウンレンダリング

`marked` ライブラリを使用してマークダウンをHTMLに変換：

```typescript
import { marked } from 'marked'

renderedContent = marked(post.content) as string
```

Svelteの `{@html}` ディレクティブで安全にHTMLを挿入。

## 結論

### 主な発見

1. **HonoとSvelteの相性**: HonoのシンプルなAPIとSvelteの軽量性は非常に相性が良い
2. **Viteの開発体験**: Viteの高速な開発サーバーとHMRにより、快適な開発が可能
3. **型安全性**: TypeScriptの使用により、フロントエンドとバックエンドの両方で型安全な開発が実現

### 推奨事項

- **本番環境**: Cloudflare WorkersやVercel Edgeなどのエッジランタイムへのデプロイを推奨
- **データベース統合**: 実際のブログには、データベース（例: Supabase, PlanetScale）の統合を検討
- **認証**: 管理画面が必要な場合は、認証システム（例: Auth.js）の追加を検討
- **SSR/SSG**: より高度なSEO対策が必要な場合は、SvelteKitへの移行を検討

### 今後の拡張案

- [ ] データベース統合（Supabase/PlanetScale）
- [ ] 記事の作成・編集機能
- [ ] 認証システムの追加
- [ ] コメント機能
- [ ] 記事の検索機能
- [ ] RSS/Atomフィード
- [ ] SEO最適化
- [ ] 画像のアップロードと最適化

## ライセンス

MIT

## 作成者

このテンプレートはAIエージェント（Claude）によって自律的に作成されました。
