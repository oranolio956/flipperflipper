// Options page script

// Load saved settings
chrome.storage.local.get('settings', (data) => {
  if (data.settings) {
    document.getElementById('notifications').checked = data.settings.notifications !== false;
    document.getElementById('autoScan').checked = data.settings.autoScan === true;
    document.getElementById('theme').checked = data.settings.theme !== 'light';
    
    if (data.settings.minProfit !== undefined) {
      document.getElementById('minProfit').value = data.settings.minProfit;
    }
    if (data.settings.maxDrive !== undefined) {
      document.getElementById('maxDrive').value = data.settings.maxDrive;
    }
    if (data.settings.targetROI !== undefined) {
      document.getElementById('targetROI').value = data.settings.targetROI;
    }
    if (data.settings.zipCode) {
      document.getElementById('zipCode').value = data.settings.zipCode;
    }
  }
});

// Save settings
document.getElementById('saveSettings').addEventListener('click', () => {
  const settings = {
    notifications: document.getElementById('notifications').checked,
    autoScan: document.getElementById('autoScan').checked,
    theme: document.getElementById('theme').checked ? 'dark' : 'light',
    minProfit: parseInt(document.getElementById('minProfit').value),
    maxDrive: parseInt(document.getElementById('maxDrive').value),
    targetROI: parseInt(document.getElementById('targetROI').value),
    zipCode: document.getElementById('zipCode').value
  };
  
  chrome.storage.local.set({ settings }, () => {
    // Show saved message
    const savedMessage = document.getElementById('savedMessage');
    savedMessage.style.display = 'inline';
    setTimeout(() => {
      savedMessage.style.display = 'none';
    }, 2000);
  });
});