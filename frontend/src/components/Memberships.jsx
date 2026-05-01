import React, { useEffect, useState } from 'react';
import { useLocale } from '../contexts/LocaleContext';
import { useCart } from '../contexts/CartContext';
import { API } from '../services/apijs';
import { formatearPrecio } from '../utils/formatPrice';

export default function Memberships() {
  const { t } = useLocale();
  const { addItem } = useCart();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    API.productos
      .list('?categoria=Membership')
      .then((data) => {
        if (!active) return;
        setPlans(Array.isArray(data) ? data : []);
        setLoadError('');
      })
      .catch((err) => {
        if (!active) return;
        setPlans([]);
        setLoadError(err?.message || 'No se pudieron cargar las membresías disponibles.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const handleAdd = async (productId) => {
    try {
      await addItem(productId);
    } catch (err) {
      alert(err?.message || 'No pudimos agregar el plan al carrito.');
    }
  };

  return (
    <section className="container py-5">
      <h2 className="text-center mb-5">{t('memberships.title')}</h2>

      {loading && (
        <div className="text-center py-4">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">{t('common.loading')}</span>
          </div>
        </div>
      )}

      {loadError && (
        <div className="alert alert-warning text-center">{loadError}</div>
      )}

      {!loading && !loadError && plans.length === 0 && (
        <p className="text-center text-muted">No hay planes de membresía disponibles.</p>
      )}

      <div className="row justify-content-center">
        {plans.map((plan) => {
          const features = Array.isArray(plan.highlights) ? plan.highlights : [];
          const sinStock = (plan.stock ?? 0) <= 0;

          return (
            <div key={plan.id} className="col-md-4 mb-4">
              <div className="card h-100 shadow-sm">
                <div className="card-body d-flex flex-column text-center">

                  <h5 className="card-title text-uppercase fw-bold mb-1">
                    {plan.nombre}
                  </h5>

                  {plan.descripcion && (
                    <p className="text-muted small mb-3">{plan.descripcion}</p>
                  )}

                  <h3 className="text-primary mb-3">
                    {formatearPrecio(plan.precio)}
                    <small className="text-muted fs-6">{t('memberships.period.perMonth')}</small>
                  </h3>

                  {features.length > 0 && (
                    <ul className="list-unstyled text-start mt-2 mb-4 flex-grow-1">
                      {features.map((feature, i) => (
                        <li key={i} className="mb-2">
                          <i className="fas fa-check text-success me-2"></i>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  )}

                  <button
                    className="btn btn-primary btn-lg mt-auto"
                    disabled={sinStock}
                    onClick={() => handleAdd(plan.id)}
                  >
                    {sinStock ? 'Sin disponibilidad' : t('memberships.selectPlan')}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
