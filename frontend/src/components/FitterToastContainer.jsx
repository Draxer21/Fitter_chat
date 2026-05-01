import { useCallback, useEffect, useState } from "react";
import { useToast } from "../contexts/ToastContext";

/* =========================================================
   FitterToastContainer — renders kimi-style toasts
   Uses classes from kimi-components.css:
     .toast-container, .fitter-toast.{type},
     .toast-icon, .toast-content, .toast-title,
     .toast-desc, .toast-close, .toast-progress
   ========================================================= */

const TOAST_ICONS = {
  success: "bi-check-circle-fill",
  error:   "bi-x-circle-fill",
  warning: "bi-exclamation-triangle-fill",
  info:    "bi-info-circle-fill",
};

const TOAST_COLORS = {
  success: "var(--success, #22c55e)",
  error:   "var(--danger, #ef4444)",
  warning: "var(--warning, #f59e0b)",
  info:    "var(--info, #3b82f6)",
};

const AUTO_DISMISS_MS = 4000;

function SingleToast({ toast, onDismiss }) {
  const [hiding, setHiding] = useState(false);

  const dismiss = useCallback(() => {
    setHiding(true);
    setTimeout(() => onDismiss(toast.id), 320);
  }, [toast.id, onDismiss]);

  useEffect(() => {
    const timer = setTimeout(dismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [dismiss]);

  return (
    <div
      className={`fitter-toast ${toast.type}${hiding ? " hiding" : ""}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      {/* Icon */}
      <div className="toast-icon" aria-hidden="true">
        <i className={`bi ${TOAST_ICONS[toast.type] || TOAST_ICONS.info}`} />
      </div>

      {/* Content */}
      <div className="toast-content">
        <div className="toast-title">{toast.title}</div>
        {toast.desc && <div className="toast-desc">{toast.desc}</div>}
      </div>

      {/* Close */}
      <button
        type="button"
        className="toast-close"
        onClick={dismiss}
        aria-label="Cerrar notificación"
      >
        <i className="bi bi-x-lg" />
      </button>

      {/* Progress bar */}
      <div
        className="toast-progress"
        style={{ color: TOAST_COLORS[toast.type] || TOAST_COLORS.info }}
      />
    </div>
  );
}

export default function FitterToastContainer() {
  const { toasts, dismissToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-label="Notificaciones">
      {toasts.map((t) => (
        <SingleToast key={t.id} toast={t} onDismiss={dismissToast} />
      ))}
    </div>
  );
}
