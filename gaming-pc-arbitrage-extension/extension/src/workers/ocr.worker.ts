/**
 * OCR Web Worker
 * Extracts text from images using Tesseract.js
 */

import { createWorker, Worker as TesseractWorker } from 'tesseract.js';
import * as Comlink from 'comlink';

class OCRService {
  private worker: TesseractWorker | null = null;
  private isInitialized = false;
  private initPromise: Promise<void> | null = null;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = this._doInitialize();
    await this.initPromise;
  }

  private async _doInitialize(): Promise<void> {
    try {
      console.log('Initializing OCR worker...');
      
      this.worker = await createWorker({
        logger: (m) => {
          if (m.status === 'recognizing text') {
            self.postMessage({
              type: 'progress',
              progress: m.progress,
            });
          }
        },
        errorHandler: (err) => {
          console.error('Tesseract error:', err);
        },
      });

      await this.worker.loadLanguage('eng');
      await this.worker.initialize('eng');
      
      // Set recognition parameters for better accuracy
      await this.worker.setParameters({
        tessedit_char_whitelist: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -.,()/$',
        preserve_interword_spaces: '1',
      });

      this.isInitialized = true;
      console.log('OCR worker initialized successfully');
    } catch (error) {
      console.error('Failed to initialize OCR worker:', error);
      throw error;
    }
  }

  async extractText(imageUrl: string): Promise<string> {
    await this.initialize();
    
    if (!this.worker) {
      throw new Error('OCR worker not initialized');
    }

    try {
      console.log('Extracting text from:', imageUrl);
      
      // Download image first to handle CORS
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      
      const { data: { text } } = await this.worker.recognize(blob);
      
      // Clean up the text
      const cleanedText = this.cleanText(text);
      console.log('Extracted text:', cleanedText);
      
      return cleanedText;
    } catch (error) {
      console.error('OCR extraction failed:', error);
      throw error;
    }
  }

  async extractTextFromMultiple(imageUrls: string[]): Promise<string[]> {
    const results: string[] = [];
    
    for (const url of imageUrls) {
      try {
        const text = await this.extractText(url);
        results.push(text);
      } catch (error) {
        console.warn(`Failed to extract text from ${url}:`, error);
        results.push('');
      }
    }
    
    return results;
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
    const texts = await this.extractTextFromMultiple(imageUrls);
    const combinedText = texts.join('\n');
    
    // Extract specific components using patterns
    const specs = {
      cpu: this.extractCPU(combinedText),
      gpu: this.extractGPU(combinedText),
      ram: this.extractRAM(combinedText),
      storage: this.extractStorage(combinedText),
      psu: this.extractPSU(combinedText),
      motherboard: this.extractMotherboard(combinedText),
      rawText: texts,
    };
    
    return specs;
  }

  private cleanText(text: string): string {
    return text
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/[^\x20-\x7E]/g, '') // Remove non-ASCII
      .trim();
  }

  private extractCPU(text: string): string | undefined {
    // Intel patterns
    const intelPatterns = [
      /i[357]-?\d{4,5}[A-Z]*/gi,
      /Core\s+i[357]\s+\d{4,5}/gi,
      /Intel.*?i[357].*?\d{4}/gi,
    ];
    
    // AMD patterns
    const amdPatterns = [
      /Ryzen\s+[357]\s+\d{4}[A-Z]*/gi,
      /AMD\s+Ryzen.*?\d{4}/gi,
      /R[357]\s+\d{4}[A-Z]*/gi,
    ];
    
    for (const pattern of [...intelPatterns, ...amdPatterns]) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  private extractGPU(text: string): string | undefined {
    // NVIDIA patterns
    const nvidiaPatterns = [
      /RTX\s*\d{4}\s*(Ti|SUPER)?/gi,
      /GTX\s*\d{4}\s*(Ti|SUPER)?/gi,
      /GeForce.*?\d{4}/gi,
    ];
    
    // AMD patterns
    const amdPatterns = [
      /RX\s*\d{4}\s*(XT)?/gi,
      /Radeon.*?\d{4}/gi,
    ];
    
    for (const pattern of [...nvidiaPatterns, ...amdPatterns]) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  private extractRAM(text: string): string | undefined {
    const patterns = [
      /\d{1,2}\s*GB\s*(?:DDR[345]|RAM)/gi,
      /\d{1,2}GB.*?(?:Memory|RAM)/gi,
      /DDR[345].*?\d{1,2}\s*GB/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  private extractStorage(text: string): string | undefined {
    const patterns = [
      /\d+\s*(?:GB|TB)\s*(?:SSD|HDD|NVMe|M\.2)/gi,
      /(?:SSD|HDD|NVMe|M\.2).*?\d+\s*(?:GB|TB)/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  private extractPSU(text: string): string | undefined {
    const patterns = [
      /\d{3,4}\s*W(?:att)?(?:\s+PSU)?/gi,
      /\d{3,4}W.*?(?:Gold|Bronze|Platinum)/gi,
      /Power\s+Supply.*?\d{3,4}W/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  private extractMotherboard(text: string): string | undefined {
    const patterns = [
      /(?:B\d{3}|X\d{3}|Z\d{3}|H\d{3})\s*[A-Z0-9\-]+/gi,
      /(?:MSI|ASUS|Gigabyte|ASRock).*?(?:B\d{3}|X\d{3}|Z\d{3})/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }

  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
      this.isInitialized = false;
    }
  }
}

// Expose the service via Comlink
const ocrService = new OCRService();
Comlink.expose(ocrService);