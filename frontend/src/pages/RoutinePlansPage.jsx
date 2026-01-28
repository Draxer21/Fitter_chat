import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/hero-plans.css";

function formatExercise(entry) {
  if (!entry) return null;
  if (typeof entry === "string") return entry;
  const name = entry.nombre || entry.name || entry.titulo || "Ejercicio";
  const series = entry.series ? ` ${entry.series} series` : "";
  const reps = entry.repeticiones ? ` x ${entry.repeticiones} reps` : "";
  const rpe = entry.rpe ? ` · ${entry.rpe}` : "";
  const rir = entry.rir ? ` · ${entry.rir}` : "";
  return `${name}${series}${reps}${rpe}${rir}`.trim();
}

export default function RoutinePlansPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;
    setStatus("loading");
    setError("");
    API.profile.routinePlans
      .list()
      .then((data) => {
        setPlans(Array.isArray(data) ? data : []);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No pudimos cargar tus rutinas guardadas.");
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
          <p className="profile-eyebrow">Rutinas</p>
          <h1 className="profile-title">Mis rutinas generadas</h1>
          <p className="profile-subtitle">Visualiza las rutinas creadas por el chatbot y retoma tu progreso cuando quieras.</p>
        </header>

        <ProfileSectionNav />

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">Cargando rutinas...</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !hasPlans && (
            <div className="hero-plans-empty">
              <h2>No tienes rutinas guardadas</h2>
              <p>Genera una rutina desde el chat y vuelve aquí para revisarla.</p>
              <Link className="btn btn-primary" to="/chat">Ir al chat</Link>
            </div>
          )}
          {hasPlans && plans.map((plan) => {
            const content = plan.content || {};
            const summary = content.summary || {};
            const exercises = content.exercises || [];
            const header = plan.title || content.header || "Rutina generada";
            const objective = plan.objective || summary.objetivo || "Objetivo";
            const muscle = summary.musculo || "fullbody";
            const level = summary.nivel || "intermedio";
            const time = summary.tiempo_min ? `${summary.tiempo_min} min` : "Duración flexible";
            const createdAt = plan.created_at ? new Date(plan.created_at).toLocaleDateString() : "";

            return (
              <article className="hero-plan-card" key={plan.id}>
                <div className="hero-plan-card-header">
                  <div>
                    <h3>{header}</h3>
                    <p className="text-muted">{objective} · {level} · {muscle}</p>
                  </div>
                  <span className="hero-plan-chip">Rutina</span>
                </div>
                <p className="hero-plan-desc">{content.fallback_notice ? `Nota: ${content.fallback_notice}` : "Rutina generada y guardada desde el chat."}</p>
                <div className="hero-plan-meta">
                  <div>
                    <span>Duración</span>
                    <strong>{time}</strong>
                  </div>
                  <div>
                    <span>Creada</span>
                    <strong>{createdAt || "Reciente"}</strong>
                  </div>
                  <div>
                    <span>ID</span>
                    <strong>{plan.id}</strong>
                  </div>
                </div>
                <details>
                  <summary className="btn btn-outline-primary">Ver detalle</summary>
                  <div className="mt-3">
                    {Array.isArray(exercises) && exercises.length > 0 ? (
                      <ol className="mb-0">
                        {exercises.map((entry, idx) => (
                          <li key={idx}>{formatExercise(entry)}</li>
                        ))}
                      </ol>
                    ) : (
                      <p className="text-muted mb-0">El detalle completo está disponible en la vista individual.</p>
                    )}
                  </div>
                </details>
                <div className="hero-plan-actions">
                  <Link className="btn btn-outline-primary" to={`/cuenta/rutinas/${plan.id}`}>Ver en página</Link>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </main>
  );
}
