# TODO: Fitter – Estado Actual del Proyecto

## ✅ Completado

### Backend
- [x] Autenticación con usuario/contraseña
- [x] Autenticación Multi-Factor (MFA)
- [x] Gestión de perfiles con cifrado de datos sensibles
- [x] Sistema de carrito de compras
- [x] Pago simulado con tarjeta (validación Luhn)
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

### Chatbot (Rasa)
- [x] Configuración de dominio
- [x] Historias de conversación
- [x] Reglas NLU
- [x] Generación de 2000 ejemplos por intent
- [x] Modelos entrenados

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
- [ ] Integración de pasarela de pago real
- [ ] Rate limiting y throttling
- [ ] Logs y auditoría más detallados

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
