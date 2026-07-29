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
        // Локально: 127.0.0.1:8080/8000; в Docker prod: http://backend:8000
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
});
