import { useEffect, useRef, useState } from "react";
import { useNotifications } from "../contexts/NotificationContext";
import "../styles/notifications.css";

const TOAST_DURATION = 5000;

const TYPE_ICONS = {
  handoff: "🔄",
  subscription: "💳",
  info: "ℹ️",
  success: "✅",
  warning: "⚠️",
  error: "❌",
};

function getTypeIcon(type) {
  return TYPE_ICONS[type] || TYPE_ICONS.info;
}

function Toast({ notification, onDismiss }) {
  const [phase, setPhase] = useState("entering");

  useEffect(() => {
    // Trigger enter animation on next frame
    const enterTimer = requestAnimationFrame(() => {
      setPhase("visible");
    });

    const dismissTimer = setTimeout(() => {
      setPhase("exiting");
      setTimeout(() => onDismiss(notification.id), 300);
    }, TOAST_DURATION);

    return () => {
      cancelAnimationFrame(enterTimer);
      clearTimeout(dismissTimer);
    };
  }, [notification.id, onDismiss]);

  const handleClose = () => {
    setPhase("exiting");
    setTimeout(() => onDismiss(notification.id), 300);
  };

  return (
    <div
      className={`toast toast--${phase === "entering" ? "entering" : phase === "exiting" ? "exiting" : ""}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <span className="toast__icon" aria-hidden="true">
        {getTypeIcon(notification.type)}
      </span>
      <div className="toast__body">
        <p className="toast__message">{notification.message}</p>
      </div>
      <button
        type="button"
        className="toast__close"
        onClick={handleClose}
        aria-label="Cerrar"
      >
        &times;
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const { notifications } = useNotifications();
  const [toasts, setToasts] = useState([]);
  const prevLengthRef = useRef(notifications.length);

  useEffect(() => {
    const currentLength = notifications.length;
    if (currentLength > prevLengthRef.current) {
      // New notification(s) added
      const newOnes = notifications.slice(0, currentLength - prevLengthRef.current);
      setToasts((prev) => [
        ...newOnes.map((n) => ({ ...n })),
        ...prev,
      ]);
    }
    prevLengthRef.current = currentLength;
  }, [notifications]);

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-container" aria-label="Notificaciones">
      {toasts.map((toast) => (
        <Toast key={toast.id} notification={toast} onDismiss={dismissToast} />
      ))}
    </div>
  );
}
