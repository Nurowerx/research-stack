import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  plugins: [react()],
  server: {
    proxy: { "/api": process.env.NX_API_PROXY || "http://127.0.0.1:8876" },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
