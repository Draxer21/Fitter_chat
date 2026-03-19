import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import { API } from "../services/apijs";
import "../styles/analytics-dashboard.css";

function KpiCard({ label, value, unit, variant }) {
  return (
    <div className={`analytics-kpi ${variant ? `analytics-kpi--${variant}` : ""}`}>
      <span className="analytics-kpi__label">{label}</span>
      <span className="analytics-kpi__value">
        {value ?? "—"}
        {unit && <small className="analytics-kpi__unit">{unit}</small>}
      </span>
    </div>
  );
}

function BarChart({ title, items }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="analytics-chart">
      <h3 className="analytics-chart__title">{title}</h3>
      <div className="analytics-chart__bars">
        {items.map((item) => (
          <div className="analytics-bar" key={item.label}>
            <span className="analytics-bar__label">{item.label}</span>
            <div className="analytics-bar__track">
              <div
                className={`analytics-bar__fill analytics-bar__fill--${item.color || "default"}`}
                style={{ width: `${Math.max((item.value / max) * 100, 2)}%` }}
              />
            </div>
            <span className="analytics-bar__value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AnalyticsDashboardPage() {
  const { t } = useLocale();
  const { isAdmin } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const snapshot = await API.metrics.snapshot();
      setData(snapshot);
      setError("");
    } catch (err) {
      setError(err?.message || t("common.error"));
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(load, 30_000);
    }
    return () => clearInterval(intervalRef.current);
  }, [autoRefresh, load]);

  if (!isAdmin) {
    return (
      <div className="analytics-page py-5">
        <div className="container">
          <div className="alert alert-danger">{t("analytics.unauthorized")}</div>
        </div>
      </div>
    );
  }

  const pct = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—");

  return (
    <div className="analytics-page py-5">
      <div className="container">
        <header className="analytics-header mb-4">
          <div>
            <h1>{t("analytics.title")}</h1>
            <p className="text-muted">{t("analytics.subtitle")}</p>
          </div>
          <div className="analytics-actions">
            <label className="form-check form-switch d-inline-flex align-items-center gap-2 me-3">
              <input
                className="form-check-input"
                type="checkbox"
                checked={autoRefresh}
                onChange={() => setAutoRefresh((v) => !v)}
              />
              <span className="form-check-label">{t("analytics.autoRefresh")}</span>
            </label>
            <button className="btn btn-outline-primary btn-sm" onClick={load}>
              {t("analytics.refresh")}
            </button>
          </div>
        </header>

        {error && <div className="alert alert-danger">{error}</div>}

        {!data && !error && <p className="text-muted">{t("common.loading")}</p>}

        {data && (
          <>
            <div className="analytics-kpis mb-4">
              <KpiCard label={t("analytics.kpi.windowSize")} value={data.window_size} unit={t("analytics.events")} />
              <KpiCard label={t("analytics.kpi.p95Latency")} value={data.p95_latency_ms?.toFixed(0)} unit={t("analytics.ms")} />
              <KpiCard label={t("analytics.kpi.fallbackRate")} value={pct(data.fallback_rate)} variant="warn" />
              <KpiCard label={t("analytics.kpi.handoffRate")} value={pct(data.handoff_rate)} variant="info" />
              <KpiCard label={t("analytics.kpi.blockedRate")} value={pct(data.blocked_rate)} variant="danger" />
            </div>

            <BarChart
              title={t("analytics.chart.statusCodes")}
              items={[
                { label: "2xx", value: data.count_2xx || 0, color: "success" },
                { label: "4xx", value: data.count_4xx || 0, color: "warn" },
                { label: "5xx", value: data.count_5xx || 0, color: "danger" },
              ]}
            />
          </>
        )}
      </div>
    </div>
  );
}
