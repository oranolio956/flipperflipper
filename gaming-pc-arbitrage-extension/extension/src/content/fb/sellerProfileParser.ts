/**
 * Facebook Seller Profile Parser
 * Extract seller metadata when user views profile
 */

export interface SellerProfile {
  sellerId: string;
  name: string;
  memberSince?: Date;
  listingCount: number;
  soldCount?: number;
  responseTime?: string;
  rating?: number;
}

/**
 * Parse seller profile page
 */
export function parseSellerProfile(): SellerProfile | null {
  try {
    // Check if we're on a seller profile page
    if (!window.location.pathname.includes('/marketplace/profile/')) {
      return null;
    }
    
    // Extract seller ID from URL
    const urlMatch = window.location.pathname.match(/profile\/(\d+)/);
    const sellerId = urlMatch?.[1] || '';
    
    // Seller name
    const nameEl = document.querySelector('h1') || 
                   document.querySelector('[role="main"] h2');
    const name = nameEl?.textContent?.trim() || 'Unknown Seller';
    
    // Active listings count
    const listingEls = document.querySelectorAll('[data-testid="marketplace-listing"]') ||
                      document.querySelectorAll('a[href*="/marketplace/item/"]');
    const listingCount = listingEls.length;
    
    // Member since (if visible)
    let memberSince: Date | undefined;
    const joinedText = Array.from(document.querySelectorAll('span'))
      .find(el => el.textContent?.includes('Joined'))?.textContent;
    
    if (joinedText) {
      const yearMatch = joinedText.match(/(\d{4})/);
      if (yearMatch) {
        memberSince = new Date(parseInt(yearMatch[1]), 0, 1);
      }
    }
    
    // Response time (if shown)
    const responseEl = Array.from(document.querySelectorAll('span'))
      .find(el => el.textContent?.includes('Typically responds'));
    const responseTime = responseEl?.textContent?.replace('Typically responds', '').trim();
    
    // Rating if available
    let rating: number | undefined;
    const ratingEl = document.querySelector('[aria-label*="rated"]');
    if (ratingEl) {
      const ratingMatch = ratingEl.getAttribute('aria-label')?.match(/(\d+\.?\d*)/);
      if (ratingMatch) {
        rating = parseFloat(ratingMatch[1]);
      }
    }
    
    return {
      sellerId,
      name,
      memberSince,
      listingCount,
      responseTime,
      rating,
    };
  } catch (error) {
    console.error('Failed to parse seller profile:', error);
    return null;
  }
}

/**
 * Cache seller profile data
 */
export function cacheSellerProfile(profile: SellerProfile) {
  chrome.runtime.sendMessage({
    type: 'CACHE_SELLER_PROFILE',
    profile,
  });
}

/**
 * Auto-parse when profile loads
 */
function initProfileParser() {
  // Wait for page to load
  setTimeout(() => {
    const profile = parseSellerProfile();
    if (profile) {
      cacheSellerProfile(profile);
    }
  }, 2000);
  
  // Also listen for navigation changes
  let lastUrl = window.location.href;
  const observer = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      setTimeout(() => {
        const profile = parseSellerProfile();
        if (profile) {
          cacheSellerProfile(profile);
        }
      }, 2000);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

// Initialize if on Facebook
if (window.location.hostname.includes('facebook.com')) {
  initProfileParser();
}