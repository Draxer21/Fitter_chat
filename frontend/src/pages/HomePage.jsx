import { useEffect, useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_index.css";
import HomeHero from "../components/HomeHero";
import Memberships from "../components/Memberships";
import Logo from "../components/Logo";
import { formatearPrecio } from "../utils/formatPrice";

const stockDisponible = (valor) => {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
};

export default function HomePage() {
  const { search } = useLocation();
  const categoria = useMemo(() => new URLSearchParams(search).get("categoria") || "", [search]);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    const q = categoria ? `?categoria=${encodeURIComponent(categoria)}` : "";
    API.productos
      .list(q)
      .then(setItems)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [categoria]);

  const add = async (id) => {
    try {
      await API.carrito.add(id);
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <main className="flex-grow-1">
      <HomeHero />

      <section className="container py-5">
        <h2 style={{ textAlign: "center", margin: "20px 0 50px 0" }}>
          Nuestras Ofertas{categoria ? ` en ${categoria}` : ""}
        </h2>

        {loading && <div className="container">Cargando.</div>}
        {err && <div className="container text-danger">Error: {err}</div>}

        <div className="productos">
          {items.map((p) => {
            const disponible = stockDisponible(p.stock);
            const sinStock = disponible <= 0;
            const imageSrc = p.imagen_url || "/fitter_logo.png";
            return (
              <div key={p.id} className="producto">
                <Link to={`/producto/${p.id}`}>
                  <Logo src={imageSrc} alt={p.nombre} className="producto__imagen" />
                  <h4>{p.nombre}</h4>
                  <p>Categoría: {p.categoria || "-"}</p>
                  <p>Disponibilidad: {disponible}</p>
                  <p>Precio: {formatearPrecio(p.precio)}</p>
                </Link>
                <button
                  className="btn btn-primary"
                  disabled={sinStock}
                  onClick={() => {
                    if (sinStock) return;
                    add(p.id);
                  }}
                >
                  {sinStock ? "Sin stock" : "Añadir al Carrito"}
                </button>
              </div>
            );
          })}
          {!loading && items.length === 0 && <p>No hay productos o servicios disponibles.</p>}
        </div>
      </section>

      <Memberships />
    </main>
  );
}
