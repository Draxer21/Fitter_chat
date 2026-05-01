import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/subscription.css";

const PLANS = ["basic", "premium", "black"];

export default function SubscriptionPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [cancelConfirm, setCancelConfirm] = useState(false);

  const loadData = useCallback(() => {
    if (!isAuthenticated) return;
    setStatus("loading");
    setError("");
    Promise.all([API.subscriptions.current(), API.subscriptions.history()])
      .then(([current, hist]) => {
        // El backend devuelve { subscription: {...} } y { subscriptions: [...] }
        setSubscription(current?.subscription || null);
        setHistory(Array.isArray(hist?.subscriptions) ? hist.subscriptions : []);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || t("subscription.loadError"));
        setStatus("error");
      });
  }, [isAuthenticated, t]);

  useEffect(() => {
    loadData();
  }, [loadData]);

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

  const currentPlanType = useMemo(
    () => (subscription?.status === "active" ? subscription.plan_type : null),
    [subscription]
  );

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString();
  };

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

        {error && <div className="alert alert-danger mt-3">{error}</div>}

        {status === "loading" && (
          <p className="text-muted text-center mt-4">{t("subscription.loading")}</p>
        )}

        {status === "ready" && (
          <>
            {/* Current subscription status */}
            <div className="subscription-status mt-4">
              {subscription && subscription.status === "active" ? (
                <div className="alert alert-success d-flex flex-wrap align-items-center gap-3">
                  <div>
                    <strong>{t("subscription.currentPlan")}:</strong>{" "}
                    {t(`subscription.plans.${subscription.plan_type}.name`)}
                    <span className="ms-3 badge bg-success">
                      {t(`subscription.status.${subscription.status}`)}
                    </span>
                  </div>
                  <div className="ms-auto d-flex gap-3 text-muted small">
                    <span>
                      {t("subscription.startDate")}: {formatDate(subscription.start_date)}
                    </span>
                    <span>
                      {t("subscription.endDate")}: {formatDate(subscription.end_date)}
                    </span>
                    {subscription.auto_renew && (
                      <span className="badge bg-info">{t("subscription.autoRenew")}</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="alert alert-info">{t("subscription.noPlan")}</div>
              )}
            </div>

            {/* Plan cards */}
            <div className="subscription-plans mt-4">
              {PLANS.map((plan) => {
                const isActive = currentPlanType === plan;
                return (
                  <div
                    key={plan}
                    className={`subscription-card subscription-card--${plan}${
                      isActive ? " subscription-card--active" : ""
                    }`}
                  >
                    <h3 className="subscription-card__name">
                      {t(`subscription.plans.${plan}.name`)}
                    </h3>
                    <p className="subscription-card__price">
                      {t(`subscription.plans.${plan}.price`)}
                    </p>
                    <p className="subscription-card__features">
                      {t(`subscription.plans.${plan}.features`)}
                    </p>
                    <div className="subscription-card__actions">
                      {isActive ? (
                        <>
                          {cancelConfirm ? (
                            <div className="d-flex gap-2">
                              <button
                                className="btn btn-danger"
                                disabled={actionLoading}
                                onClick={handleCancel}
                              >
                                {t("subscription.cancelConfirm")}
                              </button>
                              <button
                                className="btn btn-outline-secondary"
                                onClick={() => setCancelConfirm(false)}
                              >
                                {t("subscription.cancelBack")}
                              </button>
                            </div>
                          ) : (
                            <button
                              className="btn btn-outline-danger"
                              disabled={actionLoading}
                              onClick={handleCancel}
                            >
                              {t("subscription.cancel")}
                            </button>
                          )}
                        </>
                      ) : currentPlanType ? (
                        <button
                          className="btn btn-primary"
                          disabled={actionLoading}
                          onClick={() => handleChange(plan)}
                        >
                          {t("subscription.changePlan")}
                        </button>
                      ) : (
                        <button
                          className="btn btn-primary"
                          disabled={actionLoading}
                          onClick={() => handleSubscribe(plan)}
                        >
                          {t("subscription.subscribe")}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Subscription history */}
            <div className="subscription-history mt-5">
              <h2>{t("subscription.history.title")}</h2>
              {history.length === 0 ? (
                <p className="text-muted">{t("subscription.history.empty")}</p>
              ) : (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>{t("subscription.currentPlan")}</th>
                        <th>{t("subscription.startDate")}</th>
                        <th>{t("subscription.endDate")}</th>
                        <th>{t("subscription.status.label")}</th>
                        <th>{t("subscription.autoRenew")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((entry) => (
                        <tr key={entry.id}>
                          <td>{t(`subscription.plans.${entry.plan_type}.name`)}</td>
                          <td>{formatDate(entry.start_date)}</td>
                          <td>{formatDate(entry.end_date)}</td>
                          <td>
                            <span
                              className={`badge bg-${
                                entry.status === "active" ? "success" : "secondary"
                              }`}
                            >
                              {t(`subscription.status.${entry.status}`)}
                            </span>
                          </td>
                          <td>{entry.auto_renew ? t("subscription.autoRenew") : "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
