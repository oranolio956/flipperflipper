/**
 * Background Service Worker
 * Handles extension lifecycle, alarms, and automation
 */

import { MaxAutoEngine } from './automation';
import { UpdateChecker } from './updateChecker';
import { settingsManager } from '@/lib/settings';

// Initialize engines
const maxAutoEngine = new MaxAutoEngine();
const updateChecker = new UpdateChecker();

// Initialize on install/startup
chrome.runtime.onInstalled.addListener(async () => {
  console.log('Extension installed/updated');
  
  // Initialize settings
  await settingsManager.loadSettings();
  
  // Initialize engines
  await maxAutoEngine.initialize();
  await updateChecker.initialize();
  
  // Create context menus
  chrome.contextMenus.create({
    id: 'scan-page',
    title: 'Scan this page for gaming PCs',
    contexts: ['page']
  });
});

chrome.runtime.onStartup.addListener(async () => {
  console.log('Browser started');
  await maxAutoEngine.initialize();
  await updateChecker.initialize();
});

// Handle messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received:', request.action);
  
  switch (request.action) {
    case 'MAX_AUTO_ENABLE':
      maxAutoEngine.enable();
      sendResponse({ success: true });
      break;
      
    case 'MAX_AUTO_DISABLE':
      maxAutoEngine.disable();
      sendResponse({ success: true });
      break;
      
    case 'SETTINGS_UPDATED':
      handleSettingsUpdate(request.settings);
      sendResponse({ success: true });
      break;
      
    case 'CHECK_FOR_UPDATES':
      updateChecker.checkNow();
      sendResponse({ success: true });
      break;
      
    case 'SCAN_CURRENT_TAB':
      scanCurrentTab();
      sendResponse({ success: true });
      break;
      
    case 'STORE_SCAN_RESULTS':
      storeScanResults(request.listings);
      sendResponse({ success: true });
      break;
      
    case 'openDashboard':
      chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
      sendResponse({ success: true });
      break;
      
    case 'openSettings':
      chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html#/settings') });
      sendResponse({ success: true });
      break;
      
    case 'GENERATE_REPORT':
      generateReport();
      sendResponse({ success: true });
      break;
      
    default:
      console.warn('Unknown action:', request.action);
  }
  
  return false; // Synchronous response
});

// Handle settings updates
async function handleSettingsUpdate(settings: any) {
  console.log('Settings updated:', settings);
  
  // Update automation engine
  if (settings.automation) {
    if (settings.automation.enabled) {
      await maxAutoEngine.enable();
    } else {
      await maxAutoEngine.disable();
    }
    
    // Update scan interval
    if (settings.automation.scanInterval) {
      chrome.alarms.clear('auto-scan');
      chrome.alarms.create('auto-scan', {
        periodInMinutes: settings.automation.scanInterval
      });
    }
  }
}

// Scan current tab
async function scanCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab?.id) return;
  
  // Inject scanner overlay
  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'INJECT_SCANNER' });
  } catch (error) {
    console.error('Failed to inject scanner:', error);
    
    // Try injecting content script first
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['js/content-scanner.js']
    });
    
    // Retry
    await chrome.tabs.sendMessage(tab.id, { action: 'INJECT_SCANNER' });
  }
}

// Store scan results
async function storeScanResults(listings: any[]) {
  const { scannedListings = [] } = await chrome.storage.local.get(['scannedListings']);
  
  // Deduplicate by ID
  const existingIds = new Set(scannedListings.map((l: any) => l.id));
  const newListings = listings.filter(l => !existingIds.has(l.id));
  
  if (newListings.length > 0) {
    const updated = [...newListings, ...scannedListings].slice(0, 1000);
    await chrome.storage.local.set({ 
      scannedListings: updated,
      lastScanTime: new Date().toISOString()
    });
    
    // Update recent activity
    const { recentActivity = [] } = await chrome.storage.local.get(['recentActivity']);
    const scanActivity = {
      id: `scan-${Date.now()}`,
      type: 'scan',
      title: `Found ${newListings.length} new gaming PCs`,
      time: new Date().toISOString(),
      platform: new URL(listings[0]?.link || 'https://unknown').hostname
    };
    
    await chrome.storage.local.set({
      recentActivity: [scanActivity, ...recentActivity].slice(0, 50)
    });
    
    // Show notification
    if (newListings.length > 0) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
        title: 'New Gaming PCs Found!',
        message: `Found ${newListings.length} new listings`
      });
    }
  }
}

// Generate analytics report
async function generateReport() {
  const data = await chrome.storage.local.get([
    'deals',
    'scannedListings',
    'recentActivity'
  ]);
  
  const report = {
    generated: new Date().toISOString(),
    summary: {
      totalScanned: data.scannedListings?.length || 0,
      totalDeals: data.deals?.length || 0,
      activeDeals: data.deals?.filter((d: any) => 
        ['contacted', 'negotiating', 'meeting_scheduled'].includes(d.status)
      ).length || 0,
      completedDeals: data.deals?.filter((d: any) => 
        d.status === 'completed'
      ).length || 0
    },
    revenue: calculateRevenue(data.deals || []),
    topPlatforms: getTopPlatforms(data.scannedListings || []),
    activityTimeline: data.recentActivity?.slice(0, 30) || []
  };
  
  // Create downloadable report
  const blob = new Blob([JSON.stringify(report, null, 2)], { 
    type: 'application/json' 
  });
  const url = URL.createObjectURL(blob);
  
  chrome.downloads.download({
    url,
    filename: `pc-arbitrage-report-${new Date().toISOString().split('T')[0]}.json`,
    saveAs: true
  });
}

function calculateRevenue(deals: any[]) {
  const completed = deals.filter(d => d.status === 'completed');
  return {
    total: completed.reduce((sum, d) => sum + (d.soldPrice - d.purchasePrice), 0),
    average: completed.length > 0 
      ? completed.reduce((sum, d) => sum + (d.soldPrice - d.purchasePrice), 0) / completed.length
      : 0,
    count: completed.length
  };
}

function getTopPlatforms(listings: any[]) {
  const platforms: Record<string, number> = {};
  
  listings.forEach(listing => {
    const platform = listing.platform || 'unknown';
    platforms[platform] = (platforms[platform] || 0) + 1;
  });
  
  return Object.entries(platforms)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([platform, count]) => ({ platform, count }));
}

// Context menu handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'scan-page' && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { action: 'INJECT_SCANNER' });
  }
});

// Keep service worker alive
setInterval(() => {
  // Ping to keep alive
}, 20000);