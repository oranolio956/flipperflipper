/**
 * Max Auto Engine v3.4.0 - Intelligent Scanning Automation
 * Manages concurrent scans, respects settings, handles errors gracefully
 */

import { settingsManager } from './settings';

export interface ScanJob {
  id: string;
  searchId: string;
  searchName: string;
  url: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt?: string;
  completedAt?: string;
  error?: string;
  resultsCount?: number;
  tabId?: number;
}

export interface ScanSession {
  id: string;
  startedAt: string;
  completedAt?: string;
  jobs: ScanJob[];
  stats: {
    total: number;
    completed: number;
    failed: number;
    cancelled: number;
    newListings: number;
    goodDeals: number;
  };
}

export class AutomationEngine {
  private static instance: AutomationEngine;
  private currentSession: ScanSession | null = null;
  private activeJobs: Map<string, ScanJob> = new Map();
  private jobQueue: ScanJob[] = [];
  private isRunning = false;
  private isPaused = false;
  private listeners: Set<(event: AutomationEvent) => void> = new Set();
  
  private constructor() {
    this.initialize();
  }
  
  static getInstance(): AutomationEngine {
    if (!AutomationEngine.instance) {
      AutomationEngine.instance = new AutomationEngine();
    }
    return AutomationEngine.instance;
  }
  
  private async initialize() {
    // Listen for tab events
    chrome.tabs.onRemoved.addListener(this.handleTabRemoved.bind(this));
    chrome.tabs.onUpdated.addListener(this.handleTabUpdated.bind(this));
    
    // Listen for messages from content scripts
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    
    console.log('[AutoEngine] Initialized');
  }
  
  /**
   * Start a new automation session
   */
  async startSession(searchIds?: string[]): Promise<ScanSession> {
    if (this.isRunning) {
      throw new Error('Session already in progress');
    }
    
    const settings = settingsManager.get();
    const allSearches = settings.search.savedSearches;
    
    // Filter searches to run
    const searchesToRun = searchIds 
      ? allSearches.filter(s => searchIds.includes(s.id))
      : allSearches.filter(s => s.enabled);
    
    if (searchesToRun.length === 0) {
      throw new Error('No searches to run');
    }
    
    // Create session
    this.currentSession = {
      id: `session_${Date.now()}`,
      startedAt: new Date().toISOString(),
      jobs: [],
      stats: {
        total: searchesToRun.length,
        completed: 0,
        failed: 0,
        cancelled: 0,
        newListings: 0,
        goodDeals: 0
      }
    };
    
    // Create jobs
    this.jobQueue = searchesToRun.map(search => ({
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      searchId: search.id,
      searchName: search.name,
      url: search.url,
      status: 'pending' as const
    }));
    
    this.currentSession.jobs = [...this.jobQueue];
    this.isRunning = true;
    
    // Save session
    await this.saveSession();
    
    // Emit event
    this.emit({
      type: 'session_started',
      session: this.currentSession
    });
    
    // Start processing
    this.processQueue();
    
    return this.currentSession;
  }
  
  /**
   * Stop the current session
   */
  async stopSession(): Promise<void> {
    if (!this.isRunning) return;
    
    this.isRunning = false;
    
    // Cancel pending jobs
    this.jobQueue = [];
    
    // Close active tabs
    for (const [jobId, job] of this.activeJobs) {
      if (job.tabId) {
        try {
          await chrome.tabs.remove(job.tabId);
        } catch (e) {
          // Tab might already be closed
        }
      }
      job.status = 'cancelled';
    }
    
    if (this.currentSession) {
      this.currentSession.completedAt = new Date().toISOString();
      this.currentSession.stats.cancelled = this.jobQueue.length + this.activeJobs.size;
      await this.saveSession();
      
      this.emit({
        type: 'session_stopped',
        session: this.currentSession
      });
    }
    
    this.activeJobs.clear();
    console.log('[AutoEngine] Session stopped');
  }
  
  /**
   * Pause/resume scanning
   */
  setPaused(paused: boolean): void {
    this.isPaused = paused;
    
    if (!paused && this.isRunning) {
      this.processQueue();
    }
    
    this.emit({
      type: paused ? 'session_paused' : 'session_resumed',
      session: this.currentSession
    });
  }
  
  /**
   * Process the job queue
   */
  private async processQueue(): Promise<void> {
    if (!this.isRunning || this.isPaused || this.jobQueue.length === 0) {
      // Check if all jobs are done
      if (this.isRunning && this.activeJobs.size === 0 && this.jobQueue.length === 0) {
        await this.completeSession();
      }
      return;
    }
    
    const settings = settingsManager.get();
    const maxConcurrent = settings.automation.maxConcurrentTabs || 3;
    
    // Start new jobs up to the limit
    while (this.activeJobs.size < maxConcurrent && this.jobQueue.length > 0) {
      const job = this.jobQueue.shift();
      if (!job) break;
      
      // Check if we should pause for active use
      if (settings.automation.pauseDuringActive) {
        const idleState = await chrome.idle.queryState(60);
        if (idleState === 'active') {
          console.log('[AutoEngine] User active, pausing');
          this.jobQueue.unshift(job); // Put job back
          this.setPaused(true);
          
          // Check again in 30 seconds
          setTimeout(() => {
            if (this.isPaused) {
              chrome.idle.queryState(60).then(state => {
                if (state !== 'active') {
                  console.log('[AutoEngine] User idle, resuming');
                  this.setPaused(false);
                }
              });
            }
          }, 30000);
          
          return;
        }
      }
      
      this.startJob(job);
    }
  }
  
  /**
   * Start a scanning job
   */
  private async startJob(job: ScanJob): Promise<void> {
    try {
      job.status = 'running';
      job.startedAt = new Date().toISOString();
      this.activeJobs.set(job.id, job);
      
      console.log(`[AutoEngine] Starting job ${job.id} for ${job.searchName}`);
      
      // Create tab
      const tab = await chrome.tabs.create({
        url: job.url,
        active: false,
        pinned: true
      });
      
      job.tabId = tab.id;
      
      this.emit({
        type: 'job_started',
        job,
        session: this.currentSession
      });
      
      // Set timeout for job
      setTimeout(() => {
        if (this.activeJobs.has(job.id)) {
          console.warn(`[AutoEngine] Job ${job.id} timed out`);
          this.failJob(job.id, 'Scan timed out');
        }
      }, 60000); // 1 minute timeout
      
    } catch (error) {
      console.error(`[AutoEngine] Failed to start job ${job.id}:`, error);
      this.failJob(job.id, String(error));
    }
  }
  
  /**
   * Handle tab updates
   */
  private handleTabUpdated(tabId: number, changeInfo: chrome.tabs.TabChangeInfo, tab: chrome.tabs.Tab): void {
    if (changeInfo.status !== 'complete') return;
    
    // Find job for this tab
    const job = Array.from(this.activeJobs.values()).find(j => j.tabId === tabId);
    if (!job) return;
    
    console.log(`[AutoEngine] Tab loaded for job ${job.id}`);
    
    // Inject scanner after a short delay
    setTimeout(() => {
      if (job.tabId) {
        this.injectScanner(job.tabId, job.id);
      }
    }, 1000);
  }
  
  /**
   * Inject scanner into tab
   */
  private async injectScanner(tabId: number, jobId: string): Promise<void> {
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['js/scanner.js']
      });
      
      // Send scan command with job ID
      chrome.tabs.sendMessage(tabId, { 
        action: 'START_SCAN',
        jobId 
      });
      
    } catch (error) {
      console.error(`[AutoEngine] Failed to inject scanner for job ${jobId}:`, error);
      this.failJob(jobId, 'Failed to inject scanner');
    }
  }
  
  /**
   * Handle messages from content scripts
   */
  private handleMessage(request: any, sender: chrome.runtime.MessageSender, sendResponse: Function): boolean {
    if (request.action === 'SCAN_COMPLETE') {
      const job = this.activeJobs.get(request.jobId);
      if (job) {
        this.completeJob(request.jobId, request.results);
      }
      return false;
    }
    
    if (request.action === 'SCAN_FAILED') {
      const job = this.activeJobs.get(request.jobId);
      if (job) {
        this.failJob(request.jobId, request.error);
      }
      return false;
    }
    
    return false;
  }
  
  /**
   * Complete a job successfully
   */
  private async completeJob(jobId: string, results: any): Promise<void> {
    const job = this.activeJobs.get(jobId);
    if (!job) return;
    
    job.status = 'completed';
    job.completedAt = new Date().toISOString();
    job.resultsCount = results?.listings?.length || 0;
    
    console.log(`[AutoEngine] Job ${jobId} completed with ${job.resultsCount} results`);
    
    // Update session stats
    if (this.currentSession) {
      this.currentSession.stats.completed++;
      this.currentSession.stats.newListings += results?.newCount || 0;
      this.currentSession.stats.goodDeals += results?.goodDeals || 0;
    }
    
    // Clean up
    if (job.tabId) {
      try {
        await chrome.tabs.remove(job.tabId);
      } catch (e) {
        // Tab might already be closed
      }
    }
    
    this.activeJobs.delete(jobId);
    await this.saveSession();
    
    this.emit({
      type: 'job_completed',
      job,
      session: this.currentSession
    });
    
    // Process next job
    this.processQueue();
  }
  
  /**
   * Fail a job
   */
  private async failJob(jobId: string, error: string): Promise<void> {
    const job = this.activeJobs.get(jobId);
    if (!job) return;
    
    job.status = 'failed';
    job.completedAt = new Date().toISOString();
    job.error = error;
    
    console.error(`[AutoEngine] Job ${jobId} failed:`, error);
    
    // Update session stats
    if (this.currentSession) {
      this.currentSession.stats.failed++;
    }
    
    // Clean up
    if (job.tabId) {
      try {
        await chrome.tabs.remove(job.tabId);
      } catch (e) {
        // Tab might already be closed
      }
    }
    
    this.activeJobs.delete(jobId);
    await this.saveSession();
    
    this.emit({
      type: 'job_failed',
      job,
      session: this.currentSession
    });
    
    // Process next job
    this.processQueue();
  }
  
  /**
   * Handle tab removal
   */
  private handleTabRemoved(tabId: number): void {
    // Find job for this tab
    const job = Array.from(this.activeJobs.values()).find(j => j.tabId === tabId);
    if (job && job.status === 'running') {
      console.warn(`[AutoEngine] Tab closed for job ${job.id}`);
      this.failJob(job.id, 'Tab was closed');
    }
  }
  
  /**
   * Complete the session
   */
  private async completeSession(): Promise<void> {
    if (!this.currentSession) return;
    
    this.currentSession.completedAt = new Date().toISOString();
    this.isRunning = false;
    
    await this.saveSession();
    
    console.log('[AutoEngine] Session completed:', this.currentSession.stats);
    
    this.emit({
      type: 'session_completed',
      session: this.currentSession
    });
    
    // Show notification
    const settings = settingsManager.get();
    if (settings.notifications?.enabled && settings.notifications?.triggers?.autoScanComplete) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon-48.png',
        title: 'Auto Scan Complete',
        message: `Scanned ${this.currentSession.stats.completed} searches, found ${this.currentSession.stats.newListings} new listings`
      });
    }
  }
  
  /**
   * Save session to storage
   */
  private async saveSession(): Promise<void> {
    if (!this.currentSession) return;
    
    try {
      const { scanHistory = [] } = await chrome.storage.local.get(['scanHistory']);
      
      // Update or add session
      const index = scanHistory.findIndex((s: ScanSession) => s.id === this.currentSession!.id);
      if (index >= 0) {
        scanHistory[index] = this.currentSession;
      } else {
        scanHistory.unshift(this.currentSession);
      }
      
      // Keep last 50 sessions
      const trimmed = scanHistory.slice(0, 50);
      await chrome.storage.local.set({ scanHistory: trimmed });
      
    } catch (error) {
      console.error('[AutoEngine] Failed to save session:', error);
    }
  }
  
  /**
   * Get current session
   */
  getCurrentSession(): ScanSession | null {
    return this.currentSession;
  }
  
  /**
   * Get scan history
   */
  async getScanHistory(): Promise<ScanSession[]> {
    const { scanHistory = [] } = await chrome.storage.local.get(['scanHistory']);
    return scanHistory;
  }
  
  /**
   * Subscribe to events
   */
  subscribe(listener: (event: AutomationEvent) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  /**
   * Emit event
   */
  private emit(event: AutomationEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('[AutoEngine] Listener error:', error);
      }
    });
  }
  
  /**
   * Get engine status
   */
  getStatus(): EngineStatus {
    return {
      isRunning: this.isRunning,
      isPaused: this.isPaused,
      currentSession: this.currentSession,
      activeJobs: Array.from(this.activeJobs.values()),
      queueLength: this.jobQueue.length
    };
  }
}

// Event types
export type AutomationEvent = 
  | { type: 'session_started'; session: ScanSession }
  | { type: 'session_stopped'; session: ScanSession }
  | { type: 'session_completed'; session: ScanSession }
  | { type: 'session_paused'; session: ScanSession | null }
  | { type: 'session_resumed'; session: ScanSession | null }
  | { type: 'job_started'; job: ScanJob; session: ScanSession | null }
  | { type: 'job_completed'; job: ScanJob; session: ScanSession | null }
  | { type: 'job_failed'; job: ScanJob; session: ScanSession | null };

export interface EngineStatus {
  isRunning: boolean;
  isPaused: boolean;
  currentSession: ScanSession | null;
  activeJobs: ScanJob[];
  queueLength: number;
}

// Export singleton
export const automationEngine = AutomationEngine.getInstance();