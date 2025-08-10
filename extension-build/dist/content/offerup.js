// OfferUp Content Script
console.log('Gaming PC Arbitrage - OfferUp content script loaded');

// Listen for scan messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scan') {
    const listing = parseListing();
    sendResponse({ success: true, listing });
  }
});

function parseListing() {
  const listing = {
    platform: 'offerup',
    url: window.location.href,
    title: '',
    price: 0,
    description: '',
    images: [],
    location: { city: 'Unknown', state: 'Unknown' },
    seller: { name: 'Unknown', id: '' }
  };

  // Try to extract title
  const titleElement = document.querySelector('[data-testid="item-title"]') ||
                      document.querySelector('h1');
  if (titleElement) {
    listing.title = titleElement.textContent.trim();
  }

  // Try to extract price
  const priceElement = document.querySelector('[data-testid="item-price"]');
  if (priceElement) {
    const priceText = priceElement.textContent;
    const priceMatch = priceText.match(/\$?([\d,]+)/);
    if (priceMatch) {
      listing.price = parseInt(priceMatch[1].replace(/,/g, ''));
    }
  }

  // Try to extract description
  const descElement = document.querySelector('[data-testid="item-description"]');
  if (descElement) {
    listing.description = descElement.textContent.trim();
  }

  // Extract seller name
  const sellerElement = document.querySelector('[data-testid="seller-name"]');
  if (sellerElement) {
    listing.seller.name = sellerElement.textContent.trim();
  }

  console.log('Parsed listing:', listing);
  return listing;
}