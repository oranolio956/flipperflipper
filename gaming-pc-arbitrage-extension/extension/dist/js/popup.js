// Popup v3.2.0
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('open-dashboard').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'OPEN_DASHBOARD' });
    window.close();
  });
  
  document.getElementById('scan-current').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'SCAN_CURRENT_TAB' });
    window.close();
  });
});