import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "../styles/pago/style_pago.css";

export default function PaymentFailurePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  return (
    <div className="payment-page">
      <div className="payment-shell">
        <div className="payment-card">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '4rem', color: '#dc3545', marginBottom: '1rem' }}>✗</div>
            <h1 style={{ color: '#dc3545', marginBottom: '1rem' }}>Pago rechazado</h1>
            <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '2rem' }}>
              No se pudo procesar tu pago. Por favor, intenta nuevamente.
            </p>
            
            <div style={{ 
              background: '#fff3cd', 
              padding: '1.5rem', 
              borderRadius: '8px',
              marginBottom: '2rem',
              border: '1px solid #ffc107'
            }}>
              <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#856404' }}>
                <strong>Posibles causas:</strong>
              </p>
              <ul style={{ textAlign: 'left', margin: '1rem 0', paddingLeft: '2rem', color: '#856404' }}>
                <li>Fondos insuficientes</li>
                <li>Datos de tarjeta incorrectos</li>
                <li>Tarjeta bloqueada o vencida</li>
                <li>Límite de compra excedido</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                onClick={() => navigate('/pago')}
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
                Intentar nuevamente
              </button>
              <button 
                onClick={() => navigate('/carrito')}
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
                Volver al carrito
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
