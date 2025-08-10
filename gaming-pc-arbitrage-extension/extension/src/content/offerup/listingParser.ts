/**
 * OfferUp Content Script Parser
 * Handles SPA navigation and dynamic content
 */

import { sendMessage, MessageType } from '@/lib/messages';
import { debounce, throttle } from '@/lib/utils';

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
  console.log('OfferUp parser initialized');
  
  // Watch for URL changes (OfferUp is a React SPA)
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
  new MutationObserver(throttle(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      handleUrlChange();
    }
  }, 100)).observe(document, { subtree: true, childList: true });
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
    }, 1500); // OfferUp loads content dynamically
  } else {
    cleanupOverlay();
  }
}

function isListingPage(): boolean {
  // OfferUp listing patterns:
  // https://offerup.com/item/detail/[id]/[slug]
  return /\/item\/detail\/\d+/.test(location.pathname);
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
        // OfferUp renders content in main section
        if (target.closest('main') || target.querySelector('[data-testid]')) {
          debouncedParse();
          break;
        }
      }
    }
  });
  
  // Observe the main content area
  const mainContent = document.querySelector('main') || document.body;
  observer.observe(mainContent, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}

async function parseListing() {
  try {
    const data = extractListingData();
    
    if (!data.title || !data.price) {
      console.warn('Incomplete listing data, retrying...');
      // OfferUp sometimes loads content progressively
      setTimeout(parseListing, 1000);
      return;
    }
    
    // Send to background for processing
    const response = await sendMessage({
      type: MessageType.PARSE_PAGE,
      url: currentUrl,
      html: document.documentElement.outerHTML,
      platform: 'offerup',
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
  // Title - OfferUp uses various data-testid attributes
  const title = findTextBySelectors([
    '[data-testid="item-title"]',
    'h1[class*="ItemTitle"]',
    'h1',
  ]);
  
  // Price
  const priceText = findTextBySelectors([
    '[data-testid="item-price"]',
    '[class*="Price"]',
    'span[class*="currency"]',
  ]);
  const price = parsePrice(priceText);
  
  // Description
  const description = findTextBySelectors([
    '[data-testid="item-description"]',
    '[class*="ItemDescription"]',
    'div[class*="description"] p',
  ]);
  
  // Condition
  const condition = findTextBySelectors([
    '[data-testid="item-condition"]',
    'span:contains("Condition")',
  ]);
  
  // Location
  const location = findTextBySelectors([
    '[data-testid="item-location"]',
    'a[href*="location"]',
    '[class*="Location"]',
  ]);
  
  // Seller info
  const sellerName = findTextBySelectors([
    '[data-testid="seller-name"]',
    'a[href*="/profile/"] span',
    '[class*="SellerInfo"] a',
  ]);
  
  const sellerRating = findTextBySelectors([
    '[data-testid="seller-rating"]',
    '[class*="rating"]',
  ]);
  
  // Images
  const images = extractImages();
  
  // Posted time
  const postedTime = findTextBySelectors([
    '[data-testid="posted-time"]',
    'time',
    '[class*="posted"]',
  ]);
  
  return {
    title,
    price,
    description,
    condition,
    location,
    sellerName,
    sellerRating,
    images,
    postedTime,
  };
}

function findTextBySelectors(selectors: string[]): string {
  for (const selector of selectors) {
    try {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        const text = el.textContent?.trim();
        if (text) return text;
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
  
  // Main image carousel
  const imageElements = document.querySelectorAll([
    'img[data-testid*="image"]',
    '[class*="ItemImage"] img',
    '[class*="carousel"] img',
    'picture img',
  ].join(', '));
  
  imageElements.forEach(img => {
    if (img instanceof HTMLImageElement) {
      const src = img.src || img.dataset.src;
      if (src && !src.includes('placeholder') && !src.includes('avatar')) {
        images.push(src);
      }
    }
  });
  
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
  // Check if overlay already exists
  if (document.getElementById('arbitrage-overlay-root')) return;
  
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