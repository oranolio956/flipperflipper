import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { copyFileSync, mkdirSync, writeFileSync } from 'fs';

// Production build configuration for Chrome Extension
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'chrome-extension-build',
      buildEnd() {
        // Copy manifest
        copyFileSync('manifest.json', 'dist/manifest.json');
        
        // Copy icons
        mkdirSync('dist/icons', { recursive: true });
        ['16', '32', '48', '128'].forEach(size => {
          copyFileSync(`icons/icon-${size}.png`, `dist/icons/icon-${size}.png`);
        });
      }
    }
  ],
  
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false, // Keep console logs for debugging
        drop_debugger: true
      }
    },
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'popup.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
        options: resolve(__dirname, 'options.html'),
        background: resolve(__dirname, 'src/background/index.ts'),
        'content-facebook': resolve(__dirname, 'src/content/fb/index.ts'),
        'content-craigslist': resolve(__dirname, 'src/content/craigslist/index.ts'),
        'content-offerup': resolve(__dirname, 'src/content/offerup/index.ts'),
        'content-scanner': resolve(__dirname, 'src/content/scanner/index.ts')
      },
      output: {
        entryFileNames: (chunkInfo) => {
          // Place content scripts and background in js folder
          if (chunkInfo.name.includes('content-') || chunkInfo.name === 'background') {
            return 'js/[name].js';
          }
          return 'assets/[name]-[hash].js';
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        }
      }
    }
  },
  
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@arbitrage/core': resolve(__dirname, '../packages/core/src')
    }
  },
  
  // Chrome extension specific optimizations
  optimizeDeps: {
    exclude: ['chrome']
  },
  
  // Ensure proper module handling
  esbuild: {
    target: 'chrome90'
  }
});