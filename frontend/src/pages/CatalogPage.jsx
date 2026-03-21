import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { API } from "../services/apijs";
import { useCart } from "../contexts/CartContext";
import { useLocale } from "../contexts/LocaleContext";
import { formatearPrecio } from "../utils/formatPrice";
import "../styles/catalog.css";

const normalizePrice = (value) => {
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : 0;
};

const normalizeStock = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

export default function CatalogPage() {
  const location = useLocation();
  const { t } = useLocale();
  const { addItem, items: cartItems, total } = useCart();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [priceFrom, setPriceFrom] = useState("");
  const [priceTo, setPriceTo] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    API.productos
      .list("")
      .then((data) => {
        if (!active) return;
        setProducts(Array.isArray(data) ? data : []);
        setError("");
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.message || "No se pudieron cargar los productos.");
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const cat = params.get("categoria");
    if (cat) {
      setSelectedCategory(cat);
    }
    const q = params.get("q");
    if (q) {
      setSearch(q);
    }
  }, [location.search]);

  const categories = useMemo(() => {
    const set = new Set();
    products.forEach((p) => {
      if (p?.categoria) {
        set.add(p.categoria);
      }
    });
    return Array.from(set).sort();
  }, [products]);

  const priceLimits = useMemo(() => {
    if (!products.length) {
      return { min: 0, max: 0 };
    }
    const values = products.map((p) => normalizePrice(p.precio)).filter((n) => Number.isFinite(n));
    if (!values.length) {
      return { min: 0, max: 0 };
    }
    return { min: Math.min(...values), max: Math.max(...values) };
  }, [products]);

  useEffect(() => {
    if (priceLimits.min === 0 && priceLimits.max === 0) {
      setPriceFrom("");
      setPriceTo("");
    } else {
      setPriceFrom(priceLimits.min.toString());
      setPriceTo(priceLimits.max.toString());
    }
  }, [priceLimits.min, priceLimits.max]);

  const filteredProducts = useMemo(() => {
    const minPrice = normalizePrice(priceFrom);
    const maxPrice = normalizePrice(priceTo);
    const hasSearch = search.trim().length > 0;
    const searchLower = search.trim().toLowerCase();

    return products.filter((product) => {
      if (!product) {
        return false;
      }
      if (selectedCategory !== "all" && product.categoria !== selectedCategory) {
        return false;
      }
      const price = normalizePrice(product.precio);
      if (priceFrom !== "" && price < minPrice) {
        return false;
      }
      if (priceTo !== "" && maxPrice !== 0 && price > maxPrice) {
        return false;
      }
      if (inStockOnly && normalizeStock(product.stock) <= 0) {
        return false;
      }
      if (hasSearch) {
        const text = `${product.nombre || ""} ${product.descripcion || ""}`.toLowerCase();
        if (!text.includes(searchLower)) {
          return false;
        }
      }
      return true;
    });
  }, [products, selectedCategory, priceFrom, priceTo, inStockOnly, search]);

  const addToCart = async (id) => {
    try {
      await addItem(id);
    } catch (err) {
      alert(err?.message || "No se pudo agregar al carrito.");
    }
  };

  const totalItems = cartItems.reduce((acc, item) => acc + (item.cantidad || 0), 0);

  return (
    <main className="catalog-layout container-fluid py-4">
      <div className="row justify-content-center">
        <div className="col-12 col-xl-10">
          <div className="catalog-grid">
            <aside className="catalog-filters">
              <div className="catalog-filters__header">
                <h2>{t("catalog.filters")}</h2>
                {(search || selectedCategory !== "all" || inStockOnly) && (
                  <button
                    className="catalog-filters__clear"
                    onClick={() => { setSearch(""); setSelectedCategory("all"); setInStockOnly(false); setPriceFrom(priceLimits.min.toString()); setPriceTo(priceLimits.max.toString()); }}
                  >
                    {t("catalog.clearFilters")}
                  </button>
                )}
              </div>
              <div className="catalog-filter-group">
                <label htmlFor="catalog-search" className="catalog-filter-label">🔍 {t("catalog.search")}</label>
                <input
                  id="catalog-search"
                  type="text"
                  className="form-control"
                  placeholder={t("catalog.searchPlaceholder")}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <div className="catalog-filter-group">
                <label htmlFor="catalog-category" className="catalog-filter-label">📂 {t("catalog.category")}</label>
                <select
                  id="catalog-category"
                  className="form-select"
                  value={selectedCategory}
                  onChange={(event) => setSelectedCategory(event.target.value)}
                >
                  <option value="all">{t("catalog.allCategories")}</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>
              <div className="catalog-filter-group">
                <label className="catalog-filter-label">💰 {t("catalog.priceRange")}</label>
                <div className="catalog-price-inputs">
                  <input
                    type="number"
                    min="0"
                    className="form-control"
                    value={priceFrom}
                    onChange={(event) => setPriceFrom(event.target.value)}
                    placeholder={t("catalog.priceFrom")}
                  />
                  <span className="catalog-price-separator">—</span>
                  <input
                    type="number"
                    min="0"
                    className="form-control"
                    value={priceTo}
                    onChange={(event) => setPriceTo(event.target.value)}
                    placeholder={t("catalog.priceTo")}
                  />
                </div>
              </div>
              <div className="catalog-filter-group">
                <label className="catalog-stock-toggle">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    checked={inStockOnly}
                    onChange={(event) => setInStockOnly(event.target.checked)}
                  />
                  <span>📦 {t("catalog.inStockOnly")}</span>
                </label>
              </div>
              {(search || selectedCategory !== "all" || inStockOnly) && (
                <div className="catalog-active-filters">
                  <span className="catalog-active-filters__label">{t("catalog.activeFilters")}:</span>
                  {search && <span className="catalog-active-tag" onClick={() => setSearch("")}>{t("catalog.search")}: "{search}" ✕</span>}
                  {selectedCategory !== "all" && <span className="catalog-active-tag" onClick={() => setSelectedCategory("all")}>{selectedCategory} ✕</span>}
                  {inStockOnly && <span className="catalog-active-tag" onClick={() => setInStockOnly(false)}>{t("catalog.inStockOnly")} ✕</span>}
                </div>
              )}
            </aside>

            <section className="catalog-products">
              <header className="catalog-products__header">
                <div>
                  <h1>{t("catalog.title")}</h1>
                  <p className="text-muted mb-0">
                    {loading
                      ? t("catalog.loading")
                      : `${filteredProducts.length} ${t("catalog.of")} ${products.length} ${t("catalog.products")}`}
                  </p>
                </div>
              </header>

              {error && <div className="alert alert-danger">{error}</div>}
              {!loading && !error && filteredProducts.length === 0 && (
                <div className="alert alert-info">{t("catalog.noResults")}</div>
              )}

              <div className="catalog-products__grid">
                {filteredProducts.map((product) => {
                  const stock = normalizeStock(product.stock);
                  const outOfStock = stock <= 0;
                  const image = product.imagen_url || "/fitter_logo.png";
                  return (
                    <article key={product.id} className="catalog-card">
                      <Link to={`/producto/${product.id}`} className="catalog-card__image">
                        <img src={image} alt={product.nombre} loading="lazy" />
                        {product.categoria && <span className="catalog-card__badge">{product.categoria}</span>}
                      </Link>
                      <div className="catalog-card__body">
                        <h3>{product.nombre}</h3>
                        <p className="catalog-card__description">{product.descripcion || t("catalog.noDescription")}</p>
                        {product.rating && (
                          <div className="catalog-card__rating">
                            <span className="catalog-card__stars">
                              {"★".repeat(Math.round(product.rating))}{product.rating < 5 ? "☆".repeat(5 - Math.round(product.rating)) : ""}
                            </span>
                            <span>{Number(product.rating).toFixed(1)}</span>
                            {product.rating_count ? <span className="text-muted">({product.rating_count})</span> : null}
                          </div>
                        )}
                        <div className="catalog-card__meta">
                          <span>{formatearPrecio(product.precio)}</span>
                          <span>{stock > 0 ? `${stock} ${t("catalog.inStock")}` : t("catalog.outOfStock")}</span>
                        </div>
                      </div>
                      <div className="catalog-card__actions">
                        <Link to={`/producto/${product.id}`} className="btn btn-outline-secondary catalog-card__btn">
                          {t("catalog.viewDetail")}
                        </Link>
                        <button
                          type="button"
                          className="btn btn-dark catalog-card__btn"
                          disabled={outOfStock}
                          onClick={() => addToCart(product.id)}
                        >
                          {outOfStock ? t("catalog.soldOut") : t("catalog.addToCart")}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            <aside className="catalog-cart">
              <div className="catalog-cart__header">
                <h2>{t("catalog.yourCart")}</h2>
                <span>{totalItems} {totalItems === 1 ? t("catalog.product") : t("catalog.products")}</span>
              </div>
              {cartItems.length === 0 ? (
                <p className="text-muted mb-0">{t("catalog.emptyCart")}</p>
              ) : (
                <ul className="catalog-cart__list">
                  {cartItems.map((item) => (
                    <li key={item.producto_id || item.id}>
                      <div>
                        <strong>{item.nombre || item.producto?.nombre}</strong>
                        <div className="text-muted small">
                          {item.cantidad} x {formatearPrecio(item.precio || item.producto?.precio || 0)}
                        </div>
                      </div>
                      <span>{formatearPrecio((item.precio || 0) * (item.cantidad || 0))}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="catalog-cart__footer">
                <div className="catalog-cart__total">
                  <span>Total</span>
                  <strong>{formatearPrecio(total)}</strong>
                </div>
                <Link to="/carrito" className="btn btn-warning w-100">
                  {t("catalog.goToCart")}
                </Link>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
