// src/App.js
import { Suspense, useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import "./styles/legacy/login/style_index.css";
import "./styles/legacy/producto/style_index.css";
import "./styles/fixed-layout.css";

import HomePage from "./pages/HomePage";
import RutinaPage from "./pages/RutinaPage";
import ChatWidget from "./ChatWidget";
import Navbar from "./components/Navbar";
import TiendaPage from "./pages/TiendaPage";
import CarritoPage from "./pages/CarritoPage";
import BoletaPage from "./pages/BoletaPage";
import LoginPage from "./pages/LoginPage";
import TablaProductos from "./pages/TablaProductos";
import ProductoDetalle from "./pages/ProductoDetalle";
import ProductoForm from "./pages/ProductoForm";
import Footer from "./components/Footer";
import RegistroPage from "./pages/RegistroPage";




function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: "instant" }); }, [pathname]);
  return null;
}

function NotFound() {
  return (
    <div style={{ padding: 24 }}>
      <h2>404 — Página no encontrada</h2>
      <a href="/">Volver al inicio</a>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Navbar /> 

  <main className="app-content-safe-area">
        <Suspense fallback={<div style={{ padding: 16 }}>Cargando…</div>}>
          <Routes>
            {/* ✅ Home REAL: / */}
            <Route path="/" element={<HomePage />} />

            <Route path="/tienda" element={<HomePage />} />{/* si quieres alias */}
            <Route path="/producto/:id" element={<ProductoDetalle />} />
            <Route path="/registro" element={<RegistroPage />} />
            <Route path="/carrito" element={<CarritoPage />} />
            <Route path="/boleta" element={<BoletaPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/admin/productos" element={<TablaProductos />} />
            <Route path="/admin/productos/nuevo" element={<ProductoForm />} />
            <Route path="/rutina/:id" element={<RutinaPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />

      {/* Widget flotante del chat en todas las rutas */}
      <ChatWidget />
    </BrowserRouter>
  );
}
