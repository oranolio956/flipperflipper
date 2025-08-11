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