import { useEffect, useRef, useState } from "react";

/* =========================================================
   HowItWorks — "Cómo Funciona" homepage section
   - 3-step timeline: horizontal (desktop) / vertical (mobile)
   - Animated fill line via IntersectionObserver
   - Step 2 shows chat-dots typing animation
   - Uses .reveal for scroll-reveal (kimi-animations.css)
   Classes from kimi-components.css
   ========================================================= */

const STEPS = [
  {
    number: 1,
    icon: "bi-person-circle",
    title: "Crea tu perfil",
    desc: "Regístrate y cuéntanos tu objetivo, nivel de experiencia y disponibilidad.",
    chatDots: false,
  },
  {
    number: 2,
    icon: "bi-chat-dots",
    title: "Habla con la IA",
    desc: "Conversa con nuestro entrenador virtual para ajustar y personalizar cada detalle.",
    chatDots: true,
  },
  {
    number: 3,
    icon: "bi-activity",
    title: "Entrena y mejora",
    desc: "Sigue tus rutinas, registra tu progreso y deja que la IA optimice cada semana.",
    chatDots: false,
  },
];

export default function HowItWorks() {
  const sectionRef  = useRef(null);
  const [active, setActive] = useState(false);

  /* Animate the timeline fill when section enters viewport */
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setActive(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.25 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      className="section-padding"
      aria-labelledby="how-it-works-title"
      ref={sectionRef}
    >
      <div className="container">
        <div className="section-badge reveal">
          <i className="bi bi-diagram-3-fill" aria-hidden="true" />
          Proceso simple
        </div>

        <h2 id="how-it-works-title" className="section-title reveal">
          Cómo Funciona
        </h2>
        <p className="section-subtitle reveal">
          En tres pasos sencillos tu entrenador de IA estará listo para ti
        </p>

        <div className={`how-it-works reveal${active ? " visible" : ""}`}>
          {/* Horizontal connector line (desktop) */}
          <div className="timeline-line" aria-hidden="true">
            <div className={`timeline-line-fill${active ? " active" : ""}`} />
          </div>

          <div className="row g-4 position-relative">
            {STEPS.map((s) => (
              <div
                key={s.number}
                className={`col-md-4 timeline-step${active ? " active" : ""}`}
              >
                <div className="step-number" aria-hidden="true">
                  {s.number}
                </div>

                <div className="step-content">
                  <div className="step-icon" aria-hidden="true">
                    <i className={`bi ${s.icon}`} />
                  </div>

                  {/* Typing dots for step 2 */}
                  {s.chatDots && (
                    <div className="chat-dots mb-2" aria-hidden="true">
                      <span /><span /><span />
                    </div>
                  )}

                  <div className="step-title">{s.title}</div>
                  <div className="step-desc">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
