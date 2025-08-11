/**
 * Generic Scanner Content Script
 * Handles scanning on any page when requested
 */

import { injectScanner } from './overlay';

// This content script can be injected dynamically on any page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'INJECT_SCANNER') {
    console.log('[Scanner] Injecting scanner overlay...');
    injectScanner();
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'SCAN_PAGE') {
    console.log('[Scanner] Generic scan requested');
    // For generic pages, we can't parse listings
    // This is mainly used for the scanner UI injection
    sendResponse({
      success: true,
      candidates: [],
      platform: 'unknown',
      message: 'Please navigate to a marketplace page (Facebook, Craigslist, or OfferUp) to scan listings.'
    });
    return true;
  }
});

console.log('[Scanner] Generic scanner script loaded');