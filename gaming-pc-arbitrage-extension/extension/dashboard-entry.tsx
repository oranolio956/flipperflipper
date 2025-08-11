
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './src/ui/App';
import './src/ui/design/tokens.css';
import './src/ui/design/global.css';

// Ensure chrome API is available
if (!window.chrome?.runtime) {
  window.chrome = {
    runtime: {
      sendMessage: (msg, cb) => console.log('Mock sendMessage:', msg),
      getURL: (path) => path,
      onMessage: { addListener: () => {} }
    },
    storage: {
      local: {
        get: (keys, cb) => cb({}),
        set: (data, cb) => cb && cb(),
      }
    }
  };
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
