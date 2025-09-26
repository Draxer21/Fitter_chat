import { useEffect, useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_index.css";

export default function HomePage() {
  const { search } = useLocation();
  const categoria = useMemo(() => new URLSearchParams(search).get("categoria") || "", [search]);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    const q = categoria ? `?categoria=${encodeURIComponent(categoria)}` : "";
    API.productos.list(q).then(setItems).catch(e => setErr(e.message)).finally(()=>setLoading(false));
  }, [categoria]);

  const add = async (id) => { try { await API.carrito.add(id); } catch(e){ alert(e.message); } };

  return (
    <main className="flex-grow-1">
      <h2 style={{ textAlign: "center", margin: "20px 0 50px 0" }}>
        Nuestras Ofertas{categoria ? ` en ${categoria}` : ""}
      </h2>

      {loading && <div className="container">Cargando…</div>}
      {err && <div className="container text-danger">Error: {err}</div>}

      <div className="productos">
        {items.map(p => (
          <div key={p.id} className="producto">
            <Link to={`/producto/${p.id}`}>
              <img src="/fitter_logo.png" alt={p.nombre} />
              <h4>{p.nombre}</h4>
              <p>Categoría: {p.categoria || "—"}</p>
              <p>Disponibilidad: {p.stock}</p>
              <p>Precio: ${p.precio.toFixed(2)}</p>
            </Link>
            <button className="btn btn-primary" onClick={() => add(p.id)}>Añadir al Carrito</button>
          </div>
        ))}
        {!loading && items.length === 0 && <p>No hay productos o servicios disponibles.</p>}
      </div>
    </main>
  );
}
