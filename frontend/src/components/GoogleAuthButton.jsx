import { useCallback, useEffect, useRef, useState } from "react";

const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";
let googleScriptPromise = null;

const loadGoogleScript = () => {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("window_not_available"));
  }
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (googleScriptPromise) {
    return googleScriptPromise;
  }
  googleScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("google_script_failed"));
    document.head.appendChild(script);
  });
  return googleScriptPromise;
};

export default function GoogleAuthButton({
  onCredential,
  onError,
  mode = "signin",
  className = "",
}) {
  const containerRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [scriptError, setScriptError] = useState(null);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    let cancelled = false;
    if (!clientId) {
      setScriptError("missing_client_id");
      return () => {};
    }
    loadGoogleScript()
      .then(() => {
        if (!cancelled) {
          setReady(true);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setScriptError(err?.message || "load_failed");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [clientId]);

  const renderButton = useCallback(() => {
    if (!ready || !clientId || typeof window === "undefined") {
      return;
    }
    const google = window.google;
    if (!google?.accounts?.id || !containerRef.current) {
      return;
    }
    containerRef.current.innerHTML = "";
    google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (response?.credential) {
          onCredential?.(response.credential, response);
        } else {
          onError?.(new Error("missing_credential"));
        }
      },
      ux_mode: "popup",
      auto_select: false,
      use_fedcm_for_prompt: false,
    });
    const buttonMode = mode === "signup" ? "signup_with" : "signin_with";
    google.accounts.id.renderButton(containerRef.current, {
      theme: "outline",
      size: "large",
      type: "standard",
      text: buttonMode,
      shape: "rectangular",
      logo_alignment: "left",
      width: 300,
    });
  }, [ready, clientId, onCredential, onError, mode]);

  useEffect(() => {
    renderButton();
  }, [renderButton]);

  if (!clientId) {
    return (
      <div className={`alert alert-warning ${className}`} role="status">
        Google Sign-In no está configurado.
      </div>
    );
  }

  if (scriptError) {
    return (
      <div className={`alert alert-warning ${className}`} role="status">
        No se pudo cargar el botón de Google.
      </div>
    );
  }

  return (
    <div className={className}>
      <div ref={containerRef} className="d-flex justify-content-center" />
    </div>
  );
}
