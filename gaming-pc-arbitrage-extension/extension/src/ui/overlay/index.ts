/**
 * Analysis Overlay Component
 * Shows FMV, ROI, and risk assessment on listing pages
 */

import { sendMessage } from '../../lib/messages';

export function createOverlay(): HTMLElement {
  const overlay = document.createElement('div');
  overlay.id = 'arbitrage-overlay';
  overlay.className = 'arbitrage-overlay';
  overlay.innerHTML = `
    <div class="overlay-header">
      <h3>PC Arbitrage Analysis</h3>
      <button class="close-btn" aria-label="Close">×</button>
    </div>
    <div class="overlay-content">
      <div class="loading">
        <div class="spinner"></div>
        <p>Analyzing listing...</p>
      </div>
    </div>
  `;
  
  // Add styles
  addOverlayStyles();
  
  // Close button handler
  const closeBtn = overlay.querySelector('.close-btn');
  closeBtn?.addEventListener('click', () => {
    hideOverlay(overlay);
  });
  
  return overlay;
}

export function updateOverlay(overlay: HTMLElement, data: {
  listing?: any;
  analysis?: {
    fmv: number;
    confidence: number;
    breakdown: Array<{ component: string; value: number }>;
  };
  error?: string;
}) {
  const content = overlay.querySelector('.overlay-content');
  if (!content) return;
  
  if (data.error) {
    content.innerHTML = `
      <div class="error">
        <p>⚠️ ${data.error}</p>
        <button class="retry-btn">Retry Analysis</button>
      </div>
    `;
    
    const retryBtn = content.querySelector('.retry-btn');
    retryBtn?.addEventListener('click', () => {
      window.location.reload();
    });
    return;
  }
  
  if (!data.listing || !data.analysis) return;
  
  const { listing, analysis } = data;
  const roi = ((analysis.fmv - listing.price) / listing.price) * 100;
  const profit = analysis.fmv - listing.price;
  
  content.innerHTML = `
    <div class="analysis-results">
      <!-- Price Summary -->
      <div class="price-summary">
        <div class="price-item">
          <span class="label">Asking:</span>
          <span class="value">$${listing.price.toLocaleString()}</span>
        </div>
        <div class="price-item highlight">
          <span class="label">FMV:</span>
          <span class="value">$${analysis.fmv.toLocaleString()}</span>
        </div>
        <div class="price-item ${profit > 0 ? 'positive' : 'negative'}">
          <span class="label">Profit:</span>
          <span class="value">$${profit.toLocaleString()}</span>
        </div>
      </div>
      
      <!-- ROI Indicator -->
      <div class="roi-indicator">
        <div class="roi-value ${roi > 25 ? 'good' : roi > 15 ? 'moderate' : 'poor'}">
          ${roi.toFixed(1)}% ROI
        </div>
        <div class="confidence">
          Confidence: ${(analysis.confidence * 100).toFixed(0)}%
        </div>
      </div>
      
      <!-- Component Breakdown -->
      <div class="component-breakdown">
        <h4>Component Values</h4>
        <div class="components">
          ${analysis.breakdown.map(item => `
            <div class="component-item">
              <span class="name">${item.component}</span>
              <span class="value">$${item.value}</span>
            </div>
          `).join('')}
        </div>
      </div>
      
      <!-- Deal Score -->
      <div class="deal-score">
        <div class="score-bar">
          <div class="score-fill" style="width: ${calculateDealScore(roi, analysis.confidence)}%"></div>
        </div>
        <div class="score-label">
          Deal Score: ${calculateDealScore(roi, analysis.confidence)}/100
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div class="actions">
        <button class="btn btn-primary save-deal">
          💾 Save Deal
        </button>
        <button class="btn btn-secondary copy-link">
          📋 Copy Link
        </button>
        <button class="btn btn-secondary open-dashboard">
          📊 Dashboard
        </button>
      </div>
      
      <!-- Quick Stats -->
      <div class="quick-stats">
        ${listing.components?.cpu ? `<span class="stat">CPU: ${listing.components.cpu.model}</span>` : ''}
        ${listing.components?.gpu ? `<span class="stat">GPU: ${listing.components.gpu.model}</span>` : ''}
        ${listing.components?.ram ? `<span class="stat">RAM: ${listing.components.ram[0]?.capacity || 0}GB</span>` : ''}
      </div>
    </div>
  `;
  
  // Add event handlers
  const saveBtn = content.querySelector('.save-deal');
  saveBtn?.addEventListener('click', async () => {
    saveBtn.textContent = 'Saving...';
    saveBtn.setAttribute('disabled', 'true');
    
    const response = await sendMessage({
      type: 'SAVE_DEAL',
      payload: {
        listing,
        fmv: analysis.fmv,
        notes: `ROI: ${roi.toFixed(1)}%`
      }
    });
    
    if (response.payload.success) {
      saveBtn.textContent = '✓ Saved!';
      
      // Show notification
      await sendMessage({
        type: 'SHOW_NOTIFICATION',
        payload: {
          title: 'Deal Saved!',
          message: `${listing.title} - ${roi.toFixed(1)}% ROI`,
          type: 'success',
          dealId: response.payload.dealId
        }
      });
    } else {
      saveBtn.textContent = '❌ Failed';
      setTimeout(() => {
        saveBtn.textContent = '💾 Save Deal';
        saveBtn.removeAttribute('disabled');
      }, 2000);
    }
  });
  
  const copyBtn = content.querySelector('.copy-link');
  copyBtn?.addEventListener('click', () => {
    navigator.clipboard.writeText(window.location.href);
    copyBtn.textContent = '✓ Copied!';
    setTimeout(() => {
      copyBtn.textContent = '📋 Copy Link';
    }, 2000);
  });
  
  const dashboardBtn = content.querySelector('.open-dashboard');
  dashboardBtn?.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'OPEN_DASHBOARD' });
  });
}

export function hideOverlay(overlay: HTMLElement) {
  overlay.classList.add('hiding');
  setTimeout(() => {
    overlay.remove();
  }, 300);
}

function calculateDealScore(roi: number, confidence: number): number {
  // Simple scoring algorithm
  let score = 0;
  
  // ROI contribution (0-60 points)
  if (roi > 50) score += 60;
  else if (roi > 35) score += 50;
  else if (roi > 25) score += 40;
  else if (roi > 15) score += 25;
  else if (roi > 0) score += 10;
  
  // Confidence contribution (0-40 points)
  score += confidence * 40;
  
  return Math.round(Math.min(100, Math.max(0, score)));
}

function addOverlayStyles() {
  if (document.getElementById('arbitrage-overlay-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'arbitrage-overlay-styles';
  style.textContent = `
    .arbitrage-overlay {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 360px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: #1a1a1a;
      animation: slideIn 0.3s ease-out;
      max-height: 90vh;
      overflow-y: auto;
    }
    
    .arbitrage-overlay.hiding {
      animation: slideOut 0.3s ease-out;
    }
    
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
    
    .overlay-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid #e5e5e5;
      background: #f8f9fa;
      border-radius: 12px 12px 0 0;
    }
    
    .overlay-header h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1a1a1a;
    }
    
    .close-btn {
      width: 32px;
      height: 32px;
      border: none;
      background: none;
      font-size: 24px;
      cursor: pointer;
      border-radius: 6px;
      transition: background 0.2s;
      color: #666;
    }
    
    .close-btn:hover {
      background: rgba(0, 0, 0, 0.05);
    }
    
    .overlay-content {
      padding: 20px;
    }
    
    .loading {
      text-align: center;
      padding: 40px 0;
    }
    
    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid #f0f0f0;
      border-top-color: #2563eb;
      border-radius: 50%;
      margin: 0 auto 16px;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    .error {
      text-align: center;
      padding: 20px;
      color: #dc2626;
    }
    
    .error p {
      margin: 0 0 16px;
    }
    
    .retry-btn {
      padding: 8px 16px;
      background: #dc2626;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
    }
    
    .retry-btn:hover {
      background: #b91c1c;
    }
    
    .price-summary {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
      padding: 16px;
      background: #f8f9fa;
      border-radius: 8px;
    }
    
    .price-item {
      text-align: center;
    }
    
    .price-item .label {
      display: block;
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
    }
    
    .price-item .value {
      display: block;
      font-size: 18px;
      font-weight: 600;
    }
    
    .price-item.highlight .value {
      color: #2563eb;
    }
    
    .price-item.positive .value {
      color: #16a34a;
    }
    
    .price-item.negative .value {
      color: #dc2626;
    }
    
    .roi-indicator {
      text-align: center;
      margin-bottom: 20px;
    }
    
    .roi-value {
      font-size: 36px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    
    .roi-value.good {
      color: #16a34a;
    }
    
    .roi-value.moderate {
      color: #f59e0b;
    }
    
    .roi-value.poor {
      color: #dc2626;
    }
    
    .confidence {
      font-size: 12px;
      color: #666;
    }
    
    .component-breakdown {
      margin-bottom: 20px;
    }
    
    .component-breakdown h4 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 600;
      color: #666;
    }
    
    .components {
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      overflow: hidden;
    }
    
    .component-item {
      display: flex;
      justify-content: space-between;
      padding: 10px 16px;
      border-bottom: 1px solid #f0f0f0;
    }
    
    .component-item:last-child {
      border-bottom: none;
    }
    
    .component-item .name {
      color: #666;
      font-size: 13px;
    }
    
    .component-item .value {
      font-weight: 600;
      font-size: 13px;
    }
    
    .deal-score {
      margin-bottom: 20px;
    }
    
    .score-bar {
      height: 8px;
      background: #e5e5e5;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    
    .score-fill {
      height: 100%;
      background: linear-gradient(90deg, #dc2626 0%, #f59e0b 50%, #16a34a 100%);
      transition: width 0.5s ease-out;
    }
    
    .score-label {
      font-size: 12px;
      color: #666;
      text-align: center;
    }
    
    .actions {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }
    
    .btn {
      flex: 1;
      padding: 10px 12px;
      border: none;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      text-align: center;
    }
    
    .btn:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
    
    .btn-primary {
      background: #2563eb;
      color: white;
    }
    
    .btn-primary:hover:not(:disabled) {
      background: #1d4ed8;
    }
    
    .btn-secondary {
      background: #f3f4f6;
      color: #374151;
    }
    
    .btn-secondary:hover:not(:disabled) {
      background: #e5e7eb;
    }
    
    .quick-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding-top: 16px;
      border-top: 1px solid #e5e5e5;
    }
    
    .stat {
      padding: 4px 8px;
      background: #f3f4f6;
      border-radius: 4px;
      font-size: 12px;
      color: #666;
    }
  `;
  
  document.head.appendChild(style);
}