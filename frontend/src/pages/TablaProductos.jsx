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
  const nav = useNavigate();
  const { isAdmin, initialized, refresh } = useAuth();

  const load = useCallback(async () => {
    try {
      const data = await API.productos.list();
      setItems(data);
      setErr("");
    } catch (e) {
      setErr(e.message || "No se pudo cargar el inventario.");
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
      <div className="container-fluid px-4">
        <h1>Gestion de Inventario</h1>
        <div className="row g-3 align-items-center mb-3">
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
            <Link to="/admin/productos/nuevo" className="btn btn-success">
              Anadir Producto/Servicio
            </Link>
          </div>
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        <div className="table-responsive tabla-productos-wrapper mt-3">
          <table className="table table-dark table-striped table-bordered">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Precio</th>
                <th>Descripcion</th>
                <th>Categoria</th>
                <th>Stock</th>
                <th>Imagen</th>
                <th>Acciones</th>
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
                    <td className="text-center">
                      <div className="d-flex justify-content-center gap-2">
                        <Link to={`/admin/productos/${pr.id}/editar`} className="btn btn-warning" aria-label={`Editar ${pr.nombre}`}>
                          <i className="fa-solid fa-pencil" />
                        </Link>
                        <button className="btn btn-danger" onClick={() => del(pr.id)} aria-label={`Eliminar ${pr.nombre}`}>
                          <i className="fa-solid fa-trash" />
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
      </div>
    </main>
  );
}
