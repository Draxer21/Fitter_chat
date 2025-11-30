import React, { useState } from "react";
import { useLocale } from "../contexts/LocaleContext";

export default function EntrenosUnicos() {
  const { t } = useLocale();
  const [selectedPreview, setSelectedPreview] = useState(null);

  const plans = [
    {
      key: "shonen",
      title: 'Shonen Power',
      duration: '8 semanas',
      description: 'Enfocado en fuerza e hipertrofia con circuitos metabólicos.',
      img: '/flash.jpg',
      bodyType: 'Atlético y veloz',
    },
    {
      key: "ninja",
      title: 'Ninja Agility',
      duration: '6 semanas',
      description: 'Enfocado en movilidad, plyometrics y acondicionamiento.',
      img: '/shazam.jpg',
      bodyType: 'Ágil y definido',
    },
    {
      key: "mecha",
      title: 'Mecha Endurance',
      duration: '10 semanas',
      description: 'Enfocado en resistencia y trabajo aeróbico progresivo.',
      img: '/bane.jpg',
      bodyType: 'Robusto y resistente',
    },
  ];

  return (
    <main className="container py-5">
      <div className="mb-4">
        <h1 className="mb-2">Entrenos Únicos</h1>
        <p className="text-muted">Programas de entrenamiento temáticos con duración, plan alimentario, equipamiento y recomendaciones por nivel.</p>
      </div>

      <section className="mb-4">
        <h2>Resumen</h2>
        <p>
          Los "Entrenos Únicos" son planes temáticos inspirados en personajes y estilos. Cada plan tiene una duración definida,
          una propuesta de alimentación orientativa, lista de equipamiento para casa o gimnasio y recomendaciones para principiantes y
          avanzados. Antes de iniciar, revisa la <strong>Evaluación médica</strong> para saber si puedes realizarlos de forma segura.
        </p>
      </section>

      <section className="mb-4">
        <h2>Planes disponibles</h2>
        <div className="row">
          {plans.map((p) => (
            <div className="col-md-4 mb-3" key={p.key}>
              <div className={`card h-100 ${selectedPreview === p.key ? 'border-primary' : ''}`} role="button" onClick={() => setSelectedPreview(p.key)}>
                <img
                  src={p.img}
                  className="card-img-top"
                  alt={`${p.title} preview`}
                  style={{ objectFit: 'cover', height: 220 }}
                />
                <div className="card-body">
                  <h5 className="card-title">{p.title}</h5>
                  <p className="card-text mb-1"><strong>Duración:</strong> {p.duration}</p>
                  <p className="card-text text-muted small">{p.description}</p>
                  <p className="card-text"><em>Tipo de cuerpo (vista):</em> {p.bodyType}</p>
                </div>
                <div className="card-footer bg-transparent">
                  <button className={`btn ${selectedPreview === p.key ? 'btn-outline-primary' : 'btn-primary'}`} onClick={(e) => { e.stopPropagation(); setSelectedPreview(p.key); }}>
                    {selectedPreview === p.key ? 'Seleccionado' : 'Ver vista'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4">
          <h3>Vista previa seleccionada</h3>
          {!selectedPreview && <p className="text-muted">Haz clic en una tarjeta para ver una vista ampliada del tipo de cuerpo asociado al plan.</p>}
          {selectedPreview && (
            (() => {
              const p = plans.find(pl => pl.key === selectedPreview);
              return (
                <div className="card mb-3">
                  <div className="row g-0">
                    <div className="col-md-5">
                      <img src={p.img} className="img-fluid rounded-start" alt={`${p.title} large preview`} style={{ height: '100%', objectFit: 'cover' }} />
                    </div>
                    <div className="col-md-7">
                      <div className="card-body">
                        <h4 className="card-title">{p.title} — {p.duration}</h4>
                        <p className="card-text">{p.description}</p>
                        <p className="card-text"><strong>Tipo de cuerpo objetivo:</strong> {p.bodyType}</p>
                        <p className="card-text text-muted">Selecciona este estilo si te identifica el tipo de cuerpo mostrado y tus objetivos.</p>
                        <div>
                          <a className="btn btn-primary me-2" href="/registro">Inscribirme</a>
                          <button className="btn btn-outline-secondary" onClick={() => setSelectedPreview(null)}>Cerrar vista</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>
      </section>

      <section className="mb-4">
        <h2>Alimentación (orientativa)</h2>
        <p>
          Cada plan incluye un esquema alimenticio orientativo con macronutrientes objetivo (proteína, carbohidrato, grasa) y ejemplos de
          comidas. No sustituye la consulta con un nutricionista.
        </p>
        <ul>
          <li><strong>Desayuno:</strong> fuente de carbohidrato complejo + proteína (ej. avena + claras/queso fresco).</li>
          <li><strong>Almuerzo:</strong> proteína magra + carbohidrato + verduras.</li>
          <li><strong>Cena:</strong> proteína ligera + verduras + grasas saludables.</li>
        </ul>
      </section>

      <section className="mb-4">
        <h2>Equipamiento</h2>
        <div className="row">
          <div className="col-md-6">
            <h3>Casa</h3>
            <ul>
              <li>Mancuernas ajustables / juego de mancuernas</li>
              <li>Banda elástica o minibands</li>
              <li>Colchoneta de ejercicio</li>
              <li>Barra para dominadas (opcional)</li>
            </ul>
          </div>
          <div className="col-md-6">
            <h3>Gimnasio</h3>
            <ul>
              <li>Multigimnasio o banco con barra y discos</li>
              <li>Máquinas de polea y cables</li>
              <li>Estación de dominadas / TRX</li>
              <li>Equipo para cardio (cinta, bicicleta, remo)</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-4">
        <h2>Evaluación médica / Contraindicaciones</h2>
        <p>
          Antes de iniciar cualquier Entreno Único, recomendamos realizar una evaluación médica.
        </p>
        <h3>Personas que deberían consultar/evitar</h3>
        <ul>
          <li>Personas con enfermedad cardiovascular diagnosticada (angina, insuficiencia cardíaca, arritmias no controladas).</li>
          <li>Hipertensión severa no controlada (consultar médico antes de iniciar).</li>
          <li>Embarazo o postparto reciente (consultar al profesional de salud).</li>
          <li>Lesiones agudas o dolor articular no evaluado (tendinopatías, esguinces no resueltos).</li>
          <li>Enfermedades respiratorias graves sin control (ej. EPOC avanzado).</li>
        </ul>
        <p className="mb-0">Si tienes dudas, consulta con tu médico. Estos criterios son orientativos y no sustituyen la evaluación clínica.</p>
      </section>

      <section className="mb-5">
        <h2>Cómo acceder</h2>
        <p>Para ver el plan completo, descarga la guía o inscríbete en el programa.</p>
        <a className="btn btn-primary" href="/registro">Inscríbete ahora</a>
      </section>
    </main>
  );
}
