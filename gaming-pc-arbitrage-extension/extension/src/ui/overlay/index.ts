/**
 * Analysis Overlay Component
 * Shows FMV, ROI, and risk assessment on listing pages
 */

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
      <div class="loading">Analyzing listing...</div>
    </div>
  `;
  
  // Close button handler
  const closeBtn = overlay.querySelector('.close-btn');
  closeBtn?.addEventListener('click', () => {
    overlay.remove();
  });
  
  return overlay;
}

export function updateOverlay(overlay: HTMLElement, data: {
  listing: any;
  analysis: {
    fmv: number;
    roi: number;
    risk: { score: number; level: string };
  };
}) {
  const content = overlay.querySelector('.overlay-content');
  if (!content) return;
  
  const { listing, analysis } = data;
  const roiClass = analysis.roi >= 25 ? 'good' : analysis.roi >= 15 ? 'fair' : 'poor';
  const riskClass = analysis.risk.level;
  
  content.innerHTML = `
    <div class="metrics">
      <div class="metric">
        <label>Asking Price</label>
        <span class="value">$${listing.price.toLocaleString()}</span>
      </div>
      <div class="metric">
        <label>Fair Market Value</label>
        <span class="value">$${analysis.fmv.toLocaleString()}</span>
      </div>
      <div class="metric">
        <label>ROI Potential</label>
        <span class="value ${roiClass}">${analysis.roi.toFixed(1)}%</span>
      </div>
      <div class="metric">
        <label>Risk Level</label>
        <span class="value risk-${riskClass}">${analysis.risk.level.toUpperCase()}</span>
      </div>
    </div>
    
    <div class="specs">
      <h4>Detected Specs</h4>
      <ul>
        ${listing.specs?.components?.cpu ? `<li>CPU: ${listing.specs.components.cpu.model}</li>` : ''}
        ${listing.specs?.components?.gpu ? `<li>GPU: ${listing.specs.components.gpu.model}</li>` : ''}
        ${listing.specs?.components?.ram ? `<li>RAM: ${listing.specs.components.ram[0]?.capacity}GB</li>` : ''}
        ${listing.specs?.components?.storage ? `<li>Storage: ${listing.specs.components.storage[0]?.capacity}GB</li>` : ''}
      </ul>
    </div>
    
    <div class="actions">
      <button class="btn btn-primary" data-action="save-deal">
        Track Deal
      </button>
      <button class="btn btn-secondary" data-action="copy-analysis">
        Copy Analysis
      </button>
    </div>
  `;
  
  // Action handlers
  const saveBtn = content.querySelector('[data-action="save-deal"]');
  saveBtn?.addEventListener('click', async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'SAVE_DEAL',
      payload: {
        listing,
        analysis,
        askingPrice: listing.price
      }
    });
    
    if (response.success) {
      (saveBtn as HTMLElement).textContent = 'Saved!';
      (saveBtn as HTMLElement).setAttribute('disabled', 'true');
    }
  });
  
  const copyBtn = content.querySelector('[data-action="copy-analysis"]');
  copyBtn?.addEventListener('click', () => {
    const text = `
PC Arbitrage Analysis
=====================
Asking: $${listing.price}
FMV: $${analysis.fmv}
ROI: ${analysis.roi.toFixed(1)}%
Risk: ${analysis.risk.level}

${listing.specs?.components?.cpu ? `CPU: ${listing.specs.components.cpu.model}` : ''}
${listing.specs?.components?.gpu ? `GPU: ${listing.specs.components.gpu.model}` : ''}
    `.trim();
    
    navigator.clipboard.writeText(text);
    (copyBtn as HTMLElement).textContent = 'Copied!';
    setTimeout(() => {
      (copyBtn as HTMLElement).textContent = 'Copy Analysis';
    }, 2000);
  });
}