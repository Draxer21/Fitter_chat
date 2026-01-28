import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import "../styles/profile.css";

const initialFormState = {
  weight_kg: "",
  height_cm: "",
  age_years: "",
  sex: "",
  activity_level: "",
  experience_level: "",
  primary_goal: "",
  somatotipo: "no_se",
  musculo_preferido: "",
  allergies: "",
  medical_conditions: "",
  notes: "",
};

const sexOptions = [
  { value: "", labelKey: "profile.sex.select" },
  { value: "female", labelKey: "profile.sex.female" },
  { value: "male", labelKey: "profile.sex.male" },
  { value: "other", labelKey: "profile.sex.other" },
];

const activityOptions = [
  { value: "sedentario", labelKey: "profile.activity.sedentario" },
  { value: "ligero", labelKey: "profile.activity.ligero" },
  { value: "moderado", labelKey: "profile.activity.moderado" },
  { value: "intenso", labelKey: "profile.activity.intenso" },
  { value: "atleta", labelKey: "profile.activity.atleta" },
];

const experienceOptions = [
  { value: "principiante", labelKey: "profile.experience.beginner" },
  { value: "intermedio", labelKey: "profile.experience.intermediate" },
  { value: "avanzado", labelKey: "profile.experience.advanced" },
];

const goalOptions = [
  { value: "perder_grasa", labelKey: "profile.goal.perder_grasa" },
  { value: "mantener", labelKey: "profile.goal.mantener" },
  { value: "ganar_masa", labelKey: "profile.goal.ganar_masa" },
  { value: "rendimiento", labelKey: "profile.goal.rendimiento" },
];

const somatotypeOptions = [
  { value: "no_se", labelKey: "profile.somatotype.unknown" },
  { value: "ectomorfo", labelKey: "profile.somatotype.ectomorfo" },
  { value: "mesomorfo", labelKey: "profile.somatotype.mesomorfo" },
  { value: "endomorfo", labelKey: "profile.somatotype.endomorfo" },
];

const muscleOptions = [
  { value: "", labelKey: "profile.muscle.select" },
  { value: "pecho", labelKey: "profile.muscle.chest" },
  { value: "espalda", labelKey: "profile.muscle.back" },
  { value: "piernas", labelKey: "profile.muscle.legs" },
  { value: "hombros", labelKey: "profile.muscle.shoulders" },
  { value: "brazos", labelKey: "profile.muscle.arms" },
  { value: "core", labelKey: "profile.muscle.core" },
  { value: "fullbody", labelKey: "profile.muscle.fullbody" },
  { value: "cardio", labelKey: "profile.muscle.cardio" },
];

const BMI_CATEGORIES = [
  { id: "underweight", min: 0, max: 18.5, labelKey: "profile.bmi.category.underweight", rangeKey: "profile.bmi.range.underweight" },
  { id: "healthy", min: 18.5, max: 25, labelKey: "profile.bmi.category.healthy", rangeKey: "profile.bmi.range.healthy" },
  { id: "overweight", min: 25, max: 30, labelKey: "profile.bmi.category.overweight", rangeKey: "profile.bmi.range.overweight" },
  { id: "obesity", min: 30, max: Number.POSITIVE_INFINITY, labelKey: "profile.bmi.category.obesity", rangeKey: "profile.bmi.range.obesity" },
];

function normalizeProfile(profile) {
  if (!profile) return { ...initialFormState };
  return {
    weight_kg: profile.weight_kg ?? "",
    height_cm: profile.height_cm ?? "",
    age_years: profile.age_years ?? "",
    sex: profile.sex ?? "",
    activity_level: profile.activity_level ?? "",
    experience_level: profile.experience_level ?? "",
    primary_goal: profile.primary_goal ?? "",
    somatotipo: profile.somatotipo ?? "no_se",
    musculo_preferido: profile.musculo_preferido ?? "",
    allergies: profile.allergies ?? "",
    medical_conditions: profile.medical_conditions ?? "",
    notes: profile.notes ?? "",
  };
}

export default function ProfilePage() {
  const { t } = useLocale();
  const { isAuthenticated, profile: profileData, profileState, loadProfile, updateProfile } = useAuth();
  const [form, setForm] = useState(() => normalizeProfile(profileData));
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      loadProfile().catch(() => {});
    }
  }, [isAuthenticated, loadProfile]);

  useEffect(() => {
    setForm(normalizeProfile(profileData));
  }, [profileData]);

  const bmi = useMemo(() => {
    const weight = parseFloat(form.weight_kg);
    const height = parseFloat(form.height_cm);
    if (!weight || !height) return null;
    if (height <= 0) return null;
    const meters = height / 100;
    const value = weight / (meters * meters);
    if (!Number.isFinite(value)) return null;
    return Math.round(value * 100) / 100;
  }, [form.weight_kg, form.height_cm]);

  const bmiCategory = useMemo(() => {
    if (!bmi) return null;
    return BMI_CATEGORIES.find((category) => bmi >= category.min && bmi < category.max) ?? null;
  }, [bmi]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isAuthenticated) {
      setError("Inicia sesión para actualizar tu perfil.");
      return;
    }
    setStatus("saving");
    setMessage("");
    setError("");
    try {
      const payload = {};
      Object.entries(form).forEach(([key, value]) => {
        payload[key] = value === "" ? null : value;
      });
      await updateProfile(payload);
      setMessage(t("profile.alerts.success"));
    } catch (err) {
      setError(err?.message || t("profile.alerts.error"));
    } finally {
      setStatus("idle");
    }
  };

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
          <p className="profile-eyebrow">{t("profile.highlight.eyebrow")}</p>
          <h1 className="profile-title">{t("profile.title")}</h1>
          <p className="profile-subtitle">{t("profile.subtitle")}</p>
        </header>

        <div className="profile-highlight shadow-sm mb-4">
          <div>
            <h2 className="profile-highlight-title">{t("profile.highlight.title")}</h2>
            <p className="mb-0">{t("profile.highlight.subtitle")}</p>
          </div>
          <div className="profile-highlight-icon" aria-hidden="true">
            <span className="bi bi-activity" />
          </div>
        </div>

        <ProfileSectionNav />

        <div className="profile-content-grid">
          {message && <div className="alert alert-success">{message}</div>}
          {error && <div className="alert alert-danger">{error}</div>}
          {profileState.error && !error && (
            <div className="alert alert-danger">{profileState.error.message || t("profile.alerts.loadError")}</div>
          )}

          <form className="profile-form card shadow-sm border-0" onSubmit={handleSubmit}>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-4">
                  <label htmlFor="weight_kg" className="form-label">{t("profile.fields.weight")}</label>
                  <input
                    id="weight_kg"
                    name="weight_kg"
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={form.weight_kg}
                    onChange={handleChange}
                    min="0"
                  />
                </div>
                <div className="col-md-4">
                  <label htmlFor="height_cm" className="form-label">{t("profile.fields.height")}</label>
                  <input
                    id="height_cm"
                    name="height_cm"
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={form.height_cm}
                    onChange={handleChange}
                    min="0"
                  />
                </div>
                <div className="col-md-4">
                  <label htmlFor="age_years" className="form-label">{t("profile.fields.age")}</label>
                  <input
                    id="age_years"
                    name="age_years"
                    type="number"
                    className="form-control"
                    value={form.age_years}
                    onChange={handleChange}
                    min="0"
                    max="120"
                  />
                </div>
              </div>

              <div className="row g-3 mt-1">
                <div className="col-md-4">
                  <label htmlFor="sex" className="form-label">{t("profile.fields.sex")}</label>
                  <select id="sex" name="sex" className="form-select" value={form.sex} onChange={handleChange}>
                    {sexOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="activity_level" className="form-label">{t("profile.fields.activity")}</label>
                  <select id="activity_level" name="activity_level" className="form-select" value={form.activity_level} onChange={handleChange}>
                    <option value="">{t("profile.activity.select")}</option>
                    {activityOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="experience_level" className="form-label">{t("profile.fields.experience")}</label>
                  <select
                    id="experience_level"
                    name="experience_level"
                    className="form-select"
                    value={form.experience_level}
                    onChange={handleChange}
                  >
                    <option value="">{t("profile.experience.select")}</option>
                    {experienceOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="primary_goal" className="form-label">{t("profile.fields.goal")}</label>
                  <select id="primary_goal" name="primary_goal" className="form-select" value={form.primary_goal} onChange={handleChange}>
                    <option value="">{t("profile.goal.select")}</option>
                    {goalOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="somatotipo" className="form-label">{t("profile.fields.somatotype")}</label>
                  <select
                    id="somatotipo"
                    name="somatotipo"
                    className="form-select"
                    value={form.somatotipo}
                    onChange={handleChange}
                  >
                    {somatotypeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                  <small className="text-muted">{t("profile.somatotype.helper")}</small>
                </div>
              </div>

              <div className="row g-3 mt-1">
                <div className="col-md-6">
                  <label htmlFor="musculo_preferido" className="form-label">{t("profile.fields.preferredMuscle")}</label>
                  <select
                    id="musculo_preferido"
                    name="musculo_preferido"
                    className="form-select"
                    value={form.musculo_preferido}
                    onChange={handleChange}
                  >
                    {muscleOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-3">
                <label htmlFor="allergies" className="form-label">{t("profile.fields.allergies")}</label>
                <textarea
                  id="allergies"
                  name="allergies"
                  rows={2}
                  className="form-control"
                  value={form.allergies}
                  onChange={handleChange}
                  placeholder={t("profile.placeholders.allergies")}
                />
              </div>

              <div className="mt-3">
                <label htmlFor="medical_conditions" className="form-label">{t("profile.fields.medical")}</label>
                <textarea
                  id="medical_conditions"
                  name="medical_conditions"
                  rows={2}
                  className="form-control"
                  value={form.medical_conditions}
                  onChange={handleChange}
                  placeholder={t("profile.placeholders.medical")}
                />
              </div>

              <div className="mt-3">
                <label htmlFor="notes" className="form-label">{t("profile.fields.notes")}</label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  className="form-control"
                  value={form.notes}
                  onChange={handleChange}
                  placeholder={t("profile.placeholders.notes")}
                />
              </div>
            </div>

            <div className="card-footer d-flex justify-content-between align-items-center">
              <div>
                <small className="text-muted">
                  {t("profile.helper.notice")}
                </small>
              </div>
              <button type="submit" className="btn btn-dark" disabled={status === "saving" || profileState.loading}>
                {status === "saving" || profileState.loading ? t("profile.actions.saving") : t("profile.actions.save")}
              </button>
            </div>
          </form>
          {bmi && (
            <aside className="profile-aside">
              <div className="profile-bmi card border-0 shadow-sm">
                <div className="card-body d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-2">
                  <div>
                    <p className="mb-1 text-muted text-uppercase small">{t("profile.stats.bmiLabel")}</p>
                    <p className="display-6 fw-bold mb-2">{bmi}</p>
                    {bmiCategory && (
                      <span className="profile-bmi-badge badge text-uppercase fw-semibold">
                        {t(bmiCategory.labelKey)}
                      </span>
                    )}
                  </div>
                  <p className="mb-0 text-muted">{t("profile.stats.bmiNote")}</p>
                </div>
                <div className="profile-bmi-table card border-0 mt-3">
                  <div className="card-body">
                    <div className="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center">
                      <div>
                        <h3 className="profile-bmi-table-title mb-1">{t("profile.bmi.table.title")}</h3>
                        <p className="profile-bmi-table-subtitle mb-3 mb-md-0">{t("profile.bmi.table.subtitle")}</p>
                      </div>
                    </div>
                    <div className="table-responsive">
                      <table className="table align-middle mb-0 profile-bmi-table-grid">
                        <thead>
                          <tr>
                            <th scope="col">{t("profile.bmi.table.status")}</th>
                            <th scope="col">{t("profile.bmi.table.range")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {BMI_CATEGORIES.map((category) => {
                            const isActive = bmiCategory?.id === category.id;
                            return (
                              <tr key={category.id} className={isActive ? "profile-bmi-row is-active" : "profile-bmi-row"}>
                                <td>
                                  <span className="fw-semibold">{t(category.labelKey)}</span>
                                </td>
                                <td>{t(category.rangeKey)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          )}
        </div>
      </div>
    </main>
  );
}
