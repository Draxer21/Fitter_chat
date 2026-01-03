import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/hero-plans.css";

const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const BASE = rawBase && rawBase !== "/" ? rawBase.replace(/\/+$/, "") : "";

export default function HeroPlansPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    setStatus("loading");
    setError("");
    API.profile.heroPlans.list()
      .then((data) => {
        setPlans(data?.plans || []);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No pudimos cargar los entrenos únicos.");
        setStatus("error");
      });
  }, [isAuthenticated]);

  const handleDownload = async (planId) => {
    if (!planId) return;
    setDownloadingId(planId);
    setError("");
    try {
      const resp = await fetch(`${BASE}/profile/hero-plans/${planId}/pdf`, {
        credentials: "include",
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `entreno_unico_${planId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.message || "No pudimos descargar el plan.");
    } finally {
      setDownloadingId(null);
    }
  };

  const hasPlans = useMemo(() => plans.length > 0, [plans]);

  if (!isAuthenticated) {
    return (
      <main className="profile-page py-5">
        <div className="profile-shell">
          <div className="row justify-content-center">
            <div className="col-lg-6">
              <div className="alert alert-warning">
                {t("profile.messages.authRequired")}
                <div className="mt-3">
                  <Link className="btn btn-dark" to="/login">
                    {t("profile.messages.authButton")}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="profile-page py-5">
      <div className="profile-shell">
        <header className="profile-header text-center mb-4">
          <p className="profile-eyebrow">Entrenos únicos</p>
          <h1 className="profile-title">Mis planes guardados</h1>
          <p className="profile-subtitle">Revisa, descarga o comparte los planes que inscribiste desde la web o el chat.</p>
        </header>

        <ProfileSectionNav />

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">Cargando entrenos únicos...</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !hasPlans && (
            <div className="hero-plans-empty">
              <h2>No tienes planes guardados</h2>
              <p>Explora los entrenos únicos y guarda el plan que quieras recibir.</p>
              <Link className="btn btn-primary" to="/entrenos-unicos">Ver entrenos únicos</Link>
            </div>
          )}
          {hasPlans && plans.map((plan) => {
            const payload = plan.payload || {};
            return (
              <article className="hero-plan-card" key={plan.id}>
                <div className="hero-plan-card-header">
                  <div>
                    <h3>{plan.title}</h3>
                    <p className="text-muted">{payload.duration || "Duración no definida"} · {payload.body_type || "Plan heroico"}</p>
                  </div>
                  <span className="hero-plan-chip">{plan.source || "web/chat"}</span>
                </div>
                <p className="hero-plan-desc">{payload.focus || payload.training || "Plan especializado con enfoque temático."}</p>
                <div className="hero-plan-meta">
                  <div>
                    <span>Inicio</span>
                    <strong>{payload.start || "Flexible"}</strong>
                  </div>
                  <div>
                    <span>Equipamiento</span>
                    <strong>{payload.equipment || "Flexible"}</strong>
                  </div>
                </div>
                <div className="hero-plan-actions">
                  <button
                    className="btn btn-outline-primary"
                    disabled={downloadingId === plan.id}
                    onClick={() => handleDownload(plan.id)}
                  >
                    {downloadingId === plan.id ? "Descargando..." : "Descargar PDF"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </main>
  );
}
