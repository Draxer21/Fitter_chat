import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  appType: "spa",
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
    proxy: (() => {
      // Para rutas que son TAMBIÉN páginas React (ej. /chat, /carrito)
      // usamos bypass: si el browser navega directamente a esa URL (Accept: text/html)
      // servimos el SPA en vez de proxiar al backend.
      const spaBypass = (req) => {
        const accept = req.headers["accept"] || "";
        if (req.method === "GET" && accept.includes("text/html")) {
          return "/index.html"; // Vite sirve el SPA
        }
      };
      return {
        "/api":           { target: "http://localhost:5000", changeOrigin: true },
        "/auth":          { target: "http://localhost:5000", changeOrigin: true },
        "/producto":      { target: "http://localhost:5000", changeOrigin: true },
        // /carrito es también una página React → bypass en GET de navegación
        "/carrito":       { target: "http://localhost:5000", changeOrigin: true, bypass: spaBypass },
        "/orders":        { target: "http://localhost:5000", changeOrigin: true },
        "/admin/orders":  { target: "http://localhost:5000", changeOrigin: true },
        "/profile":       { target: "http://localhost:5000", changeOrigin: true },
        // /chat es también una página React → bypass en GET de navegación
        "/chat":          { target: "http://localhost:5000", changeOrigin: true, bypass: spaBypass },
        "/subscriptions": { target: "http://localhost:5000", changeOrigin: true },
        "/handoff":       { target: "http://localhost:5000", changeOrigin: true },
        "/classes":       { target: "http://localhost:5000", changeOrigin: true },
        "/metrics":       { target: "http://localhost:5000", changeOrigin: true },
        "/health":        { target: "http://localhost:5000", changeOrigin: true },
        "/notifications": { target: "http://localhost:5000", changeOrigin: true },
        "/nlu":           { target: "http://localhost:5000", changeOrigin: true },
      };
    })(),
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
    globals: true,
    exclude: ["playwright-temp/**", "node_modules/**"]
  }
});
