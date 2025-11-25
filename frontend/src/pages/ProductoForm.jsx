import { useState, useEffect } from "react";
import { useNavigate, Link, useParams } from "react-router-dom";
import { API } from "../services/apijs";
import { useAuth } from "../contexts/AuthContext";
import "../styles/legacy/tabla_productos/style_agregar_producto.css";

const CATEGORIES = ["Membership", "Personal Training", "Supplements", "Merchandise"];

const normalizaNumero = (valor, fallback = 0) => {
  const num = Number(valor);
  return Number.isFinite(num) ? num : fallback;
};

export default function ProductoForm() {
  const nav = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { isAdmin, initialized, refresh } = useAuth();
  const [f, setF] = useState({ nombre: "", precio: 0, descripcion: "", categoria: CATEGORIES[0], stock: 0 });
  const [err, setErr] = useState("");
  const [imagenFile, setImagenFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (!initialized) {
      refresh().catch(() => {});
      return;
    }
    if (!isAdmin) {
      nav("/login");
    }
  }, [initialized, isAdmin, nav, refresh]);

  useEffect(() => {
    if (!isEdit) return;
    let active = true;
    setLoading(true);
    API.productos
      .get(id)
      .then((producto) => {
        if (!active) return;
        setF({
          nombre: producto.nombre || "",
          precio: normalizaNumero(producto.precio, 0),
          descripcion: producto.descripcion || "",
          categoria: producto.categoria || CATEGORIES[0],
          stock: normalizaNumero(producto.stock, 0),
        });
        if (producto.imagen_url) {
          setPreview(producto.imagen_url);
        }
      })
      .catch((e) => {
        if (!active) return;
        setErr(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id, isEdit]);

  const save = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const payload = { ...f };
      if (imagenFile) {
        const fd = new FormData();
        fd.append("nombre", payload.nombre);
        fd.append("precio", payload.precio);
        fd.append("descripcion", payload.descripcion || "");
        fd.append("categoria", payload.categoria || "");
        fd.append("stock", payload.stock || 0);
        fd.append("imagen", imagenFile, imagenFile.name);
        if (isEdit) {
          await API.productos.update(id, fd);
        } else {
          await API.productos.create(fd);
        }
      } else {
        if (isEdit) {
          await API.productos.update(id, payload);
        } else {
          await API.productos.create(payload);
        }
      }
      nav("/admin/productos");
    } catch (ex) {
      setErr(ex.message);
    }
  };

  const onFile = (ev) => {
    const file = ev.target.files && ev.target.files[0];
    setImagenFile(file || null);
    if (file) {
      const url = URL.createObjectURL(file);
      setPreview(url);
    } else {
      setPreview(null);
    }
  };

  const titulo = isEdit ? "Editar Producto/Servicio" : "Añadir Producto/Servicio";

  return (
    <div className="container mt-5 mb-5">
      <h1 className="text-center mb-5">{titulo}</h1>

      {loading ? (
        <div className="alert alert-info">Cargando...</div>
      ) : (
        <form onSubmit={save} className="producto-form mb-5">
          <div className="table-responsive">
            <table className="table table-bordered producto-form-table">
              <tbody>
                <tr>
                  <th scope="row">Nombre</th>
                  <td>
                    <input
                      className="form-control"
                      value={f.nombre}
                      onChange={(e) => setF({ ...f, nombre: e.target.value })}
                      required
                    />
                  </td>
                </tr>
                <tr>
                  <th scope="row">Precio</th>
                  <td>
                    <input
                      className="form-control"
                      type="number"
                      step="0.01"
                      value={f.precio}
                      onChange={(e) => setF({ ...f, precio: normalizaNumero(e.target.value, 0) })}
                      required
                    />
                  </td>
                </tr>
                <tr>
                  <th scope="row">Descripción</th>
                  <td>
                    <textarea
                      className="form-control"
                      value={f.descripcion}
                      onChange={(e) => setF({ ...f, descripcion: e.target.value })}
                    />
                  </td>
                </tr>
                <tr>
                  <th scope="row">Categoría</th>
                  <td>
                    <select
                      className="form-control"
                      value={f.categoria}
                      onChange={(e) => setF({ ...f, categoria: e.target.value })}
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Stock</th>
                  <td>
                    <input
                      className="form-control"
                      type="number"
                      value={f.stock}
                      onChange={(e) => setF({ ...f, stock: normalizaNumero(e.target.value, 0) })}
                      required
                    />
                  </td>
                </tr>
                <tr>
                  <th scope="row">Imagen</th>
                  <td>
                    <input type="file" accept="image/*" onChange={onFile} className="form-control" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {err && <div className="alert alert-danger">{err}</div>}

          {preview && (
            <div className="mb-4">
              <h5>Previsualización</h5>
              <div className="preview-container p-3 border rounded">
                <img src={preview} alt="Previsualización del producto" style={{ maxWidth: 200, maxHeight: 200, objectFit: "contain" }} />
              </div>
            </div>
          )}

          <div className="d-flex justify-content-between">
            <Link to="/admin/productos" className="btn btn-secondary">
              Volver
            </Link>
            <button type="submit" className="btn btn-success">
              Guardar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}


