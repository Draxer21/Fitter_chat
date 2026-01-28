import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
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

export default function DietPlanDetailPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const { id } = useParams();
  const [plan, setPlan] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated || !id) return;
    setStatus("loading");
    setError("");
    API.profile.dietPlans
      .get(id)
      .then((data) => {
        setPlan(data || null);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No pudimos cargar la dieta.");
        setStatus("error");
      });
  }, [id, isAuthenticated]);

  const content = useMemo(() => plan?.content || {}, [plan]);
  const summary = content.summary || {};
  const meals = content.meals || [];
  const objective = summary.objective || plan?.goal || "Objetivo";
  const calories = summary.calorias || "Calorías estimadas";

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
          <h1 className="profile-title">Detalle de dieta</h1>
          <p className="profile-subtitle">Revisa el plan alimenticio completo que guardaste.</p>
        </header>

        <ProfileSectionNav />

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">Cargando dieta...</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !plan && (
            <div className="hero-plans-empty">
              <h2>Dieta no encontrada</h2>
              <p>Puede que la dieta no exista o que ya no tengas acceso.</p>
              <Link className="btn btn-primary" to="/cuenta/dietas">Volver a dietas</Link>
            </div>
          )}
          {plan && (
            <article className="hero-plan-card">
              <div className="hero-plan-card-header">
                <div>
                  <h3>{plan.title}</h3>
                  <p className="text-muted">{objective} · {calories}</p>
                </div>
                <span className="hero-plan-chip">ID {plan.id}</span>
              </div>
              <p className="hero-plan-desc">Plan alimenticio generado y guardado desde el chat.</p>
              <div className="hero-plan-meta">
                <div>
                  <span>Creada</span>
                  <strong>{plan.created_at ? new Date(plan.created_at).toLocaleDateString() : "Reciente"}</strong>
                </div>
                <div>
                  <span>Versión</span>
                  <strong>{plan.version ?? 1}</strong>
                </div>
                <div>
                  <span>ID</span>
                  <strong>{plan.id}</strong>
                </div>
              </div>
              <div>
                <h4 className="mb-2">Menú diario</h4>
                {Array.isArray(meals) && meals.length > 0 ? (
                  <div className="d-grid gap-3">
                    {meals.map((meal, idx) => (
                      <div key={idx}>
                        <strong>{meal.name || `Comida ${idx + 1}`}</strong>
                        <p className="mb-1 text-muted">{formatMealItems(meal.items) || "Sin items detallados"}</p>
                        {meal.notes && <small className="text-muted">Nota: {meal.notes}</small>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted mb-0">Sin detalle de comidas disponible.</p>
                )}
              </div>
              <div className="hero-plan-actions">
                <Link className="btn btn-outline-primary" to="/cuenta/dietas">Volver a la lista</Link>
              </div>
            </article>
          )}
        </div>
      </div>
    </main>
  );
}
