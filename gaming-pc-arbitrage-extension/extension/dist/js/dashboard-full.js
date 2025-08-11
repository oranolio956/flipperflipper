// Dashboard v3.5.0 - Full implementation
document.addEventListener('DOMContentLoaded', async () => {
  const root = document.getElementById('root');
  
  // Initialize managers
  await window.settingsManager.init();
  await window.pipelineManager.init();
  
  // Set up routes
  window.router.routes({
    '/': {
      handler: renderOverview,
      title: 'Overview'
    },
    '/scanner': {
      handler: renderScanner,
      title: 'Scanner'
    },
    '/pipeline': {
      handler: renderPipeline,
      title: 'Pipeline'
    },
    '/analytics': {
      handler: renderAnalytics,
      title: 'Analytics'
    },
    '/settings': {
      handler: renderSettings,
      title: 'Settings'
    }
  });
  
  // Render layout
  root.innerHTML = `
    <div class="dashboard-container">
      <nav class="sidebar">
        <div class="logo">
          <h2>PC Arbitrage Pro</h2>
          <span class="version">v${chrome.runtime.getManifest().version}</span>
        </div>
        <ul class="nav-menu">
          <li><a href="#/" class="nav-link active">Overview</a></li>
          <li><a href="#/scanner" class="nav-link">Scanner</a></li>
          <li><a href="#/pipeline" class="nav-link">Pipeline</a></li>
          <li><a href="#/analytics" class="nav-link">Analytics</a></li>
          <li><a href="#/settings" class="nav-link">Settings</a></li>
        </ul>
      </nav>
      <main class="main-content">
        <div id="page-content"></div>
      </main>
    </div>
  `;
  
  // Update active nav
  window.router.after((path) => {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === `#${path}`);
    });
  });
});

// Page renderers
function renderOverview() {
  const content = document.getElementById('page-content');
  const stats = window.pipelineManager.getStats();
  
  content.innerHTML = `
    <div class="page-header">
      <h1>Dashboard Overview</h1>
    </div>
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Active Deals</h3>
        <p class="stat-value">${stats.total}</p>
      </div>
      <div class="stat-card">
        <h3>Completion Rate</h3>
        <p class="stat-value">${stats.completionRate.toFixed(1)}%</p>
      </div>
      <div class="stat-card">
        <h3>Avg Pipeline Days</h3>
        <p class="stat-value">${stats.avgDaysInPipeline.toFixed(1)}</p>
      </div>
    </div>
  `;
}

function renderScanner() {
  const content = document.getElementById('page-content');
  
  content.innerHTML = `
    <div class="page-header">
      <h1>Scanner</h1>
      <button class="btn-primary" onclick="startScan()">Start Scan</button>
    </div>
    <div class="scanner-content">
      <div class="search-config">
        <h3>Search Configuration</h3>
        <input type="text" placeholder="Keywords" id="keywords" class="form-input">
        <button onclick="window.searchBuilder.suggestKeywords('gaming')">Suggestions</button>
      </div>
    </div>
  `;
}

function renderPipeline() {
  const content = document.getElementById('page-content');
  
  content.innerHTML = `
    <div class="page-header">
      <h1>Deal Pipeline</h1>
    </div>
    <div class="pipeline-board">
      ${window.pipelineManager.stages.map(stage => `
        <div class="pipeline-column">
          <h3>${stage}</h3>
          <div class="deals-list">
            ${window.pipelineManager.getDealsByStage(stage).map(deal => `
              <div class="deal-card">
                <h4>${deal.listing.title}</h4>
                <p>$${deal.listing.price}</p>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderAnalytics() {
  const content = document.getElementById('page-content');
  
  content.innerHTML = `
    <div class="page-header">
      <h1>Analytics</h1>
    </div>
    <div class="analytics-content">
      <p>Analytics dashboard will be rendered here</p>
    </div>
  `;
}

function renderSettings() {
  const content = document.getElementById('page-content');
  
  content.innerHTML = `
    <div class="page-header">
      <h1>Settings</h1>
    </div>
    <div class="settings-content">
      <p>Settings will be rendered here</p>
    </div>
  `;
  
  // Load settings UI if available
  if (window.settingsUI) {
    window.settingsUI.render();
  }
}

// Helper functions
window.startScan = function() {
  const keywords = document.getElementById('keywords').value.split(',');
  
  window.automationEngine.startSession({
    keywords: keywords,
    platforms: ['facebook', 'craigslist'],
    filters: {
      minPrice: 100,
      maxPrice: 2000
    }
  });
};
