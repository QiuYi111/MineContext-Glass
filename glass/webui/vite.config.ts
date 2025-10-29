import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_PROXY = process.env.GLASS_API_PROXY ?? "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/glass": {
        target: API_PROXY,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5174,
    proxy: {
      "/glass": {
        target: API_PROXY,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "app.js",
        chunkFileNames: "app-[name].js",
        assetFileNames: (chunkInfo) => {
          if (chunkInfo.name && chunkInfo.name.endsWith(".css")) {
            return "app.css";
          }
          return "app-[name][extname]";
        },
      },
    },
  },
});
