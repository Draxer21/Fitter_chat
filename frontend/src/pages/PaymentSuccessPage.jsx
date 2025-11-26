import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { API } from "../services/apijs";
import { formatearPrecio } from "../utils/formatPrice";
import "../styles/pago/style_pago.css";

export default function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [orderData, setOrderData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadOrderData = async () => {
      try {
        // Obtener payment_id y order_id de los parámetros de URL
        const paymentId = searchParams.get('payment_id');
        const orderId = searchParams.get('external_reference') || 
                        searchParams.get('order_id') || 
                        localStorage.getItem('pending_order_id');
        
        if (!orderId) {
          setError("No se encontró el número de orden");
          setLoading(false);
          return;
        }
        
        // Si hay payment_id, verificar el pago en MercadoPago primero
        if (paymentId) {
          try {
            await API.payments.verifyPayment(paymentId);
          } catch (verifyErr) {
            console.warn("Error verificando pago:", verifyErr);
            // Continuar aunque falle la verificación
          }
        }
        
        // Limpiar localStorage
        localStorage.removeItem('pending_order_id');
        
        // Cargar detalles de la orden desde el backend
        const data = await API.payments.getOrderPayment(orderId);
        setOrderData(data);
      } catch (err) {
        console.error("Error cargando orden:", err);
        setError("No se pudieron cargar los detalles de la orden");
      } finally {
        setLoading(false);
      }
    };

    loadOrderData();
  }, [searchParams]);

  const handleViewOrder = () => {
    if (orderData?.id) {
      navigate(`/boleta?order=${orderData.id}`);
    } else {
      navigate('/');
    }
  };

  if (loading) {
    return (
      <div className="payment-page">
        <div className="payment-shell">
          <div className="payment-card">
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              Verificando pago...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="payment-page">
        <div className="payment-shell">
          <div className="payment-card">
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <p style={{ color: '#dc3545' }}>{error}</p>
              <button onClick={() => navigate('/')} style={{
                marginTop: '1rem',
                padding: '0.75rem 2rem',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}>
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-page">
      <div className="payment-shell">
        <div className="payment-card">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '4rem', color: '#28a745', marginBottom: '1rem' }}>✓</div>
            <h1 style={{ color: '#28a745', marginBottom: '1rem' }}>¡Pago exitoso!</h1>
            <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '2rem' }}>
              Tu pago ha sido procesado correctamente.
            </p>
            
            {orderData && (
              <div style={{ 
                background: '#f8f9fa', 
                padding: '1.5rem', 
                borderRadius: '8px',
                marginBottom: '2rem'
              }}>
                <p style={{ margin: '0.5rem 0' }}>
                  <strong>Número de orden:</strong> #{orderData.id}
                </p>
                {orderData.total_amount && (
                  <p style={{ margin: '0.5rem 0' }}>
                    <strong>Total:</strong> {formatearPrecio(orderData.total_amount)}
                  </p>
                )}
                {orderData.customer_name && (
                  <p style={{ margin: '0.5rem 0' }}>
                    <strong>Cliente:</strong> {orderData.customer_name}
                  </p>
                )}
                <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#666' }}>
                  Recibirás un correo con los detalles de tu compra.
                </p>
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                onClick={handleViewOrder}
                style={{
                  padding: '0.75rem 2rem',
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                Ver orden
              </button>
              <button 
                onClick={() => navigate('/')}
                style={{
                  padding: '0.75rem 2rem',
                  background: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
