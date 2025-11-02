# Prompts sugeridos para reforzar seguridad con Codex en VS Code

## 1. Configurar cifrado de perfiles
```
Resume cómo está almacenado actualmente el perfil de usuario en backend/login/models.py y propone un esquema para cifrarlo usando Fernet. Indica archivos y pasos necesarios.
```

## 2. Validar migraciones
```
Genera una migración Alembic que mueva los campos de perfil del modelo User a una nueva tabla user_profile con cifrado Fernet y checksum SHA-256.
```

## 3. Actualizar endpoints seguros
```
Modifica backend/login/routes.py para leer y actualizar los datos cifrados del perfil, manteniendo las validaciones actuales y devolviendo errores claros cuando falle el cifrado.
```

## 4. Preparar pruebas y documentación
```
Sugiere pruebas automatizadas para cubrir el flujo de cifrado/desencriptado y actualiza README con la variable PROFILE_ENCRYPTION_KEY. Indica también qué documentación de políticas debe crearse.
```

## 5. Verificación final
```
Lista los comandos necesarios para verificar el nuevo flujo: ejecutar migraciones, correr pruebas y simular una actualización de perfil en la API.
```
