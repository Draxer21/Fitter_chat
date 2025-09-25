import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_index.css";
import "../styles/legacy/producto/style_detalle.css";

export default function TiendaPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    API.productos
      .list()
      .then(setItems)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  const add = async (id) => {
    try {
      await API.carrito.add(id);
    } catch (e) {
      alert(e.message);
    }
  };

  if (loading) return <div style={{ padding: 16 }}>Cargando productos…</div>;
  if (err) return <div style={{ padding: 16, color: "#b91c1c" }}>{err}</div>;

  return (
    <div className="legacy-scope" style={{ padding: 16 }}>
      <h2>Productos</h2>
      <div className="productos">
        {items.map((p) => (
          <div key={p.id} className="producto">
            {/* Usa una imagen genérica; ajusta si más adelante sirves una por producto */}
            <img src="/fitter_logo.png" alt="Producto" />
            <h4 title={p.nombre}>{p.nombre}</h4>
            <p className="precio">${p.precio.toFixed(2)}</p>
            <p>Stock: {p.stock}</p>
            <button onClick={() => add(p.id)}>Agregar</button>
          </div>
        ))}
      </div>
    </div>
  );
}
