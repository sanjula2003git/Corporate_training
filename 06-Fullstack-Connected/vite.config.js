import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite is the build tool / dev server. `npm run dev` starts hot-reloading.
// `base: "./"` serves the app at the root locally (http://localhost:5173)
// and keeps asset paths relative if you ever deploy it as static files.
export default defineConfig({
  base: "./",
  plugins: [react()],
});
