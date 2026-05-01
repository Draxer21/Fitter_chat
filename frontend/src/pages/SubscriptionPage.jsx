import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/subscription.css";

/* ── Helpers ── */
const formatDate = (dateStr) =>
  dateStr
    ? new Date(dateStr).toLocaleDateString("es-CL", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      })
    : "-";

const daysRemaining = (endDateStr) => {
  if (!endDateStr) return null;
  const diff = new Date(endDateStr) - new Date();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
};

/* ── Skeleton card while loading plans ── */
function PlanSkeleton() {
  return (
    <div className="subscription-card subscription-card--skeleton" aria-hidden="true">
      <div className="skel-line skel-line--name" />
      <div className="skel-line skel-line--price" />
      <div className="skel-line skel-line--feat" />
      <div className="skel-line skel-line--feat short" />
      <div className="skel-line skel-line--btn" />
    </div>
  );
}

/* ── Active plan banner ── */
function ActiveBanner({ subscription, t }) {
  const days = daysRemaining(subscription.end_date);

  return (
    <div className="active-sub-banner">
      <div className="active-sub-banner__icon" aria-hidden="true">
        <i className="bi bi-patch-check-fill" />
      </div>
      <div className="active-sub-banner__body">
        <span className="active-sub-banner__label">{t("subscription.currentPlan")}</span>
        <span className="active-sub-banner__name">
          {subscription.plan_name || subscription.plan_type}
          <span className="badge bg-success ms-2">
            {t("subscription.status.active")}
          </span>
          {subscription.auto_renew && (
            <span className="badge bg-info ms-1">
              <i className="bi bi-arrow-repeat me-1" aria-hidden="true" />
              {t("subscription.autoRenew")}
            </span>
          )}
        </span>
        <div className="active-sub-banner__dates">
          <span>
            <i className="bi bi-calendar-check me-1" aria-hidden="true" />
            {t("subscription.startDate")}: {formatDate(subscription.start_date)}
          </span>
          {subscription.end_date && (
            <span>
              <i className="bi bi-calendar-x me-1" aria-hidden="true" />
              {t("subscription.endDate")}: {formatDate(subscription.end_date)}
              {days !== null && (
                <span className={`days-pill ${days < 7 ? "days-pill--urgent" : ""}`}>
                  {days} {t("subscription.daysLeft")}
                </span>
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Individual plan card ── */
function PlanCard({ plan, isActive, currentPlanType, cancelConfirm, actionLoading, onSubscribe, onChange, onCancel, onCancelBack, t }) {
  return (
    <div
      className={[
        "subscription-card",
        `subscription-card--${plan.plan_type}`,
        isActive ? "subscription-card--active" : "",
      ].filter(Boolean).join(" ")}
    >
      {/* Active badge */}
      {isActive && (
        <div className="subscription-card__active-badge" aria-label={t("subscription.currentPlan")}>
          <i className="bi bi-check-circle-fill me-1" aria-hidden="true" />
          {t("subscription.currentPlan")}
        </div>
      )}

      <h3 className="subscription-card__name">{plan.name}</h3>
      <p className="subscription-card__price">{plan.price_display}</p>
      <p className="subscription-card__features">{plan.features}</p>

      <div className="subscription-card__actions">
        {isActive ? (
          cancelConfirm ? (
            <div className="d-flex gap-2 flex-wrap">
              <button
                className="btn btn-danger btn-sm"
                disabled={actionLoading}
                onClick={onCancel}
              >
                {t("subscription.cancelConfirm")}
              </button>
              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={onCancelBack}
              >
                {t("subscription.cancelBack")}
              </button>
            </div>
          ) : (
            <button
              className="btn btn-outline-danger btn-sm"
              disabled={actionLoading}
              onClick={onCancel}
            >
              <i className="bi bi-x-circle me-1" aria-hidden="true" />
              {t("subscription.cancel")}
            </button>
          )
        ) : currentPlanType ? (
          <button
            className="btn btn-primary"
            disabled={actionLoading}
            onClick={() => onChange(plan.plan_type)}
          >
            <i className="bi bi-arrow-left-right me-1" aria-hidden="true" />
            {t("subscription.changePlan")}
          </button>
        ) : (
          <button
            className="btn btn-primary"
            disabled={actionLoading}
            onClick={() => onSubscribe(plan.plan_type)}
          >
            <i className="bi bi-lightning-fill me-1" aria-hidden="true" />
            {t("subscription.subscribe")}
          </button>
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════
   Main Page
═══════════════════════════════════════════════════ */
export default function SubscriptionPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();

  const [plans, setPlans] = useState([]);
  const [plansLoading, setPlansLoading] = useState(true);

  const [subscription, setSubscription] = useState(null);
  const [history, setHistory] = useState([]);
  const [dataStatus, setDataStatus] = useState("idle"); // idle | loading | ready | error
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [cancelConfirm, setCancelConfirm] = useState(false);

  /* Cargar catálogo de planes (público, siempre) */
  useEffect(() => {
    API.subscriptions
      .plans()
      .then((data) => setPlans(Array.isArray(data?.plans) ? data.plans : []))
      .catch(() => setPlans([]))
      .finally(() => setPlansLoading(false));
  }, []);

  /* Cargar suscripción del usuario */
  const loadData = useCallback(() => {
    if (!isAuthenticated) return;
    setDataStatus("loading");
    setError("");
    Promise.all([API.subscriptions.current(), API.subscriptions.history()])
      .then(([current, hist]) => {
        const sub = current?.subscription || null;
        // Enriquecer con el nombre del plan si ya tenemos el catálogo
        setSubscription(sub);
        setHistory(Array.isArray(hist?.subscriptions) ? hist.subscriptions : []);
        setDataStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || t("subscription.loadError"));
        setDataStatus("error");
      });
  }, [isAuthenticated, t]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /* Enriquecer suscripción con nombre del plan del catálogo */
  const enrichedSubscription = useMemo(() => {
    if (!subscription) return null;
    const planData = plans.find((p) => p.plan_type === subscription.plan_type);
    return { ...subscription, plan_name: planData?.name || subscription.plan_type };
  }, [subscription, plans]);

  const currentPlanType = useMemo(
    () => (subscription?.status === "active" ? subscription.plan_type : null),
    [subscription]
  );

  /* Actions */
  const handleSubscribe = useCallback(
    async (planType) => {
      setActionLoading(true);
      setError("");
      try {
        await API.subscriptions.create({ plan_type: planType });
        loadData();
      } catch (err) {
        setError(err?.message || t("subscription.actionError"));
      } finally {
        setActionLoading(false);
      }
    },
    [loadData, t]
  );

  const handleChange = useCallback(
    async (planType) => {
      if (!subscription) return;
      setActionLoading(true);
      setError("");
      try {
        await API.subscriptions.update(subscription.id, { plan_type: planType });
        loadData();
      } catch (err) {
        setError(err?.message || t("subscription.actionError"));
      } finally {
        setActionLoading(false);
      }
    },
    [subscription, loadData, t]
  );

  const handleCancel = useCallback(async () => {
    if (!subscription) return;
    if (!cancelConfirm) {
      setCancelConfirm(true);
      return;
    }
    setActionLoading(true);
    setError("");
    try {
      await API.subscriptions.cancel(subscription.id);
      setCancelConfirm(false);
      loadData();
    } catch (err) {
      setError(err?.message || t("subscription.actionError"));
    } finally {
      setActionLoading(false);
    }
  }, [subscription, cancelConfirm, loadData, t]);

  /* ── Guest guard ── */
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
          <p className="profile-eyebrow">{t("subscription.eyebrow")}</p>
          <h1 className="profile-title">{t("subscription.title")}</h1>
          <p className="profile-subtitle">{t("subscription.subtitle")}</p>
        </header>

        <ProfileSectionNav />

        {error && (
          <div className="alert alert-danger mt-3" role="alert">
            <i className="bi bi-exclamation-triangle-fill me-2" aria-hidden="true" />
            {error}
          </div>
        )}

        {/* ── Estado de suscripción actual ── */}
        {dataStatus === "ready" && (
          <div className="subscription-status mt-4">
            {enrichedSubscription && enrichedSubscription.status === "active" ? (
              <ActiveBanner subscription={enrichedSubscription} t={t} />
            ) : (
              <div className="no-sub-banner">
                <i className="bi bi-info-circle-fill me-2" aria-hidden="true" />
                <span>{t("subscription.noPlan")}</span>
                <small className="d-block mt-1 opacity-75">
                  {t("subscription.noPlanDesc")}
                </small>
              </div>
            )}
          </div>
        )}

        {/* ── Tarjetas de planes ── */}
        <div className="subscription-plans mt-4">
          {plansLoading ? (
            <>
              <PlanSkeleton />
              <PlanSkeleton />
              <PlanSkeleton />
            </>
          ) : plans.length === 0 ? (
            <p className="text-muted text-center col-span-3">
              {t("subscription.plansUnavailable")}
            </p>
          ) : (
            plans.map((plan) => (
              <PlanCard
                key={plan.plan_type}
                plan={plan}
                isActive={currentPlanType === plan.plan_type}
                currentPlanType={currentPlanType}
                cancelConfirm={cancelConfirm}
                actionLoading={actionLoading}
                onSubscribe={handleSubscribe}
                onChange={handleChange}
                onCancel={handleCancel}
                onCancelBack={() => setCancelConfirm(false)}
                t={t}
              />
            ))
          )}
        </div>

        {/* ── Historial ── */}
        {dataStatus === "ready" && (
          <div className="subscription-history mt-5">
            <h2>{t("subscription.history.title")}</h2>
            {history.length === 0 ? (
              <p className="text-muted">{t("subscription.history.empty")}</p>
            ) : (
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>{t("subscription.history.plan")}</th>
                      <th>{t("subscription.startDate")}</th>
                      <th>{t("subscription.endDate")}</th>
                      <th>{t("subscription.history.status")}</th>
                      <th>{t("subscription.autoRenew")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((entry) => {
                      const planData = plans.find((p) => p.plan_type === entry.plan_type);
                      return (
                        <tr key={entry.id}>
                          <td>{planData?.name || entry.plan_type}</td>
                          <td>{formatDate(entry.start_date)}</td>
                          <td>{formatDate(entry.end_date)}</td>
                          <td>
                            <span
                              className={`badge bg-${
                                entry.status === "active"
                                  ? "success"
                                  : entry.status === "cancelled"
                                  ? "danger"
                                  : "secondary"
                              }`}
                            >
                              {t(`subscription.status.${entry.status}`) || entry.status}
                            </span>
                          </td>
                          <td>
                            {entry.auto_renew ? (
                              <i className="bi bi-check-lg text-success" aria-label="Sí" />
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
