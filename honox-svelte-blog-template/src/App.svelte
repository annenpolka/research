<script lang="ts">
  import { onMount } from 'svelte'
  import Header from './lib/Header.svelte'
  import PostList from './lib/PostList.svelte'
  import PostDetail from './lib/PostDetail.svelte'
  import TagFilter from './lib/TagFilter.svelte'

  let currentView: 'list' | 'detail' = 'list'
  let currentSlug: string = ''
  let selectedTag: string | null = null

  function showPostDetail(slug: string) {
    currentSlug = slug
    currentView = 'detail'
  }

  function showPostList() {
    currentView = 'list'
    currentSlug = ''
  }

  function filterByTag(tag: string | null) {
    selectedTag = tag
    currentView = 'list'
  }

  // Simple routing based on hash
  onMount(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1)
      if (hash.startsWith('post/')) {
        const slug = hash.slice(5)
        showPostDetail(slug)
      } else if (hash.startsWith('tag/')) {
        const tag = hash.slice(4)
        filterByTag(tag)
      } else {
        showPostList()
      }
    }

    window.addEventListener('hashchange', handleHashChange)
    handleHashChange()

    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  })
</script>

<div class="app">
  <Header />

  <main class="container">
    {#if currentView === 'list'}
      <div class="sidebar-layout">
        <aside class="sidebar">
          <TagFilter {selectedTag} on:selectTag={(e) => filterByTag(e.detail)} />
        </aside>
        <div class="main-content">
          <PostList
            {selectedTag}
            on:selectPost={(e) => {
              window.location.hash = `post/${e.detail}`
            }}
          />
        </div>
      </div>
    {:else if currentView === 'detail'}
      <PostDetail
        slug={currentSlug}
        on:back={() => {
          window.location.hash = ''
        }}
      />
    {/if}
  </main>

  <footer class="footer">
    <p>&copy; 2024 HonoX + Svelte Blog. Built with HonoX and Svelte.</p>
  </footer>
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    flex: 1;
    width: 100%;
  }

  .sidebar-layout {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 2rem;
  }

  .sidebar {
    position: sticky;
    top: 2rem;
    height: fit-content;
  }

  .main-content {
    min-width: 0;
  }

  .footer {
    background-color: #f4f4f4;
    padding: 2rem;
    text-align: center;
    margin-top: 4rem;
  }

  @media (prefers-color-scheme: dark) {
    .footer {
      background-color: #2a2a2a;
    }
  }

  @media (max-width: 768px) {
    .sidebar-layout {
      grid-template-columns: 1fr;
    }

    .sidebar {
      position: static;
    }

    .container {
      padding: 1rem;
    }
  }
</style>
