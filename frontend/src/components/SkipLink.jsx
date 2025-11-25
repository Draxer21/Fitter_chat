import React from 'react';

/**
 * SkipLink - Componente de accesibilidad que permite a usuarios de teclado
 * y lectores de pantalla saltar directamente al contenido principal.
 * 
 * Cumple con WCAG 2.1 - Criterio 2.4.1 (Bypass Blocks)
 */
export default function SkipLink({ targetId = 'main-content', text = 'Saltar al contenido principal' }) {
  const handleClick = (e) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <a 
      href={`#${targetId}`} 
      className="skip-link"
      onClick={handleClick}
      tabIndex={0}
    >
      {text}
    </a>
  );
}
