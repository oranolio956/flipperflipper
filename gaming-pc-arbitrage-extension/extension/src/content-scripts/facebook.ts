/**
 * Facebook Marketplace Content Script
 * Injects analysis overlay on listing pages
 */

import { sendMessage } from '../lib/messages';
import { createOverlay, updateOverlay, hideOverlay } from '../ui/overlay';

// Track current state
let currentOverlay: HTMLElement | null = null;
let isAnalyzing = false;
let lastUrl = '';

// Platform detection
const isListingPage = () => {
  const path = window.location.pathname;
  return path.includes('/marketplace/item/') || 
         path.includes('/groups/') && path.includes('/posts/');
};

// Initialize observer for URL changes (Facebook is SPA)
const observeUrlChanges = () => {
  let lastUrl = location.href;
  
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      handleUrlChange();
    }
  }).observe(document, { subtree: true, childList: true });
};

// Handle URL changes
const handleUrlChange = () => {
  // Remove existing overlay
  if (currentOverlay) {
    hideOverlay(currentOverlay);
    currentOverlay = null;
  }
  
  // Check if we're on a listing page
  if (isListingPage()) {
    setTimeout(() => analyzeListing(), 1000); // Wait for content to load
  }
};

// Main analysis function
async function analyzeListing() {
  if (isAnalyzing) return;
  
  try {
    isAnalyzing = true;
    
    // Create and show overlay
    if (!currentOverlay) {
      currentOverlay = createOverlay();
      document.body.appendChild(currentOverlay);
    }
    
    // Get page HTML for parsing
    const html = document.documentElement.outerHTML;
    
    // Send to background for parsing
    const parseResponse = await sendMessage({
      type: 'PARSE_LISTING',
      payload: {
        url: window.location.href,
        platform: 'facebook',
        html
      }
    });
    
    if (!parseResponse.payload.success) {
      updateOverlay(currentOverlay, {
        error: parseResponse.payload.error || 'Failed to parse listing'
      });
      return;
    }
    
    const listing = parseResponse.payload.listing;
    
    // Calculate FMV
    const fmvResponse = await sendMessage({
      type: 'CALCULATE_FMV',
      payload: { listing }
    });
    
    if (fmvResponse.type === 'ERROR') {
      updateOverlay(currentOverlay, {
        error: fmvResponse.payload.message
      });
      return;
    }
    
    // Update overlay with results
    updateOverlay(currentOverlay, {
      listing,
      analysis: {
        fmv: fmvResponse.payload.fmv,
        confidence: fmvResponse.payload.confidence,
        breakdown: fmvResponse.payload.breakdown
      }
    });
    
    // Track event
    await sendMessage({
      type: 'TRACK_EVENT',
      payload: {
        name: 'listing_analyzed',
        category: 'analysis',
        properties: {
          platform: 'facebook',
          price: listing.price,
          fmv: fmvResponse.payload.fmv,
          hasGpu: !!listing.components?.gpu
        }
      }
    });
    
  } catch (error) {
    console.error('Analysis failed:', error);
    if (currentOverlay) {
      updateOverlay(currentOverlay, {
        error: 'Analysis failed. Please try again.'
      });
    }
  } finally {
    isAnalyzing = false;
  }
}

// Listen for messages from extension
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'TRIGGER_ANALYSIS') {
    analyzeListing();
    sendResponse({ success: true });
  }
  return false;
});

// Keyboard shortcut handler
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + Shift + A to analyze
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
    e.preventDefault();
    analyzeListing();
  }
  
  // Escape to close overlay
  if (e.key === 'Escape' && currentOverlay) {
    hideOverlay(currentOverlay);
    currentOverlay = null;
  }
});

// Initialize
console.log('Gaming PC Arbitrage Extension - Facebook content script loaded');

// Start observing URL changes
observeUrlChanges();

// Check initial page
if (isListingPage()) {
  setTimeout(() => analyzeListing(), 2000); // Auto-analyze on load
}

// Clean up on unload
window.addEventListener('unload', () => {
  if (currentOverlay) {
    currentOverlay.remove();
  }
});