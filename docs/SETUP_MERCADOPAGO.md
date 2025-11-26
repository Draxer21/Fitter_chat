# Guía de Configuración - MercadoPago

## 📋 Requisitos Previos

1. Cuenta de MercadoPago (Chile)
2. Credenciales de acceso (Access Token y Public Key)
3. URL pública para recibir webhooks (para producción)

## 🔧 Configuración Paso a Paso

### 1. Obtener Credenciales de MercadoPago

1. **Ingresar al Panel de Desarrolladores:**
   - Ir a: https://www.mercadopago.cl/developers/panel

2. **Obtener Credenciales de Prueba (Testing):**
   - En el panel, ir a "Credenciales"
   - Seleccionar "Credenciales de prueba"
   - Copiar:
     - `Access Token` (comienza con `TEST-`)
     - `Public Key` (comienza con `TEST-`)

3. **Obtener Credenciales de Producción (cuando estés listo):**
   - En el panel, ir a "Credenciales"
   - Seleccionar "Credenciales de producción"
   - Completar el proceso de validación si es necesario
   - Copiar:
     - `Access Token` (comienza con `APP_USR-`)
     - `Public Key` (comienza con `APP_USR-`)

### 2. Configurar Variables de Entorno

Editar el archivo `.env` en la raíz del proyecto:

```dotenv
# MercadoPago Configuración
MERCADOPAGO_ACCESS_TOKEN=TEST-1234567890-112514-abcdefghijklmnop-1234567890
MERCADOPAGO_PUBLIC_KEY=TEST-abcd1234-5678-90ef-ghij-klmnopqrstuv
MERCADOPAGO_NOTIFICATION_URL=https://tu-dominio.com/api/payments/webhook
FRONTEND_URL=http://localhost:3000
```

**Nota:** 
- Para desarrollo local, puedes usar `http://localhost:3000` para FRONTEND_URL
- Para webhooks en desarrollo, necesitas exponer tu servidor (ver sección ngrok)

### 3. Configurar Webhook (Desarrollo Local)

Para recibir notificaciones de MercadoPago en desarrollo local:

#### Opción A: Usar ngrok

```bash
# Instalar ngrok (si no lo tienes)
# Descargar desde: https://ngrok.com/download

# Exponer tu servidor Flask (puerto 5000)
ngrok http 5000

# ngrok te dará una URL pública, ejemplo:
# https://abc123.ngrok.io
```

Actualizar `.env`:
```dotenv
MERCADOPAGO_NOTIFICATION_URL=https://abc123.ngrok.io/api/payments/webhook
```

#### Opción B: Configuración de Producción

Si ya tienes un dominio público:
```dotenv
MERCADOPAGO_NOTIFICATION_URL=https://tu-dominio.com/api/payments/webhook
```

### 4. Verificar Base de Datos

Asegurarse de que la migración con la tabla `payment` esté aplicada:

```bash
cd backend
flask db current  # Ver migración actual
flask db upgrade  # Aplicar migraciones pendientes
```

Verificar que existan las tablas:
- `payment` (con columnas: preference_id, payment_id, status, etc.)
- `order` (con columna: payment_status)

### 5. Reiniciar Servicios

```bash
# Backend
cd backend
flask run

# Frontend (en otra terminal)
cd frontend
npm start
```

## 🧪 Probar la Integración

### Tarjetas de Prueba

MercadoPago proporciona tarjetas de prueba para diferentes escenarios:

#### Pago Aprobado
```
Número: 5031 7557 3453 0604
CVV: 123
Fecha: Cualquier fecha futura (ej: 11/25)
Nombre: APRO
```

#### Pago Rechazado (fondos insuficientes)
```
Número: 5031 4332 1540 6351
CVV: 123
Fecha: Cualquier fecha futura
Nombre: OTHE
```

#### Pago Pendiente
```
Número: 5031 4500 0000 0008
CVV: 123
Fecha: Cualquier fecha futura
Nombre: PEND
```

Más tarjetas de prueba: https://www.mercadopago.com.ar/developers/es/docs/checkout-api/testing

### Flujo de Prueba Completo

1. **Agregar productos al carrito**
   - Ir a la tienda: `http://localhost:3000`
   - Agregar productos

2. **Ir al carrito**
   - Hacer clic en el ícono del carrito
   - Hacer clic en "Hacer Compra"

3. **Ingresar datos**
   - Ingresar tu nombre
   - Hacer clic en "Continuar al pago"

4. **Serás redirigido a MercadoPago**
   - Usar una de las tarjetas de prueba
   - Completar el pago

5. **Verificar resultado**
   - Serás redirigido a `/payment/success`, `/payment/failure`, o `/payment/pending`
   - Verificar que se muestre la información de la orden

6. **Verificar en base de datos**
   ```sql
   SELECT * FROM payment ORDER BY created_at DESC LIMIT 5;
   SELECT * FROM "order" ORDER BY created_at DESC LIMIT 5;
   ```

## 🐛 Troubleshooting

### Error: "MercadoPago no está configurado correctamente"

**Causa:** Credenciales incorrectas o faltantes

**Solución:**
1. Verificar que las variables en `.env` estén correctas
2. Reiniciar el servidor Flask
3. Verificar en logs: `backend/logs/app.log`

### No se reciben webhooks

**Causa:** URL no accesible públicamente

**Solución:**
1. Verificar que `MERCADOPAGO_NOTIFICATION_URL` sea una URL pública
2. Si usas ngrok, verificar que esté corriendo
3. Verificar en logs de MercadoPago (panel de desarrolladores)

### Pago se queda en "pending"

**Causa:** Webhook no se procesó correctamente

**Solución:**
1. Verificar logs del backend
2. Probar manualmente el webhook:
   ```bash
   curl -X POST http://localhost:5000/api/payments/webhook \
     -H "Content-Type: application/json" \
     -d '{"type":"payment","data":{"id":"123"}}'
   ```

### Error al crear preferencia

**Causa:** Items inválidos o datos faltantes

**Solución:**
1. Verificar que el carrito tenga productos
2. Verificar que los precios sean válidos
3. Revisar logs del backend para detalles del error

## 📊 Verificar Estado de Pago

### Opción 1: API
```bash
# Obtener estado de pago para orden 123
curl http://localhost:5000/api/payments/status/123 \
  -H "Cookie: session=tu-session-cookie"
```

### Opción 2: Base de Datos
```sql
-- Ver todos los pagos
SELECT 
  p.id,
  p.order_id,
  p.status,
  p.transaction_amount,
  o.payment_status,
  o.status
FROM payment p
JOIN "order" o ON p.order_id = o.id
ORDER BY p.created_at DESC;
```

## 🚀 Pasar a Producción

### Checklist

- [ ] Obtener credenciales de producción de MercadoPago
- [ ] Actualizar `.env` con credenciales de producción
- [ ] Configurar dominio público para webhooks
- [ ] Configurar SSL/HTTPS en el dominio
- [ ] Probar con tarjetas reales (montos pequeños)
- [ ] Configurar notificaciones por email
- [ ] Implementar logging y monitoreo
- [ ] Configurar backup de base de datos

### Variables de Producción

```dotenv
# .env (PRODUCCIÓN)
MERCADOPAGO_ACCESS_TOKEN=APP_USR-XXXXXX-XXXXXX-XXXXXXXXXXXXXX-XXXXXXXX
MERCADOPAGO_PUBLIC_KEY=APP_USR-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
MERCADOPAGO_NOTIFICATION_URL=https://tu-dominio.com/api/payments/webhook
FRONTEND_URL=https://tu-dominio.com
```

## 📚 Documentación Adicional

- **API de MercadoPago:** Ver `docs/MERCADOPAGO_API.md`
- **Documentación Oficial:** https://www.mercadopago.cl/developers/es/docs
- **Soporte:** https://www.mercadopago.cl/developers/es/support

## 🔐 Seguridad

### Buenas Prácticas

1. **Nunca** commitear credenciales al repositorio
2. Usar `.env` y agregarlo a `.gitignore`
3. Rotar credenciales periódicamente
4. Verificar firma de webhooks en producción
5. Usar HTTPS en producción
6. Implementar rate limiting en endpoints públicos
7. Validar montos antes de crear preferencias
8. Registrar todas las transacciones en logs

### Validación de Webhooks

El webhook ya valida que:
- El pago exista en la BD
- El estado sea válido
- La orden exista y esté asociada al pago

Para producción, considera agregar:
- Validación de firma HMAC
- Validación de IP de origen
- Rate limiting específico para webhooks

## ✅ Verificación Final

Antes de considerar la configuración completa:

1. [ ] Credenciales configuradas correctamente
2. [ ] Variables de entorno cargadas
3. [ ] Base de datos con migraciones aplicadas
4. [ ] Backend corriendo sin errores
5. [ ] Frontend corriendo y comunicándose con backend
6. [ ] Flujo de pago completo probado con tarjeta de prueba
7. [ ] Webhook recibiendo notificaciones (si está configurado)
8. [ ] Páginas de retorno funcionando correctamente
9. [ ] Estados de orden actualizándose correctamente

## 📞 Soporte

Si encuentras problemas:

1. Revisar logs en `backend/logs/`
2. Verificar configuración en `.env`
3. Consultar documentación oficial de MercadoPago
4. Verificar estado del servicio: https://status.mercadopago.com/
