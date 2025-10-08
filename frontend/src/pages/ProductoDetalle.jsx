import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_detalle.css";
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
  if (!p) return <div className="container">Cargando.</div>;

  const disponible = stockDisponible(p.stock);
  const sinStock = disponible <= 0;
  const imageSrc = p.imagen_url || "/fitter_logo.png";

  return (
    <main>
      <div className="container">
        <div className="producto-detalle">
          <h1>{p.nombre}</h1>
          <img src={imageSrc} alt={p.nombre} style={{ maxWidth: 300, maxHeight: 300, objectFit: "cover" }} />
          <p className="categoria">Categoría: {p.categoria || "-"}</p>
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
