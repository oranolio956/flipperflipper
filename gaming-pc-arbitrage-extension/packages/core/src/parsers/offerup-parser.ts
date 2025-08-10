/**
 * OfferUp Parser
 * Implements platform-specific parsing for OfferUp listings
 */

import { ParserStrategy, ParsedListing } from './index';
import { Platform, Listing } from '../types';

export class OfferUpParser implements ParserStrategy {
  platform: Platform = 'offerup';
  
  canParse(url: string): boolean {
    return url.includes('offerup.com');
  }
  
  parse(document: Document): ParsedListing {
    // OfferUp uses React - need to adapt selectors based on their structure
    const title = document.querySelector('h1[class*="title"]')?.textContent || 
                 document.querySelector('[data-testid="item-title"]')?.textContent ||
                 'Unknown Item';
    
    const priceText = document.querySelector('[class*="price"]')?.textContent || '0';
    const price = parseFloat(priceText.replace(/[^0-9]/g, ''));
    
    const description = document.querySelector('[class*="description"]')?.textContent || '';
    
    // Extract images
    const images: string[] = [];
    document.querySelectorAll('[class*="image-gallery"] img').forEach(img => {
      if (img instanceof HTMLImageElement && img.src) {
        images.push(img.src);
      }
    });
    
    // Location
    const locationText = document.querySelector('[class*="location"]')?.textContent || '';
    const location = {
      city: locationText.split(',')[0] || 'Unknown',
      state: locationText.split(',')[1]?.trim() || 'Unknown',
    };
    
    // Seller
    const sellerName = document.querySelector('[class*="seller-name"]')?.textContent || 'OfferUp User';
    
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
        profileUrl: undefined,
      },
    };
  }
  
  extractSellerInfo(document: Document): Listing['seller'] {
    const name = document.querySelector('[class*="seller-name"]')?.textContent || 'OfferUp User';
    
    // Try to extract member since
    const memberText = document.querySelector('[class*="member-since"]')?.textContent;
    
    // Try to extract ratings
    const ratingElement = document.querySelector('[class*="rating"]');
    const rating = ratingElement ? parseFloat(ratingElement.textContent || '0') : undefined;
    
    return {
      id: name,
      name,
      rating,
      verified: !!document.querySelector('[class*="verified"]'),
    };
  }
  
  extractImages(document: Document): Listing['images'] {
    const images: Listing['images'] = [];
    
    document.querySelectorAll('[class*="image-gallery"] img').forEach((img, index) => {
      if (img instanceof HTMLImageElement && img.src) {
        images.push({
          url: img.src,
          primary: index === 0,
        });
      }
    });
    
    return images;
  }
}