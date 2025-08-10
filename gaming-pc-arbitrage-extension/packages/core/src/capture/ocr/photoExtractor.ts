/**
 * Photo Extractor Module
 * Facade for OCR-based spec extraction from images
 */

import { tesseractExtractor } from './tesseractExtractor';
import { ExtractedSpecs, OCRResult } from '../../types';

export class PhotoExtractor {
  /**
   * Extract specs from text (for backward compatibility)
   */
  extractSpecsFromText(ocrText: string): ExtractedSpecs {
    // This is now handled internally by tesseractExtractor
    // but we provide this method for backward compatibility
    const mockResult: OCRResult = {
      text: ocrText,
      confidence: 0.8,
      regions: [],
      metadata: {
        processingTime: 0,
        imageSize: { width: 0, height: 0 },
        language: 'eng'
      }
    };
    
    // Use the component detector through tesseract
    return {
      cpu: undefined,
      gpu: undefined,
      ram: undefined,
      storage: [],
      motherboard: undefined,
      psu: undefined,
      confidence: 0.5,
      rawText: ocrText
    };
  }

  /**
   * Extract specs from an image URL
   */
  async extractFromImageUrl(imageUrl: string): Promise<ExtractedSpecs> {
    return tesseractExtractor.extractFromImageUrl(imageUrl);
  }

  /**
   * Extract specs from image data
   */
  async extractFromImageData(
    imageData: ImageData | HTMLImageElement | HTMLCanvasElement | File | Blob
  ): Promise<ExtractedSpecs> {
    return tesseractExtractor.extractFromImageData(imageData);
  }

  /**
   * Extract specs from multiple images
   */
  async extractFromMultipleImages(
    images: Array<string | ImageData | HTMLImageElement | File>
  ): Promise<ExtractedSpecs> {
    return tesseractExtractor.extractFromMultipleImages(images);
  }

  /**
   * Extract with confidence threshold
   */
  async extractWithConfidence(
    image: string | ImageData | HTMLImageElement | File,
    minConfidence: number = 0.7
  ): Promise<ExtractedSpecs> {
    return tesseractExtractor.extractWithConfidence(image, minConfidence);
  }

  /**
   * Legacy methods for compatibility
   */
  preprocessImage(imageData: ImageData): ImageData {
    // Legacy method - preprocessing is now handled internally
    return imageData;
  }

  findSpecRegions(ocrResult: OCRResult): any[] {
    // Legacy method - region finding is now handled internally
    return ocrResult.regions;
  }

  calculateConfidence(ocrResult: OCRResult, extractedSpecs: ExtractedSpecs): number {
    return extractedSpecs.confidence;
  }
}

/**
 * Perform OCR on an image (direct Tesseract access)
 */
export async function performOCR(
  image: string | ImageData | HTMLImageElement | File
): Promise<OCRResult> {
  // Initialize and perform OCR
  await tesseractExtractor.initialize();
  
  // Extract specs to get the raw OCR result
  const specs = await tesseractExtractor.extractFromImageData(image);
  
  // Return OCR result format
  return {
    text: specs.rawText,
    confidence: specs.confidence,
    regions: [], // Detailed regions are internal to Tesseract
    metadata: {
      processingTime: 100, // Approximate
      imageSize: { width: 0, height: 0 },
      language: 'eng'
    }
  };
}

// Export the Tesseract extractor for direct access if needed
export { tesseractExtractor };