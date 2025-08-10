// Dashboard script
console.log('Dashboard loaded');

// Load deals from storage
chrome.storage.local.get(['deals', 'stats'], (data) => {
  if (data.stats) {
    // Update stat cards with real data
    updateStats(data.stats);
  }
  
  if (data.deals && data.deals.length > 0) {
    // Update deals table with real data
    updateDealsTable(data.deals);
  }
});

function updateStats(stats) {
  // Update stat values if elements exist
  const statElements = {
    activeDeals: document.querySelector('.stat-value'),
    totalProfit: document.querySelectorAll('.stat-value')[1],
    avgROI: document.querySelectorAll('.stat-value')[2],
    successRate: document.querySelectorAll('.stat-value')[3]
  };
  
  if (stats.activeDeals !== undefined && statElements.activeDeals) {
    statElements.activeDeals.textContent = stats.activeDeals;
  }
  if (stats.totalProfit !== undefined && statElements.totalProfit) {
    statElements.totalProfit.textContent = `$${stats.totalProfit.toLocaleString()}`;
  }
  if (stats.avgROI !== undefined && statElements.avgROI) {
    statElements.avgROI.textContent = `${stats.avgROI}%`;
  }
  if (stats.successRate !== undefined && statElements.successRate) {
    statElements.successRate.textContent = `${stats.successRate}%`;
  }
}

function updateDealsTable(deals) {
  const tbody = document.getElementById('dealsTableBody');
  if (!tbody) return;
  
  // Clear existing rows
  tbody.innerHTML = '';
  
  // Add new rows
  deals.slice(0, 10).forEach(deal => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${deal.title || 'Unknown'}</td>
      <td>${deal.platform || 'Unknown'}</td>
      <td>$${deal.price || 0}</td>
      <td>$${deal.estimatedProfit || 0}</td>
      <td><span class="status ${deal.status}">${deal.status || 'active'}</span></td>
      <td>${formatDate(deal.date)}</td>
    `;
    tbody.appendChild(row);
  });
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString();
}