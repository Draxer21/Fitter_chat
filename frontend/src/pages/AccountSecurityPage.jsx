import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const formatDateTime = (isoString) => {
  if (!isoString) return "—";
  try {
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) {
      return isoString;
    }
    return date.toLocaleString();
  } catch (err) {
    return isoString;
  }
};

export default function AccountSecurityPage() {
  const {
    isAuthenticated,
    mfa,
    loadMfaStatus,
    startMfaSetup,
    confirmMfa,
    disableMfa,
  } = useAuth();
  const [totpCode, setTotpCode] = useState("");
  const [disableTotp, setDisableTotp] = useState("");
  const [disableBackup, setDisableBackup] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState([]);

  useEffect(() => {
    if (isAuthenticated) {
      loadMfaStatus().catch(() => {});
    } else {
      setRecoveryCodes([]);
    }
  }, [isAuthenticated, loadMfaStatus]);

  useEffect(() => {
    if (Array.isArray(mfa?.recoveryCodes)) {
      setRecoveryCodes(mfa.recoveryCodes);
    }
  }, [mfa?.recoveryCodes]);

  const setupInProgress = useMemo(() => Boolean(mfa?.secret || mfa?.otpauthUrl), [mfa?.secret, mfa?.otpauthUrl]);

  const handleStartSetup = async () => {
    setInfoMessage("");
    setErrorMessage("");
    try {
      await startMfaSetup();
      setInfoMessage("Escanea el código QR o ingresa la clave secreta en tu app autenticadora y luego confirma con un código TOTP.");
      setTotpCode("");
    } catch (err) {
      setErrorMessage(err?.message || "No fue posible iniciar la configuración.");
    }
  };

  const handleConfirm = async (event) => {
    event.preventDefault();
    setInfoMessage("");
    setErrorMessage("");
    try {
      const result = await confirmMfa(totpCode.trim());
      const codes = result?.recoveryCodes || [];
      setRecoveryCodes(codes);
      setTotpCode("");
      setInfoMessage("Autenticación multifactor activada. Guarda tus códigos de respaldo en un lugar seguro.");
    } catch (err) {
      setErrorMessage(err?.message || "No pudimos verificar el código. Intenta nuevamente.");
    }
  };

  const handleDisable = async (event) => {
    event.preventDefault();
    setInfoMessage("");
    setErrorMessage("");
    if (!disableTotp && !disableBackup) {
      setErrorMessage("Ingresa un código TOTP o uno de respaldo para continuar.");
      return;
    }
    try {
      await disableMfa({ code: disableTotp.trim(), backupCode: disableBackup.trim() });
      setDisableTotp("");
      setDisableBackup("");
      setInfoMessage("Autenticación multifactor desactivada.");
    } catch (err) {
      setErrorMessage(err?.message || "No pudimos desactivar MFA. Revisa el código e inténtalo de nuevo.");
    }
  };

  const handleRefresh = () => {
    loadMfaStatus().catch((err) => {
      setErrorMessage(err?.message || "No se pudo actualizar el estado MFA.");
    });
  };

  if (!isAuthenticated) {
    return (
      <main className="container py-5">
        <div className="row justify-content-center">
          <div className="col-lg-6">
            <div className="alert alert-warning">
              Necesitas iniciar sesión para gestionar la autenticación de dos factores.
              <div className="mt-3">
                <Link className="btn btn-dark" to="/login">
                  Ir al inicio de sesión
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="container py-5">
      <div className="row justify-content-center">
        <div className="col-xl-8 col-lg-9">
          <h1 className="mb-4">Seguridad de la cuenta</h1>
          <p className="text-muted">
            Activa la autenticación de dos factores (MFA) para proteger tu cuenta con un código adicional generado por una app (Authy, Google Authenticator, 1Password, etc.).
          </p>

          {infoMessage && <div className="alert alert-success">{infoMessage}</div>}
          {errorMessage && <div className="alert alert-danger">{errorMessage}</div>}
          {mfa?.error && !errorMessage && <div className="alert alert-danger">{mfa.error.message || "Error consultando MFA."}</div>}

          <section className="card shadow-sm mb-4">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                  <h5 className="card-title mb-1">Estado actual</h5>
                  <span className={`badge ${mfa?.enabled ? "bg-success" : "bg-secondary"}`}>
                    {mfa?.enabled ? "Activado" : "Desactivado"}
                  </span>
                  <div className="text-muted small mt-2">
                    Última activación: {formatDateTime(mfa?.enabledAt)}
                  </div>
                  <div className="text-muted small">
                    Códigos de respaldo restantes: {mfa?.backupCodesLeft ?? 0}
                  </div>
                </div>
                <button type="button" className="btn btn-outline-secondary btn-sm" onClick={handleRefresh} disabled={mfa?.loading}>
                  {mfa?.loading ? "Actualizando..." : "Actualizar estado"}
                </button>
              </div>
            </div>
          </section>

          {!mfa?.enabled && (
            <section className="card shadow-sm mb-4">
              <div className="card-body">
                <h5 className="card-title">Activar MFA</h5>
                <p className="text-muted">
                  Es necesario escanear un código QR o ingresar la clave secreta en tu aplicación autenticadora antes de confirmar.
                </p>
                <button
                  type="button"
                  className="btn btn-dark mb-3"
                  onClick={handleStartSetup}
                  disabled={mfa?.loading}
                >
                  {setupInProgress ? "Reiniciar configuración" : "Generar clave secreta"}
                </button>

                {setupInProgress && (
                  <div className="border rounded p-3 mb-3 bg-light">
                    <h6>Clave secreta</h6>
                    <code style={{ wordBreak: "break-all" }}>{mfa?.secret || "—"}</code>
                    {mfa?.otpauthUrl && (
                      <div className="mt-3">
                        <h6>Escanea el código QR</h6>
                        <img
                          src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(mfa.otpauthUrl)}`}
                          alt="QR para autenticar MFA"
                          width={180}
                          height={180}
                        />
                        <div className="small text-muted mt-2">
                          Si prefieres, abre el enlace directamente:{" "}
                          <a href={mfa.otpauthUrl} target="_blank" rel="noreferrer">
                            {mfa.otpauthUrl}
                          </a>
                        </div>
                      </div>
                    )}

                    <form className="mt-3" onSubmit={handleConfirm}>
                      <div className="mb-3">
                        <label htmlFor="confirmTotp" className="form-label">Código TOTP</label>
                        <input
                          id="confirmTotp"
                          className="form-control"
                          value={totpCode}
                          onChange={(event) => setTotpCode(event.target.value)}
                          placeholder="Introduce un código de 6 dígitos"
                          autoComplete="one-time-code"
                          required
                        />
                      </div>
                      <button type="submit" className="btn btn-success" disabled={mfa?.loading}>
                        Confirmar activación
                      </button>
                    </form>
                  </div>
                )}
              </div>
            </section>
          )}

          {mfa?.enabled && (
            <section className="card shadow-sm mb-4">
              <div className="card-body">
                <h5 className="card-title">Desactivar MFA</h5>
                <p className="text-muted">
                  Para desactivar la autenticación multifactor ingresa un código TOTP vigente o uno de tus códigos de respaldo.
                </p>
                <form onSubmit={handleDisable}>
                  <div className="row g-3">
                    <div className="col-md-6">
                      <label htmlFor="disableTotp" className="form-label">Código TOTP</label>
                      <input
                        id="disableTotp"
                        className="form-control"
                        value={disableTotp}
                        onChange={(event) => setDisableTotp(event.target.value)}
                        placeholder="Código de 6 dígitos"
                      />
                    </div>
                    <div className="col-md-6">
                      <label htmlFor="disableBackup" className="form-label">Código de respaldo</label>
                      <input
                        id="disableBackup"
                        className="form-control"
                        value={disableBackup}
                        onChange={(event) => setDisableBackup(event.target.value)}
                        placeholder="Ingresa un código de respaldo válido"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <button type="submit" className="btn btn-outline-danger" disabled={mfa?.loading}>
                      Desactivar MFA
                    </button>
                  </div>
                </form>
              </div>
            </section>
          )}

          {Array.isArray(recoveryCodes) && recoveryCodes.length > 0 && (
            <section className="card shadow-sm">
              <div className="card-body">
                <h5 className="card-title">Códigos de respaldo</h5>
                <p className="text-muted">
                  Guarda estos códigos en un lugar seguro. Cada uno puede utilizarse una sola vez cuando no tengas acceso a tu app autenticadora.
                </p>
                <ol className="ps-3">
                  {recoveryCodes.map((code) => (
                    <li key={code}>
                      <code>{code}</code>
                    </li>
                  ))}
                </ol>
              </div>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}

