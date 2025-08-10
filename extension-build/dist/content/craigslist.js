// Craigslist Content Script
console.log('Gaming PC Arbitrage - Craigslist content script loaded');

// Listen for scan messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scan') {
    const listing = parseListing();
    sendResponse({ success: true, listing });
  }
});

function parseListing() {
  const listing = {
    platform: 'craigslist',
    url: window.location.href,
    title: '',
    price: 0,
    description: '',
    images: [],
    location: { city: 'Unknown', state: 'Unknown' },
    seller: { name: 'Craigslist User', id: '' }
  };

  // Extract title
  const titleElement = document.querySelector('#titletextonly');
  if (titleElement) {
    listing.title = titleElement.textContent.trim();
  }

  // Extract price
  const priceElement = document.querySelector('.price');
  if (priceElement) {
    const priceText = priceElement.textContent;
    const priceMatch = priceText.match(/\$?([\d,]+)/);
    if (priceMatch) {
      listing.price = parseInt(priceMatch[1].replace(/,/g, ''));
    }
  }

  // Extract description
  const descElement = document.querySelector('#postingbody');
  if (descElement) {
    listing.description = descElement.textContent.trim();
  }

  // Extract images
  document.querySelectorAll('.thumb a').forEach(link => {
    listing.images.push(link.href);
  });

  // Extract location
  const locationElement = document.querySelector('.postingtitletext small');
  if (locationElement) {
    const locationText = locationElement.textContent.replace(/[()]/g, '').trim();
    const parts = locationText.split(',');
    if (parts.length > 0) {
      listing.location.city = parts[0].trim();
      if (parts.length > 1) {
        listing.location.state = parts[1].trim();
      }
    }
  }

  console.log('Parsed listing:', listing);
  return listing;
}