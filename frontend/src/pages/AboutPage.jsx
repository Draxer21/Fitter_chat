export default function AboutPage() {
  const mapStats = [
    { label: 'Usuarios activos', value: '12K+' },
    { label: 'Centros conectados', value: '34' },
    { label: 'Integraciones API', value: '18' },
    { label: 'SLA anual', value: '99.7%' },
  ];

  return (
    <main className="container py-5 about-page">
      <header className="mb-5 about-header">
        <p className="about-kicker text-uppercase fw-semibold">Sobre nosotros</p>
        <h1 className="about-title">FITTER · Misión, visión y compromiso</h1>
        <p className="about-subtitle">
          Conoce lo que nos mueve, hacia dónde vamos y cómo trabajamos para entregar un servicio de excelencia.
        </p>
        <div className="about-badges">
          <span>AI + Fitness</span>
          <span>Infraestructura Cloud</span>
          <span>Equipo MX / CL</span>
        </div>
      </header>

      <section className="about-stats-grid">
        <article>
          <h3>Presencia</h3>
          <ul>
            <li>Operamos 100% remoto con hubs en Santiago y Ciudad de México.</li>
            <li>Soportamos integraciones con clubes, centros y programas corporativos.</li>
            <li>Trabajamos bajo metodologías ágiles con actualizaciones semanales.</li>
          </ul>
        </article>
        <article>
          <h3>Impacto</h3>
          <ul>
            <li>Asesoramos rutinas, dietas y seguimiento de métricas en un único panel.</li>
            <li>Ofrecemos soporte 24/7 para administradores y entrenadores.</li>
            <li>Habilitamos análisis de datos en tiempo real para equipos médicos.</li>
          </ul>
        </article>
        <article>
          <h3>Distribución</h3>
          <div className="about-stats-list">
            {mapStats.map((item) => (
              <div key={item.label}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="about-block">
        <div className="about-text">
          <p>
            En FITTER, nuestra misión es desarrollar una plataforma digital inteligente orientada a optimizar la salud, el bienestar
            y el rendimiento físico de los usuarios mediante herramientas tecnológicas avanzadas y procesos automatizados.
          </p>
          <p className="mb-0">
            Buscamos integrar algoritmos de inteligencia artificial, monitoreo en tiempo real y modelos predictivos que permitan entregar planes
            de entrenamiento y recomendaciones personalizadas, garantizando precisión, seguridad y confiabilidad. Nuestra labor se enfoca en ofrecer
            una experiencia accesible, intuitiva y respaldada por buenas prácticas tecnológicas, aportando a la transformación digital del sector fitness
            y mejorando la calidad de vida de las personas que confían en nuestro sistema.
          </p>
        </div>
        <div className="about-card">
          <span className="about-kicker text-uppercase fw-semibold">Sobre nosotros</span>
          <h2 className="about-card-title">Misión</h2>
        </div>
      </section>

      <section className="about-block reverse">
        <div className="about-card">
          <span className="about-kicker text-uppercase fw-semibold">Sobre nosotros</span>
          <h2 className="about-card-title">Visión</h2>
        </div>
        <div className="about-text">
          <p>
            Nuestra visión consiste en posicionar a FITTER como la plataforma líder en asistencia inteligente para el entrenamiento y la salud
            en el mercado chileno y latinoamericano. Aspiramos a consolidarnos como un referente en innovación aplicada al bienestar,
            reconocidos por la eficiencia de nuestros modelos de recomendación, la robustez de nuestra arquitectura y la confiabilidad de los datos que procesamos.
          </p>
          <p className="mb-0">
            Proyectamos un crecimiento sostenible, expandiendo nuestra presencia en nuevos mercados y desarrollando soluciones complementarias que permitan a FITTER
            evolucionar hacia un ecosistema integral de autogestión del bienestar físico, manteniendo como sello distintivo el profesionalismo,
            la ética digital y la excelencia técnica.
          </p>
        </div>
      </section>

      <section className="about-block">
        <div className="about-text">
          <p>
            En FITTER reconocemos que la tecnología debe contribuir responsablemente al bienestar de las personas y a la reducción de brechas de acceso
            a servicios de salud y actividad física. Por esta razón, promovemos principios de inclusión digital, accesibilidad web y equidad tecnológica
            en el diseño e implementación de nuestros sistemas.
          </p>
          <p className="mb-0">
            Incentivamos el uso responsable de los datos personales, respetando estrictamente la legislación vigente y privilegiando la transparencia en cada proceso.
            Además, buscamos generar impacto positivo en la comunidad mediante iniciativas de educación digital, hábitos saludables y promoción de estilos de vida activos,
            reflejando nuestros valores de cercanía, ética y responsabilidad social.
          </p>
        </div>
        <div className="about-card">
          <span className="about-kicker text-uppercase fw-semibold">Sobre nosotros</span>
          <h2 className="about-card-title">Compromiso Social</h2>
        </div>
      </section>

      <section className="about-block reverse">
        <div className="about-card">
          <span className="about-kicker text-uppercase fw-semibold">Sobre nosotros</span>
          <h2 className="about-card-title">Infraestructura Tecnológica</h2>
        </div>
        <div className="about-text">
          <p>
            FITTER cuenta con una infraestructura tecnológica de última generación que respalda cada uno de sus módulos funcionales
            y facilita la entrega de un servicio confiable, estable y seguro. Disponemos de modelos de inteligencia artificial entrenados
            con TensorFlow y PyTorch, servicios alojados en entornos cloud escalables, bases de datos relacionales optimizadas para consultas
            de alto rendimiento y sistemas de monitoreo que aseguran la continuidad operativa.
          </p>
          <p className="mb-0">
            Nuestra arquitectura integra estándares modernos de desarrollo, API REST para interoperabilidad, un front-end responsivo adaptable a distintos dispositivos
            y un motor de recomendaciones basado en análisis predictivo. Esta infraestructura refleja nuestro compromiso constante con la mejora continua
            y con la entrega de soluciones tecnológicas de excelencia.
          </p>
        </div>
      </section>

      <section className="about-values-grid">
        <article>
          <h3>Valores</h3>
          <ul>
            <li>Ética digital y transparencia</li>
            <li>Aprendizaje continuo</li>
            <li>Respeto y diversidad</li>
          </ul>
        </article>
        <article>
          <h3>Relación con clientes</h3>
          <p>
            Trabajamos colaborativamente con cada gimnasio, clínica o corporativo, acompañándolos en despliegues, capacitación y soporte post implementación.
          </p>
        </article>
        <article>
          <h3>Hoja de ruta</h3>
          <p>
            Para 2026, lanzaremos módulos de telemedicina deportiva, asistentes multilingües y analítica avanzada de hábitos.
          </p>
        </article>
      </section>
    </main>
  );
}
