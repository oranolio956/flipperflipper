/**
 * Price History Hook
 * Track price changes and display sparkline
 */

import { recordPrice, getPriceHistory, getSparklineData } from '@/lib/watches';

let currentListingId: string | null = null;
let priceObserver: MutationObserver | null = null;

/**
 * Initialize price tracking for current listing
 */
export async function initPriceTracking(listingId: string, initialPrice: number) {
  currentListingId = listingId;
  
  // Record initial price
  await recordPrice(listingId, initialPrice);
  
  // Start observing price changes
  observePriceChanges();
  
  // Add sparkline to UI
  await addSparkline();
}

/**
 * Observe DOM for price changes
 */
function observePriceChanges() {
  if (priceObserver) {
    priceObserver.disconnect();
  }
  
  // Find price element
  const priceElement = findPriceElement();
  if (!priceElement) return;
  
  priceObserver = new MutationObserver(async (mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList' || mutation.type === 'characterData') {
        const newPrice = extractPrice(priceElement);
        if (newPrice && currentListingId) {
          await recordPrice(currentListingId, newPrice);
          await updateSparkline();
        }
      }
    }
  });
  
  priceObserver.observe(priceElement, {
    childList: true,
    characterData: true,
    subtree: true,
  });
}

/**
 * Find price element in DOM
 */
function findPriceElement(): Element | null {
  // Facebook selectors
  const selectors = [
    '[data-testid="marketplace_listing_price"]',
    'span[dir="auto"]:has-text("$")',
    'div[role="main"] span:has-text("$")',
  ];
  
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent?.includes('$')) {
      return el;
    }
  }
  
  // Fallback: find by content
  const spans = document.querySelectorAll('span[dir="auto"]');
  for (const span of spans) {
    if (span.textContent?.match(/^\$[\d,]+$/)) {
      return span;
    }
  }
  
  return null;
}

/**
 * Extract price from element
 */
function extractPrice(element: Element): number | null {
  const text = element.textContent || '';
  const match = text.match(/\$?([\d,]+)/);
  return match ? parseInt(match[1].replace(/,/g, '')) : null;
}

/**
 * Add sparkline to UI
 */
async function addSparkline() {
  if (!currentListingId) return;
  
  const history = await getPriceHistory(currentListingId);
  if (history.length < 2) return;
  
  const sparklineData = getSparklineData(history);
  const container = createSparklineContainer(history, sparklineData);
  
  // Insert after price
  const priceElement = findPriceElement();
  if (priceElement) {
    priceElement.parentElement?.appendChild(container);
  }
}

/**
 * Update existing sparkline
 */
async function updateSparkline() {
  if (!currentListingId) return;
  
  const existing = document.getElementById('arbitrage-sparkline');
  if (!existing) {
    await addSparkline();
    return;
  }
  
  const history = await getPriceHistory(currentListingId);
  const sparklineData = getSparklineData(history);
  
  const polyline = existing.querySelector('polyline');
  if (polyline) {
    polyline.setAttribute('points', sparklineData);
  }
  
  // Update tooltip
  const tooltip = existing.querySelector('.sparkline-tooltip');
  if (tooltip && history.length > 0) {
    const current = history[history.length - 1].price;
    const initial = history[0].price;
    const change = ((current - initial) / initial) * 100;
    
    tooltip.textContent = `${history.length} price points | ${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
  }
}

/**
 * Create sparkline container
 */
function createSparklineContainer(
  history: any[],
  sparklineData: string
): HTMLElement {
  const container = document.createElement('div');
  container.id = 'arbitrage-sparkline';
  container.style.cssText = `
    display: inline-flex;
    align-items: center;
    margin-left: 8px;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
    cursor: help;
  `;
  
  // SVG sparkline
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '60');
  svg.setAttribute('height', '20');
  svg.setAttribute('viewBox', '0 0 100 100');
  
  const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  polyline.setAttribute('points', sparklineData);
  polyline.setAttribute('fill', 'none');
  polyline.setAttribute('stroke', history[history.length - 1].price < history[0].price ? '#10b981' : '#ef4444');
  polyline.setAttribute('stroke-width', '2');
  
  svg.appendChild(polyline);
  container.appendChild(svg);
  
  // Tooltip
  const tooltip = document.createElement('span');
  tooltip.className = 'sparkline-tooltip';
  tooltip.style.cssText = `
    margin-left: 6px;
    font-size: 11px;
    color: #666;
  `;
  
  const current = history[history.length - 1].price;
  const initial = history[0].price;
  const change = ((current - initial) / initial) * 100;
  
  tooltip.textContent = `${history.length} price points | ${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
  container.appendChild(tooltip);
  
  return container;
}

/**
 * Cleanup
 */
export function cleanupPriceTracking() {
  if (priceObserver) {
    priceObserver.disconnect();
    priceObserver = null;
  }
  
  currentListingId = null;
  
  const sparkline = document.getElementById('arbitrage-sparkline');
  if (sparkline) {
    sparkline.remove();
  }
}