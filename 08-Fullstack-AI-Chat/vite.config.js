import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite is the build tool / dev server. `npm run dev` starts hot-reloading.
// PHASE 2 runs on its OWN port (5273) so it can run side-by-side with Phase 1
// (which uses 5173). `strictPort` makes it fail loudly instead of drifting to
// another port (which would break the backend's CORS allow-list).
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { port: 5273, strictPort: true },
});
