import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { API } from "../services/apijs";
import "../styles/legacy/producto/style_index.css";
import HomeHero from "../components/HomeHero";
import Memberships from "../components/Memberships";
import Logo from "../components/Logo";
import { formatearPrecio } from "../utils/formatPrice";
import { useLocale } from "../contexts/LocaleContext";
import { useCart } from "../contexts/CartContext";

const stockDisponible = (valor) => {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
};

export default function HomePage() {
  const { search, hash } = useLocation();
  const categoria = useMemo(() => new URLSearchParams(search).get("categoria") || "", [search]);
  const { t } = useLocale();
  const { addItem } = useCart();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    const q = categoria ? `?categoria=${encodeURIComponent(categoria)}` : "";
    API.productos
      .list(q)
      .then((data) => {
        if (Array.isArray(data)) {
          setItems(data);
        } else if (Array.isArray(data?.items)) {
          setItems(data.items);
        } else {
          setItems([]);
        }
        setErr("");
      })
      .catch((e) => {
        setErr(e?.message || "No se pudieron cargar los productos.");
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [categoria]);

  const add = async (id) => {
    try {
      await addItem(id);
    } catch (e) {
      alert(e.message);
    }
  };

  const updateScrollIndicators = () => {
    const node = listRef.current;
    if (!node) {
      setCanScrollLeft(false);
      setCanScrollRight(false);
      return;
    }
    const maxScrollLeft = node.scrollWidth - node.clientWidth;
    setCanScrollLeft(node.scrollLeft > 4);
    setCanScrollRight(maxScrollLeft - node.scrollLeft > 4);
  };

  const scrollProducts = (direction) => {
    const node = listRef.current;
    if (!node) return;
    const firstCard = node.querySelector(".producto");
    const styles = typeof window !== "undefined" ? window.getComputedStyle(node) : null;
    const gap = styles ? parseFloat(styles.columnGap || styles.gap || "12") : 12;
    const cardWidth = firstCard ? firstCard.getBoundingClientRect().width + gap : node.clientWidth;
    node.scrollBy({ left: direction * cardWidth, behavior: "smooth" });
    if (typeof window !== "undefined") {
      window.requestAnimationFrame(() => {
        setTimeout(updateScrollIndicators, 200);
      });
    } else {
      setTimeout(updateScrollIndicators, 200);
    }
  };

  useEffect(() => {
    const node = listRef.current;
    if (node) {
      node.scrollTo({ left: 0 });
    }
    updateScrollIndicators();
    if (!node) return;

    const handle = () => updateScrollIndicators();
    node.addEventListener("scroll", handle, { passive: true });

    let observer;
    if (typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(handle);
      observer.observe(node);
    }

    return () => {
      node.removeEventListener("scroll", handle);
      if (observer) observer.disconnect();
    };
  }, [items.length, categoria]);

  useEffect(() => {
    if (!loading && hash === "#offers") {
      const target = document.getElementById("offers");
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [loading, hash]);

  return (
    <main className="flex-grow-1">
      <HomeHero />

      <section id="offers" className="home-offers-section py-5">
        <div className="container text-center">
          <h2 style={{ margin: "20px 0 30px 0" }}>
            {t("home.offers.title")}
            {categoria ? ` ${t("home.offers.in")} ${categoria}` : ""}
          </h2>
          {loading && <p className="offers-status" role="status" aria-live="polite">{t("home.offers.loading")}</p>}
          {err && <p className="offers-status text-danger" role="alert" aria-live="assertive">{t("home.offers.errorPrefix")} {err}</p>}
          {!loading && items.length === 0 && !err && (
            <p className="offers-status" role="status" aria-live="polite">{t("home.offers.empty")}</p>
          )}
        </div>

        <div
          className={[
            "productos-scroll-wrapper",
            canScrollLeft ? "productos-scroll-wrapper--show-left" : "",
            canScrollRight ? "productos-scroll-wrapper--show-right" : ""
          ].filter(Boolean).join(" ")}
        >
          {canScrollLeft && (
            <button
              type="button"
              className="productos-scroll-btn productos-scroll-btn--left"
              onClick={() => scrollProducts(-1)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && scrollProducts(-1)}
              aria-label="Ver productos anteriores"
            >
              {"<"}
            </button>
          )}

          <div ref={listRef} className="productos productos-scroll">
            {items.map((p) => {
              const disponible = stockDisponible(p.stock);
              const sinStock = disponible <= 0;
              const imageSrc = p.imagen_url || "/fitter_logo.png";
              return (
                <div key={p.id} className="producto">
                  <Link to={`/producto/${p.id}`}>
                    <Logo src={imageSrc} alt={p.nombre} className="producto__imagen" />
                    <h4>{p.nombre}</h4>
                    <p>{t("home.offers.categoryLabel")}: {p.categoria || "-"}</p>
                    <p>{t("home.offers.availabilityLabel")}: {disponible}</p>
                    <p>{t("home.offers.priceLabel")}: {formatearPrecio(p.precio)}</p>
                  </Link>
                  <button
                    className="btn btn-primary"
                    disabled={sinStock}
                    onClick={() => {
                      if (sinStock) return;
                      add(p.id);
                    }}
                  >
                    {sinStock ? t("home.offers.button.outOfStock") : t("home.offers.button.addToCart")}
                  </button>
                </div>
              );
            })}
          </div>

          {canScrollRight && (
            <button
              type="button"
              className="productos-scroll-btn productos-scroll-btn--right"
              onClick={() => scrollProducts(1)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && scrollProducts(1)}
              aria-label="Ver mas productos"
            >
              {">"}
            </button>
          )}
        </div>
      </section>

      <Memberships />
    </main>
  );
}
