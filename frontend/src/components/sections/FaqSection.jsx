import { useState } from "react";

/* =========================================================
   FaqSection — FAQ with category tabs and accordion
   Props:
     defaultCategory {string} — initial active tab (default 'all')
   Only one item open at a time.
   FAQ data is hardcoded from kimi_ui_reference.html
   Classes from kimi-components.css
   ========================================================= */

const CATEGORIES = [
  { key: "all",        label: "Todas" },
  { key: "general",   label: "General" },
  { key: "ia",        label: "IA y Rutinas" },
  { key: "planes",    label: "Planes y Pagos" },
  { key: "privacidad", label: "Privacidad" },
];

const FAQ_ITEMS = [
  {
    cat: "general",
    question: "¿Qué es FITTER y cómo funciona?",
    answer:
      "FITTER es una plataforma de entrenamiento personalizada impulsada por inteligencia artificial. Analiza tu nivel físico, objetivos y restricciones para generar rutinas únicas adaptadas a ti.",
  },
  {
    cat: "general",
    question: "¿Necesito equipo de gimnasio?",
    answer:
      "No necesariamente. La IA puede diseñar rutinas con peso corporal, bandas elásticas o equipo completo de gimnasio según lo que tengas disponible.",
  },
  {
    cat: "ia",
    question: "¿Cómo genera la IA mis rutinas?",
    answer:
      "Nuestro algoritmo analiza tu historial de entrenamiento, progreso, feedback post-rutina y objetivos para crear planes periodizados que maximicen resultados y minimicen riesgo de lesión.",
  },
  {
    cat: "ia",
    question: "¿Puedo modificar una rutina generada por IA?",
    answer:
      "Sí, puedes sustituir ejercicios, ajustar series/repeticiones y modificar descansos. La IA aprenderá de tus preferencias para futuras rutinas.",
  },
  {
    cat: "ia",
    question: "¿Qué pasa si me lesiono o me enfermo?",
    answer:
      "Puedes reportar lesiones o días de descanso forzado en tu perfil. La IA ajustará automáticamente tu plan para mantener el progreso sin comprometer tu recuperación.",
  },
  {
    cat: "planes",
    question: "¿Puedo cambiar de plan en cualquier momento?",
    answer:
      "Sí, puedes hacer upgrade o downgrade en cualquier momento. Los cambios se aplican al siguiente ciclo de facturación.",
  },
  {
    cat: "planes",
    question: "¿Hay prueba gratuita?",
    answer:
      "Ofrecemos 14 días de prueba gratuita del plan Premium. No requiere tarjeta de crédito para empezar.",
  },
  {
    cat: "planes",
    question: "¿Cómo cancelo mi suscripción?",
    answer:
      "Puedes cancelar desde tu panel de configuración en cualquier momento. Seguirás teniendo acceso hasta el final del período pagado.",
  },
  {
    cat: "privacidad",
    question: "¿Mis datos de salud están protegidos?",
    answer:
      "Absolutamente. Cumplimos con HIPAA y GDPR. Tus datos de salud están encriptados y nunca se comparten con terceros sin tu consentimiento explícito.",
  },
  {
    cat: "privacidad",
    question: "¿La IA usa mis datos para entrenar modelos?",
    answer:
      "Solo de forma anónima y agregada. Nunca utilizamos datos personales identificables para entrenar nuestros modelos de IA.",
  },
];

export default function FaqSection({ defaultCategory = "all" }) {
  const [activeCategory, setActiveCategory] = useState(defaultCategory);
  const [openId, setOpenId]                 = useState(null);

  const filtered =
    activeCategory === "all"
      ? FAQ_ITEMS
      : FAQ_ITEMS.filter((f) => f.cat === activeCategory);

  function toggle(idx) {
    setOpenId((prev) => (prev === idx ? null : idx));
  }

  return (
    <section
      className="section-padding"
      style={{ background: "var(--surface)" }}
      aria-labelledby="faq-title"
    >
      <div className="container">
        <div className="section-badge reveal">
          <i className="bi bi-question-circle-fill" aria-hidden="true" />
          Preguntas frecuentes
        </div>

        <h2 id="faq-title" className="section-title reveal">
          ¿Tienes dudas?
        </h2>
        <p className="section-subtitle reveal">
          Respondemos las preguntas más habituales sobre FITTER
        </p>

        {/* Category tabs */}
        <div className="faq-tabs reveal" role="tablist" aria-label="Categorías de preguntas">
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              type="button"
              role="tab"
              aria-selected={activeCategory === c.key}
              className={`faq-tab${activeCategory === c.key ? " active" : ""}`}
              onClick={() => {
                setActiveCategory(c.key);
                setOpenId(null);
              }}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Accordion */}
        <div className="reveal" role="list">
          {filtered.map((item, idx) => {
            const isOpen = openId === idx;
            return (
              <div
                key={idx}
                className={`faq-item${isOpen ? " open" : ""}`}
                role="listitem"
              >
                <div
                  className="faq-question"
                  role="button"
                  tabIndex={0}
                  aria-expanded={isOpen}
                  onClick={() => toggle(idx)}
                  onKeyDown={(e) =>
                    (e.key === "Enter" || e.key === " ") && toggle(idx)
                  }
                >
                  <span>{item.question}</span>
                  <div className="faq-icon" aria-hidden="true">
                    <i className="bi bi-plus-lg" />
                  </div>
                </div>

                <div
                  className="faq-answer"
                  id={`faq-answer-${idx}`}
                  aria-hidden={!isOpen}
                >
                  {item.answer}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
