import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite is the build tool / dev server. `npm run dev` starts hot-reloading.
export default defineConfig({
  plugins: [react()],
});
