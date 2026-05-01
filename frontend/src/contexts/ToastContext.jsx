import { createContext, useCallback, useContext, useState } from "react";

/* =========================================================
   ToastContext — lightweight toast notification system
   Exports: ToastProvider, useToast
   useToast() → { showToast(type, title, desc) }
   type: 'success' | 'error' | 'warning' | 'info'
   Max 3 toasts at once; auto-dismiss after 4 s
   ========================================================= */

const ToastContext = createContext(null);

const MAX_TOASTS = 3;
let _idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((type, title, desc = "") => {
    const id = ++_idCounter;
    setToasts((prev) => {
      const next = [...prev, { id, type, title, desc }];
      // Keep only the last MAX_TOASTS
      return next.slice(-MAX_TOASTS);
    });
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }
  return ctx;
}
