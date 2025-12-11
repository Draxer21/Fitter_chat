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
      
      // Llamar al endpoint de pago con MercadoPago
      setActionError("");
      const response = await fetch('/carrito/pagar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          // El backend tomará el nombre y email de la sesión
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setActionError(data.error || 'Error al procesar la compra');
        return;
      }

      // Redirigir a MercadoPago
      const paymentUrl = data.sandbox_payment_url || data.payment_url;
      if (paymentUrl) {
        window.location.href = paymentUrl;
      } else {
        setActionError('No se pudo obtener la URL de pago');
      }

    } catch (err) {
      setActionError(err?.message || 'Error al procesar la compra');
      setShowLoginPrompt(false);
    }
  };

  const isLoading = status === "loading";
  const isUpdating = status === "updating";
  const generalError = error?.message || "";
  const errorMessage = actionError || generalError;
  const rows = Array.isArray(items) ? items : [];
  const totalValue = Number(total) || 0;
  const hasItems = rows.length > 0;
  const totalUnits = rows.reduce((acc, v) => acc + (v.cantidad || 0), 0);

  return (
    <div className="cart-page">
      <section className="cart-hero">
        <div className="cart-hero-text">
          <p className="cart-hero-meta text-uppercase">Resumen de compra</p>
          <h1 className="cart-title">Carrito</h1>
          <p className="cart-hero-description">
            {hasItems
              ? "Verifica los productos agregados antes de finalizar tu pedido. Todos los pagos se procesan de forma segura."
              : "Aún no agregas productos. Explora nuestro catálogo y vuelve para completar tu compra."}
          </p>
          <div className="cart-hero-actions">
            <button className="cart-ghost-btn" onClick={() => (window.location.href = "/catalogo")}>
              Seguir explorando
            </button>
            {hasItems && (
              <button className="cart-primary-btn" onClick={buy} disabled={isUpdating}>
                Finalizar compra
              </button>
            )}
          </div>
        </div>
        <div className="cart-hero-stats">
          <div>
            <p className="label">Total estimado</p>
            <h3>{formatearPrecio(totalValue)}</h3>
          </div>
          <div>
            <p className="label">Productos</p>
            <h4>{totalUnits}</h4>
          </div>
        </div>
      </section>

      <section className="cart-benefits-grid">
        <article>
          <strong>Pagos protegidos</strong>
          <p>Integración con pasarelas certificadas PCI-DSS, incluida MercadoPago.</p>
        </article>
        <article>
          <strong>Soporte 24/7</strong>
          <p>Chat y correo para resolver dudas antes y después de tu compra.</p>
        </article>
        <article>
          <strong>Facturación transparente</strong>
          <p>Boleta electrónica y seguimiento del pedido en todo momento.</p>
        </article>
      </section>

      {isLoading && <div className="loading-cart" role="status" aria-live="polite">Cargando...</div>}

      {errorMessage && <div className="error-cart" role="alert" aria-live="assertive">{errorMessage}</div>}

      {!isLoading && !errorMessage && !hasItems && (
        <div className="empty-cart" role="status" aria-live="polite">
          <div className="empty-cart-icon" aria-hidden="true">🛒</div>
          <p>Sin productos en el carrito</p>
          <button className="cart-primary-btn" onClick={() => (window.location.href = "/catalogo")}>
            Ir al catálogo
          </button>
        </div>
      )}

      {!isLoading && !errorMessage && hasItems && (
        <div className="cart-body">
          <div className="cart-list">
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
          </div>

          <aside className="cart-summary-card">
            <h3>Resumen del pedido</h3>
            <p className="cart-summary-note">Incluye impuestos y cargos según tu método de pago.</p>
            <dl>
              <div>
                <dt>Productos</dt>
                <dd>{totalUnits}</dd>
              </div>
              <div>
                <dt>Total estimado</dt>
                <dd>{formatearPrecio(totalValue)}</dd>
              </div>
            </dl>
            <div className="cart-summary-actions">
              <button onClick={handleClear} className="ghost-btn" disabled={isUpdating}>
                Limpiar carrito
              </button>
              <button onClick={buy} className="primary-btn" disabled={isUpdating}>
                Pagar ahora
              </button>
            </div>
          </aside>
        </div>
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
