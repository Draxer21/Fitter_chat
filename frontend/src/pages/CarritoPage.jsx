import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/carrito/style_carrito.css";

export default function CarritoPage() {
  const nav = useNavigate();
  const [state, setState] = useState({ items: {}, total: 0, unidades: 0 });

  const load = () => API.carrito.estado().then(setState);
  useEffect(() => { load(); }, []);

  const inc = (id) => API.carrito.add(id).then(load);
  const dec = (id) => API.carrito.dec(id).then(load);
  const del = (id) => API.carrito.remove(id).then(load);
  const clear = () => API.carrito.clear().then(load);
  const validar = async () => {
    const r = await API.carrito.validar();
    if (r?.exito) nav("/boleta");
    else if (r?.errores) alert(r.errores.join("\n"));
    else alert("Error validando.");
  };

  const items = Object.values(state.items || {});
  return (
    <div className="legacy-scope" style={{ padding: 16 }}>
      <h2>Carrito</h2>
      {items.length === 0 ? (
        <p>Tu carrito está vacío.</p>
      ) : (
        <table className="tabla-carrito">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Cant.</th>
              <th>PU</th>
              <th>Total</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.producto_id}>
                <td>{it.nombre}</td>
                <td>
                  <button onClick={() => dec(it.producto_id)}>-</button>
                  <span style={{ margin: "0 8px" }}>{it.cantidad}</span>
                  <button onClick={() => inc(it.producto_id)}>+</button>
                </td>
                <td>${it.precio_unitario.toFixed(2)}</td>
                <td>${it.acumulado.toFixed(2)}</td>
                <td>
                  <button onClick={() => del(it.producto_id)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 12 }}>
        <strong>Total: ${Number(state.total || 0).toFixed(2)}</strong>
      </div>
      <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
        <button onClick={clear}>Limpiar</button>
        <button onClick={validar}>Validar compra</button>
      </div>
    </div>
  );
}
