import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Phase 2: the real API is served here, so the app stays same-origin.
    proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } },
  },
});
