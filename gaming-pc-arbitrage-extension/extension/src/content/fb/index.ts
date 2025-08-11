/**
 * Facebook Marketplace Content Script
 * Production implementation - parses real listings
 */

import { parseListingCard, extractListingDetails } from './parser';
import { injectScanner } from '../scanner/overlay';

// Respond to background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'PING') {
    sendResponse({ pong: true });
    return true;
  }

  if (request.action === 'SCAN_PAGE') {
    console.log('[FB Scanner] Starting page scan...');
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
    
    // Find all marketplace listing cards
    const selectors = [
      '[data-testid="marketplace-feed-item"]',
      'div[role="article"] a[href*="/marketplace/item/"]',
      'div[class*="x1xfsgkm"] a[href*="/marketplace/item/"]',
      'a[href*="/marketplace/item/"][role="link"]'
    ];
    
    let listingElements: Element[] = [];
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        listingElements = Array.from(elements);
        console.log(`[FB Scanner] Found ${elements.length} listings with selector: ${selector}`);
        break;
      }
    }
    
    if (listingElements.length === 0) {
      console.log('[FB Scanner] No listings found on page');
      return { 
        success: true, 
        candidates: [],
        scanTime: performance.now() - startTime,
        platform: 'facebook'
      };
    }
    
    // Parse each listing
    for (const element of listingElements) {
      try {
        const listing = parseListingCard(element as HTMLElement);
        if (listing && listing.price > 0) {
          // Filter for gaming PCs
          const title = listing.title.toLowerCase();
          const desc = listing.description?.toLowerCase() || '';
          const combined = title + ' ' + desc;
          
          const gamingKeywords = ['gaming', 'pc', 'computer', 'desktop', 'rtx', 'gtx', 'radeon', 'ryzen', 'intel', 'i5', 'i7', 'i9'];
          const hasGamingKeyword = gamingKeywords.some(kw => combined.includes(kw));
          
          if (hasGamingKeyword) {
            listings.push({
              ...listing,
              id: `fb-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              platform: 'facebook',
              scannedAt: new Date().toISOString(),
              autoScanned: request.autoScan || false,
              searchId: request.searchId
            });
          }
        }
      } catch (error) {
        console.error('[FB Scanner] Error parsing listing:', error);
      }
    }
    
    console.log(`[FB Scanner] Found ${listings.length} gaming PC listings`);
    
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
      platform: 'facebook',
      totalScanned: listingElements.length
    };
    
  } catch (error) {
    console.error('[FB Scanner] Scan failed:', error);
    return {
      success: false,
      error: error.message,
      platform: 'facebook'
    };
  }
}

// Auto-inject scanner if on marketplace
if (window.location.pathname.includes('/marketplace')) {
  console.log('[FB Scanner] Content script loaded on marketplace page');
  
  // Wait for page to load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => injectScanner(), 1000);
    });
  } else {
    setTimeout(() => injectScanner(), 1000);
  }
}