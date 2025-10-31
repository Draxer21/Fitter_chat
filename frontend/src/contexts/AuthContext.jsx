import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API } from "../services/apijs";

const AuthContext = createContext(null);

const anonymousUser = { auth: false, user: null, is_admin: false };

const makeDefaultMfaState = () => ({
  enabled: false,
  enabledAt: null,
  backupCodesLeft: 0,
  secret: null,
  otpauthUrl: null,
  recoveryCodes: [],
  loading: false,
  error: null,
});

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
  const [mfaState, setMfaState] = useState(() => makeDefaultMfaState());
  const [initialized, setInitialized] = useState(false);
  const initRef = useRef(false);

  const applyAuth = useCallback((payload) => {
    const normalized = normalizeAuthPayload(payload);
    setAuthState(normalized);
    return normalized;
  }, []);

  const resetMfa = useCallback(() => {
    setMfaState(makeDefaultMfaState());
  }, []);

  const loadMfaStatus = useCallback(async () => {
    setMfaState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await API.auth.mfa.status();
      const normalized = {
        enabled: Boolean(data?.enabled),
        enabledAt: data?.enabled_at || data?.enabledAt || null,
        backupCodesLeft: data?.backup_codes_left ?? data?.backupCodesLeft ?? (Array.isArray(data?.backup_codes) ? data.backup_codes.length : 0),
      };
      setMfaState({
        ...makeDefaultMfaState(),
        ...normalized,
        loading: false,
      });
      return normalized;
    } catch (err) {
      if (err?.status === 401) {
        resetMfa();
        return makeDefaultMfaState();
      }
      setMfaState((prev) => ({ ...prev, loading: false, error: err }));
      throw err;
    }
  }, [resetMfa]);

  const refresh = useCallback(async () => {
    setStatus((prev) => (prev === "authenticating" ? prev : "loading"));
    try {
      const data = await API.auth.me();
      const normalized = applyAuth(data);
      setError(null);
      if (normalized?.auth) {
        loadMfaStatus().catch(() => {});
      } else {
        resetMfa();
      }
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
    async (username, password, options = {}) => {
      setStatus("authenticating");
      try {
        const data = await API.auth.login(username, password, options);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        loadMfaStatus().catch(() => {});
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
      resetMfa();
      setError(null);
      setInitialized(true);
      setStatus("ready");
    }
  }, [applyAuth, resetMfa]);

  const startMfaSetup = useCallback(async () => {
    if (!authState?.auth) {
      throw new Error("No autenticado");
    }
    setMfaState((prev) => ({ ...prev, loading: true, error: null, recoveryCodes: [] }));
    try {
      const data = await API.auth.mfa.setup();
      const normalized = {
        secret: data?.secret || null,
        otpauthUrl: data?.otpauth_url || data?.otpauthUrl || null,
      };
      setMfaState((prev) => ({
        ...prev,
        ...normalized,
        loading: false,
        enabled: false,
        error: null,
      }));
      return normalized;
    } catch (err) {
      setMfaState((prev) => ({ ...prev, loading: false, error: err }));
      throw err;
    }
  }, [authState?.auth]);

  const confirmMfa = useCallback(
    async (code) => {
      if (!code) {
        throw new Error("Codigo requerido");
      }
      setMfaState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const data = await API.auth.mfa.confirm({ code });
        const recoveryCodes = data?.backup_codes || data?.recovery_codes || [];
        await loadMfaStatus();
        setMfaState((prev) => ({
          ...prev,
          loading: false,
          error: null,
          recoveryCodes,
          secret: null,
          otpauthUrl: null,
        }));
        return { recoveryCodes };
      } catch (err) {
        setMfaState((prev) => ({ ...prev, loading: false, error: err }));
        throw err;
      }
    },
    [loadMfaStatus]
  );

  const disableMfa = useCallback(
    async ({ code, backupCode } = {}) => {
      setMfaState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        await API.auth.mfa.disable({ code, backupCode });
        await loadMfaStatus();
        setMfaState((prev) => ({
          ...prev,
          loading: false,
          error: null,
          recoveryCodes: [],
          secret: null,
          otpauthUrl: null,
        }));
      } catch (err) {
        setMfaState((prev) => ({ ...prev, loading: false, error: err }));
        throw err;
      }
    },
    [loadMfaStatus]
  );

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
      mfa: mfaState,
      loadMfaStatus,
      startMfaSetup,
      confirmMfa,
      disableMfa,
    }),
    [authState, status, initialized, error, login, logout, refresh, setUser, mfaState, loadMfaStatus, startMfaSetup, confirmMfa, disableMfa]
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
