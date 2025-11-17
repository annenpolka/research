import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

// CORS設定
app.use('/*', cors())

// ブログ記事のダミーデータ
const posts = [
  {
    id: 1,
    title: 'HonoXとSvelteで始めるモダンWebアプリケーション',
    slug: 'getting-started-honox-svelte',
    excerpt: 'HonoXとSvelteを組み合わせた高速で軽量なWebアプリケーションの作り方を紹介します。',
    content: `# HonoXとSvelteで始めるモダンWebアプリケーション

HonoXは、Cloudflare Workersを始めとする様々なエッジランタイムで動作する高速なWebフレームワークです。

## なぜHonoXとSvelteなのか?

- **高速**: 両方とも非常に軽量で高速
- **シンプル**: 学習コストが低い
- **モダン**: 最新のWeb標準をサポート

## 始め方

まずは依存関係をインストールしましょう...`,
    date: '2024-01-15',
    author: 'Claude',
    tags: ['HonoX', 'Svelte', 'TypeScript']
  },
  {
    id: 2,
    title: 'Svelteのリアクティビティを理解する',
    slug: 'understanding-svelte-reactivity',
    excerpt: 'Svelteのリアクティビティシステムは他のフレームワークとは異なります。その仕組みを深く理解しましょう。',
    content: `# Svelteのリアクティビティを理解する

Svelteのリアクティビティは、コンパイル時に最適化される独自の仕組みです。

## 基本的な使い方

\`\`\`svelte
<script>
  let count = 0;
  $: doubled = count * 2;
</script>
\`\`\`

このシンプルな構文で、リアクティブな変数を定義できます。`,
    date: '2024-01-20',
    author: 'Claude',
    tags: ['Svelte', 'JavaScript', 'Reactivity']
  },
  {
    id: 3,
    title: 'HonoでREST APIを構築する',
    slug: 'building-rest-api-with-hono',
    excerpt: 'Honoを使った効率的なREST APIの構築方法を学びましょう。',
    content: `# HonoでREST APIを構築する

Honoは、Express.jsのようなAPIでありながら、より高速で軽量です。

## ルーティング

\`\`\`typescript
app.get('/api/posts', (c) => {
  return c.json({ posts })
})
\`\`\`

シンプルで直感的なAPIです。`,
    date: '2024-01-25',
    author: 'Claude',
    tags: ['Hono', 'API', 'TypeScript']
  }
]

// API Routes
app.get('/api/posts', (c) => {
  return c.json({ posts })
})

app.get('/api/posts/:slug', (c) => {
  const slug = c.req.param('slug')
  const post = posts.find(p => p.slug === slug)

  if (!post) {
    return c.json({ error: 'Post not found' }, 404)
  }

  return c.json({ post })
})

app.get('/api/tags', (c) => {
  const tags = Array.from(new Set(posts.flatMap(p => p.tags)))
  return c.json({ tags })
})

app.get('/api/posts/tag/:tag', (c) => {
  const tag = c.req.param('tag')
  const filteredPosts = posts.filter(p => p.tags.includes(tag))
  return c.json({ posts: filteredPosts })
})

const port = 3000
console.log(`Server running at http://localhost:${port}`)

export default app
