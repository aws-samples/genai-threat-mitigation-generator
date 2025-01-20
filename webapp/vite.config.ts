import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
  build: {
    outDir: "build",
    target: "esnext"
  },
  test: {
    environment: "jsdom",
    setupFiles: ['./tests/setup.ts'],
    globals: true // disable to explicitly import vitest exports in test files
  }
});
