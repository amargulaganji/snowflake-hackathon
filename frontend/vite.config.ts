import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/members': { target: 'http://localhost:8000', changeOrigin: true },
      '/ask': { target: 'http://localhost:8000', changeOrigin: true },
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/admin': { target: 'http://localhost:8000', changeOrigin: true },
      '/studio': { target: 'http://localhost:8000', changeOrigin: true },
      '/documents': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
  },
});
