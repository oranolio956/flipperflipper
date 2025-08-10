/**
 * Tesseract.js OCR Implementation
 * Production-ready optical character recognition for PC specs extraction
 */

import { createWorker, Worker, RecognizeResult } from 'tesseract.js';
import { ComponentDetector } from '../../parsers/component-detector';
import { ExtractedSpecs, OCRResult } from '../../types';

export interface OCRConfig {
  languages: string[];
  workerPath?: string;
  corePath?: string;
  langPath?: string;
  cacheMethod?: 'refresh' | 'none' | 'rebuild';
  gzip?: boolean;
  logger?: (log: any) => void;
}

export interface OCRJobProgress {
  status: string;
  progress: number;
  jobId: string;
  userJobId?: string;
}

export class TesseractExtractor {
  private worker: Worker | null = null;
  private componentDetector: ComponentDetector;
  private config: OCRConfig;
  private isInitialized = false;
  private jobQueue: Map<string, (result: ExtractedSpecs) => void> = new Map();

  constructor(config?: Partial<OCRConfig>) {
    this.componentDetector = new ComponentDetector();
    this.config = {
      languages: ['eng'],
      cacheMethod: 'refresh',
      gzip: true,
      logger: (log) => {
        if (log.status === 'recognizing text') {
          const jobId = log.userJobId || 'unknown';
          const progress = log.progress || 0;
          this.onProgress({ status: log.status, progress, jobId });
        }
      },
      ...config
    };
  }

  /**
   * Initialize Tesseract worker
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.worker = await createWorker({
        workerPath: this.config.workerPath,
        corePath: this.config.corePath,
        langPath: this.config.langPath,
        cacheMethod: this.config.cacheMethod,
        gzip: this.config.gzip,
        logger: this.config.logger
      });

      await this.worker.loadLanguage(this.config.languages.join('+'));
      await this.worker.initialize(this.config.languages.join('+'));

      // Configure for better PC specs recognition
      await this.worker.setParameters({
        tessedit_char_whitelist: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .-/()[]{}:,@',
        preserve_interword_spaces: '1',
        tessedit_pageseg_mode: '11', // Sparse text mode
      });

      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize Tesseract:', error);
      throw new Error('OCR initialization failed');
    }
  }

  /**
   * Extract specs from an image URL
   */
  async extractFromImageUrl(imageUrl: string, jobId?: string): Promise<ExtractedSpecs> {
    await this.initialize();
    
    try {
      const result = await this.performOCR(imageUrl, jobId);
      return this.extractSpecsFromOCRResult(result);
    } catch (error) {
      console.error('OCR extraction failed:', error);
      throw error;
    }
  }

  /**
   * Extract specs from image data
   */
  async extractFromImageData(
    imageData: ImageData | HTMLImageElement | HTMLCanvasElement | File | Blob,
    jobId?: string
  ): Promise<ExtractedSpecs> {
    await this.initialize();
    
    try {
      const result = await this.performOCR(imageData, jobId);
      return this.extractSpecsFromOCRResult(result);
    } catch (error) {
      console.error('OCR extraction failed:', error);
      throw error;
    }
  }

  /**
   * Extract specs from multiple images (batch processing)
   */
  async extractFromMultipleImages(
    images: Array<string | ImageData | HTMLImageElement | File>,
    onProgress?: (completed: number, total: number) => void
  ): Promise<ExtractedSpecs> {
    await this.initialize();

    const allTexts: string[] = [];
    const allResults: OCRResult[] = [];

    for (let i = 0; i < images.length; i++) {
      try {
        const result = await this.performOCR(images[i], `batch-${i}`);
        allTexts.push(result.text);
        allResults.push(result);
        
        if (onProgress) {
          onProgress(i + 1, images.length);
        }
      } catch (error) {
        console.warn(`Failed to process image ${i}:`, error);
      }
    }

    // Combine all text and extract specs
    const combinedText = allTexts.join('\n');
    const combinedResult: OCRResult = {
      text: combinedText,
      confidence: allResults.reduce((sum, r) => sum + r.confidence, 0) / allResults.length,
      regions: allResults.flatMap(r => r.regions),
      metadata: {
        processingTime: allResults.reduce((sum, r) => sum + r.metadata.processingTime, 0),
        imageSize: { width: 0, height: 0 }, // Not applicable for batch
        language: this.config.languages[0]
      }
    };

    return this.extractSpecsFromOCRResult(combinedResult);
  }

  /**
   * Perform OCR on image
   */
  private async performOCR(
    image: string | ImageData | HTMLImageElement | HTMLCanvasElement | File | Blob,
    jobId?: string
  ): Promise<OCRResult> {
    if (!this.worker) {
      throw new Error('OCR worker not initialized');
    }

    const startTime = performance.now();

    try {
      // Preprocess image if needed
      const processedImage = await this.preprocessImage(image);
      
      // Perform OCR
      const result: RecognizeResult = await this.worker.recognize(processedImage, {
        rotateAuto: true,
        rotateRadians: 0
      }, {
        userJobId: jobId
      });

      const processingTime = performance.now() - startTime;

      // Convert to our OCR result format
      return {
        text: result.data.text,
        confidence: result.data.confidence,
        regions: result.data.words.map(word => ({
          text: word.text,
          confidence: word.confidence,
          boundingBox: {
            x: word.bbox.x0,
            y: word.bbox.y0,
            width: word.bbox.x1 - word.bbox.x0,
            height: word.bbox.y1 - word.bbox.y0
          }
        })),
        metadata: {
          processingTime,
          imageSize: {
            width: result.data.imageWidth || 0,
            height: result.data.imageHeight || 0
          },
          language: result.data.language || this.config.languages[0]
        }
      };
    } catch (error) {
      console.error('OCR processing failed:', error);
      throw error;
    }
  }

  /**
   * Extract PC specs from OCR result
   */
  private extractSpecsFromOCRResult(ocrResult: OCRResult): ExtractedSpecs {
    const text = ocrResult.text;
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);

    // Use component detector for structured extraction
    const components = this.componentDetector.detectAll(text);

    // Enhanced extraction with context awareness
    const specs: ExtractedSpecs = {
      cpu: components.cpu?.model || this.extractCPU(lines),
      gpu: components.gpu?.model || this.extractGPU(lines),
      ram: components.ram?.[0]?.capacity 
        ? `${components.ram[0].capacity}GB ${components.ram[0].type || 'DDR4'} ${components.ram[0].speed || ''}MHz`.trim()
        : this.extractRAM(lines),
      storage: [
        ...(components.storage?.map(s => 
          `${s.capacity}${s.capacity > 100 ? 'GB' : 'TB'} ${s.type}`
        ) || []),
        ...this.extractStorage(lines)
      ].filter((s, i, arr) => arr.indexOf(s) === i), // Remove duplicates
      motherboard: components.motherboard?.model || this.extractMotherboard(lines),
      psu: components.psu?.model || this.extractPSU(lines),
      confidence: ocrResult.confidence,
      rawText: ocrResult.text
    };

    // Calculate confidence based on how many components were found
    const foundComponents = Object.values(specs).filter(v => 
      v && v !== specs.rawText && (Array.isArray(v) ? v.length > 0 : true)
    ).length;
    
    specs.confidence = Math.min(
      ocrResult.confidence,
      (foundComponents / 6) // Normalize by expected component count
    );

    return specs;
  }

  /**
   * Enhanced component extraction methods
   */
  private extractCPU(lines: string[]): string | undefined {
    const cpuPatterns = [
      /(?:Intel|AMD|Ryzen|Core)\s*(?:Core\s*)?([i357]?\d?[-\s]?\d{4,5}[A-Z]?(?:\s*[KTX])?)/i,
      /Ryzen\s*([357])\s*(\d{4}[GXU]?)/i,
      /(?:CPU|Processor)[:\s]+([^,\n]+)/i
    ];

    for (const line of lines) {
      for (const pattern of cpuPatterns) {
        const match = line.match(pattern);
        if (match) {
          return this.cleanComponentName(match[0]);
        }
      }
    }
    return undefined;
  }

  private extractGPU(lines: string[]): string | undefined {
    const gpuPatterns = [
      /(?:NVIDIA|GeForce|RTX|GTX|Radeon|RX|AMD)\s*(?:GeForce\s*)?([A-Z]?[A-Z]?\s*\d{3,4}(?:\s*Ti)?(?:\s*Super)?)/i,
      /(?:GPU|Graphics|Video\s*Card)[:\s]+([^,\n]+)/i,
      /(\d{1,2}GB)\s*(?:GDDR\d|HBM\d?)/i
    ];

    for (const line of lines) {
      for (const pattern of gpuPatterns) {
        const match = line.match(pattern);
        if (match) {
          return this.cleanComponentName(match[0]);
        }
      }
    }
    return undefined;
  }

  private extractRAM(lines: string[]): string | undefined {
    const ramPatterns = [
      /(\d{1,3})\s*GB\s*(?:RAM|Memory|DDR\d)/i,
      /(?:RAM|Memory)[:\s]+(\d{1,3})\s*GB/i,
      /DDR(\d)\s*(\d{4,5})\s*(?:MHz)?\s*(\d{1,3})\s*GB/i
    ];

    for (const line of lines) {
      for (const pattern of ramPatterns) {
        const match = line.match(pattern);
        if (match) {
          return this.cleanComponentName(match[0]);
        }
      }
    }
    return undefined;
  }

  private extractStorage(lines: string[]): string[] {
    const storagePatterns = [
      /(\d+)\s*([GT]B)\s*(SSD|HDD|NVMe|M\.2|SATA)/i,
      /(?:Storage|Drive)[:\s]+([^,\n]+)/i,
      /(Samsung|WD|Western\s*Digital|Seagate|Kingston|Crucial)\s*\d+\s*[GT]B/i
    ];

    const storage: string[] = [];
    for (const line of lines) {
      for (const pattern of storagePatterns) {
        const match = line.match(pattern);
        if (match && !storage.some(s => s.includes(match[0]))) {
          storage.push(this.cleanComponentName(match[0]));
        }
      }
    }
    return storage;
  }

  private extractMotherboard(lines: string[]): string | undefined {
    const moboPatterns = [
      /(ASUS|MSI|Gigabyte|ASRock|EVGA)\s*[A-Z0-9\-]+/i,
      /(?:Motherboard|Mobo|MB)[:\s]+([^,\n]+)/i,
      /(B\d{3}|X\d{3}|Z\d{3}|H\d{3})\s*[A-Z0-9\-]*/i
    ];

    for (const line of lines) {
      for (const pattern of moboPatterns) {
        const match = line.match(pattern);
        if (match) {
          return this.cleanComponentName(match[0]);
        }
      }
    }
    return undefined;
  }

  private extractPSU(lines: string[]): string | undefined {
    const psuPatterns = [
      /(\d{3,4})\s*W(?:att)?\s*(?:PSU|Power|Supply)/i,
      /(?:PSU|Power\s*Supply)[:\s]+([^,\n]+)/i,
      /(Corsair|EVGA|Seasonic|Thermaltake)\s*\d{3,4}\s*W/i,
      /80\+\s*(Bronze|Silver|Gold|Platinum|Titanium)/i
    ];

    for (const line of lines) {
      for (const pattern of psuPatterns) {
        const match = line.match(pattern);
        if (match) {
          return this.cleanComponentName(match[0]);
        }
      }
    }
    return undefined;
  }

  /**
   * Preprocess image for better OCR results
   */
  private async preprocessImage(
    image: string | ImageData | HTMLImageElement | HTMLCanvasElement | File | Blob
  ): Promise<string | ImageData | HTMLCanvasElement> {
    // If it's already a string URL or simple format, return as is
    if (typeof image === 'string' || image instanceof ImageData) {
      return image;
    }

    // Convert File/Blob to canvas for preprocessing
    if (image instanceof File || image instanceof Blob) {
      const bitmap = await createImageBitmap(image);
      const canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(bitmap, 0, 0);
      image = canvas;
    }

    // Apply preprocessing if it's an image element or canvas
    if (image instanceof HTMLImageElement || image instanceof HTMLCanvasElement) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      
      // Set canvas size
      if (image instanceof HTMLImageElement) {
        canvas.width = image.naturalWidth || image.width;
        canvas.height = image.naturalHeight || image.height;
      } else {
        canvas.width = image.width;
        canvas.height = image.height;
      }

      // Draw original image
      ctx.drawImage(image, 0, 0);

      // Apply filters for better OCR
      ctx.filter = 'contrast(1.5) brightness(1.1) grayscale(1)';
      ctx.drawImage(canvas, 0, 0);

      // Sharpen the image
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      this.sharpenImage(imageData);
      ctx.putImageData(imageData, 0, 0);

      return canvas;
    }

    return image;
  }

  /**
   * Apply sharpening filter to image data
   */
  private sharpenImage(imageData: ImageData): void {
    const weights = [
      0, -1, 0,
      -1, 5, -1,
      0, -1, 0
    ];
    
    const side = Math.round(Math.sqrt(weights.length));
    const halfSide = Math.floor(side / 2);
    const src = imageData.data;
    const sw = imageData.width;
    const sh = imageData.height;
    const w = sw;
    const h = sh;
    const output = new Uint8ClampedArray(src);

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const dstOff = (y * w + x) * 4;
        let r = 0, g = 0, b = 0;
        
        for (let cy = 0; cy < side; cy++) {
          for (let cx = 0; cx < side; cx++) {
            const scy = y + cy - halfSide;
            const scx = x + cx - halfSide;
            
            if (scy >= 0 && scy < sh && scx >= 0 && scx < sw) {
              const srcOff = (scy * sw + scx) * 4;
              const wt = weights[cy * side + cx];
              r += src[srcOff] * wt;
              g += src[srcOff + 1] * wt;
              b += src[srcOff + 2] * wt;
            }
          }
        }
        
        output[dstOff] = r;
        output[dstOff + 1] = g;
        output[dstOff + 2] = b;
      }
    }

    // Copy output back to image data
    for (let i = 0; i < src.length; i++) {
      src[i] = output[i];
    }
  }

  /**
   * Clean component name
   */
  private cleanComponentName(name: string): string {
    return name
      .replace(/[:\-–—]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Progress callback
   */
  private onProgress(progress: OCRJobProgress): void {
    // Can be overridden or emit events
    console.log(`OCR Progress: ${progress.jobId} - ${Math.round(progress.progress * 100)}%`);
  }

  /**
   * Terminate worker
   */
  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
      this.isInitialized = false;
    }
  }

  /**
   * Extract text regions that likely contain specs
   */
  async extractSpecRegions(
    image: string | ImageData | HTMLImageElement | File
  ): Promise<Array<{ text: string; boundingBox: any; confidence: number }>> {
    await this.initialize();

    const result = await this.performOCR(image);
    
    // Filter regions that likely contain PC specs
    const specKeywords = [
      'cpu', 'processor', 'gpu', 'graphics', 'ram', 'memory', 
      'storage', 'ssd', 'hdd', 'motherboard', 'psu', 'power',
      'intel', 'amd', 'nvidia', 'ryzen', 'core', 'geforce',
      'rtx', 'gtx', 'ddr', 'gb', 'tb', 'ghz', 'mhz'
    ];

    return result.regions.filter(region => {
      const textLower = region.text.toLowerCase();
      return specKeywords.some(keyword => textLower.includes(keyword));
    });
  }

  /**
   * Confidence-based extraction with multiple attempts
   */
  async extractWithConfidence(
    image: string | ImageData | HTMLImageElement | File,
    minConfidence: number = 0.7,
    maxAttempts: number = 3
  ): Promise<ExtractedSpecs> {
    let bestResult: ExtractedSpecs | null = null;
    let bestConfidence = 0;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        // Apply different preprocessing on each attempt
        const processedImage = await this.applyAdaptivePreprocessing(image, attempt);
        const result = await this.extractFromImageData(processedImage);

        if (result.confidence > bestConfidence) {
          bestConfidence = result.confidence;
          bestResult = result;
        }

        if (result.confidence >= minConfidence) {
          return result;
        }
      } catch (error) {
        console.warn(`Extraction attempt ${attempt + 1} failed:`, error);
      }
    }

    if (!bestResult) {
      throw new Error('All extraction attempts failed');
    }

    return bestResult;
  }

  /**
   * Apply different preprocessing strategies
   */
  private async applyAdaptivePreprocessing(
    image: string | ImageData | HTMLImageElement | File,
    strategy: number
  ): Promise<HTMLCanvasElement> {
    // Convert to canvas first
    let canvas: HTMLCanvasElement;
    
    if (typeof image === 'string') {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = image;
      });
      canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(img, 0, 0);
    } else if (image instanceof File) {
      const bitmap = await createImageBitmap(image);
      canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(bitmap, 0, 0);
    } else if (image instanceof HTMLImageElement) {
      canvas = document.createElement('canvas');
      canvas.width = image.naturalWidth || image.width;
      canvas.height = image.naturalHeight || image.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(image, 0, 0);
    } else if (image instanceof ImageData) {
      canvas = document.createElement('canvas');
      canvas.width = image.width;
      canvas.height = image.height;
      const ctx = canvas.getContext('2d')!;
      ctx.putImageData(image, 0, 0);
    } else {
      throw new Error('Unsupported image type');
    }

    const ctx = canvas.getContext('2d')!;

    // Apply different strategies
    switch (strategy) {
      case 0:
        // Standard preprocessing
        ctx.filter = 'contrast(1.5) brightness(1.1) grayscale(1)';
        break;
      case 1:
        // High contrast for faded text
        ctx.filter = 'contrast(2) brightness(1.2) grayscale(1) invert(1)';
        break;
      case 2:
        // Enhance dark images
        ctx.filter = 'brightness(1.5) contrast(1.8) grayscale(1)';
        break;
    }

    ctx.drawImage(canvas, 0, 0);
    return canvas;
  }
}

// Export singleton for easy use
export const tesseractExtractor = new TesseractExtractor();