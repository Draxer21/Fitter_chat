import { Link, useParams, useNavigate } from "react-router-dom";
import { useLocale } from "../contexts/LocaleContext";
import "../styles/entreno-detalle.css";
import React, { useState } from "react";

const PLAN_CONTENT = {
  superman_corenswet: {
    title: "Superman (David Corenswet)",
    duration: "12-16 semanas",
    subtitle: "Rutina 'Superman en Casa' (Solo Mancuernas)",
    overview:
      "Corenswet se enfocó en el 'look de superhéroe': hombros anchos y cintura estrecha (forma de V). En esta rutina solo tienes mancuernas, por lo cual usaremos frecuencia 2 (entrenar cada músculo 2 veces por semana) para maximizar resultados. Cada sesión dura entre 60-75 minutos, incluyendo 10 min de calentamiento y 5-10 min de estiramientos. La dieta es un superávit calórico con alimentos económicos y ricos en proteína.",
    routine: [
      {
        title: "Días 1 y 4: Torso Superior",
        items: [
          "Press de pecho (suelo): 4 x 10-12 reps.",
          "Remo a una mano: 4 x 12 reps por lado.",
          "Press militar de pie: 3 x 10 reps.",
          "Vuelos laterales: 3 x 15-20 reps.",
          "Flexiones (Push-ups): 3 al fallo técnico.",
        ],
      },
      {
        title: "Días 2 y 5: Piernas y Core",
        items: [
          "Sentadilla Goblet: 4 x 12 reps.",
          "Peso muerto rumano: 4 x 10-12 reps.",
          "Zancadas (Lunges): 3 x 10 reps por pierna.",
          "Plancha abdominal: 3 x 45-60 seg.",
        ],
      },
      {
        title: "Días 3 y 6: Brazos y Puntos Débiles",
        items: [
          "Curl de bíceps: 3 x 12 reps.",
          "Copa de tríceps: 3 x 12 reps.",
          "Encogimientos de hombros: 3 x 15 reps.",
        ],
      },
    ],
    diet: {
      title: 'El Plan de Comidas: "Combustible de Acero"',
      overview:
        "Buscaremos un balance de macronutrientes aproximado de 30% Proteína, 50% Carbohidratos y 20% Grasas.",
      shopping: [
        "Huevos: Bandejas de 30.",
        "Legumbres: Lentejas/Garbanzos.",
        "Arroz y Fideos: Bolsas de 5kg.",
        "Avena: Granel o bolsas grandes.",
        "Pollo: Cuartos traseros.",
        "Jurel en tarro: El rey del ahorro.",
      ],
      nutritionalGuide: [
        { momento: "Pre-Entreno (1 hr antes)", objetivo: "Energía", accion: "Carbohidratos simples." },
        { momento: "Post-Entreno (máx 2 hrs)", objetivo: "Reparación", accion: "Proteína fuerte." },
        { momento: "Días de Descanso", objetivo: "Mantenimiento", accion: "Bajar carbos, mantener proteína." },
      ],
      dailyMenu: [
        "Comida 1: Avena con 2 claras de huevo, canela y fruta.",
        "Comida 2: 1.5 a 2 tazas de arroz con 150g de Jurel y ensalada.",
        "Snack: Pan con 2 huevos duros o pasta de jurel.",
        "Comida 3: 1 cuarto trasero de pollo al horno con 2 papas cocidas.",
      ],
      mealImages: [
        "/agua-limon.jpg",
        "/arroz-atun.jpg",
        "/avena.jpg",
        "/cafe.jpg",
        "/pan-integral.jpg",
        "/patata.jpg",
        "/pollo-horno.JPG",
      ],
    },
    warnings: [
      "Problemas Cardíacos: El esfuerzo eleva la presión arterial.",
      "Lesiones de Columna: Técnica perfecta en peso muerto.",
      "Hernias Inguinales: El esfuerzo de carga puede agravarlas.",
    ],
    tips: [
      "Sobrecarga Progresiva: Haz las repeticiones más lentas (3 seg para bajar).",
      "El descanso es gratis: Intenta dormir 8 horas.",
      "Agua: 3 litros al día. Es el suplemento más barato.",
    ],
  },
};

export default function EntrenoDetalle() {
  const { planKey } = useParams();
  const navigate = useNavigate();
  const { t } = useLocale();
  const plan = PLAN_CONTENT[planKey];
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  if (!plan) {
    return (
      <main className="profile-page entrenos-page" style={{ paddingTop: 80 }}>
        <div className="profile-shell text-center">
          <h1 className="profile-title">{t("entrenos.detail.notFound")}</h1>
          <Link className="btn btn-primary" to="/entrenos-unicos">{t("entrenos.detail.backToList")}</Link>
        </div>
      </main>
    );
  }

  const images = plan.diet.mealImages || [];
  const nextImage = () => setCurrentImageIndex((i) => (i + 1) % images.length);
  const prevImage = () => setCurrentImageIndex((i) => (i - 1 + images.length) % images.length);

  return (
    <main className="profile-page entrenos-page ed-page">
      <div className="profile-shell p-0 overflow-hidden">
        {/* HEADER */}
        <header className="ed-header">
          <div className="row g-0 align-items-stretch">
            <div className="col-lg-5 col-md-5 overflow-hidden">
              <img
                src={plan.img || "/superman-david.jpg"}
                alt={plan.title}
                className="ed-hero-img"
                draggable={false}
              />
            </div>
            <div className="col-lg-7 col-md-7 p-4 p-md-5 d-flex flex-column justify-content-center">
              <span className="ed-badge">{plan.duration}</span>
              <h1 className="ed-title">{plan.title}</h1>
              <h4 className="ed-subtitle">{plan.subtitle}</h4>
              <p className="ed-overview">{plan.overview}</p>
              <div className="d-flex gap-3 mt-4 flex-wrap">
                <button className="btn btn-outline-primary" onClick={() => navigate(-1)}>← {t("entrenos.detail.back")}</button>
                <Link className="btn btn-primary" to="/entrenos-unicos">{t("entrenos.detail.explorePlans")}</Link>
              </div>
            </div>
          </div>
        </header>

        {/* CONTENIDO */}
        <div className="ed-content">
          {/* Rutina */}
          <section className="mb-5">
            <h2 className="ed-section-title">{t("entrenos.detail.trainingPlan")}</h2>
            <div className="row g-4">
              {plan.routine.map((block) => (
                <div key={block.title} className="col-md-4">
                  <div className="ed-routine-card">
                    <h3 className="ed-routine-card-title">{block.title}</h3>
                    <ul className="ps-3 mb-0 small">
                      {block.items.map((item) => <li key={item} className="mb-2">{item}</li>)}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Dieta */}
          <section className="ed-diet-section">
            <h2 className="ed-diet-title">{plan.diet.title}</h2>
            <p className="ed-diet-overview">{plan.diet.overview}</p>

            <div className="row g-5">
              <div className="col-md-5">
                <h3 className="ed-diet-subtitle">{t("entrenos.detail.shoppingList")}</h3>
                <ul className="ed-diet-list">
                  {plan.diet.shopping.map((item) => <li key={item} className="mb-2">{item}</li>)}
                </ul>
              </div>
              <div className="col-md-7">
                <h3 className="ed-diet-subtitle">{t("entrenos.detail.dailyMenu")}</h3>
                <div className="ed-menu-list">
                  {plan.diet.dailyMenu.map((item, idx) => (
                    <div key={idx} className="ed-menu-item">{item}</div>
                  ))}
                </div>
              </div>
            </div>

            {/* Carrusel de Comidas */}
            {images.length > 0 && (
              <div className="ed-meal-carousel-wrap">
                <h4 className="ed-meal-carousel-title">{t("entrenos.preview.meals")}</h4>
                <div className="ed-meal-carousel">
                  <button className="ed-meal-carousel-btn ed-meal-carousel-btn--prev" onClick={prevImage} aria-label={t("entrenos.preview.mealPrev")}>‹</button>
                  <img
                    src={images[currentImageIndex]}
                    alt={`Comida ${currentImageIndex + 1}`}
                    className="ed-meal-carousel-img"
                    draggable={false}
                  />
                  <button className="ed-meal-carousel-btn ed-meal-carousel-btn--next" onClick={nextImage} aria-label={t("entrenos.preview.mealNext")}>›</button>
                  <div className="ed-meal-carousel-indicator">
                    {currentImageIndex + 1} / {images.length}
                  </div>
                </div>
              </div>
            )}

            {/* Tabla Nutricional */}
            <div className="table-responsive mt-5">
              <table className="ed-nutrition-table">
                <thead>
                  <tr>
                    <th>{t("entrenos.detail.moment")}</th>
                    <th>{t("entrenos.detail.goal")}</th>
                    <th>{t("entrenos.detail.action")}</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.diet.nutritionalGuide.map((row, i) => (
                    <tr key={i}>
                      <td className="fw-bold">{row.momento}</td>
                      <td><span className="ed-nutrition-badge">{row.objetivo}</span></td>
                      <td className="ed-nutrition-action">{row.accion}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Advertencias y Consejos */}
          <section className="row g-4 mt-5">
            <div className="col-md-6">
              <div className="ed-warn-card ed-warn-card--danger">
                <h5 className="ed-warn-card-title ed-warn-card-title--danger">⚠️ {t("entrenos.detail.warnings")}</h5>
                <ul className="small mb-0">
                  {plan.warnings.map((w) => <li key={w} className="mb-2">{w}</li>)}
                </ul>
              </div>
            </div>
            <div className="col-md-6">
              <div className="ed-warn-card ed-warn-card--success">
                <h5 className="ed-warn-card-title ed-warn-card-title--success">💡 {t("entrenos.detail.tips")}</h5>
                <ul className="small mb-0">
                  {plan.tips.map((tip) => <li key={tip} className="mb-2">{tip}</li>)}
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
