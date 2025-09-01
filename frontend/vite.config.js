import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 從環境變數讀取
const API_BASE_URL = process.env.VITE_API_BASE_URL
const DEV_PORT = parseInt(process.env.VITE_DEV_PORT) || 3000


export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: DEV_PORT,
    proxy: {
      '/api': {
        target: API_BASE_URL || 'http://localhost:8945',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
