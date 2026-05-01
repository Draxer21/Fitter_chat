import { useEffect, useState } from 'react';
import { initMercadoPago, CardPayment } from '@mercadopago/sdk-react';
import { API } from '../services/apijs';

// Track which key MP was initialized with so we can detect mismatches
let mpInitializedKey = null;

export default function CheckoutForm({ orderId, total, onSuccess, onError, onClose }) {
  const [ready, setReady] = useState(false);
  const [processing, setProcessing] = useState(false);
  // Always fetch from backend — it's the source of truth for test vs. production
  const [publicKey, setPublicKey] = useState(null);

  // Always fetch the public key from the backend to guarantee key consistency
  useEffect(() => {
    fetch('/api/payments/public-key', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => {
        if (d.public_key) setPublicKey(d.public_key);
      })
      .catch(() => {
        // Fallback to env var if backend is unreachable
        const envKey = import.meta.env.VITE_MP_PUBLIC_KEY || '';
        if (envKey) setPublicKey(envKey);
      });
  }, []);

  useEffect(() => {
    if (!publicKey) return;
    // Only (re-)initialize when the key actually changes
    if (mpInitializedKey !== publicKey) {
      initMercadoPago(publicKey, { locale: 'es-CL' });
      mpInitializedKey = publicKey;
    }
    setReady(true);
  }, [publicKey]);

  const handleSubmit = async (formData) => {
    setProcessing(true);
    // El Brick puede pasar { formData, additionalData } o el objeto plano
    const d = formData?.formData ?? formData;

    const payload = {
      token:             d.token,
      payment_method_id: d.payment_method_id ?? d.paymentMethodId,
      issuer_id:         d.issuer_id         ?? d.issuerId ?? null,
      installments:      d.installments      ?? 1,
      transaction_amount: total,   // siempre usamos el total de la orden
      order_id:          orderId,
      payer: {
        email:          d.payer?.email,
        identification: d.payer?.identification ?? {},
      },
    };

    try {
      const res = await fetch('/api/payments/process-card', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
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
    paymentMethods: {
      creditCard: 'all',
      debitCard: 'all',
    },
    visual: {
      style: {
        theme: 'default',
      },
    },
  };

  return (
    <div className="checkout-form-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="checkout-form-modal">
        <div className="checkout-form-header">
          <h4 className="checkout-form-title">
            <i className="fa-solid fa-lock me-2 text-success" />
            Pago seguro
          </h4>
          <button className="checkout-form-close" onClick={onClose} aria-label="Cerrar">
            <i className="fa-solid fa-xmark" />
          </button>
        </div>

        <div className="checkout-form-amount">
          <span>Total a pagar</span>
          <strong>
            {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(total)}
          </strong>
        </div>

        {processing && (
          <div className="checkout-form-processing">
            <div className="spinner-border spinner-border-sm text-primary me-2" />
            Procesando pago...
          </div>
        )}

        {!publicKey && (
          <div className="checkout-form-processing">
            <div className="spinner-border spinner-border-sm text-primary me-2" />
            Cargando formulario de pago...
          </div>
        )}

        {ready && publicKey && !processing && (
          <CardPayment
            initialization={{ amount: total }}
            customization={customization}
            onSubmit={handleSubmit}
            onError={(err) => onError('Error en el formulario de pago: ' + (err?.message || ''))}
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
