import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useParams } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/product-detail.css";
import { formatearPrecio } from "../utils/formatPrice";
import { useCart } from "../contexts/CartContext";

const stockDisponible = (valor) => {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
};

export default function ProductoDetalle() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [related, setRelated] = useState([]);
  const [relatedError, setRelatedError] = useState("");
  const [showFullDescription, setShowFullDescription] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const { addItem } = useCart();

  useEffect(() => {
    setSelectedImageIndex(0);
    let active = true;
    setLoading(true);
    API.productos
      .get(id)
      .then((data) => {
        if (!active) return;
        setP(data);
        setErr("");
      })
      .catch((e) => {
        if (!active) return;
        setErr(e.message);
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  useEffect(() => {
    if (!p) {
      setRelated([]);
      return;
    }
    let active = true;
    API.productos
      .list("")
      .then((data) => {
        if (!active) return;
        const items = Array.isArray(data) ? data : [];
        const filtered = items
          .filter((item) => item.id !== p.id)
          .filter((item) => !p.categoria || item.categoria === p.categoria)
          .slice(0, 8);
        setRelated(filtered);
        setRelatedError("");
      })
      .catch((e) => {
        if (!active) return;
        setRelated([]);
        setRelatedError(e.message || "No se pudieron cargar productos relacionados.");
      });
    return () => {
      active = false;
    };
  }, [p]);

  const add = async () => {
    if (!p) return;
    try {
      await addItem(p.id);
    } catch (e) {
      alert(e.message);
    }
  };

  const addRelated = async (productId) => {
    try {
      await addItem(productId);
    } catch (e) {
      alert(e.message);
    }
  };

  const disponible = stockDisponible(p?.stock);
  const sinStock = disponible <= 0;
  const imageSrc = p?.imagen_url || "/fitter_logo.png";

  const galleryImages = useMemo(() => {
    if (Array.isArray(p?.gallery) && p.gallery.length > 0) {
      return p.gallery;
    }
    return [imageSrc];
  }, [p, imageSrc]);

  const shortDescription = useMemo(() => {
    const descripcion = p?.descripcion;
    if (!descripcion) return "Sin descripción adicional.";
    if (showFullDescription || descripcion.length < 320) {
      return descripcion;
    }
    return `${descripcion.slice(0, 320)}…`;
  }, [p, showFullDescription]);

  const specifications = useMemo(() => {
    const rows = [];
    rows.push({ label: "Categoría", value: p?.categoria || "—" });
    rows.push({ label: "Código", value: p ? `#${p.id}` : "—" });
    rows.push({ label: "Disponibilidad", value: disponible > 0 ? `${disponible} unidades` : "Sin stock" });
    rows.push({ label: "Precio", value: formatearPrecio(p?.precio || 0) });
    if (p?.brand) {
      rows.unshift({ label: "Marca", value: p.brand });
    }
    if (Array.isArray(p?.specifications)) {
      p.specifications.forEach((row) => {
        if (row && row.label) {
          rows.push({
            label: row.label,
            value: row.value ?? row.descripcion ?? row.detail ?? "—",
          });
        }
      });
    }
    return rows;
  }, [p, disponible]);

  if (err) {
    return (
      <main className="product-detail-page">
        <div className="container text-danger py-5">Error: {err}</div>
      </main>
    );
  }

  if (loading || !p) {
    return (
      <main className="product-detail-page">
        <div className="container py-5">Cargando…</div>
      </main>
    );
  }

  return (
    <main className="product-detail-page">
      <div className="container">
        <nav className="product-breadcrumb">
          <Link to="/">Inicio</Link>
          {p.categoria && (
            <>
              <span>/</span>
              <Link to={`/catalogo?categoria=${encodeURIComponent(p.categoria)}`}>{p.categoria}</Link>
            </>
          )}
          <span>/</span>
          <span className="product-breadcrumb__current">{p.nombre}</span>
        </nav>

        <div className="product-detail-grid">
          <section className="product-gallery">
            <div className="product-gallery__main">
              <img src={galleryImages[selectedImageIndex] || imageSrc} alt={p.nombre} />
            </div>
            {galleryImages.length > 1 && (
              <div className="product-gallery__thumbnails">
                {galleryImages.map((img, index) => (
                  <button
                    key={img || index}
                    type="button"
                    className={`product-gallery__thumb ${index === selectedImageIndex ? "product-gallery__thumb--active" : ""}`}
                    onClick={() => setSelectedImageIndex(index)}
                  >
                    <img src={img} alt={`${p.nombre} vista ${index + 1}`} />
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="product-summary">
            <small className="product-summary__brand">{p.brand || p.categoria || "Producto Fitter"}</small>
            <h1>{p.nombre}</h1>
            {p.rating && (
              <div className="product-summary__rating">
                <span className="product-summary__rating-stars">
                  {"★".repeat(Math.round(p.rating))}
                  {p.rating < 5 ? "☆".repeat(5 - Math.round(p.rating)) : ""}
                </span>
                <span>{Number(p.rating).toFixed(1)} / 5</span>
                {p.rating_count ? <span className="text-muted">({p.rating_count} opiniones)</span> : null}
              </div>
            )}
            <div className="product-summary__price">
              <span className="product-summary__amount">{formatearPrecio(p.precio)}</span>
              <span className={`product-summary__stock ${sinStock ? "product-summary__stock--empty" : ""}`}>
                {sinStock ? "Sin stock disponible" : `${disponible} unidades listas para envío`}
              </span>
            </div>
            <p className="product-summary__description">{shortDescription}</p>
            {p.descripcion && p.descripcion.length > 320 && (
              <button
                type="button"
                className="btn btn-link p-0"
                onClick={() => setShowFullDescription((prev) => !prev)}
              >
                {showFullDescription ? "Ver menos" : "Ver descripción completa"}
              </button>
            )}
            {Array.isArray(p.highlights) && p.highlights.length > 0 && (
              <ul className="product-summary__highlights">
                {p.highlights.map((highlight, index) => (
                  <li key={index}>{highlight}</li>
                ))}
              </ul>
            )}

            <div className="product-summary__actions">
              <button
                type="button"
                className="btn btn-dark btn-lg"
                disabled={sinStock}
                onClick={() => {
                  if (!sinStock) add();
                }}
              >
                {sinStock ? "No disponible" : "Agregar al carrito"}
              </button>
              <Link to="/carrito" className="btn btn-outline-secondary btn-lg">
                Ir al carrito
              </Link>
            </div>

            <div className="product-summary__info">
              <div>
                <strong>Entrega rápida</strong>
                <p className="text-muted mb-0">Disponibilidad inmediata para retiro o envío.</p>
              </div>
              <div>
                <strong>Pago seguro</strong>
                <p className="text-muted mb-0">Protegemos tus datos con métodos de pago seguros.</p>
              </div>
            </div>
          </section>
        </div>

        <section className="product-details">
          <div className="product-specs">
            <h2>Especificaciones</h2>
            <dl>
              {specifications.map((spec) => (
                <div key={spec.label} className="product-specs__row">
                  <dt>{spec.label}</dt>
                  <dd>{spec.value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="product-description">
            <h2>Información adicional</h2>
            <p>{p.descripcion || "No se proporcionó información adicional para este producto."}</p>
          </div>
        </section>

        <section className="product-related">
          <header className="d-flex justify-content-between align-items-center mb-3">
            <h3>Tal vez te interese</h3>
            <Link to="/catalogo" className="btn btn-link">Ver todo el catálogo</Link>
          </header>
          {relatedError && <div className="alert alert-warning">{relatedError}</div>}
          {!relatedError && related.length === 0 && (
            <p className="text-muted">No encontramos productos similares por ahora.</p>
          )}
          <div className="product-related__grid">
            {related.map((item) => {
              const stock = stockDisponible(item.stock);
              return (
                <article key={item.id} className="product-related__card">
                  <Link to={`/producto/${item.id}`}>
                    <img src={item.imagen_url || "/fitter_logo.png"} alt={item.nombre} />
                    <h4>{item.nombre}</h4>
                  </Link>
                  <span className="product-related__price">{formatearPrecio(item.precio)}</span>
                  <span className="product-related__stock">
                    {stock > 0 ? `${stock} disponibles` : "Sin stock"}
                  </span>
                  <button
                    type="button"
                    className="btn btn-outline-dark btn-sm"
                    disabled={stock <= 0}
                    onClick={() => addRelated(item.id)}
                  >
                    Añadir
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}
