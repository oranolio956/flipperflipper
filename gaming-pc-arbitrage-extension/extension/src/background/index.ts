/**
 * Background Service Worker
 * Handles extension lifecycle, alarms, and automation
 */

import { automationHandler } from './automation';
import { maxAutoEngine } from './maxAutoEngine';
import { updateChecker } from './updateChecker';

// Initialize automation on install/startup
chrome.runtime.onInstalled.addListener(async () => {
  console.log('Extension installed/updated');
  await automationHandler.initialize();
});

chrome.runtime.onStartup.addListener(async () => {
  console.log('Browser started');
  await automationHandler.initialize();
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open dashboard in new tab
  chrome.tabs.create({
    url: chrome.runtime.getURL('dashboard.html')
  });
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openDashboard') {
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html')
    });
    sendResponse({ success: true });
    return true;
  }

  if (request.action === 'scanPage' && sender.tab?.id) {
    // Inject scanner into current tab
    chrome.scripting.executeScript({
      target: { tabId: sender.tab.id },
      files: ['js/content-scanner.js']
    }).then(() => {
      sendResponse({ success: true });
    }).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }

  // Max Auto Engine controls
  if (request.action === 'MAX_AUTO_ENABLE') {
    maxAutoEngine.enable().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'MAX_AUTO_DISABLE') {
    maxAutoEngine.disable().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'MAX_AUTO_GET_STATUS') {
    maxAutoEngine.getStatus().then((status) => {
      sendResponse({ success: true, status });
    });
    return true;
  }

  if (request.action === 'MAX_AUTO_ADD_SEARCH') {
    maxAutoEngine.addSearch(request.search).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'MAX_AUTO_TEST_SCAN') {
    maxAutoEngine.testScan(request.searchId).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  // Store scan results from content scripts
  if (request.action === 'STORE_SCAN_RESULTS') {
    chrome.storage.local.get(['scannedListings', 'scanHistory'], (result) => {
      const scannedListings = result.scannedListings || [];
      const scanHistory = result.scanHistory || [];
      
      // Add new listings
      const newListings = request.listings.map((listing: any) => ({
        ...listing,
        scanId: request.scanId,
        searchId: request.searchId,
        timestamp: new Date().toISOString()
      }));
      
      // Merge with existing, remove duplicates
      const allListings = [...newListings, ...scannedListings];
      const uniqueListings = allListings.filter((listing, index, self) =>
        index === self.findIndex((l) => l.url === listing.url)
      );
      
      // Keep only last 500 listings
      const trimmedListings = uniqueListings.slice(0, 500);
      
      // Update scan history
      scanHistory.unshift({
        scanId: request.scanId,
        searchId: request.searchId,
        timestamp: new Date().toISOString(),
        resultsCount: newListings.length,
        platform: request.listings[0]?.platform || 'unknown'
      });
      
      // Save to storage
      chrome.storage.local.set({
        scannedListings: trimmedListings,
        scanHistory: scanHistory.slice(0, 100),
        lastScanTime: new Date().toISOString()
      }, () => {
        sendResponse({ success: true, stored: newListings.length });
      });
    });
    return true;
  }
  
  // Handle scan page requests from UI
  if (request.action === 'SCAN_PAGE') {
    // Forward to the active tab's content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id!, request, (response) => {
          sendResponse(response || { success: false, error: 'No response from content script' });
        });
      } else {
        sendResponse({ success: false, error: 'No active tab' });
      }
    });
    return true;
  }
  
  // Open dashboard
  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
    sendResponse({ success: true });
    return true;
  }
  
  // Open settings
  if (request.action === 'openSettings') {
    chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html#/settings') });
    sendResponse({ success: true });
    return true;
  }

  // Update checker controls
  if (request.action === 'GET_UPDATE_STATUS') {
    updateChecker.getStatus().then((status) => {
      sendResponse({ success: true, status });
    });
    return true;
  }

  if (request.action === 'CHECK_FOR_UPDATES') {
    updateChecker.checkForUpdates().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'APPLY_UPDATE') {
    updateChecker.applyUpdate().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  return false;
});

// Keep service worker alive
setInterval(() => {
  chrome.storage.local.get(['keepAlive'], () => {
    // Just accessing storage keeps the service worker alive
  });
}, 20000);