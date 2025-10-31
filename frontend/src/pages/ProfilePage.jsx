import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const initialFormState = {
  weight_kg: "",
  height_cm: "",
  age_years: "",
  sex: "",
  activity_level: "",
  primary_goal: "",
  allergies: "",
  medical_conditions: "",
  notes: "",
};

const sexOptions = [
  { value: "", label: "Seleccionar" },
  { value: "female", label: "Femenino" },
  { value: "male", label: "Masculino" },
  { value: "other", label: "Otro" },
];

const activityOptions = [
  "sedentario",
  "ligero",
  "moderado",
  "intenso",
  "atleta",
];

const goalOptions = [
  "perder_grasa",
  "mantener",
  "ganar_masa",
  "rendimiento",
];

function normalizeProfile(profile) {
  if (!profile) return { ...initialFormState };
  return {
    weight_kg: profile.weight_kg ?? "",
    height_cm: profile.height_cm ?? "",
    age_years: profile.age_years ?? "",
    sex: profile.sex ?? "",
    activity_level: profile.activity_level ?? "",
    primary_goal: profile.primary_goal ?? "",
    allergies: profile.allergies ?? "",
    medical_conditions: profile.medical_conditions ?? "",
    notes: profile.notes ?? "",
  };
}

export default function ProfilePage() {
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
      setMessage("Perfil actualizado correctamente.");
    } catch (err) {
      setError(err?.message || "No pudimos guardar tus datos.");
    } finally {
      setStatus("idle");
    }
  };

  if (!isAuthenticated) {
    return (
      <main className="container py-5">
        <div className="row justify-content-center">
          <div className="col-lg-6">
            <div className="alert alert-warning">
              Necesitas iniciar sesión para editar tu perfil.
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
          <h1 className="mb-4">Mi información</h1>
          <p className="text-muted">
            Comparte tus datos básicos para personalizar mejor tus rutinas, recomendaciones y planes de alimentación.
          </p>

          {message && <div className="alert alert-success">{message}</div>}
          {error && <div className="alert alert-danger">{error}</div>}
          {profileState.error && !error && (
            <div className="alert alert-danger">{profileState.error.message || "Error al cargar el perfil."}</div>
          )}

          <form className="card shadow-sm" onSubmit={handleSubmit}>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-4">
                  <label htmlFor="weight_kg" className="form-label">Peso (kg)</label>
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
                  <label htmlFor="height_cm" className="form-label">Altura (cm)</label>
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
                  <label htmlFor="age_years" className="form-label">Edad</label>
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
                  <label htmlFor="sex" className="form-label">Sexo</label>
                  <select id="sex" name="sex" className="form-select" value={form.sex} onChange={handleChange}>
                    {sexOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="activity_level" className="form-label">Nivel de actividad</label>
                  <select id="activity_level" name="activity_level" className="form-select" value={form.activity_level} onChange={handleChange}>
                    <option value="">Seleccionar</option>
                    {activityOptions.map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label htmlFor="primary_goal" className="form-label">Objetivo principal</label>
                  <select id="primary_goal" name="primary_goal" className="form-select" value={form.primary_goal} onChange={handleChange}>
                    <option value="">Seleccionar</option>
                    {goalOptions.map((value) => (
                      <option key={value} value={value}>
                        {value.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-3">
                <label htmlFor="allergies" className="form-label">Alergias</label>
                <textarea
                  id="allergies"
                  name="allergies"
                  rows={2}
                  className="form-control"
                  value={form.allergies}
                  onChange={handleChange}
                  placeholder="Ej. lactosa, frutos secos"
                />
              </div>

              <div className="mt-3">
                <label htmlFor="medical_conditions" className="form-label">Padecimientos</label>
                <textarea
                  id="medical_conditions"
                  name="medical_conditions"
                  rows={2}
                  className="form-control"
                  value={form.medical_conditions}
                  onChange={handleChange}
                  placeholder="Indica enfermedades, lesiones o condiciones médicas relevantes"
                />
              </div>

              <div className="mt-3">
                <label htmlFor="notes" className="form-label">Notas adicionales</label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  className="form-control"
                  value={form.notes}
                  onChange={handleChange}
                  placeholder="Objetivos específicos, limitaciones u otros comentarios"
                />
              </div>

              {bmi && (
                <div className="alert alert-info mt-3 mb-0">
                  Tu IMC estimado es <strong>{bmi}</strong>. Lo usamos solo como referencia rápida.
                </div>
              )}
            </div>

            <div className="card-footer d-flex justify-content-between align-items-center">
              <div>
                <small className="text-muted">
                  Los cambios impactarán en tus recomendaciones de rutina y dieta.
                </small>
              </div>
              <button type="submit" className="btn btn-dark" disabled={status === "saving" || profileState.loading}>
                {status === "saving" || profileState.loading ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
