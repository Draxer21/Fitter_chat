import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API } from "../services/apijs";

const AuthContext = createContext(null);

const anonymousUser = { auth: false, user: null, is_admin: false };

const normalizeAuthPayload = (payload) => {
  if (!payload || typeof payload !== "object") {
    return { ...anonymousUser };
  }
  const authFlag = Boolean(payload.auth ?? payload.user);
  if (!authFlag) {
    return { ...anonymousUser };
  }
  const user = payload.user ?? payload;
  return {
    auth: true,
    user: user || null,
    is_admin: Boolean(payload.is_admin ?? user?.is_admin),
  };
};

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState({ ...anonymousUser });
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const initRef = useRef(false);

  const applyAuth = useCallback((payload) => {
    const normalized = normalizeAuthPayload(payload);
    setAuthState(normalized);
    return normalized;
  }, []);

  const refresh = useCallback(async () => {
    setStatus((prev) => (prev === "authenticating" ? prev : "loading"));
    try {
      const data = await API.auth.me();
      const normalized = applyAuth(data);
      setError(null);
      return normalized;
    } catch (err) {
      applyAuth(null);
      setError(err);
      throw err;
    } finally {
      setInitialized(true);
      setStatus("ready");
    }
  }, [applyAuth]);

  const login = useCallback(
    async (username, password) => {
      setStatus("authenticating");
      try {
        const data = await API.auth.login(username, password);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        return normalized;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setInitialized(true);
        setStatus("ready");
      }
    },
    [applyAuth]
  );

  const logout = useCallback(async () => {
    setStatus("loading");
    try {
      await API.auth.logout();
    } catch (err) {
      // ignore logout network failures
    } finally {
      applyAuth(null);
      setError(null);
      setInitialized(true);
      setStatus("ready");
    }
  }, [applyAuth]);

  const setUser = useCallback((updater) => {
    setAuthState((prev) => {
      const nextUser = typeof updater === "function" ? updater(prev.user) : updater;
      if (!nextUser) {
        return { ...anonymousUser };
      }
      return {
        auth: true,
        user: nextUser,
        is_admin: Boolean(nextUser?.is_admin),
      };
    });
  }, []);

  useEffect(() => {
    if (initRef.current) {
      return;
    }
    initRef.current = true;
    refresh().catch(() => {
      /* initial auth fetch can fail silently */
    });
  }, [refresh]);

  const value = useMemo(
    () => ({
      auth: authState,
      user: authState.user,
      isAuthenticated: Boolean(authState.auth && authState.user),
      isAdmin: Boolean(authState.is_admin),
      status,
      loading: status === "loading" && !initialized,
      authenticating: status === "authenticating",
      initialized,
      error,
      login,
      logout,
      refresh,
      setUser,
    }),
    [authState, status, initialized, error, login, logout, refresh, setUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
