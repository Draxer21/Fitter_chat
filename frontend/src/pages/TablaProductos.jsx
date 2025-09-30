import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_tabla_productos.css";
import Logo from "../components/Logo";

export default function TablaProductos() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const load = ()=> API.productos.list().then(setItems).catch(e=>setErr(e.message));
  useEffect(()=>{
    let mounted = true;
    // comprobar privilegios admin
    API.auth.me().then(r=>{ if(!r?.is_admin) nav('/login'); else { if(mounted) load(); } }).catch(()=>nav('/login'));
    return ()=>{ mounted = false; };
  }, []);

  const del = async(id) => { if(window.confirm("¿Eliminar producto?")){ await API.productos.del(id); load(); } };

  return (
    <main className="flex-grow-1">
      <div className="container">
        <h1>Gestión de Inventario</h1>
        <div className="d-flex justify-content-end mb-2">
          <Link to="/admin/productos/nuevo" className="btn btn-success">Añadir Producto/Servicio</Link>
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        <div className="table-responsive">
          <table className="table table-dark table-striped table-bordered">
            <thead>
              <tr>
                <th>ID</th><th>Nombre</th><th>Precio</th>
                <th>Descripción</th><th>Categoría</th><th>Stock</th><th>Imagen</th><th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map(pr=>(
                <tr key={pr.id}>
                  <td>{pr.id}</td>
                  <td>{pr.nombre}</td>
                  <td>{pr.precio.toFixed(2)}</td>
                  <td>{pr.descripcion || ""}</td>
                  <td>{pr.categoria || ""}</td>
                  <td>{pr.stock}</td>
                  <td><Logo src="/fitter_logo.png" alt="" style={{width:40}} /></td>
                  <td className="text-center">
                    <div className="d-flex justify-content-center">
                      {/* Link de edición opcional */}
                      {/* <Link to={`/admin/productos/${pr.id}`} className="btn btn-warning me-2"><i className="fa-solid fa-pencil" /></Link> */}
                      <button className="btn btn-danger" onClick={()=>del(pr.id)}><i className="fa-solid fa-trash" /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length===0 && <tr><td colSpan={8} className="text-center">Sin productos</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
