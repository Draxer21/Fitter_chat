import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/hero-plans.css";

const PlanComparisonModal = lazy(() => import("../components/PlanComparisonModal"));

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
  const [compareMode, setCompareMode] = useState(false);
  const [selected, setSelected] = useState([]);
  const [showComparison, setShowComparison] = useState(false);

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
        setError(err?.message || t("routinePlans.loadError"));
        setStatus("error");
      });
  }, [isAuthenticated]);

  const hasPlans = useMemo(() => plans.length > 0, [plans]);

  const toggleSelect = useCallback((id) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  }, []);

  const handleCompare = () => {
    if (selected.length === 2) setShowComparison(true);
  };

  const exitCompareMode = () => {
    setCompareMode(false);
    setSelected([]);
    setShowComparison(false);
  };

  const planA = useMemo(() => plans.find((p) => p.id === selected[0]), [plans, selected]);
  const planB = useMemo(() => plans.find((p) => p.id === selected[1]), [plans, selected]);

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
          <p className="profile-eyebrow">{t("routinePlans.eyebrow")}</p>
          <h1 className="profile-title">{t("routinePlans.title")}</h1>
          <p className="profile-subtitle">{t("routinePlans.subtitle")}</p>
        </header>

        <ProfileSectionNav />

        {hasPlans && plans.length >= 2 && (
          <div className="d-flex justify-content-end gap-2 mb-3">
            {compareMode ? (
              <>
                <button
                  className="btn btn-primary btn-sm"
                  disabled={selected.length !== 2}
                  onClick={handleCompare}
                >
                  {t("comparison.compare")} ({selected.length}/2)
                </button>
                <button className="btn btn-outline-secondary btn-sm" onClick={exitCompareMode}>
                  {t("comparison.close")}
                </button>
              </>
            ) : (
              <button className="btn btn-outline-primary btn-sm" onClick={() => setCompareMode(true)}>
                {t("comparison.mode")}
              </button>
            )}
          </div>
        )}

        <div className="hero-plans-grid">
          {status === "loading" && <p className="text-muted">{t("routinePlans.loading")}</p>}
          {error && <div className="alert alert-danger">{error}</div>}
          {status === "ready" && !hasPlans && (
            <div className="hero-plans-empty">
              <h2>{t("routinePlans.empty.title")}</h2>
              <p>{t("routinePlans.empty.desc")}</p>
              <Link className="btn btn-primary" to="/chat">{t("common.goToChat")}</Link>
            </div>
          )}
          {hasPlans && plans.map((plan) => {
            const content = plan.content || {};
            const summary = content.summary || {};
            const exercises = content.exercises || [];
            const header = plan.title || content.header || t("routinePlans.defaultTitle");
            const objective = plan.objective || summary.objetivo || t("dietPlans.defaultObjective");
            const muscle = summary.musculo || "fullbody";
            const level = summary.nivel || "intermedio";
            const time = summary.tiempo_min ? `${summary.tiempo_min} min` : t("common.flexibleDuration");
            const createdAt = plan.created_at ? new Date(plan.created_at).toLocaleDateString() : "";
            const isSelected = selected.includes(plan.id);

            return (
              <article
                className={`hero-plan-card ${compareMode && isSelected ? "hero-plan-card--selected" : ""}`}
                key={plan.id}
                onClick={compareMode ? () => toggleSelect(plan.id) : undefined}
                style={compareMode ? { cursor: "pointer" } : undefined}
              >
                {compareMode && (
                  <input
                    type="checkbox"
                    className="form-check-input position-absolute"
                    style={{ top: 12, right: 12 }}
                    checked={isSelected}
                    onChange={() => toggleSelect(plan.id)}
                    aria-label={t("comparison.select")}
                  />
                )}
                <div className="hero-plan-card-header">
                  <div>
                    <h3>{header}</h3>
                    <p className="text-muted">{objective} · {level} · {muscle}</p>
                  </div>
                  <span className="hero-plan-chip">{t("routinePlans.chip")}</span>
                </div>
                <p className="hero-plan-desc">{content.fallback_notice ? `${t("common.note")}: ${content.fallback_notice}` : t("routinePlans.defaultDesc")}</p>
                <div className="hero-plan-meta">
                  <div>
                    <span>{t("common.duration")}</span>
                    <strong>{time}</strong>
                  </div>
                  <div>
                    <span>{t("common.created")}</span>
                    <strong>{createdAt || t("common.recent")}</strong>
                  </div>
                  <div>
                    <span>{t("common.id")}</span>
                    <strong>{plan.id}</strong>
                  </div>
                </div>
                {!compareMode && (
                  <>
                    <details>
                      <summary className="btn btn-outline-primary">{t("common.viewDetail")}</summary>
                      <div className="mt-3">
                        {Array.isArray(exercises) && exercises.length > 0 ? (
                          <ol className="mb-0">
                            {exercises.map((entry, idx) => (
                              <li key={idx}>{formatExercise(entry)}</li>
                            ))}
                          </ol>
                        ) : (
                          <p className="text-muted mb-0">{t("routinePlans.detailHint")}</p>
                        )}
                      </div>
                    </details>
                    <div className="hero-plan-actions">
                      <Link className="btn btn-outline-primary" to={`/cuenta/rutinas/${plan.id}`}>{t("common.viewPage")}</Link>
                    </div>
                  </>
                )}
              </article>
            );
          })}
        </div>
      </div>

      {showComparison && planA && planB && (
        <Suspense fallback={null}>
          <PlanComparisonModal
            planA={planA}
            planB={planB}
            planType="routine"
            onClose={() => setShowComparison(false)}
          />
        </Suspense>
      )}
    </main>
  );
}
