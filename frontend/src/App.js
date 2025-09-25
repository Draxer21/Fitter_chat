// src/App.js
import { Suspense, useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import RutinaPage from "./pages/RutinaPage";
// ⬇️ Usa el widget flotante (no la página Chatbot)
import ChatWidget from "./ChatWidget";

// Scroll al top en cada navegación
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

function NotFound() {
  return (
    <div style={{ padding: 24 }}>
      <h2>404 — Página no encontrada</h2>
      <p>La ruta solicitada no existe.</p>
      <a href="/">Volver al inicio</a>
    </div>
  );
}

export default function App() {
  const basename = process.env.PUBLIC_URL || "/";

  return (
    <BrowserRouter basename={basename}>
      <ScrollToTop />

      <header className="app-header" style={{ padding: 12, fontWeight: 600 }}>
        Fitter Chatbot
      </header>

      <main>
        <Suspense fallback={<div style={{ padding: 16 }}>Cargando…</div>}>
          <Routes>
            {/* tu landing, si la tienes; si no, puedes apuntar a otra página */}
            <Route path="/" element={<div style={{ padding: 24 }}>Bienvenido a Fitter</div>} />
            <Route path="/rutina/:id" element={<RutinaPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>

      {/* 🔽 AQUÍ el agregado flotante, visible en todas las rutas */}
      <ChatWidget />
    </BrowserRouter>
  );
}
