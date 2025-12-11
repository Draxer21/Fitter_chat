// src/App.js
import { Suspense, useEffect, lazy } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import "./App.css";
import "./styles/fixed-layout.css";
import "./styles/theme-transitions.css";
import "./styles/theme-overrides.css";
import "./styles/theme-final-override.css";
import "./styles/accessibility.css";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import SideControls from "./components/SideControls";
import { LocaleProvider } from "./contexts/LocaleContext";
import { AuthProvider } from "./contexts/AuthContext";
import { CartProvider } from "./contexts/CartContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { FontSizeProvider } from "./contexts/FontSizeContext";
import LegacyStylesLayout from "./layouts/LegacyStylesLayout";

const HomePage = lazy(() => import("./pages/HomePage"));
const RutinaPage = lazy(() => import("./pages/RutinaPage"));
const CarritoPage = lazy(() => import("./pages/CarritoPage"));
const BoletaPage = lazy(() => import("./pages/BoletaPage"));
const PagoPage = lazy(() => import("./pages/PagoPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const TablaProductos = lazy(() => import("./pages/TablaProductos"));
const ProductoDetalle = lazy(() => import("./pages/ProductoDetalle"));
const ProductoForm = lazy(() => import("./pages/ProductoForm"));
const RegistroPage = lazy(() => import("./pages/RegistroPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const AccountSecurityPage = lazy(() => import("./pages/AccountSecurityPage"));
const CatalogPage = lazy(() => import("./pages/CatalogPage"));
const AdminSalesPage = lazy(() => import("./pages/AdminSalesPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const TermsPage = lazy(() => import("./pages/TermsPage"));
const PrivacyPage = lazy(() => import("./pages/PrivacyPage"));
const AccessibilityPage = lazy(() => import("./pages/AccessibilityPage"));
const ChatPage = lazy(() => import("./pages/ChatPage"));
const EntrenosUnicos = lazy(() => import("./pages/EntrenosUnicos"));

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
      <h2>404 - Pagina no encontrada</h2>
      <a href="/">Volver al inicio</a>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <FontSizeProvider>
        <LocaleProvider>
          <AuthProvider>
            <CartProvider>
              <BrowserRouter>
                <a className="skip-link" href="#main-content">Saltar al contenido principal</a>
                <ScrollToTop />
                <Navbar />

                <main id="main-content" className="app-content-safe-area" tabIndex="-1" role="main" aria-label="Contenido principal">
                  <Suspense fallback={<div style={{ padding: 16 }}>Cargando.</div>}>
                    <Routes>
                      <Route element={<LegacyStylesLayout />}>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/tienda" element={<HomePage />} />
                        <Route path="/producto/:id" element={<ProductoDetalle />} />
                        <Route path="/registro" element={<RegistroPage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/sobre-nosotros" element={<AboutPage />} />
                        <Route path="/terminos" element={<TermsPage />} />
                        <Route path="/entrenos-unicos" element={<EntrenosUnicos />} />
                        <Route path="/privacidad" element={<PrivacyPage />} />
                        <Route path="/accesibilidad" element={<AccessibilityPage />} />
                      </Route>

                      <Route path="/catalogo" element={<CatalogPage />} />
                      <Route path="/chat" element={<ChatPage />} />
                      <Route path="/carrito" element={<CarritoPage />} />
                      <Route path="/pago" element={<PagoPage />} />
                      <Route path="/boleta" element={<BoletaPage />} />
                      <Route path="/admin/productos" element={<TablaProductos />} />
                      <Route path="/admin/productos/nuevo" element={<ProductoForm />} />
                      <Route path="/admin/productos/:id/editar" element={<ProductoForm />} />
                      <Route path="/admin/ventas" element={<AdminSalesPage />} />
                      <Route path="/rutina/:id" element={<RutinaPage />} />
                      <Route path="/cuenta/perfil" element={<ProfilePage />} />
                      <Route path="/cuenta/seguridad" element={<AccountSecurityPage />} />
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Suspense>
                </main>
                <Footer />

                <SideControls />
              </BrowserRouter>
            </CartProvider>
          </AuthProvider>
        </LocaleProvider>
      </FontSizeProvider>
    </ThemeProvider>
  );
}
