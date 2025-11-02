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
