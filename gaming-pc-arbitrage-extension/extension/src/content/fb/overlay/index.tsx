/**
 * Overlay Entry Point
 * Mounts the React overlay app when content script creates container
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { OverlayApp } from './App';
import './styles.css';

// Wait for the container to be created by content script
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    if (mutation.type === 'childList') {
      const container = document.getElementById('arbitrage-overlay-root');
      if (container && !container.hasAttribute('data-mounted')) {
        // Mark as mounted to prevent duplicate renders
        container.setAttribute('data-mounted', 'true');
        
        // Create shadow root for style isolation
        const shadow = container.attachShadow({ mode: 'open' });
        
        // Create app container inside shadow root
        const appContainer = document.createElement('div');
        appContainer.id = 'app';
        shadow.appendChild(appContainer);
        
        // Inject styles into shadow root
        const style = document.createElement('style');
        style.textContent = getOverlayStyles();
        shadow.appendChild(style);
        
        // Mount React app
        const root = ReactDOM.createRoot(appContainer);
        root.render(
          <React.StrictMode>
            <OverlayApp />
          </React.StrictMode>
        );
        
        // Stop observing once mounted
        observer.disconnect();
        break;
      }
    }
  }
});

// Start observing
observer.observe(document.body, {
  childList: true,
  subtree: false,
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  observer.disconnect();
});

/**
 * Get overlay styles for shadow DOM
 * This includes Tailwind styles and component styles
 */
function getOverlayStyles(): string {
  // In production, this would be the compiled CSS
  // For now, return basic styles
  return `
    /* Reset and base styles */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    /* Import Tailwind (in production, this would be compiled) */
    @import url('https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css');
    
    /* Custom overlay styles */
    #app {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: #1a1a1a;
    }
    
    /* Ensure our overlay is on top */
    .fixed {
      position: fixed !important;
      z-index: 9999 !important;
    }
  `;
}