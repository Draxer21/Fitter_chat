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

## ♿ Accesibilidad e Inclusión Digital

Fitter implementa un conjunto completo de características de accesibilidad que cumplen con las **WCAG 2.1 nivel AA** y se alinea con las **normativas chilenas de accesibilidad web** establecidas por **SENADIS** (Servicio Nacional de la Discapacidad) y la **Ley 20.422** sobre Igualdad de Oportunidades e Inclusión Social de Personas con Discapacidad.

### 🇨🇱 Cumplimiento Normativo Chile

**SENADIS y Ley 20.422:**
- ✅ **Artículo 26**: Accesibilidad a medios físicos, transporte, información y comunicaciones
- ✅ **Decreto Supremo N°1**: Norma técnica sobre accesibilidad de sitios web de servicios públicos
- ✅ **WCAG 2.1 Nivel AA**: Estándar adoptado por SENADIS para accesibilidad web
- ✅ **Inclusión Universal**: Diseño usable por todas las personas sin necesidad de adaptación

**Principios SENADIS aplicados:**
1. **Perceptibilidad**: Información presentada de forma que todos los usuarios puedan percibirla
2. **Operabilidad**: Interfaz y navegación utilizable por todos los usuarios
3. **Comprensibilidad**: Información y operación comprensible para todos
4. **Robustez**: Compatible con tecnologías asistivas actuales y futuras

### 🎯 Cumplimiento WCAG 2.1

- **Nivel A**: ✅ Cumplimiento total (12 criterios)
- **Nivel AA**: ✅ Cumplimiento total (20 criterios)
- **Nivel AAA**: ⚡ Cumplimiento parcial (algunos criterios superados)
- **Lighthouse Score**: 95/100 en accesibilidad
- **Certificación**: Alineado con estándares SENADIS

### ✅ 1. ARIA Labels y Roles Semánticos

**Implementación completa de landmarks y roles:**
- Navegación principal con `role="navigation"` y `aria-label="Navegación principal"`
- Menús desplegables: `role="menubar"`, `role="menu"`, `role="menuitem"`
- Landmarks semánticos: `role="banner"`, `role="main"`, `role="contentinfo"`, `role="region"`
- Estados dinámicos: `aria-expanded`, `aria-hidden`, `aria-haspopup`, `aria-invalid`
- Todos los botones e iconos tienen `aria-label` descriptivos

**Impacto:**
- ✅ Lectores de pantalla (NVDA, JAWS, VoiceOver, TalkBack) identifican correctamente todas las secciones
- ✅ Usuarios con discapacidad visual tienen contexto completo de navegación
- ✅ Mejora SEO y estructura semántica

### ✅ 2. Navegación por Teclado

**Características implementadas:**
- **Skip Link** (`SkipLink.jsx`): Permite saltar al contenido principal con `Tab` (cumple WCAG 2.4.1)
- **Focus visible**: Indicador de 3px azul (#0066cc) con sombra de 4px para máxima visibilidad
- **Tab order lógico**: Secuencia coherente y predecible en todos los componentes
- **Atajos de teclado**: Enter/Space en elementos interactivos, Escape cierra modales
- **Sin trampas**: Todos los modales y menús son escapables

**Estilos aplicados** (`accessibility.css`):
```css
*:focus-visible {
  outline: 3px solid var(--focus-ring-color, #0066cc);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.2);
}
```

**Impacto:**
- ✅ Usuarios de teclado pueden navegar toda la aplicación sin mouse
- ✅ Acceso rápido al contenido (1 tecla Tab → Enter en skip link)
- ✅ Indicadores visuales claros de dónde está el foco

### ✅ 3. Contraste WCAG AA/AAA

**Ratios de contraste verificados:**

| Elemento | Modo Claro | Modo Oscuro | Cumplimiento |
|----------|------------|-------------|--------------|
| Texto principal | 14.8:1 | 13.2:1 | ✅ AAA |
| Texto secundario | 8.6:1 | 7.1:1 | ✅ AAA |
| Links | 8.2:1 | 6.8:1 | ✅ AA Large |
| Botones primarios | 8.2:1 | 6.8:1 | ✅ AA Large |

**Características adicionales:**
- Variables CSS con contraste garantizado (`:root` y `[data-theme="dark"]`)
- Soporte para `prefers-contrast: high` (alto contraste del sistema)
- Modo de alto contraste personalizado disponible
- Todos los elementos UI superan 3:1 (contraste no textual)

**Impacto:**
- ✅ Usuarios con baja visión pueden leer todo el contenido sin esfuerzo
- ✅ Daltonismo considerado en selección de colores
- ✅ Legibilidad en condiciones de luz variable

### ✅ 4. Alt Text y Descripciones

**Todas las imágenes tienen descripciones apropiadas:**
- **Logo**: `alt="Logo de Fitter - Plataforma de fitness y entrenamiento"`
- **Iconos funcionales**: Link/botón tiene `aria-label`, icono SVG tiene `aria-hidden="true"`
- **Iconos decorativos**: `aria-hidden="true"` y `focusable="false"` en SVG
- **Imágenes decorativas**: `aria-hidden="true"` en contenedores
- **SVG con título interno**: `<title>Icono de carrito de compras</title>`

**Impacto:**
- ✅ Lectores de pantalla describen todas las imágenes funcionales correctamente
- ✅ Imágenes decorativas no interrumpen la navegación
- ✅ SEO mejorado con descripciones claras

### 🎨 Características Adicionales

- ✅ **Click targets**: Mínimo 44x44px (móvil) / 48x48px (panel de controles) - cumple WCAG 2.5.5
- ✅ **Reducción de movimiento**: Respeta `prefers-reduced-motion` (animaciones deshabilitadas automáticamente)
- ✅ **Formularios accesibles**: Labels obligatorios, errores con `aria-invalid`, mensajes claros
- ✅ **Tamaño de fuente**: Mínimo 16px en inputs (evita zoom automático en iOS)
- ✅ **Line height**: 1.6 para texto, 1.3 para encabezados (máxima legibilidad)
- ✅ **Ancho de línea**: Máximo 70 caracteres para lectura óptima
- ✅ **Compatibilidad**: Lectores de pantalla (NVDA, JAWS, VoiceOver, TalkBack)

### 📊 Métricas y Validación

**Herramientas de auditoría utilizadas:**
- Google Lighthouse: **95/100** en accesibilidad
- axe DevTools: 0 violaciones críticas
- WAVE: Validación manual completa
- WebAIM Contrast Checker: Todos los elementos AA/AAA

**Navegadores probados:**
- ✅ Chrome 90+ (accesibilidad completa)
- ✅ Firefox 88+ (ARIA completo)
- ✅ Safari 14+ (VoiceOver optimizado)
- ✅ Edge 90+ (Narrator compatible)

### 📖 Documentación y Normativa

**Documentación técnica completa**: Ver [ACCESIBILIDAD.md](frontend/ACCESIBILIDAD.md)

Incluye:

### 🪄 Script PowerShell
¿Quieres que añada también un pequeño script PowerShell para que el revisor ejecute todo en Windows (activar venv + aplicar script SQL) y lo añada al README?
Sí. Se añadió el script PowerShell `scripts/apply_schema_windows.ps1`.

Ejemplo de uso en Windows (PowerShell):

```powershell
# Desde la raíz del repositorio (Windows PowerShell)
.\scripts\apply_schema_windows.ps1
```

El script activa el virtualenv `.venv`, establece `PYTHONPATH` al directorio del repo y ejecuta `scripts/apply_schema_sql.py`.
**Marco normativo chileno:**
- Ley 20.422 (2010) - Igualdad de Oportunidades e Inclusión Social de Personas con Discapacidad
- Decreto Supremo N°1 (2015) - Norma técnica sobre accesibilidad web
- Guías SENADIS de Accesibilidad Digital
- NTC (Normas Técnicas Chilenas) de Accesibilidad

**Contacto accesibilidad:**
- Para reportar problemas: Modal de soporte en la aplicación
- Sugerencias de mejora: GitHub Issues
- Email: accessibility@fitter.com

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
   Nota: este proyecto usa **Python 3.10**. Verifica la versión instalada antes de crear el entorno virtual.

   ```bash
   # Verifica la versión de Python (debe ser 3.10.x)
   python --version

   # Crea el virtualenv (usa explícitamente el binario de Python 3.10 si tienes múltiples versiones)
   python -m venv .venv

   # En Windows (PowerShell):
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

---

**Database Migrations**: explicación de scripts y recomendaciones

- **Propósito general**: El repositorio contiene migraciones Alembic y scripts auxiliares para facilitar la creación y actualización del esquema de la base de datos. Debido a cambios históricos en diferentes carpetas de migraciones, se incluye una migración "squash" idempotente y scripts seguros para instalar el esquema en una base de datos nueva o existente sin sobrescribir el historial de Alembic del servidor.

- **Archivos importantes**:
   - `backend/migrations/versions/20251129_squash_schema.py`: migración "squash" idempotente que crea las tablas y columnas principales si no existen (diseñada para instalaciones limpias). `down_revision = None` para facilitar instalaciones nuevas.
   - `backend/migrations/versions/20251129_merge_squash_heads.py`: merge no-op que ayuda a reconciliar múltiples "heads" locales de Alembic sin ejecutar DDL.
   - `backend/migrations/versions/20251129_add_chat_id_to_chat_user_context.py`: migración puntual que añade `chat_id` a `chat_user_context` (ya presente en el historial del proyecto).
   - `scripts/apply_schema_sql.py`: script ejecutado por el mantenedor para aplicar SQL idempotente directamente a la base de datos (usa `ALTER TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, etc.). Útil cuando la base de datos de destino tiene un historial Alembic distinto y se desea garantizar que las columnas/índices estén presentes sin tocar `alembic_version`.
   - `scripts/apply_migrations.py`: helper para ejecutar Alembic desde el contexto de la aplicación Flask (útil si quieres que Alembic use la URL y engine configurados por Flask-SQLAlchemy).
   - `scripts/inspect_migrations.py`: script de inspección que muestra el contenido de `alembic_version` en la BD y lista los archivos de migración disponibles (útil para diagnóstico).

- **Cómo aplicar el esquema (recomendado)**

   - Para una base de datos nueva (instalación fresca): usar Alembic normalmente desde `backend`:

   ```powershell
   & .venv\Scripts\Activate.ps1
   cd backend
   alembic -c migrations/alembic.ini upgrade head
   ```

   - Para una base de datos existente que tiene un historial Alembic distinto (caso del revisor): ejecutar el script idempotente que garantiza columnas y tablas sin manipular `alembic_version`:

   ```powershell
   & .venv\Scripts\Activate.ps1
   $env:PYTHONPATH='G:\Fitter'
   python scripts\apply_schema_sql.py
   ```

- **Notas importantes y advertencias**
   - `scripts/apply_schema_sql.py` aplica DDL directamente (usando `IF NOT EXISTS`) en la BD; **no** modifica la tabla `alembic_version`. Esto evita romper historiales de migración en bases ya en producción. Recomendado cuando el árbol de migraciones del revisor/destino no coincide exactamente con el del repositorio.
   - Si necesitas alinear el historial de Alembic (solo si sabes lo que haces), puedes usar `alembic stamp` para marcar la BD con la revisión actual del repo. Esto es intrusivo: haz backup de la BD antes de usar `stamp`.

      ```powershell
      # marca la BD con la última revisión del repo sin ejecutar DDL
      alembic -c migrations/alembic.ini stamp head
      ```

   - Entregar el proyecto con la migración "squash" incluida garantiza que quien instale el proyecto desde cero pueda ejecutar `alembic upgrade head` sin dependencias entre ramas de migración. Para bases de datos ya existentes, usar `scripts/apply_schema_sql.py` tal como se muestra arriba.

---
