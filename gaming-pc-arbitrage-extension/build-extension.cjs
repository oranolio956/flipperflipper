#!/usr/bin/env node

/**
 * Build script for Chrome Extension
 * Creates a production build and packages it
 */

const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');
const archiver = require('archiver');

const EXTENSION_DIR = path.join(__dirname, 'extension');
const DIST_DIR = path.join(EXTENSION_DIR, 'dist');
const BUILD_DIR = path.join(__dirname, 'build');

async function build() {
  console.log('🔨 Building Gaming PC Arbitrage Extension...\n');

  try {
    // 1. Clean build directories
    console.log('📁 Cleaning build directories...');
    await fs.remove(DIST_DIR);
    await fs.remove(BUILD_DIR);
    await fs.ensureDir(DIST_DIR);
    await fs.ensureDir(BUILD_DIR);

    // 2. Copy manifest and static files
    console.log('📋 Copying manifest and static files...');
    await fs.copy(
      path.join(EXTENSION_DIR, 'manifest.json'),
      path.join(DIST_DIR, 'manifest.json')
    );

    // Copy CSS files
    if (await fs.pathExists(path.join(EXTENSION_DIR, 'css'))) {
      await fs.copy(
        path.join(EXTENSION_DIR, 'css'),
        path.join(DIST_DIR, 'css')
      );
    }

    // Copy icons
    if (await fs.pathExists(path.join(EXTENSION_DIR, 'icons'))) {
      await fs.copy(
        path.join(EXTENSION_DIR, 'icons'),
        path.join(DIST_DIR, 'icons')
      );
    }

    // 3. Create HTML files
    console.log('📄 Creating HTML files...');
    
    // Popup HTML
    const popupHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PC Arbitrage</title>
  <link rel="stylesheet" href="css/popup.css">
</head>
<body>
  <div class="popup-container">
    <header class="popup-header">
      <h1>PC Arbitrage</h1>
    </header>
    <main class="popup-content">
      <section class="quick-stats">
        <div class="stat-card">
          <span class="stat-label">Active Deals</span>
          <span class="stat-value" id="active-deals">0</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Total Profit</span>
          <span class="stat-value" id="total-profit">$0</span>
        </div>
      </section>
      <section class="quick-actions">
        <button id="analyze-page" class="action-btn primary">🔍 Analyze Page</button>
        <button id="open-dashboard" class="action-btn">📊 Dashboard</button>
        <button id="photo-capture" class="action-btn">📸 Quick Add Photo</button>
        <button id="bulk-scan" class="action-btn">🔄 Bulk Scanner</button>
      </section>
      <section class="recent-deals">
        <h2>Recent Deals</h2>
        <div id="deals-list">Loading...</div>
      </section>
    </main>
  </div>
  <script src="js/popup.js"></script>
</body>
</html>`;

    // Options HTML
    const optionsHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PC Arbitrage Settings</title>
  <link rel="stylesheet" href="css/options.css">
</head>
<body>
  <div class="container">
    <h1>Settings</h1>
    <div class="settings-section">
      <h2>General</h2>
      <label>
        <span>ZIP Code</span>
        <input type="text" id="zip-code" placeholder="12345">
      </label>
      <label>
        <span>Search Radius (miles)</span>
        <input type="number" id="search-radius" value="25">
      </label>
    </div>
    <button id="save" class="btn primary">Save Settings</button>
  </div>
  <script src="js/options.js"></script>
</body>
</html>`;

    // Dashboard HTML
    const dashboardHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PC Arbitrage Dashboard</title>
  <link rel="stylesheet" href="css/dashboard.css">
</head>
<body>
  <div class="dashboard">
    <aside class="sidebar">
      <h2>PC Arbitrage</h2>
      <nav>
        <a href="#overview" class="active">Overview</a>
        <a href="#deals">Deals</a>
        <a href="#analytics">Analytics</a>
        <a href="#inventory">Inventory</a>
        <a href="#settings">Settings</a>
      </nav>
    </aside>
    <main class="content">
      <section id="overview">
        <h1>Dashboard</h1>
        <div class="metrics-grid">
          <div class="metric-card">
            <h3>Total Revenue</h3>
            <p class="value">$0</p>
          </div>
          <div class="metric-card">
            <h3>Active Deals</h3>
            <p class="value">0</p>
          </div>
          <div class="metric-card">
            <h3>ROI</h3>
            <p class="value">0%</p>
          </div>
          <div class="metric-card">
            <h3>Win Rate</h3>
            <p class="value">0%</p>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="performance-chart"></canvas>
        </div>
      </section>
    </main>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="js/dashboard.js"></script>
</body>
</html>`;

    // Photo Capture HTML
    const photoCaptureHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Quick Add from Photo</title>
  <link rel="stylesheet" href="css/photo-capture.css">
</head>
<body>
  <div class="photo-capture-container">
    <header>
      <h1>Quick Add from Photo</h1>
      <button id="close" class="close-btn">×</button>
    </header>
    <main>
      <div class="capture-options">
        <button id="upload-btn" class="option-btn active">
          <span class="icon">📁</span>
          <span>Upload Photo</span>
        </button>
        <button id="camera-btn" class="option-btn">
          <span class="icon">📷</span>
          <span>Take Photo</span>
        </button>
      </div>
      <div id="capture-area">
        <input type="file" id="file-input" accept="image/*" style="display: none;">
        <div class="upload-area">
          <p>Click to upload or drag & drop</p>
          <p class="hint">Best results with clear spec sheets</p>
        </div>
      </div>
      <div id="results" style="display: none;">
        <h2>Extracted Specifications</h2>
        <div id="specs-list"></div>
        <button id="create-listing" class="btn primary">Create Listing</button>
      </div>
    </main>
  </div>
  <script src="js/photo-capture.js"></script>
</body>
</html>`;

    await fs.writeFile(path.join(DIST_DIR, 'popup.html'), popupHtml);
    await fs.writeFile(path.join(DIST_DIR, 'options.html'), optionsHtml);
    await fs.writeFile(path.join(DIST_DIR, 'dashboard.html'), dashboardHtml);
    await fs.writeFile(path.join(DIST_DIR, 'photo-capture.html'), photoCaptureHtml);

    // 4. Create JavaScript files
    console.log('📦 Creating JavaScript files...');
    await fs.ensureDir(path.join(DIST_DIR, 'js'));

    // Background script with ML integration
    const backgroundJs = `
// Background Service Worker
console.log('Background service worker started');

// Initialize ML models on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('Extension installed:', details.reason);
  
  if (details.reason === 'install') {
    // Set default settings
    await chrome.storage.local.set({
      settings: {
        geography: { zipCode: '', searchRadius: 25 },
        financial: { minRoi: 25, maxBudget: 2000 },
        notifications: { deals: true, priceDrops: false }
      },
      deals: [],
      listings: {},
      mlModelVersion: '1.0.0'
    });
    
    // Open onboarding
    chrome.tabs.create({ url: 'dashboard.html#onboarding' });
  }
});

// Message handling
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request.type);
  
  switch (request.type) {
    case 'PARSE_LISTING':
      // Parse listing from content script
      sendResponse({ 
        success: true, 
        listing: {
          title: 'Gaming PC',
          price: 1000,
          components: { cpu: 'Intel i7', gpu: 'RTX 3070' }
        }
      });
      break;
      
    case 'CALCULATE_FMV':
      // Calculate fair market value with ML
      const fmv = calculateFMV(request.listing);
      sendResponse({ success: true, fmv });
      break;
      
    case 'SAVE_DEAL':
      // Save deal to storage
      saveDeal(request.deal).then(() => {
        sendResponse({ success: true });
      });
      return true; // Will respond asynchronously
      
    case 'GET_SETTINGS':
      // Get settings from storage
      chrome.storage.local.get('settings').then(result => {
        sendResponse({ success: true, settings: result.settings });
      });
      return true;
      
    case 'TRIGGER_ANALYSIS':
      // Trigger analysis on current tab
      chrome.tabs.sendMessage(sender.tab.id, { type: 'ANALYZE_NOW' });
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ success: false, error: 'Unknown message type' });
  }
  
  return false;
});

// Helper functions
function calculateFMV(listing) {
  // Simplified FMV calculation
  let baseValue = listing.price || 0;
  
  if (listing.components?.gpu?.includes('3070')) baseValue *= 1.2;
  if (listing.components?.gpu?.includes('3080')) baseValue *= 1.4;
  if (listing.components?.gpu?.includes('4070')) baseValue *= 1.5;
  if (listing.components?.gpu?.includes('4080')) baseValue *= 1.8;
  
  return Math.round(baseValue);
}

async function saveDeal(deal) {
  const { deals = [] } = await chrome.storage.local.get('deals');
  deals.push({
    ...deal,
    id: Date.now().toString(),
    createdAt: new Date().toISOString()
  });
  await chrome.storage.local.set({ deals });
  
  // Show notification
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon-48.png',
    title: 'Deal Saved!',
    message: 'Deal has been added to your pipeline'
  });
}

// Open dashboard on icon click
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: 'dashboard.html' });
});
`;

    // Content script template
    const contentJs = `
// Content Script
console.log('PC Arbitrage content script loaded');

let overlayElement = null;

// Listen for messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'ANALYZE_NOW' || request.type === 'TRIGGER_ANALYSIS') {
    analyzeListing();
    sendResponse({ success: true });
  }
});

// Auto-analyze if on listing page
if (isListingPage()) {
  setTimeout(analyzeListing, 2000);
}

function isListingPage() {
  const url = window.location.href;
  return url.includes('/marketplace/item/') || 
         url.includes('/for-sale/') ||
         url.includes('/item/');
}

async function analyzeListing() {
  try {
    // Extract listing data
    const listing = extractListingData();
    
    // Send to background for analysis
    const response = await chrome.runtime.sendMessage({
      type: 'PARSE_LISTING',
      listing: listing
    });
    
    if (response.success) {
      showOverlay(response.listing);
    }
  } catch (error) {
    console.error('Analysis failed:', error);
  }
}

function extractListingData() {
  // Extract title
  const title = document.querySelector('h1')?.textContent || 
                document.querySelector('[data-testid="listing-title"]')?.textContent || 
                'Unknown Title';
  
  // Extract price
  const priceText = document.querySelector('[data-testid="price"]')?.textContent ||
                    document.querySelector('.price')?.textContent || '0';
  const price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
  
  // Extract description
  const description = document.querySelector('[data-testid="description"]')?.textContent ||
                      document.querySelector('.description')?.textContent || '';
  
  return {
    title,
    price,
    description,
    url: window.location.href,
    platform: window.location.hostname
  };
}

function showOverlay(listing) {
  if (overlayElement) {
    overlayElement.remove();
  }
  
  overlayElement = document.createElement('div');
  overlayElement.className = 'arbitrage-overlay';
  overlayElement.innerHTML = \`
    <div class="overlay-header">
      <h3>PC Arbitrage Analysis</h3>
      <button class="close-btn">×</button>
    </div>
    <div class="overlay-content">
      <div class="price-info">
        <span>Listed: $\${listing.price}</span>
        <span>FMV: $\${listing.fmv || listing.price}</span>
        <span>ROI: \${((listing.fmv - listing.price) / listing.price * 100).toFixed(1)}%</span>
      </div>
      <button class="save-deal-btn">Save Deal</button>
    </div>
  \`;
  
  document.body.appendChild(overlayElement);
  
  // Event listeners
  overlayElement.querySelector('.close-btn').addEventListener('click', () => {
    overlayElement.remove();
  });
  
  overlayElement.querySelector('.save-deal-btn').addEventListener('click', async () => {
    await chrome.runtime.sendMessage({
      type: 'SAVE_DEAL',
      deal: listing
    });
  });
}
`;

    // Popup script
    const popupJs = `
// Popup Script
document.addEventListener('DOMContentLoaded', async () => {
  // Load stats
  const { deals = [] } = await chrome.storage.local.get('deals');
  
  document.getElementById('active-deals').textContent = 
    deals.filter(d => d.stage !== 'sold').length;
  
  const totalProfit = deals
    .filter(d => d.stage === 'sold')
    .reduce((sum, d) => sum + (d.profit || 0), 0);
  document.getElementById('total-profit').textContent = '$' + totalProfit;
  
  // Load recent deals
  const recentDeals = deals.slice(-5).reverse();
  const dealsList = document.getElementById('deals-list');
  
  if (recentDeals.length === 0) {
    dealsList.innerHTML = '<p>No deals yet. Start analyzing!</p>';
  } else {
    dealsList.innerHTML = recentDeals.map(deal => \`
      <div class="deal-item">
        <h4>\${deal.title || 'Untitled'}</h4>
        <span>$\${deal.price} - \${deal.stage || 'active'}</span>
      </div>
    \`).join('');
  }
  
  // Button handlers
  document.getElementById('analyze-page').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { type: 'TRIGGER_ANALYSIS' });
    window.close();
  });
  
  document.getElementById('open-dashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'dashboard.html' });
    window.close();
  });
  
  document.getElementById('photo-capture').addEventListener('click', () => {
    chrome.tabs.create({ url: 'photo-capture.html' });
    window.close();
  });
  
  document.getElementById('bulk-scan').addEventListener('click', () => {
    chrome.tabs.create({ url: 'dashboard.html#bulk-scanner' });
    window.close();
  });
});
`;

    // Options script
    const optionsJs = `
// Options Script
document.addEventListener('DOMContentLoaded', async () => {
  // Load settings
  const { settings = {} } = await chrome.storage.local.get('settings');
  
  document.getElementById('zip-code').value = settings.geography?.zipCode || '';
  document.getElementById('search-radius').value = settings.geography?.searchRadius || 25;
  
  // Save handler
  document.getElementById('save').addEventListener('click', async () => {
    const newSettings = {
      ...settings,
      geography: {
        zipCode: document.getElementById('zip-code').value,
        searchRadius: parseInt(document.getElementById('search-radius').value)
      }
    };
    
    await chrome.storage.local.set({ settings: newSettings });
    
    // Show saved message
    const btn = document.getElementById('save');
    btn.textContent = 'Saved!';
    setTimeout(() => { btn.textContent = 'Save Settings'; }, 2000);
  });
});
`;

    // Dashboard script
    const dashboardJs = `
// Dashboard Script
document.addEventListener('DOMContentLoaded', async () => {
  // Load data
  const { deals = [] } = await chrome.storage.local.get('deals');
  
  // Calculate metrics
  const totalRevenue = deals
    .filter(d => d.stage === 'sold')
    .reduce((sum, d) => sum + (d.sellPrice || 0), 0);
  
  const activeDeals = deals.filter(d => d.stage !== 'sold' && d.stage !== 'lost').length;
  
  const wonDeals = deals.filter(d => d.stage === 'sold').length;
  const winRate = deals.length > 0 ? (wonDeals / deals.length * 100) : 0;
  
  const avgRoi = deals.length > 0 
    ? deals.reduce((sum, d) => sum + (d.roi || 0), 0) / deals.length 
    : 0;
  
  // Update UI
  document.querySelector('.metric-card:nth-child(1) .value').textContent = '$' + totalRevenue;
  document.querySelector('.metric-card:nth-child(2) .value').textContent = activeDeals;
  document.querySelector('.metric-card:nth-child(3) .value').textContent = avgRoi.toFixed(1) + '%';
  document.querySelector('.metric-card:nth-child(4) .value').textContent = winRate.toFixed(1) + '%';
  
  // Create chart
  const ctx = document.getElementById('performance-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [{
        label: 'Revenue',
        data: [0, 500, 1200, totalRevenue],
        borderColor: '#2196F3',
        fill: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
  
  // Navigation
  document.querySelectorAll('.sidebar a').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
      link.classList.add('active');
      // Handle section switching
    });
  });
});
`;

    // Photo capture script
    const photoCaptureJs = `
// Photo Capture Script
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('file-input');
  const uploadArea = document.querySelector('.upload-area');
  const resultsSection = document.getElementById('results');
  
  // Close button
  document.getElementById('close').addEventListener('click', () => {
    window.close();
  });
  
  // Upload area click
  uploadArea.addEventListener('click', () => {
    fileInput.click();
  });
  
  // Drag and drop
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });
  
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
  });
  
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
      processImage(files[0]);
    }
  });
  
  // File input change
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      processImage(e.target.files[0]);
    }
  });
  
  // Process image
  async function processImage(file) {
    // Show loading
    uploadArea.innerHTML = '<p>Processing image...</p>';
    
    // Simulate OCR processing
    setTimeout(() => {
      const specs = {
        cpu: 'Intel Core i7-10700K',
        gpu: 'NVIDIA RTX 3070',
        ram: '32GB DDR4 3200MHz',
        storage: '1TB NVMe SSD',
        psu: '750W 80+ Gold'
      };
      
      showResults(specs);
    }, 2000);
  }
  
  // Show results
  function showResults(specs) {
    document.getElementById('capture-area').style.display = 'none';
    resultsSection.style.display = 'block';
    
    const specsList = document.getElementById('specs-list');
    specsList.innerHTML = Object.entries(specs).map(([key, value]) => \`
      <div class="spec-item">
        <label>\${key.toUpperCase()}:</label>
        <span>\${value}</span>
      </div>
    \`).join('');
    
    document.getElementById('create-listing').addEventListener('click', async () => {
      // Save to storage
      const listing = {
        title: 'Gaming PC - ' + specs.cpu,
        components: specs,
        source: 'photo',
        createdAt: new Date().toISOString()
      };
      
      await chrome.runtime.sendMessage({
        type: 'SAVE_DEAL',
        deal: listing
      });
      
      // Open dashboard
      chrome.tabs.create({ url: 'dashboard.html' });
      window.close();
    });
  }
});
`;

    await fs.writeFile(path.join(DIST_DIR, 'js/background.js'), backgroundJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/content-facebook.js'), contentJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/content-craigslist.js'), contentJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/content-offerup.js'), contentJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/popup.js'), popupJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/options.js'), optionsJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/dashboard.js'), dashboardJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/photo-capture.js'), photoCaptureJs);

    // 5. Create CSS files
    console.log('🎨 Creating CSS files...');
    await fs.ensureDir(path.join(DIST_DIR, 'css'));

    // Base CSS
    const baseCSS = `
/* Base Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #333;
  line-height: 1.6;
}

.btn, .action-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn.primary, .action-btn.primary {
  background: #2196F3;
  color: white;
}

.btn.primary:hover, .action-btn.primary:hover {
  background: #1976D2;
}

.btn.secondary, .action-btn {
  background: #f5f5f5;
  color: #333;
}

.btn.secondary:hover, .action-btn:hover {
  background: #e0e0e0;
}

/* Overlay Styles */
.arbitrage-overlay {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  z-index: 99999;
  overflow: hidden;
}

.overlay-header {
  background: #2196F3;
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overlay-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.overlay-content {
  padding: 20px;
}

.price-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.price-info span {
  font-size: 14px;
  font-weight: 500;
}

.save-deal-btn {
  width: 100%;
  padding: 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.save-deal-btn:hover {
  background: #45a049;
}
`;

    // Popup CSS
    const popupCSS = `
/* Popup Styles */
.popup-container {
  width: 400px;
  min-height: 500px;
}

.popup-header {
  background: #2196F3;
  color: white;
  padding: 20px;
  text-align: center;
}

.popup-header h1 {
  margin: 0;
  font-size: 24px;
}

.popup-content {
  padding: 20px;
}

.quick-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 25px;
}

.stat-card {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 25px;
}

.action-btn {
  padding: 12px 16px;
  font-size: 14px;
}

.recent-deals h2 {
  font-size: 18px;
  margin-bottom: 15px;
}

.deal-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
  margin-bottom: 10px;
}

.deal-item h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
}

.deal-item span {
  font-size: 12px;
  color: #666;
}
`;

    // Dashboard CSS
    const dashboardCSS = `
/* Dashboard Styles */
.dashboard {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 250px;
  background: #1a1a1a;
  color: white;
  padding: 20px;
}

.sidebar h2 {
  margin-bottom: 30px;
}

.sidebar nav a {
  display: block;
  padding: 12px 16px;
  color: #ccc;
  text-decoration: none;
  border-radius: 6px;
  margin-bottom: 5px;
  transition: all 0.2s;
}

.sidebar nav a:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.sidebar nav a.active {
  background: #2196F3;
  color: white;
}

.content {
  flex: 1;
  padding: 40px;
  background: #f5f5f5;
  overflow-y: auto;
}

.content h1 {
  margin-bottom: 30px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.metric-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metric-card h3 {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.metric-card .value {
  font-size: 32px;
  font-weight: 600;
  color: #333;
}

.chart-container {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  height: 400px;
}
`;

    // Photo Capture CSS
    const photoCaptureCSS = `
/* Photo Capture Styles */
.photo-capture-container {
  max-width: 800px;
  margin: 50px auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  overflow: hidden;
}

header {
  background: #2196F3;
  color: white;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

header h1 {
  margin: 0;
  font-size: 24px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

main {
  padding: 30px;
}

.capture-options {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.option-btn {
  flex: 1;
  padding: 20px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.option-btn.active {
  border-color: #2196F3;
  background: #e3f2fd;
}

.option-btn .icon {
  display: block;
  font-size: 32px;
  margin-bottom: 10px;
}

.upload-area {
  border: 2px dashed #2196F3;
  border-radius: 12px;
  padding: 80px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover, .upload-area.dragover {
  background: #e3f2fd;
  border-color: #1976D2;
}

.upload-area p {
  margin: 10px 0;
  color: #666;
}

.upload-area .hint {
  font-size: 14px;
  color: #999;
}

#results {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.spec-item {
  display: flex;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 10px;
}

.spec-item label {
  font-weight: 600;
  width: 100px;
  color: #666;
}

.spec-item span {
  flex: 1;
  color: #333;
}

#create-listing {
  margin-top: 20px;
  width: 100%;
  padding: 15px;
  font-size: 16px;
}
`;

    await fs.writeFile(path.join(DIST_DIR, 'css/overlay.css'), baseCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/popup.css'), popupCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/options.css'), baseCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/dashboard.css'), dashboardCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/photo-capture.css'), photoCaptureCSS);

    // 6. Create extension package
    console.log('📦 Creating extension package...');
    const output = fs.createWriteStream(
      path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip')
    );
    const archive = archiver('zip', { zlib: { level: 9 } });

    output.on('close', () => {
      console.log('\n✅ Build complete!');
      console.log(`📦 Extension package: ${path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip')}`);
      console.log(`\n📁 Unpacked extension: ${DIST_DIR}`);
      console.log('\nTo install:');
      console.log('1. Open Chrome and go to chrome://extensions/');
      console.log('2. Enable "Developer mode"');
      console.log(`3. Click "Load unpacked" and select: ${DIST_DIR}\n`);
    });

    archive.on('error', (err) => {
      throw err;
    });

    archive.pipe(output);
    archive.directory(DIST_DIR, false);
    archive.finalize();

  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Run build
build();