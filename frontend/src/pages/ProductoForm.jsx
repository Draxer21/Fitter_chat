import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_agregar_producto.css";

export default function ProductoForm() {
  const nav = useNavigate();
  const CATEGORIES = ["Membership", "Personal Training", "Supplements", "Merchandise"];
  const [f, setF] = useState({ nombre:"", precio:0, descripcion:"", categoria: CATEGORIES[0], stock:0 });
  const [err, setErr] = useState("");
  const [imagenFile, setImagenFile] = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(()=>{
    API.auth.me().then(r=>{ if(!r?.is_admin) nav('/login'); }).catch(()=>nav('/login'));
  }, []);

  const save = async(e)=>{
    e.preventDefault(); setErr("");
    try{
      // Si hay archivo, crear FormData
      if (imagenFile) {
        const fd = new FormData();
        fd.append('nombre', f.nombre);
        fd.append('precio', f.precio);
        fd.append('descripcion', f.descripcion || '');
        fd.append('categoria', f.categoria || '');
        fd.append('stock', f.stock || 0);
        fd.append('imagen', imagenFile, imagenFile.name);
        await API.productos.create(fd);
      } else {
        await API.productos.create(f);
      }
      nav("/admin/productos");
    }catch(ex){ setErr(ex.message); }
  };

  const onFile = (ev) => {
    const file = ev.target.files && ev.target.files[0];
    setImagenFile(file || null);
    if (file) {
      const url = URL.createObjectURL(file);
      setPreview(url);
    } else {
      setPreview(null);
    }
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
              <tr>
                <th>Categoría</th>
                <td>
                  <select className="form-control" value={f.categoria} onChange={e=>setF({...f, categoria:e.target.value})}>
                    {CATEGORIES.map(c=> <option key={c} value={c}>{c}</option>)}
                  </select>
                </td>
              </tr>
              <tr><th>Stock</th><td><input className="form-control" type="number" value={f.stock} onChange={e=>setF({...f, stock:+e.target.value})} required /></td></tr>
              <tr><th>Imagen</th><td><input type="file" accept="image/*" onChange={onFile} className="form-control" /></td></tr>
            </tbody>
          </table>
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        {preview && (
          <div className="mb-3">
            <label>Previsualización</label>
            <div><img src={preview} alt="preview" style={{maxWidth: 200, maxHeight: 200}}/></div>
          </div>
        )}

        <div className="d-flex justify-content-between">
          <Link to="/admin/productos" className="btn btn-secondary">VOLVER</Link>
          <button type="submit" className="btn btn-success">Guardar</button>
        </div>
      </form>
    </div>
  );
}
