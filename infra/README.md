# Infra – Nginx perimetral y Compose de referencia

Este folder contiene artefactos mínimos para levantar la topología propuesta (Nginx como reverse proxy frente a Flask y Rasa).

## Archivos
- `nginx.conf`: reverse proxy con rate limiting básico, headers de seguridad y upstreams a `backend:5000`, `rasa:5005` y `rasa-actions:5055`.
- `docker-compose.yml`: stack de referencia con Postgres, backend (build local), Rasa, Rasa SDK y Nginx.

## Uso rápido (local/docker)
1. Exporta las claves/secretos (ejemplo):
   ```powershell
   $env:PROFILE_ENCRYPTION_KEY="tu_clave_fernet"
   $env:CHAT_CONTEXT_API_KEY="token_contexto"
   $env:METRICS_API_KEY="token_metrics"
   ```
2. Desde `infra/`, levanta el stack:
   ```bash
   docker compose up -d --build
   ```
3. Nginx sirve en `http://localhost:80` y reenvía al backend/Rasa. Ajusta el tamaño de petición (`client_max_body_size`) o los límites en `nginx.conf` según tu caso.

## Notas
- El compose asume que la app Flask y las migraciones viven en el repo raíz. Ajusta `SQLALCHEMY_DATABASE_URI` si usas DB gestionada.
- Para TLS, monta tus certificados en `./infra/certs` y añade el bloque `listen 443 ssl` en `nginx.conf`.
- Si ya tienes backend/Rasa fuera de Docker, puedes usar solo el servicio `nginx` apuntando a sus hosts/puertos.*** End Patch
