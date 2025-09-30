export default function Footer() {
  return (
    <footer className="footer bg-dark text-light border-top-0">
      <div className="container-footer">
        {/* Top section: brand + tagline */}
        <div className="footer-section footer-top text-center">
          <div className="footer-brand">
            <h3 className="footer-logo"><span className="logo-fi">fi</span><span className="logo-tter">tter</span></h3>
            <p className="footer-tagline">Transforma tu vida con Fitter</p>
          </div>
        </div>

        <hr className="footer-separator" />

        {/* Middle section: links columns */}
        <div className="footer-section footer-middle">
          <div className="footer-row">
            <div className="footer-links">
              <h4>Fitter</h4>
              <ul>
                <li><a href="#!">Sobre Nosotros</a></li>
                <li><a href="#!">Ubicaciones</a></li>
              </ul>
            </div>

            <div className="footer-links">
              <h4>Dirección y Contacto</h4>
              <ul>
                <li>
                  <a href="https://www.google.com/maps/place/Gran+Av.+José+Miguel+Carrera+6543,+La+Cisterna">
                    123 Avenida Fitness <br /> Suite 101 <br /> Ciudad Gimnasio
                  </a>
                </li>
                <li><a href="#!">+1 (555) 123-4567</a></li>
              </ul>
            </div>

            <div className="footer-links">
              <h4>Redes Sociales</h4>
              <div className="social-links">
                <a href="#!" aria-label="Facebook"><i className="bi bi-facebook" /></a>
                <a href="#!" aria-label="Instagram"><i className="bi bi-instagram" /></a>
                <a href="#!" aria-label="Twitter"><i className="bi bi-twitter" /></a>
              </div>
            </div>
          </div>
        </div>

        <hr className="footer-separator" />

        {/* Bottom section: small print */}
        <div className="footer-section footer-bottom text-center">
          <small>© {new Date().getFullYear()} Fitter. Todos los derechos reservados.</small>
        </div>
      </div>
    </footer>
  );
}
