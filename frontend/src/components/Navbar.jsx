import { NavLink } from "react-router-dom";

const link = {
  color: "gainsboro",
  textDecoration: "none",
  marginRight: 12,
};

export default function Navbar() {
  return (
    <nav className="custom-navbar" style={{ padding: "10px 16px" }}>
      <NavLink to="/" style={{ ...link, fontWeight: 700, color: "#fff" }}>
        Fitter
      </NavLink>
      <NavLink to="/tienda" style={link}>Tienda</NavLink>
      <NavLink to="/carrito" style={link}>Carrito</NavLink>
      <NavLink to="/admin/productos" style={link}>Productos</NavLink>
      <NavLink to="/login" style={link}>Login</NavLink>
    </nav>
  );
}
