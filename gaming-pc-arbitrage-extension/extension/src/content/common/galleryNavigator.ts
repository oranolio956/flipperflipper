/**
 * Gallery Navigator
 * User-initiated photo gallery scanner
 */

export interface GalleryPhoto {
  url: string;
  index: number;
  caption?: string;
}

export interface GalleryProgress {
  current: number;
  total: number;
  photos: GalleryPhoto[];
}

type ProgressCallback = (progress: GalleryProgress) => void;

/**
 * Scan all photos in gallery
 */
export async function scanGallery(
  onProgress?: ProgressCallback
): Promise<GalleryPhoto[]> {
  const photos: GalleryPhoto[] = [];
  
  // Find gallery container
  const gallery = findGalleryContainer();
  if (!gallery) {
    throw new Error('No photo gallery found');
  }
  
  // Get total count
  const totalPhotos = getTotalPhotoCount(gallery);
  if (totalPhotos === 0) {
    return photos;
  }
  
  // Scan each photo
  for (let i = 0; i < totalPhotos; i++) {
    // Navigate to photo
    await navigateToPhoto(gallery, i);
    
    // Extract photo data
    const photo = await extractCurrentPhoto(i);
    if (photo) {
      photos.push(photo);
    }
    
    // Report progress
    if (onProgress) {
      onProgress({
        current: i + 1,
        total: totalPhotos,
        photos: [...photos],
      });
    }
    
    // Add delay to avoid detection
    await delay(500 + Math.random() * 500);
  }
  
  return photos;
}

/**
 * Find gallery container element
 */
function findGalleryContainer(): Element | null {
  // Facebook selectors
  const selectors = [
    '[role="dialog"] [role="img"]',
    '[data-pagelet="MediaViewerPhoto"]',
    'div[style*="transform"]',
  ];
  
  for (const selector of selectors) {
    const container = document.querySelector(selector);
    if (container) {
      return container.closest('[role="dialog"]') || container;
    }
  }
  
  // Craigslist
  const clGallery = document.querySelector('.gallery');
  if (clGallery) return clGallery;
  
  // OfferUp
  const ouGallery = document.querySelector('[data-testid="item-image-carousel"]');
  if (ouGallery) return ouGallery;
  
  return null;
}

/**
 * Get total photo count
 */
function getTotalPhotoCount(gallery: Element): number {
  // Look for indicators
  const indicators = gallery.querySelectorAll(
    '.carousel-indicator, [role="button"][aria-label*="photo"], .thumb'
  );
  if (indicators.length > 0) {
    return indicators.length;
  }
  
  // Look for text like "1 of 5"
  const text = gallery.textContent || '';
  const match = text.match(/\d+\s*of\s*(\d+)/i);
  if (match) {
    return parseInt(match[1]);
  }
  
  // Default to visible images
  const images = gallery.querySelectorAll('img');
  return images.length;
}

/**
 * Navigate to specific photo
 */
async function navigateToPhoto(gallery: Element, index: number): Promise<void> {
  // Try thumbnail click
  const thumbs = gallery.querySelectorAll('.thumb, [role="button"][aria-label*="photo"]');
  if (thumbs[index]) {
    (thumbs[index] as HTMLElement).click();
    await delay(300);
    return;
  }
  
  // Try next button clicks
  const nextBtn = gallery.querySelector(
    '[aria-label="Next"], [aria-label*="next"], .next-button'
  ) as HTMLElement;
  
  if (nextBtn && index > 0) {
    for (let i = 0; i < index; i++) {
      nextBtn.click();
      await delay(300);
    }
  }
}

/**
 * Extract current photo data
 */
async function extractCurrentPhoto(index: number): Promise<GalleryPhoto | null> {
  // Find active image
  const selectors = [
    'img[src*="scontent"], img[src*="fbcdn"]', // Facebook
    '.gallery img.active, .gallery img:not([style*="display: none"])', // Craigslist
    '[data-testid="item-image"] img', // OfferUp
  ];
  
  let img: HTMLImageElement | null = null;
  for (const selector of selectors) {
    img = document.querySelector(selector);
    if (img?.src) break;
  }
  
  if (!img?.src) return null;
  
  // Get full resolution URL
  let url = img.src;
  
  // Facebook: get higher resolution
  if (url.includes('fbcdn')) {
    url = url.replace(/\/s\d+x\d+\//, '/').replace(/\/p\d+x\d+\//, '/');
  }
  
  // Get caption if available
  const caption = img.alt || img.getAttribute('aria-label') || undefined;
  
  return {
    url,
    index,
    caption,
  };
}

/**
 * Utility delay function
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create gallery scanner UI
 */
export function createGalleryScannerUI(
  onScan: () => void,
  onCancel?: () => void
): HTMLElement {
  const container = document.createElement('div');
  container.className = 'arbitrage-gallery-scanner';
  container.innerHTML = `
    <div class="scanner-header">
      <h3>Photo Scanner</h3>
      <button class="close-btn">&times;</button>
    </div>
    <div class="scanner-content">
      <p>Scan all photos in this gallery?</p>
      <div class="progress-container" style="display: none;">
        <div class="progress-bar">
          <div class="progress-fill" style="width: 0%"></div>
        </div>
        <div class="progress-text">0 / 0 photos</div>
      </div>
      <div class="scanner-actions">
        <button class="scan-btn">Scan Photos</button>
        <button class="cancel-btn" style="display: none;">Cancel</button>
      </div>
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .arbitrage-gallery-scanner {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 300px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .scanner-header {
      padding: 12px 16px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .scanner-header h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
    
    .close-btn {
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
      color: #6b7280;
    }
    
    .scanner-content {
      padding: 16px;
    }
    
    .scanner-content p {
      margin: 0 0 16px 0;
      color: #374151;
    }
    
    .progress-container {
      margin-bottom: 16px;
    }
    
    .progress-bar {
      height: 4px;
      background: #e5e7eb;
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    
    .progress-fill {
      height: 100%;
      background: #3b82f6;
      transition: width 0.3s ease;
    }
    
    .progress-text {
      font-size: 12px;
      color: #6b7280;
      text-align: center;
    }
    
    .scanner-actions {
      display: flex;
      gap: 8px;
    }
    
    .scan-btn, .cancel-btn {
      flex: 1;
      padding: 8px 16px;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }
    
    .scan-btn {
      background: #3b82f6;
      color: white;
    }
    
    .scan-btn:hover {
      background: #2563eb;
    }
    
    .cancel-btn {
      background: #f3f4f6;
      color: #374151;
    }
    
    .cancel-btn:hover {
      background: #e5e7eb;
    }
  `;
  
  document.head.appendChild(style);
  
  // Event handlers
  const closeBtn = container.querySelector('.close-btn') as HTMLElement;
  const scanBtn = container.querySelector('.scan-btn') as HTMLElement;
  const cancelBtn = container.querySelector('.cancel-btn') as HTMLElement;
  
  closeBtn.addEventListener('click', () => {
    container.remove();
    style.remove();
    onCancel?.();
  });
  
  scanBtn.addEventListener('click', () => {
    scanBtn.style.display = 'none';
    cancelBtn.style.display = 'block';
    container.querySelector('.progress-container')!.style.display = 'block';
    onScan();
  });
  
  cancelBtn.addEventListener('click', () => {
    container.remove();
    style.remove();
    onCancel?.();
  });
  
  return container;
}