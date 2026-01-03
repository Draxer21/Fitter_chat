import React, { useState } from "react";
import { useLocale } from "../contexts/LocaleContext";
import { useAuth } from "../contexts/AuthContext";
import { API } from "../services/apijs";
import "../styles/entrenos-unicos.css";

export default function EntrenosUnicos() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [selectedPreview, setSelectedPreview] = useState(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusError, setStatusError] = useState("");
  const [savedPlan, setSavedPlan] = useState(null);

  const handleScrollToPlans = () => {
    const target = document.getElementById("planes-disponibles");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleEnrollPlan = async (plan) => {
    if (!plan) return;
    setStatusMessage("");
    setStatusError("");
    setSavedPlan(null);
    if (!isAuthenticated) {
      setStatusError("Inicia sesión para recibir el plan en tu perfil.");
      return;
    }
    try {
      const details = planDetails[plan.key] || {};
      const response = await API.profile.heroPlans.create({
        plan_key: plan.key,
        title: plan.title,
        payload: {
          plan_key: plan.key,
          title: plan.title,
          duration: plan.duration,
          focus: details.focus || plan.description,
          body_type: plan.bodyType,
          training: details.training,
          diet: details.diet,
          calories: details.calories,
          macros: details.macros,
          meals: details.meals,
          sources: details.sources,
          guidelines: details.guidelines,
        },
        source: "web",
      });
      setSavedPlan(response?.plan || null);
      setStatusMessage("Plan guardado en tu perfil. Puedes verlo en tu cuenta.");
    } catch (err) {
      setStatusError(err?.message || "No pude guardar el plan. Intentalo otra vez.");
    }
  };

  const handleDownload = async (planId) => {
    if (!planId) return;
    setStatusError("");
    try {
      const rawBase = import.meta.env.VITE_API_BASE_URL || "";
      const BASE = rawBase && rawBase !== "/" ? rawBase.replace(/\/+$/, "") : "";
      const resp = await fetch(`${BASE}/profile/hero-plans/${planId}/pdf`, { credentials: "include" });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `entreno_unico_${planId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setStatusError(err?.message || "No pude descargar el plan.");
    }
  };

  const getPlanByIndex = (idx) => plans[(idx + plans.length) % plans.length];
  const handlePrevPlan = () => setCarouselIndex((prev) => (prev - 1 + plans.length) % plans.length);
  const handleNextPlan = () => setCarouselIndex((prev) => (prev + 1) % plans.length);

  const planDetails = {
    flash: {
      focus: "Fuerza e hipertrofia con circuitos metabólicos",
      training: "4-5 sesiones/semana con compuestos, bloques de potencia y core.",
      diet: "Superavit moderado con proteínas magras y carbohidratos complejos.",
      calories: "Ajuste según peso y objetivo.",
      macros: "Proteína 1.6-2.2 g/kg, carbos altos, grasas moderadas.",
      meals: [
        "Avena con claras y fruta",
        "Pollo con arroz integral y verduras",
        "Batido de proteína post-entreno",
      ],
      sources: [],
      guidelines: [
        "Calienta 8-10 min y prioriza técnica.",
        "Progresión semanal de cargas o repeticiones.",
        "Descanso 60-90 s en accesorios y 2-3 min en compuestos.",
      ],
    },
    shazam: {
      focus: "Movilidad, pliometría y acondicionamiento funcional",
      training: "4 sesiones/semana con drills de agilidad, saltos y core reactivo.",
      diet: "Mantenimiento con proteína alta y carbos alrededor del entreno.",
      calories: "Mantenimiento calórico.",
      macros: "Proteína alta, carbos moderados, grasas estables.",
      meals: [
        "Huevos con avena y fruta",
        "Pescado con quinoa y verduras",
        "Yogur griego con frutos secos",
      ],
      sources: [],
      guidelines: [
        "Enfoca calidad de movimiento antes de velocidad.",
        "Incluye movilidad diaria 10-15 min.",
        "Recuperación activa 1-2 días por semana.",
      ],
    },
    mecha: {
      focus: "Resistencia progresiva y trabajo aeróbico estructurado",
      training: "4-5 sesiones/semana con cardio guiado y fuerza base.",
      diet: "Mantenimiento o leve superávit con carbos para energía.",
      calories: "Ajuste según demanda de cardio.",
      macros: "Proteína 1.6-2.0 g/kg, carbos altos, grasas moderadas.",
      meals: [
        "Tostadas integrales con huevos",
        "Carne magra con batata",
        "Snack de frutos secos",
      ],
      sources: [],
      guidelines: [
        "No saltes las sesiones de cardio progresivo.",
        "Prioriza hidratación y electrolitos.",
        "Mantén 7-8 h de sueño para recuperación.",
      ],
    },
    batman_bale: {
      focus: "Fuerza + volumen con base en compuestos",
      training: "Compuestos tipo press banca, sentadilla y peso muerto con trabajo funcional.",
      diet: "Fase de aumento agresivo y luego dieta limpia hipercalórica.",
      calories: "No especificadas; aumento agresivo al inicio.",
      macros: "No especificadas; prioridad a proteína magra y carbos complejos.",
      meals: [
        "Avena con batido de proteína",
        "Salmón con arroz y batata",
        "Pasta integral con proteína magra",
      ],
      sources: [
        "https://www.gq.com.mx/entretenimiento/articulo/christian-bale-rutinas-de-ejercicio-en-su-carrera",
        "https://steelsupplements.com/blogs/steel-blog/christian-bales-batman-workout-routine-and-diet-plan",
        "https://forums.superherohype.com/threads/bales-diet-and-training-for-bb.311673/",
      ],
      guidelines: [
        "Prioriza los compuestos y sube cargas gradualmente.",
        "Agrega 2 bloques de acondicionamiento por semana.",
        "Evita entrenar al fallo en todas las series.",
      ],
    },
    batman_affleck: {
      focus: "Hipertrofia con énfasis en fuerza máxima",
      training: "Cargas altas con volumen estilo culturismo y circuitos de acondicionamiento.",
      diet: "Dieta six-pack, sin lácteos, 6 comidas diarias y control de sodio.",
      calories: "3500-4000 kcal/día",
      macros: "Proteína alta, carbos complejos moderados, grasas saludables.",
      meals: [
        "Claras con avena y banana",
        "Pechuga de pollo con camote",
        "Salmón con brócoli",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/ben-affleck-batman-workout-diet-plan",
      ],
      guidelines: [
        "Entrena 5-6 días con cargas altas.",
        "Controla sodio y evita alcohol.",
        "Incluye circuitos cortos de acondicionamiento.",
      ],
    },
    batman_pattinson: {
      focus: "Fuerza relativa y acondicionamiento funcional",
      training: "Calistenia, cardio y boxeo con trabajo de core.",
      diet: "Mantenimiento o ligero déficit con proteína alta.",
      calories: "~2800 kcal/día",
      macros: "Proteína 200-220 g/día; carbos fibrosos; grasas moderadas.",
      meals: [
        "Avena con huevo cocido",
        "Atún con tortitas de arroz",
        "Filete magro con arroz y vegetales",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/robert-pattinson-batman-workout-diet-plan",
        "https://www.menshealth.com/fitness/a39367846/robert-pattinson-batman-diet-plan-aseel-soueid/",
      ],
      guidelines: [
        "Prioriza movilidad y cardio 3-4 veces por semana.",
        "Busca funcionalidad antes que volumen.",
        "Core diario de 10-15 min.",
      ],
    },
    capitan_america_evans: {
      focus: "Hipertrofia total y fuerza con alto volumen",
      training: "Split torso-pierna con compuestos pesados y trabajo de core.",
      diet: "Superávit moderado-alto con comidas frecuentes.",
      calories: "~4000 kcal/día",
      macros: "Proteína 200-240 g/día; carbos altos; grasas saludables.",
      meals: [
        "Avena con frutas y nueces",
        "Ensalada de pollo con arroz integral",
        "Caseína antes de dormir",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/chris-evans-captain-america-workout-diet-plan",
        "https://www.gq.com.mx/cuidados/fitness/articulos/rutina-de-ejercicio-de-chris-evans/3021",
      ],
      guidelines: [
        "Come cada 2-3 horas en fase de volumen.",
        "No descuides tren inferior.",
        "Suma movimientos gimnásticos para estabilidad.",
      ],
    },
    superman_cavill: {
      focus: "Hipertrofia + fuerza con alto volumen",
      training: "Fases de fuerza máxima y luego circuitos intensos.",
      diet: "Fase de volumen hipercalórica y ajuste a alimentos más magros.",
      calories: "~5000 kcal/día (volumen)",
      macros: "Proteína ~300 g/día; carbos altos; grasas saludables.",
      meals: [
        "5 claras + 2 yemas + filete",
        "Curry de pollo con arroz jazmín",
        "Batido de caseína nocturno",
      ],
      sources: [
        "http://abcnews.go.com/blogs/entertainment/2013/06/henry-cavill-made-enormous-changes-using-man-of-steel-workout",
        "https://manofmany.com/culture/fitness/henry-cavills-superman-diet-workout-plan",
      ],
      guidelines: [
        "Volumen alto con control de grasa.",
        "Cardio ligero en ayunas en fase de definición.",
        "Recuperación estricta y sueño 8 h.",
      ],
    },
    superman_corenswet: {
      focus: "Volumen con sobrecarga progresiva",
      training: "Split empuje-tracción-piernas con progresión semanal.",
      diet: "Volumen limpio con 5 comidas y 2 batidos hipercalóricos.",
      calories: "4500-6000 kcal/día",
      macros: "Proteína ~250 g/día; carbos abundantes; grasas moderadas.",
      meals: [
        "4 huevos + avena con mantequilla de maní",
        "Pollo con arroz",
        "Batido hipercalórico",
      ],
      sources: [
        "https://www.gq.com/story/david-corenswet-superman-legacy-workout-1",
        "https://www.eonline.com/news/1419758/supermans-david-corenswet-details-diet-and-workout-transformation",
        "https://menshealth.com.au/david-corenswet-workout-routine-diet-plan/",
        "https://www.eatingwell.com/david-corenswet-weight-gain-for-superman-11769355",
      ],
      guidelines: [
        "Progresión semanal de cargas o repeticiones.",
        "Prioriza técnica y rango completo.",
        "Recuperación activa 1 día por semana.",
      ],
    },
    wolverine_jackman: {
      focus: "Fuerza + hipertrofia con periodización",
      training: "Básicos pesados con progresión y bloques 4x10-12 a 4x5.",
      diet: "Ayuno 16/8 con ingesta calórica alta en ventana.",
      calories: "~4000 kcal/día (volumen)",
      macros: "230 g proteína / 230 g carbohidratos / 230 g grasas aprox.",
      meals: [
        "Avena con arándanos y 2 huevos",
        "Filete magro + batata + brócoli",
        "Pescado blanco con aguacate",
      ],
      sources: [
        "https://www.businessinsider.com/how-hugh-jackman-got-in-shape-for-logan-2017-3",
        "https://www.businessinsider.com/4000-calorie-diet-hugh-jackman-get-shredded-to-play-wolverine-2020-7",
      ],
      guidelines: [
        "Periodiza cargas cada 3-4 semanas.",
        "Incluye HIIT moderado en definición.",
        "Controla hidratación antes de sesiones exigentes.",
      ],
    },
  };

  const plans = [
    {
      key: "flash",
      title: 'Flash',
      duration: '8 semanas',
      description: 'Enfocado en fuerza e hipertrofia con circuitos metabólicos.',
      img: '/flash.jpg',
      bodyType: 'Atlético y veloz',
      exclusiveNotes: [
        'Incluye complejos de potencia y circuitos metabólicos que solo se habilitan con la inscripción al programa.',
        'En rutinas generales se puede rescatar 1-2 movimientos (ej. contrastes o sprints) pero no el bloque completo.',
        'Pensado para quienes buscan el físico atlético con alto volumen de potencia.'
      ],
    },
    {
      key: "shazam",
      title: 'Shazam',
      duration: '6 semanas',
      description: 'Enfocado en movilidad, plyometrics y acondicionamiento.',
      img: '/shazam.jpg',
      bodyType: 'Ágil y definido',
      exclusiveNotes: [
        'Acceso a módulos de parkour-lite, pliometría avanzada y sesiones de agilidad que no se publican fuera del programa.',
        'Para rutinas estándar solo se permite tomar 1-2 drills como complemento; la progresión completa es exclusiva.',
        'Ideal para trabajar coordinación, core reactivo y definición con enfoque ninja.'
      ],
    },
    {
      key: "mecha",
      title: 'Bane',
      duration: '10 semanas',
      description: 'Enfocado en resistencia y trabajo aeróbico progresivo.',
      img: '/bane.jpg',
      bodyType: 'Robusto y resistente',
      exclusiveNotes: [
        'Integra bloques de strongman, sled drags y hero WODs diseñados solo para quienes se inscriben en el plan.',
        'Las rutinas generales solo pueden reutilizar 1-2 ejercicios pesados como inspiración, no la estructura completa.',
        'Construye la base robusta y resistente que ves en el render del plan.'
      ],
    },
    {
      key: "batman_bale",
      title: "Batman (Christian Bale)",
      duration: "12 semanas",
      description: "Fuerza y volumen con compuestos pesados y acondicionamiento funcional.",
      img: "/batman-bale.jpg",
      bodyType: "Atlético y marcado",
      exclusiveNotes: [
        "Incluye bloques de fuerza tipo 'golden 5' y trabajo funcional inspirado en artes marciales.",
        "Solo se libera el esquema completo con fases de volumen y definición dentro del plan.",
        "Pensado para construir torso amplio con cintura compacta.",
      ],
    },
    {
      key: "batman_affleck",
      title: "Batman (Ben Affleck)",
      duration: "12 semanas",
      description: "Hipertrofia con énfasis en fuerza máxima y densidad muscular.",
      img: "/batman-affleck.jpg",
      bodyType: "Masivo y denso",
      exclusiveNotes: [
        "Programa de cargas altas con bloques de volumen y fuerza para espalda, pecho y hombros.",
        "Incluye sesiones tipo chaos training y circuitos de acondicionamiento pesado.",
        "No se publica fuera del plan el protocolo de volumen completo.",
      ],
    },
    {
      key: "batman_pattinson",
      title: "Batman (Robert Pattinson)",
      duration: "8 semanas",
      description: "Fuerza relativa, movilidad y acondicionamiento funcional.",
      img: "/batman-pattinson.jpg",
      bodyType: "Fibroso y ágil",
      exclusiveNotes: [
        "Integra boxeo, cardio y calistenia con sacos de arena para look definido.",
        "Las rutinas generales solo muestran una parte del circuito funcional.",
        "Ideal si buscas agilidad y resistencia con bajo volumen.",
      ],
    },
    {
      key: "capitan_america_evans",
      title: "Capitán América (Chris Evans)",
      duration: "12 semanas",
      description: "Hipertrofia total y fuerza con alto volumen.",
      img: "/cap-am-chris.jpg",
      bodyType: "Musculoso y equilibrado",
      exclusiveNotes: [
        "Split torso-pierna con sobrecarga progresiva y trabajo de core frecuente.",
        "Incluye fases de potencia y ejercicios gimnásticos avanzados.",
        "Acceso completo solo desde la inscripción al plan.",
      ],
    },
    {
      key: "superman_cavill",
      title: "Superman (Henry Cavill)",
      duration: "12 semanas",
      description: "Volumen alto con fases de fuerza y acondicionamiento intenso.",
      img: "/superman-henry.jpg",
      bodyType: "Masivo y definido",
      exclusiveNotes: [
        "Incluye fases de hipertrofia y circuitos de alta intensidad para definición.",
        "Se libera el plan de volumen y el ajuste final solo en el programa.",
        "Pensado para un físico dominante en pecho y hombros.",
      ],
    },
    {
      key: "superman_corenswet",
      title: "Superman (David Corenswet)",
      duration: "20 semanas",
      description: "Volumen con sobrecarga progresiva y división empuje-tracción-piernas.",
      img: "/superman-david.jpg",
      bodyType: "Muy masivo",
      exclusiveNotes: [
        "Plan de ganancia muscular controlada con progresión semanal.",
        "Incluye ejemplos de comidas hipercalóricas y calendario de fases.",
        "La guía completa solo está disponible dentro del plan.",
      ],
    },
    {
      key: "wolverine_jackman",
      title: "Wolverine (Hugh Jackman)",
      duration: "12 semanas",
      description: "Fuerza máxima con periodización y definición avanzada.",
      img: "/wolverine-hugh.jpg",
      bodyType: "Muy musculoso y definido",
      exclusiveNotes: [
        "Bloques 4x10-12 a 4x5 y trabajo funcional para escenas de combate.",
        "Incluye ventana de nutrición tipo 16/8 para fases específicas.",
        "Rutina completa disponible solo para inscritos.",
      ],
    },
  ];

  return (
    <main className="entrenos-page">
      <header className="entrenos-hero">
        <div className="entrenos-hero-content">
          <p className="entrenos-eyebrow">Colección premium 2025</p>
          <h1 className="entrenos-title">Entrenos Únicos</h1>
          <p className="entrenos-lead">
            Programas de entrenamiento temáticos con duración definida, guías nutricionales y recomendaciones por nivel.
            Diseñados para lograr físicos icónicos con un enfoque serio y progresivo.
          </p>
          <div className="entrenos-hero-actions">
            <button className="btn btn-primary" onClick={handleScrollToPlans}>Explorar planes</button>
            <a className="btn btn-outline-secondary" href="/registro">Inscribirme</a>
          </div>
          <div className="entrenos-hero-meta">
            <div>
              <span>Duración</span>
              <strong>6-20 semanas</strong>
            </div>
            <div>
              <span>Entrenamiento</span>
              <strong>Fuerza + acondicionamiento</strong>
            </div>
            <div>
              <span>Nutrición</span>
              <strong>Macros + ejemplos de comidas</strong>
            </div>
          </div>
        </div>
      </header>

      <section className="entrenos-section">
        <div className="entrenos-section-header">
          <h2>Resumen</h2>
          <p>
            Cada plan incluye una progresión completa, guía alimentaria orientativa y sugerencias de equipamiento para casa o gimnasio.
            Antes de iniciar, revisa la <strong>evaluación médica</strong> para asegurar que puedes entrenar con seguridad.
          </p>
        </div>
      </section>

      <section className="entrenos-section">
        <div className="entrenos-section-header">
          <h2>Acceso exclusivo a estos planes</h2>
          <p>
            Estos estilos se diseñaron para replicar el físico mostrado en la vista previa. Solo puedes acceder a las progresiones completas
            desde esta página o al inscribirte en el programa.
          </p>
        </div>
        <div className="entrenos-exclusive-grid">
          {plans.map((p) => (
            <article className="entrenos-exclusive-card" key={`exclusive-${p.key}`}>
              <header>
                <h3>{p.title}</h3>
                <p>{p.duration} · {p.bodyType}</p>
              </header>
              <ul>
                {(p.exclusiveNotes || []).map((note, idx) => (
                  <li key={`${p.key}-note-${idx}`}>{note}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="entrenos-section" id="planes-disponibles">
        <div className="entrenos-section-header">
          <h2>Planes disponibles</h2>
          <p>Explora los planes en el carrusel y previsualiza el estilo antes de inscribirte.</p>
        </div>
        {(statusMessage || statusError) && (
          <div className="entrenos-alerts">
            {statusMessage && <div className="alert alert-success">{statusMessage}</div>}
            {statusError && <div className="alert alert-danger">{statusError}</div>}
          </div>
        )}
        <div className="entrenos-carousel">
          <button className="entrenos-carousel-btn" onClick={handlePrevPlan} aria-label="Plan anterior">
            ‹
          </button>
          <div className="entrenos-carousel-track">
            {[-1, 0, 1].map((offset) => {
              const plan = getPlanByIndex(carouselIndex + offset);
              const isCenter = offset === 0;
              return (
                <article
                  className={`entreno-card entreno-card--carousel ${isCenter ? "is-center" : ""} ${selectedPreview === plan.key ? "is-selected" : ""}`}
                  key={`${plan.key}-${offset}`}
                  role="button"
                  onClick={() => setSelectedPreview(plan.key)}
                >
                  <div className="entreno-card-image">
                    <img src={plan.img} alt={`${plan.title} preview`} />
                  </div>
                  <div className="entreno-card-body">
                    <div className="entreno-card-meta">
                      <span>{plan.duration}</span>
                      <span>{plan.bodyType}</span>
                    </div>
                    <h3>{plan.title}</h3>
                    <p className="entreno-card-desc">{plan.description}</p>
                  </div>
                  <div className="entreno-card-footer">
                    <button className={`btn ${selectedPreview === plan.key ? "btn-outline-primary" : "btn-primary"}`} onClick={(e) => { e.stopPropagation(); setSelectedPreview(plan.key); }}>
                      {selectedPreview === plan.key ? "Seleccionado" : "Ver vista"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          <button className="entrenos-carousel-btn" onClick={handleNextPlan} aria-label="Plan siguiente">
            ›
          </button>
        </div>

        <div className="entreno-preview">
          <h3>Vista previa seleccionada</h3>
          {!selectedPreview && <p className="text-muted">Haz clic en una tarjeta para ver una vista ampliada del tipo de cuerpo asociado al plan.</p>}
          {selectedPreview && (
            (() => {
              const p = plans.find(pl => pl.key === selectedPreview);
              const details = planDetails[p?.key] || {};
              return (
                <div className="entreno-preview-card">
                  <div className="entreno-preview-image">
                    <img src={p.img} alt={`${p.title} large preview`} />
                  </div>
                  <div className="entreno-preview-body">
                    <h4>{p.title} — {p.duration}</h4>
                    <p>{p.description}</p>
                    <p><strong>Tipo de cuerpo objetivo:</strong> {p.bodyType}</p>
                    <div className="entreno-preview-details">
                      <div>
                        <strong>Entrenamiento:</strong>
                        <p>{details.training || "Consulta la guia completa del plan para el detalle."}</p>
                      </div>
                      <div>
                        <strong>Nutricion:</strong>
                        <p>{details.diet || "Incluye guia de macros y ejemplo de comidas."}</p>
                      </div>
                      {details.calories && <p><strong>Calorias:</strong> {details.calories}</p>}
                      {details.macros && <p><strong>Macros:</strong> {details.macros}</p>}
                      {(details.meals || []).length > 0 && (
                        <div>
                          <strong>Ejemplos de comidas:</strong>
                          <ul>
                            {details.meals.map((meal) => (
                              <li key={`${p.key}-meal-${meal}`}>{meal}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(details.guidelines || []).length > 0 && (
                        <div>
                          <strong>Instrucciones generales:</strong>
                          <ul>
                            {details.guidelines.map((note) => (
                              <li key={`${p.key}-guide-${note}`}>{note}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(details.sources || []).length > 0 && (
                        <div>
                          <strong>Fuentes:</strong>
                          <ul>
                            {details.sources.map((src) => (
                              <li key={`${p.key}-src-${src}`}>{src}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    <p className="text-muted">Selecciona este estilo si te identifica el tipo de cuerpo mostrado y tus objetivos.</p>
                    <div className="entreno-preview-actions">
                      <button className="btn btn-primary" onClick={() => handleEnrollPlan(p)}>Recibir plan</button>
                      {!isAuthenticated && <a className="btn btn-outline-secondary" href="/registro">Registrarme</a>}
                      {savedPlan?.id && savedPlan?.plan_key === p.key && (
                        <button className="btn btn-outline-primary" onClick={() => handleDownload(savedPlan.id)}>Descargar PDF</button>
                      )}
                      <button className="btn btn-outline-secondary" onClick={() => setSelectedPreview(null)}>Cerrar vista</button>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>
      </section>

      <section className="entrenos-section entrenos-info-grid">
        <article>
          <h2>Alimentación (orientativa)</h2>
          <p>
            Cada plan incluye un esquema alimenticio orientativo con macronutrientes objetivo (proteína, carbohidrato, grasa) y ejemplos de
            comidas. No sustituye la consulta con un nutricionista.
          </p>
          <ul>
            <li><strong>Desayuno:</strong> carbohidrato complejo + proteína (ej. avena + claras o queso fresco).</li>
            <li><strong>Almuerzo:</strong> proteína magra + carbohidrato + verduras.</li>
            <li><strong>Cena:</strong> proteína ligera + verduras + grasas saludables.</li>
          </ul>
        </article>
        <article>
          <h2>Equipamiento</h2>
          <div className="entrenos-equip-grid">
            <div>
              <h3>Casa</h3>
              <ul>
                <li>Mancuernas ajustables / juego de mancuernas</li>
                <li>Banda elástica o minibands</li>
                <li>Colchoneta de ejercicio</li>
                <li>Barra para dominadas (opcional)</li>
              </ul>
            </div>
            <div>
              <h3>Gimnasio</h3>
              <ul>
                <li>Multigimnasio o banco con barra y discos</li>
                <li>Máquinas de polea y cables</li>
                <li>Estación de dominadas / TRX</li>
                <li>Equipo para cardio (cinta, bicicleta, remo)</li>
              </ul>
            </div>
          </div>
        </article>
      </section>

      <section className="entrenos-section entrenos-info-grid">
        <article>
          <h2>Evaluación médica</h2>
          <p>Antes de iniciar cualquier Entreno Único, recomendamos realizar una evaluación médica.</p>
          <ul>
            <li>Enfermedad cardiovascular diagnosticada o arritmias no controladas.</li>
            <li>Hipertensión severa no controlada (consultar médico antes de iniciar).</li>
            <li>Embarazo o postparto reciente (consultar profesional de salud).</li>
            <li>Lesiones agudas o dolor articular no evaluado.</li>
            <li>Enfermedades respiratorias graves sin control.</li>
          </ul>
          <p className="text-muted">Si tienes dudas, consulta con tu médico. Estos criterios son orientativos.</p>
        </article>
        <article className="entrenos-cta-card">
          <h2>Cómo acceder</h2>
          <p>Para ver el plan completo, descarga la guía o inscríbete en el programa.</p>
          <div className="entrenos-cta-actions">
            <a className="btn btn-primary" href="/registro">Inscríbete ahora</a>
            <button className="btn btn-outline-secondary" onClick={handleScrollToPlans}>Ver planes</button>
          </div>
        </article>
      </section>
    </main>
  );
}
