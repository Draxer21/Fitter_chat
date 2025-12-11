import React from 'react';

export default function AccessibilityPage() {
  return (
    <main className="container py-5 accessibility-page">
      <header className="accessibility-hero mb-5">
        <p className="legal-meta text-uppercase fw-semibold small mb-2">
          Declaración institucional
        </p>
        <h1>Accesibilidad e inclusión digital</h1>
        <p className="accessibility-subtitle">
          Diseñamos FITTER para que cada persona pueda entrenar con independencia de su dispositivo, contexto o capacidad.
        </p>
        <div className="accessibility-badges">
          <span>WCAG 2.1 AA</span>
          <span>Ley 20.422</span>
          <span>SENADIS</span>
          <span>Testing NVDA · VoiceOver</span>
        </div>
      </header>

      <section className="accessibility-highlight-grid" aria-label="Resumen de pilares">
        <article>
          <h3>Diseño universal</h3>
          <p>Interfaces pensadas desde el inicio para teclado, lectores de pantalla y dispositivos táctiles.</p>
        </article>
        <article>
          <h3>Contenido perceptible</h3>
          <p>Contrastes AA, ajustes de tipografía y soporte de idioma para entregar información clara.</p>
        </article>
        <article>
          <h3>Operación segura</h3>
          <p>Componentes con roles ARIA, orden lógico y mensajes de error anunciados correctamente.</p>
        </article>
      </section>

      <section className="accessibility-anchor-nav" aria-label="Índice de secciones">
        <p className="mb-2">Explora los apartados clave:</p>
        <div className="accessibility-anchor-links">
          <a href="#commitment">Compromiso</a>
          <a href="#features">Características</a>
          <a href="#controls">Controles</a>
          <a href="#feedback">Retroalimentación</a>
          <a href="#date">Actualización</a>
        </div>
      </section>

      <section className="mb-5 accessibility-panel" aria-labelledby="commitment">
        <h2 id="commitment">Nuestro Compromiso</h2>
        <p>
          En <strong>Fitter</strong>, nos comprometemos a garantizar que nuestra plataforma sea accesible
          para todas las personas, independientemente de sus capacidades. Seguimos las pautas de accesibilidad
          del contenido web <strong>WCAG 2.1 nivel AA</strong> y la normativa chilena vigente.
        </p>
      </section>

      <section className="mb-5 accessibility-panel" aria-labelledby="features">
        <h2 id="features">Características de Accesibilidad</h2>

        <h3 className="h5 mt-4">1. Navegación por Teclado</h3>
        <ul>
          <li><kbd>Tab</kbd> - Navegar hacia adelante</li>
          <li><kbd>Shift</kbd> + <kbd>Tab</kbd> - Navegar hacia atrás</li>
          <li><kbd>Enter</kbd> o <kbd>Espacio</kbd> - Activar enlaces y botones</li>
          <li>Indicadores visuales claros para el foco del teclado</li>
          <li>Enlace "Saltar al contenido principal" al inicio de cada página</li>
        </ul>

        <h3 className="h5 mt-4">2. Compatibilidad con Lectores de Pantalla</h3>
        <ul>
          <li>Etiquetas ARIA descriptivas en todos los elementos interactivos</li>
          <li>Estructura semántica HTML5 apropiada</li>
          <li>Texto alternativo descriptivo en todas las imágenes</li>
          <li>Navegación por landmarks (regiones, navegación, principal)</li>
        </ul>

        <h3 className="h5 mt-4">3. Contraste de Color (WCAG AA)</h3>
        <ul>
          <li>Ratio de contraste mínimo 4.5:1 para texto normal</li>
          <li>Ratio de contraste mínimo 3:1 para texto grande</li>
          <li>Modo oscuro/claro con paletas optimizadas</li>
        </ul>

        <h3 className="h5 mt-4">4. Tamaño y Espaciado</h3>
        <ul>
          <li>Tamaño mínimo de objetivos táctiles: 44x44 píxeles</li>
          <li>Controles de zoom integrados (aumentar/disminuir fuente)</li>
          <li>Compatible con zoom del navegador hasta 200%</li>
        </ul>
      </section>

      <section className="mb-5 accessibility-callouts" aria-labelledby="controls">
        <div>
        <h2 id="controls">Controles de Accesibilidad</h2>
        <p>Panel lateral derecho con:</p>
        <ul>
          <li><strong>Tema:</strong> Cambia entre modo claro y oscuro</li>
          <li><strong>Idioma:</strong> Selecciona tu idioma preferido</li>
          <li><strong>Zoom:</strong> Aumenta, disminuye o restablece el tamaño de fuente</li>
        </ul>
        </div>
        <div>
          <h3 className="h5 mt-4">Compatibilidad probada</h3>
          <p>Probamos con NVDA 2024, VoiceOver en iOS y TalkBack en Android. Realizamos auditorías trimestrales con axe y Lighthouse.</p>
        </div>
      </section>

      <section className="mb-5 accessibility-panel" aria-labelledby="feedback">
        <h2 id="feedback">Retroalimentación</h2>
        <p>
          Si encuentras problemas de accesibilidad, contáctanos en{' '}
          <a href="mailto:accesibilidad@fitter.com">accesibilidad@fitter.com</a> o agenda una videollamada con nuestro equipo de soporte inclusivo.
        </p>
      </section>

      <section className="mb-5 accessibility-panel" aria-labelledby="date">
        <h2 id="date">Última Actualización</h2>
        <p><time dateTime="2025-11-24">24 de noviembre de 2025</time></p>
      </section>
    </main>
  );
}
