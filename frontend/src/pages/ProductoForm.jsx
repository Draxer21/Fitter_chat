import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_agregar_producto.css";

export default function ProductoForm() {
  const nav = useNavigate();
  const [f, setF] = useState({ nombre:"", precio:0, descripcion:"", categoria:"", stock:0 });
  const [err, setErr] = useState("");

  const save = async(e)=>{
    e.preventDefault(); setErr("");
    try{
      await API.productos.create(f);
      nav("/admin/productos");
    }catch(ex){ setErr(ex.message); }
  };

  return (
    <div className="container mt-5">
      <center><h1 style={{marginBottom: 80}}>Añadir Producto/Servicio</h1></center>

      <form onSubmit={save} style={{marginBottom: 80}}>
        <div className="table-responsive">
          <table className="table">
            <tbody>
              <tr><th>Nombre</th><td><input className="form-control" value={f.nombre} onChange={e=>setF({...f, nombre:e.target.value})} required /></td></tr>
              <tr><th>Precio</th><td><input className="form-control" type="number" step="0.01" value={f.precio} onChange={e=>setF({...f, precio:+e.target.value})} required /></td></tr>
              <tr><th>Descripción</th><td><textarea className="form-control" value={f.descripcion} onChange={e=>setF({...f, descripcion:e.target.value})} /></td></tr>
              <tr><th>Categoría</th><td><input className="form-control" value={f.categoria} onChange={e=>setF({...f, categoria:e.target.value})} /></td></tr>
              <tr><th>Stock</th><td><input className="form-control" type="number" value={f.stock} onChange={e=>setF({...f, stock:+e.target.value})} required /></td></tr>
            </tbody>
          </table>
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        <div className="d-flex justify-content-between">
          <Link to="/admin/productos" className="btn btn-secondary">VOLVER</Link>
          <button type="submit" className="btn btn-success">Guardar</button>
        </div>
      </form>
    </div>
  );
}
