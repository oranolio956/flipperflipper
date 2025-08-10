// Popup script
document.getElementById('scanPage').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Send message to content script
  chrome.tabs.sendMessage(tab.id, { action: 'scan' }, (response) => {
    if (response && response.success) {
      document.querySelector('.status').innerHTML = '<strong>Status:</strong> Listing scanned!';
    }
  });
});

document.getElementById('openDashboard').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
});

document.getElementById('openSettings').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});