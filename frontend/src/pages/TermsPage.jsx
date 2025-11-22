export default function TermsPage() {
  return (
    <main className="container py-5 legal-page">
      <div className="legal-hero mb-4">
        <p className="legal-meta text-uppercase fw-semibold small mb-2">Última actualización: 22 de noviembre de 2025</p>
        <h1 className="legal-title mb-2">Términos y Condiciones de Uso de Fitter</h1>
        <p className="mb-0">
          Estos Términos se rigen por la legislación chilena, en particular por la Ley N° 19.496 sobre Protección de los Derechos de los Consumidores y la Ley N° 21.719 sobre Protección de Datos Personales, además de otras normas aplicables.
        </p>
      </div>

      <div className="legal-grid">
        <section className="legal-card">
          <h2 className="legal-section-title">1. Aceptación de los Términos</h2>
          <p>
            Al registrarte, acceder o utilizar cualquiera de los servicios de Fitter, confirmas que has leído, comprendido y aceptas estos Términos en su
            totalidad. Si no estás de acuerdo, por favor, no utilices la plataforma.
          </p>
          <p>
            Debes ser mayor de 18 años o, si eres menor, contar con el consentimiento de un tutor legal. Proporcionarás información veraz y actualizada
            durante el registro y uso de la plataforma. Si actúas en nombre de una entidad, garantizas tener autoridad para vincularla a estos Términos.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">2. Descripción del Servicio</h2>
          <p>
            Fitter es una aplicación full-stack que ofrece rutinas de ejercicio personalizadas, recomendaciones de estilo de vida, un chatbot asistido por IA,
            una tienda en línea y gestión de usuarios (registro, perfiles, autenticación multifactor, notificaciones y panel administrativo).
          </p>
          <p>
            Las rutinas y recomendaciones no constituyen asesoramiento médico profesional. Fitter no reemplaza la evaluación de un profesional de la salud;
            recomendamos consultar con médicos, nutricionistas o entrenadores certificados antes de iniciar cualquier programa.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">3. Registro y Cuentas de Usuario</h2>
          <h3>3.1 Creación de Cuenta</h3>
          <p>
            Para acceder a servicios personalizados, debes registrarte proporcionando información precisa, incluyendo nombre, correo electrónico, datos físicos
            y preferencias. El registro es gratuito para usuarios básicos, pero puede requerir verificación.
          </p>
          <h3>3.2 Responsabilidades del Usuario</h3>
          <ul className="ps-4">
            <li>Mantener la confidencialidad de tus credenciales y códigos MFA.</li>
            <li>Notificar a soporte@fitter.cl ante accesos no autorizados.</li>
            <li>Responsabilizarse por las actividades realizadas bajo su cuenta.</li>
            <li>El MFA es obligatorio para cuentas administrativas y recomendado para todos.</li>
          </ul>
          <h3>3.3 Suspensión o Terminación</h3>
          <p>
            Fitter puede suspender o terminar cuentas por incumplimiento de estos Términos, actividades fraudulentas o inactividad. En caso de terminación,
            se perderá acceso a los datos salvo los requeridos por ley.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">4. Privacidad y Protección de Datos</h2>
          <p>
            Fitter se compromete a proteger la privacidad conforme a la normativa aplicable. Consulte la Política de Privacidad y Política de Seguridad para
            detalles completos.
          </p>
          <p>
            Datos recopilados: información personal (nombre, email, datos físicos, condiciones médicas), datos de uso y preferencias. Uso: personalizar servicios,
            procesar pagos y mejorar la plataforma. No vendemos datos a terceros sin consentimiento.
          </p>
          <p>
            Protección: datos sensibles se cifran con AES-128 (Fernet), se almacenan en servidores seguros y se anonimizan en logs. Rotación de claves anual.
            Derechos: acceso, rectificación, eliminación o portabilidad. Solicítalo a privacidad@fitter.cl.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">5. Uso Aceptable</h2>
          <p>Al utilizar Fitter, te comprometes a:</p>
          <ul className="ps-4">
            <li>Usar la plataforma para fines personales y no comerciales sin autorización.</li>
            <li>No violar leyes ni derechos de terceros.</li>
            <li>No intentar hackear, inyectar código malicioso, enviar spam o sobrecargar servidores.</li>
            <li>No utilizar el chatbot para actividades ilícitas o perjudiciales.</li>
          </ul>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">6. Propiedad Intelectual</h2>
          <p>
            Todo el contenido de Fitter (código, diseños, logos, textos, imágenes, algoritmos y bases de datos) es propiedad exclusiva de Fitter SpA o sus
            licenciadores. No se permite copiar, distribuir o modificar sin autorización escrita.
          </p>
          <p>
            El usuario retiene derechos sobre su contenido personal, pero concede a Fitter una licencia no exclusiva para procesarlo y mostrarlo en la
            plataforma.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">7. Pagos y Compras</h2>
          <h3>7.1 Tienda en Línea</h3>
          <p>La tienda permite comprar productos con carrito, pagos seguros y boletas electrónicas. Los precios incluyen IVA y pueden variar.</p>
          <h3>7.2 Procesamiento de Pagos</h3>
          <p>Pagos se procesan a través de pasarelas seguras. Fitter no almacena datos de tarjetas.</p>
          <h3>7.3 Reembolsos y Devoluciones</h3>
          <p>
            Productos defectuosos: derecho a devolución dentro de 7 días, conforme a la Ley del Consumidor. Servicios digitales: no reembolsables una vez
            utilizados, salvo fallos técnicos imputables a Fitter. Solicitudes a soporte@fitter.cl.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">8. Descargos de Responsabilidad</h2>
          <p>
            Las rutinas y recomendaciones son generales y no constituyen asesoramiento médico. Fitter no asume responsabilidad por lesiones o daños.
            Respecto a disponibilidad, no garantizamos servicio 100% ininterrumpido.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">9. Terminación</h2>
          <p>
            Los Términos permanecen vigentes mientras uses la plataforma. Puedes terminar eliminando tu cuenta. Fitter puede terminar por incumplimiento,
            notificando con 30 días de antelación salvo casos graves.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">10. Modificaciones</h2>
          <p>
            Fitter puede actualizar estos Términos por cambios normativos, técnicos o de servicio. Avisaremos con 15 días de antelación. El uso continuado
            implica aceptación.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">11. Ley Aplicable y Resolución de Disputas</h2>
          <p>
            Estos Términos se rigen por la legislación de la República de Chile. En particular, la relación entre los usuarios y Fitter se ajusta a la Ley N° 19.496 sobre Protección de los Derechos de los Consumidores y a la Ley N° 21.719 sobre Protección de Datos Personales, junto con otras normas sectoriales y de protección de datos aplicables.
          </p>
          <p>
            Cualquier disputa derivada de estos Términos será sometida, en primera instancia, a intentos de resolución amistosa. Si no fuera posible, las partes se someterán a la jurisdicción de los tribunales competentes de Chile.
          </p>
        </section>

        <section className="legal-card">
          <h2 className="legal-section-title">12. Contacto</h2>
          <p>
            Para consultas o ejercer derechos, contacta a soporte@fitter.cl o privacidad@fitter.cl.
          </p>
          <p className="mb-0">Al aceptar estos Términos, reconoces haber leído y comprendido todas las secciones.</p>
        </section>
      </div>
    </main>
  );
}
