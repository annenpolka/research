<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte'

  export let selectedTag: string | null = null

  const dispatch = createEventDispatcher()

  interface Post {
    id: number
    title: string
    slug: string
    excerpt: string
    date: string
    author: string
    tags: string[]
  }

  let posts: Post[] = []
  let loading = true
  let error: string | null = null

  async function fetchPosts() {
    try {
      loading = true
      const url = selectedTag
        ? `http://localhost:3000/api/posts/tag/${selectedTag}`
        : 'http://localhost:3000/api/posts'

      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch posts')
      }
      const data = await response.json()
      posts = data.posts
      error = null
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error'
      posts = []
    } finally {
      loading = false
    }
  }

  onMount(() => {
    fetchPosts()
  })

  $: if (selectedTag !== undefined) {
    fetchPosts()
  }

  function selectPost(slug: string) {
    dispatch('selectPost', slug)
  }
</script>

<div class="post-list">
  {#if selectedTag}
    <div class="tag-info">
      <h2>タグ: {selectedTag}</h2>
    </div>
  {/if}

  {#if loading}
    <div class="loading">読み込み中...</div>
  {:else if error}
    <div class="error">エラー: {error}</div>
  {:else if posts.length === 0}
    <div class="empty">記事が見つかりませんでした。</div>
  {:else}
    <div class="posts">
      {#each posts as post (post.id)}
        <article class="post-card" on:click={() => selectPost(post.slug)}>
          <h2 class="post-title">{post.title}</h2>
          <div class="post-meta">
            <span class="post-date">{post.date}</span>
            <span class="post-author">by {post.author}</span>
          </div>
          <p class="post-excerpt">{post.excerpt}</p>
          <div class="post-tags">
            {#each post.tags as tag}
              <span class="tag">{tag}</span>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  {/if}
</div>

<style>
  .post-list {
    width: 100%;
  }

  .tag-info {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #667eea;
  }

  .tag-info h2 {
    margin: 0;
    color: #667eea;
  }

  .loading,
  .error,
  .empty {
    text-align: center;
    padding: 3rem;
    font-size: 1.2rem;
  }

  .error {
    color: #ff4444;
  }

  .posts {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .post-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .post-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    border-color: #667eea;
  }

  .post-title {
    margin: 0 0 0.5rem 0;
    color: #333;
    font-size: 1.5rem;
  }

  .post-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #666;
  }

  .post-excerpt {
    color: #555;
    line-height: 1.6;
    margin-bottom: 1rem;
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

  @media (prefers-color-scheme: dark) {
    .post-card {
      background: #2a2a2a;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .post-title {
      color: #fff;
    }

    .post-meta {
      color: #aaa;
    }

    .post-excerpt {
      color: #ccc;
    }
  }
</style>
