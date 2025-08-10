/**
 * Facebook Marketplace Parser
 * Implements platform-specific parsing for Facebook listings
 */

import { ParserStrategy, ParsedListing } from './index';
import { Platform, Listing } from '../types';

export class FacebookParser implements ParserStrategy {
  platform: Platform = 'facebook';
  
  canParse(url: string): boolean {
    return url.includes('facebook.com') || url.includes('fb.com');
  }
  
  parse(document: Document): ParsedListing {
    // Facebook uses React with dynamic rendering, so we need multiple strategies
    
    // Extract title - try multiple selectors
    const title = this.extractText(document, [
      '[data-testid="marketplace-pdp-title"]',
      'h1 span',
      '[role="main"] h1',
      '.dati1w0a.qt6c0cv9.hv4rvrfc span',
    ]) || 'Unknown Item';
    
    // Extract price
    const priceText = this.extractText(document, [
      '[data-testid="marketplace-pdp-price"]',
      '[aria-label*="Price"]',
      'div[class*="price"] span',
      '.d2edcug0.hpfvmrgz span',
    ]) || '0';
    const price = this.parsePrice(priceText);
    
    // Extract description
    const description = this.extractText(document, [
      '[data-testid="marketplace-pdp-description"]',
      '[class*="description"] span',
      'div[data-testid="marketplace-pdp-component"] div[dir="auto"]',
      '.ii04i59q.j83agx80 span',
    ]) || '';
    
    // Extract images
    const images = this.extractImages(document);
    
    // Extract location
    const locationText = this.extractText(document, [
      '[aria-label*="Location"]',
      '[data-testid="marketplace-pdp-location"]',
      'a[href*="location"] span',
      '.oajrlxb2.g5ia77u1 span',
    ]) || '';
    const location = this.parseLocation(locationText);
    
    // Extract seller info
    const sellerName = this.extractText(document, [
      '[data-testid="marketplace-pdp-seller-name"]',
      'a[href*="/profile/"] span',
      '[aria-label*="Seller"] span',
      '.qzhwtbm6.knvmm38d span',
    ]) || 'Unknown Seller';
    
    const sellerProfileUrl = this.extractAttribute(document, [
      'a[href*="/profile/"]',
      '[data-testid="marketplace-pdp-seller-name"] a',
    ], 'href');
    
    return {
      url: window.location.href,
      platform: this.platform,
      title,
      description,
      price,
      images,
      location,
      seller: {
        name: sellerName,
        profileUrl: sellerProfileUrl,
      },
    };
  }
  
  extractSellerInfo(document: Document): Listing['seller'] {
    const name = this.extractText(document, [
      '[data-testid="marketplace-pdp-seller-name"]',
      'a[href*="/profile/"] span',
    ]) || 'Unknown Seller';
    
    const profileUrl = this.extractAttribute(document, [
      'a[href*="/profile/"]',
      '[data-testid="marketplace-pdp-seller-name"] a',
    ], 'href');
    
    // Try to extract member since date
    const memberSinceText = this.extractText(document, [
      '[aria-label*="Joined"]',
      'span:contains("Joined")',
      '.rq0escxv.l9j0dhe7:contains("member")',
    ]);
    
    // Try to extract response rate
    const responseRateText = this.extractText(document, [
      '[aria-label*="response"]',
      'span:contains("responds")',
    ]);
    
    const responseRate = responseRateText ? this.parseResponseRate(responseRateText) : undefined;
    
    // Extract seller ID from profile URL
    const sellerId = profileUrl ? this.extractSellerIdFromUrl(profileUrl) : name;
    
    return {
      id: sellerId,
      name,
      profileUrl,
      memberSince: memberSinceText ? new Date(memberSinceText) : undefined,
      responseRate,
      verified: this.checkIfVerified(document),
    };
  }
  
  extractImages(document: Document): Listing['images'] {
    const images: Listing['images'] = [];
    
    // Main image
    const mainImageSelectors = [
      '[data-testid="marketplace-pdp-image"] img',
      '[role="img"][style*="background-image"]',
      '.x1n2onr6.x1ja2u2z img',
    ];
    
    for (const selector of mainImageSelectors) {
      const elements = document.querySelectorAll(selector);
      elements.forEach((el, index) => {
        let url = '';
        
        if (el instanceof HTMLImageElement) {
          url = el.src;
        } else {
          // Extract from background-image style
          const style = (el as HTMLElement).style.backgroundImage;
          const match = style.match(/url\("?(.+?)"?\)/);
          if (match) url = match[1];
        }
        
        if (url && !url.includes('static.xx.fbcdn.net/rsrc')) { // Filter out FB UI images
          images.push({
            url,
            primary: index === 0,
          });
        }
      });
    }
    
    // Thumbnail images
    const thumbnailSelectors = [
      '[data-testid="marketplace-pdp-thumbnails"] img',
      '[role="button"] img[height="60"]',
    ];
    
    for (const selector of thumbnailSelectors) {
      const elements = document.querySelectorAll<HTMLImageElement>(selector);
      elements.forEach(img => {
        if (img.src && !images.some(i => i.url === img.src)) {
          images.push({
            url: img.src,
            primary: false,
          });
        }
      });
    }
    
    return images;
  }
  
  // Helper methods
  
  private extractText(document: Document, selectors: string[]): string | undefined {
    for (const selector of selectors) {
      try {
        const element = document.querySelector(selector);
        if (element?.textContent) {
          return element.textContent.trim();
        }
      } catch (e) {
        // Some selectors might be invalid, continue trying
        continue;
      }
    }
    return undefined;
  }
  
  private extractAttribute(document: Document, selectors: string[], attribute: string): string | undefined {
    for (const selector of selectors) {
      try {
        const element = document.querySelector(selector);
        if (element) {
          return element.getAttribute(attribute) || undefined;
        }
      } catch (e) {
        continue;
      }
    }
    return undefined;
  }
  
  private parsePrice(priceText: string): number {
    // Remove currency symbols and parse
    const cleanPrice = priceText.replace(/[^0-9.,]/g, '');
    const price = parseFloat(cleanPrice.replace(',', ''));
    return isNaN(price) ? 0 : price;
  }
  
  private parseLocation(locationText: string): ParsedListing['location'] {
    // Facebook location format: "City, State" or "City, State·X miles away"
    const parts = locationText.split('·')[0].split(',');
    const city = parts[0]?.trim() || 'Unknown';
    const state = parts[1]?.trim() || 'Unknown';
    
    // Extract distance if present
    const distanceMatch = locationText.match(/(\d+)\s*miles?\s*away/i);
    const distance = distanceMatch ? parseInt(distanceMatch[1]) : undefined;
    
    return { city, state, distance };
  }
  
  private parseResponseRate(text: string): number | undefined {
    // Parse "Usually responds within X hours" or "X% response rate"
    const percentMatch = text.match(/(\d+)%/);
    if (percentMatch) {
      return parseInt(percentMatch[1]);
    }
    
    // Convert time-based response to percentage estimate
    if (text.includes('within an hour') || text.includes('within 1 hour')) {
      return 95;
    } else if (text.includes('within a few hours')) {
      return 85;
    } else if (text.includes('within a day')) {
      return 70;
    }
    
    return undefined;
  }
  
  private extractSellerIdFromUrl(url: string): string {
    // Extract user ID from Facebook profile URL
    // Format: /profile.php?id=123456 or /username
    const idMatch = url.match(/id=(\d+)/);
    if (idMatch) return idMatch[1];
    
    const usernameMatch = url.match(/facebook\.com\/([^/?]+)/);
    if (usernameMatch) return usernameMatch[1];
    
    return url;
  }
  
  private checkIfVerified(document: Document): boolean {
    // Check for verification badges
    const verifiedSelectors = [
      '[aria-label*="Verified"]',
      '[data-testid="verified-badge"]',
      'img[src*="verified"]',
    ];
    
    for (const selector of verifiedSelectors) {
      if (document.querySelector(selector)) {
        return true;
      }
    }
    
    return false;
  }
}