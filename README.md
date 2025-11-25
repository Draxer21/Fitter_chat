# 🤖 Fitter – Chatbot con Rasa

Proyecto de Título – Ingeniería en Informática (INACAP)  
Autores: Bryan Carreño / Diego Guzman  
Docente Guía: Ivan Riquelme Nuñez  

---

## 📌 Descripción
Fitter es una **plataforma integral para gimnasios y centros deportivos** con chatbot en español diseñado con **Rasa**. Permite a los usuarios y administradores:
- Consultar rutinas personalizadas de entrenamiento (a través del chatbot).
- Gestionar inventario y productos.
- Realizar compras y pagos simulados.
- Registrar reservas de clases.
- Gestionar órdenes y perfiles de usuario.
- Recibir notificaciones por email.
- Autenticación segura con MFA.

El sistema cumple con la normativa chilena (Ley 21.719) sobre protección de datos.

---

## 🌙 Sistema de temas (Modo Claro / Oscuro)

La aplicación frontend incluye un **sistema de temas dinámico** con soporte completo para modo claro y oscuro:

- **Acceso rápido:** Botón 🌙/☀️ en la esquina inferior izquierda (controles laterales)
- **Persistencia:** El tema seleccionado se guarda en `localStorage` y se mantiene entre sesiones
- **Respuesta del SO:** Se detecta automáticamente la preferencia del sistema operativo (si no hay tema guardado)
- **Variables CSS:** Sistema de variables CSS (`--bg`, `--text`, `--primary`, etc.) que se aplican globalmente
- **Transiciones suaves:** Cambios de color suave de 200ms para mejor UX
- **Cobertura completa:** Todos los componentes (Bootstrap, formularios, botones, modales, etc.) respetan el tema

**Colores por tema:**
- Modo claro: Fondo blanco (#ffffff), texto oscuro (#111827)
- Modo oscuro: Fondo muy oscuro (#0b1020), texto claro (#e5e7eb)

---

## 🛠️ Tecnologías utilizadas
- **Python 3.10** (entorno base)
- **Rasa 3.6** (NLP / NLU)
- **Flask** (servidor backend)
- **SQLAlchemy** (ORM para base de datos)
- **HTML + JavaScript Vanilla** (interfaz web)
- **Docker** (containerización)
- **GitHub** (versionamiento)

---

## 🔐 Configuración de seguridad

- Genera una clave Fernet para cifrar la información sensible del perfil y expórtala como `PROFILE_ENCRYPTION_KEY` antes de iniciar el backend o ejecutar migraciones:

  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  export PROFILE_ENCRYPTION_KEY="<clave-generada>"
  ```

- Revisa las políticas y lineamientos de seguridad en `docs/policies/security-policy.md` y los términos y condiciones en `docs/policies/terms-and-conditions.md`.

- Para coordinar el trabajo asistido por modelos en VS Code, usa los prompts sugeridos en `docs/prompts/codex_security_prompts.md`.

---

## ▶️ Arranque rápido en VS Code

1. **Prepara las dependencias una sola vez**
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\Activate.ps1
   # En Linux/Mac:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   pip install rasa
   ```
2. **Exporta las variables sensibles** (ejemplo):
   ```bash
   # Windows (PowerShell):
   $env:PROFILE_ENCRYPTION_KEY="<clave-Fernet>"
   $env:CHAT_CONTEXT_API_KEY="<token-opcional>"
   
   # Linux/Mac:
   export PROFILE_ENCRYPTION_KEY="<clave-Fernet>"
   export CHAT_CONTEXT_API_KEY="<token-opcional>"
   ```
3. **Inicia los servicios desde la terminal integrada de VS Code**:
   ```bat
   scripts\start_project.bat
   ```
   El script levanta tres servicios:
   - Backend Flask en `http://localhost:5000`
   - Servidor Rasa en `http://localhost:5005`
   - Servidor de acciones Rasa SDK en `http://localhost:5055`

Cuando termines la sesión, presiona `Ctrl+C` en la terminal para cerrar todos los servicios de forma ordenada.

## 📁 Estructura del proyecto

```
Fitter/
├── backend/              # Servidor Flask con módulos de negocio
│   ├── carritoapp/       # Gestión de carrito de compras
│   ├── chat/             # Integración con Rasa Chatbot
│   ├── gestor_inventario/# Gestión de productos e inventario
│   ├── login/            # Autenticación y MFA
│   ├── orders/           # Gestión de órdenes
│   ├── profile/          # Perfiles de usuario (con cifrado)
│   ├── security/         # Seguridad y sesiones
│   ├── notifications/    # Notificaciones por email
│   ├── migrations/       # Migraciones de BD (Alembic)
│   └── templates/        # Templates HTML
├── Chatbot/              # Modelos y configuración de Rasa
│   ├── data/             # NLU, stories, rules, specs
│   └── models/           # Modelos entrenados
├── scripts/              # Scripts de utilidad
│   ├── start_project.bat # Script de inicio
│   └── generate_nlu_dataset.py
├── infra/                # Configuración Docker y Nginx
└── requirements.txt      # Dependencias Python
```

## 🧪 Generar ejemplos NLU

Usa el script `scripts/generate_nlu_dataset.py` para recrear el dataset NLU a partir de los YAML en `Chatbot/data/specs`:

```bash
python scripts/generate_nlu_dataset.py --update-nlu
```

El comando genera hasta 2 000 ejemplos por intent, crea un respaldo en `Chatbot/data/generated/nlu_generated.yml` y actualiza `Chatbot/data/nlu.yml`.

## 🧪 Tests

Ejecuta los tests del backend:

```bash
python -m pytest backend/tests/
```

Incluye tests para:
- Autenticación MFA
- Modelos de productos
- Perfiles de usuario
