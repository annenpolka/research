<script lang="ts">
  function goHome() {
    window.location.hash = ''
  }
</script>

<header class="header">
  <div class="container">
    <h1 class="logo" on:click={goHome}>
      <span class="logo-icon">📝</span>
      HonoX + Svelte Blog
    </h1>
    <nav>
      <a href="#" on:click|preventDefault={goHome}>Home</a>
      <a href="https://github.com/honojs/hono" target="_blank" rel="noopener">HonoX</a>
      <a href="https://svelte.dev" target="_blank" rel="noopener">Svelte</a>
    </nav>
  </div>
</header>

<style>
  .header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem 0;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .logo {
    font-size: 1.5rem;
    font-weight: bold;
    cursor: pointer;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: transform 0.2s;
  }

  .logo:hover {
    transform: scale(1.05);
  }

  .logo-icon {
    font-size: 2rem;
  }

  nav {
    display: flex;
    gap: 2rem;
  }

  nav a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.2s;
  }

  nav a:hover {
    opacity: 0.8;
  }

  @media (max-width: 768px) {
    .container {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    nav {
      gap: 1rem;
    }

    .logo {
      font-size: 1.2rem;
    }
  }
</style>
