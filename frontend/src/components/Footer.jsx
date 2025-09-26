export default function Footer() {
  return (
    <footer className="footer">
      <div className="container-footer">
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
              <a href="#!"><i className="fab fa-facebook-f" /></a>
              <a href="#!"><i className="fab fa-instagram" /></a>
              <a href="#!"><i className="fab fa-twitter" /></a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
