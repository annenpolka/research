<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte'

  export let selectedTag: string | null = null

  const dispatch = createEventDispatcher()

  let tags: string[] = []
  let loading = true
  let error: string | null = null

  async function fetchTags() {
    try {
      loading = true
      const response = await fetch('http://localhost:3000/api/tags')
      if (!response.ok) {
        throw new Error('Failed to fetch tags')
      }
      const data = await response.json()
      tags = data.tags
      error = null
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error'
      tags = []
    } finally {
      loading = false
    }
  }

  onMount(() => {
    fetchTags()
  })

  function selectTag(tag: string | null) {
    dispatch('selectTag', tag)
    if (tag) {
      window.location.hash = `tag/${tag}`
    } else {
      window.location.hash = ''
    }
  }
</script>

<div class="tag-filter">
  <h3 class="filter-title">タグで絞り込み</h3>

  {#if loading}
    <div class="loading">読み込み中...</div>
  {:else if error}
    <div class="error">エラー</div>
  {:else}
    <div class="tags">
      <button
        class="tag-button"
        class:active={selectedTag === null}
        on:click={() => selectTag(null)}
      >
        すべて
      </button>
      {#each tags as tag}
        <button
          class="tag-button"
          class:active={selectedTag === tag}
          on:click={() => selectTag(tag)}
        >
          {tag}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .tag-filter {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .filter-title {
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
    color: #333;
  }

  .loading,
  .error {
    text-align: center;
    padding: 1rem;
    font-size: 0.9rem;
    color: #666;
  }

  .tags {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tag-button {
    background: #f4f4f4;
    border: 2px solid transparent;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
    text-align: left;
    transition: all 0.2s;
    color: #333;
  }

  .tag-button:hover {
    background: #e8e8e8;
    transform: translateX(4px);
  }

  .tag-button.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
  }

  @media (prefers-color-scheme: dark) {
    .tag-filter {
      background: #2a2a2a;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .filter-title {
      color: #fff;
    }

    .tag-button {
      background: #1a1a1a;
      color: #ddd;
    }

    .tag-button:hover {
      background: #333;
    }

    .tag-button.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
  }
</style>
