import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import webExtension from 'vite-plugin-web-extension';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    webExtension({
      manifest: () => ({
        manifest_version: 3,
        name: 'Gaming PC Arbitrage Assistant',
        version: '2.0.0',
        description: 'Find profitable gaming PC deals across marketplaces',
        permissions: [
          'storage',
          'notifications',
          'activeTab',
          'scripting',
          'alarms',
          'tabs',
          'idle'
        ],
        host_permissions: [
          'https://*.facebook.com/*',
          'https://*.craigslist.org/*',
          'https://*.offerup.com/*'
        ],
        background: {
          service_worker: 'src/background/index.ts',
          type: 'module'
        },
        action: {
          default_popup: 'popup.html',
          default_icon: {
            '16': 'icons/icon-16.png',
            '32': 'icons/icon-32.png',
            '48': 'icons/icon-48.png',
            '128': 'icons/icon-128.png'
          }
        },
        content_scripts: [
          {
            matches: ['https://*.facebook.com/*'],
            js: ['src/content/facebook.ts'],
            css: ['src/content/overlay.css'],
            run_at: 'document_idle'
          },
          {
            matches: ['https://*.craigslist.org/*'],
            js: ['src/content/craigslist.ts'],
            css: ['src/content/overlay.css'],
            run_at: 'document_idle'
          },
          {
            matches: ['https://*.offerup.com/*'],
            js: ['src/content/offerup.ts'],
            css: ['src/content/overlay.css'],
            run_at: 'document_idle'
          }
        ],
        web_accessible_resources: [
          {
            resources: ['dashboard.html', 'icons/*'],
            matches: ['<all_urls>']
          }
        ],
        icons: {
          '16': 'icons/icon-16.png',
          '32': 'icons/icon-32.png',
          '48': 'icons/icon-48.png',
          '128': 'icons/icon-128.png'
        }
      }),
      additionalInputs: {
        html: ['popup.html', 'dashboard.html', 'options.html'],
        scripts: ['src/popup/index.tsx', 'src/dashboard/index.tsx', 'src/options/index.tsx'],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@arbitrage/core': path.resolve(__dirname, '../packages/core/src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name][extname]';
          }
          return 'assets/[name][extname]';
        },
      },
    },
  },
});