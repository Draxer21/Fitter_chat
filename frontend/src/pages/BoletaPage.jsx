import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { API } from "../services/apijs";

export default function BoletaPage() {
  const location = useLocation();
  const orderId = useMemo(() => new URLSearchParams(location.search).get("order"), [location.search]);
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    API.carrito.boleta(orderId).then(setData).catch((e) => setErr(e.message));
  }, [orderId]);

  const carrito = useMemo(() => data?.carrito || {}, [data]);
  const items = useMemo(() => Object.values(carrito.items || data?.items || {}), [carrito, data]);
  const total = useMemo(() => carrito.total ?? data?.total_carrito ?? data?.total ?? 0, [carrito, data]);

  if (err) return <div style={{ padding: 16, color: "#b91c1c" }}>{err}</div>;
  if (!data) return <div style={{ padding: 16 }}>Generando boleta…</div>;

  return (
    <div className="legacy-scope" style={{ padding: 16 }}>
      <h2>Boleta</h2>
      <p>Fecha: {data.fecha}</p>
      <table>
        <thead>
          <tr>
            <th>Producto</th>
            <th>Cant.</th>
            <th>PU</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.producto_id}>
              <td>{it.nombre}</td>
              <td>{it.cantidad}</td>
              <td>${Number(it.precio_unitario || 0).toFixed(2)}</td>
              <td>${Number(it.acumulado || 0).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Total: ${Number(total || 0).toFixed(2)}</h3>
    </div>
  );
}




