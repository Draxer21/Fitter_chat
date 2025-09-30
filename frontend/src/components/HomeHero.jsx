import React from 'react';
import '../styles/hero.css';

export default function HomeHero() {
  const style = {
    backgroundImage: "linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)), url('/gym.jpg')",
    backgroundSize: 'cover',
    backgroundPosition: 'center center'
  };

  return (
    <header className="home-hero" style={style}>
      <div className="hero-overlay" />
      <div className="hero-inner container">
        <div className="hero-content">
          <h1 className="hero-title"><span className="muted">CONSTRUYE</span> <span className="highlight">TU CUERPO</span></h1>
          <h2 className="hero-sub">TRANSFORMA <strong>TU VIDA</strong></h2>
          <p className="hero-desc">Quien esta fumando conchesumare</p>
          <div className="hero-cta">
            <a className="btn btn-outline-dark btn-lg" href="/registro">PRUEBA GRATIS</a>
          </div>
        </div>
      </div>

      <div className="hero-features container">
        <div className="row">
          <div className="col-md-3 feature">
            <h5>EL MEJOR ENTRENAMIENTO</h5>
            <p>Entrenamientos diseñados para maximizar tus resultados con profesionales a tu lado.</p>
          </div>
          <div className="col-md-3 feature">
            <h5>IA ENTRENADA</h5>
            <p>Nuestra ia es la mejor.</p>
          </div>
          <div className="col-md-3 feature">
            <h5>GIMNASIO DE ALTA TECNOLOGÍA</h5>
            <p>Instalaciones modernas y tecnología.</p>
          </div>
          <div className="col-md-3 feature">
            <h5>MIEMBROS SATISFECHOS</h5>
            <p>Únete a una comunidad motivadora y comprueba los resultados por ti mismo.</p>
          </div>
        </div>
      </div>
    </header>
  );
}
