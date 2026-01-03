import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API } from "../services/apijs";

const AuthContext = createContext(null);

const anonymousUser = { auth: false, user: null, is_admin: false };

const makeDefaultProfileState = () => ({
  data: null,
  loading: false,
  error: null,
});

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
  const [profileState, setProfileState] = useState(makeDefaultProfileState());
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

  const resetProfile = useCallback(() => {
    setProfileState(makeDefaultProfileState());
  }, []);

  const loadProfile = useCallback(async () => {
    setProfileState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const payload = await API.profile.me();
      const data = payload?.profile || null;
      setProfileState({ data, loading: false, error: null });
      if (data) {
        setAuthState((prev) => ({
          ...prev,
          user: prev?.user ? { ...prev.user, profile: data } : prev.user,
        }));
      }
      return data;
    } catch (err) {
      if (err?.status === 401) {
        resetProfile();
        return null;
      }
      setProfileState((prev) => ({ ...prev, loading: false, error: err }));
      throw err;
    }
  }, [resetProfile]);

  const updateProfile = useCallback(async (changes = {}) => {
    setProfileState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const payload = await API.profile.update(changes);
      const data = payload?.profile || null;
      setProfileState({ data, loading: false, error: null });
      if (data) {
        setAuthState((prev) => ({
          ...prev,
          user: prev?.user ? { ...prev.user, profile: data } : prev.user,
        }));
      }
      return data;
    } catch (err) {
      if (err?.status === 401) {
        resetProfile();
      } else {
        setProfileState((prev) => ({ ...prev, loading: false, error: err }));
      }
      throw err;
    }
  }, [resetProfile]);

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
        loadProfile().catch(() => {});
      } else {
        resetMfa();
        resetProfile();
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
  }, [applyAuth, loadMfaStatus, loadProfile, resetMfa, resetProfile]);

  const login = useCallback(
    async (username, password, options = {}) => {
      setStatus("authenticating");
      try {
        const data = await API.auth.login(username, password, options);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        loadMfaStatus().catch(() => {});
        loadProfile().catch(() => {});
        return normalized;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setInitialized(true);
        setStatus("ready");
      }
    },
    [applyAuth, loadMfaStatus, loadProfile]
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
      resetProfile();
      setError(null);
      setInitialized(true);
      setStatus("ready");
    }
  }, [applyAuth, resetMfa, resetProfile]);

  const loginWithGoogle = useCallback(
    async (credential, options = {}) => {
      if (!credential) {
        throw new Error("Token de Google requerido");
      }
      setStatus("authenticating");
      try {
        const data = await API.auth.googleLogin(credential, options);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        loadMfaStatus().catch(() => {});
        loadProfile().catch(() => {});
        return normalized;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setInitialized(true);
        setStatus("ready");
      }
    },
    [applyAuth, loadMfaStatus, loadProfile]
  );

  const updateUsername = useCallback(
    async (username) => {
      if (!username) {
        throw new Error("Nombre de usuario requerido");
      }
      try {
        const data = await API.auth.updateUsername(username);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        return normalized?.user;
      } catch (err) {
        setError(err);
        throw err;
      }
    },
    [applyAuth]
  );

  const updateEmail = useCallback(
    async (email) => {
      if (!email) {
        throw new Error("Correo requerido");
      }
      try {
        const data = await API.auth.updateEmail(email);
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        return normalized?.user;
      } catch (err) {
        setError(err);
        throw err;
      }
    },
    [applyAuth]
  );

  const updatePassword = useCallback(
    async ({ currentPassword, newPassword, confirmPassword } = {}) => {
      if (!newPassword) {
        throw new Error("Nueva contraseña requerida");
      }
      try {
        const data = await API.auth.updatePassword({ currentPassword, newPassword, confirmPassword });
        const normalized = applyAuth({ auth: true, user: data?.user, is_admin: data?.user?.is_admin ?? data?.is_admin });
        setError(null);
        return normalized?.user;
      } catch (err) {
        setError(err);
        throw err;
      }
    },
    [applyAuth]
  );

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
      loginWithGoogle,
      logout,
      updateUsername,
      updateEmail,
      updatePassword,
      refresh,
      setUser,
      profile: profileState.data,
      profileState,
      profileLoading: profileState.loading,
      profileError: profileState.error,
      loadProfile,
      updateProfile,
      mfa: mfaState,
      loadMfaStatus,
      startMfaSetup,
      confirmMfa,
      disableMfa,
    }),
    [authState, status, initialized, error, login, loginWithGoogle, logout, refresh, setUser, profileState, loadProfile, updateProfile, updateUsername, updateEmail, updatePassword, mfaState, loadMfaStatus, startMfaSetup, confirmMfa, disableMfa]
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
