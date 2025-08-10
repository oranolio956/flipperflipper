// Facebook Marketplace Content Script
console.log('Gaming PC Arbitrage - Facebook content script loaded');

// Listen for scan messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scan') {
    const listing = parseListing();
    sendResponse({ success: true, listing });
  }
});

function parseListing() {
  const listing = {
    platform: 'facebook',
    url: window.location.href,
    title: '',
    price: 0,
    description: '',
    images: [],
    location: { city: 'Unknown', state: 'Unknown' },
    seller: { name: 'Unknown', id: '' }
  };

  // Try to extract title
  const titleElement = document.querySelector('h1[class*="title"]') || 
                      document.querySelector('[role="heading"][aria-level="1"]');
  if (titleElement) {
    listing.title = titleElement.textContent.trim();
  }

  // Try to extract price
  const priceElement = document.querySelector('[class*="price"]');
  if (priceElement) {
    const priceText = priceElement.textContent;
    const priceMatch = priceText.match(/\$?([\d,]+)/);
    if (priceMatch) {
      listing.price = parseInt(priceMatch[1].replace(/,/g, ''));
    }
  }

  // Try to extract description
  const descElement = document.querySelector('[class*="description"]');
  if (descElement) {
    listing.description = descElement.textContent.trim();
  }

  // Extract images
  document.querySelectorAll('img[class*="product"], img[class*="listing"]').forEach(img => {
    if (img.src && !img.src.includes('profile')) {
      listing.images.push(img.src);
    }
  });

  console.log('Parsed listing:', listing);
  return listing;
}