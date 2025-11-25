import React from 'react';

export default function AccessibilityPage() {
  return (
    <main className="container py-5">
      <h1 className="mb-4">Declaración de Accesibilidad</h1>
      
      <section className="mb-5" aria-labelledby="commitment">
        <h2 id="commitment">Nuestro Compromiso</h2>
        <p>
          En <strong>Fitter</strong>, nos comprometemos a garantizar que nuestra plataforma sea accesible 
          para todas las personas, independientemente de sus capacidades. Seguimos las pautas de accesibilidad 
          del contenido web <strong>WCAG 2.1 nivel AA</strong>.
        </p>
      </section>

      <section className="mb-5" aria-labelledby="features">
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

      <section className="mb-5" aria-labelledby="controls">
        <h2 id="controls">Controles de Accesibilidad</h2>
        <p>Panel lateral derecho con:</p>
        <ul>
          <li><strong>Tema:</strong> Cambia entre modo claro y oscuro</li>
          <li><strong>Idioma:</strong> Selecciona tu idioma preferido</li>
          <li><strong>Zoom:</strong> Aumenta, disminuye o restablece el tamaño de fuente</li>
        </ul>
      </section>

      <section className="mb-5" aria-labelledby="feedback">
        <h2 id="feedback">Retroalimentación</h2>
        <p>
          Si encuentras problemas de accesibilidad, contáctanos en{' '}
          <a href="mailto:accesibilidad@fitter.com">accesibilidad@fitter.com</a>
        </p>
      </section>

      <section className="mb-5" aria-labelledby="date">
        <h2 id="date">Última Actualización</h2>
        <p><time dateTime="2025-11-24">24 de noviembre de 2025</time></p>
      </section>
    </main>
  );
}
