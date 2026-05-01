import { useNavigate } from "react-router-dom";

/* =========================================================
   NotFoundPage — 404 page with fitness theme
   Classes from kimi-components.css: .page-404, .gradient-text,
     .dumbbell-svg, .num-404, .msg-404, .btn-home, .decorative-stats
   ========================================================= */

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <main className="page-404" aria-label="Página no encontrada">
      {/* Floating dumbbell SVG */}
      <svg
        className="dumbbell-svg"
        viewBox="0 0 120 120"
        fill="none"
        aria-hidden="true"
        role="img"
      >
        <rect x="10" y="45" width="100" height="30" rx="6" fill="var(--brand-500)" />
        <rect x="0"   y="35" width="15"  height="50" rx="4" fill="var(--brand-600)" />
        <rect x="105" y="35" width="15"  height="50" rx="4" fill="var(--brand-600)" />
        <circle cx="60" cy="60" r="12" fill="var(--brand-300)" />
      </svg>

      {/* 404 number */}
      <div className="num-404 gradient-text" aria-hidden="true">404</div>

      {/* Message */}
      <p className="msg-404">
        Este ejercicio no existe en tu rutina.
        <br />
        Revisa tu plan o vuelve al inicio.
      </p>

      {/* CTA */}
      <button
        type="button"
        className="btn-home"
        onClick={() => navigate("/")}
        aria-label="Volver a la página de inicio"
      >
        <i className="bi bi-house-fill me-2" aria-hidden="true" />
        Volver al inicio
      </button>

      {/* Decorative background stats */}
      <span className="decorative-stats s1" aria-hidden="true">12,450 kcal</span>
      <span className="decorative-stats s2" aria-hidden="true">47 rutinas</span>
      <span className="decorative-stats s3" aria-hidden="true">78.5 kg</span>
      <span className="decorative-stats s4" aria-hidden="true">12 días racha</span>
    </main>
  );
}
