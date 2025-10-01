import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_detalle.css";
import Logo from "../components/Logo";
import { formatearPrecio } from "../utils/formatPrice";

const stockDisponible = (valor) => {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
};

export default function ProductoDetalle() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    API.productos
      .get(id)
      .then(setP)
      .catch((e) => setErr(e.message));
  }, [id]);

  const add = async () => {
    if (!p) return;
    try {
      await API.carrito.add(p.id);
    } catch (e) {
      alert(e.message);
    }
  };

  if (err) return <div className="container text-danger">Error: {err}</div>;
  if (!p) return <div className="container">Cargando…</div>;

  const disponible = stockDisponible(p.stock);
  const sinStock = disponible <= 0;

  return (
    <main>
      <div className="container">
        <div className="producto-detalle">
          <h1>{p.nombre}</h1>
          <Logo src="/fitter_logo.png" style={{ width: 300, height: 300 }} alt={p.nombre} />
          <p className="categoria">Categoría: {p.categoria || "—"}</p>
          <p className="categoria">Disponibilidad: {disponible}</p>
          <p className="precio">Precio: {formatearPrecio(p.precio)}</p>
          <p className="descripcion">{p.descripcion || ""}</p>
          <button className="btn btn-primary" disabled={sinStock} onClick={() => { if (!sinStock) add(); }}>
            {sinStock ? "Sin stock" : "Añadir al Carrito"}
          </button>
        </div>
      </div>
    </main>
  );
}
