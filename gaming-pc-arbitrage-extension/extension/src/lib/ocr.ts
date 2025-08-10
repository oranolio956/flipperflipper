/**
 * OCR Service Wrapper
 * Provides easy access to OCR functionality via web worker
 */

import * as Comlink from 'comlink';
import type { Remote } from 'comlink';
import { getSettings } from './settings';

interface OCRWorkerAPI {
  initialize(): Promise<void>;
  extractText(imageUrl: string): Promise<string>;
  extractTextFromMultiple(imageUrls: string[]): Promise<string[]>;
  extractSpecsFromImages(imageUrls: string[]): Promise<{
    cpu?: string;
    gpu?: string;
    ram?: string;
    storage?: string;
    psu?: string;
    motherboard?: string;
    rawText: string[];
  }>;
  terminate(): Promise<void>;
}

class OCRManager {
  private worker: Worker | null = null;
  private api: Remote<OCRWorkerAPI> | null = null;
  private initPromise: Promise<void> | null = null;
  private progressCallback?: (progress: number) => void;

  async initialize(): Promise<void> {
    if (this.api) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = this._doInitialize();
    await this.initPromise;
  }

  private async _doInitialize(): Promise<void> {
    try {
      // Check if OCR is enabled in settings
      const settings = await getSettings();
      if (!settings.features.ocr_photo_extractor) {
        throw new Error('OCR feature is disabled in settings');
      }

      // Create worker
      this.worker = new Worker(
        new URL('../workers/ocr.worker.ts', import.meta.url),
        { type: 'module' }
      );

      // Listen for progress updates
      this.worker.addEventListener('message', (event) => {
        if (event.data.type === 'progress' && this.progressCallback) {
          this.progressCallback(event.data.progress);
        }
      });

      // Wrap with Comlink
      this.api = Comlink.wrap<OCRWorkerAPI>(this.worker);

      // Initialize the worker
      await this.api.initialize();
    } catch (error) {
      console.error('Failed to initialize OCR manager:', error);
      this.cleanup();
      throw error;
    }
  }

  async extractTextFromImage(imageUrl: string): Promise<string> {
    await this.initialize();
    
    if (!this.api) {
      throw new Error('OCR service not initialized');
    }

    return await this.api.extractText(imageUrl);
  }

  async extractTextFromImages(imageUrls: string[]): Promise<string[]> {
    await this.initialize();
    
    if (!this.api) {
      throw new Error('OCR service not initialized');
    }

    return await this.api.extractTextFromMultiple(imageUrls);
  }

  async extractSpecsFromImages(imageUrls: string[]): Promise<{
    cpu?: string;
    gpu?: string;
    ram?: string;
    storage?: string;
    psu?: string;
    motherboard?: string;
    rawText: string[];
  }> {
    await this.initialize();
    
    if (!this.api) {
      throw new Error('OCR service not initialized');
    }

    return await this.api.extractSpecsFromImages(imageUrls);
  }

  setProgressCallback(callback: (progress: number) => void): void {
    this.progressCallback = callback;
  }

  async terminate(): Promise<void> {
    if (this.api) {
      await this.api.terminate();
    }
    this.cleanup();
  }

  private cleanup(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this.api = null;
    this.initPromise = null;
    this.progressCallback = undefined;
  }
}

// Singleton instance
let ocrManager: OCRManager | null = null;

export function getOCRManager(): OCRManager {
  if (!ocrManager) {
    ocrManager = new OCRManager();
  }
  return ocrManager;
}

// Convenience functions
export async function extractTextFromImage(imageUrl: string): Promise<string> {
  const manager = getOCRManager();
  return await manager.extractTextFromImage(imageUrl);
}

export async function extractTextFromImages(imageUrls: string[]): Promise<string[]> {
  const manager = getOCRManager();
  return await manager.extractTextFromImages(imageUrls);
}

export async function extractSpecsFromImages(imageUrls: string[]): Promise<{
  cpu?: string;
  gpu?: string;
  ram?: string;
  storage?: string;
  psu?: string;
  motherboard?: string;
  rawText: string[];
}> {
  const manager = getOCRManager();
  return await manager.extractSpecsFromImages(imageUrls);
}

export function setOCRProgressCallback(callback: (progress: number) => void): void {
  const manager = getOCRManager();
  manager.setProgressCallback(callback);
}