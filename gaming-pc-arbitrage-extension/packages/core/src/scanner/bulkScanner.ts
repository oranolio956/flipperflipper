/**
 * Bulk URL Scanner
 * Batch processing system for scanning multiple marketplace listings
 */

import { MarketplaceParser } from '../parsers/marketplace';
import { ComponentDetector } from '../parsers/component-detector';
import { FMVCalculator } from '../valuation/fmv';
import { RiskEngine } from '../risk/engine';
import { Listing } from '../types';

export interface ScanJob {
  id: string;
  urls: string[];
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total: number;
    processed: number;
    successful: number;
    failed: number;
  };
  results: ScanResult[];
  options: ScanOptions;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

export interface ScanResult {
  url: string;
  status: 'success' | 'failed' | 'skipped';
  listing?: Listing;
  analysis?: ListingAnalysis;
  error?: string;
  processingTime: number;
}

export interface ListingAnalysis {
  fmv: number;
  suggestedOffer: number;
  roi: number;
  roiPercentage: number;
  dealQuality: 'excellent' | 'good' | 'fair' | 'poor';
  risks: any[];
  opportunities: string[];
}

export interface ScanOptions {
  parallel: boolean;
  maxConcurrent: number;
  timeout: number; // ms per URL
  retryFailed: boolean;
  analyzeComponents: boolean;
  calculateROI: boolean;
  checkRisks: boolean;
  filters?: ScanFilters;
}

export interface ScanFilters {
  minPrice?: number;
  maxPrice?: number;
  platforms?: string[];
  mustHaveGPU?: boolean;
  minROI?: number;
  excludeKeywords?: string[];
}

export interface ScanProgress {
  jobId: string;
  current: number;
  total: number;
  currentUrl?: string;
  status: string;
}

export class BulkScanner {
  private jobs: Map<string, ScanJob> = new Map();
  private activeScans: Map<string, AbortController> = new Map();
  private parser: MarketplaceParser;
  private detector: ComponentDetector;
  private fmvCalculator: FMVCalculator;
  private riskEngine: RiskEngine;
  private progressCallbacks: Map<string, (progress: ScanProgress) => void> = new Map();
  private readonly STORAGE_KEY = 'bulkScanJobs';

  constructor() {
    this.parser = new MarketplaceParser();
    this.detector = new ComponentDetector();
    this.fmvCalculator = new FMVCalculator();
    this.riskEngine = new RiskEngine();
    this.loadJobs();
  }

  /**
   * Create a new bulk scan job
   */
  async createScanJob(
    urls: string[],
    options?: Partial<ScanOptions>
  ): Promise<ScanJob> {
    const job: ScanJob = {
      id: `scan_${Date.now()}`,
      urls: this.deduplicateUrls(urls),
      status: 'pending',
      progress: {
        total: urls.length,
        processed: 0,
        successful: 0,
        failed: 0
      },
      results: [],
      options: {
        parallel: true,
        maxConcurrent: 3,
        timeout: 30000,
        retryFailed: true,
        analyzeComponents: true,
        calculateROI: true,
        checkRisks: true,
        ...options
      },
      createdAt: new Date()
    };

    this.jobs.set(job.id, job);
    await this.saveJobs();

    return job;
  }

  /**
   * Start scanning a job
   */
  async startScan(
    jobId: string,
    progressCallback?: (progress: ScanProgress) => void
  ): Promise<ScanJob> {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error('Job not found');
    if (job.status !== 'pending') throw new Error('Job already started');

    if (progressCallback) {
      this.progressCallbacks.set(jobId, progressCallback);
    }

    job.status = 'running';
    job.startedAt = new Date();
    await this.saveJobs();

    // Create abort controller for cancellation
    const abortController = new AbortController();
    this.activeScans.set(jobId, abortController);

    try {
      if (job.options.parallel) {
        await this.scanParallel(job, abortController.signal);
      } else {
        await this.scanSequential(job, abortController.signal);
      }

      job.status = 'completed';
    } catch (error) {
      job.status = 'failed';
      job.error = error instanceof Error ? error.message : 'Unknown error';
    } finally {
      job.completedAt = new Date();
      this.activeScans.delete(jobId);
      this.progressCallbacks.delete(jobId);
      await this.saveJobs();
    }

    return job;
  }

  /**
   * Cancel a running scan
   */
  async cancelScan(jobId: string): Promise<void> {
    const controller = this.activeScans.get(jobId);
    if (controller) {
      controller.abort();
    }

    const job = this.jobs.get(jobId);
    if (job && job.status === 'running') {
      job.status = 'cancelled';
      job.completedAt = new Date();
      await this.saveJobs();
    }
  }

  /**
   * Scan URLs in parallel
   */
  private async scanParallel(job: ScanJob, signal: AbortSignal): Promise<void> {
    const { maxConcurrent } = job.options;
    const chunks = this.chunkArray(job.urls, maxConcurrent);

    for (const chunk of chunks) {
      if (signal.aborted) break;

      const promises = chunk.map(url => this.scanSingleUrl(job, url, signal));
      await Promise.allSettled(promises);
    }
  }

  /**
   * Scan URLs sequentially
   */
  private async scanSequential(job: ScanJob, signal: AbortSignal): Promise<void> {
    for (const url of job.urls) {
      if (signal.aborted) break;
      await this.scanSingleUrl(job, url, signal);
    }
  }

  /**
   * Scan a single URL
   */
  private async scanSingleUrl(
    job: ScanJob,
    url: string,
    signal: AbortSignal
  ): Promise<void> {
    const startTime = Date.now();
    this.emitProgress(job, url);

    try {
      // Check abort signal
      if (signal.aborted) {
        throw new Error('Scan cancelled');
      }

      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Timeout')), job.options.timeout);
      });

      // Parse listing with timeout
      const listing = await Promise.race([
        this.parser.parse(url),
        timeoutPromise
      ]) as Listing;

      // Apply filters
      if (!this.passesFilters(listing, job.options.filters)) {
        job.results.push({
          url,
          status: 'skipped',
          processingTime: Date.now() - startTime
        });
        job.progress.processed++;
        this.emitProgress(job);
        return;
      }

      // Analyze listing
      let analysis: ListingAnalysis | undefined;
      if (job.options.analyzeComponents || job.options.calculateROI || job.options.checkRisks) {
        analysis = await this.analyzeListing(listing, job.options);
      }

      // Store result
      job.results.push({
        url,
        status: 'success',
        listing,
        analysis,
        processingTime: Date.now() - startTime
      });

      job.progress.processed++;
      job.progress.successful++;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      job.results.push({
        url,
        status: 'failed',
        error: errorMessage,
        processingTime: Date.now() - startTime
      });

      job.progress.processed++;
      job.progress.failed++;

      // Retry if enabled and not cancelled
      if (job.options.retryFailed && !signal.aborted && errorMessage !== 'Scan cancelled') {
        await this.delay(2000); // Wait 2 seconds before retry
        await this.scanSingleUrl(job, url, signal); // Recursive retry
        return;
      }
    }

    this.emitProgress(job);
    await this.saveJobs();
  }

  /**
   * Analyze a listing
   */
  private async analyzeListing(
    listing: Listing,
    options: ScanOptions
  ): Promise<ListingAnalysis> {
    const analysis: Partial<ListingAnalysis> = {};

    // Detect components
    if (options.analyzeComponents && !listing.components) {
      const components = await this.detector.detectAllComponents(
        `${listing.title} ${listing.description}`
      );
      listing.components = components;
    }

    // Calculate FMV and ROI
    if (options.calculateROI) {
      const fmv = this.fmvCalculator.calculate(listing);
      const suggestedOffer = Math.round(fmv * 0.7); // 70% of FMV
      const roi = fmv - suggestedOffer;
      const roiPercentage = (roi / suggestedOffer) * 100;

      analysis.fmv = fmv;
      analysis.suggestedOffer = suggestedOffer;
      analysis.roi = roi;
      analysis.roiPercentage = roiPercentage;

      // Determine deal quality
      if (roiPercentage > 50) analysis.dealQuality = 'excellent';
      else if (roiPercentage > 30) analysis.dealQuality = 'good';
      else if (roiPercentage > 15) analysis.dealQuality = 'fair';
      else analysis.dealQuality = 'poor';
    }

    // Check risks
    if (options.checkRisks) {
      const risks = await this.riskEngine.assessRisks(listing);
      analysis.risks = risks;
    }

    // Identify opportunities
    analysis.opportunities = this.identifyOpportunities(listing, analysis);

    return analysis as ListingAnalysis;
  }

  /**
   * Check if listing passes filters
   */
  private passesFilters(listing: Listing, filters?: ScanFilters): boolean {
    if (!filters) return true;

    if (filters.minPrice && listing.price < filters.minPrice) return false;
    if (filters.maxPrice && listing.price > filters.maxPrice) return false;
    
    if (filters.platforms && !filters.platforms.includes(listing.platform)) {
      return false;
    }

    if (filters.mustHaveGPU && !listing.components?.gpu) return false;

    if (filters.excludeKeywords) {
      const text = `${listing.title} ${listing.description}`.toLowerCase();
      for (const keyword of filters.excludeKeywords) {
        if (text.includes(keyword.toLowerCase())) return false;
      }
    }

    return true;
  }

  /**
   * Identify opportunities in a listing
   */
  private identifyOpportunities(
    listing: Listing,
    analysis: Partial<ListingAnalysis>
  ): string[] {
    const opportunities: string[] = [];

    // Price opportunities
    if (analysis.roiPercentage && analysis.roiPercentage > 40) {
      opportunities.push('High profit margin potential');
    }

    if (listing.price < 500 && listing.components?.gpu) {
      opportunities.push('Underpriced GPU system');
    }

    // Component opportunities
    if (listing.components?.gpu?.model.match(/RTX|3060|3070|3080|3090|4060|4070|4080|4090/i)) {
      opportunities.push('High-demand GPU model');
    }

    if (listing.components?.cpu?.model.match(/i9|Ryzen 9/i)) {
      opportunities.push('High-end CPU included');
    }

    // Seller opportunities
    if (listing.seller.responseRate && listing.seller.responseRate > 0.8) {
      opportunities.push('Responsive seller');
    }

    // Timing opportunities
    const listingAge = (Date.now() - listing.postedAt.getTime()) / (1000 * 60 * 60 * 24);
    if (listingAge > 14) {
      opportunities.push('Aged listing - seller may be motivated');
    }

    return opportunities;
  }

  /**
   * Get scan results summary
   */
  getScanSummary(jobId: string): {
    totalDeals: number;
    excellentDeals: number;
    goodDeals: number;
    totalROI: number;
    avgROI: number;
    topDeals: ScanResult[];
  } | null {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    const successfulResults = job.results.filter(r => r.status === 'success' && r.analysis);
    
    const excellentDeals = successfulResults.filter(
      r => r.analysis?.dealQuality === 'excellent'
    ).length;
    
    const goodDeals = successfulResults.filter(
      r => r.analysis?.dealQuality === 'good'
    ).length;

    const totalROI = successfulResults.reduce(
      (sum, r) => sum + (r.analysis?.roi || 0),
      0
    );

    const avgROI = successfulResults.length > 0 
      ? totalROI / successfulResults.length 
      : 0;

    const topDeals = [...successfulResults]
      .sort((a, b) => (b.analysis?.roi || 0) - (a.analysis?.roi || 0))
      .slice(0, 10);

    return {
      totalDeals: successfulResults.length,
      excellentDeals,
      goodDeals,
      totalROI,
      avgROI,
      topDeals
    };
  }

  /**
   * Export scan results
   */
  exportResults(jobId: string, format: 'json' | 'csv' = 'json'): string {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error('Job not found');

    if (format === 'json') {
      return JSON.stringify(job.results, null, 2);
    }

    // CSV export
    const headers = [
      'URL',
      'Status',
      'Title',
      'Price',
      'Platform',
      'FMV',
      'Suggested Offer',
      'ROI',
      'ROI %',
      'Deal Quality',
      'Risks',
      'Opportunities'
    ];

    const rows = job.results.map(result => {
      if (result.status !== 'success') {
        return [result.url, result.status, '', '', '', '', '', '', '', '', result.error || '', ''];
      }

      const listing = result.listing!;
      const analysis = result.analysis;

      return [
        result.url,
        result.status,
        listing.title,
        listing.price,
        listing.platform,
        analysis?.fmv || '',
        analysis?.suggestedOffer || '',
        analysis?.roi || '',
        analysis?.roiPercentage?.toFixed(1) || '',
        analysis?.dealQuality || '',
        analysis?.risks?.length || 0,
        analysis?.opportunities?.join('; ') || ''
      ];
    });

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    return csv;
  }

  /**
   * Get URLs from various sources
   */
  async extractUrlsFromText(text: string): string[] {
    const urlRegex = /https?:\/\/(www\.)?(facebook\.com\/marketplace|craigslist\.org|offerup\.com)[^\s<>"{}|\\^`\[\]]+/gi;
    const matches = text.match(urlRegex) || [];
    return this.deduplicateUrls(matches);
  }

  /**
   * Import URLs from file
   */
  async importUrlsFromFile(file: File): Promise<string[]> {
    const text = await file.text();
    
    if (file.type === 'application/json') {
      try {
        const data = JSON.parse(text);
        if (Array.isArray(data)) {
          return this.deduplicateUrls(data.filter(item => typeof item === 'string'));
        }
      } catch (error) {
        console.error('Invalid JSON file');
      }
    }

    // Try to extract URLs from text
    return this.extractUrlsFromText(text);
  }

  /**
   * Utility methods
   */
  private deduplicateUrls(urls: string[]): string[] {
    const normalized = urls.map(url => {
      try {
        const parsed = new URL(url);
        // Remove tracking parameters
        parsed.searchParams.delete('fbclid');
        parsed.searchParams.delete('utm_source');
        parsed.searchParams.delete('utm_medium');
        parsed.searchParams.delete('utm_campaign');
        return parsed.toString();
      } catch {
        return url;
      }
    });

    return [...new Set(normalized)];
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private emitProgress(job: ScanJob, currentUrl?: string): void {
    const callback = this.progressCallbacks.get(job.id);
    if (callback) {
      callback({
        jobId: job.id,
        current: job.progress.processed,
        total: job.progress.total,
        currentUrl,
        status: `Processing ${job.progress.processed}/${job.progress.total}`
      });
    }
  }

  /**
   * Persistence methods
   */
  private async loadJobs(): Promise<void> {
    const { [this.STORAGE_KEY]: saved } = await chrome.storage.local.get(this.STORAGE_KEY);
    if (saved) {
      Object.entries(saved).forEach(([id, data]: [string, any]) => {
        this.jobs.set(id, {
          ...data,
          createdAt: new Date(data.createdAt),
          startedAt: data.startedAt ? new Date(data.startedAt) : undefined,
          completedAt: data.completedAt ? new Date(data.completedAt) : undefined
        });
      });
    }
  }

  private async saveJobs(): Promise<void> {
    const data: Record<string, any> = {};
    this.jobs.forEach((job, id) => {
      data[id] = {
        ...job,
        createdAt: job.createdAt.toISOString(),
        startedAt: job.startedAt?.toISOString(),
        completedAt: job.completedAt?.toISOString()
      };
    });
    await chrome.storage.local.set({ [this.STORAGE_KEY]: data });
  }

  /**
   * Get all jobs
   */
  getAllJobs(): ScanJob[] {
    return Array.from(this.jobs.values())
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  /**
   * Get job by ID
   */
  getJob(jobId: string): ScanJob | undefined {
    return this.jobs.get(jobId);
  }

  /**
   * Delete a job
   */
  async deleteJob(jobId: string): Promise<void> {
    // Cancel if running
    await this.cancelScan(jobId);
    
    this.jobs.delete(jobId);
    await this.saveJobs();
  }
}

// Export singleton instance
export const bulkScanner = new BulkScanner();