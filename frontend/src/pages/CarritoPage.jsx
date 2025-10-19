import { useEffect, useState } from "react";
import "../styles/legacy/carrito/style_carrito.css";
import { formatearPrecio } from "../utils/formatPrice";
import { useCart } from "../contexts/CartContext";
import { useAuth } from "../contexts/AuthContext";

export default function CarritoPage() {
  const { items, total, refresh, addItem, decrementItem, removeItem, clearCart, status, error } = useCart();
  const { isAuthenticated, refresh: refreshAuth } = useAuth();
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const handleMutation = async (runner) => {
    setActionError("");
    try {
      await runner();
    } catch (err) {
      setActionError(err?.message || "No se pudo actualizar el carrito.");
    }
  };

  const handleInc = (id) => handleMutation(() => addItem(id));
  const handleDec = (id) => handleMutation(() => decrementItem(id));
  const handleRemove = (id) => handleMutation(() => removeItem(id));
  const handleClear = () => handleMutation(() => clearCart());

  const buy = async () => {
    try {
      let authed = isAuthenticated;
      if (!authed) {
        const result = await refreshAuth().catch(() => null);
        authed = Boolean(result?.auth);
      }
      if (!authed) {
        setShowLoginPrompt(true);
        return;
      }
    } catch {
      setShowLoginPrompt(true);
      return;
    }
    window.location.href = "/pago";
  };

  const isLoading = status === "loading";
  const isUpdating = status === "updating";
  const generalError = error?.message || "";
  const errorMessage = actionError || generalError;
  const rows = Array.isArray(items) ? items : [];
  const totalValue = Number(total) || 0;

  return (
    <div className="cart-container">
      <h1 className="cart-title">CARRITO</h1>

      {isLoading && <div className="loading-cart">Cargando...</div>}

      {errorMessage && <div className="error-cart">{errorMessage}</div>}

      {!isLoading && !errorMessage && rows.length === 0 && (
        <div className="empty-cart">Sin Productos</div>
      )}

      {!isLoading && !errorMessage && rows.length > 0 && (
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
                  <button onClick={() => handleDec(v.producto_id)} className="quantity-btn" disabled={isUpdating}>
                    -
                  </button>
                  <span className="quantity-display">{v.cantidad}</span>
                  <button onClick={() => handleInc(v.producto_id)} className="quantity-btn" disabled={isUpdating}>
                    +
                  </button>
                  <button onClick={() => handleRemove(v.producto_id)} className="remove-btn" disabled={isUpdating}>
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          ))}

          <div className="cart-summary">
            <div className="cart-total">Total: {formatearPrecio(totalValue)}</div>
            <div className="cart-actions">
              <button onClick={handleClear} className="action-btn clear-btn" disabled={isUpdating}>
                Limpiar
              </button>
              <button onClick={buy} className="action-btn checkout-btn" disabled={isUpdating}>
                Hacer Compra
              </button>
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
                  <h5 className="modal-title">Necesitas iniciar sesion</h5>
                  <button type="button" className="btn-close" aria-label="Close" onClick={() => setShowLoginPrompt(false)} />
                </div>
                <div className="modal-body">
                  <p>Para completar la compra debes iniciar sesion. Deseas ir al formulario de inicio de sesion ahora?</p>
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
