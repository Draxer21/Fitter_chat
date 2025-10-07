import React from 'react';

export default function Memberships() {
  const memberships = [
    {
      id: 1,
      name: 'BÁSICO',
      price: '$29.990',
      period: '/mes',
      features: [
        'Acceso ilimitado a todas las sedes',
        'Entrenamiento libre',
        'Clases grupales',
        'Acceso a sauna y duchas'
      ]
    },
    {
      id: 2,
      name: 'PREMIUM',
      price: '$49.990',
      period: '/mes',
      features: [
        'Todo lo del Básico',
        'Entrenamiento personalizado',
        'Acceso a zona VIP',
        'Bebidas energéticas ilimitadas',
        'Descuentos en suplementos'
      ]
    },
    {
      id: 3,
      name: 'BLACK',
      price: '$69.990',
      period: '/mes',
      features: [
        'Todo lo del Premium',
        'Acceso 24/7',
        'Masajista personal',
        'Nutricionista incluido',
        'Invitados ilimitados'
      ]
    }
  ];

  return (
    <section className="container py-5">
      <h2 className="text-center mb-5">Nuestras Membresías</h2>
      <div className="row">
        {memberships.map((membership) => (
          <div key={membership.id} className="col-md-4 mb-4">
            <div className="card h-100 shadow-sm">
              <div className="card-body text-center">
                <h5 className="card-title">{membership.name}</h5>
                <h3 className="text-primary">{membership.price}<small className="text-muted">{membership.period}</small></h3>
                <ul className="list-unstyled mt-3">
                  {membership.features.map((feature, index) => (
                    <li key={index} className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>{feature}
                    </li>
                  ))}
                </ul>
                <button className="btn btn-primary btn-lg mt-3">Elegir Plan</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
