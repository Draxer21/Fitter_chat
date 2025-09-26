import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark custom-navbar p-3">
      <NavLink className="navbar-brand" to="/">
        <img src="/fitter_logo.png" alt="Fitter" width="120" height="60" className="d-inline-block align-text-top" />
      </NavLink>

      <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown"
        aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
        <span className="navbar-toggler-icon" />
      </button>

      <div className="collapse navbar-collapse" id="navbarNavDropdown">
        <ul className="navbar-nav">
          <li className="nav-item"><NavLink className="nav-link" to="/">Inicio</NavLink></li>

          <li className="nav-item dropdown">
            <a className="nav-link dropdown-toggle" href="#!" id="navbarDropdownMenuLink" role="button"
               data-bs-toggle="dropdown" aria-expanded="false">
              Productos y Servicios
            </a>
            <div className="dropdown-menu" aria-labelledby="navbarDropdownMenuLink">
              <NavLink className="dropdown-item" to="/?categoria=Membership">Membresías</NavLink>
              <NavLink className="dropdown-item" to="/?categoria=Personal%20Training">Entrenamiento Personal</NavLink>
              <NavLink className="dropdown-item" to="/?categoria=Supplements">Suplementos</NavLink>
              <NavLink className="dropdown-item" to="/?categoria=Merchandise">Mercancía</NavLink>
            </div>
          </li>

          <li className="nav-item"><NavLink className="nav-link" to="/admin/productos">Control de Inventario</NavLink></li>
          <li className="nav-item"><NavLink className="nav-link" to="/admin/productos/nuevo">Añadir Producto/Servicio</NavLink></li>
          <li className="nav-item"><a className="nav-link" href="#!" data-bs-toggle="modal" data-bs-target="#soporteModal">Soporte</a></li>
          <li className="nav-item"><NavLink className="nav-link" to="/login">Acceso de Administrador</NavLink></li>
        </ul>

        <ul className="navbar-nav ms-auto">
          <li className="nav-item">
            <NavLink className="nav-link" to="/carrito" aria-label="Carrito de Compras">
              <i className="fa-solid fa-cart-shopping fa-2x" style={{ color: "#ffffff" }} />
            </NavLink>
          </li>
        </ul>
      </div>

      {/* Modal soporte (simplificado) */}
      <div className="modal fade" id="soporteModal" tabIndex={-1} aria-labelledby="soporteLabel" aria-hidden="true">
        <div className="modal-dialog"><div className="modal-content">
          <div className="modal-header" style={{ backgroundColor: "black" }}>
            <h1 className="modal-title fs-5" id="soporteLabel" style={{ color: "#ffffff" }}>Contactar Soporte</h1>
            <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close" style={{ backgroundColor: "#ffffff" }} />
          </div>
          <div className="modal-body">
            <strong><a href="https://api.whatsapp.com/send/?phone=945747265&text&type=phone_number&app_absent=0" style={{ textDecoration: "none" }}>
              <i className="fa-brands fa-whatsapp" /> +1 (555) 123-4567</a></strong><br /><br />
            <strong><a href="#!" style={{ textDecoration: "none" }}>
              <i className="fa-solid fa-phone" /> +1 (555) 123-4567 24/7</a></strong><br /><br />
            <strong><a href="#!" style={{ textDecoration: "none" }}>
              <i className="fa-solid fa-envelope" /> support@fittergym.com</a></strong><br /><br /><br />
            <h4>Ticket de Soporte</h4>
            <form>
              <div className="form-group">
                <label htmlFor="ticketEmail">Correo Electrónico</label>
                <input className="form-control" id="ticketEmail" placeholder="Introduce tu correo" />
              </div>
              <div className="form-group">
                <label htmlFor="ticketDesc">Describe tu problema</label>
                <textarea className="form-control" id="ticketDesc" rows={3} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop: 8 }}>Enviar</button>
            </form>
          </div>
        </div></div>
      </div>
    </nav>
  );
}
