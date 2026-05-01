import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import ProfileSectionNav from "../components/ProfileSectionNav";
import { API } from "../services/apijs";
import "../styles/subscription.css";

const STATUS_LABELS = {
  pending:   { label: "Pendiente",   cls: "warning" },
  confirmed: { label: "Confirmado",  cls: "success" },
  paid:      { label: "Pagado",      cls: "success" },
  cancelled: { label: "Cancelado",   cls: "danger"  },
  failed:    { label: "Fallido",     cls: "danger"  },
  refunded:  { label: "Reembolsado", cls: "secondary" },
};

function formatCLP(amount) {
  return new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP" }).format(amount);
}

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("es-CL", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function StatusBadge({ status }) {
  const info = STATUS_LABELS[status] || { label: status, cls: "secondary" };
  return <span className={`badge bg-${info.cls}`}>{info.label}</span>;
}

function OrderCard({ order, onDownloadPdf }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card border-0 shadow-sm mb-3">
      <div
        className="card-header d-flex align-items-center justify-content-between gap-2"
        style={{ cursor: "pointer", background: "var(--surface, #fff)", borderRadius: open ? "12px 12px 0 0" : 12 }}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="d-flex align-items-center gap-3 flex-wrap">
          <span className="fw-semibold">Orden #{order.id}</span>
          <StatusBadge status={order.status} />
          <span className="text-muted small">{formatDate(order.created_at)}</span>
        </div>
        <div className="d-flex align-items-center gap-3">
          <span className="fw-bold">{formatCLP(order.total_amount)}</span>
          <i className={`fa-solid fa-chevron-${open ? "up" : "down"} text-muted`} />
        </div>
      </div>

      {open && (
        <div className="card-body pt-2">
          {/* Productos */}
          <table className="table table-sm mb-3">
            <thead>
              <tr className="small text-muted">
                <th>Producto</th>
                <th className="text-end">Qty</th>
                <th className="text-end">Precio unit.</th>
                <th className="text-end">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {(order.items || []).map((item, i) => (
                <tr key={i}>
                  <td>{item.product_name}</td>
                  <td className="text-end">{item.quantity}</td>
                  <td className="text-end">{formatCLP(item.unit_price)}</td>
                  <td className="text-end">{formatCLP(item.subtotal)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="fw-bold">
                <td colSpan={3} className="text-end">Total</td>
                <td className="text-end">{formatCLP(order.total_amount)}</td>
              </tr>
            </tfoot>
          </table>

          {/* Pago */}
          <div className="d-flex flex-wrap gap-3 small text-muted mb-3">
            {order.payment_method && (
              <span><i className="fa-solid fa-credit-card me-1" />Método: {order.payment_method}</span>
            )}
            {order.payment_reference && (
              <span><i className="fa-solid fa-receipt me-1" />Ref: {order.payment_reference}</span>
            )}
          </div>

          {/* Acciones */}
          <div className="d-flex gap-2 flex-wrap">
            <button
              className="btn btn-sm btn-outline-dark"
              onClick={() => onDownloadPdf(order.id)}
            >
              <i className="fa-solid fa-file-pdf me-1" />Descargar boleta
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MisComprasPage() {
  const { isAuthenticated } = useAuth();
  const [orders, setOrders]         = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [status, setStatus]         = useState("idle");
  const [error, setError]           = useState("");
  const [pdfLoading, setPdfLoading] = useState(null);

  const load = useCallback(() => {
    if (!isAuthenticated) return;
    setStatus("loading");
    setError("");

    Promise.all([
      API.orders.my(),
      API.subscriptions.current().catch(() => null),
    ])
      .then(([ordersData, sub]) => {
        setOrders(ordersData?.orders || []);
        setSubscription(sub?.subscription || null);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err?.message || "No se pudo cargar tu historial de compras.");
        setStatus("error");
      });
  }, [isAuthenticated]);

  useEffect(() => { load(); }, [load]);

  const handleDownloadPdf = async (orderId) => {
    setPdfLoading(orderId);
    try {
      const res = await API.orders.receiptPdf(orderId);
      if (!res.ok) { alert("No se pudo generar la boleta."); return; }
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `boleta_${orderId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Error al descargar la boleta.");
    } finally {
      setPdfLoading(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <main className="profile-page py-5">
        <div className="profile-shell">
          <div className="row justify-content-center">
            <div className="col-lg-6">
              <div className="alert alert-warning">
                Debes iniciar sesión para ver tus compras.
                <div className="mt-3">
                  <Link className="btn btn-dark" to="/login">Iniciar sesión</Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="profile-page py-5">
      <div className="profile-shell">
        <header className="profile-header text-center mb-4">
          <p className="profile-eyebrow text-uppercase">Mi cuenta</p>
          <h1 className="profile-title">Mis compras</h1>
          <p className="profile-subtitle">Historial de pedidos y estado de tu suscripción.</p>
        </header>

        <ProfileSectionNav />

        {/* Suscripción activa */}
        {subscription && (
          <div className="card border-0 shadow-sm mb-4">
            <div className="card-body d-flex flex-wrap align-items-center justify-content-between gap-3">
              <div>
                <p className="text-muted small text-uppercase mb-1">Suscripción actual</p>
                <h5 className="fw-bold mb-1 text-capitalize">{subscription.plan_type || "—"}</h5>
                <div className="d-flex gap-3 flex-wrap small text-muted">
                  <span>
                    <StatusBadge status={subscription.status} />
                  </span>
                  {subscription.end_date && (
                    <span>
                      <i className="fa-solid fa-calendar-xmark me-1" />
                      Vence: {formatDate(subscription.end_date)}
                    </span>
                  )}
                </div>
              </div>
              <Link to="/cuenta/suscripcion" className="btn btn-sm btn-outline-dark">
                Gestionar suscripción
              </Link>
            </div>
          </div>
        )}

        {/* Estado de carga */}
        {status === "loading" && (
          <div className="text-center py-5 text-muted">
            <div className="spinner-border spinner-border-sm me-2" />Cargando...
          </div>
        )}
        {status === "error" && (
          <div className="alert alert-danger">{error}</div>
        )}

        {/* Historial de órdenes */}
        {status === "ready" && (
          <>
            {orders.length === 0 ? (
              <div className="text-center py-5">
                <i className="fa-solid fa-bag-shopping fa-3x text-muted mb-3" />
                <p className="text-muted">Aún no tienes compras registradas.</p>
                <Link to="/catalogo" className="btn btn-dark mt-2">
                  Ir al catálogo
                </Link>
              </div>
            ) : (
              <div>
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <h5 className="fw-bold mb-0">
                    {orders.length} {orders.length === 1 ? "pedido" : "pedidos"}
                  </h5>
                  <button className="btn btn-sm btn-outline-secondary" onClick={load}>
                    <i className="fa-solid fa-rotate-right me-1" />Actualizar
                  </button>
                </div>
                {orders.map((order) => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onDownloadPdf={handleDownloadPdf}
                    pdfLoading={pdfLoading}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
