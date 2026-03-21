# Fitter – Plataforma Integral para Gimnasios

Proyecto de Titulo – Ingenieria en Informatica (INACAP)
Autores: Bryan Carreno / Diego Guzman
Docente Guia: Ivan Riquelme Nunez

---

## Descripcion

Fitter es una **plataforma integral para gimnasios y centros deportivos** con chatbot en espanol disenado con **Rasa**. Permite a los usuarios y administradores:

- Consultar rutinas personalizadas de entrenamiento (a traves del chatbot).
- Gestionar inventario y productos con catalogo avanzado.
- Realizar compras y pagos simulados.
- Reservar clases con calendario interactivo semanal/mensual.
- Explorar planes de entrenamiento de heroes (Entrenos Unicos).
- Comparar planes de rutinas y dietas side-by-side.
- Gestionar suscripciones (Basic / Premium / Black).
- Recibir notificaciones en tiempo real via WebSocket.
- Solicitar handoff a agente humano desde el chat.
- Consultar metricas operacionales en dashboard de analiticas.
- Navegar en multiples idiomas (Espanol / Ingles).
- Autenticacion segura con MFA y Google Sign-In.

El sistema cumple con la normativa chilena (Ley 21.719) sobre proteccion de datos y WCAG 2.1 nivel AA.

---

## Features Principales

### Multi-idioma (i18n)
- Soporte completo Espanol / Ingles con `LocaleContext`
- Selector de idioma en controles laterales
- 200+ claves de traduccion cubriendo todas las paginas

### Catalogo de Productos
- Grid de productos con filtros (categoria, precio, stock)
- Tags de filtros activos con remocion individual
- Descripcion con line-clamp y dark mode completo
- Sidebar de carrito con resumen de compra

### Entrenos Unicos
- Planes de entrenamiento inspirados en heroes (Superman Corenswet, etc.)
- Carousel de cards con navegacion
- Vista detalle con plan de entrenamiento + dieta + tabla nutricional
- Carousel de imagenes de comidas por heroe

### Calendario de Clases
- Vista semanal y mensual con CSS Grid
- Reserva/cancelacion de clases con validacion de capacidad
- Indicadores visuales: reservada (verde), llena (gris), disponible (azul)
- Datos de ejemplo cuando el backend no esta disponible

### Comparacion de Planes
- Modal reutilizable para comparar 2 planes side-by-side
- Funciona con rutinas y dietas
- Resalta diferencias entre planes

### Gestion de Suscripciones
- Tres niveles: Basic, Premium, Black
- CRUD completo con estados (active/cancelled/expired/pending)
- Cambio y cancelacion desde el perfil

### Handoff a Humano
- Solicitud de atencion humana desde el chatbot
- Panel admin con cola de handoffs (pendientes/asignados/resueltos)
- Notificacion en tiempo real a admins

### Dashboard de Analiticas
- KPI cards: fallback rate, handoff rate, p95 latency
- Distribucion de status codes (2xx/4xx/5xx)
- Auto-refresh cada 30 segundos

### Notificaciones en Tiempo Real
- WebSocket con Socket.IO (backend + frontend)
- Campana con badge de no leidas en navbar
- Toasts auto-dismiss con `aria-live="polite"`
- Eventos: booking confirmado, suscripcion cambiada, handoff creado

---

## Sistema de Temas (Modo Claro / Oscuro)

- **Acceso rapido:** Boton en controles laterales
- **Persistencia:** Se guarda en `localStorage`
- **Respuesta del SO:** Detecta `prefers-color-scheme` automaticamente
- **Variables CSS:** Sistema completo (`--bg`, `--text`, `--surface`, `--border`, `--muted`)
- **Transiciones suaves:** 200ms para cambios de color
- **Cobertura completa:** Todos los componentes respetan el tema

---

## Accesibilidad

Fitter cumple con **WCAG 2.1 nivel AA** y la **Ley 20.422** (Chile).

- ARIA labels y roles semanticos completos
- Navegacion por teclado con skip-link
- Contraste AA/AAA verificado en ambos temas
- Alt text en todas las imagenes funcionales
- Click targets minimo 44x44px
- Respeta `prefers-reduced-motion`
- Sistema de botones normalizado con `buttons.css`

Documentacion completa en [ACCESIBILIDAD.md](frontend/ACCESIBILIDAD.md).

---

## Tecnologias

### Backend
- **Python 3.10**
- **Rasa 3.6** (NLP / NLU)
- **Flask 3.1.2** + Flask-SQLAlchemy + Flask-Migrate
- **python-socketio 5.15** (WebSocket en tiempo real)
- **PostgreSQL** con psycopg2-binary
- **Alembic** (migraciones de esquema)
- **PyOTP** (MFA), **Cryptography** (cifrado), **ReportLab** (PDFs)
- **MercadoPago SDK** (pagos)

### Frontend
- **React 18.2** con **Vite 5.4** (bundler)
- **React Router DOM 7.9**
- **Bootstrap 5.3**
- **socket.io-client 4.8** (notificaciones en tiempo real)
- **Vitest** + **Testing Library** (tests)

### DevOps
- **Docker** + **Nginx** (proxy reverso)
- **GitHub** (control de versiones)

---

## Estructura del Proyecto

```
Fitter/
├── backend/
│   ├── carritoapp/          # Carrito de compras
│   ├── chat/                # Integracion con Rasa
│   ├── classes/             # Clases y reservas (ClassBooking)
│   ├── gestor_inventario/   # Productos e inventario
│   ├── handoff/             # Handoff a agente humano
│   ├── login/               # Autenticacion y MFA
│   ├── metrics/             # Metricas operacionales
│   ├── notifications/       # Notificaciones por email
│   ├── orders/              # Gestion de ordenes
│   ├── profile/             # Perfiles (con cifrado)
│   ├── realtime/            # WebSocket (Socket.IO)
│   ├── security/            # Seguridad y sesiones
│   ├── subscriptions/       # Gestion de suscripciones
│   └── templates/           # Templates HTML
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, Footer, SideControls, NotificationBell, etc.
│   │   ├── contexts/        # Auth, Cart, Theme, Locale, FontSize, Notification
│   │   ├── pages/           # Todas las paginas (lazy-loaded)
│   │   ├── services/        # API client (apijs.js)
│   │   └── styles/          # CSS por feature + buttons.css + legacy/
│   └── dist/                # Build de produccion
├── Chatbot/                 # Modelos y config de Rasa
│   ├── data/                # NLU, stories, rules
│   └── models/              # Modelos entrenados
├── actions/                 # Acciones personalizadas de Rasa
├── migrations/              # Migraciones Alembic
├── scripts/                 # Scripts de utilidad
├── infra/                   # Docker y Nginx
└── requirements.txt         # Dependencias Python
```

---

## Arranque Rapido

### 1. Dependencias

```bash
# Python 3.10 requerido
python -m venv .venv

# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
pip install rasa

# Frontend
cd frontend
npm install
```

### 2. Variables de entorno

```bash
export PROFILE_ENCRYPTION_KEY="<clave-Fernet>"
export CHAT_CONTEXT_API_KEY="<token-opcional>"
export GOOGLE_CLIENT_IDS="tu-client-id.apps.googleusercontent.com"
export VITE_GOOGLE_CLIENT_ID="tu-client-id.apps.googleusercontent.com"
```

Genera la clave Fernet:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Base de datos

```bash
cd backend
alembic -c migrations/alembic.ini upgrade head
```

Para bases existentes con historial Alembic diferente:
```bash
python scripts/apply_schema_sql.py
```

### 4. Iniciar servicios

```bash
# Opcion 1: Script automatico (Windows)
scripts\start_project.bat

# Opcion 2: Manual
# Terminal 1 - Backend Flask:
python -m flask --app backend.app run --port 5000

# Terminal 2 - Rasa:
rasa run --enable-api --cors "*"

# Terminal 3 - Rasa Actions:
rasa run actions

# Terminal 4 - Frontend (desarrollo):
cd frontend && npm run dev
```

Servicios:
- Backend Flask: `http://localhost:5000`
- Rasa: `http://localhost:5005`
- Rasa Actions: `http://localhost:5055`
- Frontend dev: `http://localhost:3000`

---

## Tests

```bash
# Backend (28 tests)
python -m pytest backend/tests/ -v

# Frontend (3 tests)
cd frontend && npx vitest run
```

Tests backend cubren: autenticacion MFA, Google Auth, chat audit/consent, perfiles, productos, endpoints operacionales.

Tests frontend: smoke test de App (navbar, login CTA, logo).

---

## Build de Produccion

```bash
cd frontend
npm run build
```

Los archivos se generan en `frontend/dist/`.

---

## Login con Google

- `GOOGLE_CLIENT_IDS` acepta uno o varios Client IDs (separados por comas)
- `VITE_GOOGLE_CLIENT_ID` debe apuntar al Client ID del frontend
- Usuarios nuevos reciben formulario para definir su apodo
- Modo mock disponible para tests: `GOOGLE_AUTH_VERIFY_MODE=mock`

---

## Seguridad

- Cifrado de datos sensibles con Fernet (`PROFILE_ENCRYPTION_KEY`)
- CSRF protection en todas las operaciones POST/PUT/DELETE
- MFA con TOTP y codigos de respaldo
- Rate limiting en endpoints sensibles
- Cumplimiento Ley 21.719 (proteccion de datos, Chile)

Politicas completas en `docs/policies/security-policy.md`.

---

## Migraciones

El proyecto usa Alembic para migraciones de esquema. Migraciones recientes:

- `20260319_add_class_booking.py` — Modelo ClassBooking
- `20260319_add_subscription.py` — Modelo Subscription
- `20260319_add_handoff_request.py` — Modelo HandoffRequest

Ver `migrations/versions/` para el historial completo.

---

## Generar ejemplos NLU

```bash
python scripts/generate_nlu_dataset.py --update-nlu
```

Genera hasta 2000 ejemplos por intent y actualiza `Chatbot/data/nlu.yml`.
