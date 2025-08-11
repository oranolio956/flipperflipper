// Routing Smoke Test v3.2.0
// Tests that all navigation routes work correctly

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

describe('Routing Smoke Tests', () => {
  let browser;
  let page;
  const extensionPath = path.join(__dirname, '..');
  
  beforeAll(async () => {
    // Launch browser with extension
    browser = await puppeteer.launch({
      headless: false, // Set to true for CI
      args: [
        `--disable-extensions-except=${extensionPath}`,
        `--load-extension=${extensionPath}`
      ]
    });
  });
  
  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });
  
  beforeEach(async () => {
    // Get extension ID
    const targets = await browser.targets();
    const extensionTarget = targets.find(target => 
      target.type() === 'service_worker' || 
      target.type() === 'background_page'
    );
    
    if (!extensionTarget) {
      throw new Error('Extension not loaded');
    }
    
    const extensionUrl = extensionTarget.url();
    const [,, extensionId] = extensionUrl.split('/');
    
    // Open dashboard
    page = await browser.newPage();
    await page.goto(`chrome-extension://${extensionId}/dashboard.html`);
    await page.waitForSelector('.app-container', { timeout: 5000 });
  });
  
  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });
  
  test('Dashboard loads with correct title', async () => {
    const title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Dashboard');
  });
  
  test('All navigation links are present', async () => {
    const navLinks = await page.$$eval('.nav-link', links => 
      links.map(link => ({
        text: link.querySelector('.nav-text')?.textContent,
        testId: link.getAttribute('data-testid')
      }))
    );
    
    const expectedRoutes = [
      'Dashboard', 'Scanner', 'Pipeline', 'Inventory', 'Routes', 
      'Finance', 'Comps', 'Analytics', 'Experiments', 'Automation',
      'Team', 'Settings', 'Integrations', 'Help', 'Features'
    ];
    
    expectedRoutes.forEach(route => {
      expect(navLinks.some(link => link.text === route)).toBe(true);
    });
  });
  
  test('Navigation to each route updates page title', async () => {
    const routes = [
      { selector: '[data-testid="route-scanner"]', title: 'Scanner' },
      { selector: '[data-testid="route-pipeline"]', title: 'Pipeline' },
      { selector: '[data-testid="route-settings"]', title: 'Settings' },
      { selector: '[data-testid="route-automation"]', title: 'Automation' }
    ];
    
    for (const route of routes) {
      await page.click(route.selector);
      await page.waitForTimeout(100); // Wait for navigation
      
      const currentTitle = await page.$eval('[data-testid="page-title"]', el => el.textContent);
      expect(currentTitle).toBe(route.title);
      
      // Check active state
      const isActive = await page.$eval(route.selector, el => el.classList.contains('active'));
      expect(isActive).toBe(true);
    }
  });
  
  test('Dashboard quick action button works', async () => {
    // Navigate away from dashboard
    await page.click('[data-testid="route-settings"]');
    await page.waitForTimeout(100);
    
    // Click dashboard button
    await page.click('#btn-dashboard');
    await page.waitForTimeout(100);
    
    const title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Dashboard');
  });
  
  test('Settings quick action button works', async () => {
    // Make sure we're not on settings
    await page.click('[data-testid="route-dashboard"]');
    await page.waitForTimeout(100);
    
    // Click settings button
    await page.click('#btn-settings');
    await page.waitForTimeout(100);
    
    const title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Settings');
  });
  
  test('Version HUD is visible and clickable', async () => {
    const versionHud = await page.$('.version-hud');
    expect(versionHud).toBeTruthy();
    
    // Check version text
    const versionText = await page.$eval('.version-text', el => el.textContent);
    expect(versionText).toBe('v3.2.0');
    
    // Click to expand
    await page.click('.version-hud');
    await page.waitForTimeout(100);
    
    // Check details are visible
    const detailsVisible = await page.$eval('.version-details', el => 
      window.getComputedStyle(el).display !== 'none'
    );
    expect(detailsVisible).toBe(true);
  });
  
  test('Browser back/forward navigation works', async () => {
    // Navigate through multiple pages
    await page.click('[data-testid="route-scanner"]');
    await page.waitForTimeout(100);
    
    await page.click('[data-testid="route-pipeline"]');
    await page.waitForTimeout(100);
    
    await page.click('[data-testid="route-settings"]');
    await page.waitForTimeout(100);
    
    // Go back
    await page.goBack();
    await page.waitForTimeout(100);
    
    let title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Pipeline');
    
    // Go back again
    await page.goBack();
    await page.waitForTimeout(100);
    
    title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Scanner');
    
    // Go forward
    await page.goForward();
    await page.waitForTimeout(100);
    
    title = await page.$eval('[data-testid="page-title"]', el => el.textContent);
    expect(title).toBe('Pipeline');
  });
});

// Alternative: Manual test runner for environments without Puppeteer
if (typeof window !== 'undefined') {
  window.runManualRoutingTests = async function() {
    console.log('🧪 Running Manual Routing Tests...\n');
    
    const results = [];
    
    // Test 1: Check all routes exist
    console.log('Test 1: Checking all routes...');
    const navLinks = document.querySelectorAll('.nav-link');
    const expectedCount = 15;
    results.push({
      test: 'All navigation links present',
      pass: navLinks.length === expectedCount,
      message: `Found ${navLinks.length} of ${expectedCount} expected links`
    });
    
    // Test 2: Test navigation
    console.log('Test 2: Testing navigation...');
    const scannerLink = document.querySelector('[data-testid="route-scanner"]');
    if (scannerLink) {
      scannerLink.click();
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const title = document.querySelector('[data-testid="page-title"]')?.textContent;
      results.push({
        test: 'Navigation to Scanner',
        pass: title === 'Scanner',
        message: `Page title: ${title}`
      });
    }
    
    // Test 3: Test quick actions
    console.log('Test 3: Testing quick action buttons...');
    const dashboardBtn = document.getElementById('btn-dashboard');
    if (dashboardBtn) {
      dashboardBtn.click();
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const title = document.querySelector('[data-testid="page-title"]')?.textContent;
      results.push({
        test: 'Dashboard quick action',
        pass: title === 'Dashboard',
        message: `Page title: ${title}`
      });
    }
    
    // Print results
    console.log('\n📊 Test Results:');
    results.forEach(result => {
      console.log(`${result.pass ? '✅' : '❌'} ${result.test}: ${result.message}`);
    });
    
    const passed = results.filter(r => r.pass).length;
    const total = results.length;
    console.log(`\n🏁 Total: ${passed}/${total} tests passed`);
    
    return results;
  };
}