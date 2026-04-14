import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [tailwindcss()],
  
  // Input configuration
  build: {
    outDir: 'static_compiled',
    rollupOptions: {
      input: {
        main: resolve(fileURLToPath(new URL('.', import.meta.url)), 'static_src/javascript/main.js')
      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // Check if names array exists and has at least one element
          const fileName = assetInfo.names && assetInfo.names.length > 0 
            ? assetInfo.names[0] 
            : assetInfo.fileName || '';

          if (fileName.endsWith('.css')) {
            return 'css/[name][extname]'
          }
          if (/\.(ttf|woff|woff2)$/.test(fileName)) {
            return 'fonts/[name][extname]'
          }
          if (/\.(png|jpe?g|gif|svg|webp)$/.test(fileName)) {
            return 'images/[name][extname]'
          }
          return '[name][extname]'
        }
      }
    },
    // Copy static files
    copyPublicDir: true
  },
  
  // Development server configuration
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      // Proxy for Django server
      '!/static/': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  
  // CSS configuration
  css: {
    devSourcemap: true
  },
  
  // Base configuration
  publicDir: 'static_src/public',
  
  resolve: {
    alias: {
      '@': resolve(fileURLToPath(new URL('.', import.meta.url)), 'static_src')
    }
  }
})
