import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Allow JSX syntax in .js files during dev pre-bundling and build
  esbuild: {
    loader: "jsx",
    include: /src\/.*\.[jt]sx?$/
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        ".js": "jsx"
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      "/api": "http://localhost:5000",
      "/auth": "http://localhost:5000",
      "/producto": "http://localhost:5000",
      "/carrito": "http://localhost:5000",
      "/orders": "http://localhost:5000",
      "/admin": "http://localhost:5000",
      "/profile": "http://localhost:5000",
      "/chat": "http://localhost:5000"
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
    globals: true
  }
});
