import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_tabla_productos.css";
import "../styles/legacy/tabla_productos/style_agregar_producto.css";

export default function TablaProductos() {
  const [items, setItems] = useState([]);
  const [f, setF] = useState({ nombre: "", precio: 0, stock: 0 });
  const [err, setErr] = useState("");

  const load = () =>
    API.productos
      .list()
      .then(setItems)
      .catch((e) => setErr(e.message));

  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await API.productos.create(f);
      setF({ nombre: "", precio: 0, stock: 0 });
      load();
    } catch (e) {
      setErr(e.message);
    }
  };

  const del = async (id) => {
    if (!window.confirm("¿Eliminar producto?")) return;
    await API.productos.del(id);
    load();
  };

  return (
    <div className="legacy-scope" style={{ padding: 16 }}>
      <h2>Productos (admin)</h2>

      <form onSubmit={save} className="form-agregar">
        <input
          placeholder="Nombre"
          value={f.nombre}
          onChange={(e) => setF({ ...f, nombre: e.target.value })}
          required
        />
        <input
          type="number"
          step="0.01"
          placeholder="Precio"
          value={f.precio}
          onChange={(e) => setF({ ...f, precio: +e.target.value })}
          required
        />
        <input
          type="number"
          placeholder="Stock"
          value={f.stock}
          onChange={(e) => setF({ ...f, stock: +e.target.value })}
          required
        />
        <button>Agregar</button>
      </form>

      {err && <div style={{ color: "#b91c1c", marginTop: 8 }}>{err}</div>}

      <table className="tabla-productos" style={{ marginTop: 12 }}>
        <thead>
          <tr><th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th><th /></tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.nombre}</td>
              <td>${p.precio.toFixed(2)}</td>
              <td>{p.stock}</td>
              <td><button onClick={() => del(p.id)}>Eliminar</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
