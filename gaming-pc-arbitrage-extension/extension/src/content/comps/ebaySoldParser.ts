/**
 * eBay Sold Items Parser
 * Extracts sold gaming PC listings from eBay search results
 */

import { CompRecord, normalizeCompTitleToSpecs } from '@/core/comps';
import { generateId } from '@/core';

export function parseEbaySoldItems(): CompRecord[] {
  const comps: CompRecord[] = [];
  
  // eBay sold items have specific selectors
  const soldItems = document.querySelectorAll('.s-item');
  
  soldItems.forEach((item) => {
    try {
      // Check if it's a sold item (has SOLD indicator)
      const soldIndicator = item.querySelector('.s-item__detail--signal') ||
                           item.querySelector('.s-item__purchase-options');
      
      if (!soldIndicator?.textContent?.toLowerCase().includes('sold')) {
        return;
      }
      
      // Extract title
      const titleEl = item.querySelector('.s-item__title');
      const title = titleEl?.textContent?.trim() || '';
      
      // Skip if not gaming PC related
      const lower = title.toLowerCase();
      if (!lower.includes('gaming') && !lower.includes('pc') && 
          !lower.includes('desktop') && !lower.includes('computer')) {
        return;
      }
      
      // Extract price
      const priceEl = item.querySelector('.s-item__price');
      const priceText = priceEl?.textContent || '';
      const priceMatch = priceText.match(/[\d,]+\.?\d*/);
      const price = priceMatch ? parseFloat(priceMatch[0].replace(/,/g, '')) : 0;
      
      if (price === 0) return;
      
      // Extract sold date
      const dateEl = item.querySelector('.s-item__detail--signal');
      const dateText = dateEl?.textContent || '';
      const dateMatch = dateText.match(/Sold\s+(.+)/i);
      const soldDate = dateMatch ? parseSoldDate(dateMatch[1]) : new Date();
      
      // Extract URL
      const linkEl = item.querySelector('.s-item__link');
      const url = linkEl?.getAttribute('href') || '';
      
      // Extract location if available
      const locationEl = item.querySelector('.s-item__location');
      const locationText = locationEl?.textContent || '';
      
      // Extract specs from title
      const specs = normalizeCompTitleToSpecs(title);
      
      const comp: CompRecord = {
        id: generateId(),
        source: 'ebay',
        title,
        price,
        currency: 'USD',
        timestamp: soldDate,
        url,
        ...specs,
      };
      
      // Add location if parsed
      if (locationText) {
        const parts = locationText.split(',');
        if (parts.length >= 2) {
          comp.location = {
            city: parts[0].trim(),
            state: parts[1].trim(),
          };
        }
      }
      
      comps.push(comp);
    } catch (error) {
      console.error('Failed to parse eBay item:', error);
    }
  });
  
  return comps;
}

/**
 * Parse eBay sold date format
 */
function parseSoldDate(dateStr: string): Date {
  const now = new Date();
  const lower = dateStr.toLowerCase().trim();
  
  // Handle relative dates
  if (lower.includes('today')) {
    return now;
  }
  
  if (lower.includes('yesterday')) {
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday;
  }
  
  // Handle "X days ago"
  const daysMatch = lower.match(/(\d+)\s*days?\s*ago/);
  if (daysMatch) {
    const days = parseInt(daysMatch[1]);
    const past = new Date(now);
    past.setDate(past.getDate() - days);
    return past;
  }
  
  // Try to parse absolute date
  try {
    const parsed = new Date(dateStr);
    if (!isNaN(parsed.getTime())) {
      return parsed;
    }
  } catch (e) {
    // Fall through
  }
  
  return now;
}

/**
 * Send comps to background
 */
export function sendCompsToBackground(comps: CompRecord[]) {
  chrome.runtime.sendMessage({
    type: 'SAVE_COMPS',
    comps,
  });
}