import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import webExtension from 'vite-plugin-web-extension';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    react(),
    webExtension({
      manifest: () => ({
        ...require('./public/manifest.json'),
        // Add development-specific overrides if needed
      }),
      additionalInputs: {
        scripts: [
          'src/background/index.ts',
          'src/content/index.ts',
        ],
        html: [
          'public/popup.html',
          'public/options.html',
          'public/overlay.html',
        ],
      },
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
        popup: resolve(__dirname, 'public/popup.html'),
        options: resolve(__dirname, 'public/options.html'),
        background: resolve(__dirname, 'src/background/index.ts'),
        content: resolve(__dirname, 'src/content/index.ts'),
      },
      output: {
        entryFileNames: '[name].js',
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