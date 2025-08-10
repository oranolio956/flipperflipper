/**
 * Seller Meta Parser
 * Extract detailed seller information and verification status
 */

export interface SellerMeta {
  id: string;
  name: string;
  profileUrl: string;
  memberSince?: Date;
  rating?: number;
  ratingCount?: number;
  responseTime?: string;
  badges: string[];
  listingCount?: number;
  soldCount?: number;
  verified: boolean;
  businessAccount: boolean;
}

/**
 * Parse seller metadata from profile or listing
 */
export function parseSellerMeta(): SellerMeta | null {
  // Try profile page first
  if (isProfilePage()) {
    return parseProfilePage();
  }
  
  // Try listing page
  if (isListingPage()) {
    return parseListingSellerInfo();
  }
  
  return null;
}

/**
 * Check if on profile page
 */
function isProfilePage(): boolean {
  return window.location.pathname.includes('/profile/') ||
         window.location.pathname.includes('/marketplace/profile/') ||
         document.querySelector('[data-pagelet="ProfileTilesFeed"]') !== null;
}

/**
 * Check if on listing page
 */
function isListingPage(): boolean {
  return window.location.pathname.includes('/marketplace/item/') ||
         document.querySelector('[data-pagelet="MarketplacePDP"]') !== null;
}

/**
 * Parse profile page
 */
function parseProfilePage(): SellerMeta | null {
  const meta: Partial<SellerMeta> = {
    badges: [],
  };
  
  // Name
  const nameEl = document.querySelector('h1[dir="auto"], [data-pagelet="ProfileTilesFeed"] h1');
  if (nameEl) {
    meta.name = nameEl.textContent?.trim() || '';
  }
  
  // Profile URL
  meta.profileUrl = window.location.href.split('?')[0];
  
  // Extract ID from URL
  const idMatch = window.location.href.match(/\/profile\/(\d+)/);
  if (idMatch) {
    meta.id = idMatch[1];
  }
  
  // Member since
  const aboutSection = document.querySelector('[aria-label*="About"]');
  if (aboutSection) {
    const joinedText = aboutSection.textContent || '';
    const joinedMatch = joinedText.match(/Joined\s+(\w+\s+\d{4})/i);
    if (joinedMatch) {
      meta.memberSince = new Date(joinedMatch[1]);
    }
  }
  
  // Marketplace stats
  const statsContainer = document.querySelector('[role="main"]');
  if (statsContainer) {
    // Rating
    const ratingEl = statsContainer.querySelector('[aria-label*="rating"], [aria-label*="stars"]');
    if (ratingEl) {
      const ratingText = ratingEl.getAttribute('aria-label') || '';
      const ratingMatch = ratingText.match(/([\d.]+)\s*(?:out of|\/)\s*5/);
      if (ratingMatch) {
        meta.rating = parseFloat(ratingMatch[1]);
      }
      
      // Rating count
      const countMatch = ratingText.match(/(\d+)\s*(?:rating|review)/i);
      if (countMatch) {
        meta.ratingCount = parseInt(countMatch[1]);
      }
    }
    
    // Listing count
    const listingText = statsContainer.textContent || '';
    const listingMatch = listingText.match(/(\d+)\s*(?:listing|item)s?\s*(?:for sale|available)/i);
    if (listingMatch) {
      meta.listingCount = parseInt(listingMatch[1]);
    }
    
    // Response time
    const responseMatch = listingText.match(/(?:responds?|reply|replies)\s*(?:within|in)\s*([^.]+)/i);
    if (responseMatch) {
      meta.responseTime = responseMatch[1].trim();
    }
  }
  
  // Badges
  const badgeElements = document.querySelectorAll('[aria-label*="badge"], [aria-label*="verified"]');
  badgeElements.forEach(badge => {
    const label = badge.getAttribute('aria-label') || '';
    if (label && !meta.badges.includes(label)) {
      meta.badges.push(label);
    }
  });
  
  // Verification status
  meta.verified = meta.badges.some(b => 
    b.toLowerCase().includes('verified') || 
    b.toLowerCase().includes('authentic')
  );
  
  // Business account
  meta.businessAccount = meta.badges.some(b => 
    b.toLowerCase().includes('business') ||
    b.toLowerCase().includes('shop')
  );
  
  if (!meta.name || !meta.id) return null;
  
  return meta as SellerMeta;
}

/**
 * Parse seller info from listing page
 */
function parseListingSellerInfo(): SellerMeta | null {
  const meta: Partial<SellerMeta> = {
    badges: [],
  };
  
  // Find seller section
  const sellerSection = document.querySelector(
    '[aria-label*="Seller information"], [data-testid="marketplace_pdp_seller_section"]'
  );
  
  if (!sellerSection) return null;
  
  // Name and link
  const sellerLink = sellerSection.querySelector('a[href*="/profile/"], a[href*="/marketplace/profile/"]');
  if (sellerLink) {
    meta.name = sellerLink.textContent?.trim() || '';
    meta.profileUrl = new URL(sellerLink.getAttribute('href') || '', window.location.origin).href;
    
    const idMatch = meta.profileUrl.match(/\/profile\/(\d+)/);
    if (idMatch) {
      meta.id = idMatch[1];
    }
  }
  
  // Rating
  const ratingEl = sellerSection.querySelector('[role="img"][aria-label*="star"], [aria-label*="rating"]');
  if (ratingEl) {
    const label = ratingEl.getAttribute('aria-label') || '';
    const match = label.match(/([\d.]+)/);
    if (match) {
      meta.rating = parseFloat(match[1]);
    }
  }
  
  // Response time
  const responseEl = Array.from(sellerSection.querySelectorAll('span')).find(el => 
    el.textContent?.includes('respond') || el.textContent?.includes('reply')
  );
  if (responseEl) {
    const timeMatch = responseEl.textContent?.match(/(?:within|in)\s+(.+)/);
    if (timeMatch) {
      meta.responseTime = timeMatch[1].trim();
    }
  }
  
  // Member since
  const memberText = sellerSection.textContent || '';
  const sinceMatch = memberText.match(/(?:Member since|Joined)\s+(\w+\s+\d{4})/i);
  if (sinceMatch) {
    meta.memberSince = new Date(sinceMatch[1]);
  }
  
  // Badges (look for icons/labels)
  sellerSection.querySelectorAll('[aria-label], [title]').forEach(el => {
    const label = el.getAttribute('aria-label') || el.getAttribute('title') || '';
    if (label && (
      label.includes('verified') ||
      label.includes('badge') ||
      label.includes('authentic') ||
      label.includes('business')
    )) {
      meta.badges.push(label);
    }
  });
  
  meta.verified = meta.badges.length > 0;
  meta.businessAccount = meta.badges.some(b => 
    b.toLowerCase().includes('business') ||
    b.toLowerCase().includes('shop')
  );
  
  if (!meta.name || !meta.id) return null;
  
  return meta as SellerMeta;
}

/**
 * Calculate seller trust score
 */
export function calculateSellerTrustScore(seller: SellerMeta): {
  score: number;
  factors: string[];
} {
  let score = 50; // Base score
  const factors: string[] = [];
  
  // Member duration
  if (seller.memberSince) {
    const years = (Date.now() - seller.memberSince.getTime()) / (365 * 24 * 60 * 60 * 1000);
    if (years > 5) {
      score += 15;
      factors.push('Long-time member (5+ years)');
    } else if (years > 2) {
      score += 10;
      factors.push('Established member (2+ years)');
    } else if (years > 1) {
      score += 5;
      factors.push('Member for over 1 year');
    } else {
      score -= 10;
      factors.push('New member (< 1 year)');
    }
  }
  
  // Rating
  if (seller.rating !== undefined) {
    if (seller.rating >= 4.8) {
      score += 15;
      factors.push('Excellent rating');
    } else if (seller.rating >= 4.5) {
      score += 10;
      factors.push('Good rating');
    } else if (seller.rating >= 4.0) {
      score += 5;
      factors.push('Decent rating');
    } else {
      score -= 10;
      factors.push('Low rating');
    }
    
    // Rating count matters
    if (seller.ratingCount && seller.ratingCount > 50) {
      score += 5;
      factors.push('Many reviews');
    }
  }
  
  // Response time
  if (seller.responseTime) {
    if (seller.responseTime.includes('hour') || seller.responseTime.includes('minute')) {
      score += 5;
      factors.push('Fast responder');
    }
  }
  
  // Verification
  if (seller.verified) {
    score += 10;
    factors.push('Verified account');
  }
  
  // Business account
  if (seller.businessAccount) {
    score += 5;
    factors.push('Business account');
  }
  
  // Listing volume
  if (seller.listingCount) {
    if (seller.listingCount > 20) {
      score -= 5;
      factors.push('High volume seller');
    } else if (seller.listingCount === 1) {
      score -= 5;
      factors.push('Only one listing');
    }
  }
  
  return {
    score: Math.max(0, Math.min(100, score)),
    factors,
  };
}