import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { io } from "socket.io-client";
import { useAuth } from "../contexts/AuthContext";

const NotificationContext = createContext(null);

const MAX_NOTIFICATIONS = 50;

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const socketRef = useRef(null);

  const addNotification = useCallback((notif) => {
    setNotifications((prev) => {
      const newNotif = {
        id: Date.now(),
        type: notif.type || "info",
        message: notif.message || "",
        timestamp: new Date(),
        read: false,
        ...notif,
      };
      const updated = [newNotif, ...prev];
      return updated.slice(0, MAX_NOTIFICATIONS);
    });
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      return;
    }

    const socketUrl = typeof window !== "undefined" ? window.location.origin : BACKEND_URL;
    const socket = io(socketUrl, {
      withCredentials: true,
      transports: ["websocket", "polling"],
    });

    socketRef.current = socket;

    socket.on("notification", (data) => {
      addNotification({ type: data.type || "info", message: data.message || "", ...data });
    });

    socket.on("new_handoff", (data) => {
      addNotification({
        type: "handoff",
        message: data.message || "notifications.newHandoff",
        ...data,
      });
    });

    socket.on("subscription_update", (data) => {
      addNotification({
        type: "subscription",
        message: data.message || "notifications.subscriptionUpdate",
        ...data,
      });
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [isAuthenticated, addNotification]);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !n.read).length,
    [notifications]
  );

  const value = useMemo(
    () => ({
      notifications,
      unreadCount,
      addNotification,
      markAllRead,
      clearAll,
    }),
    [notifications, unreadCount, addNotification, markAllRead, clearAll]
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return ctx;
}
