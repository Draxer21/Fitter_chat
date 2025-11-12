# 🤖 Fitter – Chatbot con Rasa

Proyecto de Título – Ingeniería en Informática (INACAP)  
Autores: Bryan Carreño / Diego Guzman  
Docente Guía: Ivan Riquelme Nuñez  

---

## 📌 Descripción
Fitter es un **chatbot en español** diseñado con **Rasa** para el contexto de gimnasios y centros deportivos.  
Permite a los usuarios:
- Consultar rutinas personalizadas de entrenamiento.
- Obtener información de servicios.
- Registrar reservas de clases.
- Resolver dudas frecuentes.

El sistema se integra con un **backend en Flask/Django** y una interfaz web básica en **HTML/JS**, cumpliendo con la normativa chilena (Ley 21.719) sobre protección de datos.

---

## 🛠️ Tecnologías utilizadas
- **Python 3.10** (entorno base)
- **Rasa 3.6** (NLP / NLU)
- **Flask** (servidor backend para integración web)
- **HTML + JS** (interfaz de usuario simple)
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
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install rasa
   npm install --prefix frontend
   ```
2. **Exporta las variables sensibles** (ejemplo):
   ```bash
   export PROFILE_ENCRYPTION_KEY="<clave Fernet>"
   export CHAT_CONTEXT_API_KEY="<token opcional para Rasa/actions>"
   ```
3. **Inicia todo desde la terminal integrada de VS Code**:
   ```bash
   ./scripts/start_project.sh
   ```
   En Windows usa:
   ```bat
   scripts\start_project.bat
   ```
   El script levanta cuatro servicios:
   - Backend Flask en `http://localhost:5000`
   - Servidor Rasa en `http://localhost:5005`
   - Servidor de acciones Rasa SDK en `http://localhost:5055`
   - Frontend React en `http://localhost:3000`

   Puedes omitir componentes con flags como `--skip-frontend` o `--skip-chatbot`. Usa `./scripts/start_project.sh --help` o `scripts\start_project.bat --help` para ver todas las opciones y variables disponibles.

Cuando termines la sesión, presiona `Ctrl+C` en la terminal para cerrar todos los servicios de forma ordenada.
