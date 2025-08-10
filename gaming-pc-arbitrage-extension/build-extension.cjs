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
    
    // Copy CSS
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
    
    // 3. Create minimal HTML files
    console.log('📄 Creating HTML files...');
    
    // Popup HTML
    const popupHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>PC Arbitrage Assistant</title>
  <link rel="stylesheet" href="css/popup.css">
</head>
<body>
  <div id="root"></div>
  <script src="js/popup.js"></script>
</body>
</html>`;
    
    await fs.writeFile(path.join(DIST_DIR, 'popup.html'), popupHtml);
    
    // Options HTML
    const optionsHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Settings - PC Arbitrage Assistant</title>
  <link rel="stylesheet" href="css/options.css">
</head>
<body>
  <div id="root"></div>
  <script src="js/options.js"></script>
</body>
</html>`;
    
    await fs.writeFile(path.join(DIST_DIR, 'options.html'), optionsHtml);
    
    // Dashboard HTML
    const dashboardHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Dashboard - PC Arbitrage Assistant</title>
  <link rel="stylesheet" href="css/dashboard.css">
</head>
<body>
  <div id="root"></div>
  <script src="js/dashboard.js"></script>
</body>
</html>`;
    
    await fs.writeFile(path.join(DIST_DIR, 'dashboard.html'), dashboardHtml);
    
    // 4. Create minimal JS files
    console.log('📦 Creating JavaScript files...');
    await fs.ensureDir(path.join(DIST_DIR, 'js'));
    
    // Background script
    const backgroundJs = `// Background service worker
console.log('Gaming PC Arbitrage Extension - Background Service Worker');

chrome.runtime.onInstalled.addListener((details) => {
  console.log('Extension installed:', details.reason);
  
  if (details.reason === 'install') {
    chrome.storage.local.set({
      settings: {
        version: '1.0.0',
        enabled: true
      }
    });
  }
});

// Message handler
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request.type);
  sendResponse({ success: true });
  return true;
});`;
    
    await fs.writeFile(path.join(DIST_DIR, 'js/background.js'), backgroundJs);
    
    // Content script
    const contentJs = `// Content script
console.log('Gaming PC Arbitrage Extension - Content Script loaded');

// Check if we're on a supported platform
const hostname = window.location.hostname;
const isSupported = 
  hostname.includes('facebook.com') ||
  hostname.includes('craigslist.org') ||
  hostname.includes('offerup.com');

if (isSupported) {
  console.log('Platform supported:', hostname);
  
  // Send message to background
  chrome.runtime.sendMessage({
    type: 'CONTENT_LOADED',
    platform: hostname
  });
}`;
    
    await fs.writeFile(path.join(DIST_DIR, 'js/content-facebook.js'), contentJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/content-craigslist.js'), contentJs);
    await fs.writeFile(path.join(DIST_DIR, 'js/content-offerup.js'), contentJs);
    
    // Popup script
    const popupJs = `// Popup script
document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('root');
  root.innerHTML = \`
    <div style="width: 350px; padding: 20px; font-family: Arial, sans-serif;">
      <h1 style="font-size: 18px; margin: 0 0 10px 0;">PC Arbitrage Assistant</h1>
      <p style="margin: 0 0 15px 0; color: #666;">Find profitable gaming PC deals</p>
      
      <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
        <strong>Status:</strong> Active ✅
      </div>
      
      <button id="dashboard" style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 10px;">
        Open Dashboard
      </button>
      
      <button id="settings" style="width: 100%; padding: 10px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Settings
      </button>
    </div>
  \`;
  
  document.getElementById('dashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
  });
  
  document.getElementById('settings').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});`;
    
    await fs.writeFile(path.join(DIST_DIR, 'js/popup.js'), popupJs);
    
    // Options script
    const optionsJs = `// Options script
document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('root');
  root.innerHTML = \`
    <div style="max-width: 600px; margin: 20px auto; padding: 20px; font-family: Arial, sans-serif;">
      <h1>Settings</h1>
      <p>Configure your PC arbitrage preferences</p>
      
      <div style="margin-top: 30px;">
        <label style="display: block; margin-bottom: 5px;">
          <input type="checkbox" checked> Enable extension
        </label>
        
        <label style="display: block; margin-bottom: 5px;">
          <input type="checkbox" checked> Show notifications
        </label>
        
        <label style="display: block; margin-bottom: 5px;">
          <input type="checkbox"> Advanced mode
        </label>
      </div>
      
      <button style="margin-top: 20px; padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Save Settings
      </button>
    </div>
  \`;
});`;
    
    await fs.writeFile(path.join(DIST_DIR, 'js/options.js'), optionsJs);
    
    // Dashboard script
    const dashboardJs = `// Dashboard script
document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('root');
  root.innerHTML = \`
    <div style="max-width: 1200px; margin: 20px auto; padding: 20px; font-family: Arial, sans-serif;">
      <h1>PC Arbitrage Dashboard</h1>
      <p>Track your deals and analyze performance</p>
      
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px;">
        <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
          <h3>Active Deals</h3>
          <p style="font-size: 36px; font-weight: bold; margin: 10px 0;">0</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
          <h3>Total Profit</h3>
          <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #4CAF50;">$0</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
          <h3>Avg ROI</h3>
          <p style="font-size: 36px; font-weight: bold; margin: 10px 0;">0%</p>
        </div>
      </div>
      
      <div style="margin-top: 40px;">
        <h2>Recent Listings</h2>
        <p style="color: #666;">No listings found. Visit Facebook Marketplace to start finding deals!</p>
      </div>
    </div>
  \`;
});`;
    
    await fs.writeFile(path.join(DIST_DIR, 'js/dashboard.js'), dashboardJs);
    
    // 5. Create CSS files
    console.log('🎨 Creating CSS files...');
    await fs.ensureDir(path.join(DIST_DIR, 'css'));
    
    const baseCSS = `/* Base styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}`;
    
    await fs.writeFile(path.join(DIST_DIR, 'css/popup.css'), baseCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/options.css'), baseCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/dashboard.css'), baseCSS);
    await fs.writeFile(path.join(DIST_DIR, 'css/overlay.css'), baseCSS);
    
    // 6. Create ZIP file
    console.log('📦 Creating extension package...');
    const output = fs.createWriteStream(path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip'));
    const archive = archiver('zip', { zlib: { level: 9 } });
    
    output.on('close', () => {
      console.log(`\n✅ Build complete!`);
      console.log(`📦 Extension package: ${path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip')}`);
      console.log(`📁 Unpacked extension: ${DIST_DIR}`);
      console.log(`\nTo install:`);
      console.log(`1. Open Chrome and go to chrome://extensions/`);
      console.log(`2. Enable "Developer mode"`);
      console.log(`3. Click "Load unpacked" and select: ${DIST_DIR}`);
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