<script>
  let screens = [];
  let layouts = [];
  let selectedWidget = null;

  async function fetchScreens() {
    const res = await fetch("/api/screens");
    screens = await res.json();
  }

  async function fetchLayouts() {
    const res = await fetch("/api/layouts");
    layouts = await res.json();
  }

  // Poll screens every 3s
  setInterval(fetchScreens, 3000);
  fetchScreens();
  fetchLayouts();
</script>

<main>
  <header>
    <h1>div-screens editor</h1>
    <span class="status">
      {screens.length} screen{screens.length !== 1 ? "s" : ""} connected
    </span>
  </header>

  <div class="editor-layout">
    <aside class="widget-palette">
      <h2>Widgets</h2>
      <button class="widget-btn">Clock</button>
      <button class="widget-btn">Text</button>
      <button class="widget-btn">Bar</button>
      <button class="widget-btn">Mini Bars</button>
      <button class="widget-btn">Separator</button>
      <button class="widget-btn">Image</button>
      <button class="widget-btn">API</button>
    </aside>

    <section class="canvas-area">
      <div class="canvas-wrapper">
        <canvas id="screen-canvas" width="320" height="480"></canvas>
      </div>
      <div class="screen-tabs">
        {#each screens as screen}
          <button class="tab">{screen.name} ({screen.port})</button>
        {/each}
        {#if screens.length === 0}
          <span class="no-screens">No screens detected</span>
        {/if}
      </div>
    </section>

    <aside class="properties">
      <h2>Properties</h2>
      {#if selectedWidget}
        <p>Widget: {selectedWidget.type}</p>
      {:else}
        <p class="hint">Select a widget to edit</p>
      {/if}
    </aside>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: "JetBrains Mono", "SF Mono", monospace;
    background: #0f0f19;
    color: #dcdcdc;
  }

  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: #1e1e32;
    border-bottom: 1px solid #3c3c50;
  }

  header h1 {
    font-size: 16px;
    margin: 0;
    color: #00c8ff;
  }

  .status {
    font-size: 12px;
    color: #646478;
  }

  .editor-layout {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .widget-palette {
    width: 160px;
    padding: 12px;
    background: #1a1a2e;
    border-right: 1px solid #3c3c50;
    overflow-y: auto;
  }

  .widget-palette h2 {
    font-size: 13px;
    color: #646478;
    margin: 0 0 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .widget-btn {
    display: block;
    width: 100%;
    padding: 8px;
    margin-bottom: 6px;
    background: #2a2a44;
    color: #dcdcdc;
    border: 1px solid #3c3c50;
    border-radius: 4px;
    cursor: grab;
    font-family: inherit;
    font-size: 12px;
    text-align: left;
  }

  .widget-btn:hover {
    background: #3a3a54;
    border-color: #00c8ff;
  }

  .canvas-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px;
  }

  .canvas-wrapper {
    border: 2px solid #3c3c50;
    border-radius: 4px;
    box-shadow: 0 0 20px rgba(0, 200, 255, 0.1);
  }

  #screen-canvas {
    display: block;
    background: #0f0f19;
  }

  .screen-tabs {
    display: flex;
    gap: 8px;
  }

  .tab {
    padding: 6px 12px;
    background: #2a2a44;
    color: #dcdcdc;
    border: 1px solid #3c3c50;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
  }

  .tab:hover {
    border-color: #00c8ff;
  }

  .no-screens {
    font-size: 11px;
    color: #646478;
  }

  .properties {
    width: 220px;
    padding: 12px;
    background: #1a1a2e;
    border-left: 1px solid #3c3c50;
    overflow-y: auto;
  }

  .properties h2 {
    font-size: 13px;
    color: #646478;
    margin: 0 0 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .hint {
    font-size: 12px;
    color: #646478;
  }
</style>
