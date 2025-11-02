import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "../services/apijs";
import { formatearPrecio } from "../utils/formatPrice";
import "../styles/pago/style_pago.css";
import { useCart } from "../contexts/CartContext";

function luhnCheck(cardNumber) {
  let sum = 0;
  let shouldDouble = false;
  for (let i = cardNumber.length - 1; i >= 0; i--) {
    const digitChar = cardNumber.charAt(i);
    if (!/^\d$/.test(digitChar)) {
      return false;
    }
    let digit = parseInt(digitChar, 10);
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}

function formatCardNumber(value) {
  const digits = value.replace(/\D/g, "").slice(0, 19);
  const groups = digits.match(/.{1,4}/g);
  return groups ? groups.join(" ") : digits;
}

function formatExpiry(value) {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length <= 2) {
    return digits;
  }
  return `${digits.slice(0, 2)}/${digits.slice(2)}`;
}

function sanitizeName(value) {
  return value.replace(/\s{2,}/g, " ");
}

function detectCardBrand(rawValue) {
  const digits = rawValue.replace(/\D/g, "");
  if (!digits) {
    return "Tarjeta";
  }
  if (/^4/.test(digits)) {
    return "Visa";
  }
  if (/^5[1-5]/.test(digits) || /^2(2[2-9]|[3-7]\d)/.test(digits)) {
    return "Mastercard";
  }
  if (/^3[47]/.test(digits)) {
    return "American Express";
  }
  if (/^3(0[0-5]|[68])/.test(digits)) {
    return "Diners Club";
  }
  if (/^6(?:011|5)/.test(digits)) {
    return "Discover";
  }
  return "Tarjeta";
}

function maskCardDisplay(rawValue) {
  const digits = rawValue.replace(/\D/g, "");
  const base = (digits + "*******************").slice(0, 19);
  const groups = base.match(/.{1,4}/g);
  return groups ? groups.join(" ").trim() : "**** **** **** ****";
}

function normalizeExpiryDisplay(exp) {
  if (!exp) {
    return "MM/YY";
  }
  const [mm = "", yy = ""] = exp.split("/");
  if (!mm || !yy) {
    return "MM/YY";
  }
  return `${mm.padEnd(2, "0")}/${yy.padEnd(2, "0")}`.slice(0, 5);
}

function formatNameDisplay(name) {
  const trimmed = name.trim();
  if (!trimmed) {
    return "Nombre Apellido";
  }
  return trimmed.toUpperCase();
}

function PaymentCardPreview({ number, name, exp, cvv, focus, brand }) {
  const isFlipped = focus === "cvv";
  const numberGroups = (number || "").split(" ").filter(Boolean);
  const safeCvv = cvv || "***";
  return (
    <div className="payment-card-preview" aria-hidden="true">
      <div className={`payment-card-visual ${isFlipped ? "payment-card-visual--flipped" : ""}`}>
        <div className="payment-card-face payment-card-face--front">
          <div className="payment-card-top">
            <span className="payment-card-brand">{brand}</span>
            <span className="payment-card-chip" />
          </div>
          <div className="payment-card-number">
            {numberGroups.length > 0
              ? numberGroups.map((group, index) => (
                  <span key={index} className="payment-card-number-group">
                    {group}
                  </span>
                ))
              : "**** **** **** ****"}
          </div>
          <div className="payment-card-footer">
            <div>
              <span className="payment-card-label">Titular</span>
              <span className="payment-card-value">{name}</span>
            </div>
            <div>
              <span className="payment-card-label">Expira</span>
              <span className="payment-card-value">{exp}</span>
            </div>
          </div>
        </div>

        <div className="payment-card-face payment-card-face--back">
          <div className="payment-card-stripe" />
          <div className="payment-card-cvv-row">
            <span className="payment-card-label">CVV</span>
            <span className="payment-card-cvv">{safeCvv}</span>
          </div>
          <div className="payment-card-brand payment-card-brand--back">{brand}</div>
        </div>
      </div>
    </div>
  );
}

const steps = [
  { label: "Carrito", status: "done" },
  { label: "Pago", status: "current" },
  { label: "Confirmacion", status: "pending" }
];

export default function PagoPage() {
  const [form, setForm] = useState({ card_num: "", exp: "", cvv: "", name: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [focusedField, setFocusedField] = useState("card_num");
  const navigate = useNavigate();
  const { items: cartItems, total: cartTotal, refresh: refreshCart, status: cartStatus, error: cartError } = useCart();
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setSummaryError("");
    refreshCart()
      .then(() => {
        if (!cancelled) {
          setSummaryError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setSummaryError(err?.message || "No se pudo cargar el resumen.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [refreshCart]);

  const summaryItems = useMemo(() => (Array.isArray(cartItems) ? cartItems : []), [cartItems]);
  const isSummaryLoading = cartStatus === "loading";
  const combinedSummaryError = summaryError || cartError?.message || "";

  const totalItems = useMemo(
    () => summaryItems.reduce((acc, item) => acc + (Number(item.cantidad) || 0), 0),
    [summaryItems]
  );

  const subtotal = useMemo(
    () =>
      summaryItems.reduce(
        (acc, item) => acc + (Number(item.acumulado) || (Number(item.precio_unitario) || 0) * (Number(item.cantidad) || 0)),
        0
      ),
    [summaryItems]
  );

  const totalToCharge = useMemo(() => {
    const baseTotal = Number(cartTotal) || 0;
    const candidate = Math.max(subtotal, baseTotal);
    return candidate < 0 ? 0 : candidate;
  }, [cartTotal, subtotal]);

  const cardBrand = useMemo(() => detectCardBrand(form.card_num), [form.card_num]);
  const displayNumber = useMemo(() => maskCardDisplay(form.card_num), [form.card_num]);
  const displayName = useMemo(() => formatNameDisplay(form.name), [form.name]);
  const displayExp = useMemo(() => normalizeExpiryDisplay(form.exp), [form.exp]);
  const displayCvv = useMemo(() => {
    if (!form.cvv) {
      return "***";
    }
    const clean = form.cvv.replace(/\D/g, "");
    if (!clean) {
      return "***";
    }
    const base = (clean + "***").slice(0, 4);
    return base.padEnd(clean.length < 3 ? 3 : base.length, "*");
  }, [form.cvv]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    let nextValue = value;
    if (name === "card_num") {
      nextValue = formatCardNumber(value);
    } else if (name === "exp") {
      nextValue = formatExpiry(value);
    } else if (name === "cvv") {
      nextValue = value.replace(/\D/g, "").slice(0, 4);
    } else if (name === "name") {
      nextValue = sanitizeName(value);
    }
    setForm((prev) => ({ ...prev, [name]: nextValue }));
  };

  const handleFocus = (field) => {
    setFocusedField(field);
  };

  const validate = () => {
    const errs = {};
    const cardNum = form.card_num.replace(/\s/g, "");
    if (!cardNum || !/^\d{13,19}$/.test(cardNum) || !luhnCheck(cardNum)) {
      errs.card_num = "Numero de tarjeta invalido.";
    }

    if (!form.exp || !/^\d{2}\/\d{2}$/.test(form.exp)) {
      errs.exp = "Fecha de expiracion invalida (MM/YY).";
    } else {
      const [mmRaw, yyRaw] = form.exp.split("/");
      const mm = Number(mmRaw);
      const yy = Number(yyRaw);
      if (!Number.isInteger(mm) || mm < 1 || mm > 12) {
        errs.exp = "Mes invalido.";
      } else {
        const expDate = new Date(2000 + yy, mm - 1, 1);
        const today = new Date();
        const startOfCurrentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        if (expDate < startOfCurrentMonth) {
          errs.exp = "Tarjeta expirada.";
        }
      }
    }

    if (!form.cvv || !/^\d{3,4}$/.test(form.cvv)) {
      errs.cvv = "CVV invalido.";
    }

    if (!form.name.trim()) {
      errs.name = "Nombre del titular requerido.";
    } else if (form.name.trim().length < 3) {
      errs.name = "Ingresa el nombre completo.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      return;
    }
    setLoading(true);
    try {
      const result = await API.carrito.pagar({
        ...form,
        card_num: form.card_num.replace(/\s/g, ""),
        name: form.name.trim()
      });
      await refreshCart().catch(() => {});
      const orderId = result?.order_id;
      if (orderId) {
        navigate(`/boleta?order=${orderId}`);
      } else {
        navigate("/boleta");
      }
    } catch (err) {
      const message = err?.payload?.error || err.message || "No se pudo procesar el pago. Inténtalo nuevamente.";
      setErrors({ general: message });
    } finally {
      setLoading(false);
    }
  };

  const showEmptySummary = !isSummaryLoading && !combinedSummaryError && summaryItems.length === 0;

  return (
    <div className="payment-page">
      <div className="payment-shell">
        <div className="payment-card">
          <header className="payment-header">
            <div className="payment-branding">
              <div className="payment-brand">Fitter Pay</div>
              <div className="payment-security">
                <svg className="payment-lock-icon" viewBox="0 0 20 20" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M5.5 8V6a4.5 4.5 0 0 1 9 0v2h.75A1.75 1.75 0 0 1 17 9.75v6.5A1.75 1.75 0 0 1 15.25 18H4.75A1.75 1.75 0 0 1 3 16.25v-6.5A1.75 1.75 0 0 1 4.75 8H5.5Zm2-2a2.5 2.5 0 1 1 5 0v2h-5V6Zm3.25 6.448a1.25 1.25 0 1 0-1.5 0V14.5h1.5v-2.052Z"
                  />
                </svg>
                <span>Pago cifrado SSL</span>
              </div>
            </div>
            <div className="payment-steps">
              {steps.map((step) => (
                <span key={step.label} className={`payment-step payment-step--${step.status}`}>
                  <span className="payment-step-dot" />
                  {step.label}
                </span>
              ))}
            </div>
          </header>

          <div className="payment-content">
            <section className="payment-main">
              <div className="payment-main-headline">
                <h1>Completa tu pago</h1>
                <p>Verifica los datos y finaliza la compra con una experiencia segura inspirada en los portales bancarios.</p>
              </div>

              <div className="payment-main-visuals">
                <PaymentCardPreview
                  number={displayNumber}
                  name={displayName}
                  exp={displayExp}
                  cvv={displayCvv}
                  focus={focusedField}
                  brand={cardBrand}
                />

                <div className="payment-card-logos" aria-hidden="true">
                  <span className="payment-logo payment-logo--visa">VISA</span>
                  <span className="payment-logo payment-logo--mastercard">Mastercard</span>
                  <span className="payment-logo payment-logo--amex">Amex</span>
                  <span className="payment-logo payment-logo--diners">Diners</span>
                </div>
              </div>

              <form className="payment-form" onSubmit={handleSubmit} noValidate>
                <label className="payment-field">
                  <span className="payment-label">Numero de tarjeta</span>
                  <input
                    type="text"
                    name="card_num"
                    inputMode="numeric"
                    autoComplete="cc-number"
                    value={form.card_num}
                    onChange={handleChange}
                    onFocus={() => handleFocus("card_num")}
                    placeholder="1234 5678 9012 3456"
                    className={errors.card_num ? "payment-input payment-input--error" : "payment-input"}
                  />
                  <span className="payment-hint">16 a 19 digitos, sin guiones.</span>
                  {errors.card_num && <span className="payment-error">{errors.card_num}</span>}
                </label>

                <div className="payment-field-grid">
                  <label className="payment-field">
                    <span className="payment-label">Expiracion (MM/YY)</span>
                    <input
                      type="text"
                      name="exp"
                      inputMode="numeric"
                      autoComplete="cc-exp"
                      value={form.exp}
                      onChange={handleChange}
                      onFocus={() => handleFocus("exp")}
                      placeholder="12/28"
                      className={errors.exp ? "payment-input payment-input--error" : "payment-input"}
                    />
                    {errors.exp && <span className="payment-error">{errors.exp}</span>}
                  </label>

                  <label className="payment-field">
                    <span className="payment-label">CVV</span>
                    <input
                      type="text"
                      name="cvv"
                      inputMode="numeric"
                      autoComplete="cc-csc"
                      value={form.cvv}
                      onChange={handleChange}
                      onFocus={() => handleFocus("cvv")}
                      placeholder="123"
                      className={errors.cvv ? "payment-input payment-input--error" : "payment-input"}
                    />
                    <span className="payment-hint">3 o 4 digitos segun la tarjeta.</span>
                    {errors.cvv && <span className="payment-error">{errors.cvv}</span>}
                  </label>
                </div>

                <label className="payment-field">
                  <span className="payment-label">Nombre del titular</span>
                  <input
                    type="text"
                    name="name"
                    autoComplete="cc-name"
                    value={form.name}
                    onChange={handleChange}
                    onFocus={() => handleFocus("name")}
                    placeholder="Nombre Apellido"
                    className={errors.name ? "payment-input payment-input--error" : "payment-input"}
                  />
                  {errors.name && <span className="payment-error">{errors.name}</span>}
                </label>

                {errors.general && <div className="payment-alert">{errors.general}</div>}

                <button type="submit" className="payment-submit" disabled={loading}>
                  {loading ? "Procesando pago..." : `Pagar ${formatearPrecio(totalToCharge)}`}
                </button>
                <div className="payment-terms">
                  <p>
                    Al continuar aceptas nuestros terminos y condiciones. Este cargo puede aparecer en tu estado de cuenta como
                    <strong> Fitter</strong>.
                  </p>
                </div>
              </form>

              <div className="payment-trust">
                <div className="payment-trust-item">
                  <svg className="payment-lock-icon" viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      fill="currentColor"
                      d="M5.5 8V6a4.5 4.5 0 0 1 9 0v2h.75A1.75 1.75 0 0 1 17 9.75v6.5A1.75 1.75 0 0 1 15.25 18H4.75A1.75 1.75 0 0 1 3 16.25v-6.5A1.75 1.75 0 0 1 4.75 8H5.5Zm2-2a2.5 2.5 0 1 1 5 0v2h-5V6Zm3.25 6.448a1.25 1.25 0 1 0-1.5 0V14.5h1.5v-2.052Z"
                    />
                  </svg>
                  <div>
                    <h3>Compra protegida</h3>
                    <p>Aplicamos protocolos PCI-DSS y verificacion de identidad para proteger tus pagos.</p>
                  </div>
                </div>
                <div className="payment-trust-item">
                  <svg className="payment-lock-icon" viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      fill="currentColor"
                      d="M10 3.5 4 9.5h1.5V15h3v-3h3v3h3V9.5H16L10 3.5Z"
                    />
                  </svg>
                  <div>
                    <h3>Entrega garantizada</h3>
                    <p>Si algo falla, nuestro equipo estara disponible 24/7 para ayudarte con tu pedido.</p>
                  </div>
                </div>
              </div>
            </section>

            <aside className="payment-sidebar">
              <div className="payment-summary">
                <div className="payment-summary-header">
                  <h2>Resumen del pedido</h2>
                  <p>{totalItems > 0 ? `${totalItems} articulo${totalItems > 1 ? "s" : ""}` : "Sin articulos en el carrito"}</p>
                </div>

                {isSummaryLoading && <div className="payment-summary-state">Cargando resumen...</div>}
                {combinedSummaryError && <div className="payment-summary-state payment-summary-state--error">{combinedSummaryError}</div>}
                {showEmptySummary && (
                  <div className="payment-summary-state">
                    <p>No hay productos asociados al pago.</p>
                    <button type="button" className="payment-secondary-btn" onClick={() => navigate("/carrito")}>
                      Volver al carrito
                    </button>
                  </div>
                )}

                {!isSummaryLoading && !combinedSummaryError && summaryItems.length > 0 && (
                  <>
                    <ul className="payment-summary-items">
                      {summaryItems.slice(0, 3).map((item) => (
                        <li key={item.producto_id || item.id} className="payment-summary-item">
                          <div>
                            <span className="payment-summary-name">{item.nombre || "Producto"}</span>
                            <span className="payment-summary-meta">x{item.cantidad || 1}</span>
                          </div>
                          <span className="payment-summary-price">
                            {formatearPrecio(Number(item.acumulado) || Number(item.precio_unitario) || 0)}
                          </span>
                        </li>
                      ))}
                    </ul>
                    {summaryItems.length > 3 && (
                      <div className="payment-summary-more">
                        + {summaryItems.length - 3} articulo{summaryItems.length - 3 > 1 ? "s" : ""} mas
                      </div>
                    )}

                    <div className="payment-summary-breakdown">
                      <div className="payment-summary-row">
                        <span>Subtotal</span>
                        <span>{formatearPrecio(subtotal)}</span>
                      </div>
                      <div className="payment-summary-row">
                        <span>Envio</span>
                        <span>Sin costo</span>
                      </div>
                      <div className="payment-summary-row payment-summary-row--total">
                        <span>Total a pagar</span>
                        <span>{formatearPrecio(totalToCharge)}</span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="payment-help">
                <h3>Necesitas ayuda?</h3>
                <p>Escribenos a soporte@fitter.com o llama al +56 9 1234 5678 para asistencia inmediata.</p>
                <button type="button" className="payment-secondary-btn" onClick={() => navigate("/carrito")}>
                  Revisar carrito
                </button>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
}




