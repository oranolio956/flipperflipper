/**
 * Popup Script
 * Handles popup UI interactions and settings management
 */

// State
let currentSettings = null;
let recentDeals = [];

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await loadRecentDeals();
  await updateStats();
  setupEventListeners();
});

// Load settings from storage
async function loadSettings() {
  try {
    const { settings } = await chrome.storage.local.get('settings');
    currentSettings = settings || getDefaultSettings();
    applySettingsToUI();
  } catch (error) {
    console.error('Failed to load settings:', error);
    currentSettings = getDefaultSettings();
  }
}

// Get default settings
function getDefaultSettings() {
  return {
    geography: {
      zipCode: '',
      maxDistance: 25
    },
    financial: {
      targetROI: 25,
      minDealValue: 500
    },
    notifications: {
      priceDrops: true,
      newListings: true,
      dealUpdates: true
    }
  };
}

// Apply settings to UI
function applySettingsToUI() {
  // Location
  document.getElementById('zip-code').value = currentSettings.geography?.zipCode || '';
  document.getElementById('max-distance').value = currentSettings.geography?.maxDistance || 25;
  
  // Financial
  document.getElementById('target-roi').value = currentSettings.financial?.targetROI || 25;
  document.getElementById('min-deal-value').value = currentSettings.financial?.minDealValue || 500;
  
  // Notifications
  document.getElementById('notify-price-drops').checked = currentSettings.notifications?.priceDrops !== false;
  document.getElementById('notify-new-listings').checked = currentSettings.notifications?.newListings !== false;
  document.getElementById('notify-deal-updates').checked = currentSettings.notifications?.dealUpdates !== false;
}

// Load recent deals
async function loadRecentDeals() {
  try {
    const { deals } = await chrome.storage.local.get('deals');
    recentDeals = (deals || [])
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, 5);
    
    displayRecentDeals();
  } catch (error) {
    console.error('Failed to load deals:', error);
  }
}

// Display recent deals
function displayRecentDeals() {
  const dealsList = document.getElementById('deals-list');
  
  if (recentDeals.length === 0) {
    dealsList.innerHTML = `
      <div class="empty-state">
        <p>No deals yet. Start by analyzing a listing!</p>
      </div>
    `;
    return;
  }
  
  dealsList.innerHTML = recentDeals.map(deal => {
    const roi = deal.roi || 0;
    const roiClass = roi > 25 ? 'good' : roi > 15 ? 'moderate' : 'poor';
    
    return `
      <div class="deal-item" data-deal-id="${deal.id}">
        <div class="deal-info">
          <h4>${truncateText(deal.title || 'Untitled', 40)}</h4>
          <p class="deal-meta">
            <span class="price">$${deal.askingPrice || 0}</span>
            <span class="roi ${roiClass}">${roi.toFixed(1)}% ROI</span>
          </p>
        </div>
        <button class="view-btn" data-deal-id="${deal.id}">View</button>
      </div>
    `;
  }).join('');
  
  // Add click handlers for view buttons
  dealsList.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const dealId = e.target.dataset.dealId;
      chrome.tabs.create({
        url: chrome.runtime.getURL(`dashboard.html#/deals/${dealId}`)
      });
    });
  });
}

// Update statistics
async function updateStats() {
  try {
    const { deals } = await chrome.storage.local.get('deals');
    const allDeals = deals || [];
    
    // Active deals (not sold or passed)
    const activeDeals = allDeals.filter(d => 
      d.status !== 'sold' && d.status !== 'passed'
    ).length;
    
    // Total profit (sold deals only)
    const totalProfit = allDeals
      .filter(d => d.status === 'sold' && d.profit)
      .reduce((sum, d) => sum + d.profit, 0);
    
    // Average ROI
    const dealsWithROI = allDeals.filter(d => d.roi);
    const avgROI = dealsWithROI.length > 0
      ? dealsWithROI.reduce((sum, d) => sum + d.roi, 0) / dealsWithROI.length
      : 0;
    
    // Update UI
    document.getElementById('active-deals').textContent = activeDeals;
    document.getElementById('total-profit').textContent = `$${totalProfit.toLocaleString()}`;
    document.getElementById('avg-roi').textContent = `${avgROI.toFixed(1)}%`;
  } catch (error) {
    console.error('Failed to update stats:', error);
  }
}

// Setup event listeners
function setupEventListeners() {
  // Analyze page button
  document.getElementById('analyze-page').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    // Check if on supported site
    const supportedSites = [
      'facebook.com/marketplace',
      'craigslist.org',
      'offerup.com'
    ];
    
    const isSupported = supportedSites.some(site => tab.url.includes(site));
    
    if (!isSupported) {
      showNotification('This site is not supported. Try Facebook Marketplace, Craigslist, or OfferUp.', 'error');
      return;
    }
    
    // Send message to content script
    chrome.tabs.sendMessage(tab.id, { type: 'TRIGGER_ANALYSIS' });
    window.close();
  });
  
  // Open dashboard button
  document.getElementById('open-dashboard').addEventListener('click', () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html')
    });
    window.close();
  });
  
  // Settings button
  document.getElementById('settings-btn').addEventListener('click', () => {
    document.getElementById('settings-panel').style.display = 'block';
  });
  
  // Close settings button
  document.getElementById('close-settings').addEventListener('click', () => {
    document.getElementById('settings-panel').style.display = 'none';
  });
  
  // Save settings button
  document.getElementById('save-settings').addEventListener('click', saveSettings);
}

// Save settings
async function saveSettings() {
  try {
    // Gather settings from UI
    const newSettings = {
      ...currentSettings,
      geography: {
        zipCode: document.getElementById('zip-code').value,
        maxDistance: parseInt(document.getElementById('max-distance').value) || 25
      },
      financial: {
        targetROI: parseInt(document.getElementById('target-roi').value) || 25,
        minDealValue: parseInt(document.getElementById('min-deal-value').value) || 500
      },
      notifications: {
        priceDrops: document.getElementById('notify-price-drops').checked,
        newListings: document.getElementById('notify-new-listings').checked,
        dealUpdates: document.getElementById('notify-deal-updates').checked
      }
    };
    
    // Save to storage
    await chrome.storage.local.set({ settings: newSettings });
    currentSettings = newSettings;
    
    // Notify background script
    chrome.runtime.sendMessage({
      type: 'UPDATE_SETTINGS',
      payload: { settings: newSettings }
    });
    
    showNotification('Settings saved!', 'success');
    
    // Close settings panel after delay
    setTimeout(() => {
      document.getElementById('settings-panel').style.display = 'none';
    }, 1500);
  } catch (error) {
    console.error('Failed to save settings:', error);
    showNotification('Failed to save settings', 'error');
  }
}

// Show notification
function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Add to notifications section
  const notificationsSection = document.getElementById('notifications-section');
  const notificationsList = document.getElementById('notifications-list');
  
  notificationsSection.style.display = 'block';
  notificationsList.appendChild(notification);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => {
      notification.remove();
      if (notificationsList.children.length === 0) {
        notificationsSection.style.display = 'none';
      }
    }, 300);
  }, 3000);
}

// Utility: Truncate text
function truncateText(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

// Listen for messages from background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'DEAL_SAVED') {
    // Reload deals when a new one is saved
    loadRecentDeals();
    updateStats();
  }
});

// Auto-refresh stats every 30 seconds while popup is open
setInterval(() => {
  updateStats();
}, 30000);