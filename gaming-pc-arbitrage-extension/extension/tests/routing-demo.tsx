import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from '../src/ui/App';
import { prettyDOM } from '@testing-library/react';

// Mock chrome API
(window as any).chrome = {
  storage: {
    local: {
      get: (keys: string[], callback: Function) => callback({}),
      set: (data: any, callback?: Function) => callback?.(),
    },
  },
  runtime: {
    sendMessage: (msg: any) => Promise.resolve({}),
  },
  tabs: {
    query: (opts: any, callback: Function) => callback([]),
    sendMessage: (tabId: number, msg: any) => Promise.resolve({}),
  },
};

// Create test container
const container = document.createElement('div');
container.id = 'test-root';
document.body.appendChild(container);

// Render app
const root = ReactDOM.createRoot(container);
root.render(<App />);

// Wait for render and capture DOM snapshots
setTimeout(() => {
  console.log('=== DASHBOARD DOM SNAPSHOT ===');
  const dashboardSection = document.querySelector('.dashboard-page');
  if (dashboardSection) {
    console.log(prettyDOM(dashboardSection, 1000, { highlight: false }));
  }

  // Navigate to Scanner
  window.location.hash = '#/scanner';
  
  setTimeout(() => {
    console.log('\n=== SCANNER DOM SNAPSHOT ===');
    const scannerSection = document.querySelector('.scanner-page');
    if (scannerSection) {
      console.log(prettyDOM(scannerSection, 1000, { highlight: false }));
    }

    // Navigate to Listing Detail
    window.location.hash = '#/listing/test-123';
    
    setTimeout(() => {
      console.log('\n=== LISTING DETAIL DOM SNAPSHOT ===');
      const listingSection = document.querySelector('.listing-detail-page');
      if (listingSection) {
        console.log(prettyDOM(listingSection, 1000, { highlight: false }));
      }

      // Show all routes
      console.log('\n=== ALL NAVIGATION LINKS ===');
      const navLinks = document.querySelectorAll('.nav-link');
      navLinks.forEach((link) => {
        const href = link.getAttribute('href');
        const text = link.textContent?.trim();
        console.log(`- ${text}: ${href}`);
      });
    }, 100);
  }, 100);
}, 100);