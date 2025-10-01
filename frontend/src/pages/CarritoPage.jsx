import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/carrito/style_carrito.css";
import { formatearPrecio } from "../utils/formatPrice";

const estadoInicial = { items: {}, total: 0 };

export default function CarritoPage() {
  const [state, setState] = useState(estadoInicial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const data = await API.carrito.estado();
      setState(data || estadoInicial);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const applyAndSet = (data) => {
    if (data?.carrito) {
      setState(data.carrito);
    } else if (data) {
      setState(data);
    }
  };

  const inc = async (id) => {
    try {
      const data = await API.carrito.add(id);
      applyAndSet(data);
    } catch (e) {
      alert(e.message);
    }
  };

  const dec = async (id) => {
    try {
      const data = await API.carrito.dec(id);
      applyAndSet(data);
    } catch (e) {
      alert(e.message);
    }
  };

  const del = async (id) => {
    try {
      const data = await API.carrito.remove(id);
      applyAndSet(data);
    } catch (e) {
      alert(e.message);
    }
  };

  const cls = async () => {
    try {
      const data = await API.carrito.clear();
      applyAndSet(data);
    } catch (e) {
      alert(e.message);
    }
  };

  const buy = async () => {
    try {
      const me = await API.auth.me();
      if (!me || me?.error) {
        setShowLoginPrompt(true);
        return;
      }
    } catch (e) {
      setShowLoginPrompt(true);
      return;
    }

    try {
      const r = await API.carrito.validar();
      if (r?.errores) {
        alert(r.errores.join("\n"));
      } else if (r?.error) {
        alert(r.error);
      } else {
        applyAndSet(r);
        window.location.href = "/boleta";
      }
    } catch (e) {
      alert(e.message);
    }
  };

  const rows = Object.values(state.items || {});

  return (
    <div className="container" style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div className="alert" role="alert" style={{ backgroundColor: "rgba(0,0,0,0.904)" }}>
        <div className="table-responsive">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th scope="row" colSpan={5} className="text-center">
                  CARRITO
                </th>
              </tr>
              <tr>
                <th>NOMBRE</th>
                <th>CANTIDAD</th>
                <th>PRECIO UNITARIO</th>
                <th>PRECIO TOTAL DEL PRODUCTO</th>
                <th>ELIMINAR/AGREGAR</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={5} className="text-center">
                    Cargando…
                  </td>
                </tr>
              )}
              {!loading && error && (
                <tr>
                  <td colSpan={5} className="text-center text-danger">
                    {error}
                  </td>
                </tr>
              )}
              {!loading && !error && rows.length > 0 &&
                rows.map((v) => (
                  <tr key={v.producto_id}>
                    <td>{v.nombre}</td>
                    <td>{v.cantidad}</td>
                    <td>{formatearPrecio(v.precio_unitario)}</td>
                    <td>{formatearPrecio(v.acumulado)}</td>
                    <td>
                      <button onClick={() => dec(v.producto_id)} className="badge btn btn-dark badge-dark">
                        -
                      </button>{" "}
                      <button onClick={() => inc(v.producto_id)} className="badge btn btn-dark badge-dark">
                        +
                      </button>{" "}
                      <button onClick={() => del(v.producto_id)} className="badge btn btn-danger">
                        x
                      </button>
                    </td>
                  </tr>
                ))}
              {!loading && !error && rows.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <div className="alert alert-danger text-center">Sin Productos</div>
                  </td>
                </tr>
              )}
              <tr>
                <th scope="row">Total:</th>
                <td colSpan={4}>{formatearPrecio(state.total || 0)}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <hr />
      </div>

      <div className="row text-center">
        <div className="col-6">
          <button onClick={cls} className="btn btn-danger">
            Limpiar
          </button>
        </div>
        <div className="col-6">
          <button onClick={buy} className="btn btn-success">
            Hacer Compra
          </button>
        </div>
      </div>

      {showLoginPrompt && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog" style={{ backgroundColor: "transparent" }}>
            <div className="modal-dialog modal-dialog-centered" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Necesitas iniciar sesión</h5>
                  <button type="button" className="btn-close" aria-label="Close" onClick={() => setShowLoginPrompt(false)} />
                </div>
                <div className="modal-body">
                  <p>Para completar la compra debes iniciar sesión. ¿Deseas ir al formulario de inicio de sesión ahora?</p>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowLoginPrompt(false)}>
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      window.location.href = "/login?next=/carrito";
                    }}
                  >
                    Ir a Login
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show" style={{ opacity: 0.5 }} />
        </>
      )}
    </div>
  );
}
