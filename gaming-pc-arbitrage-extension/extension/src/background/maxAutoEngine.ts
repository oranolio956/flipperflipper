/**
 * Max Auto Engine - Compliant marketplace automation
 * Opens saved search tabs on schedule, triggers scanning, stores results
 */

import { SavedSearch } from '../types';

export class MaxAutoEngine {
  private isEnabled = false;
  private activeSearches: Map<string, SavedSearch> = new Map();
  private scanQueue: string[] = [];
  private lastRunTime: Map<string, number> = new Map();
  
  constructor() {
    this.initialize();
  }

  async initialize() {
    // Load state from storage
    const result = await chrome.storage.local.get(['automationEnabled', 'savedSearches', 'lastRunTimes']);
    this.isEnabled = result.automationEnabled || false;
    
    if (result.savedSearches) {
      result.savedSearches.forEach((search: SavedSearch) => {
        if (search.enabled) {
          this.activeSearches.set(search.id, search);
        }
      });
    }
    
    this.lastRunTime = new Map(Object.entries(result.lastRunTimes || {}));
    
    // Set up alarm listeners
    chrome.alarms.onAlarm.addListener(this.handleAlarm.bind(this));
    
    // Schedule next runs
    if (this.isEnabled) {
      this.scheduleAllSearches();
    }
  }

  async enable() {
    this.isEnabled = true;
    await chrome.storage.local.set({ automationEnabled: true });
    this.scheduleAllSearches();
    
    // Notify UI
    chrome.runtime.sendMessage({
      type: 'AUTOMATION_STATUS_CHANGED',
      status: 'active'
    });
  }

  async disable() {
    this.isEnabled = false;
    await chrome.storage.local.set({ automationEnabled: false });
    
    // Clear all alarms
    for (const searchId of this.activeSearches.keys()) {
      await chrome.alarms.clear(`search-scan-${searchId}`);
    }
    
    // Notify UI
    chrome.runtime.sendMessage({
      type: 'AUTOMATION_STATUS_CHANGED',
      status: 'off'
    });
  }

  async addSearch(search: SavedSearch) {
    this.activeSearches.set(search.id, search);
    
    if (this.isEnabled && search.enabled) {
      this.scheduleSearch(search);
    }
    
    // Save to storage
    const searches = Array.from(this.activeSearches.values());
    await chrome.storage.local.set({ savedSearches: searches });
  }

  async removeSearch(searchId: string) {
    this.activeSearches.delete(searchId);
    await chrome.alarms.clear(`search-scan-${searchId}`);
    
    // Save to storage
    const searches = Array.from(this.activeSearches.values());
    await chrome.storage.local.set({ savedSearches: searches });
  }

  private async scheduleAllSearches() {
    for (const search of this.activeSearches.values()) {
      if (search.enabled) {
        await this.scheduleSearch(search);
      }
    }
  }

  private async scheduleSearch(search: SavedSearch) {
    const alarmName = `search-scan-${search.id}`;
    
    // Check if user is idle before scheduling
    const idleState = await chrome.idle.queryState(60); // 60 second threshold
    
    if (idleState === 'active') {
      // User is active, delay the scan
      console.log(`User active, delaying scan for ${search.name}`);
      await chrome.alarms.create(alarmName, {
        delayInMinutes: 5 // Try again in 5 minutes
      });
      return;
    }
    
    // Schedule based on cadence
    await chrome.alarms.create(alarmName, {
      periodInMinutes: search.cadenceMinutes,
      delayInMinutes: 0.1 // Start almost immediately
    });
  }

  private async handleAlarm(alarm: chrome.alarms.Alarm) {
    if (!alarm.name.startsWith('search-scan-') || !this.isEnabled) {
      return;
    }
    
    const searchId = alarm.name.replace('search-scan-', '');
    const search = this.activeSearches.get(searchId);
    
    if (!search || !search.enabled) {
      return;
    }
    
    // Check user idle state
    const idleState = await chrome.idle.queryState(60);
    if (idleState === 'active') {
      console.log(`User active, postponing scan for ${search.name}`);
      // Reschedule for later
      await chrome.alarms.create(alarm.name, {
        delayInMinutes: 5
      });
      return;
    }
    
    // Execute the scan
    await this.executeScan(search);
  }

  private async executeScan(search: SavedSearch) {
    console.log(`Max Auto: Starting scan for "${search.name}"`);
    
    try {
      // Record scan start
      const scanId = `scan-${Date.now()}`;
      await this.logEvent({
        type: 'scan_started',
        searchId: search.id,
        searchName: search.name,
        url: search.url,
        timestamp: new Date().toISOString()
      });
      
      // Create and pin tab
      const tab = await chrome.tabs.create({
        url: search.url,
        active: false,
        pinned: true
      });
      
      if (!tab.id) {
        throw new Error('Failed to create tab');
      }
      
      // Wait for page to load
      await this.waitForTabLoad(tab.id);
      
      // Inject content script if needed
      await this.ensureContentScriptInjected(tab.id, search.platform);
      
      // Wait a bit for dynamic content
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Trigger scan via content script
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: 'SCAN_PAGE',
        scanId,
        searchId: search.id,
        autoScan: true
      });
      
      if (response?.success) {
        // Store results
        const candidates = response.candidates || [];
        await this.storeScanResults(search, candidates);
        
        // Log success
        await this.logEvent({
          type: 'scan_completed',
          searchId: search.id,
          candidateCount: candidates.length,
          timestamp: new Date().toISOString()
        });
        
        // Notify if new high-value candidates
        const highValue = candidates.filter((c: any) => c.roi > 0.3);
        if (highValue.length > 0) {
          await this.notifyNewCandidates(search, highValue);
        }
      } else {
        throw new Error(response?.error || 'Scan failed');
      }
      
      // Close tab after delay
      setTimeout(() => {
        chrome.tabs.remove(tab.id!);
      }, 2000);
      
      // Update last run time
      this.lastRunTime.set(search.id, Date.now());
      await this.saveLastRunTimes();
      
    } catch (error) {
      console.error(`Max Auto: Scan failed for "${search.name}"`, error);
      
      await this.logEvent({
        type: 'scan_failed',
        searchId: search.id,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }

  private async waitForTabLoad(tabId: number): Promise<void> {
    return new Promise((resolve) => {
      const listener = (tabIdUpdated: number, info: chrome.tabs.TabChangeInfo) => {
        if (tabIdUpdated === tabId && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
    });
  }

  private async ensureContentScriptInjected(tabId: number, platform: string) {
    try {
      // Check if content script is already injected
      const response = await chrome.tabs.sendMessage(tabId, { action: 'PING' });
      if (response?.pong) {
        return; // Already injected
      }
    } catch (e) {
      // Not injected, inject now
    }
    
    // Inject content script based on platform
    const scriptFile = platform === 'facebook' ? 'content-facebook.js' :
                      platform === 'craigslist' ? 'content-craigslist.js' :
                      platform === 'offerup' ? 'content-offerup.js' : null;
                      
    if (scriptFile) {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: [`js/${scriptFile}`]
      });
      
      // Also inject CSS
      await chrome.scripting.insertCSS({
        target: { tabId },
        files: ['css/overlay.css']
      });
    }
  }

  private async storeScanResults(search: SavedSearch, candidates: any[]) {
    // Get existing listings
    const result = await chrome.storage.local.get(['scannedListings']);
    const existingListings = result.scannedListings || [];
    
    // Merge new candidates, avoiding duplicates
    const existingIds = new Set(existingListings.map((l: any) => l.id));
    const newCandidates = candidates.filter(c => !existingIds.has(c.id));
    
    // Add metadata
    const enrichedCandidates = newCandidates.map(c => ({
      ...c,
      foundVia: search.name,
      searchId: search.id,
      scannedAt: new Date().toISOString(),
      autoScanned: true
    }));
    
    // Store (keep last 500 listings)
    const allListings = [...enrichedCandidates, ...existingListings].slice(0, 500);
    await chrome.storage.local.set({ scannedListings: allListings });
    
    // Update candidate count for this search
    search.lastScanResults = candidates.length;
    search.lastScanTime = new Date().toISOString();
    await this.addSearch(search);
  }

  private async notifyNewCandidates(search: SavedSearch, candidates: any[]) {
    const bestCandidate = candidates.sort((a, b) => b.roi - a.roi)[0];
    
    await chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon-128.png',
      title: `New High-Value Find!`,
      message: `${bestCandidate.title} - ${Math.round(bestCandidate.roi * 100)}% ROI from ${search.name}`,
      buttons: [
        { title: 'View Details' },
        { title: 'Dismiss' }
      ],
      requireInteraction: true
    });
  }

  private async logEvent(event: any) {
    const result = await chrome.storage.local.get(['automationLogs']);
    const logs = result.automationLogs || [];
    
    // Add event to logs (keep last 1000)
    logs.unshift(event);
    if (logs.length > 1000) {
      logs.length = 1000;
    }
    
    await chrome.storage.local.set({ automationLogs: logs });
    
    // Notify UI of new log
    chrome.runtime.sendMessage({
      type: 'AUTOMATION_LOG_ADDED',
      event
    });
  }

  private async saveLastRunTimes() {
    const times: Record<string, number> = {};
    this.lastRunTime.forEach((time, id) => {
      times[id] = time;
    });
    await chrome.storage.local.set({ lastRunTimes: times });
  }

  // Public methods for UI
  
  async getStatus() {
    return {
      enabled: this.isEnabled,
      activeSearchCount: this.activeSearches.size,
      searches: Array.from(this.activeSearches.values()),
      lastRunTimes: Object.fromEntries(this.lastRunTime)
    };
  }

  async getLogs(limit = 100) {
    const result = await chrome.storage.local.get(['automationLogs']);
    const logs = result.automationLogs || [];
    return logs.slice(0, limit);
  }

  async pauseSearch(searchId: string) {
    const search = this.activeSearches.get(searchId);
    if (search) {
      search.enabled = false;
      await this.addSearch(search);
      await chrome.alarms.clear(`search-scan-${searchId}`);
    }
  }

  async resumeSearch(searchId: string) {
    const search = this.activeSearches.get(searchId);
    if (search) {
      search.enabled = true;
      await this.addSearch(search);
      if (this.isEnabled) {
        await this.scheduleSearch(search);
      }
    }
  }

  async testScan(searchId: string) {
    const search = this.activeSearches.get(searchId);
    if (search) {
      await this.executeScan(search);
    }
  }
}

// Export singleton instance
export const maxAutoEngine = new MaxAutoEngine();