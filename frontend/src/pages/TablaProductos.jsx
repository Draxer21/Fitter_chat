import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/tabla_productos/style_tabla_productos.css";
import { formatearPrecio } from "../utils/formatPrice";

const stockDisponible = (valor) => {
  const stock = Number(valor);
  return Number.isFinite(stock) ? stock : 0;
};

export default function TablaProductos() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const load = () =>
    API.productos
      .list()
      .then(setItems)
      .catch((e) => setErr(e.message));

  useEffect(() => {
    let mounted = true;
    API.auth
      .me()
      .then((r) => {
        if (!r?.is_admin) {
          nav("/login");
          return;
        }
        if (mounted) load();
      })
      .catch(() => nav("/login"));
    return () => {
      mounted = false;
    };
  }, []);

  const del = async (id) => {
    if (window.confirm('Eliminar producto?')) {
      await API.productos.del(id);
      load();
    }
  };

  return (
    <main className="flex-grow-1">
      <div className="container">
        <h1>Gestion de Inventario</h1>
        <div className="d-flex justify-content-end mb-2">
          <Link to="/admin/productos/nuevo" className="btn btn-success">
            Anadir Producto/Servicio
          </Link>
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        <div className="table-responsive">
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
              {items.map((pr) => {
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
                        <Link
                          to={`/admin/productos/${pr.id}/editar`}
                          className="btn btn-warning"
                          aria-label={`Editar ${pr.nombre}`}
                        >
                          <i className="fa-solid fa-pencil" />
                        </Link>
                        <button
                          className="btn btn-danger"
                          onClick={() => del(pr.id)}
                          aria-label={`Eliminar ${pr.nombre}`}
                        >
                          <i className="fa-solid fa-trash" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {items.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center">
                    Sin productos
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
