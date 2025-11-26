# API de MercadoPago - Documentación

## ✅ Estado de Implementación

La API de MercadoPago está **completamente implementada** con integración frontend y backend completa.

### 📁 Archivos Backend

1. **`backend/payments/models.py`** - Modelo Payment para la BD
2. **`backend/payments/service.py`** - Servicio de integración con MercadoPago SDK
3. **`backend/payments/routes.py`** - Endpoints REST de la API
4. **`backend/payments/__init__.py`** - Módulo de pagos
5. **`backend/carritoapp/routes.py`** - Modificado endpoint `/pagar` para crear preferencias

### 📁 Archivos Frontend

1. **`frontend/src/pages/PagoPage.jsx`** - Modificado para redireccionar a MercadoPago
2. **`frontend/src/pages/PaymentSuccessPage.jsx`** - Página de pago exitoso
3. **`frontend/src/pages/PaymentFailurePage.jsx`** - Página de pago rechazado
4. **`frontend/src/pages/PaymentPendingPage.jsx`** - Página de pago pendiente
5. **`frontend/src/App.js`** - Agregadas rutas `/payment/success`, `/payment/failure`, `/payment/pending`
6. **`frontend/src/services/apijs.js`** - Agregados métodos `payments.getOrderPayment()` y `payments.getStatus()`

### 🗃️ Modelo de Datos

**Tabla: `payment`**
- `id` - Primary key
- `order_id` - Foreign key → order.id
- `preference_id` - ID de preferencia de MercadoPago (único)
- `payment_id` - ID del pago en MercadoPago (único)
- `status` - Estado: pending, approved, rejected, cancelled, refunded, in_process
- `transaction_amount` - Monto de la transacción
- `currency_id` - Moneda (CLP por defecto)
- `payment_method_id` - Método de pago usado
- `payment_type_id` - Tipo de pago
- `merchant_order_id` - ID de orden de comerciante
- `external_reference` - Referencia externa (order_id)
- `payer_email` - Email del pagador
- `payer_id` - ID del pagador
- `created_at`, `updated_at`, `approved_at` - Timestamps

**Tabla: `order`** (actualizada)
- Agregado campo `payment_status`: pending, paid, failed, refunded
- Cambiado `status` default de "paid" a "pending"

### 🔌 Endpoints de la API

#### 1. Crear Preferencia de Pago
```
POST /api/payments/create-preference
```

**Request:**
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

**Response:**
```json
{
  "success": true,
  "preference_id": "1234567-abcd1234-efgh5678",
  "init_point": "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=...",
  "sandbox_init_point": "https://sandbox.mercadopago.cl/checkout/v1/redirect?pref_id=...",
  "payment_id": 1
}
```

#### 2. Webhook de Notificaciones
```
POST /api/payments/webhook
```

Recibe notificaciones de MercadoPago cuando cambia el estado de un pago.

**Automáticamente actualiza:**
- Estado del pago en la tabla `payment`
- `payment_status` y `status` de la orden

#### 3. Consultar Estado de Pago
```
GET /api/payments/status/<order_id>
```

**Response:**
```json
{
  "id": 1,
  "order_id": 123,
  "preference_id": "1234567-abcd1234-efgh5678",
  "payment_id": "98765432",
  "status": "approved",
  "transaction_amount": 50000,
  "currency_id": "CLP",
  "payment_method_id": "visa",
  "created_at": "2025-11-25T10:30:00",
  "approved_at": "2025-11-25T10:35:00"
}
```

#### 4. Consultar Orden con Pago
```
GET /api/payments/order/<order_id>
```

Retorna información completa de la orden incluyendo el pago.

### ⚙️ Configuración Requerida

Agregar al archivo `.env`:

```env
# MercadoPago configuración
MERCADOPAGO_ACCESS_TOKEN=TEST-your-access-token-here
MERCADOPAGO_PUBLIC_KEY=TEST-your-public-key-here
MERCADOPAGO_NOTIFICATION_URL=https://your-domain.com/api/payments/webhook
FRONTEND_URL=http://localhost:3000
```

**Obtener credenciales:**
1. Ir a https://www.mercadopago.cl/developers/panel
2. Crear una aplicación
3. Copiar Access Token y Public Key de la sección "Credenciales de prueba"

### 📦 Dependencias

```bash
pip install mercadopago
```

Ya instalado en el proyecto.

### 🔄 Flujo Completo de Pago

1. **Cliente crea orden** → `POST /api/orders` → status='pending', payment_status='pending'

2. **Frontend solicita preferencia** → `POST /api/payments/create-preference`
   - Se crea registro en tabla `payment`
   - Se obtiene `init_point` de MercadoPago

3. **Cliente es redirigido** → `init_point` (checkout de MercadoPago)

### 🚀 Flujo Completo de Pago

1. **Usuario agrega productos al carrito** y hace clic en "Hacer Compra"
   - Frontend: Redirige a `/pago`

2. **Usuario ingresa su nombre** en `PagoPage.jsx`
   - Formulario simplificado (solo nombre requerido)
   - Email se obtiene de la sesión del usuario

3. **Frontend envía solicitud** → `POST /carrito/pagar`
   ```javascript
   const response = await API.carrito.pagar({ name: "Juan Pérez" });
   // response = {
   //   order_id: 123,
   //   preference_id: "xxx",
   //   init_point: "https://mercadopago.cl/checkout/..."
   // }
   ```

4. **Backend crea orden y preferencia**
   - Crea orden con `status="pending"` y `payment_status="pending"`
   - Llama a `MercadoPagoService.create_preference()`
   - Retorna `init_point` para redirección

5. **Frontend guarda order_id y redirige** a MercadoPago
   ```javascript
   localStorage.setItem('pending_order_id', result.order_id);
   window.location.href = result.init_point;
   ```

6. **Usuario completa pago** en MercadoPago
   - Ingresa datos de tarjeta
   - Confirma pago

7. **MercadoPago procesa pago y envía webhook** → `POST /api/payments/webhook`
   - Backend actualiza `payment.status`
   - Actualiza `order.payment_status` y `order.status`

8. **MercadoPago redirige usuario** según resultado:
   - Aprobado: `http://localhost:3000/payment/success?external_reference=123`
   - Rechazado: `http://localhost:3000/payment/failure?external_reference=123`
   - Pendiente: `http://localhost:3000/payment/pending?external_reference=123`

9. **Frontend muestra resultado**
   - Carga detalles de orden desde `API.payments.getOrderPayment(orderId)`
   - Muestra información de orden, total, cliente
   - Opciones: Ver orden, Volver al inicio, Reintentar (si falló)

### 🛡️ Seguridad

- ✅ Autenticación requerida (sesión de usuario)
- ✅ Verificación de propiedad de la orden
- ✅ Validación de pagos duplicados
- ✅ Logs de errores y eventos

### 🧪 Testing

Para testing, usar las credenciales de prueba de MercadoPago y tarjetas de prueba:

**Tarjetas de prueba:**
- Aprobada: 5031 7557 3453 0604
- Rechazada: 5031 4332 1540 6351
- Pendiente: 5031 4500 0000 0008

CVV: 123
Fecha: Cualquier fecha futura

### 📊 Estados de Pago

**Payment.status:**
- `pending` - Pago pendiente
- `approved` - Pago aprobado
- `rejected` - Pago rechazado
- `cancelled` - Pago cancelado
- `refunded` - Pago reembolsado
- `in_process` - Pago en proceso

**Order.payment_status:**
- `pending` - Esperando pago
- `paid` - Pago completado
- `failed` - Pago fallido
- `refunded` - Pago reembolsado

**Order.status:**
- `pending` - Orden creada
- `confirmed` - Orden confirmada (pago aprobado)
- `shipped` - Orden enviada
- `delivered` - Orden entregada
- `cancelled` - Orden cancelada

### 🚀 Ejemplo de Integración Frontend

```javascript
// 1. Crear orden
const orderResponse = await fetch('/api/orders', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ items: [...] })
});
const order = await orderResponse.json();

// 2. Crear preferencia de pago
const prefResponse = await fetch('/api/payments/create-preference', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    order_id: order.id,
    payer_info: {
      name: 'Juan',
      surname: 'Pérez',
      email: 'juan@example.com'
    }
  })
});
const preference = await prefResponse.json();

// 3. Redirigir al checkout de MercadoPago
window.location.href = preference.init_point;
```

---

**Última actualización:** 25 de noviembre de 2025
