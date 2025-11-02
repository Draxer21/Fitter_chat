import { useEffect, useMemo, useState } from "react";
import { API } from "../services/apijs";
import { useAuth } from "../contexts/AuthContext";
import { formatearPrecio } from "../utils/formatPrice";
import "../styles/admin-sales.css";

const formatDate = (iso) => {
  try {
    return new Date(iso).toLocaleDateString();
  } catch (err) {
    return iso;
  }
};

function SummaryCard({ label, value }) {
  return (
    <div className="sales-card">
      <span className="sales-card__label">{label}</span>
      <strong className="sales-card__value">{value}</strong>
    </div>
  );
}

function BarChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-muted">Sin datos para el rango seleccionado.</p>;
  }
  const max = Math.max(...data.map((item) => item.total || 0));
  return (
    <div className="sales-chart">
      {data.map((item) => (
        <div key={item.date} className="sales-chart__item">
          <div
            className="sales-chart__bar"
            style={{ height: max ? `${Math.max((item.total / max) * 100, 6)}%` : "6%" }}
          />
          <span className="sales-chart__label">{formatDate(item.date)}</span>
          <span className="sales-chart__value">{formatearPrecio(item.total)}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminSalesPage() {
  const { isAdmin } = useAuth();
  const [summary, setSummary] = useState(null);
  const [orders, setOrders] = useState([]);
  const [filters, setFilters] = useState({ status: "", start: "", end: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async (params = {}) => {
    setLoading(true);
    try {
      const query = new URLSearchParams({ ...params });
      const summaryData = await API.orders.summary(query.toString());
      const listData = await API.orders.list(query.toString());
      setSummary(summaryData);
      setOrders(listData?.orders || []);
      setError("");
    } catch (err) {
      setError(err?.message || "No pudimos cargar los datos de ventas.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin]);

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.start) params.start = filters.start;
    if (filters.end) params.end = filters.end;
    loadData(params);
  };

  if (!isAdmin) {
    return <div className="container py-5">No autorizado.</div>;
  }

  return (
    <main className="container py-4 admin-sales">
      <h1 className="mb-4">Panel de ventas</h1>
      <form className="sales-filters" onSubmit={applyFilters}>
        <div>
          <label className="form-label">Estado</label>
          <select name="status" className="form-select" value={filters.status} onChange={handleFilterChange}>
            <option value="">Todos</option>
            <option value="paid">Pagados</option>
            <option value="refunded">Reembolsados</option>
            <option value="cancelled">Cancelados</option>
          </select>
        </div>
        <div>
          <label className="form-label">Desde</label>
          <input type="date" name="start" className="form-control" value={filters.start} onChange={handleFilterChange} />
        </div>
        <div>
          <label className="form-label">Hasta</label>
          <input type="date" name="end" className="form-control" value={filters.end} onChange={handleFilterChange} />
        </div>
        <button type="submit" className="btn btn-dark align-self-end">Aplicar</button>
      </form>

      {loading && <div className="alert alert-info">Cargando informacion...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {summary && !loading && !error && (
        <>
          <section className="sales-summary">
            <SummaryCard label="Ventas totales" value={formatearPrecio(summary.total_sales)} />
            <SummaryCard label="Ordenes" value={summary.total_orders} />
            <SummaryCard label="Ordenes pagadas" value={summary.paid_orders} />
            <SummaryCard label="Ventas ultimos 30 dias" value={formatearPrecio(summary.sales_last_30)} />
          </section>

          <section className="sales-chart-section">
            <h2>Ventas diarias (30 dias)</h2>
            <BarChart data={summary.daily_sales} />
          </section>

          <section className="sales-top-products">
            <h2>Productos destacados</h2>
            <ul>
              {summary.top_products.map((item) => (
                <li key={item.name}>
                  <strong>{item.name}</strong> - {item.quantity} uds - {formatearPrecio(item.revenue)}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      <section className="sales-table-section">
        <h2>Ordenes recientes</h2>
        <div className="table-responsive">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{formatDate(order.created_at)}</td>
                  <td>{order.customer_name || "Invitado"}</td>
                  <td>{formatearPrecio(order.total_amount)}</td>
                  <td>
                    <span className={`badge bg-${order.status === "paid" ? "success" : "secondary"}`}>
                      {order.status}
                    </span>
                  </td>
                </tr>
              ))}
              {!orders.length && !loading && (
                <tr>
                  <td colSpan={5} className="text-center text-muted py-4">Sin ordenes para los filtros seleccionados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
