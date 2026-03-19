import { Link, useParams, useNavigate } from "react-router-dom";
import "../styles/entrenos-unicos.css";
import React, { useState, useRef } from "react"; 

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
        "Comida 3: 1 cuarto trasero de pollo al horno con 2 papas cocidas."
      ],
    mealimages:[
      "/agua-limon.jpg",
      "/arroz-atun.jpg",
      "/avena.jpg",
      "/cafe.jpg",
      "/pan-integral.jpg",
      "/patata.jpg",
      "/pollo-horno.jpg",
    ]
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

// --- COMPONENTE INTERNO PARA EL ZOOM  ---
function RetailZoomImage({ src, alt, zoomLevel = 3.5 }) {
  const [zoomStyle, setZoomStyle] = useState({});
  const [isHovering, setIsHovering] = useState(false);
  const containerRef = useRef(null);

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;

    const { left, top, width, height } = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - left) / width) * 100;
    const y = ((e.clientY - top) / height) * 100;

    // Calculamos el desfase (offset) para que el mouse actúe como una lente.
    const xOffset = -(x - 50) * (zoomLevel / 2);
    const yOffset = -(y - 50) * (zoomLevel / 2);

    setZoomStyle({
      transformOrigin: `${x}% ${y}%`,
      transform: `scale(${zoomLevel}) translate(${xOffset}px, ${yOffset}px)`,
    });
  };

  const handleMouseEnter = () => {
    setIsHovering(true);
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    setZoomStyle({}); // Reseteamos los estilos al salir
  };

  return (
    <div
      ref={containerRef}
      className={`entreno-retail-zoom-container ${isHovering ? "is-zoomed" : ""}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <img
        src={src}
        alt={alt}
        className="entreno-hero-img-base"
        loading="lazy"
      />
      <img
        src={src}
        alt={`${alt} zoomed`}
        className="entreno-hero-img-zoom"
        style={zoomStyle}
      />
    </div>
  );
}
// ---------------------------------------------------

export default function EntrenoDetalle() {
  const { planKey } = useParams();
  const navigate = useNavigate();
  const plan = PLAN_CONTENT[planKey];
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  if (!plan) {
    return (
      <main className="profile-page entrenos-page" style={{ paddingTop: 80 }}>
        <div className="profile-shell text-center">
          <h1 className="profile-title">Plan no encontrado</h1>
          <Link className="btn btn-primary" to="/entrenos-unicos">Volver a la lista</Link>
        </div>
      </main>
    );
  }

  const nextImage = () => {
    setCurrentImageIndex((prevIndex) => prevIndex ===  plan.diet.mealimages.length - 1 ? 0: prevIndex + 1);
  };

  const prevImage = () => {
    setCurrentImageIndex((prevIndex) => prevIndex === 0 ?  plan.diet.mealimages.length - 1 : prevIndex - 1);
  };

  return (
    <main className="profile-page entrenos-page entreno-detail-page" style={{ paddingTop: 80 }}>
      <div className="profile-shell p-0 overflow-hidden"> 
        {/* HEADER */}
        <header className="profile-header bg-white border-bottom shadow-sm">
          <div className="row g-0 align-items-stretch">
            {/* Imagen: Con la lógica de retail integrada */}
            <div className="col-lg-5 col-md-5 overflow-hidden">
              <RetailZoomImage 
                src={plan.img || "/superman-david.jpg"} 
                alt={plan.title} 
                zoomLevel={3.0} //  ajustar el nivel de zoom aquí
              />
            </div>
            {/* Texto */}
            <div className="col-lg-7 col-md-7 p-4 p-md-5 d-flex flex-column justify-content-center">
              <div className="entreno-detail-content">
                <span className="badge bg-primary-subtle text-primary mb-3 px-3 py-2">{plan.duration}</span>
                <h1 className="profile-title display-5 fw-bold mb-2">{plan.title}</h1>
                <h4 className="profile-subtitle text-muted mb-4">{plan.subtitle}</h4>
                <p className="text-muted lh-lg fs-5">{plan.overview}</p>
                <div className="d-flex gap-3 mt-4">
                  <button className="btn btn-outline-primary px-4 py-2" onClick={() => navigate(-1)}>← Volver</button>
                  <Link className="btn btn-primary px-4 py-2" to="/entrenos-unicos">Explorar otros planes</Link>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* CONTENIDO INTERMEDIO */}
        <div className="container-fluid px-4 px-md-5 py-5">
          {/* Rutina */}
          <section className="mb-5">
            <h2 className="h3 border-start border-primary border-4 ps-3 mb-4 fw-bold">Plan de Entrenamiento</h2>
            <div className="row g-4">
              {plan.routine.map((block) => (
                <div key={block.title} className="col-md-4">
                  <div className="card h-100 border-0 shadow-sm p-4 bg-light text-dark">
                    <h3 className="h6 fw-bold text-primary text-uppercase mb-3">{block.title}</h3>
                    <ul className="ps-3 mb-0 small">
                      {block.items.map((item) => <li key={item} className="mb-2">{item}</li>)}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Dieta */}
          <section className="mb-5 p-4 p-md-5 rounded-4 bg-dark text-white shadow">
            <h2 className="h3 mb-4 text-primary fw-bold">{plan.diet.title}</h2>
            <p className="mb-5 opacity-75">{plan.diet.overview}</p>
            
            <div className="row g-5">
              <div className="col-md-5">
                <h3 className="h5 fw-bold mb-3">Lista de Compras</h3>
                <ul className="opacity-75">
                  {plan.diet.shopping.map((item) => <li key={item} className="mb-2">{item}</li>)}
                </ul>
              </div>
              <div className="col-md-7">
                <h3 className="h5 fw-bold mb-3">Menú Diario Detallado</h3>
                <div className="list-group list-group-flush">
                  {plan.diet.dailyMenu.map((item, idx) => (
                    <div key={idx} className="list-group-item bg-transparent text-white border-secondary px-0 py-3 small">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {/* Carrusel de Imágenes de Comidas */}
            {plan.diet.mealimages && plan.diet.mealimages.length > 0 && (
              <div className="mt-5 pt-4 border-top border-secondary">
                <h4 className="h6 fw-bold text-primary text-uppercase text-center">Visualiza tus comidas</h4>
                <div className="entrenos-carousel-container relative rounded-3 overflow-hidden shadow-sm bg-white">
                  <img
                      src={plan.diet.mealimages[currentImageIndex]}
                      alt={`Comida ${currentImageIndex + 1}`}
                      className="d-block w-100 object-fit-cover"
                      style={{ height: "300px" }}
                  />
                  <button
                    onClick={prevImage}
                    classname="carousel-btn carousel-btn-prev"
                    aria-label="Imagen Anterior">
                  </button>
                  <button
                    onClick={nextImage}
                    classname="carousel-btn carousel-btn-next"
                    aria-label="Imagen Siguiente">
                  </button>
                  <div className="carousel-indicator small px-2 py-1 rounded bg-dark text-white opacity-75">
                    {currentImageIndex + 1} / {plan.diet.mealimages.length}
                  </div>
                </div>
              </div>
            )}
            {/* Tabla Nutricional */}
            <div className="table-responsive mt-5">
              <table className="table table-dark table-hover align-middle border-secondary">
                <thead>
                  <tr>
                    <th className="text-primary">Momento</th>
                    <th className="text-primary">Objetivo</th>
                    <th className="text-primary">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.diet.nutritionalGuide.map((row, i) => (
                    <tr key={i}>
                      <td className="fw-bold">{row.momento}</td>
                      <td><span className="badge bg-primary w-100">{row.objetivo}</span></td>
                      <td className="small opacity-75">{row.accion}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ADVERTENCIAS Y CONSEJOS (AL FINAL) */}
          <section className="row g-4 mt-5">
            <div className="col-md-6">
              <div className="h-100 p-4 border-top border-danger border-4 bg-white shadow-sm rounded-bottom">
                <h5 className="text-danger fw-bold mb-3">⚠️ Contraindicaciones</h5>
                <ul className="small mb-0 text-muted">
                  {plan.warnings.map(w => <li key={w} className="mb-2">{w}</li>)}
                </ul>
              </div>
            </div>
            <div className="col-md-6">
              <div className="h-100 p-4 border-top border-success border-4 bg-white shadow-sm rounded-bottom">
                <h5 className="text-success fw-bold mb-3">💡 Consejos de Superman</h5>
                <ul className="small mb-0 text-muted">
                  {plan.tips.map(t => <li key={t} className="mb-2">{t}</li>)}
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
