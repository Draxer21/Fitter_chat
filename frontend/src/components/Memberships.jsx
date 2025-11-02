import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocale } from '../contexts/LocaleContext';
import { useCart } from '../contexts/CartContext';
import { API } from '../services/apijs';
import { formatearPrecio } from '../utils/formatPrice';

const PLANS = [
  {
    id: 'basic',
    nameKey: 'memberships.plans.basic.name',
    price: '$29.990',
    periodKey: 'memberships.period.perMonth',
    featureKeys: [
      'memberships.plans.basic.feature.1',
      'memberships.plans.basic.feature.2',
      'memberships.plans.basic.feature.3',
      'memberships.plans.basic.feature.4',
    ],
  },
  {
    id: 'premium',
    nameKey: 'memberships.plans.premium.name',
    price: '$49.990',
    periodKey: 'memberships.period.perMonth',
    featureKeys: [
      'memberships.plans.premium.feature.1',
      'memberships.plans.premium.feature.2',
      'memberships.plans.premium.feature.3',
      'memberships.plans.premium.feature.4',
      'memberships.plans.premium.feature.5',
    ],
  },
  {
    id: 'black',
    nameKey: 'memberships.plans.black.name',
    price: '$69.990',
    periodKey: 'memberships.period.perMonth',
    featureKeys: [
      'memberships.plans.black.feature.1',
      'memberships.plans.black.feature.2',
      'memberships.plans.black.feature.3',
      'memberships.plans.black.feature.4',
      'memberships.plans.black.feature.5',
    ],
  },
];

export default function Memberships() {
  const { t } = useLocale();
  const { addItem } = useCart();
  const [membershipProducts, setMembershipProducts] = useState([]);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    API.productos
      .list('?categoria=Membership')
      .then((data) => {
        if (!active) return;
        setMembershipProducts(Array.isArray(data) ? data : []);
        setLoadError('');
      })
      .catch((err) => {
        if (!active) return;
        setMembershipProducts([]);
        setLoadError(err?.message || 'No se pudieron cargar las membresías disponibles.');
      });
    return () => {
      active = false;
    };
  }, []);

  const resolveProductForPlan = useCallback(
    (plan, index) => {
      if (!membershipProducts.length) {
        return null;
      }
      const normalizedId = plan.id.toLowerCase();
      const byName = membershipProducts.find((product) => {
        const name = (product.nombre || '').toLowerCase();
        return name.includes(normalizedId);
      });
      if (byName) {
        return byName;
      }
      return membershipProducts[index] || membershipProducts[0];
    },
    [membershipProducts]
  );

  const displayPlans = useMemo(
    () =>
      PLANS.map((plan, index) => {
        const product = resolveProductForPlan(plan, index);
        return {
          ...plan,
          product,
          displayPrice:
            product && product.precio !== undefined && product.precio !== null
              ? formatearPrecio(product.precio)
              : plan.price,
        };
      }),
    [resolveProductForPlan]
  );

  const handleAddPlan = async (plan) => {
    try {
      const product = plan.product;
      if (!product) {
        throw new Error(
          'No encontramos un producto asociado a esta membresía. Revisa el catálogo de productos de categoría "Membership".'
        );
      }
      await addItem(product.id);
    } catch (err) {
      alert(err?.message || "No pudimos agregar el plan al carrito.");
    }
  };

  return (
    <section className="container py-5">
      <h2 className="text-center mb-5">{t('memberships.title')}</h2>
      {loadError && <div className="alert alert-warning text-center">{loadError}</div>}
      <div className="row">
        {displayPlans.map((plan, index) => (
          <div key={plan.id} className="col-md-4 mb-4">
            <div className="card h-100 shadow-sm">
              <div className="card-body text-center">
                <h5 className="card-title">{t(plan.nameKey)}</h5>
                <h3 className="text-primary">
                  {plan.displayPrice}
                  <small className="text-muted">{t(plan.periodKey)}</small>
                </h3>
                <ul className="list-unstyled mt-3">
                  {plan.featureKeys.map((featureKey) => (
                    <li key={featureKey} className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>
                      {t(featureKey)}
                    </li>
                  ))}
                </ul>
                <button
                  className="btn btn-primary btn-lg mt-3"
                  onClick={() => handleAddPlan(plan)}
                >
                  {t('memberships.selectPlan')}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
