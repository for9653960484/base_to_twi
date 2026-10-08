import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        // Локально backend на 8000. В Docker prod compose задаёт VITE_PROXY_TARGET=http://backend:8000
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Крупные PDF (до 50 MB) иначе могут оборваться по таймауту прокси
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },
});
