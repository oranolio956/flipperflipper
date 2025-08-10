import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import webExtension from 'vite-plugin-web-extension';
import { resolve } from 'path';
import fs from 'fs';

export default defineConfig({
  plugins: [
    react(),
    webExtension({
      manifest: () => ({
        ...JSON.parse(fs.readFileSync('./manifest.json', 'utf-8')),
        // Add development-specific overrides if needed
      }),
      additionalInputs: [
        'src/background/index.ts',
        'src/content/fb/index.ts',
        'src/content/craigslist/index.ts',
        'src/content/offerup/index.ts',
        'public/popup.html',
        'public/options.html',
        'public/overlay.html',
      ],
      webExtConfig: {
        startUrl: 'https://www.facebook.com/marketplace',
        chromiumBinary: process.env.CHROME_PATH,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@core': resolve(__dirname, '../packages/core/src'),
      '@ui': resolve(__dirname, '../packages/ui/src'),
      '@data': resolve(__dirname, '../packages/data/src'),
      '@ml': resolve(__dirname, '../packages/ml/src'),
      '@integrations': resolve(__dirname, '../packages/integrations/src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'src/ui/popup/index.html'),
        options: resolve(__dirname, 'src/ui/options/index.html'),
        dashboard: resolve(__dirname, 'src/ui/dashboard/index.html'),
        background: resolve(__dirname, 'src/background/index.ts'),
        'content/fb': resolve(__dirname, 'src/content/fb/index.ts'),
        'content/craigslist': resolve(__dirname, 'src/content/craigslist/index.ts'),
        'content/offerup': resolve(__dirname, 'src/content/offerup/index.ts'),
        'workers/ocr': resolve(__dirname, 'src/workers/ocr.worker.ts'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          // Workers need to be in their own directory
          if (chunkInfo.name.includes('worker')) {
            return 'workers/[name].js';
          }
          return '[name].js';
        },
        chunkFileNames: 'chunks/[name].[hash].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },
  server: {
    port: 3000,
    hmr: {
      port: 3001,
    },
  },
});