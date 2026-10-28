import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // in development the API runs separately on port 8000
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
