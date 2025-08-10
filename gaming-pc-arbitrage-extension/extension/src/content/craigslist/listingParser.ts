/**
 * Craigslist Content Script Parser
 * Handles both list and detail pages
 */

import { sendMessage, MessageType } from '@/lib/messages';
import { debounce } from '@/lib/utils';

// State management
let currentUrl = '';
let observer: MutationObserver | null = null;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  console.log('Craigslist parser initialized');
  
  // Check if we're on a listing page
  if (isListingPage()) {
    handleListingPage();
  }
  
  // Watch for navigation (Craigslist uses regular page loads, not SPA)
  window.addEventListener('popstate', handleUrlChange);
  
  // Listen for manual parse requests
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'parse') {
      parseListing();
    }
  });
}

function handleUrlChange() {
  if (isListingPage()) {
    handleListingPage();
  } else {
    cleanupOverlay();
  }
}

function isListingPage(): boolean {
  // Craigslist listing patterns:
  // https://city.craigslist.org/zip/sss/d/title/123456789.html
  // https://city.craigslist.org/sys/123456789.html (computers)
  const path = window.location.pathname;
  return /\/\w+\/\d+\.html$/.test(path) || 
         /\/sys\/\d+\.html$/.test(path) ||
         /\/sss\/d\/[^/]+\/\d+\.html$/.test(path);
}

function handleListingPage() {
  currentUrl = location.href;
  
  // Craigslist loads everything on initial page load
  // Just parse immediately
  setTimeout(parseListing, 500);
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
      platform: 'craigslist',
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
  const title = document.querySelector('#titletextonly')?.textContent?.trim() || 
                document.querySelector('.postingtitletext #titletextonly')?.textContent?.trim() || '';
  
  // Price
  const priceText = document.querySelector('.price')?.textContent || '';
  const price = parsePrice(priceText);
  
  // Description
  const description = document.querySelector('#postingbody')?.textContent?.trim() || '';
  
  // Location
  const locationEl = document.querySelector('.postingtitletext small') || 
                     document.querySelector('.postingtitle small');
  const location = locationEl?.textContent?.replace(/[()]/g, '').trim() || '';
  
  // Images
  const images = extractImages();
  
  // Posted time
  const timeEl = document.querySelector('time.date');
  const postedTime = timeEl?.getAttribute('datetime') || '';
  
  // Reply info (email/phone might be hidden)
  const replyButton = document.querySelector('.reply-button');
  const hasReply = !!replyButton;
  
  return {
    title,
    price,
    description,
    location,
    images,
    postedTime,
    hasReply,
  };
}

function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9]/g, '');
  const price = parseInt(cleaned, 10);
  return isNaN(price) ? 0 : price;
}

function extractImages(): string[] {
  const images: string[] = [];
  
  // Main images
  const thumbs = document.querySelectorAll('.thumb');
  thumbs.forEach(thumb => {
    const link = thumb.getAttribute('href');
    if (link) {
      images.push(link);
    }
  });
  
  // Single image listings
  const singleImage = document.querySelector('.slide img');
  if (singleImage && images.length === 0) {
    const src = singleImage.getAttribute('src');
    if (src) images.push(src);
  }
  
  return images;
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
}