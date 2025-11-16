import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    // reduce file watchers on low-end machines
    watch: {
      // use polling only if you face missing-change events on Windows network drives
      // usePolling: false
    }
  },
  build: {
    target: 'es2019',
    chunkSizeWarningLimit: 1200
  },
  // Keep logs minimal
  logLevel: 'info'
});
