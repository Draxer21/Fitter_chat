# Integración de MercadoPago

Esta guía explica cómo configurar y usar la integración de MercadoPago para procesar pagos en Fitter.

## Configuración

### 1. Obtener Credenciales

1. Crea una cuenta en [MercadoPago Chile](https://www.mercadopago.cl/)
2. Ve al [Panel de Desarrolladores](https://www.mercadopago.cl/developers/panel/credentials)
3. Obtén tus credenciales:
   - **Access Token**: Para comunicarte con la API de MercadoPago
   - **Public Key**: Para el frontend (opcional, para Checkout Pro)

### 2. Configurar Variables de Entorno

Edita el archivo `.env` en la raíz del proyecto:

```env
# MercadoPago configuration
MERCADOPAGO_ACCESS_TOKEN=tu_access_token_aqui
MERCADOPAGO_PUBLIC_KEY=tu_public_key_aqui
MERCADOPAGO_NOTIFICATION_URL=https://tu-dominio.com/api/payments/webhook
FRONTEND_URL=http://localhost:3000
```

**Importante:**
- En desarrollo, usa las credenciales de **Sandbox/Testing**
- En producción, usa las credenciales de **Producción**
- La `MERCADOPAGO_NOTIFICATION_URL` debe ser accesible públicamente para recibir webhooks

### 3. Configurar Webhooks en MercadoPago

1. Ve a [Configuración de Webhooks](https://www.mercadopago.cl/developers/panel/webhooks)
2. Agrega una nueva URL de notificación: `https://tu-dominio.com/api/payments/webhook`
3. Selecciona los eventos:
   - `payment` (pagos)
   - `merchant_order` (órdenes)

## Endpoints de la API

### 1. Crear Preferencia de Pago

**POST** `/api/payments/create-preference`

Crea una preferencia de pago en MercadoPago para una orden existente.

**Headers:**
```
Cookie: session=<session_id>
Content-Type: application/json
```

**Body:**
```json
{
  "order_id": 123,
  "payer_info": {
    "name": "Juan",
    "surname": "Pérez",
    "email": "juan@example.com"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "preference_id": "123456789-abc123-def456",
  "init_point": "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=...",
  "sandbox_init_point": "https://sandbox.mercadopago.cl/checkout/v1/redirect?pref_id=...",
  "payment_id": 1
}
```

### 2. Webhook de Notificaciones

**POST** `/api/payments/webhook`

Endpoint para recibir notificaciones de MercadoPago. Este endpoint es llamado automáticamente por MercadoPago.

**No requiere autenticación** (viene de MercadoPago)

### 3. Obtener Estado de un Pago

**GET** `/api/payments/status/<payment_id>`

Obtiene el estado actual de un pago.

**Response (200):**
```json
{
  "id": 1,
  "order_id": 123,
  "preference_id": "123456789-abc123",
  "payment_id": "987654321",
  "status": "approved",
  "transaction_amount": 25000,
  "currency_id": "CLP",
  "payment_method_id": "credit_card",
  "created_at": "2025-11-25T12:00:00",
  "approved_at": "2025-11-25T12:05:00"
}
```

### 4. Obtener Pago de una Orden

**GET** `/api/payments/order/<order_id>`

Obtiene la información del pago asociado a una orden.

## Estados de Pago

Los pagos pueden tener los siguientes estados:

- `pending`: Pago pendiente
- `approved`: Pago aprobado
- `rejected`: Pago rechazado
- `cancelled`: Pago cancelado
- `refunded`: Pago reembolsado
- `in_process`: Pago en proceso

## Flujo de Trabajo

### 1. Cliente crea una orden

```javascript
// Frontend crea una orden primero
const response = await fetch('/api/orders/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    items: [
      { product_id: 1, quantity: 2, price: 12500 }
    ]
  })
});

const order = await response.json();
```

### 2. Cliente solicita crear preferencia de pago

```javascript
const paymentResponse = await fetch('/api/payments/create-preference', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    order_id: order.id,
    payer_info: {
      name: 'Juan',
      surname: 'Pérez',
      email: 'juan@example.com'
    }
  })
});

const payment = await paymentResponse.json();
```

### 3. Redirigir al cliente a MercadoPago

```javascript
// En desarrollo/testing usar sandbox_init_point
// En producción usar init_point
if (process.env.NODE_ENV === 'production') {
  window.location.href = payment.init_point;
} else {
  window.location.href = payment.sandbox_init_point;
}
```

### 4. MercadoPago procesa el pago

El cliente completa el pago en MercadoPago.

### 5. MercadoPago notifica al webhook

MercadoPago envía una notificación al endpoint `/api/payments/webhook` con información del pago.

### 6. El sistema actualiza el estado

El webhook actualiza automáticamente:
- Estado del pago en la tabla `payment`
- Estado de la orden en la tabla `order`

### 7. Cliente es redirigido de vuelta

MercadoPago redirige al cliente a:
- `/payment/success` si el pago fue aprobado
- `/payment/failure` si el pago fue rechazado
- `/payment/pending` si el pago está pendiente

## Modelo de Datos

### Tabla Payment

```python
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    preference_id = db.Column(db.String(255), unique=True)
    payment_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(50))
    transaction_amount = db.Column(db.Float)
    currency_id = db.Column(db.String(10))
    payment_method_id = db.Column(db.String(50))
    payment_type_id = db.Column(db.String(50))
    merchant_order_id = db.Column(db.String(255))
    external_reference = db.Column(db.String(255))
    payer_email = db.Column(db.String(255))
    payer_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
```

## Testing en Sandbox

MercadoPago proporciona tarjetas de prueba para testing:

### Tarjetas de Crédito de Prueba (Chile)

| Tarjeta | Número | CVV | Fecha |
|---------|--------|-----|-------|
| Visa | 4168 8188 4444 7115 | 123 | 11/25 |
| Mastercard | 5416 7526 0258 2580 | 123 | 11/25 |

**Usuarios de prueba:**
- **Aprobado**: Usar cualquier email válido
- **Rechazado**: Cambiar el CVV a 000

Ver más tarjetas de prueba en: https://www.mercadopago.cl/developers/es/docs/checkout-pro/additional-content/test-cards

## Seguridad

- ✅ El Access Token **NUNCA** se envía al frontend
- ✅ Todos los endpoints de pago requieren autenticación (excepto webhook)
- ✅ Se verifica que la orden pertenezca al usuario autenticado
- ✅ No se pueden crear múltiples pagos aprobados para la misma orden
- ✅ Los webhooks son procesados de forma segura

## Troubleshooting

### Error: "MERCADOPAGO_ACCESS_TOKEN no está configurado"

Solución: Asegúrate de configurar la variable de entorno en `.env`

### Webhook no recibe notificaciones

Soluciones:
1. Verifica que la URL del webhook sea accesible públicamente
2. En desarrollo local, usa [ngrok](https://ngrok.com/) para exponer tu servidor
3. Verifica que la URL esté correctamente configurada en el panel de MercadoPago

### Pago aprobado pero orden no se actualiza

Solución: Revisa los logs del servidor para ver si hay errores en el procesamiento del webhook

## Recursos Adicionales

- [Documentación de MercadoPago](https://www.mercadopago.cl/developers/es/docs)
- [SDK de Python](https://github.com/mercadopago/sdk-python)
- [Checkout Pro](https://www.mercadopago.cl/developers/es/docs/checkout-pro/landing)
