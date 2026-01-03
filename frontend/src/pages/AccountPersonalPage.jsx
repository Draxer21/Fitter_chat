import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import AccountDetailsCard from "../components/AccountDetailsCard";
import ProfileSectionNav from "../components/ProfileSectionNav";
import "../styles/profile.css";

export default function AccountPersonalPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <main className="profile-page py-5">
        <div className="profile-shell">
          <div className="row justify-content-center">
            <div className="col-lg-6">
              <div className="alert alert-warning">
                {t("profile.messages.authRequired")}
                <div className="mt-3">
                  <Link className="btn btn-dark" to="/login">
                    {t("profile.messages.authButton")}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="profile-page py-5">
      <div className="profile-shell">
        <header className="profile-header text-center mb-4">
          <p className="profile-eyebrow">{t("account.page.eyebrow")}</p>
          <h1 className="profile-title">{t("account.page.title")}</h1>
          <p className="profile-subtitle">{t("account.page.subtitle")}</p>
        </header>

        <ProfileSectionNav />

        <div className="profile-content-grid">
          <div className="profile-form-wrapper">
            <AccountDetailsCard />
          </div>
        </div>
      </div>
    </main>
  );
}
