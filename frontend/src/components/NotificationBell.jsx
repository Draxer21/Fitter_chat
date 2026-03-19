import { useEffect, useRef, useState } from "react";
import { useNotifications } from "../contexts/NotificationContext";
import { useLocale } from "../contexts/LocaleContext";
import "../styles/notifications.css";

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

function getRelativeTime(timestamp, t) {
  const now = new Date();
  const diff = Math.floor((now - new Date(timestamp)) / 1000);
  if (diff < 60) {
    return t("notifications.momentAgo");
  }
  const minutes = Math.floor(diff / 60);
  if (minutes < 60) {
    const template = t("notifications.minutesAgo");
    return template.replace("{n}", minutes);
  }
  const hours = Math.floor(minutes / 60);
  const template = t("notifications.hoursAgo");
  return template.replace("{n}", hours);
}

export default function NotificationBell() {
  const { notifications, unreadCount, markAllRead, clearAll } = useNotifications();
  const { t } = useLocale();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  return (
    <div className="notification-bell" ref={containerRef}>
      <button
        className="notification-bell__button nav-link d-flex align-items-center px-3"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={t("notifications.title")}
        aria-expanded={open}
        title={t("notifications.title")}
        type="button"
      >
        🔔
        {unreadCount > 0 && (
          <span className="notification-badge" aria-hidden="true">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="notification-dropdown" role="dialog" aria-label={t("notifications.title")}>
          <div className="notification-dropdown__header">
            <h6 className="notification-dropdown__title">{t("notifications.title")}</h6>
            <div className="notification-dropdown__actions">
              {notifications.length > 0 && (
                <>
                  <button
                    type="button"
                    className="notification-dropdown__action-btn"
                    onClick={markAllRead}
                  >
                    {t("notifications.markAllRead")}
                  </button>
                  <button
                    type="button"
                    className="notification-dropdown__action-btn"
                    onClick={clearAll}
                  >
                    {t("notifications.clearAll")}
                  </button>
                </>
              )}
            </div>
          </div>

          {notifications.length === 0 ? (
            <div className="notification-dropdown__empty">
              {t("notifications.empty")}
            </div>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {notifications.map((notif) => (
                <li
                  key={notif.id}
                  className={`notification-item${notif.read ? "" : " notification-item--unread"}`}
                >
                  <span className="notification-item__icon" aria-hidden="true">
                    {getTypeIcon(notif.type)}
                  </span>
                  <div className="notification-item__body">
                    <p className="notification-item__message">{notif.message}</p>
                    <span className="notification-item__time">
                      {getRelativeTime(notif.timestamp, t)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
