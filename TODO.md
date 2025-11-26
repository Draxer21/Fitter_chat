# TODO: Implement Simulated Card Payment in Shopping Cart

## Backend Changes
- [x] Refactor routes.py: Extract `validar_y_deducir()` function for stock validation and deduction without clearing cart.
- [x] Modify `/validar` endpoint to use `validar_y_deducir()` then clear cart.
- [x] Add `/pagar` endpoint: Validate simulated payment data, call `validar_y_deducir()`, return success.
- [x] Modify `/boleta` and `/boleta_json` to clear cart after generating receipt.

### Backend
- [x] Autenticación con usuario/contraseña
- [x] Autenticación Multi-Factor (MFA)
- [x] Gestión de perfiles con cifrado de datos sensibles
- [x] Sistema de carrito de compras
- [x] Pago simulado con tarjeta (validación Luhn)
- [x] **Integración completa con MercadoPago API**
- [x] Generación de boletas/recibos
- [x] Gestión de inventario y productos
- [x] Gestión de órdenes
- [x] Notificaciones por email
- [x] Integración con Rasa Chatbot
- [x] Tests para MFA, perfiles y productos
- [x] Migraciones de base de datos (Alembic)
- [x] Seguridad CSRF

### Frontend
- [x] Templates HTML para: índice, login, registro, tienda, carrito, pago, boleta
- [x] JavaScript Vanilla para funcionalidad del cliente
- [x] API client (apijs.js) para comunicación con backend
- [x] Validación de formularios
- [x] Sistema de temas (Modo claro/oscuro) con CSS variables
- [x] Context API para manejo de tema global
- [x] Persistencia de preferencia de tema
- [x] **Integración con MercadoPago (redirección a checkout)**
- [x] **Páginas de retorno de pago (success, failure, pending)**

## Routing
- [x] Update App.js: Add route for `/pago` to PagoPage.

### DevOps
- [x] Dockerfile para backend
- [x] docker-compose.yml
- [x] Configuración Nginx
- [x] Script de inicio (start_project.bat)

## 📋 Pendiente/Futuro

### Backend
- [ ] Autenticación OAuth2/Google
- [ ] Panel administrativo para gestión de productos
- [ ] Reportes de ventas y métricas
- [ ] Rate limiting y throttling
- [ ] Logs y auditoría más detallados
- [ ] Envío de notificación por email al confirmar pago

### MercadoPago
- [ ] Configurar credenciales reales de producción
- [ ] Configurar URL pública para webhook (ngrok o dominio real)
- [ ] Probar flujo completo end-to-end con tarjetas de prueba
- [ ] Implementar manejo de reembolsos
- [ ] Agregar soporte para pagos en cuotas personalizadas

### Frontend
- [ ] Interfaz moderna con framework (React/Vue)
- [ ] Dashboard de usuario
- [ ] Historial de compras
- [ ] Wishlist
- [ ] Búsqueda y filtros avanzados

### Chatbot
- [ ] Reconocimiento de intents más complejos
- [ ] Integración con búsqueda de productos
- [ ] Recomendaciones personalizadas
- [ ] Soporte multiidioma

### Testing
- [ ] Cobertura de tests al 80%+
- [ ] Tests de integración E2E
- [ ] Tests de carga y performance

### Documentación
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Guía de contribución
- [ ] Troubleshooting guide
