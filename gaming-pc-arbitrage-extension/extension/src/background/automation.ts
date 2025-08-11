/**
 * Background Automation Handler
 * Manages automated tab opening and scanning based on alarms
 */

import { savedSearchesManager, SavedSearch } from '../lib/automation/savedSearches';

interface ScanResult {
  searchId: string;
  url: string;
  foundCount: number;
  newCandidates: number;
  error?: string;
}

class AutomationHandler {
  private activeTabs: Map<string, number> = new Map(); // searchId -> tabId
  private scanQueue: SavedSearch[] = [];
  private isProcessing = false;

  async initialize() {
    // Listen for alarms
    chrome.alarms.onAlarm.addListener(this.handleAlarm.bind(this));

    // Listen for tab events
    chrome.tabs.onRemoved.addListener(this.handleTabRemoved.bind(this));

    // Listen for messages from content scripts
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));

    // Check if automation should be running
    const settings = await savedSearchesManager.getSettings();
    if (settings.enabled) {
      console.log('Automation enabled, scheduling searches...');
      // Reschedule any searches that were missed while extension was inactive
      const searches = await savedSearchesManager.getScheduledScans();
      for (const search of searches) {
        if (!search.nextScan || new Date(search.nextScan) < new Date()) {
          this.scanQueue.push(search);
        }
      }
      this.processQueue();
    }
  }

  private async handleAlarm(alarm: chrome.alarms.Alarm) {
    if (!alarm.name.startsWith('search-scan-')) return;

    const searchId = alarm.name.replace('search-scan-', '');
    const search = await savedSearchesManager.get(searchId);
    
    if (!search || !search.enabled) return;

    const settings = await savedSearchesManager.getSettings();
    if (!settings.enabled) return;

    // Check if user is actively using browser
    if (settings.pauseDuringActiveUse) {
      const isActive = await this.isUserActive();
      if (isActive) {
        console.log(`Postponing scan for ${search.name} - user is active`);
        return;
      }
    }

    // Add to queue
    this.scanQueue.push(search);
    this.processQueue();
  }

  private async processQueue() {
    if (this.isProcessing || this.scanQueue.length === 0) return;

    this.isProcessing = true;
    const settings = await savedSearchesManager.getSettings();

    while (this.scanQueue.length > 0) {
      // Check tab limit
      if (this.activeTabs.size >= settings.maxTabsOpen) {
        console.log('Tab limit reached, waiting...');
        await new Promise(resolve => setTimeout(resolve, 5000));
        continue;
      }

      const search = this.scanQueue.shift()!;
      await this.performScan(search);
      
      // Small delay between scans
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    this.isProcessing = false;
  }

  private async performScan(search: SavedSearch): Promise<void> {
    console.log(`Starting scan for: ${search.name}`);

    try {
      // Create tab
      const tab = await chrome.tabs.create({
        url: search.url,
        active: false, // Open in background
        pinned: true, // Pin to save space
      });

      if (!tab.id) {
        throw new Error('Failed to create tab');
      }

      this.activeTabs.set(search.id, tab.id);

      // Wait for tab to load
      await this.waitForTabLoad(tab.id);

      // Inject content script if needed
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['js/content-scanner.js'],
      });

      // Trigger scan
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: 'performAutomatedScan',
        searchId: search.id,
        filters: search.filters,
      });

      // Process results
      if (response && response.success) {
        await this.processResults({
          searchId: search.id,
          url: search.url,
          foundCount: response.totalFound || 0,
          newCandidates: response.newCandidates || 0,
        });
      }

      // Close tab if configured
      const settings = await savedSearchesManager.getSettings();
      if (settings.closeTabsAfterScan) {
        await chrome.tabs.remove(tab.id);
        this.activeTabs.delete(search.id);
      }

    } catch (error) {
      console.error(`Scan failed for ${search.name}:`, error);
      await this.processResults({
        searchId: search.id,
        url: search.url,
        foundCount: 0,
        newCandidates: 0,
        error: error.message,
      });
    }
  }

  private async waitForTabLoad(tabId: number, timeout = 30000): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const checkTab = async () => {
        try {
          const tab = await chrome.tabs.get(tabId);
          
          if (tab.status === 'complete') {
            resolve();
            return;
          }

          if (Date.now() - startTime > timeout) {
            reject(new Error('Tab load timeout'));
            return;
          }

          setTimeout(checkTab, 500);
        } catch (error) {
          reject(error);
        }
      };

      checkTab();
    });
  }

  private async processResults(result: ScanResult): Promise<void> {
    // Update search record
    await savedSearchesManager.recordScan(result.searchId, result.foundCount);

    // Store results
    const existingResults = await chrome.storage.local.get(['scanResults']);
    const results = existingResults.scanResults || [];
    results.push({
      ...result,
      timestamp: new Date().toISOString(),
    });

    // Keep only last 100 results
    if (results.length > 100) {
      results.splice(0, results.length - 100);
    }

    await chrome.storage.local.set({ scanResults: results });

    // Notify if new candidates found
    if (result.newCandidates > 0) {
      const settings = await savedSearchesManager.getSettings();
      if (settings.notifyOnNewFinds) {
        await this.showNotification(result);
      }
    }

    // Update dashboard stats
    await this.updateDashboardStats(result);
  }

  private async showNotification(result: ScanResult): Promise<void> {
    const search = await savedSearchesManager.get(result.searchId);
    if (!search) return;

    chrome.notifications.create({
      type: 'basic',
      iconUrl: '/icons/icon-128.png',
      title: 'New Candidates Found!',
      message: `Found ${result.newCandidates} new listings from ${search.name}`,
      buttons: [
        { title: 'View Results' }
      ],
    });
  }

  private async updateDashboardStats(result: ScanResult): Promise<void> {
    const { recentCandidates = [] } = await chrome.storage.local.get(['recentCandidates']);
    
    // Add placeholder candidates (in real implementation, these would come from content script)
    if (result.newCandidates > 0) {
      const newCandidates = Array.from({ length: Math.min(result.newCandidates, 5) }, (_, i) => ({
        id: `auto-${Date.now()}-${i}`,
        title: `Gaming PC - Found via automation`,
        platform: new URL(result.url).hostname.split('.')[0],
        price: Math.floor(Math.random() * 1000) + 500,
        estimatedProfit: Math.floor(Math.random() * 300) + 100,
        riskScore: Math.random() * 0.5,
        foundAt: new Date(),
      }));

      const updated = [...newCandidates, ...recentCandidates].slice(0, 20);
      await chrome.storage.local.set({ recentCandidates: updated });
    }
  }

  private async isUserActive(): Promise<boolean> {
    // Check if user has interacted with browser in last 5 minutes
    const idle = await chrome.idle.queryState(300);
    return idle === 'active';
  }

  private handleTabRemoved(tabId: number): void {
    // Clean up tracking when tabs are closed
    for (const [searchId, id] of this.activeTabs.entries()) {
      if (id === tabId) {
        this.activeTabs.delete(searchId);
        break;
      }
    }
  }

  private handleMessage(
    request: any,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response?: any) => void
  ): boolean {
    if (request.action === 'getAutomationStatus') {
      savedSearchesManager.getSettings().then(settings => {
        sendResponse({ 
          enabled: settings.enabled,
          activeTabs: this.activeTabs.size,
          queueLength: this.scanQueue.length,
        });
      });
      return true; // Will respond asynchronously
    }

    return false;
  }

  // Public methods for testing
  async triggerScan(searchId: string): Promise<void> {
    const search = await savedSearchesManager.get(searchId);
    if (search) {
      this.scanQueue.push(search);
      this.processQueue();
    }
  }

  getStatus() {
    return {
      activeTabs: this.activeTabs.size,
      queueLength: this.scanQueue.length,
      isProcessing: this.isProcessing,
    };
  }
}

export const automationHandler = new AutomationHandler();