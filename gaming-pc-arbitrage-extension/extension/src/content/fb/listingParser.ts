/**
 * Facebook Marketplace Content Script Parser
 * Watches for listing pages and extracts data
 */

import { sendMessage, MessageType } from '@/lib/messages';
import { debounce } from '@/lib/utils';

// State management
let currentUrl = '';
let observer: MutationObserver | null = null;
let parseTimeout: NodeJS.Timeout | null = null;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  console.log('FB Marketplace parser initialized');
  
  // Watch for URL changes (SPA navigation)
  setupUrlWatcher();
  
  // Check if we're already on a listing page
  if (isListingPage()) {
    handleListingPage();
  }
  
  // Listen for manual parse requests
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'parse') {
      parseListing();
    }
  });
}

function setupUrlWatcher() {
  // Watch for URL changes
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      handleUrlChange();
    }
  }).observe(document, { subtree: true, childList: true });
}

function handleUrlChange() {
  if (isListingPage()) {
    // Clean up previous observer
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    
    // Debounce to let page settle
    if (parseTimeout) clearTimeout(parseTimeout);
    parseTimeout = setTimeout(() => {
      handleListingPage();
    }, 1000);
  } else {
    // Clean up when leaving listing page
    cleanupOverlay();
  }
}

function isListingPage(): boolean {
  // Facebook Marketplace item URL patterns:
  // https://www.facebook.com/marketplace/item/123456789
  // https://www.facebook.com/marketplace/you/selling/item/123456789
  return /\/marketplace\/.*\/item\/\d+|\/marketplace\/item\/\d+/.test(location.href);
}

function handleListingPage() {
  currentUrl = location.href;
  
  // Set up mutation observer for dynamic content
  setupMutationObserver();
  
  // Initial parse
  parseListing();
}

function setupMutationObserver() {
  if (observer) return;
  
  const debouncedParse = debounce(parseListing, 500);
  
  observer = new MutationObserver((mutations) => {
    // Look for price or description changes
    for (const mutation of mutations) {
      if (mutation.type === 'childList' || mutation.type === 'characterData') {
        const target = mutation.target as HTMLElement;
        if (target.textContent?.includes('$') || 
            target.closest('[role="main"]')) {
          debouncedParse();
          break;
        }
      }
    }
  });
  
  // Observe the main content area
  const mainContent = document.querySelector('[role="main"]');
  if (mainContent) {
    observer.observe(mainContent, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }
}

async function parseListing() {
  try {
    const data = extractListingData();
    
    if (!data.title || !data.price) {
      console.warn('Incomplete listing data');
      return;
    }
    
    // Send to background for processing
    const response = await sendMessage({
      type: MessageType.PARSE_PAGE,
      url: currentUrl,
      html: document.documentElement.outerHTML,
      platform: 'facebook',
    });
    
    if (response.success && response.listing) {
      // Update overlay with results
      updateOverlay({
        listing: response.listing,
        fmv: response.fmv,
        roi: response.roi,
        risk: response.risk,
      });
    }
  } catch (error) {
    console.error('Parse error:', error);
  }
}

function extractListingData() {
  // Title
  const titleSelectors = [
    'h1 span',
    '[data-testid="marketplace-pdp-title"]',
    'div[class*="title"] span',
  ];
  const title = findText(titleSelectors);
  
  // Price
  const priceSelectors = [
    '[data-testid="marketplace-pdp-price"]',
    '[aria-label*="Price"]',
    'div[class*="price"] span',
  ];
  const priceText = findText(priceSelectors);
  const price = parsePrice(priceText);
  
  // Description
  const descSelectors = [
    '[data-testid="marketplace-pdp-description"]',
    'div[class*="description"] span',
  ];
  const description = findText(descSelectors);
  
  // Location
  const locationSelectors = [
    '[aria-label*="Location"]',
    'a[href*="location"] span',
  ];
  const location = findText(locationSelectors);
  
  // Seller
  const sellerSelectors = [
    '[data-testid="marketplace-pdp-seller-name"]',
    'a[href*="/profile/"] span',
  ];
  const sellerName = findText(sellerSelectors);
  
  // Images
  const images = extractImages();
  
  return {
    title,
    price,
    description,
    location,
    sellerName,
    images,
  };
}

function findText(selectors: string[]): string {
  for (const selector of selectors) {
    try {
      const el = document.querySelector(selector);
      if (el?.textContent) {
        return el.textContent.trim();
      }
    } catch (e) {
      // Invalid selector, continue
    }
  }
  return '';
}

function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9.,]/g, '');
  const price = parseFloat(cleaned.replace(',', ''));
  return isNaN(price) ? 0 : price;
}

function extractImages(): string[] {
  const images: string[] = [];
  
  // Main image container selectors
  const selectors = [
    '[data-testid="marketplace-pdp-image"] img',
    '[role="img"][style*="background-image"]',
    'img[src*="scontent"]',
  ];
  
  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      let url = '';
      
      if (el instanceof HTMLImageElement) {
        url = el.src;
      } else {
        // Extract from background-image
        const style = (el as HTMLElement).style.backgroundImage;
        const match = style.match(/url\("?(.+?)"?\)/);
        if (match) url = match[1];
      }
      
      if (url && !url.includes('static.xx.fbcdn.net')) {
        images.push(url);
      }
    });
  }
  
  return [...new Set(images)]; // Dedupe
}

// Overlay management
let overlayContainer: HTMLElement | null = null;

function updateOverlay(data: any) {
  if (!overlayContainer) {
    createOverlay();
  }
  
  // Send data to overlay React app
  window.postMessage({
    type: 'ARBITRAGE_UPDATE',
    data,
  }, '*');
}

function createOverlay() {
  // Inject overlay container
  overlayContainer = document.createElement('div');
  overlayContainer.id = 'arbitrage-overlay-root';
  document.body.appendChild(overlayContainer);
  
  // The overlay React app will mount here
}

function cleanupOverlay() {
  if (overlayContainer) {
    overlayContainer.remove();
    overlayContainer = null;
  }
  
  if (observer) {
    observer.disconnect();
    observer = null;
  }
}