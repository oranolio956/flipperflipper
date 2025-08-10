/**
 * Craigslist Parser
 * Implements platform-specific parsing for Craigslist listings
 */

import { ParserStrategy, ParsedListing } from './index';
import { Platform, Listing } from '../types';

export class CraigslistParser implements ParserStrategy {
  platform: Platform = 'craigslist';
  
  canParse(url: string): boolean {
    return url.includes('craigslist.org');
  }
  
  parse(document: Document): ParsedListing {
    // Craigslist has a simpler structure
    const title = document.querySelector('#titletextonly')?.textContent || 
                 document.querySelector('.postingtitletext')?.textContent || 
                 'Unknown Item';
    
    const priceElement = document.querySelector('.price');
    const price = priceElement ? parseFloat(priceElement.textContent!.replace(/[^0-9]/g, '')) : 0;
    
    const description = document.querySelector('#postingbody')?.textContent || '';
    
    // Extract images
    const images: string[] = [];
    // Gallery thumbnails - get the href from anchor tags
    document.querySelectorAll('.thumb').forEach(thumb => {
      const link = thumb.getAttribute('href');
      if (link) images.push(link);
    });
    // Fallback to img tags
    if (images.length === 0) {
      document.querySelectorAll('.gallery img, .slide img').forEach(img => {
        if (img instanceof HTMLImageElement && img.src) {
          images.push(img.src);
        }
      });
    }
    
    // Location from small tag in title or breadcrumb
    const locationEl = document.querySelector('.postingtitletext small') || 
                      document.querySelector('.postingtitle small');
    const locationFromTitle = locationEl?.textContent?.replace(/[()]/g, '').trim() || '';
    const locationFromBreadcrumb = document.querySelector('.crumb.area a')?.textContent || '';
    const locationText = locationFromTitle || locationFromBreadcrumb || '';
    
    const location = {
      city: locationText.split(',')[0]?.trim() || 'Unknown',
      state: locationText.split(',')[1]?.trim() || 'Unknown',
    };
    
    return {
      url: window.location.href,
      platform: this.platform,
      title,
      description,
      price,
      images,
      location,
      seller: {
        name: 'Craigslist User',
        profileUrl: undefined,
      },
    };
  }
  
  extractSellerInfo(document: Document): Listing['seller'] {
    // Craigslist doesn't expose seller info
    return {
      id: 'anonymous',
      name: 'Craigslist User',
      verified: false,
    };
  }
  
  extractImages(document: Document): Listing['images'] {
    const images: Listing['images'] = [];
    
    document.querySelectorAll('.gallery img, .thumb img').forEach((img, index) => {
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