import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/api": "http://localhost:8069",
      "/ws": { target: "ws://localhost:8069", ws: true },
    },
  },
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
});
