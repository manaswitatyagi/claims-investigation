import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: Vite serves the UI and proxies /api to the Python view server.
// Demo: `npm run build` emits ../src/presentation/static, which the Python
// server serves directly, so a demo is one process and one command.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../src/presentation/static", emptyOutDir: true },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
