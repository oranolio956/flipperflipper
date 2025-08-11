// Dashboard v3.2.0
console.log('[Dashboard] Loading v3.2.0...');

document.addEventListener('DOMContentLoaded', async () => {
  const root = document.getElementById('root');
  
  // Get data from storage
  const { listings = [], settings = {} } = await chrome.storage.local.get(['listings', 'settings']);
  
  // Build UI
  root.innerHTML = `
    <div class="container">
      <header>
        <h1>Gaming PC Arbitrage Dashboard</h1>
        <span class="version">v3.2.0</span>
      </header>
      
      <div class="stats">
        <div class="stat-card">
          <h3>Total Listings</h3>
          <p class="stat-value">${listings.length}</p>
        </div>
        <div class="stat-card">
          <h3>Automation</h3>
          <p class="stat-value">${settings.automation?.enabled ? 'ON' : 'OFF'}</p>
        </div>
      </div>
      
      <div class="listings">
        <h2>Recent Listings</h2>
        <div class="listings-grid">
          ${listings.slice(0, 10).map(listing => `
            <div class="listing-card">
              <h4>${listing.title}</h4>
              <p class="price">$${listing.price}</p>
              <p class="platform">${listing.platform}</p>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
});