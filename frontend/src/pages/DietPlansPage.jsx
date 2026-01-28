import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/hero-plans.css";

function formatMealItems(items) {
  if (!Array.isArray(items)) return null;
  if (items.length === 0) return null;
  if (typeof items[0] === "string") return items.join(", ");
  return items
    .map((it) => {
      const name = it?.name || it?.id || "Item";
      const qty = it?.qty ? ` (${it.qty})` : "";
      const kcal = it?.kcal ? `, ${it.kcal} kcal` : "";
      return `${name}${qty}${kcal}`.trim();
    })
    .join(", ");
}

export default function DietPlansPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;
    setStatus("loading");
    setError("");
    API.profile.dietPlans
      .list()
      .then((data) => {
        setPlans(Array.isArray(data) ? data : []);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No pudimos cargar tus dietas guardadas.");
        setStatus("error");
      });
  }, [isAuthenticated]);

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
          <p className="profile-eyebrow">Dietas</p>
          <h1 className="profile-title">Mis dietas generadas</h1>
          <p className="profile-subtitle">Consulta los planes alimenticios que guardaste desde el chat.</p>
        </header>

        <ProfileSectionNav />

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">Cargando dietas...</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !hasPlans && (
            <div className="hero-plans-empty">
              <h2>No tienes dietas guardadas</h2>
              <p>Genera una dieta desde el chat y vuelve aquí para revisarla.</p>
              <Link className="btn btn-primary" to="/chat">Ir al chat</Link>
            </div>
          )}
          {hasPlans && plans.map((plan) => {
            const content = plan.content || {};
            const summary = content.summary || {};
            const meals = content.meals || [];
            const objective = plan.goal || summary.objective || "Objetivo";
            const calories = summary.calorias || "Calorías estimadas";
            const createdAt = plan.created_at ? new Date(plan.created_at).toLocaleDateString() : "";
            const firstMeal = meals[0] || {};
            const previewItems = formatMealItems(firstMeal.items) || "Menú disponible al abrir el detalle.";

            return (
              <article className="hero-plan-card" key={plan.id}>
                <div className="hero-plan-card-header">
                  <div>
                    <h3>{plan.title}</h3>
                    <p className="text-muted">{objective} · {calories}</p>
                  </div>
                  <span className="hero-plan-chip">Dieta</span>
                </div>
                <p className="hero-plan-desc">{previewItems}</p>
                <div className="hero-plan-meta">
                  <div>
                    <span>Creada</span>
                    <strong>{createdAt || "Reciente"}</strong>
                  </div>
                  <div>
                    <span>ID</span>
                    <strong>{plan.id}</strong>
                  </div>
                  <div>
                    <span>Versión</span>
                    <strong>{plan.version ?? 1}</strong>
                  </div>
                </div>
                <div className="hero-plan-actions">
                  <Link className="btn btn-outline-primary" to={`/cuenta/dietas/${plan.id}`}>Ver detalle</Link>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </main>
  );
}
