import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite is the build tool / dev server. `npm run dev` starts hot-reloading.
// `base` is the sub-path where the built app lives on GitHub Pages.
export default defineConfig({
  base: "/Corporate_training/03-React-Version/",
  plugins: [react()],
});
