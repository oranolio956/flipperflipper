/**
 * OfferUp Content Script
 * Production implementation - parses real listings
 */

import { injectScanner } from '../scanner/overlay';

// Respond to background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'PING') {
    sendResponse({ pong: true });
    return true;
  }

  if (request.action === 'SCAN_PAGE') {
    console.log('[OU Scanner] Starting page scan...');
    performScan(request).then(sendResponse);
    return true; // Will respond asynchronously
  }

  if (request.action === 'INJECT_SCANNER') {
    injectScanner();
    sendResponse({ success: true });
    return true;
  }
});

async function performScan(request: any) {
  try {
    const listings = [];
    const startTime = performance.now();
    
    // Find all OfferUp listing cards
    const selectors = [
      'a[href*="/item/detail/"]',
      '[data-testid="item-card"]',
      'div[class*="ItemCard"]'
    ];
    
    let listingElements: Element[] = [];
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        listingElements = Array.from(elements);
        console.log(`[OU Scanner] Found ${elements.length} listings with selector: ${selector}`);
        break;
      }
    }
    
    // If no luck with selectors, try finding by structure
    if (listingElements.length === 0) {
      const allLinks = document.querySelectorAll('a');
      listingElements = Array.from(allLinks).filter(link => {
        const href = link.getAttribute('href') || '';
        return href.includes('/item/') && link.querySelector('img');
      });
      
      if (listingElements.length > 0) {
        console.log(`[OU Scanner] Found ${listingElements.length} listings by structure`);
      }
    }
    
    if (listingElements.length === 0) {
      console.log('[OU Scanner] No listings found on page');
      return { 
        success: true, 
        candidates: [],
        scanTime: performance.now() - startTime,
        platform: 'offerup'
      };
    }
    
    // Parse each listing
    for (const element of listingElements) {
      try {
        const listing = parseListingCard(element as HTMLElement);
        if (listing && listing.price > 0) {
          // Filter for gaming PCs
          const title = listing.title.toLowerCase();
          const gamingKeywords = ['gaming', 'pc', 'computer', 'desktop', 'rtx', 'gtx', 'radeon', 'ryzen', 'intel', 'i5', 'i7', 'i9'];
          const hasGamingKeyword = gamingKeywords.some(kw => title.includes(kw));
          
          if (hasGamingKeyword) {
            listings.push({
              ...listing,
              id: `ou-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              platform: 'offerup',
              scannedAt: new Date().toISOString(),
              autoScanned: request.autoScan || false,
              searchId: request.searchId
            });
          }
        }
      } catch (error) {
        console.error('[OU Scanner] Error parsing listing:', error);
      }
    }
    
    console.log(`[OU Scanner] Found ${listings.length} gaming PC listings`);
    
    // Store results if this is an auto-scan
    if (request.autoScan && listings.length > 0) {
      await chrome.runtime.sendMessage({
        action: 'STORE_SCAN_RESULTS',
        listings,
        searchId: request.searchId,
        scanId: request.scanId
      });
    }
    
    return {
      success: true,
      candidates: listings,
      scanTime: performance.now() - startTime,
      platform: 'offerup',
      totalScanned: listingElements.length
    };
    
  } catch (error) {
    console.error('[OU Scanner] Scan failed:', error);
    return {
      success: false,
      error: error.message,
      platform: 'offerup'
    };
  }
}

function parseListingCard(element: HTMLElement): any {
  try {
    // Get URL
    const linkEl = element.tagName === 'A' ? element : element.closest('a');
    if (!linkEl) return null;
    
    const url = (linkEl as HTMLAnchorElement).href;
    
    // Get title - try multiple approaches
    let title = '';
    const titleSelectors = [
      '[class*="ItemTitle"]',
      'p[class*="title"]',
      'span[class*="title"]',
      'h3',
      'h4'
    ];
    
    for (const selector of titleSelectors) {
      const titleEl = element.querySelector(selector);
      if (titleEl?.textContent) {
        title = titleEl.textContent.trim();
        if (title.length > 5) break;
      }
    }
    
    // If still no title, look in image alt text
    if (!title) {
      const imgEl = element.querySelector('img');
      title = imgEl?.alt || '';
    }
    
    if (!title) return null;
    
    // Get price
    let price = 0;
    const priceText = findTextContent(element, /\$[\d,]+/);
    if (priceText) {
      price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
    }
    
    // Get image
    const imgEl = element.querySelector('img') as HTMLImageElement;
    const imageUrl = imgEl?.src;
    
    // Get location - OfferUp often shows distance
    const locationText = findTextContent(element, /\d+\s*mi(les)?\s*away/i) ||
                        findTextContent(element, /[A-Z][a-z]+,\s*[A-Z]{2}/);
    
    // Get condition if available
    const conditionText = findTextContent(element, /(new|like new|good|fair|poor)/i);
    
    return {
      title,
      price,
      url,
      imageUrl,
      location: locationText,
      condition: conditionText,
      postedDate: new Date().toISOString() // OfferUp doesn't always show date on cards
    };
    
  } catch (error) {
    console.error('[OU Parser] Error parsing card:', error);
    return null;
  }
}

function findTextContent(element: HTMLElement, pattern: RegExp): string | null {
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null
  );
  
  let node;
  while (node = walker.nextNode()) {
    const text = node.textContent?.trim();
    if (text && pattern.test(text)) {
      return text;
    }
  }
  
  return null;
}

// Auto-inject scanner if on search page
if (window.location.pathname.includes('/search/') || 
    window.location.pathname.includes('/browse/') ||
    window.location.search.includes('q=')) {
  console.log('[OU Scanner] Content script loaded on search page');
  
  // Wait for page to load (OfferUp is a SPA)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => injectScanner(), 2000); // Longer delay for SPA
    });
  } else {
    setTimeout(() => injectScanner(), 2000);
  }
}