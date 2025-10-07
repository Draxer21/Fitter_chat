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

    // Redirect to payment page
    window.location.href = "/pago";
  };

  const rows = Object.values(state.items || {});

  return (
    <div className="cart-container">
      <h1 className="cart-title">CARRITO</h1>

      {loading && <div className="loading-cart">Cargando…</div>}

      {error && <div className="error-cart">{error}</div>}

      {!loading && !error && rows.length === 0 && (
        <div className="empty-cart">Sin Productos</div>
      )}

      {!loading && !error && rows.length > 0 && (
        <>
          {rows.map((v) => (
            <div key={v.producto_id} className="cart-item">
              <img
                src={v.imagen || "/placeholder.jpg"}
                alt={v.nombre}
                className="cart-item-image"
              />
              <div className="cart-item-details">
                <div className="cart-item-name">{v.nombre}</div>
                <div className="cart-item-price">
                  Precio unitario: {formatearPrecio(v.precio_unitario)} | Total: {formatearPrecio(v.acumulado)}
                </div>
                <div className="cart-item-controls">
                  <button onClick={() => dec(v.producto_id)} className="quantity-btn">-</button>
                  <span className="quantity-display">{v.cantidad}</span>
                  <button onClick={() => inc(v.producto_id)} className="quantity-btn">+</button>
                  <button onClick={() => del(v.producto_id)} className="remove-btn">Eliminar</button>
                </div>
              </div>
            </div>
          ))}

          <div className="cart-summary">
            <div className="cart-total">Total: {formatearPrecio(state.total || 0)}</div>
            <div className="cart-actions">
              <button onClick={cls} className="action-btn clear-btn">Limpiar</button>
              <button onClick={buy} className="action-btn checkout-btn">Hacer Compra</button>
            </div>
          </div>
        </>
      )}

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
