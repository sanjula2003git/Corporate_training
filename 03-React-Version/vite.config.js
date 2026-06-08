import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite is the build tool / dev server. `npm run dev` starts hot-reloading.
// `base` is the sub-path where the built app lives.
// - On Vercel the app serves from the domain root, so base must be "/".
//   (Vercel sets the VERCEL env var automatically during its build.)
// - On GitHub Pages it lives under the repo/sub-folder path.
export default defineConfig({
  base: process.env.VERCEL ? "/" : "/Corporate_training/03-React-Version/",
  plugins: [react()],
});
