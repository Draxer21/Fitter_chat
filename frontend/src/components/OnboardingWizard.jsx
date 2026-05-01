import { useEffect, useRef, useState } from "react";

/* =========================================================
   OnboardingWizard — 4-step new-user onboarding flow
   Props:
     onComplete(data) — callback when user finishes
   Also exports: launchConfetti()
   Classes from kimi-components.css
   ========================================================= */

const GOALS = [
  { icon: "bi-droplet-fill",        name: "Perder grasa" },
  { icon: "bi-lightning-charge-fill", name: "Ganar músculo" },
  { icon: "bi-heart-pulse-fill",    name: "Mejorar resistencia" },
  { icon: "bi-shield-check",        name: "Mantenerme" },
];

const LEVELS = [
  { name: "Principiante", desc: "Nunca o casi nunca has entrenado. Empezaremos suave." },
  { name: "Intermedio",   desc: "Entrenas 2-3 veces por semana. Buscamos progresar." },
  { name: "Avanzado",     desc: "Entrenas 4+ veces por semana. Quieres optimizar." },
];

const RESTRICTIONS = ["Rodilla", "Espalda", "Hombro", "Ninguna"];

const TOTAL_STEPS = 4;

/* Exported confetti launcher — can be used independently */
export function launchConfetti() {
  const existing = document.getElementById("fitter-confetti-container");
  const container = existing || document.createElement("div");
  if (!existing) {
    container.id = "fitter-confetti-container";
    container.className = "confetti-container";
    document.body.appendChild(container);
  }
  container.innerHTML = "";

  const colors = [
    "#15803d", "#86efac", "#4ade80", "#22c55e",
    "#166534", "#fbbf24", "#3b82f6",
  ];

  for (let i = 0; i < 60; i++) {
    const piece = document.createElement("div");
    piece.className = "confetti-piece";
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = colors[Math.floor(Math.random() * colors.length)];
    piece.style.width  = `${Math.random() * 10 + 5}px`;
    piece.style.height = `${Math.random() * 10 + 5}px`;
    piece.style.borderRadius = Math.random() > 0.5 ? "50%" : "0";
    piece.style.animationDelay    = `${Math.random() * 2}s`;
    piece.style.animationDuration = `${Math.random() * 2 + 2}s`;
    container.appendChild(piece);
  }

  setTimeout(() => {
    if (container.parentNode) container.innerHTML = "";
  }, 5000);
}

export default function OnboardingWizard({ onComplete }) {
  const [step, setStep]               = useState(1);
  const [goal, setGoal]               = useState("");
  const [level, setLevel]             = useState("");
  const [restrictions, setRestrictions] = useState([]);
  const [freq, setFreq]               = useState(3);
  const containerRef                  = useRef(null);

  const progressWidth = `${(step / TOTAL_STEPS) * 100}%`;

  function toggleRestriction(name) {
    setRestrictions((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name]
    );
  }

  function next() {
    if (step < TOTAL_STEPS) {
      setStep((s) => s + 1);
    } else {
      launchConfetti();
      onComplete?.({ goal, level, restrictions, freq });
    }
  }

  function prev() {
    if (step > 1) setStep((s) => s - 1);
  }

  const isNextDisabled =
    (step === 1 && !goal) ||
    (step === 2 && !level);

  // Scroll wizard into view when mounted
  useEffect(() => {
    containerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  return (
    <div className="wizard-container" ref={containerRef}>
      {/* Progress bar */}
      <div className="wizard-progress">
        <div
          className="wizard-progress-bar"
          style={{ width: progressWidth }}
          role="progressbar"
          aria-valuenow={step}
          aria-valuemin={1}
          aria-valuemax={TOTAL_STEPS}
        />
      </div>

      {/* Steps */}
      <div className="wizard-steps">
        {/* Step 1 — Goal */}
        <div className={`wizard-step${step === 1 ? " active" : step > 1 ? " prev" : ""}`}>
          <h4 className="fw-bold mb-1">¿Cuál es tu objetivo principal?</h4>
          <p className="mb-4" style={{ color: "var(--text-3)", fontSize: "0.9rem" }}>
            Selecciona el que mejor se adapte a ti
          </p>
          <div className="row g-3">
            {GOALS.map((g) => (
              <div key={g.name} className="col-6">
                <div
                  className={`goal-card${goal === g.name ? " selected" : ""}`}
                  role="button"
                  tabIndex={0}
                  onClick={() => setGoal(g.name)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setGoal(g.name)}
                  aria-pressed={goal === g.name}
                >
                  <div className="goal-icon">
                    <i className={`bi ${g.icon}`} aria-hidden="true" />
                  </div>
                  <div className="goal-name">{g.name}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 2 — Level */}
        <div className={`wizard-step${step === 2 ? " active" : step > 2 ? " prev" : ""}`}>
          <h4 className="fw-bold mb-1">¿Cuál es tu nivel de experiencia?</h4>
          <p className="mb-4" style={{ color: "var(--text-3)", fontSize: "0.9rem" }}>
            Esto nos ayuda a calibrar la intensidad
          </p>
          <div className="row g-3">
            {LEVELS.map((l) => (
              <div key={l.name} className="col-12">
                <div
                  className={`level-card${level === l.name ? " selected" : ""}`}
                  role="button"
                  tabIndex={0}
                  onClick={() => setLevel(l.name)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setLevel(l.name)}
                  aria-pressed={level === l.name}
                >
                  <div className="level-name">{l.name}</div>
                  <div className="level-desc">{l.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 3 — Restrictions + frequency */}
        <div className={`wizard-step${step === 3 ? " active" : step > 3 ? " prev" : ""}`}>
          <h4 className="fw-bold mb-1">Restricciones y frecuencia</h4>
          <p className="mb-3" style={{ color: "var(--text-3)", fontSize: "0.9rem" }}>
            ¿Tienes alguna limitación física?
          </p>

          <div className="mb-4">
            {RESTRICTIONS.map((r) => (
              <div key={r} className="form-check mb-2">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id={`chk-${r}`}
                  checked={restrictions.includes(r)}
                  onChange={() => toggleRestriction(r)}
                  style={{ borderColor: "var(--border-2)" }}
                />
                <label
                  className="form-check-label"
                  htmlFor={`chk-${r}`}
                  style={{ color: "var(--text-2)" }}
                >
                  {r}
                </label>
              </div>
            ))}
          </div>

          <p className="mb-2" style={{ color: "var(--text-3)", fontSize: "0.9rem" }}>
            ¿Cuántos días a la semana puedes entrenar?
          </p>

          <input
            type="range"
            className="wizard-slider"
            min={1}
            max={7}
            value={freq}
            onChange={(e) => setFreq(Number(e.target.value))}
            aria-label={`Frecuencia semanal: ${freq} días`}
          />

          <div className="d-flex justify-content-between" style={{ fontSize: "0.8rem", color: "var(--text-3)" }}>
            <span>1 día</span>
            <span style={{ fontWeight: 700, color: "var(--brand-500)" }}>{freq} días</span>
            <span>7 días</span>
          </div>
        </div>

        {/* Step 4 — Summary */}
        <div className={`wizard-step${step === 4 ? " active" : ""}`}>
          <div className="text-center py-4">
            <div
              style={{
                width: 80, height: 80, borderRadius: "50%",
                background: "linear-gradient(135deg, var(--brand-500), var(--brand-300))",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "2.5rem", color: "white", margin: "0 auto 1.5rem",
              }}
            >
              <i className="bi bi-check-lg" aria-hidden="true" />
            </div>

            <h4 className="fw-bold mb-2">¡Todo listo!</h4>
            <p className="mb-4" style={{ color: "var(--text-3)", fontSize: "0.95rem" }}>
              Hemos preparado tu plan personalizado basado en tus respuestas.
            </p>

            <div
              style={{
                background: "var(--bg)", border: "1px solid var(--border)",
                borderRadius: 12, padding: "1.25rem", textAlign: "left", marginBottom: "1.5rem",
              }}
            >
              <div className="d-flex justify-content-between mb-2">
                <span style={{ color: "var(--text-3)" }}>Objetivo:</span>
                <span className="fw-bold">{goal || "—"}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span style={{ color: "var(--text-3)" }}>Nivel:</span>
                <span className="fw-bold">{level || "—"}</span>
              </div>
              <div className="d-flex justify-content-between">
                <span style={{ color: "var(--text-3)" }}>Frecuencia:</span>
                <span className="fw-bold">{freq} días/semana</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="wizard-nav">
        <button
          type="button"
          className="btn-prev"
          onClick={prev}
          style={{ visibility: step === 1 ? "hidden" : "visible" }}
        >
          Anterior
        </button>

        <button
          type="button"
          className="btn-next"
          onClick={next}
          disabled={isNextDisabled}
          style={isNextDisabled ? { opacity: 0.5, cursor: "not-allowed" } : {}}
        >
          {step === TOTAL_STEPS ? "Empezar con FITTER" : "Siguiente"}
          {step === TOTAL_STEPS && (
            <i className="bi bi-arrow-right ms-2" aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}
