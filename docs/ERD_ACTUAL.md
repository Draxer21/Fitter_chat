# ERD actual de la base de datos (modelo vigente)

Este diagrama refleja las entidades persistentes detectadas en los modelos SQLAlchemy actuales.

```mermaid
erDiagram
    USER {
        int id PK
        string email
        string username
        string full_name
        string auth_provider
        bool is_admin
        datetime created_at
        datetime updated_at
    }

    USER_PROFILE {
        int id PK
        int user_id FK UNIQUE
        binary encrypted_payload
        string payload_checksum
        datetime created_at
        datetime updated_at
    }

    USER_HERO_PLAN {
        int id PK
        int user_id FK
        string plan_key
        string title
        json payload
        datetime created_at
    }

    CHAT_USER_CONTEXT {
        int id PK
        string sender_id UNIQUE
        string chat_id
        int user_id FK
        json history
        bool consent_given
        datetime last_interaction_at
        datetime created_at
        datetime updated_at
    }

    PROGRESS_LOG {
        int id PK
        string sender_id
        int user_id FK
        string metric
        string value
        datetime recorded_at
        datetime created_at
    }

    DIET_PLANS {
        uuid id PK
        int user_id FK
        string title
        string goal
        json content
        int version
        datetime created_at
        datetime updated_at
    }

    ROUTINE_PLANS {
        uuid id PK
        int user_id FK
        string title
        string objective
        json content
        int version
        datetime created_at
        datetime updated_at
    }

    SUBSCRIPTION {
        int id PK
        int user_id FK
        string plan_type
        string status
        datetime start_date
        datetime end_date
    }

    HANDOFF_REQUEST {
        int id PK
        int user_id FK
        int assigned_admin_id FK
        string sender_id
        string reason
        string status
        datetime created_at
        datetime updated_at
    }

    ORDER {
        int id PK
        int user_id
        string customer_email
        string status
        numeric total_amount
        string currency
        string payment_method
        string payment_reference
        json metadata
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id
        string product_name
        int quantity
        numeric unit_price
        numeric subtotal
    }

    PAYMENT {
        int id PK
        int order_id FK
        string preference_id UNIQUE
        string payment_id UNIQUE
        string status
        float transaction_amount
        string currency_id
        datetime created_at
        datetime updated_at
    }

    FITNESS_CLASS {
        int id PK
        string name
        int duration_min
        int capacity
        bool active
        datetime created_at
        datetime updated_at
    }

    CLASS_SESSION {
        int id PK
        int class_id FK
        datetime start_time
        int duration_override
        int capacity_override
        bool is_exclusive
        datetime created_at
        datetime updated_at
    }

    CLASS_BOOKING {
        int id PK
        int session_id FK
        int user_id FK
        datetime booked_at
        datetime cancelled_at
    }

    USER ||--|| USER_PROFILE : has_one
    USER ||--o{ USER_HERO_PLAN : has_many
    USER ||--o{ CHAT_USER_CONTEXT : links_by_user_id
    USER ||--o{ PROGRESS_LOG : tracks
    USER ||--o{ DIET_PLANS : owns
    USER ||--o{ ROUTINE_PLANS : owns
    USER ||--o{ SUBSCRIPTION : has
    USER ||--o{ HANDOFF_REQUEST : requests
    USER ||--o{ HANDOFF_REQUEST : assigned_admin

    ORDER ||--|{ ORDER_ITEM : contains
    ORDER ||--|| PAYMENT : paid_by

    FITNESS_CLASS ||--o{ CLASS_SESSION : schedules
    CLASS_SESSION ||--o{ CLASS_BOOKING : receives
    USER ||--o{ CLASS_BOOKING : books
```

## Nota de alineación con el diagrama antiguo

- El esquema antiguo con `Rutina`, `DetalleRutina` y `Ejercicio` como tablas normalizadas no es el modelo persistente actual.
- El modelo vigente guarda planes en `routine_plans.content` y `diet_plans.content` (JSON).
- `PerfilFisico` ahora corresponde a `user_profile` y parte de su información sensible se almacena cifrada en `encrypted_payload`.
- `OrdenPago` no existe como tabla con ese nombre; hoy se usa `order` + `payment`.
- No se detectó una tabla `audit_log` activa en los modelos actuales.

## Aclaraciones para informe académico

- Este archivo documenta un ERD (modelo de datos), no un diagrama de clases UML.
- En ERD no se usan visibilidades `+`/`-`; esas marcas aplican a UML de clases.
- Si en el informe incluyes UML de clases para `Action` y derivadas, usa `-` en atributos y `+` en métodos para mayor formalidad.
- Las flechas punteadas con texto explicativo deben describirse como dependencias de uso (runtime), no como asociaciones estructurales persistentes.
- En el estado actual del código, no hay un modelo SQLAlchemy `AuditLog` activo; por eso no se representa en este ERD.
