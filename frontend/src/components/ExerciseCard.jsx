import { useState } from "react";
import { useToast } from "../contexts/ToastContext";

/* =========================================================
   ExerciseCard — display a single exercise
   Props:
     name        {string}   Exercise name
     reps        {string}   e.g. "4 series x 12 repeticiones"
     muscle      {string}   Badge label (e.g. "Pecho")
     difficulty  {number}   1-5 filled dots
     imageUrl    {string}   Cover image URL
     description {string}   Optional — enables "expanded" variant
     compact     {boolean}  Compact list variant
   Classes from kimi-components.css
   ========================================================= */

function CheckmarkSVG() {
  return (
    <svg className="checkmark-svg" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12l3 3 5-6" />
    </svg>
  );
}

export default function ExerciseCard({
  name = "Ejercicio",
  reps = "",
  muscle = "",
  difficulty = 3,
  imageUrl = "",
  description = "",
  compact = false,
}) {
  const [completed, setCompleted] = useState(false);
  const { showToast } = useToast();

  const clampedDifficulty = Math.min(5, Math.max(0, Math.round(difficulty)));

  const toggle = () => {
    const next = !completed;
    setCompleted(next);
    if (next) {
      showToast(
        "success",
        "Ejercicio completado",
        `¡Sigue así! ${name} registrado correctamente.`
      );
    }
  };

  const cardClasses = [
    "exercise-card",
    compact ? "compact" : "",
    description && !compact ? "expanded" : "",
    completed ? "completed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cardClasses}>
      {/* Image */}
      {imageUrl && (
        <div className="ex-img-wrap">
          <img src={imageUrl} className="ex-img" alt={name} loading="lazy" />
          {muscle && <span className="ex-badge">{muscle}</span>}
          <div className="ex-img-overlay">
            <span style={{ color: "white", fontWeight: 600 }}>Ver detalles</span>
          </div>
        </div>
      )}

      {/* Body */}
      <div className="ex-body">
        <div className="ex-name">{name}</div>
        {reps && <div className="ex-reps">{reps}</div>}

        {/* Difficulty dots */}
        {!compact && (
          <div className="difficulty" aria-label={`Dificultad: ${clampedDifficulty} de 5`}>
            {Array.from({ length: 5 }, (_, i) => (
              <div
                key={i}
                className={`dot${i < clampedDifficulty ? " active" : ""}`}
              />
            ))}
          </div>
        )}

        {/* Description (expanded variant) */}
        {description && !compact && (
          <div className="ex-desc">{description}</div>
        )}

        {/* Complete button */}
        <button
          type="button"
          className="btn-complete"
          onClick={toggle}
          aria-pressed={completed}
          aria-label={completed ? `${name} completado` : `Marcar ${name} como completado`}
        >
          {completed ? (
            <>
              <CheckmarkSVG />
              Completado
            </>
          ) : (
            <span className="btn-text">Completado</span>
          )}
        </button>
      </div>
    </div>
  );
}
