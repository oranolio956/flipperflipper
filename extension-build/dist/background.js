// Background Service Worker
console.log('Gaming PC Arbitrage Extension - Background Service Worker Started');

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed');
  
  // Initialize default settings
  chrome.storage.local.set({
    settings: {
      theme: 'dark',
      notifications: true,
      autoScan: false
    }
  });
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request);
  
  if (request.type === 'PARSE_PAGE') {
    // Handle page parsing
    sendResponse({ success: true, data: 'Page parsed' });
  }
  
  return true; // Will respond asynchronously
});

// Create context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scan-listing',
    title: 'Scan this listing',
    contexts: ['page'],
    documentUrlPatterns: [
      'https://www.facebook.com/marketplace/*',
      'https://*.craigslist.org/*',
      'https://offerup.com/*'
    ]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'scan-listing') {
    chrome.tabs.sendMessage(tab.id, { action: 'scan' });
  }
});