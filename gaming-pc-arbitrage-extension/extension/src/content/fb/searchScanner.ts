/**
 * Facebook Search Scanner
 * Parse all visible listings on search results page
 */

import { generateId } from '@/core';
import { FMVCalculator } from '@/core/calculators/fmv-calculator';
import { RiskEngine } from '@/core/risk/risk-engine';
import { ComponentDetector } from '@/core/parsers/component-detector';

export interface QuickListing {
  id: string;
  title: string;
  price: number;
  location: string;
  thumbnail?: string;
  url: string;
  daysListed?: number;
  
  // Quick analysis
  components?: {
    cpu?: string;
    gpu?: string;
    ram?: number;
    storage?: number;
  };
  fmv?: number;
  roi?: number;
  riskScore?: number;
  dealScore?: number;
}

/**
 * Scan all visible listings on search page
 */
export function scanSearchResults(): QuickListing[] {
  const listings: QuickListing[] = [];
  
  // Facebook search results selectors
  const resultCards = document.querySelectorAll(
    '[data-testid="marketplace-search-result"],' +
    'a[href*="/marketplace/item/"],' +
    'div[role="article"] a[href*="/marketplace/"]'
  );
  
  const fmvCalculator = new FMVCalculator();
  const riskEngine = new RiskEngine();
  const detector = new ComponentDetector();
  
  resultCards.forEach((card) => {
    try {
      // Extract basic info
      const titleEl = card.querySelector('span[dir="auto"]') ||
                     card.querySelector('[role="heading"]');
      const title = titleEl?.textContent?.trim() || '';
      
      // Skip if not gaming PC related
      const keywords = ['gaming', 'pc', 'desktop', 'computer', 'rtx', 'gtx', 'ryzen', 'intel'];
      if (!keywords.some(kw => title.toLowerCase().includes(kw))) {
        return;
      }
      
      // Price
      const priceEl = card.querySelector('span[dir="auto"]');
      const priceText = Array.from(card.querySelectorAll('span'))
        .find(el => el.textContent?.includes('$'))?.textContent || '';
      const priceMatch = priceText.match(/\$?([\d,]+)/);
      const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0;
      
      if (price === 0) return;
      
      // Location
      const locationEl = Array.from(card.querySelectorAll('span'))
        .find(el => el.textContent?.includes(','));
      const location = locationEl?.textContent?.trim() || 'Unknown';
      
      // Thumbnail
      const imgEl = card.querySelector('img');
      const thumbnail = imgEl?.src;
      
      // URL
      const linkEl = card.tagName === 'A' ? card : card.querySelector('a');
      const url = (linkEl as HTMLAnchorElement)?.href || '';
      
      // Days listed (if shown)
      const timeEl = Array.from(card.querySelectorAll('span'))
        .find(el => el.textContent?.match(/\d+\s*(hour|day|week)/));
      let daysListed = 0;
      if (timeEl) {
        const timeText = timeEl.textContent || '';
        if (timeText.includes('hour')) daysListed = 0;
        else if (timeText.includes('day')) {
          const days = parseInt(timeText.match(/\d+/)?.[0] || '1');
          daysListed = days;
        } else if (timeText.includes('week')) {
          const weeks = parseInt(timeText.match(/\d+/)?.[0] || '1');
          daysListed = weeks * 7;
        }
      }
      
      // Quick component detection
      const components = detector.detectAll(title);
      const componentSummary = {
        cpu: components.cpu?.model,
        gpu: components.gpu?.model,
        ram: components.ram?.reduce((sum, r) => sum + (r.capacity || 0), 0),
        storage: components.storage?.reduce((sum, s) => sum + (s.capacity || 0), 0),
      };
      
      // Quick FMV calculation
      let fmv = 0;
      let roi = 0;
      let dealScore = 0;
      
      if (components.cpu || components.gpu) {
        const value = fmvCalculator.calculateSystemValue({
          cpu: components.cpu,
          gpu: components.gpu,
          ram: components.ram || [],
          storage: components.storage || [],
        });
        
        fmv = value.totalValue.fmv;
        roi = ((fmv - price) / price) * 100;
        
        // Deal score factors in ROI and days listed
        dealScore = roi - (daysListed * 2); // Penalize older listings
      }
      
      // Quick risk assessment
      const riskScore = 0; // Would need full listing data for real risk
      
      listings.push({
        id: generateId(),
        title,
        price,
        location,
        thumbnail,
        url,
        daysListed,
        components: componentSummary,
        fmv,
        roi: Math.round(roi),
        riskScore,
        dealScore: Math.round(dealScore),
      });
    } catch (error) {
      console.error('Failed to parse listing card:', error);
    }
  });
  
  // Sort by deal score
  return listings.sort((a, b) => (b.dealScore || 0) - (a.dealScore || 0));
}

/**
 * Create results panel UI
 */
export function createResultsPanel(listings: QuickListing[]) {
  // Remove existing panel
  const existing = document.getElementById('arbitrage-scanner-panel');
  if (existing) existing.remove();
  
  const panel = document.createElement('div');
  panel.id = 'arbitrage-scanner-panel';
  panel.innerHTML = `
    <div class="scanner-header">
      <h3>Scan Results (${listings.length})</h3>
      <button class="close-btn">×</button>
    </div>
    <div class="scanner-filters">
      <select class="filter-select" id="sort-by">
        <option value="dealScore">Deal Score</option>
        <option value="roi">ROI %</option>
        <option value="price">Price</option>
        <option value="daysListed">Days Listed</option>
      </select>
      <input type="number" class="filter-input" id="min-roi" placeholder="Min ROI %">
    </div>
    <div class="scanner-results">
      ${listings.map(listing => `
        <div class="result-card" data-id="${listing.id}">
          <div class="result-main">
            ${listing.thumbnail ? `<img src="${listing.thumbnail}" alt="">` : ''}
            <div class="result-info">
              <h4>${listing.title}</h4>
              <div class="result-details">
                <span class="price">$${listing.price.toLocaleString()}</span>
                ${listing.fmv ? `<span class="fmv">FMV: $${listing.fmv.toLocaleString()}</span>` : ''}
                ${listing.roi ? `<span class="roi ${listing.roi > 20 ? 'good' : listing.roi > 0 ? 'ok' : 'bad'}">ROI: ${listing.roi}%</span>` : ''}
              </div>
              <div class="result-specs">
                ${listing.components?.gpu ? `<span class="spec">GPU: ${listing.components.gpu}</span>` : ''}
                ${listing.components?.cpu ? `<span class="spec">CPU: ${listing.components.cpu}</span>` : ''}
              </div>
              <div class="result-meta">
                <span>${listing.location}</span>
                ${listing.daysListed !== undefined ? `<span>${listing.daysListed}d ago</span>` : ''}
              </div>
            </div>
          </div>
          <div class="result-actions">
            <button class="open-btn" data-url="${listing.url}">Open</button>
            <button class="track-btn" data-id="${listing.id}">Track</button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    #arbitrage-scanner-panel {
      position: fixed;
      right: 20px;
      top: 20px;
      bottom: 20px;
      width: 400px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      z-index: 10000;
      display: flex;
      flex-direction: column;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .scanner-header {
      padding: 16px 20px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .scanner-header h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
    
    .close-btn {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: #6b7280;
    }
    
    .scanner-filters {
      padding: 12px 20px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      gap: 8px;
    }
    
    .filter-select, .filter-input {
      padding: 6px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
    }
    
    .scanner-results {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
    }
    
    .result-card {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 8px;
    }
    
    .result-main {
      display: flex;
      gap: 12px;
      margin-bottom: 8px;
    }
    
    .result-card img {
      width: 60px;
      height: 60px;
      object-fit: cover;
      border-radius: 6px;
    }
    
    .result-info {
      flex: 1;
    }
    
    .result-info h4 {
      margin: 0 0 4px 0;
      font-size: 14px;
      font-weight: 600;
      line-height: 1.2;
    }
    
    .result-details {
      display: flex;
      gap: 8px;
      margin-bottom: 4px;
      font-size: 13px;
    }
    
    .price {
      font-weight: 600;
    }
    
    .fmv {
      color: #6b7280;
    }
    
    .roi {
      font-weight: 500;
    }
    
    .roi.good { color: #10b981; }
    .roi.ok { color: #f59e0b; }
    .roi.bad { color: #ef4444; }
    
    .result-specs {
      display: flex;
      gap: 8px;
      margin-bottom: 4px;
      font-size: 12px;
    }
    
    .spec {
      background: #e5e7eb;
      padding: 2px 6px;
      border-radius: 4px;
    }
    
    .result-meta {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #6b7280;
    }
    
    .result-actions {
      display: flex;
      gap: 8px;
    }
    
    .open-btn, .track-btn {
      flex: 1;
      padding: 6px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      background: white;
      font-size: 13px;
      cursor: pointer;
    }
    
    .open-btn:hover, .track-btn:hover {
      background: #f3f4f6;
    }
  `;
  
  document.head.appendChild(style);
  document.body.appendChild(panel);
  
  // Add event listeners
  panel.querySelector('.close-btn')?.addEventListener('click', () => {
    panel.remove();
    style.remove();
  });
  
  // Open listing
  panel.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    if (target.classList.contains('open-btn')) {
      const url = target.getAttribute('data-url');
      if (url) window.open(url, '_blank');
    }
  });
  
  // Sort functionality
  const sortSelect = panel.querySelector('#sort-by') as HTMLSelectElement;
  sortSelect?.addEventListener('change', () => {
    const sortedListings = [...listings].sort((a, b) => {
      const key = sortSelect.value as keyof QuickListing;
      return (b[key] as number || 0) - (a[key] as number || 0);
    });
    updateResults(sortedListings);
  });
  
  // Filter functionality
  const minRoiInput = panel.querySelector('#min-roi') as HTMLInputElement;
  minRoiInput?.addEventListener('input', () => {
    const minRoi = parseInt(minRoiInput.value) || 0;
    const filtered = listings.filter(l => (l.roi || 0) >= minRoi);
    updateResults(filtered);
  });
  
  function updateResults(newListings: QuickListing[]) {
    const resultsEl = panel.querySelector('.scanner-results');
    if (resultsEl) {
      resultsEl.innerHTML = newListings.map(listing => `
        <div class="result-card" data-id="${listing.id}">
          <!-- Same content as above -->
        </div>
      `).join('');
    }
  }
}