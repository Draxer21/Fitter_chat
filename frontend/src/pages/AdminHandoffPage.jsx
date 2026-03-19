import { useCallback, useEffect, useRef, useState } from "react";
import { API } from "../services/apijs";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import "../styles/admin-handoff.css";

const FILTERS = ["all", "pending", "assigned", "resolved"];
const REFRESH_INTERVAL = 30_000;

const formatDate = (iso) => {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

function StatusBadge({ status, t }) {
  const key = `handoff.status.${status}`;
  return (
    <span className={`handoff-badge handoff-badge--${status}`}>
      {t(key)}
    </span>
  );
}

function ResolveModal({ request, t, onClose, onSubmit }) {
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(request.id, notes);
      onClose();
    } catch {
      setSubmitting(false);
    }
  };

  return (
    <div className="handoff-resolve-modal" onClick={onClose}>
      <div
        className="handoff-resolve-modal__content"
        onClick={(e) => e.stopPropagation()}
      >
        <h4>{t("handoff.resolve")}</h4>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label" htmlFor="resolve-notes">
              {t("handoff.resolveNotes")}
            </label>
            <textarea
              id="resolve-notes"
              className="form-control"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              required
            />
          </div>
          <div className="d-flex justify-content-end gap-2">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              {t("handoff.cancel") || "Cancel"}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {t("handoff.resolve")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AdminHandoffPage() {
  const { isAdmin } = useAuth();
  const { t } = useLocale();

  const [requests, setRequests] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [resolving, setResolving] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const status = activeFilter === "all" ? undefined : activeFilter;
      const [list, countData] = await Promise.all([
        API.handoff.list(status),
        API.handoff.pendingCount(),
      ]);
      setRequests(list);
      setPendingCount(countData?.count ?? 0);
      setError("");
    } catch {
      setError(t("handoff.error"));
    } finally {
      setLoading(false);
    }
  }, [activeFilter, t]);

  useEffect(() => {
    if (!isAdmin) return;
    setLoading(true);
    fetchData();
  }, [isAdmin, fetchData]);

  useEffect(() => {
    if (!isAdmin) return;
    intervalRef.current = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [isAdmin, fetchData]);

  const handleAssign = async (id) => {
    try {
      await API.handoff.assign(id);
      await fetchData();
    } catch {
      setError(t("handoff.error"));
    }
  };

  const handleResolve = async (id, notes) => {
    await API.handoff.resolve(id, notes);
    await fetchData();
  };

  if (!isAdmin) {
    return (
      <div className="handoff-page container py-4">
        <div className="alert alert-danger">{t("handoff.unauthorized")}</div>
      </div>
    );
  }

  return (
    <div className="handoff-page container py-4">
      <div className="d-flex align-items-center gap-3 mb-4">
        <h2 className="mb-0">{t("handoff.title")}</h2>
        {pendingCount > 0 && (
          <span className="badge bg-danger rounded-pill">
            {pendingCount}
          </span>
        )}
      </div>
      <p className="text-muted mb-4">{t("handoff.subtitle")}</p>

      {/* Filter tabs */}
      <div className="handoff-filters mb-4">
        {FILTERS.map((filter) => (
          <button
            key={filter}
            className={`handoff-filter ${activeFilter === filter ? "handoff-filter--active" : ""}`}
            onClick={() => setActiveFilter(filter)}
          >
            {t(`handoff.filter.${filter}`)}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border" role="status" />
        </div>
      ) : requests.length === 0 ? (
        <p className="text-muted text-center py-5">{t("handoff.empty")}</p>
      ) : (
        <>
          {/* Desktop table */}
          <div className="handoff-table d-none d-md-block">
            <table className="table table-hover align-middle">
              <thead>
                <tr>
                  <th>{t("handoff.table.sender")}</th>
                  <th>{t("handoff.table.reason")}</th>
                  <th>{t("handoff.table.status")}</th>
                  <th>{t("handoff.table.created")}</th>
                  <th>{t("handoff.table.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id}>
                    <td>{req.sender_id}</td>
                    <td>{req.reason}</td>
                    <td>
                      <StatusBadge status={req.status} t={t} />
                    </td>
                    <td>{formatDate(req.created_at)}</td>
                    <td>
                      {req.status === "pending" && (
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => handleAssign(req.id)}
                        >
                          {t("handoff.assign")}
                        </button>
                      )}
                      {req.status === "assigned" && (
                        <button
                          className="btn btn-sm btn-success"
                          onClick={() => setResolving(req)}
                        >
                          {t("handoff.resolve")}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="d-md-none d-flex flex-column gap-3">
            {requests.map((req) => (
              <div key={req.id} className="handoff-card">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <strong>{req.sender_id}</strong>
                  <StatusBadge status={req.status} t={t} />
                </div>
                <p className="mb-1">{req.reason}</p>
                <small className="text-muted d-block mb-2">
                  {formatDate(req.created_at)}
                </small>
                {req.assigned_admin_id && (
                  <small className="text-muted d-block mb-2">
                    Admin: {req.assigned_admin_id}
                  </small>
                )}
                <div className="d-flex gap-2">
                  {req.status === "pending" && (
                    <button
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => handleAssign(req.id)}
                    >
                      {t("handoff.assign")}
                    </button>
                  )}
                  {req.status === "assigned" && (
                    <button
                      className="btn btn-sm btn-success"
                      onClick={() => setResolving(req)}
                    >
                      {t("handoff.resolve")}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Resolve modal */}
      {resolving && (
        <ResolveModal
          request={resolving}
          t={t}
          onClose={() => setResolving(null)}
          onSubmit={handleResolve}
        />
      )}
    </div>
  );
}
