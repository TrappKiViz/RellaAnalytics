import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Allows access from network IPs (recommended for ngrok)
    allowedHosts: [
      // Add your ngrok hostname here
      'd875-2600-1700-8f30-19b0-50b8-eeda-3af6-6290.ngrok-free.app',
      // Keep localhost as well
      'localhost',
      '127.0.0.1',
      'rellaanalyticsdb-1.onrender.com', // Allow Render frontend hosting
    ],
     // --- IMPORTANT: Add Proxy for API calls ---
     // If your frontend (running on e.g. 5173) calls your backend API (running on e.g. 5000),
     // you need this proxy to avoid CORS issues when accessing via ngrok.
     proxy: {
       '/api': { // Match requests starting with /api
         target: 'http://127.0.0.1:5000', // Your Flask backend address
         changeOrigin: true, // Recommended for virtual hosted sites
         secure: false,      // Typically false for local http backend
         // Optional: rewrite path if needed, e.g., remove /api prefix
         // rewrite: (path) => path.replace(/^\/api/, ''),
       },
     },
  },
});
