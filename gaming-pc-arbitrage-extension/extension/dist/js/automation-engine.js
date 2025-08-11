// AutomationEngine v3.5.0 - Smart scanning automation
class AutomationEngine {
  constructor() {
    this.isRunning = false;
    this.currentSession = null;
    this.queue = [];
    this.activeTabs = new Map();
    this.results = [];
    this.config = {
      maxConcurrentTabs: 3,
      scanDelay: 2000,
      pageTimeout: 30000,
      retryAttempts: 3
    };
    
    this.init();
  }
  
  init() {
    // Listen for messages
    if (chrome.runtime) {
      chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'SCAN_COMPLETE') {
          this.handleScanComplete(sender.tab.id, request.data);
        }
      });
    }
  }
  
  async startSession(options) {
    if (this.isRunning) {
      throw new Error('Automation already running');
    }
    
    this.isRunning = true;
    this.currentSession = {
      id: Date.now().toString(),
      startTime: Date.now(),
      options: options,
      stats: {
        scanned: 0,
        found: 0,
        errors: 0
      }
    };
    
    // Build search URLs
    const urls = this.buildSearchUrls(options);
    this.queue = urls;
    
    // Start processing
    this.processQueue();
    
    return this.currentSession;
  }
  
  buildSearchUrls(options) {
    const urls = [];
    const { keywords, platforms, filters } = options;
    
    platforms.forEach(platform => {
      keywords.forEach(keyword => {
        const url = window.searchBuilder.buildSearchUrl(
          platform,
          [keyword],
          filters
        );
        urls.push({ platform, keyword, url });
      });
    });
    
    return urls;
  }
  
  async processQueue() {
    while (this.queue.length > 0 && this.isRunning) {
      if (this.activeTabs.size < this.config.maxConcurrentTabs) {
        const item = this.queue.shift();
        this.scanUrl(item);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  async scanUrl(item) {
    try {
      const tab = await chrome.tabs.create({
        url: item.url,
        active: false
      });
      
      this.activeTabs.set(tab.id, {
        ...item,
        startTime: Date.now()
      });
      
      // Set timeout
      setTimeout(() => {
        if (this.activeTabs.has(tab.id)) {
          this.handleTimeout(tab.id);
        }
      }, this.config.pageTimeout);
      
    } catch (error) {
      console.error('Failed to create tab:', error);
      this.currentSession.stats.errors++;
    }
  }
  
  handleScanComplete(tabId, data) {
    const tabInfo = this.activeTabs.get(tabId);
    if (!tabInfo) return;
    
    this.activeTabs.delete(tabId);
    this.currentSession.stats.scanned++;
    
    if (data.listings && data.listings.length > 0) {
      this.currentSession.stats.found += data.listings.length;
      this.results.push(...data.listings);
    }
    
    // Close tab
    chrome.tabs.remove(tabId);
    
    // Check if done
    if (this.queue.length === 0 && this.activeTabs.size === 0) {
      this.completeSession();
    }
  }
  
  handleTimeout(tabId) {
    this.activeTabs.delete(tabId);
    this.currentSession.stats.errors++;
    chrome.tabs.remove(tabId);
  }
  
  completeSession() {
    this.isRunning = false;
    this.currentSession.endTime = Date.now();
    this.currentSession.results = this.results;
    
    // Notify
    chrome.runtime.sendMessage({
      action: 'AUTOMATION_COMPLETE',
      session: this.currentSession
    });
    
    // Reset
    this.currentSession = null;
    this.results = [];
  }
  
  stopSession() {
    this.isRunning = false;
    
    // Close all active tabs
    this.activeTabs.forEach((info, tabId) => {
      chrome.tabs.remove(tabId);
    });
    
    this.activeTabs.clear();
    this.queue = [];
    
    if (this.currentSession) {
      this.currentSession.cancelled = true;
      this.completeSession();
    }
  }
}

window.automationEngine = new AutomationEngine();
