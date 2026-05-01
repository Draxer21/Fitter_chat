import { useEffect, useRef, useState } from 'react';
import { initMercadoPago, CardPayment } from '@mercadopago/sdk-react';
import { API } from '../services/apijs';

// ── MP SDK initialization guard (module-level singleton) ──
let mpInitializedKey = null;

// ── Test cards for Chile sandbox ──
const TEST_CARDS = [
  { brand: 'Visa',       number: '4009 1753 3280 6176', cvv: '123', exp: '11/25' },
  { brand: 'Mastercard', number: '5031 7557 3453 0604', cvv: '123', exp: '11/25' },
  { brand: 'Amex',       number: '3711 8030 3257 522',  cvv: '1234', exp: '11/25' },
];

// ── CSRF helper — grabs a token from the backend ──
let _csrfToken = null;
let _csrfPromise = null;

async function getCsrfToken() {
  if (_csrfToken) return _csrfToken;
  if (!_csrfPromise) {
    _csrfPromise = fetch('/auth/csrf-token', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => {
        _csrfToken = d?.csrf_token || '';
        return _csrfToken;
      })
      .finally(() => { _csrfPromise = null; });
  }
  return _csrfPromise;
}

async function csrfHeaders(extra = {}) {
  const token = await getCsrfToken();
  return { ...extra, ...(token ? { 'X-CSRF-Token': token } : {}) };
}

// ════════════════════════════════════════════════
export default function CheckoutForm({ orderId, total, onSuccess, onError, onClose }) {
  const [ready, setReady]           = useState(false);
  const [processing, setProcessing] = useState(false);
  const [publicKey, setPublicKey]   = useState(null);
  const [isTestMode, setIsTestMode] = useState(false);
  const [showTestCards, setShowTestCards] = useState(false);
  const hasFetched = useRef(false);

  // ── Fetch public key from backend, fall back to VITE env var ──
  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    const envKey = import.meta.env.VITE_MP_PUBLIC_KEY || '';

    fetch('/api/payments/public-key', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => {
        // Use backend key if set, otherwise fall back to frontend env var
        const key = d?.public_key || envKey;
        if (key) {
          setPublicKey(key);
          setIsTestMode(Boolean(d?.is_test_mode) || key.startsWith('TEST-'));
        } else {
          onError('No se pudo cargar la clave de pago. Contacta a soporte.');
        }
      })
      .catch(() => {
        // Network error → use VITE env var
        if (envKey) {
          setPublicKey(envKey);
          setIsTestMode(envKey.startsWith('TEST-'));
        } else {
          onError('No se pudo conectar con el servidor de pagos.');
        }
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Initialize MP SDK once per key ──
  useEffect(() => {
    if (!publicKey) return;
    if (mpInitializedKey !== publicKey) {
      initMercadoPago(publicKey, { locale: 'es-CL' });
      mpInitializedKey = publicKey;
    }
    setReady(true);
  }, [publicKey]);

  // ── Handle CardPayment Brick submit ──
  const handleSubmit = async (formData) => {
    setProcessing(true);
    const d = formData?.formData ?? formData;

    const payload = {
      token:              d.token,
      payment_method_id:  d.payment_method_id ?? d.paymentMethodId,
      issuer_id:          d.issuer_id ?? d.issuerId ?? null,
      installments:       d.installments ?? 1,
      transaction_amount: total,
      order_id:           orderId,
      payer: {
        email:          d.payer?.email,
        identification: d.payer?.identification ?? {},
      },
    };

    try {
      const headers = await csrfHeaders({ 'Content-Type': 'application/json' });
      const res = await fetch('/api/payments/process-card', {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify(payload),
      });

      const result = await res.json();

      if (!res.ok) {
        onError(result.error || 'El pago fue rechazado.');
        return;
      }

      if (result.status === 'approved') {
        onSuccess(result);
      } else if (result.status === 'in_process' || result.status === 'pending') {
        onSuccess({ ...result, pending: true });
      } else {
        onError(`Pago ${result.status}: ${result.status_detail || 'intenta con otro medio.'}`);
      }
    } catch {
      onError('Error de conexión al procesar el pago.');
    } finally {
      setProcessing(false);
    }
  };

  const customization = {
    paymentMethods: { creditCard: 'all', debitCard: 'all' },
    visual: { style: { theme: 'default' } },
  };

  return (
    <div
      className="checkout-form-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="checkout-form-modal">
        {/* Header */}
        <div className="checkout-form-header">
          <h4 className="checkout-form-title">
            <i className="fa-solid fa-lock me-2 text-success" />
            Pago seguro
          </h4>
          <button className="checkout-form-close" onClick={onClose} aria-label="Cerrar">
            <i className="fa-solid fa-xmark" />
          </button>
        </div>

        {/* Amount */}
        <div className="checkout-form-amount">
          <span>Total a pagar</span>
          <strong>
            {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(total)}
          </strong>
        </div>

        {/* ── Test-mode banner ── */}
        {isTestMode && (
          <div className="checkout-testmode-banner">
            <div className="checkout-testmode-header" onClick={() => setShowTestCards((v) => !v)}>
              <span>
                <i className="fa-solid fa-flask me-2" />
                Modo de prueba — usa tarjetas de test
              </span>
              <i className={`fa-solid fa-chevron-${showTestCards ? 'up' : 'down'}`} />
            </div>

            {showTestCards && (
              <table className="checkout-testmode-table">
                <thead>
                  <tr>
                    <th>Red</th>
                    <th>Número</th>
                    <th>CVV</th>
                    <th>Vencimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {TEST_CARDS.map((c) => (
                    <tr key={c.brand}>
                      <td>{c.brand}</td>
                      <td>
                        <code
                          className="checkout-testmode-copy"
                          title="Click para copiar"
                          onClick={() => navigator.clipboard?.writeText(c.number.replace(/\s/g, ''))}
                        >
                          {c.number}
                        </code>
                      </td>
                      <td><code>{c.cvv}</code></td>
                      <td><code>{c.exp}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <p className="checkout-testmode-note">
              Cualquier nombre, RUT: <code>11111111-1</code>, email: cualquiera
            </p>
          </div>
        )}

        {/* Processing spinner */}
        {processing && (
          <div className="checkout-form-processing">
            <div className="spinner-border spinner-border-sm text-primary me-2" />
            Procesando pago...
          </div>
        )}

        {/* Loading key */}
        {!publicKey && !processing && (
          <div className="checkout-form-processing">
            <div className="spinner-border spinner-border-sm text-primary me-2" />
            Cargando formulario de pago...
          </div>
        )}

        {/* CardPayment Brick */}
        {ready && publicKey && !processing && (
          <CardPayment
            initialization={{ amount: total }}
            customization={customization}
            onSubmit={handleSubmit}
            onError={(err) => {
              const msg = err?.message || '';
              // Hint extra cuando el error es de tokenización en modo test
              const hint = isTestMode && msg.toLowerCase().includes('token')
                ? ' (En modo prueba usa una tarjeta de test — ver tabla arriba)'
                : '';
              onError(`Error en el formulario de pago: ${msg}${hint}`);
              if (!showTestCards && isTestMode) setShowTestCards(true);
            }}
          />
        )}

        <p className="checkout-form-footer">
          <i className="fa-solid fa-shield-halved me-1 text-muted" />
          Tus datos están protegidos con cifrado SSL
        </p>
      </div>
    </div>
  );
}
