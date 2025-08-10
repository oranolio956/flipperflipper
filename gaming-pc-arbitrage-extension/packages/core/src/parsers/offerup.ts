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
    const title = document.querySelector('[data-testid="item-title"]')?.textContent?.trim() || 
                 document.querySelector('h1[class*="ItemTitle"]')?.textContent?.trim() ||
                 document.querySelector('h1')?.textContent?.trim() ||
                 'Unknown Item';
    
    const priceElement = document.querySelector('[data-testid="item-price"]') ||
                        document.querySelector('[class*="Price"]') ||
                        document.querySelector('span[class*="currency"]');
    const priceText = priceElement?.textContent || '0';
    const price = parseFloat(priceText.replace(/[^0-9.,]/g, '').replace(',', ''));
    
    const description = document.querySelector('[data-testid="item-description"]')?.textContent?.trim() || 
                       document.querySelector('[class*="ItemDescription"]')?.textContent?.trim() ||
                       document.querySelector('div[class*="description"] p')?.textContent?.trim() ||
                       '';
    
    // Extract images
    const images: string[] = [];
    const imageSelectors = [
      'img[data-testid*="image"]',
      '[class*="ItemImage"] img',
      '[class*="carousel"] img',
      'picture img'
    ];
    document.querySelectorAll(imageSelectors.join(', ')).forEach(img => {
      if (img instanceof HTMLImageElement) {
        const src = img.src || (img as any).dataset?.src;
        if (src && !src.includes('placeholder') && !src.includes('avatar')) {
          images.push(src);
        }
      }
    });
    
    // Location
    const locationElement = document.querySelector('[data-testid="item-location"]') ||
                           document.querySelector('a[href*="location"]') ||
                           document.querySelector('[class*="Location"]');
    const locationText = locationElement?.textContent?.trim() || '';
    const location = {
      city: locationText.split(',')[0]?.trim() || 'Unknown',
      state: locationText.split(',')[1]?.trim() || 'Unknown',
    };
    
    // Seller
    const sellerName = document.querySelector('[data-testid="seller-name"]')?.textContent?.trim() || 
                      document.querySelector('a[href*="/profile/"] span')?.textContent?.trim() ||
                      document.querySelector('[class*="SellerInfo"] a')?.textContent?.trim() ||
                      'OfferUp User';
    
    // Seller rating
    const sellerRating = document.querySelector('[data-testid="seller-rating"]')?.textContent?.trim() ||
                        document.querySelector('[class*="rating"]')?.textContent?.trim() ||
                        '';
    
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
        images.push(img.src);
      }
    });
    
    return images;
  }
}