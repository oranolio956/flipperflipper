/**
 * Scanner Overlay Injector
 * Injects the scanning UI into marketplace pages
 */

export function injectScanner() {
  // Check if already injected
  if (document.getElementById('arbitrage-scanner-root')) {
    console.log('[Scanner] Already injected');
    return;
  }
  
  // Create container
  const container = document.createElement('div');
  container.id = 'arbitrage-scanner-root';
  container.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 360px;
    max-height: 80vh;
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    pointer-events: none;
  `;
  
  // Create scanner UI
  const scanner = document.createElement('div');
  scanner.style.cssText = `
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    overflow: hidden;
    pointer-events: auto;
    transform: translateX(400px);
    transition: transform 0.3s ease;
  `;
  
  scanner.innerHTML = `
    <div style="padding: 16px; border-bottom: 1px solid #e5e7eb;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">
          PC Arbitrage Scanner
        </h3>
        <button id="scanner-close" style="
          background: none;
          border: none;
          padding: 4px;
          cursor: pointer;
          color: #6b7280;
          font-size: 20px;
          line-height: 1;
        ">×</button>
      </div>
    </div>
    
    <div style="padding: 16px;">
      <button id="scanner-scan-btn" style="
        width: 100%;
        padding: 12px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
      ">
        <span style="display: flex; align-items: center; justify-content: center; gap: 8px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
            <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
            <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
            <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
            <rect x="7" y="7" width="10" height="10"></rect>
          </svg>
          Scan This Page
        </span>
      </button>
      
      <div id="scanner-status" style="
        margin-top: 12px;
        padding: 12px;
        background: #f3f4f6;
        border-radius: 6px;
        font-size: 13px;
        color: #4b5563;
        display: none;
      "></div>
      
      <div id="scanner-results" style="
        margin-top: 12px;
        max-height: 400px;
        overflow-y: auto;
      "></div>
      
      <div style="
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        gap: 8px;
      ">
        <button id="scanner-dashboard" style="
          flex: 1;
          padding: 8px;
          background: #f3f4f6;
          color: #374151;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        ">Dashboard</button>
        
        <button id="scanner-settings" style="
          flex: 1;
          padding: 8px;
          background: #f3f4f6;
          color: #374151;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        ">Settings</button>
      </div>
    </div>
  `;
  
  container.appendChild(scanner);
  document.body.appendChild(container);
  
  // Animate in
  setTimeout(() => {
    scanner.style.transform = 'translateX(0)';
  }, 100);
  
  // Wire up buttons
  const scanBtn = document.getElementById('scanner-scan-btn') as HTMLButtonElement;
  const closeBtn = document.getElementById('scanner-close') as HTMLButtonElement;
  const dashboardBtn = document.getElementById('scanner-dashboard') as HTMLButtonElement;
  const settingsBtn = document.getElementById('scanner-settings') as HTMLButtonElement;
  const statusDiv = document.getElementById('scanner-status') as HTMLDivElement;
  const resultsDiv = document.getElementById('scanner-results') as HTMLDivElement;
  
  scanBtn.addEventListener('click', async () => {
    scanBtn.disabled = true;
    scanBtn.innerHTML = `
      <span style="display: flex; align-items: center; justify-content: center; gap: 8px;">
        <svg class="scanner-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"></path>
        </svg>
        Scanning...
      </span>
    `;
    
    statusDiv.style.display = 'block';
    statusDiv.textContent = 'Analyzing listings on this page...';
    resultsDiv.innerHTML = '';
    
    try {
      // Request scan from content script
      const response = await chrome.runtime.sendMessage({
        action: 'SCAN_PAGE',
        url: window.location.href
      });
      
      if (response.success && response.candidates) {
        const count = response.candidates.length;
        statusDiv.innerHTML = `
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
              <path d="M20 6L9 17l-5-5"></path>
            </svg>
            Found ${count} gaming PC listing${count !== 1 ? 's' : ''}
          </div>
        `;
        
        // Display results
        if (count > 0) {
          resultsDiv.innerHTML = response.candidates.map((listing: any) => `
            <div style="
              padding: 12px;
              border: 1px solid #e5e7eb;
              border-radius: 6px;
              margin-bottom: 8px;
              cursor: pointer;
              transition: all 0.2s;
            " class="scanner-listing" data-url="${listing.url}">
              <div style="font-size: 14px; font-weight: 500; color: #111827; margin-bottom: 4px;">
                ${listing.title}
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 16px; font-weight: 600; color: #059669;">
                  $${listing.price.toLocaleString()}
                </span>
                ${listing.roi ? `
                  <span style="
                    font-size: 12px;
                    padding: 2px 8px;
                    background: ${listing.roi > 0.3 ? '#fef3c7' : '#f3f4f6'};
                    color: ${listing.roi > 0.3 ? '#d97706' : '#6b7280'};
                    border-radius: 4px;
                  ">
                    ${Math.round(listing.roi * 100)}% ROI
                  </span>
                ` : ''}
              </div>
              ${listing.location ? `
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                  📍 ${listing.location}
                </div>
              ` : ''}
            </div>
          `).join('');
          
          // Add click handlers
          resultsDiv.querySelectorAll('.scanner-listing').forEach(el => {
            el.addEventListener('click', () => {
              const url = el.getAttribute('data-url');
              if (url) window.open(url, '_blank');
            });
            
            el.addEventListener('mouseenter', () => {
              (el as HTMLElement).style.borderColor = '#3b82f6';
              (el as HTMLElement).style.background = '#f0f9ff';
            });
            
            el.addEventListener('mouseleave', () => {
              (el as HTMLElement).style.borderColor = '#e5e7eb';
              (el as HTMLElement).style.background = 'white';
            });
          });
        }
      } else {
        statusDiv.innerHTML = `
          <div style="display: flex; align-items: center; gap: 8px; color: #ef4444;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12" y2="16"></line>
            </svg>
            Scan failed. Please try again.
          </div>
        `;
      }
      
    } catch (error) {
      console.error('[Scanner] Scan error:', error);
      statusDiv.innerHTML = `
        <div style="color: #ef4444;">Error: ${error.message}</div>
      `;
    } finally {
      scanBtn.disabled = false;
      scanBtn.innerHTML = `
        <span style="display: flex; align-items: center; justify-content: center; gap: 8px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
            <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
            <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
            <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
            <rect x="7" y="7" width="10" height="10"></rect>
          </svg>
          Scan This Page
        </span>
      `;
    }
  });
  
  closeBtn.addEventListener('click', () => {
    scanner.style.transform = 'translateX(400px)';
    setTimeout(() => container.remove(), 300);
  });
  
  dashboardBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'openDashboard' });
  });
  
  settingsBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'openSettings' });
  });
  
  // Add spinning animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes scanner-spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .scanner-spin {
      animation: scanner-spin 1s linear infinite;
    }
  `;
  document.head.appendChild(style);
  
  console.log('[Scanner] Overlay injected');
}