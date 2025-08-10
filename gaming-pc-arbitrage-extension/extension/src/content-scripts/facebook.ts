/**
 * Facebook Marketplace Content Script
 * Injects analysis overlay on listing pages
 */

import { FacebookMarketplaceParser } from '@arbitrage/core';
import { createOverlay, updateOverlay } from '../ui/overlay';

// Only run on listing pages
const isListingPage = () => {
  return window.location.pathname.includes('/marketplace/item/') ||
         window.location.pathname.includes('/groups/') ||
         document.querySelector('[data-pagelet="MainFeed"]');
};

// Initialize parser
const parser = new FacebookMarketplaceParser();
let currentOverlay: HTMLElement | null = null;

// Main analysis function
async function analyzeListing() {
  if (!isListingPage()) return;
  
  try {
    // Parse the listing
    const listing = parser.extractListing(document);
    if (!listing) {
      console.log('Could not parse listing');
      return;
    }
    
    // Send to background for analysis
    const response = await chrome.runtime.sendMessage({
      type: 'ANALYZE_LISTING',
      payload: listing
    });
    
    if (response.success) {
      // Create or update overlay
      if (!currentOverlay) {
        currentOverlay = createOverlay();
        document.body.appendChild(currentOverlay);
      }
      
      updateOverlay(currentOverlay, {
        listing,
        analysis: response.result
      });
    }
  } catch (error) {
    console.error('Analysis error:', error);
  }
}

// Listen for messages from background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'TRIGGER_ANALYSIS') {
    analyzeListing();
    sendResponse({ success: true });
  } else if (message.type === 'TRIGGER_TRACK_DEAL') {
    if (currentOverlay) {
      const saveButton = currentOverlay.querySelector('[data-action="save-deal"]');
      if (saveButton) {
        (saveButton as HTMLElement).click();
      }
    }
    sendResponse({ success: true });
  }
});

// Auto-analyze on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', analyzeListing);
} else {
  analyzeListing();
}

// Watch for URL changes (SPA navigation)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(analyzeListing, 1000); // Wait for content to load
  }
}).observe(document, { subtree: true, childList: true });

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.altKey && e.key === 'a') {
    e.preventDefault();
    analyzeListing();
  }
});