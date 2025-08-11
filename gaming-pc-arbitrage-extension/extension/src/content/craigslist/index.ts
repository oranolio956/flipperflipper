/**
 * Craigslist Content Script
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
    console.log('[CL Scanner] Starting page scan...');
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
    
    // Find all Craigslist listing rows
    const selectors = [
      '.result-row',
      'li.cl-search-result',
      '.rows li'
    ];
    
    let listingElements: Element[] = [];
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        listingElements = Array.from(elements);
        console.log(`[CL Scanner] Found ${elements.length} listings with selector: ${selector}`);
        break;
      }
    }
    
    if (listingElements.length === 0) {
      console.log('[CL Scanner] No listings found on page');
      return { 
        success: true, 
        candidates: [],
        scanTime: performance.now() - startTime,
        platform: 'craigslist'
      };
    }
    
    // Parse each listing
    for (const element of listingElements) {
      try {
        const listing = parseListingRow(element as HTMLElement);
        if (listing && listing.price > 0) {
          // Filter for gaming PCs
          const title = listing.title.toLowerCase();
          const gamingKeywords = ['gaming', 'pc', 'computer', 'desktop', 'rtx', 'gtx', 'radeon', 'ryzen', 'intel', 'i5', 'i7', 'i9'];
          const hasGamingKeyword = gamingKeywords.some(kw => title.includes(kw));
          
          if (hasGamingKeyword) {
            listings.push({
              ...listing,
              id: `cl-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              platform: 'craigslist',
              scannedAt: new Date().toISOString(),
              autoScanned: request.autoScan || false,
              searchId: request.searchId
            });
          }
        }
      } catch (error) {
        console.error('[CL Scanner] Error parsing listing:', error);
      }
    }
    
    console.log(`[CL Scanner] Found ${listings.length} gaming PC listings`);
    
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
      platform: 'craigslist',
      totalScanned: listingElements.length
    };
    
  } catch (error) {
    console.error('[CL Scanner] Scan failed:', error);
    return {
      success: false,
      error: error.message,
      platform: 'craigslist'
    };
  }
}

function parseListingRow(element: HTMLElement): any {
  try {
    // Get link and title
    const linkEl = element.querySelector('.result-title') as HTMLAnchorElement;
    if (!linkEl) return null;
    
    const url = linkEl.href;
    const title = linkEl.textContent?.trim() || '';
    
    // Get price
    const priceEl = element.querySelector('.result-price');
    const priceText = priceEl?.textContent || '';
    const price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
    
    // Get date
    const dateEl = element.querySelector('.result-date');
    const dateText = dateEl?.textContent?.trim() || '';
    
    // Get location
    const hoodEl = element.querySelector('.result-hood');
    const location = hoodEl?.textContent?.trim().replace(/[()]/g, '') || '';
    
    // Get image if available
    const imgEl = element.querySelector('.result-image img') as HTMLImageElement;
    const imageUrl = imgEl?.src;
    
    return {
      title,
      price,
      url,
      location,
      imageUrl,
      postedDate: parseCraigslistDate(dateText)
    };
    
  } catch (error) {
    console.error('[CL Parser] Error parsing row:', error);
    return null;
  }
}

function parseCraigslistDate(dateText: string): string {
  try {
    // Craigslist uses format like "Dec 15" or "Nov 28"
    const currentYear = new Date().getFullYear();
    const parsed = new Date(`${dateText} ${currentYear}`);
    
    // If the date is in the future, it's probably from last year
    if (parsed > new Date()) {
      parsed.setFullYear(currentYear - 1);
    }
    
    return parsed.toISOString();
  } catch (error) {
    return new Date().toISOString();
  }
}

// Auto-inject scanner if on search results
if (window.location.pathname.includes('/search/') || window.location.pathname.includes('/sss')) {
  console.log('[CL Scanner] Content script loaded on search page');
  
  // Wait for page to load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => injectScanner(), 1000);
    });
  } else {
    setTimeout(() => injectScanner(), 1000);
  }
}