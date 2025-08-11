// Background Service Worker for Gaming PC Arbitrage Extension
// Version 3.2.0 - Production Build

// Initialize on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('[Background] Extension installed:', details.reason);
  
  // Set default settings
  const defaultSettings = {
    version: '3.2.0',
    automation: {
      enabled: false,
      scanInterval: 30,
      maxTabs: 3
    },
    notifications: {
      enabled: true,
      sound: false
    }
  };
  
  const { settings } = await chrome.storage.local.get(['settings']);
  if (!settings) {
    await chrome.storage.local.set({ settings: defaultSettings });
  }
  
  // Create context menu
  chrome.contextMenus.create({
    id: 'scan-page',
    title: 'Scan this page for deals',
    contexts: ['page']
  });
});

// Handle messages from UI and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Background] Message received:', request.action);
  
  switch (request.action) {
    case 'OPEN_DASHBOARD':
      chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
      break;
      
    case 'SCAN_CURRENT_TAB':
      handleScanCurrentTab();
      break;
      
    case 'GET_VERSION':
      sendResponse({ version: chrome.runtime.getManifest().version });
      break;
      
    case 'STORE_SCAN_RESULTS':
      handleStoreScanResults(request.data).then(sendResponse);
      return true; // Will respond asynchronously
      
    default:
      console.warn('[Background] Unknown action:', request.action);
  }
});

// Context menu handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'scan-page' && tab?.id) {
    injectScanner(tab.id);
  }
});

// Scan current tab
async function handleScanCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    await injectScanner(tab.id);
  }
}

// Inject scanner into tab
async function injectScanner(tabId: number) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['js/scanner.js']
    });
    
    chrome.tabs.sendMessage(tabId, { action: 'START_SCAN' });
  } catch (error) {
    console.error('[Background] Failed to inject scanner:', error);
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon-48.png',
      title: 'Scan Failed',
      message: 'Unable to scan this page. Make sure you\'re on a supported marketplace.'
    });
  }
}

// Store scan results
async function handleStoreScanResults(data: any) {
  try {
    const { listings = [] } = await chrome.storage.local.get(['listings']);
    
    // Deduplicate
    const existingIds = new Set(listings.map((l: any) => l.id));
    const newListings = data.listings.filter((l: any) => !existingIds.has(l.id));
    
    if (newListings.length > 0) {
      const updated = [...newListings, ...listings].slice(0, 1000); // Keep last 1000
      await chrome.storage.local.set({ listings: updated });
      
      // Show notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon-48.png',
        title: 'Scan Complete',
        message: `Found ${newListings.length} new listings`
      });
    }
    
    return { success: true, newCount: newListings.length };
  } catch (error) {
    console.error('[Background] Failed to store results:', error);
    return { success: false, error: String(error) };
  }
}

// Keep service worker alive
setInterval(() => {
  chrome.storage.local.get(['ping'], () => {
    // Just accessing storage keeps the service worker alive
  });
}, 20000);

console.log('[Background] Service worker initialized v3.2.0');