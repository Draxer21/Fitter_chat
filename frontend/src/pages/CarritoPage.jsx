import { useEffect, useState } from "react";
import "../styles/legacy/carrito/style_carrito.css";
import "../styles/checkout-form.css";
import { formatearPrecio } from "../utils/formatPrice";
import { useCart } from "../contexts/CartContext";
import { useAuth } from "../contexts/AuthContext";
import CheckoutForm from "../components/CheckoutForm";
import { API } from "../services/apijs";

export default function CarritoPage() {
  const { items, total, refresh, addItem, decrementItem, removeItem, clearCart, status, error } = useCart();
  const { isAuthenticated, refresh: refreshAuth, user } = useAuth();
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [actionError, setActionError] = useState("");
  const [checkoutState, setCheckoutState] = useState(null); // null | { orderId, total } | 'success' | 'pending'
  const [paymentError, setPaymentError] = useState("");

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

      setActionError("");
      setPaymentError("");

      // Incluir name/email del usuario autenticado (requerido por el backend)
      const currentUser = user || {};
      const orderBody = {
        name: currentUser.nombre || currentUser.full_name || currentUser.name || '',
        email: currentUser.email || '',
      };

      const data = await API.carrito.pagar(orderBody);

      // Abrir el formulario de pago con el order_id y total
      setCheckoutState({ orderId: data.order_id, total: data.total });

    } catch (err) {
      const msg = err?.payload?.error || err?.message || 'Error al procesar la compra.';
      setActionError(msg);
    }
  };

  const handlePaymentSuccess = (result) => {
    setCheckoutState(result.pending ? 'pending' : 'success');
    refresh().catch(() => {});
  };

  const handlePaymentError = (msg) => {
    setPaymentError(msg);
    setCheckoutState(null);
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

      {/* Modal de pago con Checkout API */}
      {checkoutState && typeof checkoutState === 'object' && (
        <CheckoutForm
          orderId={checkoutState.orderId}
          total={checkoutState.total}
          onSuccess={handlePaymentSuccess}
          onError={handlePaymentError}
          onClose={() => setCheckoutState(null)}
        />
      )}

      {/* Pago aprobado */}
      {checkoutState === 'success' && (
        <div className="checkout-form-overlay">
          <div className="checkout-form-modal text-center py-4">
            <i className="fa-solid fa-circle-check fa-3x text-success mb-3" />
            <h4 className="fw-bold">¡Pago aprobado!</h4>
            <p className="text-muted">Tu orden fue confirmada exitosamente.</p>
            <button className="btn btn-success mt-2" onClick={() => { setCheckoutState(null); window.location.href = '/perfil'; }}>
              Ver mis órdenes
            </button>
          </div>
        </div>
      )}

      {/* Pago pendiente */}
      {checkoutState === 'pending' && (
        <div className="checkout-form-overlay">
          <div className="checkout-form-modal text-center py-4">
            <i className="fa-solid fa-clock fa-3x text-warning mb-3" />
            <h4 className="fw-bold">Pago en proceso</h4>
            <p className="text-muted">Tu pago está siendo procesado. Te notificaremos cuando se confirme.</p>
            <button className="btn btn-primary mt-2" onClick={() => setCheckoutState(null)}>
              Entendido
            </button>
          </div>
        </div>
      )}

      {/* Error de pago */}
      {paymentError && (
        <div className="alert alert-danger mx-3 mt-3" role="alert">
          <i className="fa-solid fa-triangle-exclamation me-2" />
          {paymentError}
          <button className="btn-close float-end" onClick={() => setPaymentError("")} />
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
