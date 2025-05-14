import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      'd875-2600-1700-8f30-19b0-50b8-eeda-3af6-6290.ngrok-free.app',
      'localhost',
      '127.0.0.1',
      'rellaanalyticsdb-1.onrender.com',
    ],
    proxy: {
      '/api': 'http://localhost:5000', // <--- ADD THIS LINE
    },
  },
});
