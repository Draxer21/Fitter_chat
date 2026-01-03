import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";

const usernamePattern = /^[a-z0-9_-]{3,32}$/;
const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function AccountDetailsCard() {
  const { t } = useLocale();
  const { user, updateUsername, updateEmail, updatePassword } = useAuth();
  const [accountMessage, setAccountMessage] = useState("");
  const [accountError, setAccountError] = useState("");
  const [accountStatus, setAccountStatus] = useState({
    username: "idle",
    email: "idle",
    password: "idle",
  });
  const [accountForm, setAccountForm] = useState(() => ({
    username: user?.username || "",
    email: user?.email || "",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  }));

  useEffect(() => {
    setAccountForm((prev) => ({
      ...prev,
      username: user?.username || "",
      email: user?.email || "",
    }));
  }, [user?.username, user?.email]);

  const handleAccountChange = (event) => {
    const { name, value } = event.target;
    setAccountForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleUsernameUpdate = async (event) => {
    event.preventDefault();
    setAccountMessage("");
    setAccountError("");
    const nextUsername = accountForm.username.trim().toLowerCase();
    if (!nextUsername) {
      setAccountError(t("account.errors.usernameRequired"));
      return;
    }
    if (!usernamePattern.test(nextUsername)) {
      setAccountError(t("account.errors.usernameInvalid"));
      return;
    }
    setAccountStatus((prev) => ({ ...prev, username: "saving" }));
    try {
      await updateUsername(nextUsername);
      setAccountMessage(t("account.alerts.usernameSuccess"));
    } catch (err) {
      setAccountError(err?.message || t("account.alerts.updateError"));
    } finally {
      setAccountStatus((prev) => ({ ...prev, username: "idle" }));
    }
  };

  const handleEmailUpdate = async (event) => {
    event.preventDefault();
    setAccountMessage("");
    setAccountError("");
    const nextEmail = accountForm.email.trim().toLowerCase();
    if (!nextEmail || !emailPattern.test(nextEmail)) {
      setAccountError(t("account.errors.emailRequired"));
      return;
    }
    setAccountStatus((prev) => ({ ...prev, email: "saving" }));
    try {
      await updateEmail(nextEmail);
      setAccountMessage(t("account.alerts.emailSuccess"));
    } catch (err) {
      setAccountError(err?.message || t("account.alerts.updateError"));
    } finally {
      setAccountStatus((prev) => ({ ...prev, email: "idle" }));
    }
  };

  const handlePasswordUpdate = async (event) => {
    event.preventDefault();
    setAccountMessage("");
    setAccountError("");
    const currentPassword = accountForm.currentPassword;
    const newPassword = accountForm.newPassword.trim();
    const confirmPassword = accountForm.confirmPassword.trim();

    if (!newPassword) {
      setAccountError(t("account.errors.passwordRequired"));
      return;
    }
    if (newPassword.length < 6) {
      setAccountError(t("account.errors.passwordLength"));
      return;
    }
    if (confirmPassword && newPassword !== confirmPassword) {
      setAccountError(t("account.errors.passwordMismatch"));
      return;
    }
    if (user?.has_password && !currentPassword) {
      setAccountError(t("account.errors.currentPasswordRequired"));
      return;
    }
    setAccountStatus((prev) => ({ ...prev, password: "saving" }));
    try {
      await updatePassword({ currentPassword, newPassword, confirmPassword });
      setAccountForm((prev) => ({
        ...prev,
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      }));
      setAccountMessage(t("account.alerts.passwordSuccess"));
    } catch (err) {
      setAccountError(err?.message || t("account.alerts.updateError"));
    } finally {
      setAccountStatus((prev) => ({ ...prev, password: "idle" }));
    }
  };

  return (
    <section className="profile-account card shadow-sm border-0">
      <div className="card-body">
        <div className="profile-account-header">
          <div>
            <p className="text-uppercase small text-muted mb-1">{t("account.section.eyebrow")}</p>
            <h2 className="h5 mb-1">{t("account.section.title")}</h2>
            <p className="text-muted mb-0">{t("account.section.subtitle")}</p>
          </div>
          <span className="badge rounded-pill text-bg-light border">{user?.email || "—"}</span>
        </div>

        {accountMessage && <div className="alert alert-success mt-3">{accountMessage}</div>}
        {accountError && <div className="alert alert-danger mt-3">{accountError}</div>}

        <div className="row g-4 mt-1">
          <div className="col-lg-6">
            <form onSubmit={handleUsernameUpdate} className="account-form">
              <label htmlFor="accountUsername" className="form-label">{t("account.username.label")}</label>
              <input
                id="accountUsername"
                name="username"
                className="form-control"
                value={accountForm.username}
                onChange={handleAccountChange}
                placeholder={t("account.username.placeholder")}
                autoComplete="username"
              />
              <button
                type="submit"
                className="btn btn-outline-dark mt-3"
                disabled={accountStatus.username === "saving"}
              >
                {accountStatus.username === "saving" ? t("profile.actions.saving") : t("account.username.action")}
              </button>
            </form>
          </div>
          <div className="col-lg-6">
            <form onSubmit={handleEmailUpdate} className="account-form">
              <label htmlFor="accountEmail" className="form-label">{t("account.email.label")}</label>
              <input
                id="accountEmail"
                name="email"
                type="email"
                className="form-control"
                value={accountForm.email}
                onChange={handleAccountChange}
                placeholder={t("account.email.placeholder")}
                autoComplete="email"
              />
              <button
                type="submit"
                className="btn btn-outline-dark mt-3"
                disabled={accountStatus.email === "saving"}
              >
                {accountStatus.email === "saving" ? t("profile.actions.saving") : t("account.email.action")}
              </button>
            </form>
          </div>
          <div className="col-12">
            <form onSubmit={handlePasswordUpdate} className="account-form">
              <div className="row g-3">
                <div className="col-md-4">
                  <label htmlFor="currentPassword" className="form-label">{t("account.password.current")}</label>
                  <input
                    id="currentPassword"
                    name="currentPassword"
                    type="password"
                    className="form-control"
                    value={accountForm.currentPassword}
                    onChange={handleAccountChange}
                    autoComplete="current-password"
                  />
                </div>
                <div className="col-md-4">
                  <label htmlFor="newPassword" className="form-label">{t("account.password.new")}</label>
                  <input
                    id="newPassword"
                    name="newPassword"
                    type="password"
                    className="form-control"
                    value={accountForm.newPassword}
                    onChange={handleAccountChange}
                    autoComplete="new-password"
                  />
                </div>
                <div className="col-md-4">
                  <label htmlFor="confirmPassword" className="form-label">{t("account.password.confirm")}</label>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    className="form-control"
                    value={accountForm.confirmPassword}
                    onChange={handleAccountChange}
                    autoComplete="new-password"
                  />
                </div>
              </div>
              <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mt-3">
                <small className="text-muted">{t("account.password.hint")}</small>
                <button
                  type="submit"
                  className="btn btn-outline-dark"
                  disabled={accountStatus.password === "saving"}
                >
                  {accountStatus.password === "saving" ? t("profile.actions.saving") : t("account.password.action")}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
