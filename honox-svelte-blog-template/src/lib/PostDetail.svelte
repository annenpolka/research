<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte'
  import { marked } from 'marked'

  export let slug: string

  const dispatch = createEventDispatcher()

  interface Post {
    id: number
    title: string
    slug: string
    content: string
    date: string
    author: string
    tags: string[]
  }

  let post: Post | null = null
  let loading = true
  let error: string | null = null
  let renderedContent = ''

  async function fetchPost() {
    try {
      loading = true
      const response = await fetch(`http://localhost:3000/api/posts/${slug}`)
      if (!response.ok) {
        throw new Error('記事が見つかりませんでした')
      }
      const data = await response.json()
      post = data.post
      renderedContent = marked(post.content) as string
      error = null
    } catch (e) {
      error = e instanceof Error ? e.message : '不明なエラー'
      post = null
    } finally {
      loading = false
    }
  }

  onMount(() => {
    fetchPost()
  })

  $: if (slug) {
    fetchPost()
  }

  function goBack() {
    dispatch('back')
  }
</script>

<div class="post-detail">
  {#if loading}
    <div class="loading">読み込み中...</div>
  {:else if error}
    <div class="error">エラー: {error}</div>
    <button class="back-button" on:click={goBack}>← 戻る</button>
  {:else if post}
    <article class="post">
      <button class="back-button" on:click={goBack}>← 戻る</button>

      <header class="post-header">
        <h1 class="post-title">{post.title}</h1>
        <div class="post-meta">
          <span class="post-date">{post.date}</span>
          <span class="post-author">by {post.author}</span>
        </div>
        <div class="post-tags">
          {#each post.tags as tag}
            <span class="tag">{tag}</span>
          {/each}
        </div>
      </header>

      <div class="post-content">
        {@html renderedContent}
      </div>
    </article>
  {/if}
</div>

<style>
  .post-detail {
    max-width: 800px;
    margin: 0 auto;
  }

  .loading,
  .error {
    text-align: center;
    padding: 3rem;
    font-size: 1.2rem;
  }

  .error {
    color: #ff4444;
  }

  .back-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 2rem;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .back-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .post {
    background: white;
    border-radius: 12px;
    padding: 3rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .post-header {
    border-bottom: 2px solid #f0f0f0;
    padding-bottom: 2rem;
    margin-bottom: 2rem;
  }

  .post-title {
    margin: 0 0 1rem 0;
    color: #333;
    font-size: 2.5rem;
    line-height: 1.2;
  }

  .post-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 1rem;
    color: #666;
  }

  .post-tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .tag {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .post-content {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #333;
  }

  .post-content :global(h1) {
    margin-top: 2rem;
    margin-bottom: 1rem;
    color: #333;
  }

  .post-content :global(h2) {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: #333;
  }

  .post-content :global(h3) {
    margin-top: 1.25rem;
    margin-bottom: 0.5rem;
    color: #333;
  }

  .post-content :global(p) {
    margin-bottom: 1rem;
  }

  .post-content :global(code) {
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }

  .post-content :global(pre) {
    background-color: #f4f4f4;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1.5rem 0;
  }

  .post-content :global(pre code) {
    background-color: transparent;
    padding: 0;
  }

  @media (prefers-color-scheme: dark) {
    .post {
      background: #2a2a2a;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .post-header {
      border-bottom-color: #444;
    }

    .post-title {
      color: #fff;
    }

    .post-meta {
      color: #aaa;
    }

    .post-content {
      color: #ddd;
    }

    .post-content :global(h1),
    .post-content :global(h2),
    .post-content :global(h3) {
      color: #fff;
    }

    .post-content :global(code) {
      background-color: #1a1a1a;
    }

    .post-content :global(pre) {
      background-color: #1a1a1a;
    }
  }

  @media (max-width: 768px) {
    .post {
      padding: 1.5rem;
    }

    .post-title {
      font-size: 1.8rem;
    }

    .post-content {
      font-size: 1rem;
    }
  }
</style>
