import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "../styles/pago/style_pago.css";

export default function PaymentPendingPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [orderData, setOrderData] = useState(null);

  useEffect(() => {
    const orderId = searchParams.get('external_reference') || 
                    searchParams.get('order_id') || 
                    localStorage.getItem('pending_order_id');
    
    if (orderId) {
      localStorage.removeItem('pending_order_id');
      setOrderData({ id: orderId });
    }
  }, [searchParams]);

  return (
    <div className="payment-page">
      <div className="payment-shell">
        <div className="payment-card">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '4rem', color: '#ffc107', marginBottom: '1rem' }}>⏱</div>
            <h1 style={{ color: '#ffc107', marginBottom: '1rem' }}>Pago pendiente</h1>
            <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '2rem' }}>
              Tu pago está siendo procesado. Te notificaremos cuando se confirme.
            </p>
            
            {orderData?.id && (
              <div style={{ 
                background: '#f8f9fa', 
                padding: '1.5rem', 
                borderRadius: '8px',
                marginBottom: '2rem'
              }}>
                <p style={{ margin: '0.5rem 0' }}>
                  <strong>Número de orden:</strong> #{orderData.id}
                </p>
                <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#666' }}>
                  El proceso puede tardar algunos minutos.
                </p>
              </div>
            )}

            <div style={{ 
              background: '#e7f3ff', 
              padding: '1.5rem', 
              borderRadius: '8px',
              marginBottom: '2rem',
              border: '1px solid #b3d9ff'
            }}>
              <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#004085' }}>
                <strong>¿Qué sigue?</strong>
              </p>
              <ul style={{ textAlign: 'left', margin: '1rem 0', paddingLeft: '2rem', color: '#004085' }}>
                <li>Recibirás un email cuando se confirme el pago</li>
                <li>Puedes revisar el estado en tu historial de órdenes</li>
                <li>Si tienes dudas, contacta a soporte</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                onClick={() => navigate('/')}
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
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
