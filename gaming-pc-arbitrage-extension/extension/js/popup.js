/**
 * Popup Script
 * Handles popup UI interactions and settings management
 */

let currentSettings = null;
let recentDeals = [];

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await loadRecentDeals();
  await updateStats();
  setupEventListeners();
});

// Load settings from storage
async function loadSettings() {
  try {
    const result = await chrome.storage.local.get('settings');
    currentSettings = result.settings || getDefaultSettings();
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
      searchRadius: 25
    },
    financial: {
      minRoi: 25,
      maxBudget: 2000
    },
    notifications: {
      deals: true,
      priceDrops: false
    }
  };
}

// Apply settings to UI
function applySettingsToUI() {
  document.getElementById('zip-code').value = currentSettings.geography.zipCode || '';
  document.getElementById('search-radius').value = currentSettings.geography.searchRadius || 25;
  document.getElementById('min-roi').value = currentSettings.financial.minRoi || 25;
  document.getElementById('max-budget').value = currentSettings.financial.maxBudget || 2000;
  document.getElementById('notify-deals').checked = currentSettings.notifications.deals !== false;
  document.getElementById('notify-price-drops').checked = currentSettings.notifications.priceDrops === true;
}

// Load recent deals
async function loadRecentDeals() {
  try {
    const result = await chrome.storage.local.get(['deals', 'listings']);
    const deals = result.deals || [];
    const listings = result.listings || {};
    
    // Combine deal data with listing data
    recentDeals = deals.map(deal => ({
      ...deal,
      listing: listings[deal.listingId] || deal.listing
    })).filter(deal => deal.listing);
    
    // Sort by most recent
    recentDeals.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
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
  
  dealsList.innerHTML = recentDeals.slice(0, 5).map(deal => {
    const roi = deal.analysis?.roi || ((deal.analysis?.fmv - deal.listing.price) / deal.listing.price * 100);
    const profit = deal.analysis?.profit || (deal.analysis?.fmv - deal.listing.price);
    
    return `
      <div class="deal-item" data-deal-id="${deal.id}">
        <div class="deal-header">
          <h4>${truncateText(deal.listing.title, 50)}</h4>
          <span class="deal-platform">${deal.listing.platform}</span>
        </div>
        <div class="deal-stats">
          <span class="deal-price">$${deal.listing.price}</span>
          <span class="deal-roi ${roi > 25 ? 'good' : roi > 15 ? 'moderate' : 'poor'}">
            ${roi.toFixed(1)}% ROI
          </span>
          <span class="deal-profit ${profit > 0 ? 'positive' : 'negative'}">
            $${profit.toFixed(0)}
          </span>
        </div>
        <div class="deal-actions">
          <button class="mini-btn" onclick="viewDeal('${deal.id}')">View</button>
          <button class="mini-btn" onclick="openListing('${deal.listing.url}')">Open</button>
        </div>
      </div>
    `;
  }).join('');
}

// Update statistics
async function updateStats() {
  try {
    const result = await chrome.storage.local.get(['deals']);
    const deals = result.deals || [];
    
    // Calculate stats
    const activeDeals = deals.filter(d => d.stage !== 'sold' && d.stage !== 'lost').length;
    const soldDeals = deals.filter(d => d.stage === 'sold');
    
    const totalProfit = soldDeals.reduce((sum, deal) => {
      const profit = (deal.salePrice || 0) - (deal.purchasePrice || deal.listing.price);
      return sum + profit;
    }, 0);
    
    const avgRoi = soldDeals.length > 0
      ? soldDeals.reduce((sum, deal) => {
          const cost = deal.purchasePrice || deal.listing.price;
          const roi = ((deal.salePrice || 0) - cost) / cost * 100;
          return sum + roi;
        }, 0) / soldDeals.length
      : 0;
    
    // Update UI
    document.getElementById('active-deals').textContent = activeDeals;
    document.getElementById('total-profit').textContent = `$${totalProfit.toLocaleString()}`;
    document.getElementById('avg-roi').textContent = `${avgRoi.toFixed(1)}%`;
    
    // Add color classes based on values
    const profitElement = document.getElementById('total-profit');
    profitElement.classList.toggle('positive', totalProfit > 0);
    profitElement.classList.toggle('negative', totalProfit < 0);
  } catch (error) {
    console.error('Failed to update stats:', error);
  }
}

// Setup event listeners
function setupEventListeners() {
  // Analyze page button
  document.getElementById('analyze-page').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Check if on a supported marketplace
    const supportedSites = ['facebook.com', 'craigslist.org', 'offerup.com'];
    const isSupported = supportedSites.some(site => tab.url.includes(site));
    
    if (!isSupported) {
      showNotification('Please navigate to a marketplace listing (Facebook, Craigslist, or OfferUp)', 'error');
      return;
    }
    
    // Send message to content script
    chrome.tabs.sendMessage(tab.id, { type: 'TRIGGER_ANALYSIS' }, response => {
      if (chrome.runtime.lastError) {
        showNotification('Unable to analyze this page. Try refreshing.', 'error');
      } else {
        window.close();
      }
    });
  });
  
  // Open dashboard button
  document.getElementById('open-dashboard').addEventListener('click', () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html')
    });
    window.close();
  });
  
  // Photo capture button
  document.getElementById('photo-capture').addEventListener('click', () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('photo-capture.html')
    });
    window.close();
  });
  
  // Bulk scanner button
  document.getElementById('bulk-scan').addEventListener('click', () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html#bulk-scanner')
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
  document.getElementById('save-settings').addEventListener('click', async () => {
    await saveSettings();
  });
}

// Save settings
async function saveSettings() {
  const newSettings = {
    ...currentSettings,
    geography: {
      zipCode: document.getElementById('zip-code').value,
      searchRadius: parseInt(document.getElementById('search-radius').value)
    },
    financial: {
      minRoi: parseInt(document.getElementById('min-roi').value),
      maxBudget: parseInt(document.getElementById('max-budget').value)
    },
    notifications: {
      deals: document.getElementById('notify-deals').checked,
      priceDrops: document.getElementById('notify-price-drops').checked
    }
  };
  
  try {
    await chrome.storage.local.set({ settings: newSettings });
    
    // Send message to background script to update settings
    chrome.runtime.sendMessage({
      type: 'UPDATE_SETTINGS',
      payload: { settings: newSettings }
    });
    
    currentSettings = newSettings;
    showNotification('Settings saved successfully!', 'success');
    
    // Close settings panel
    setTimeout(() => {
      document.getElementById('settings-panel').style.display = 'none';
    }, 1000);
  } catch (error) {
    console.error('Failed to save settings:', error);
    showNotification('Failed to save settings', 'error');
  }
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => notification.classList.add('show'), 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Helper functions
function truncateText(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Global functions for deal actions
window.viewDeal = function(dealId) {
  chrome.tabs.create({
    url: `${chrome.runtime.getURL('dashboard.html')}#deal/${dealId}`
  });
  window.close();
};

window.openListing = function(url) {
  chrome.tabs.create({ url });
  window.close();
};

// Listen for deal updates
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'DEAL_SAVED') {
    loadRecentDeals();
    updateStats();
  }
});

// Refresh stats periodically
setInterval(() => {
  updateStats();
}, 30000); // Every 30 seconds