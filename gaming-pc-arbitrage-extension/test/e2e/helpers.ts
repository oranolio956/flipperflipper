/**
 * E2E Test Helpers
 * Utilities for Playwright end-to-end testing
 */

import { Page, BrowserContext, chromium } from '@playwright/test';
import path from 'path';

export interface ExtensionPage {
  page: Page;
  extensionId: string;
  context: BrowserContext;
}

/**
 * Load extension in browser
 */
export async function loadExtension(): Promise<ExtensionPage> {
  const pathToExtension = path.join(__dirname, '../../dist');
  
  const context = await chromium.launchPersistentContext('', {
    headless: false,
    args: [
      `--disable-extensions-except=${pathToExtension}`,
      `--load-extension=${pathToExtension}`,
    ],
  });
  
  // Get extension ID
  let extensionId = '';
  const backgroundPages = context.backgroundPages();
  if (backgroundPages.length > 0) {
    const url = backgroundPages[0].url();
    extensionId = url.split('/')[2];
  }
  
  // Open extension popup
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  
  return { page, extensionId, context };
}

/**
 * Navigate to marketplace
 */
export async function navigateToMarketplace(
  page: Page,
  platform: 'facebook' | 'craigslist' | 'offerup'
): Promise<void> {
  const urls = {
    facebook: 'https://www.facebook.com/marketplace',
    craigslist: 'https://craigslist.org',
    offerup: 'https://offerup.com',
  };
  
  await page.goto(urls[platform]);
  await page.waitForLoadState('networkidle');
}

/**
 * Mock marketplace listing
 */
export async function mockListing(page: Page, listing: {
  title: string;
  price: number;
  description: string;
  specs?: Record<string, string>;
}): Promise<void> {
  // Inject mock listing into page
  await page.evaluate((listingData) => {
    const mockHtml = `
      <div class="mock-listing" data-testid="listing">
        <h1>${listingData.title}</h1>
        <div class="price">$${listingData.price}</div>
        <div class="description">${listingData.description}</div>
        ${listingData.specs ? `
          <div class="specs">
            ${Object.entries(listingData.specs).map(([key, value]) => 
              `<div class="spec-${key}">${value}</div>`
            ).join('')}
          </div>
        ` : ''}
      </div>
    `;
    document.body.innerHTML = mockHtml;
  }, listing);
}

/**
 * Wait for extension to parse page
 */
export async function waitForParsing(page: Page, timeout = 5000): Promise<void> {
  await page.waitForFunction(
    () => {
      // Check if extension has added its UI elements
      return document.querySelector('[data-extension-parsed="true"]') !== null;
    },
    { timeout }
  );
}

/**
 * Get parsed data from extension
 */
export async function getParsedData(page: Page): Promise<any> {
  return await page.evaluate(() => {
    // Get data from extension's injected elements or storage
    return (window as any).__extensionParsedData || null;
  });
}

/**
 * Simulate user action
 */
export async function simulateUserAction(
  page: Page,
  action: 'click' | 'hover' | 'scroll',
  selector: string
): Promise<void> {
  switch (action) {
    case 'click':
      await page.click(selector);
      break;
    case 'hover':
      await page.hover(selector);
      break;
    case 'scroll':
      await page.evaluate((sel) => {
        document.querySelector(sel)?.scrollIntoView();
      }, selector);
      break;
  }
}

/**
 * Check extension notification
 */
export async function checkNotification(
  page: Page,
  expectedText: string
): Promise<boolean> {
  try {
    await page.waitForSelector('.extension-notification', { timeout: 3000 });
    const text = await page.textContent('.extension-notification');
    return text?.includes(expectedText) || false;
  } catch {
    return false;
  }
}

/**
 * Test data generators
 */
export const testData = {
  validListing: () => ({
    title: 'Gaming PC - RTX 3080, i7-12700K',
    price: 1200,
    description: 'High-end gaming PC with RTX 3080 graphics card and Intel i7-12700K processor. 32GB DDR4 RAM, 1TB NVMe SSD.',
    specs: {
      cpu: 'Intel Core i7-12700K',
      gpu: 'NVIDIA RTX 3080',
      ram: '32GB DDR4 3200MHz',
      storage: '1TB NVMe SSD',
    },
  }),
  
  lowValueListing: () => ({
    title: 'Budget PC',
    price: 300,
    description: 'Basic computer for office work',
    specs: {
      cpu: 'Intel Core i3-10100',
      ram: '8GB DDR4',
    },
  }),
  
  suspiciousListing: () => ({
    title: 'AMAZING DEAL!!! RTX 4090 CHEAP!!!',
    price: 200,
    description: 'Brand new RTX 4090! Must sell TODAY! Cash only! Text me at...',
  }),
};

/**
 * Performance metrics
 */
export async function measurePerformance(
  page: Page,
  operation: () => Promise<void>
): Promise<{
  duration: number;
  memory: { before: number; after: number };
}> {
  // Get initial memory
  const memoryBefore = await page.evaluate(() => {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize;
    }
    return 0;
  });
  
  const start = Date.now();
  await operation();
  const duration = Date.now() - start;
  
  // Get final memory
  const memoryAfter = await page.evaluate(() => {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize;
    }
    return 0;
  });
  
  return {
    duration,
    memory: {
      before: memoryBefore,
      after: memoryAfter,
    },
  };
}

/**
 * Clean up after tests
 */
export async function cleanup(extensionPage: ExtensionPage): Promise<void> {
  await extensionPage.context.close();
}