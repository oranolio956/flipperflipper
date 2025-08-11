#!/bin/bash

# Create all missing JavaScript files for the Gaming PC Arbitrage Extension

echo "Creating missing JavaScript files..."

# Create search-builder.js
cat > extension/dist/js/search-builder.js << 'EOF'
// SearchBuilder v3.5.0 - Multi-platform search URL builder
class SearchBuilder {
  constructor() {
    this.platforms = {
      facebook: {
        name: 'Facebook Marketplace',
        baseUrl: 'https://www.facebook.com/marketplace/search',
        params: {
          query: 'query',
          minPrice: 'minPrice',
          maxPrice: 'maxPrice',
          radius: 'radius',
          sort: 'sortBy'
        }
      },
      craigslist: {
        name: 'Craigslist',
        baseUrl: 'https://craigslist.org/search/sss',
        params: {
          query: 'query',
          minPrice: 'min_price',
          maxPrice: 'max_price',
          radius: 'search_distance'
        }
      },
      offerup: {
        name: 'OfferUp',
        baseUrl: 'https://offerup.com/search',
        params: {
          query: 'q',
          minPrice: 'price_min',
          maxPrice: 'price_max'
        }
      }
    };
  }
  
  buildSearchUrl(platform, keywords, filters = {}) {
    const config = this.platforms[platform];
    if (!config) throw new Error(`Unknown platform: ${platform}`);
    
    const params = new URLSearchParams();
    
    // Add keywords
    if (keywords.length > 0) {
      params.set(config.params.query, keywords.join(' '));
    }
    
    // Add filters
    Object.entries(filters).forEach(([key, value]) => {
      if (config.params[key] && value !== undefined) {
        params.set(config.params[key], value);
      }
    });
    
    return `${config.baseUrl}?${params.toString()}`;
  }
  
  suggestKeywords(category) {
    const suggestions = {
      gaming: ['gaming pc', 'gaming computer', 'rgb pc', 'custom pc'],
      gpu: ['rtx 3080', 'rtx 3070', 'rtx 3090', 'rx 6800'],
      cpu: ['i7', 'i9', 'ryzen 7', 'ryzen 9']
    };
    
    return suggestions[category] || [];
  }
}

window.searchBuilder = new SearchBuilder();
EOF

# Create automation-engine.js
cat > extension/dist/js/automation-engine.js << 'EOF'
// AutomationEngine v3.5.0 - Smart scanning automation
class AutomationEngine {
  constructor() {
    this.isRunning = false;
    this.currentSession = null;
    this.queue = [];
    this.activeTabs = new Map();
    this.results = [];
    this.config = {
      maxConcurrentTabs: 3,
      scanDelay: 2000,
      pageTimeout: 30000,
      retryAttempts: 3
    };
    
    this.init();
  }
  
  init() {
    // Listen for messages
    if (chrome.runtime) {
      chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'SCAN_COMPLETE') {
          this.handleScanComplete(sender.tab.id, request.data);
        }
      });
    }
  }
  
  async startSession(options) {
    if (this.isRunning) {
      throw new Error('Automation already running');
    }
    
    this.isRunning = true;
    this.currentSession = {
      id: Date.now().toString(),
      startTime: Date.now(),
      options: options,
      stats: {
        scanned: 0,
        found: 0,
        errors: 0
      }
    };
    
    // Build search URLs
    const urls = this.buildSearchUrls(options);
    this.queue = urls;
    
    // Start processing
    this.processQueue();
    
    return this.currentSession;
  }
  
  buildSearchUrls(options) {
    const urls = [];
    const { keywords, platforms, filters } = options;
    
    platforms.forEach(platform => {
      keywords.forEach(keyword => {
        const url = window.searchBuilder.buildSearchUrl(
          platform,
          [keyword],
          filters
        );
        urls.push({ platform, keyword, url });
      });
    });
    
    return urls;
  }
  
  async processQueue() {
    while (this.queue.length > 0 && this.isRunning) {
      if (this.activeTabs.size < this.config.maxConcurrentTabs) {
        const item = this.queue.shift();
        this.scanUrl(item);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  async scanUrl(item) {
    try {
      const tab = await chrome.tabs.create({
        url: item.url,
        active: false
      });
      
      this.activeTabs.set(tab.id, {
        ...item,
        startTime: Date.now()
      });
      
      // Set timeout
      setTimeout(() => {
        if (this.activeTabs.has(tab.id)) {
          this.handleTimeout(tab.id);
        }
      }, this.config.pageTimeout);
      
    } catch (error) {
      console.error('Failed to create tab:', error);
      this.currentSession.stats.errors++;
    }
  }
  
  handleScanComplete(tabId, data) {
    const tabInfo = this.activeTabs.get(tabId);
    if (!tabInfo) return;
    
    this.activeTabs.delete(tabId);
    this.currentSession.stats.scanned++;
    
    if (data.listings && data.listings.length > 0) {
      this.currentSession.stats.found += data.listings.length;
      this.results.push(...data.listings);
    }
    
    // Close tab
    chrome.tabs.remove(tabId);
    
    // Check if done
    if (this.queue.length === 0 && this.activeTabs.size === 0) {
      this.completeSession();
    }
  }
  
  handleTimeout(tabId) {
    this.activeTabs.delete(tabId);
    this.currentSession.stats.errors++;
    chrome.tabs.remove(tabId);
  }
  
  completeSession() {
    this.isRunning = false;
    this.currentSession.endTime = Date.now();
    this.currentSession.results = this.results;
    
    // Notify
    chrome.runtime.sendMessage({
      action: 'AUTOMATION_COMPLETE',
      session: this.currentSession
    });
    
    // Reset
    this.currentSession = null;
    this.results = [];
  }
  
  stopSession() {
    this.isRunning = false;
    
    // Close all active tabs
    this.activeTabs.forEach((info, tabId) => {
      chrome.tabs.remove(tabId);
    });
    
    this.activeTabs.clear();
    this.queue = [];
    
    if (this.currentSession) {
      this.currentSession.cancelled = true;
      this.completeSession();
    }
  }
}

window.automationEngine = new AutomationEngine();
EOF

# Create parser.js
cat > extension/dist/js/parser.js << 'EOF'
// ListingParser v3.5.0 - Extract structured data from listings
class ListingParser {
  constructor() {
    this.patterns = {
      gpu: /\b(RTX|GTX|RX|Arc)\s*\d{4}\w*/gi,
      cpu: /\b(i[357]|Ryzen\s*[357]|Xeon)\s*\d{4}\w*/gi,
      ram: /\b\d{1,3}\s*GB\s*(RAM|Memory|DDR)/gi,
      storage: /\b\d+\s*(GB|TB)\s*(SSD|HDD|NVMe)/gi,
      price: /\$\s*\d+\.?\d*/g
    };
  }
  
  parse(listing) {
    const text = `${listing.title} ${listing.description}`.toLowerCase();
    
    return {
      ...listing,
      specs: this.extractSpecs(text),
      condition: this.assessCondition(text),
      analysis: this.analyzeDeal(listing)
    };
  }
  
  extractSpecs(text) {
    return {
      gpu: this.extract(text, this.patterns.gpu),
      cpu: this.extract(text, this.patterns.cpu),
      ram: this.extract(text, this.patterns.ram),
      storage: this.extract(text, this.patterns.storage)
    };
  }
  
  extract(text, pattern) {
    const matches = text.match(pattern);
    return matches ? matches[0] : null;
  }
  
  assessCondition(text) {
    const conditions = {
      'like new': 0.95,
      'excellent': 0.90,
      'very good': 0.85,
      'good': 0.80,
      'fair': 0.70,
      'parts': 0.50
    };
    
    for (const [term, score] of Object.entries(conditions)) {
      if (text.includes(term)) {
        return { term, score };
      }
    }
    
    return { term: 'unknown', score: 0.75 };
  }
  
  analyzeDeal(listing) {
    const specs = this.extractSpecs(`${listing.title} ${listing.description}`);
    const fmv = this.calculateFMV(specs);
    const profit = fmv - listing.price;
    const roi = (profit / listing.price) * 100;
    
    return {
      fmv,
      profit,
      roi,
      rating: this.rateDeal(roi)
    };
  }
  
  calculateFMV(specs) {
    // Simplified FMV calculation
    let value = 400; // Base value
    
    if (specs.gpu) {
      if (specs.gpu.includes('3080')) value += 500;
      else if (specs.gpu.includes('3070')) value += 400;
      else if (specs.gpu.includes('3060')) value += 300;
    }
    
    if (specs.cpu) {
      if (specs.cpu.includes('i7')) value += 200;
      else if (specs.cpu.includes('i5')) value += 150;
    }
    
    return value;
  }
  
  rateDeal(roi) {
    if (roi >= 50) return 'excellent';
    if (roi >= 30) return 'good';
    if (roi >= 20) return 'fair';
    return 'poor';
  }
}

window.listingParser = new ListingParser();
EOF

# Create pipeline-manager.js
cat > extension/dist/js/pipeline-manager.js << 'EOF'
// PipelineManager v3.5.0 - Deal pipeline state management
class PipelineManager {
  constructor() {
    this.deals = new Map();
    this.stages = [
      'scanner',
      'analysis', 
      'contacted',
      'negotiating',
      'scheduled',
      'purchased',
      'testing',
      'listed',
      'sold'
    ];
    
    this.init();
  }
  
  async init() {
    const stored = await chrome.storage.local.get(['deals']);
    if (stored.deals) {
      stored.deals.forEach(deal => {
        this.deals.set(deal.id, deal);
      });
    }
  }
  
  createDeal(listing) {
    const deal = {
      id: Date.now().toString(),
      listing: listing,
      stage: 'scanner',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      notes: [],
      tasks: [],
      metrics: {
        daysInPipeline: 0,
        touchpoints: 0
      }
    };
    
    this.deals.set(deal.id, deal);
    this.save();
    
    return deal;
  }
  
  updateStage(dealId, newStage) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    const oldStage = deal.stage;
    deal.stage = newStage;
    deal.updatedAt = Date.now();
    
    // Update metrics
    deal.metrics.touchpoints++;
    deal.metrics.daysInPipeline = Math.floor(
      (Date.now() - deal.createdAt) / (1000 * 60 * 60 * 24)
    );
    
    this.save();
    
    return { deal, oldStage, newStage };
  }
  
  addNote(dealId, note) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    deal.notes.push({
      id: Date.now().toString(),
      text: note,
      timestamp: Date.now()
    });
    
    deal.updatedAt = Date.now();
    this.save();
    
    return deal;
  }
  
  addTask(dealId, task) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    deal.tasks.push({
      id: Date.now().toString(),
      text: task,
      completed: false,
      createdAt: Date.now()
    });
    
    deal.updatedAt = Date.now();
    this.save();
    
    return deal;
  }
  
  completeTask(dealId, taskId) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    const task = deal.tasks.find(t => t.id === taskId);
    if (task) {
      task.completed = true;
      task.completedAt = Date.now();
      deal.updatedAt = Date.now();
      this.save();
    }
    
    return deal;
  }
  
  getDealsByStage(stage) {
    return Array.from(this.deals.values())
      .filter(deal => deal.stage === stage);
  }
  
  getStats() {
    const stats = {
      total: this.deals.size,
      byStage: {},
      avgDaysInPipeline: 0,
      completionRate: 0
    };
    
    let totalDays = 0;
    let completed = 0;
    
    this.deals.forEach(deal => {
      stats.byStage[deal.stage] = (stats.byStage[deal.stage] || 0) + 1;
      totalDays += deal.metrics.daysInPipeline;
      
      if (deal.stage === 'sold') {
        completed++;
      }
    });
    
    stats.avgDaysInPipeline = this.deals.size > 0 
      ? totalDays / this.deals.size 
      : 0;
      
    stats.completionRate = this.deals.size > 0
      ? (completed / this.deals.size) * 100
      : 0;
    
    return stats;
  }
  
  async save() {
    const dealsArray = Array.from(this.deals.values());
    await chrome.storage.local.set({ deals: dealsArray });
  }
}

window.pipelineManager = new PipelineManager();
EOF

# Create dashboard-full.js
cat > extension/dist/js/dashboard-full.js << 'EOF'
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
EOF

# Create remaining CSS files
cat > extension/dist/css/search-builder.css << 'EOF'
/* SearchBuilder Styles */
.search-builder {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.keyword-input {
  display: flex;
  gap: 8px;
}

.keyword-suggestions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.suggestion-chip {
  padding: 4px 12px;
  background: #e3f2fd;
  border-radius: 16px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-chip:hover {
  background: #1976d2;
  color: white;
}

.filter-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.filter-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #666;
}

.platform-select {
  display: flex;
  gap: 12px;
}

.platform-option {
  padding: 8px 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.platform-option.selected {
  border-color: #1976d2;
  background: #e3f2fd;
}

.search-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
EOF

cat > extension/dist/css/settings.css << 'EOF'
/* Settings Styles */
.settings-page {
  display: flex;
  height: 100%;
  background: #f5f5f5;
}

.settings-container {
  display: flex;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.settings-sidebar {
  width: 240px;
  background: #fafafa;
  border-right: 1px solid #e0e0e0;
}

.settings-nav {
  padding: 20px 0;
}

.settings-nav-item {
  display: block;
  padding: 12px 24px;
  color: #666;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.settings-nav-item:hover {
  background: #f0f0f0;
  color: #333;
}

.settings-nav-item.active {
  background: #e3f2fd;
  color: #1976d2;
  border-left: 3px solid #1976d2;
}

.settings-main {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.settings-section {
  max-width: 600px;
}

.settings-section h2 {
  margin-bottom: 24px;
  color: #333;
}

.settings-group {
  margin-bottom: 32px;
}

.settings-group h3 {
  margin-bottom: 16px;
  color: #555;
  font-size: 18px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.setting-label {
  flex: 1;
}

.setting-label h4 {
  margin: 0 0 4px 0;
  color: #333;
  font-weight: 500;
}

.setting-description {
  color: #666;
  font-size: 14px;
}

.form-input,
.form-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #1976d2;
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.settings-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid #e0e0e0;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #d32f2f;
}
EOF

# Create onboarding.html
cat > extension/dist/onboarding.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to PC Arbitrage Pro</title>
</head>
<body>
  <div id="root"></div>
  <script src="js/settings-manager.js"></script>
  <script src="js/onboarding.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      window.onboarding.init('root');
    });
  </script>
</body>
</html>
EOF

# Update dashboard.html to include all scripts
cat > extension/dist/dashboard.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gaming PC Arbitrage Dashboard v3.11.0</title>
  <link rel="stylesheet" href="css/dashboard.css">
  <link rel="stylesheet" href="css/search-builder.css">
  <link rel="stylesheet" href="css/settings.css">
</head>
<body>
  <div id="root">Loading...</div>
  
  <!-- Core modules -->
  <script src="js/router.js"></script>
  <script src="js/settings-manager.js"></script>
  <script src="js/search-builder.js"></script>
  <script src="js/automation-engine.js"></script>
  <script src="js/parser.js"></script>
  <script src="js/pipeline-manager.js"></script>
  
  <!-- Dashboard -->
  <script src="js/dashboard-full.js"></script>
</body>
</html>
EOF

echo "All files created successfully!"
EOF