/**
 * Background Service Worker
 * Handles extension lifecycle, message routing, and background tasks
 */

import { onMessage, type Message } from '../lib/messages';
import { db } from '../lib/db';
import { 
  FMVCalculator, 
  ROICalculator, 
  FacebookMarketplaceParser,
  CraigslistParser,
  OfferUpParser,
  RiskEngine,
  DEFAULT_SETTINGS
} from '@arbitrage/core';

// Initialize services
const fmvCalculator = new FMVCalculator(DEFAULT_SETTINGS);
const roiCalculator = new ROICalculator(DEFAULT_SETTINGS);
const riskEngine = new RiskEngine(DEFAULT_SETTINGS);

const parsers = {
  facebook: new FacebookMarketplaceParser(),
  craigslist: new CraigslistParser(),
  offerup: new OfferUpParser()
};

// Initialize extension on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('Extension installed:', details.reason);
  
  if (details.reason === 'install') {
    // Set default settings
    await chrome.storage.local.set({
      settings: DEFAULT_SETTINGS,
      installDate: new Date().toISOString(),
      version: chrome.runtime.getManifest().version
    });
    
    // Open onboarding page
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html#/onboarding')
    });
  } else if (details.reason === 'update') {
    // Handle updates
    const previousVersion = details.previousVersion;
    console.log(`Updated from ${previousVersion} to ${chrome.runtime.getManifest().version}`);
  }
});

// Message handler
onMessage(async (message: Message, sender) => {
  console.log('Background received message:', message.type);
  
  switch (message.type) {
    case 'PARSE_LISTING': {
      try {
        const { platform, html, url } = message.payload;
        const parser = parsers[platform];
        
        if (!parser) {
          return { success: false, error: 'Unknown platform' };
        }
        
        // Create DOM from HTML
        const dom = new DOMParser().parseFromString(html, 'text/html');
        const listing = parser.extractListing(dom);
        
        if (!listing) {
          return { success: false, error: 'Failed to parse listing' };
        }
        
        // Enhance listing with URL
        listing.url = url;
        
        return {
          type: 'LISTING_PARSED',
          payload: { listing, success: true }
        };
      } catch (error) {
        return {
          type: 'LISTING_PARSED',
          payload: { 
            success: false, 
            error: error instanceof Error ? error.message : 'Parse error'
          }
        };
      }
    }
    
    case 'CALCULATE_FMV': {
      try {
        const { listing } = message.payload;
        const fmvResult = fmvCalculator.calculate(listing);
        const roiResult = roiCalculator.calculate(listing, fmvResult);
        const riskResult = riskEngine.assessRisk(listing);
        
        // Store in database
        const savedListing = await db.listings.add({
          ...listing,
          id: `${listing.platform}_${Date.now()}`,
          savedAt: new Date(),
          analysis: {
            fmv: fmvResult.total,
            componentValue: fmvResult.total,
            profitPotential: roiResult.netProfit,
            roi: roiResult.roi,
            margin: roiResult.profitMargin,
            dealScore: roiResult.dealScore,
            confidence: fmvResult.confidence
          },
          risks: {
            score: riskResult.score,
            flags: riskResult.flags,
            stolen: { probability: 0, indicators: [] },
            scam: { probability: 0, patterns: [] },
            technical: { issues: [], severity: 'low' }
          }
        });
        
        return {
          type: 'FMV_CALCULATED',
          payload: {
            fmv: fmvResult.total,
            confidence: fmvResult.confidence,
            breakdown: fmvResult.componentBreakdown.map(c => ({
              component: c.name,
              value: c.adjustedValue
            }))
          }
        };
      } catch (error) {
        return {
          type: 'ERROR',
          payload: {
            message: 'FMV calculation failed',
            details: error instanceof Error ? error.message : 'Unknown error'
          }
        };
      }
    }
    
    case 'SAVE_DEAL': {
      try {
        const { listing, fmv, notes } = message.payload;
        
        const dealId = `deal_${Date.now()}`;
        await db.deals.add({
          id: dealId,
          listingId: listing.id,
          listing,
          platform: listing.platform,
          status: 'watching',
          askingPrice: listing.price,
          offers: [],
          messages: [],
          metadata: {
            createdAt: new Date(),
            updatedAt: new Date(),
            source: 'manual',
            version: 1,
            notes
          }
        });
        
        // Track analytics event
        await db.analytics.add({
          id: `event_${Date.now()}`,
          name: 'deal_created',
          category: 'deals',
          timestamp: new Date(),
          properties: {
            platform: listing.platform,
            askingPrice: listing.price,
            fmv,
            roi: ((fmv - listing.price) / listing.price) * 100
          }
        });
        
        return {
          type: 'DEAL_SAVED',
          payload: { dealId, success: true }
        };
      } catch (error) {
        return {
          type: 'DEAL_SAVED',
          payload: { 
            dealId: '', 
            success: false,
            error: error instanceof Error ? error.message : 'Save failed'
          }
        };
      }
    }
    
    case 'GET_SETTINGS': {
      const { settings } = await chrome.storage.local.get('settings');
      return {
        type: 'SETTINGS_RETRIEVED',
        payload: { settings: settings || DEFAULT_SETTINGS }
      };
    }
    
    case 'UPDATE_SETTINGS': {
      const { settings } = message.payload;
      await chrome.storage.local.set({ settings });
      
      // Reinitialize services with new settings
      fmvCalculator.updateSettings(settings);
      roiCalculator.settings = settings;
      riskEngine.settings = settings;
      
      return {
        type: 'SETTINGS_UPDATED',
        payload: { success: true }
      };
    }
    
    case 'SHOW_NOTIFICATION': {
      const { title, message: body, type, dealId } = message.payload;
      
      // Create notification
      const notificationId = await chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
        title,
        message: body,
        priority: type === 'error' ? 2 : 1,
        requireInteraction: type === 'success' && dealId
      });
      
      // Handle click
      if (dealId) {
        chrome.notifications.onClicked.addListener((id) => {
          if (id === notificationId) {
            chrome.tabs.create({
              url: chrome.runtime.getURL(`dashboard.html#/deals/${dealId}`)
            });
          }
        });
      }
      
      return { success: true };
    }
    
    case 'TRACK_EVENT': {
      const { name, category, properties } = message.payload;
      
      await db.analytics.add({
        id: `event_${Date.now()}`,
        name,
        category,
        timestamp: new Date(),
        properties
      });
      
      return { success: true };
    }
    
    default: {
      return {
        type: 'ERROR',
        payload: {
          message: 'Unknown message type',
          code: 'UNKNOWN_MESSAGE'
        }
      };
    }
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({
    url: chrome.runtime.getURL('dashboard.html')
  });
});

// Handle alarms for scheduled tasks
chrome.alarms.onAlarm.addListener(async (alarm) => {
  console.log('Alarm triggered:', alarm.name);
  
  if (alarm.name.startsWith('deal_followup_')) {
    const dealId = alarm.name.replace('deal_followup_', '');
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
      title: 'Deal Follow-up Reminder',
      message: 'Time to follow up on your deal!',
      priority: 2,
      requireInteraction: true
    });
  }
});

// Export for testing
export { fmvCalculator, roiCalculator, riskEngine };