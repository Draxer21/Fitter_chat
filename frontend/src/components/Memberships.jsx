import React from 'react';
import { useLocale } from '../contexts/LocaleContext';

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

  return (
    <section className="container py-5">
      <h2 className="text-center mb-5">{t('memberships.title')}</h2>
      <div className="row">
        {PLANS.map((plan) => (
          <div key={plan.id} className="col-md-4 mb-4">
            <div className="card h-100 shadow-sm">
              <div className="card-body text-center">
                <h5 className="card-title">{t(plan.nameKey)}</h5>
                <h3 className="text-primary">
                  {plan.price}
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
                <button className="btn btn-primary btn-lg mt-3">
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
