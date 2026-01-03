import React, { useState } from 'react';

/**
 * Componente para procesar pagos con MercadoPago
 * 
 * Uso:
 * <MercadoPagoCheckout orderId={123} />
 */
const MercadoPagoCheckout = ({ orderId, userInfo }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePayment = async () => {
    try {
      setLoading(true);
      setError(null);

      // Crear preferencia de pago
      const response = await fetch('/api/payments/create-preference', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Importante para enviar cookies de sesión
        body: JSON.stringify({
          order_id: orderId,
          payer_info: {
            name: userInfo?.firstName || '',
            surname: userInfo?.lastName || '',
            email: userInfo?.email || '',
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al crear preferencia de pago');
      }

      const data = await response.json();

      // Redirigir a MercadoPago
      // En producción usar init_point, en desarrollo usar sandbox_init_point
      const checkoutUrl = import.meta.env.PROD
        ? data.init_point 
        : data.sandbox_init_point;

      window.location.href = checkoutUrl;

    } catch (err) {
      console.error('Error al procesar pago:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mercadopago-checkout">
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <button
        onClick={handlePayment}
        disabled={loading}
        className="btn btn-primary btn-lg"
      >
        {loading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Procesando...
          </>
        ) : (
          <>
            <i className="bi bi-credit-card me-2"></i>
            Pagar con MercadoPago
          </>
        )}
      </button>
    </div>
  );
};

export default MercadoPagoCheckout;


/**
 * Componente para mostrar el resultado del pago
 * Usar en las páginas de retorno: /payment/success, /payment/failure, /payment/pending
 */
export const PaymentResult = ({ status }) => {
  const getStatusInfo = () => {
    switch (status) {
      case 'success':
        return {
          title: '¡Pago Exitoso!',
          message: 'Tu pago ha sido procesado correctamente.',
          icon: 'bi-check-circle-fill text-success',
          variant: 'success',
        };
      case 'failure':
        return {
          title: 'Pago Rechazado',
          message: 'No se pudo procesar tu pago. Por favor, intenta nuevamente.',
          icon: 'bi-x-circle-fill text-danger',
          variant: 'danger',
        };
      case 'pending':
        return {
          title: 'Pago Pendiente',
          message: 'Tu pago está siendo procesado. Te notificaremos cuando se complete.',
          icon: 'bi-clock-fill text-warning',
          variant: 'warning',
        };
      default:
        return {
          title: 'Estado Desconocido',
          message: 'No pudimos determinar el estado de tu pago.',
          icon: 'bi-question-circle-fill text-secondary',
          variant: 'secondary',
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="payment-result text-center py-5">
      <div className={`alert alert-${statusInfo.variant}`} role="alert">
        <i className={`bi ${statusInfo.icon} fs-1 mb-3 d-block`}></i>
        <h2>{statusInfo.title}</h2>
        <p className="mb-0">{statusInfo.message}</p>
      </div>

      <div className="mt-4">
        <a href="/orders" className="btn btn-primary me-2">
          Ver mis órdenes
        </a>
        <a href="/" className="btn btn-outline-secondary">
          Volver al inicio
        </a>
      </div>
    </div>
  );
};


/**
 * Hook personalizado para obtener el estado de un pago
 */
export const usePaymentStatus = (paymentId) => {
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (!paymentId) {
      setLoading(false);
      return;
    }

    const fetchPaymentStatus = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/payments/status/${paymentId}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Error al obtener estado del pago');
        }

        const data = await response.json();
        setPayment(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPaymentStatus();
  }, [paymentId]);

  return { payment, loading, error };
};


/**
 * Componente para mostrar el estado de un pago en tiempo real
 */
export const PaymentStatus = ({ paymentId }) => {
  const { payment, loading, error } = usePaymentStatus(paymentId);

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
      </div>
    );
  }

  if (!payment) {
    return null;
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: 'warning',
      approved: 'success',
      rejected: 'danger',
      cancelled: 'secondary',
      refunded: 'info',
      in_process: 'primary',
    };
    return statusMap[status] || 'secondary';
  };

  return (
    <div className="payment-status card">
      <div className="card-body">
        <h5 className="card-title">Estado del Pago</h5>
        
        <div className="row mt-3">
          <div className="col-md-6">
            <p>
              <strong>Estado:</strong>{' '}
              <span className={`badge bg-${getStatusBadge(payment.status)}`}>
                {payment.status}
              </span>
            </p>
            <p><strong>Monto:</strong> ${payment.transaction_amount.toLocaleString('es-CL')} {payment.currency_id}</p>
            <p><strong>Orden ID:</strong> #{payment.order_id}</p>
          </div>
          
          <div className="col-md-6">
            {payment.payment_method_id && (
              <p><strong>Método de pago:</strong> {payment.payment_method_id}</p>
            )}
            <p><strong>Fecha de creación:</strong> {new Date(payment.created_at).toLocaleString('es-CL')}</p>
            {payment.approved_at && (
              <p><strong>Fecha de aprobación:</strong> {new Date(payment.approved_at).toLocaleString('es-CL')}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
