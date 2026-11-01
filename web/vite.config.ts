import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: Vite serves the UI and proxies /api to the Python view server.
// Demo: `npm run build` emits ../src/presentation/static, which the Python
// server serves directly, so a demo is one process and one command.
//
// Static host: `VITE_STATIC=1 VITE_BASE=/<repo>/ VITE_OUT=dist npm run build`
// builds the same app against a baked `public/claim-view.json` instead of the
// API. Three env vars rather than a second config, so there is one build to
// keep working — a separate static entry point would drift from this one and
// the drift would only show up on the hosted page.
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE ?? "/",
  build: {
    outDir: process.env.VITE_OUT ?? "../src/presentation/static",
    emptyOutDir: true,
  },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
