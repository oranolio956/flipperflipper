/**
 * Facebook Marketplace Parser
 * Extracts listing data from DOM elements
 */

export interface ParsedListing {
  title: string;
  price: number;
  description?: string;
  location?: string;
  imageUrl?: string;
  url: string;
  sellerId?: string;
  postedDate?: string;
}

export function parseListingCard(element: HTMLElement): ParsedListing | null {
  try {
    // Get the link element
    const linkElement = element.tagName === 'A' ? element : element.querySelector('a[href*="/marketplace/item/"]');
    if (!linkElement) return null;
    
    const url = (linkElement as HTMLAnchorElement).href;
    const itemId = extractItemId(url);
    if (!itemId) return null;
    
    // Extract title - Facebook uses various selectors
    const titleSelectors = [
      'span[class*="x1lliihq"][class*="x1plvlek"]',
      'span[dir="auto"]',
      '[role="heading"]',
      'h3'
    ];
    
    let title = '';
    for (const selector of titleSelectors) {
      const titleEl = element.querySelector(selector);
      if (titleEl?.textContent) {
        title = titleEl.textContent.trim();
        if (title.length > 5) break; // Found a reasonable title
      }
    }
    
    if (!title) return null;
    
    // Extract price
    const priceSelectors = [
      'span:has-text("$")',
      'span[class*="x193iq5w"]',
      'div[class*="x1xmf6yo"]'
    ];
    
    let price = 0;
    const priceText = findTextContent(element, /\$[\d,]+/);
    if (priceText) {
      price = parsePrice(priceText);
    } else {
      // Try selectors
      for (const selector of priceSelectors) {
        const priceEl = element.querySelector(selector);
        if (priceEl?.textContent?.includes('$')) {
          price = parsePrice(priceEl.textContent);
          if (price > 0) break;
        }
      }
    }
    
    // Extract location
    const locationText = findTextContent(element, /\d+\s*(mi|miles?|km)\s*(away)?/i) || 
                       findTextContent(element, /[A-Z][a-z]+,\s*[A-Z]{2}/);
    
    // Extract image
    const imgElement = element.querySelector('img[src*="scontent"]') as HTMLImageElement;
    const imageUrl = imgElement?.src;
    
    // Extract description if available
    const descSelectors = [
      'span[class*="x6ikm8r"]',
      'div[class*="x1iorvi4"]'
    ];
    
    let description = '';
    for (const selector of descSelectors) {
      const descEl = element.querySelector(selector);
      if (descEl?.textContent && descEl.textContent !== title) {
        description = descEl.textContent.trim();
        break;
      }
    }
    
    return {
      title,
      price,
      description,
      location: locationText,
      imageUrl,
      url,
      sellerId: itemId,
      postedDate: extractPostedDate(element)
    };
    
  } catch (error) {
    console.error('[FB Parser] Error parsing listing card:', error);
    return null;
  }
}

export function extractListingDetails(pageDocument: Document): ParsedListing | null {
  try {
    // This would be called on the actual listing page
    // Extract more detailed information
    const title = pageDocument.querySelector('h1')?.textContent?.trim() || '';
    const priceEl = pageDocument.querySelector('[class*="x193iq5w"]:has-text("$")');
    const price = priceEl ? parsePrice(priceEl.textContent || '') : 0;
    
    // Get description
    const descEl = pageDocument.querySelector('[class*="xz9dl7a"]');
    const description = descEl?.textContent?.trim();
    
    // Get seller info
    const sellerEl = pageDocument.querySelector('a[href*="/profile.php"]');
    const sellerId = sellerEl?.getAttribute('href')?.match(/id=(\d+)/)?.[1];
    
    // Get images
    const images = Array.from(pageDocument.querySelectorAll('img[src*="scontent"]'))
      .map(img => (img as HTMLImageElement).src)
      .filter(src => src.includes('marketplace'));
    
    return {
      title,
      price,
      description,
      url: window.location.href,
      sellerId,
      imageUrl: images[0],
      location: pageDocument.querySelector('[class*="x1xmf6yo"]')?.textContent?.trim()
    };
    
  } catch (error) {
    console.error('[FB Parser] Error extracting listing details:', error);
    return null;
  }
}

// Helper functions
function extractItemId(url: string): string | null {
  const match = url.match(/\/marketplace\/item\/(\d+)/);
  return match ? match[1] : null;
}

function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9]/g, '');
  return parseInt(cleaned) || 0;
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

function extractPostedDate(element: HTMLElement): string | null {
  // Look for relative time like "2 hours ago", "3 days ago"
  const timePattern = /\d+\s*(hours?|days?|weeks?|months?)\s*ago/i;
  const timeText = findTextContent(element, timePattern);
  
  if (timeText) {
    // Convert to approximate date
    const now = new Date();
    const match = timeText.match(/(\d+)\s*(hour|day|week|month)/i);
    if (match) {
      const amount = parseInt(match[1]);
      const unit = match[2].toLowerCase();
      
      switch (unit) {
        case 'hour':
          now.setHours(now.getHours() - amount);
          break;
        case 'day':
          now.setDate(now.getDate() - amount);
          break;
        case 'week':
          now.setDate(now.getDate() - (amount * 7));
          break;
        case 'month':
          now.setMonth(now.getMonth() - amount);
          break;
      }
      
      return now.toISOString();
    }
  }
  
  return null;
}