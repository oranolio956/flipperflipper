/**
 * Background Service Worker
 * Handles extension lifecycle, message routing, and background tasks
 */

import { performanceTracker } from '@arbitrage/core';

// Message types
interface ExtensionMessage {
  type: string;
  payload?: any;
  tabId?: number;
}

// Initialize extension on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('Extension installed:', details.reason);
  
  if (details.reason === 'install') {
    // Set default settings
    await chrome.storage.local.set({
      settings: {
        version: '1.0.0',
        location: {
          zipCode: '',
          maxDistance: 25,
          preferredMeetingSpots: []
        },
        pricing: {
          targetROI: 25,
          minDealValue: 500,
          includeShipping: true,
          includeFees: true
        },
        notifications: {
          enabled: true,
          priceDrops: true,
          newListings: true,
          messages: true,
          dealUpdates: true
        }
      }
    });
    
    // Open welcome page
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html#/welcome')
    });
  }
});

// Message handler
chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
  console.log('Background received message:', message.type);
  
  performanceTracker.measure('message-handler', 'api', async () => {
    try {
      switch (message.type) {
        case 'ANALYZE_LISTING':
          handleAnalyzeListing(message.payload, sendResponse);
          return true; // Will respond asynchronously
          
        case 'SAVE_DEAL':
          handleSaveDeal(message.payload, sendResponse);
          return true;
          
        case 'GET_SETTINGS':
          handleGetSettings(sendResponse);
          return true;
          
        case 'UPDATE_SETTINGS':
          handleUpdateSettings(message.payload, sendResponse);
          return true;
          
        case 'OPEN_DASHBOARD':
          chrome.tabs.create({
            url: chrome.runtime.getURL('dashboard.html')
          });
          sendResponse({ success: true });
          break;
          
        case 'REQUEST_PERMISSIONS':
          handlePermissionRequest(message.payload, sendResponse);
          return true;
          
        default:
          sendResponse({ error: 'Unknown message type' });
      }
    } catch (error) {
      console.error('Message handler error:', error);
      sendResponse({ error: error.message });
    }
  });
  
  return false; // Synchronous response
});

// Command handlers
chrome.commands.onCommand.addListener(async (command) => {
  console.log('Command:', command);
  
  switch (command) {
    case 'analyze-listing':
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: 'TRIGGER_ANALYSIS' });
      }
      break;
      
    case 'track-deal':
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (activeTab?.id) {
        chrome.tabs.sendMessage(activeTab.id, { type: 'TRIGGER_TRACK_DEAL' });
      }
      break;
      
    case 'open-dashboard':
      chrome.tabs.create({
        url: chrome.runtime.getURL('dashboard.html')
      });
      break;
  }
});

// Alarm handlers for scheduled tasks
chrome.alarms.onAlarm.addListener(async (alarm) => {
  console.log('Alarm fired:', alarm.name);
  
  if (alarm.name.startsWith('followup-')) {
    await handleFollowupReminder(alarm.name);
  } else if (alarm.name === 'backup') {
    await performBackup();
  } else if (alarm.name === 'cleanup') {
    await performDataCleanup();
  }
});

// Helper functions
async function handleAnalyzeListing(payload: any, sendResponse: Function) {
  try {
    // Placeholder - would analyze listing
    const result = {
      fmv: 1200,
      roi: 25,
      risk: { score: 30, level: 'low' }
    };
    sendResponse({ success: true, result });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleSaveDeal(payload: any, sendResponse: Function) {
  try {
    const { deals = [] } = await chrome.storage.local.get('deals');
    const newDeal = {
      ...payload,
      id: `deal-${Date.now()}`,
      metadata: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        source: 'manual',
        version: 1
      }
    };
    
    deals.push(newDeal);
    await chrome.storage.local.set({ deals });
    
    sendResponse({ success: true, deal: newDeal });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleGetSettings(sendResponse: Function) {
  try {
    const { settings } = await chrome.storage.local.get('settings');
    sendResponse({ success: true, settings });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleUpdateSettings(payload: any, sendResponse: Function) {
  try {
    const { settings } = await chrome.storage.local.get('settings');
    const updatedSettings = { ...settings, ...payload };
    await chrome.storage.local.set({ settings: updatedSettings });
    sendResponse({ success: true, settings: updatedSettings });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handlePermissionRequest(payload: any, sendResponse: Function) {
  try {
    const { permissions, origins } = payload;
    const granted = await chrome.permissions.request({
      permissions: permissions || [],
      origins: origins || []
    });
    sendResponse({ success: true, granted });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleFollowupReminder(alarmName: string) {
  const dealId = alarmName.replace('followup-', '');
  
  // Show notification
  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
    title: 'Follow-up Reminder',
    message: `Time to follow up on deal ${dealId}`,
    buttons: [
      { title: 'View Deal' },
      { title: 'Snooze' }
    ]
  });
}

async function performBackup() {
  try {
    console.log('Performing scheduled backup...');
    // Placeholder - would implement backup logic
  } catch (error) {
    console.error('Backup failed:', error);
  }
}

async function performDataCleanup() {
  try {
    console.log('Performing data cleanup...');
    // Remove old data based on retention settings
    const { settings } = await chrome.storage.local.get('settings');
    const retentionDays = settings?.dataRetention?.dealHistory || 90;
    
    // Placeholder - would implement cleanup logic
  } catch (error) {
    console.error('Cleanup failed:', error);
  }
}

// Set up periodic tasks
chrome.runtime.onStartup.addListener(() => {
  // Schedule daily cleanup
  chrome.alarms.create('cleanup', {
    periodInMinutes: 24 * 60 // Daily
  });
  
  // Schedule weekly backup
  chrome.alarms.create('backup', {
    periodInMinutes: 7 * 24 * 60 // Weekly
  });
});

// Export for testing
export { handleAnalyzeListing, handleSaveDeal };