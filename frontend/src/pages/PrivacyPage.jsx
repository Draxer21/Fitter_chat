export default function PrivacyPage() {
  return (
    <main className="container py-5 legal-page">
      <div className="legal-hero mb-4 privacy-hero">
        <p className="legal-meta text-uppercase fw-semibold small mb-2">
          Última actualización: 31 de octubre de 2025
        </p>
        <h1 className="legal-title mb-2">Términos y condiciones / Tratamiento de datos – FITTER</h1>
        <p className="legal-subtitle">Protegemos tu información con estándares nacionales e internacionales.</p>
        <div className="privacy-badges">
          <span>Ley 19.628 y Ley 21.459</span>
          <span>Cifrado extremo a extremo</span>
          <span>Derechos ARCO garantizados</span>
        </div>
      </div>

      <section className="privacy-highlight-grid">
        <article className="privacy-highlight-card">
          <h3>¿Quién administra tus datos?</h3>
          <p>FITTER SpA es el responsable del tratamiento, con equipos alojados en servidores certificados dentro de Chile.</p>
        </article>
        <article className="privacy-highlight-card">
          <h3>¿Para qué los usamos?</h3>
          <p>La información se emplea para crear tu perfil, personalizar rutinas, enviar avisos técnicos y responder solicitudes.</p>
        </article>
        <article className="privacy-highlight-card">
          <h3>¿Cómo te protegemos?</h3>
          <p>Aplicamos cifrado TLS, controles de acceso, monitoreo continuo y procesos de anonimización ante auditorías.</p>
        </article>
      </section>

      <section className="privacy-anchor-nav" aria-label="Índice rápido">
        <p className="mb-2">Ve directo a la sección que necesitas:</p>
        <div className="privacy-anchor-links">
          <a href="#responsable">Responsable</a>
          <a href="#finalidad">Finalidad</a>
          <a href="#base-legal">Base legal</a>
          <a href="#conservacion">Conservación</a>
          <a href="#derechos">Derechos</a>
          <a href="#seguridad">Seguridad</a>
          <a href="#terceros">Terceros</a>
          <a href="#modificaciones">Cambios</a>
          <a href="#aceptacion">Aceptación</a>
        </div>
      </section>

      <section className="privacy-callouts">
        <article>
          <h3>Ejercer tus derechos</h3>
          <p>Escríbenos a <strong>privacidad@fitter.cl</strong> y detalla si deseas acceso, rectificación, cancelación u oposición.</p>
        </article>
        <article>
          <h3>Ayuda personalizada</h3>
          <p>¿Tienes dudas urgentes? Agenda una llamada con nuestro equipo de seguridad para revisar tu caso paso a paso.</p>
        </article>
      </section>

      <div className="legal-grid">
        <section className="legal-card" id="responsable">
          <h2 className="legal-section-title">1. Identificación del responsable del tratamiento</h2>
          <p>
            El presente sitio web y la aplicación móvil FITTER son administrados por FITTER SpA, empresa chilena dedicada al desarrollo de soluciones tecnológicas para el acompañamiento deportivo y el bienestar físico, con domicilio en [Ciudad], Chile.
          </p>
          <p className="mb-0">
            Para cualquier consulta sobre esta política o el tratamiento de datos personales, puede comunicarse a través del correo: privacidad@fitter.cl.
          </p>
        </section>

        <section className="legal-card" id="finalidad">
          <h2 className="legal-section-title">2. Finalidad del tratamiento de datos</h2>
          <p>
            Al registrarse en FITTER, utilizar la aplicación o enviar información a través de los formularios disponibles, el usuario autoriza a FITTER al tratamiento de los datos personales entregados (por ejemplo: nombre, correo electrónico, datos básicos de perfil y datos relacionados con su actividad física) con el interés legítimo y/o contractual de:
          </p>
          <ul className="ps-4">
            <li>Crear y gestionar su cuenta de usuario en la plataforma.</li>
            <li>Configurar su perfil de entrenamiento (objetivos, nivel de experiencia, preferencias).</li>
            <li>Permitir la interacción con el chatbot de inteligencia artificial y la entrega de recomendaciones generales de entrenamiento y bienestar.</li>
            <li>Registrar y mostrar su progreso dentro de la aplicación.</li>
            <li>Atender consultas, solicitudes o comentarios enviados por los usuarios.</li>
            <li>Mantener comunicación relacionada con el servicio (avisos técnicos, actualizaciones, cambios en términos y políticas).</li>
          </ul>
          <p className="mb-0">
            En ningún caso los datos personales serán utilizados para fines distintos a los declarados ni serán cedidos a terceros con fines comerciales sin la autorización expresa del usuario.
          </p>
        </section>

        <section className="legal-card" id="base-legal">
          <h2 className="legal-section-title">3. Base legal del tratamiento</h2>
          <p>El tratamiento de los datos personales se basa en:</p>
          <ul className="ps-4">
            <li>
              La ejecución de la relación contractual entre el usuario y FITTER, necesaria para prestar los servicios de la plataforma (creación de cuenta, uso de la app, generación de recomendaciones).
            </li>
            <li>
              El consentimiento del usuario, especialmente para el tratamiento de datos vinculados a su actividad física y bienestar, que pueden considerarse datos especialmente protegidos.
            </li>
            <li>
              El interés legítimo de FITTER en mantener comunicación con sus usuarios, mejorar la calidad del servicio y garantizar la seguridad de la plataforma, respetando en todo momento los derechos y libertades de los titulares de datos.
            </li>
          </ul>
          <p className="mb-0">
            Este tratamiento es necesario para responder a solicitudes iniciadas voluntariamente por el usuario y para el funcionamiento normal de la plataforma, sin perjuicio de que el titular conserve en todo momento sus derechos de acceso, rectificación, cancelación y oposición.
          </p>
        </section>

        <section className="legal-card" id="conservacion">
          <h2 className="legal-section-title">4. Conservación de los datos</h2>
          <p>
            Los datos proporcionados se conservarán durante el tiempo que la cuenta de usuario se mantenga activa y por un periodo máximo de 24 meses desde la última interacción relevante en la plataforma, o hasta que el titular solicite su eliminación, siempre que no exista una obligación legal de conservarlos por más tiempo.
          </p>
          <p className="mb-0">
            Pasados dichos plazos, los datos serán eliminados o, en su caso, anonimizados de forma segura y definitiva para fines estadísticos.
          </p>
        </section>

        <section className="legal-card" id="derechos">
          <h2 className="legal-section-title">5. Derechos de los titulares</h2>
          <p>El titular de los datos podrá ejercer en cualquier momento los derechos reconocidos por la normativa chilena en materia de protección de datos personales, incluyendo:</p>
          <ul className="ps-4">
            <li>Derecho de acceso: conocer qué datos personales son tratados y con qué finalidad.</li>
            <li>Derecho de rectificación: solicitar la corrección de datos inexactos o desactualizados.</li>
            <li>Derecho de cancelación o eliminación: pedir la eliminación de sus datos cuando ya no sean necesarios para los fines declarados o cuando retire su consentimiento, en la medida en que la ley lo permita.</li>
            <li>Derecho de oposición: oponerse al tratamiento basado en interés legítimo o a ciertas comunicaciones.</li>
          </ul>
          <p className="mb-0">
            Las solicitudes podrán realizarse por escrito al correo: privacidad@fitter.cl, indicando nombre completo, medio de contacto y el derecho que se desea ejercer.
          </p>
        </section>

        <section className="legal-card" id="seguridad">
          <h2 className="legal-section-title">6. Seguridad de la información</h2>
          <p>
            FITTER implementa medidas técnicas y organizativas adecuadas para garantizar la seguridad y confidencialidad de los datos personales, evitando su pérdida, acceso no autorizado o manipulación indebida.
          </p>
          <p className="mb-0">
            Entre estas medidas se incluyen, entre otras, el uso de comunicaciones cifradas, controles de acceso a los sistemas, registro de eventos relevantes y revisiones periódicas de la configuración de seguridad.
          </p>
        </section>

        <section className="legal-card" id="terceros">
          <h2 className="legal-section-title">7. Enlaces y servicios de terceros</h2>
          <p>
            La plataforma FITTER puede estar vinculada a servicios de terceros (por ejemplo, proveedores de infraestructura, herramientas de analítica o pasarelas de pago). Estos servicios mantienen sus propias políticas de privacidad, las cuales el usuario puede revisar en los sitios oficiales de cada proveedor.
          </p>
          <p className="mb-0">
            FITTER no se hace responsable por el tratamiento de datos personales que dichos terceros realicen fuera de lo informado en esta política.
          </p>
        </section>

        <section className="legal-card" id="modificaciones">
          <h2 className="legal-section-title">8. Modificaciones de esta política</h2>
          <p>
            FITTER se reserva el derecho de modificar estos términos de tratamiento de datos para adecuarlos a cambios normativos, a mejoras en sus procesos de protección de datos o a nuevas funcionalidades de la plataforma.
          </p>
          <p className="mb-0">
            Cualquier modificación será publicada oportunamente en esta misma página, indicando la fecha de actualización. Cuando los cambios sean relevantes, se informará al usuario mediante avisos en la aplicación o por correo electrónico.
          </p>
        </section>

        <section className="legal-card" id="aceptacion">
          <h2 className="legal-section-title">9. Aceptación de los términos</h2>
          <p className="mb-0">
            El registro en la plataforma, el uso de la aplicación o el envío de información a través de los formularios de FITTER implican la aceptación expresa de estos Términos y Condiciones relativos al tratamiento de datos personales, de las finalidades indicadas y de las bases legales descritas.
          </p>
        </section>
      </div>
    </main>
  );
}
