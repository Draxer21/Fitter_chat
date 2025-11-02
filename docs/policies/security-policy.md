# Política de Seguridad de la Información

## Objetivo
Proteger la confidencialidad, integridad y disponibilidad de los datos manejados por el ecosistema Fitter.

## Alcance
- Backend Flask y servicios asociados (Rasa, base de datos PostgreSQL, almacenamiento de logs).
- Acciones personalizadas del chatbot y procesos automáticos de notificaciones.
- Colaboradores internos, proveedores y contratistas que tengan acceso a los ambientes o datos de Fitter.

## Principios
1. **Minimización de datos**: solo se recolecta la información estrictamente necesaria para ofrecer rutinas y recomendaciones.
2. **Segregación de responsabilidades**: acceso privilegiado limitado a personal autorizado, revisado trimestralmente.
3. **Protección criptográfica**: todo dato sensible (perfiles de salud, tokens de autenticación, códigos MFA) se cifra en reposo y tránsito.
4. **Auditoría continua**: registro centralizado de accesos, cambios críticos y fallos de seguridad.
5. **Mejora continua**: evaluación semestral de la postura de seguridad y planes de remediación documentados.

## Controles Técnicos
- **Gestión de claves**
  - `SECRET_KEY`, `PROFILE_ENCRYPTION_KEY` y credenciales SMTP se distribuyen vía gestor de secretos y nunca se versionan.
  - Rotación anual obligatoria o inmediata ante incidente.
- **Autenticación y MFA**
  - MFA basado en TOTP obligatorio para cuentas administrativas.
  - Códigos de respaldo cifrados y regenerados tras cada uso.
- **Protección de datos sensibles**
  - Perfiles de usuarios almacenados cifrados con Fernet (AES-128) y validados con checksum SHA-256.
  - Logs con datos personales anonimizados y purgados cada 90 días.
- **Monitoreo y alertas**
  - Alertas sobre intentos de autenticación fallidos, consumo de códigos de respaldo y errores de cifrado.
  - Revisión diaria de logs críticos (`backend/logs/backend.log`).

## Controles Organizacionales
- **Clasificación de la información** en niveles Público, Interno y Sensible.
- **Política de acceso**: principio de mínimo privilegio, altas/bajas registradas en sistema de tickets.
- **Concientización**: capacitación anual obligatoria sobre phishing, ingeniería social y manejo seguro de datos médicos.
- **Gestión de incidentes**: plan formal con tiempos de respuesta (SLA 4h crítica, 24h alta, 72h media), responsable designado y procedimientos de comunicación.

## Cumplimiento y Auditoría
- Revisiones internas semestrales alineadas a ISO/IEC 27001 Anexo A.
- Auditorías externas anuales enfocadas en cumplimiento normativo (Ley 21.719) y salvaguardas ISO 27701.
- Evidencias mínimas: bitácoras de acceso, reportes de rotación de claves, actas de capacitación, registros de incidentes.

## Revisión
- Propietario: CISO del proyecto Fitter.
- Próxima revisión: 6 meses después de la fecha de publicación.
