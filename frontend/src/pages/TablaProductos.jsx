import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_tabla_productos.css";
import { formatearPrecio } from "../utils/formatPrice";
import { useAuth } from "../contexts/AuthContext";

const stockDisponible = (valor) => {
  const stock = Number(valor);
  return Number.isFinite(stock) ? stock : 0;
};

export default function TablaProductos() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();
  const { isAdmin, initialized, refresh } = useAuth();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await API.productos.list();
      setItems(data);
      setErr("");
    } catch (e) {
      setErr(e.message || "No se pudo cargar el inventario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!initialized) {
      refresh().catch(() => {});
      return;
    }
    if (!isAdmin) {
      nav("/login");
      return;
    }
    load();
  }, [initialized, isAdmin, load, nav, refresh]);

  const del = useCallback(
    async (id) => {
      if (!window.confirm("Eliminar producto?")) {
        return;
      }
      try {
        await API.productos.del(id);
        await load();
      } catch (e) {
        setErr(e.message || "No se pudo eliminar el producto.");
      }
    },
    [load]
  );

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredItems = normalizedQuery
    ? items.filter((pr) => {
        const fields = [pr.id?.toString(), pr.nombre, pr.descripcion, pr.categoria];
        return fields.some((field) => String(field ?? "").toLowerCase().includes(normalizedQuery));
      })
    : items;
  const hasSearch = normalizedQuery.length > 0;

  return (
    <main className="flex-grow-1">
      <div className="container-fluid px-4 py-5">
        <h1 className="mb-4 mt-4">Gestión de Inventario</h1>
        <div className="row g-3 align-items-center mb-4">
          <div className="col-12 col-md-8">
            <form className="input-group" role="search" onSubmit={(e) => e.preventDefault()}>
              <span className="input-group-text bg-dark text-white border-secondary">
                <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
              </span>
              <input
                type="search"
                className="form-control"
                placeholder="Buscar por nombre, descripcion o categoria"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Buscar producto en inventario"
              />
            </form>
          </div>
          <div className="col-12 col-md-4 d-grid d-md-flex justify-content-md-end">
            <Link 
              to="/admin/productos/nuevo" 
              className="btn btn-success"
              aria-label="Añadir nuevo producto o servicio al inventario"
            >
              <i className="fa-solid fa-plus me-2" aria-hidden="true" />
              Añadir Producto/Servicio
            </Link>
          </div>
        </div>

        {err && (
          <div className="alert alert-danger" role="alert">
            <i className="fa-solid fa-exclamation-triangle me-2" aria-hidden="true" />
            {err}
          </div>
        )}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Cargando productos...</span>
            </div>
            <p className="mt-3 text-muted">Cargando inventario...</p>
          </div>
        ) : (
          <div className="table-responsive tabla-productos-wrapper mt-3">
            <table className="table table-dark table-striped table-bordered" aria-label="Tabla de productos del inventario">
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Nombre</th>
                <th scope="col">Precio</th>
                <th scope="col">Descripción</th>
                <th scope="col">Categoría</th>
                <th scope="col">Stock</th>
                <th scope="col">Imagen</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((pr) => {
                const stock = stockDisponible(pr.stock);
                const imageSrc = pr.imagen_url || "/fitter_logo.png";
                return (
                  <tr key={pr.id}>
                    <td>{pr.id}</td>
                    <td>{pr.nombre}</td>
                    <td>{formatearPrecio(pr.precio)}</td>
                    <td>{pr.descripcion || ""}</td>
                    <td>{pr.categoria || ""}</td>
                    <td>{stock}</td>
                    <td>
                      <img src={imageSrc} alt={pr.nombre} style={{ width: 60, height: 60, objectFit: "cover", borderRadius: 6 }} />
                    </td>
                    <td className="text-center align-middle">
                      <div className="d-flex justify-content-center align-items-center gap-2">
                        <Link 
                          to={`/admin/productos/${pr.id}/editar`} 
                          className="btn btn-warning btn-action"
                          aria-label={`Editar ${pr.nombre}`}
                          title="Editar"
                        >
                          <i className="fa-solid fa-pen-to-square" aria-hidden="true" />
                        </Link>
                        <button 
                          className="btn btn-danger btn-action" 
                          onClick={() => del(pr.id)} 
                          aria-label={`Eliminar ${pr.nombre}`}
                          title="Eliminar"
                        >
                          <i className="fa-solid fa-trash-can" aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center">
                    {hasSearch ? "Sin coincidencias" : "Sin productos"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        )}

        {!loading && filteredItems.length > 0 && (
          <div className="mt-3 text-muted small">
            <i className="fa-solid fa-box me-2" aria-hidden="true" />
            Mostrando {filteredItems.length} de {items.length} producto{items.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </main>
  );
}
