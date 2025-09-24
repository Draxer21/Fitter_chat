// src/App.js
import { Suspense, lazy, useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Chatbot from "./Chatbot";               // <--- Asegúrate de que Chatbot.jsx está en src/
import RutinaPage from "./pages/RutinaPage";   // <--- Ajusta al nombre real del archivo


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

function App() {
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
            <Route path="/" element={<Chatbot />} />
            <Route path="/rutina/:id" element={<RutinaPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
    </BrowserRouter>
  );
}

export default App;
