// Scanner v3.2.0
console.log('[Scanner] Injected v3.2.0');

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'START_SCAN') {
    console.log('[Scanner] Starting scan...');
    
    // Look for listings on the page
    const listings = [];
    
    // Facebook Marketplace
    if (window.location.hostname.includes('facebook.com')) {
      document.querySelectorAll('[data-testid="marketplace-feed-item"]').forEach((el, i) => {
        const title = el.querySelector('[class*="title"]')?.textContent || '';
        const price = el.querySelector('[class*="price"]')?.textContent || '';
        
        if (title.toLowerCase().includes('gaming') || title.toLowerCase().includes('pc')) {
          listings.push({
            id: 'fb-' + Date.now() + '-' + i,
            title,
            price: parseInt(price.replace(/[^0-9]/g, '')) || 0,
            platform: 'facebook',
            url: window.location.href,
            foundAt: new Date().toISOString()
          });
        }
      });
    }
    
    // Send results back
    chrome.runtime.sendMessage({
      action: 'STORE_SCAN_RESULTS',
      data: { listings }
    });
    
    console.log('[Scanner] Found', listings.length, 'listings');
  }
});