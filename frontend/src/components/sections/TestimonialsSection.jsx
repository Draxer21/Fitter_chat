/* =========================================================
   TestimonialsSection — 3 glassmorphism testimonial cards
   Data hardcoded from kimi_ui_reference.html (section 10)
   Classes from kimi-components.css:
     .testimonials-bg, .testimonial-card, .testi-avatar,
     .testi-stars, .testi-quote, .testi-name, .testi-role
   ========================================================= */

const TESTIMONIALS = [
  {
    initials: "MR",
    gradient: "linear-gradient(135deg, #15803d, #86efac)",
    stars: 5,
    quote:
      '"En 3 meses bajé 8 kg sin sentir que estaba haciendo dieta. La IA se adapta perfectamente a mis horarios caóticos."',
    name: "María Rodríguez",
    role: "Socio Premium — Santiago",
    delay: 0,
  },
  {
    initials: "CG",
    gradient: "linear-gradient(135deg, #166534, #4ade80)",
    stars: 5,
    quote:
      '"Como entrenador profesional, uso FITTER para complementar las sesiones con mis clientes. La calidad de las rutinas es excepcional."',
    name: "Carlos Gómez",
    role: "Entrenador Certificado — Viña del Mar",
    delay: 0.15,
  },
  {
    initials: "AL",
    gradient: "linear-gradient(135deg, #14532d, #22c55e)",
    stars: 4.5,
    quote:
      '"Recuperé la movilidad de mi rodilla gracias a las rutinas adaptativas. Nunca pensé que una app pudiera ser tan personalizada."',
    name: "Ana López",
    role: "Usuario desde 2025 — Concepción",
    delay: 0.3,
  },
];

function Stars({ count }) {
  const full = Math.floor(count);
  const half = count % 1 >= 0.5;
  return (
    <div className="testi-stars" aria-label={`${count} de 5 estrellas`}>
      {Array.from({ length: full }, (_, i) => (
        <i key={i} className="bi bi-star-fill" aria-hidden="true" />
      ))}
      {half && <i className="bi bi-star-half" aria-hidden="true" />}
    </div>
  );
}

export default function TestimonialsSection() {
  return (
    <section
      className="section-padding testimonials-bg"
      aria-labelledby="testimonials-title"
    >
      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        <div className="section-badge reveal">
          <i className="bi bi-chat-quote-fill" aria-hidden="true" />
          Testimonios reales
        </div>

        <h2 id="testimonials-title" className="section-title reveal">
          Lo que dicen nuestros usuarios
        </h2>
        <p className="section-subtitle reveal">
          Miles de personas ya transformaron su rutina con FITTER
        </p>

        <div className="row g-4">
          {TESTIMONIALS.map((t) => (
            <div
              key={t.initials}
              className="col-md-4 reveal"
              style={{ transitionDelay: `${t.delay}s` }}
            >
              <article className="testimonial-card" aria-label={`Testimonio de ${t.name}`}>
                {/* Avatar */}
                <div
                  className="testi-avatar"
                  style={{ background: t.gradient }}
                  aria-hidden="true"
                >
                  {t.initials}
                </div>

                {/* Stars */}
                <Stars count={t.stars} />

                {/* Quote */}
                <p className="testi-quote">{t.quote}</p>

                {/* Author */}
                <div className="testi-name">{t.name}</div>
                <div className="testi-role">{t.role}</div>
              </article>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
