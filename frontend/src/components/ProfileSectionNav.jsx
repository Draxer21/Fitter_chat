import { NavLink } from "react-router-dom";
import { useLocale } from "../contexts/LocaleContext";

export default function ProfileSectionNav() {
  const { t } = useLocale();

  return (
    <nav className="profile-section-tabs" aria-label={t("profile.nav.label")}>
      <NavLink
        to="/cuenta/datos-personales"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("profile.nav.personal")}
      </NavLink>
      <NavLink
        to="/cuenta/perfil"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("profile.nav.chatbot")}
      </NavLink>
      <NavLink
        to="/cuenta/seguridad"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("nav.account.security")}
      </NavLink>
      <NavLink
        to="/cuenta/entrenos-unicos"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("profile.nav.hero_plans")}
      </NavLink>
      <NavLink
        to="/cuenta/rutinas"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("profile.nav.routines")}
      </NavLink>
      <NavLink
        to="/cuenta/dietas"
        className={({ isActive }) => `profile-section-tab ${isActive ? "is-active" : ""}`}
      >
        {t("profile.nav.diets")}
      </NavLink>
    </nav>
  );
}
