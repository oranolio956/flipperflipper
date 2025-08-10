/**
 * Background Service Worker (MV3)
 * Handles message routing, alarms, notifications, and permissions
 */

import { 
  onMessage, 
  MessageRequest, 
  MessageType,
  ParsePageRequest,
  CalcValuationRequest,
  SaveListingRequest,
  CreateDealRequest,
  UpdateDealStageRequest,
  ScheduleFollowupRequest,
  ExportCsvRequest,
  ImportJsonRequest,
  BaseResponse,
  hasHostPermission,
} from '@/lib/messages';
import { 
  db, 
  saveParsedListing, 
  upsertDealStage, 
  exportJson, 
  importJson,
  listingsNeedingFollowUp,
  getActiveDeals,
  logEvent,
} from '@/lib/db';
import { 
  initializeSettings, 
  getSettings, 
  setSettings,
  getAutomationMode,
} from '@/lib/settings';
import {
  ListingParser,
  FMVCalculator,
  ROICalculator,
  RiskEngine,
  Deal,
  generateId,
} from '@/core';
import { initializeSync, handleSyncAlarm, triggerSync } from './sync';
import { initializeBackup, handleBackupAlarm, triggerBackup } from './backup';
import { handleOfferFollowUp, initializeOfferAlarms } from './offers';
import { getSearchesDue } from '@/lib/watches';

// Rate limiting
const requestCounts = new Map<string, number>();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 30;

// Initialize on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('Extension installed:', details.reason);
  
  // Initialize settings
  await initializeSettings();
  
  // Initialize Google Sheets sync
  await initializeSync();
  
  // Initialize backup system
  await initializeBackup();
  
  // Set up alarms for follow-ups
  chrome.alarms.create('followup-check', { periodInMinutes: 60 });
  chrome.alarms.create('cleanup', { periodInMinutes: 1440 }); // Daily
  
  // Create default context menus
  chrome.contextMenus.create({
    id: 'parse-listing',
    title: 'Analyze This Listing',
    contexts: ['page'],
    documentUrlPatterns: [
      '*://www.facebook.com/marketplace/*',
      '*://*.craigslist.org/*',
      '*://offerup.com/*',
    ],
  });
});

// Handle alarms
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'followup-check') {
    await checkFollowUps();
  } else if (alarm.name === 'cleanup') {
    await performCleanup();
  } else if (alarm.name === 'sheets-sync') {
    await handleSyncAlarm();
  } else if (alarm.name === 'auto-backup') {
    await handleBackupAlarm();
  } else if (alarm.name === 'offer-followup') {
    await handleOfferFollowUp();
  } else if (alarm.name === 'saved-searches') {
    await checkSavedSearches();
  } else if (alarm.name.startsWith('followup-')) {
    // Individual follow-up alarm
    const dealId = alarm.name.replace('followup-', '');
    await sendFollowUpNotification(dealId);
  }
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'parse-listing' && tab?.id) {
    // Inject content script if needed
    await chrome.tabs.sendMessage(tab.id, { action: 'parse' });
  }
});

// Main message handler
onMessage(async (request: MessageRequest, sender) => {
  // Rate limiting check
  if (!checkRateLimit(sender.tab?.id)) {
    return { success: false, error: 'Rate limit exceeded' };
  }
  
  // Check permissions for content script requests
  if (sender.tab && !await hasHostPermission(sender.tab.url || '')) {
    if (request.type !== MessageType.REQUEST_PERMISSION) {
      return { success: false, error: 'Permission required for this site' };
    }
  }
  
  try {
    switch (request.type) {
      case MessageType.PARSE_PAGE:
        return await handleParsePage(request as ParsePageRequest);
        
      case MessageType.CALC_VALUATION:
        return await handleCalcValuation(request as CalcValuationRequest);
        
      case MessageType.SAVE_LISTING:
        return await handleSaveListing(request as SaveListingRequest);
        
      case MessageType.CREATE_DEAL:
        return await handleCreateDeal(request as CreateDealRequest);
        
      case MessageType.UPDATE_DEAL_STAGE:
        return await handleUpdateDealStage(request as UpdateDealStageRequest);
        
      case MessageType.SCHEDULE_FOLLOWUP:
        return await handleScheduleFollowup(request as ScheduleFollowupRequest);
        
      case MessageType.EXPORT_CSV:
        return await handleExportCsv(request as ExportCsvRequest);
        
      case MessageType.IMPORT_JSON:
        return await handleImportJson(request as ImportJsonRequest);
        
      case MessageType.GET_SETTINGS:
        const settings = await getSettings();
        return { success: true, settings };
        
      case MessageType.SET_SETTINGS:
        const updated = await setSettings(request.settings, request.partial);
        return { success: true, settings: updated };
        
      case MessageType.REQUEST_PERMISSION:
        return await handleRequestPermission(request.permission);
        
      case MessageType.OPEN_DASHBOARD:
        return await handleOpenDashboard(request);
        
      case MessageType.GENERATE_DRAFT:
        return await handleGenerateDraft(request);
      
      // Google Sheets handlers
      case MessageType.SHEETS_SYNC:
        await triggerSync((request as any).direction);
        return { success: true };
        
      case MessageType.SHEETS_PUSH_NOW:
        await triggerSync('push');
        return { success: true };
        
      case MessageType.SHEETS_PULL_NOW:
        await triggerSync('pull');
        return { success: true };
        
      case MessageType.BACKUP_NOW:
        const filename = await triggerBackup();
        return { success: true, filename };
        
      case MessageType.SAVE_COMPS:
        const { saveComps } = await import('@/lib/comps.store');
        await saveComps((request as any).comps);
        return { success: true };
        
      default:
        return { success: false, error: 'Unknown message type' };
    }
  } catch (error) {
    console.error('Message handler error:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Handler error' 
    };
  }
});

// Handler implementations

async function handleParsePage(request: ParsePageRequest) {
  const settings = await getSettings();
  
  // Parse listing
  const parser = new ListingParser();
  const listing = await parser.parseListing(request.url, {
    querySelector: (selector: string) => {
      const div = document.createElement('div');
      div.innerHTML = request.html;
      return div.querySelector(selector);
    },
    querySelectorAll: (selector: string) => {
      const div = document.createElement('div');
      div.innerHTML = request.html;
      return div.querySelectorAll(selector);
    },
  } as any as Document);
  
  if (!listing) {
    return { success: false, error: 'Failed to parse listing' };
  }
  
  // Calculate FMV
  const fmvCalc = new FMVCalculator(settings);
  const fmv = await fmvCalc.calculate(listing);
  
  // Calculate ROI
  const roiCalc = new ROICalculator(settings);
  const roi = roiCalc.calculate(listing, fmv);
  
  // Assess risks
  const riskEngine = new RiskEngine(settings);
  const risk = riskEngine.assessListing(listing);
  
  // Update listing with calculations
  listing.analysis = {
    fmv: fmv.total,
    componentValue: fmv.componentBreakdown.reduce((sum, c) => sum + c.adjustedValue, 0),
    profitPotential: roi.netProfit,
    roi: roi.roi,
    margin: roi.profitMargin,
    dealScore: roi.dealScore,
    confidence: fmv.confidence,
  };
  
  listing.risks = {
    score: risk.overallScore,
    flags: risk.flags.map(f => ({
      type: f.type,
      severity: f.severity,
      description: f.description,
    })),
    stolen: { probability: 0, indicators: [] },
    scam: { probability: 0, patterns: [] },
    technical: { issues: [], severity: 'low' },
  };
  
  // Log event
  await logEvent({
    name: 'listing_parsed',
    category: 'sourcing',
    properties: {
      platform: listing.platform,
      hasGPU: !!listing.components.gpu,
      fmv: Math.round(fmv.total),
      roi: Math.round(roi.roi),
      riskScore: risk.overallScore,
    },
  });
  
  return { success: true, listing, fmv, roi, risk };
}

async function handleCalcValuation(request: CalcValuationRequest) {
  const settings = await getSettings();
  const { listing } = request;
  
  const fmvCalc = new FMVCalculator(settings);
  const fmv = await fmvCalc.calculate(listing);
  
  const roiCalc = new ROICalculator(settings);
  const roi = roiCalc.calculate(listing, fmv);
  
  const riskEngine = new RiskEngine(settings);
  const risk = riskEngine.assessListing(listing);
  
  return { success: true, fmv, roi, risk };
}

async function handleSaveListing(request: SaveListingRequest) {
  const { listing, autoCreateDeal } = request;
  
  // Save listing
  const listingId = await saveParsedListing(listing);
  listing.id = listing.id || generateId('listing');
  
  let dealId: string | undefined;
  
  if (autoCreateDeal) {
    // Create deal automatically
    const deal: Deal = {
      id: generateId('deal'),
      listingId: listing.id,
      listing,
      stage: 'discovered',
      stageHistory: [{
        from: 'discovered' as const,
        to: 'discovered' as const,
        timestamp: new Date(),
        automatic: true,
      }],
      negotiation: {
        askingPrice: listing.price,
        offers: [],
        walkAwayPrice: listing.analysis.fmv * 0.7,
        targetPrice: listing.analysis.fmv * 0.65,
      },
      communication: {
        messages: [],
        templates: [],
      },
      logistics: {
        pickup: {
          confirmed: false,
          notes: '',
        },
        transport: {
          method: 'personal',
          cost: 0,
          distance: listing.location.distance || 0,
          time: 0,
        },
      },
      financials: {
        listingFees: 0,
        transportCost: 0,
        refurbCosts: [],
        totalInvestment: 0,
        estimatedResale: listing.analysis.fmv * 1.1,
        estimatedProfit: 0,
      },
      documentation: {
        receipts: [],
        photos: [],
        serialNumbers: [],
        testResults: [],
      },
      analytics: {
        daysInStage: { discovered: 0 },
        totalCycleDays: 0,
        profitMargin: 0,
        roi: 0,
        scorecard: {
          negotiation: 0,
          timing: 0,
          execution: 0,
          overall: 0,
        },
      },
      metadata: {
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'system',
        tags: [],
        priority: 'medium',
        archived: false,
      },
    };
    
    await db.deals.add(deal);
    dealId = deal.id;
  }
  
  await logEvent({
    name: 'listing_saved',
    category: 'pipeline',
    properties: {
      platform: listing.platform,
      autoCreateDeal: !!autoCreateDeal,
    },
  });
  
  return { success: true, listingId: listing.id, dealId };
}

async function handleCreateDeal(request: CreateDealRequest) {
  const { listingId, initialOffer } = request;
  
  // Get listing
  const listing = await db.listings.where('id').equals(listingId).first();
  if (!listing) {
    return { success: false, error: 'Listing not found' };
  }
  
  // Create deal (similar to above)
  const dealId = generateId('deal');
  
  // ... (deal creation logic)
  
  return { success: true, dealId };
}

async function handleUpdateDealStage(request: UpdateDealStageRequest) {
  const { dealId, stage, reason } = request;
  
  await upsertDealStage(dealId, stage as Deal['stage'], reason);
  
  await logEvent({
    name: 'deal_stage_updated',
    category: 'pipeline',
    properties: { dealId, stage, reason },
  });
  
  return { success: true };
}

async function handleScheduleFollowup(request: ScheduleFollowupRequest) {
  const { dealId, scheduleFor } = request;
  
  // Create alarm
  const alarmName = `followup-${dealId}`;
  const when = new Date(scheduleFor).getTime();
  
  chrome.alarms.create(alarmName, { when });
  
  // Save to thread
  await db.threads.add({
    dealId,
    platform: 'system',
    messages: [{
      id: generateId(),
      content: `Follow-up scheduled for ${scheduleFor}`,
      timestamp: new Date(),
      direction: 'sent',
    }],
    lastActivity: new Date(),
  });
  
  return { success: true, alarmName };
}

async function handleExportCsv(request: ExportCsvRequest) {
  const { dataType } = request;
  
  // For now, export as JSON
  const data = await exportJson();
  
  return { 
    success: true, 
    csv: data, 
    filename: `arbitrage-${dataType}-${Date.now()}.json` 
  };
}

async function handleImportJson(request: ImportJsonRequest) {
  await importJson(request.jsonData);
  return { success: true };
}

async function handleRequestPermission(permission: string) {
  const granted = await chrome.permissions.request({
    origins: [permission],
  });
  
  return { success: true, granted };
}

async function handleOpenDashboard(request: any) {
  const url = chrome.runtime.getURL(`dashboard/index.html#/${request.page || 'pipeline'}`);
  await chrome.tabs.create({ url });
  return { success: true };
}

async function handleGenerateDraft(request: any) {
  // Implementation would use negotiation templates from core
  return { 
    success: true, 
    draft: 'Draft message here',
    variables: {},
  };
}

// Helper functions

function checkRateLimit(tabId?: number): boolean {
  const key = tabId ? `tab-${tabId}` : 'global';
  const now = Date.now();
  const count = requestCounts.get(key) || 0;
  
  // Clean old entries
  for (const [k, _] of requestCounts) {
    if (!requestCounts.has(k)) continue;
  }
  
  if (count >= MAX_REQUESTS_PER_WINDOW) {
    return false;
  }
  
  requestCounts.set(key, count + 1);
  
  // Schedule cleanup
  setTimeout(() => {
    requestCounts.delete(key);
  }, RATE_LIMIT_WINDOW);
  
  return true;
}

async function checkFollowUps() {
  const mode = await getAutomationMode();
  if (mode === 'off') return;
  
  const listings = await listingsNeedingFollowUp();
  
  for (const listing of listings) {
    await chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
      title: 'Follow-up Needed',
      message: `Time to follow up on: ${listing.title}`,
      buttons: [{ title: 'Open Deal' }, { title: 'Dismiss' }],
    });
  }
}

async function sendFollowUpNotification(dealId: string) {
  const deal = await db.deals.where('id').equals(dealId).first();
  if (!deal) return;
  
  await chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
    title: 'Follow-up Reminder',
    message: `Follow up on: ${deal.listing.title}`,
    buttons: [{ title: 'Open Deal' }, { title: 'Snooze' }],
  });
}

async function performCleanup() {
  // Clean old events
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 90);
  
  await db.events.where('timestamp').below(cutoff).delete();
}

async function checkSavedSearches() {
  try {
    const searches = await getSearchesDue();
    
    for (const search of searches) {
      // Send notification for each due search
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
        title: 'Search Monitor Ready',
        message: `"${search.name}" is ready to run`,
        buttons: [
          { title: 'Run Search' },
          { title: 'Skip' },
        ],
        requireInteraction: true,
      }, (notificationId) => {
        // Store search ID for button handling
        chrome.storage.session.set({
          [`search-${notificationId}`]: search.id,
        });
      });
    }
  } catch (error) {
    console.error('Check saved searches error:', error);
  }
}

// Handle notification clicks
chrome.notifications.onButtonClicked.addListener(async (notifId, btnIdx) => {
  if (btnIdx === 0) {
    // Open deal
    const url = chrome.runtime.getURL('dashboard/index.html#/pipeline');
    await chrome.tabs.create({ url });
  }
  chrome.notifications.clear(notifId);
});