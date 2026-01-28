import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
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

export default function RoutinePlanDetailPage() {
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
    API.profile.routinePlans
      .get(id)
      .then((data) => {
        setPlan(data || null);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No pudimos cargar la rutina.");
        setStatus("error");
      });
  }, [id, isAuthenticated]);

  const content = useMemo(() => plan?.content || {}, [plan]);
  const summary = content.summary || {};
  const exercises = content.exercises || [];
  const header = content.header || plan?.title || "Rutina";
  const objective = summary.objetivo || plan?.objective || "Objetivo";
  const muscle = summary.musculo || "fullbody";
  const level = summary.nivel || "intermedio";
  const time = summary.tiempo_min ? `${summary.tiempo_min} min` : "Duración flexible";

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
          <h1 className="profile-title">Detalle de rutina</h1>
          <p className="profile-subtitle">Revisa el contenido completo de tu rutina guardada.</p>
        </header>

        <ProfileSectionNav />

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">Cargando rutina...</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !plan && (
            <div className="hero-plans-empty">
              <h2>Rutina no encontrada</h2>
              <p>Puede que la rutina no exista o que ya no tengas acceso.</p>
              <Link className="btn btn-primary" to="/cuenta/rutinas">Volver a rutinas</Link>
            </div>
          )}
          {plan && (
            <article className="hero-plan-card">
              <div className="hero-plan-card-header">
                <div>
                  <h3>{header}</h3>
                  <p className="text-muted">{objective} · {level} · {muscle}</p>
                </div>
                <span className="hero-plan-chip">ID {plan.id}</span>
              </div>
              <p className="hero-plan-desc">{content.fallback_notice ? `Nota: ${content.fallback_notice}` : "Rutina generada y guardada desde el chat."}</p>
              <div className="hero-plan-meta">
                <div>
                  <span>Duración</span>
                  <strong>{time}</strong>
                </div>
                <div>
                  <span>Creada</span>
                  <strong>{plan.created_at ? new Date(plan.created_at).toLocaleDateString() : "Reciente"}</strong>
                </div>
                <div>
                  <span>Versión</span>
                  <strong>{plan.version ?? 1}</strong>
                </div>
              </div>
              <div>
                <h4 className="mb-2">Ejercicios</h4>
                {Array.isArray(exercises) && exercises.length > 0 ? (
                  <ol className="mb-0">
                    {exercises.map((entry, idx) => (
                      <li key={idx}>{formatExercise(entry)}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-muted mb-0">Sin detalle de ejercicios disponible.</p>
                )}
              </div>
              <div className="hero-plan-actions">
                <Link className="btn btn-outline-primary" to="/cuenta/rutinas">Volver a la lista</Link>
              </div>
            </article>
          )}
        </div>
      </div>
    </main>
  );
}
