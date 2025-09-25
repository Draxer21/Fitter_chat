import { useEffect, useState } from "react";
import { API } from "../services/apijs";

export default function BoletaPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    API.carrito.boleta().then(setData).catch((e) => setErr(e.message));
  }, []);

  if (err) return <div style={{ padding: 16, color: "#b91c1c" }}>{err}</div>;
  if (!data) return <div style={{ padding: 16 }}>Generando boleta…</div>;

  const items = Object.values(data.items || {});
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
              <td>${it.precio_unitario.toFixed(2)}</td>
              <td>${it.acumulado.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Total: ${data.total.toFixed(2)}</h3>
    </div>
  );
}
