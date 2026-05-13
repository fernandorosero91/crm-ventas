# CRM - Sistema de Gestión de Ventas y Clientes

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/Licencia-MIT-10b981?style=flat)

---

## Descripción

Sistema web de gestión de ventas y clientes (CRM) desarrollado con Django 6.0. Permite a equipos comerciales hacer seguimiento de clientes, gestionar oportunidades de venta a través de un pipeline por etapas, registrar seguimientos, visualizar KPIs en un dashboard interactivo y exportar reportes en PDF, Excel y CSV.

**Características principales:**

- Autenticación segura con tres roles: Administrador, Supervisor y Vendedor
- CRUD completo de clientes y oportunidades de venta
- Pipeline de ventas con 6 etapas y control de transiciones
- Registro de seguimientos (llamadas, emails, reuniones)
- Dashboard con KPIs y gráficos dinámicos (Chart.js)
- Notificaciones automáticas y recordatorios por correo
- Exportación de reportes en PDF, Excel y CSV
- Buscador inteligente por nombre, email o ID
- Arquitectura modular con 7 aplicaciones Django independientes
- Despliegue con Docker + Gunicorn + Nginx

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6.0 |
| Base de datos | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Frontend | HTML + Tailwind CSS + JavaScript |
| Gráficos | Chart.js |
| Servidor WSGI | Gunicorn |
| Proxy inverso | Nginx |
| Contenedores | Docker + Docker Compose |
| Despliegue | Dockploy |
| Exportación | ReportLab (PDF) + openpyxl (Excel) |

---

## Requisitos Previos

Antes de instalar el proyecto, asegúrate de tener:

- **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
- **Docker & Docker Compose** — [docs.docker.com/get-docker](https://docs.docker.com/get-docker/)
- **PostgreSQL 16** (solo para instalación local sin Docker) — [postgresql.org/download](https://www.postgresql.org/download/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/crm.git
cd crm
```

### 2. Crear y activar el entorno virtual

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus valores:

```dotenv
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_URL=postgresql://crm_user:tu_password@localhost:5432/crm_db
# O bien variables individuales:
DB_NAME=crm_db
DB_USER=crm_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# Email (opcional en desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Crear la base de datos en PostgreSQL

```bash
psql -U postgres -c "CREATE DATABASE crm_db;"
psql -U postgres -c "CREATE USER crm_user WITH PASSWORD 'tu_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;"
```

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en [http://localhost:8000](http://localhost:8000).

---

## Despliegue con Docker

### Desarrollo

```bash
# Construir e iniciar todos los servicios (Django + PostgreSQL + Redis)
docker-compose up --build

# En segundo plano
docker-compose up --build -d

# Ver logs
docker-compose logs -f web

# Detener servicios
docker-compose down
```

La aplicación estará disponible en [http://localhost:8000](http://localhost:8000).

### Producción (local)

```bash
# Copiar y configurar variables de entorno de producción
cp .env.prod.example .env.prod
# Editar .env.prod con valores reales de producción

# Construir e iniciar con Nginx
docker-compose -f docker-compose.prod.yml up --build -d

# Crear superusuario en producción
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

La aplicación estará disponible en [http://localhost:80](http://localhost:80).

---

## Despliegue en Producción (Dockploy)

[Dockploy](https://dockploy.com) es la plataforma de despliegue configurada para este proyecto. Sigue estos pasos:

### Paso 1 — Preparar el repositorio

Asegúrate de que el repositorio esté en GitHub/GitLab con los archivos:
- `Dockerfile`
- `docker-compose.prod.yml`
- `dockploy.json`
- `.env.prod.example` (nunca subas `.env.prod` real)

### Paso 2 — Crear el proyecto en Dockploy

1. Inicia sesión en tu instancia de Dockploy
2. Haz clic en **"New Project"** → selecciona **"Docker Compose"**
3. Conecta tu repositorio de GitHub/GitLab
4. Selecciona la rama `main` (o `release/`)
5. Dockploy detectará automáticamente el `dockploy.json`

### Paso 3 — Configurar variables de entorno

En el panel de Dockploy, ve a **"Environment Variables"** y agrega todas las variables del archivo `.env.prod.example`:

```
DJANGO_SECRET_KEY=<clave-secreta-larga-y-aleatoria>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com,www.tudominio.com
POSTGRES_DB=crm_prod
POSTGRES_USER=crm_user
POSTGRES_PASSWORD=<password-seguro>
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@tudominio.com
DJANGO_SUPERUSER_PASSWORD=<password-admin-seguro>
```

### Paso 4 — Configurar el dominio

1. En Dockploy, ve a **"Domains"** y agrega tu dominio
2. Activa **SSL automático** (Let's Encrypt)
3. El proxy de Dockploy redirigirá el tráfico al puerto 80 del contenedor Nginx

### Paso 5 — Desplegar

1. Haz clic en **"Deploy"**
2. Dockploy ejecutará `docker-compose -f docker-compose.prod.yml up --build`
3. El `entrypoint.sh` se encargará automáticamente de:
   - Esperar a que PostgreSQL esté listo
   - Ejecutar `migrate`
   - Ejecutar `collectstatic`
   - Crear el superusuario (si las variables están configuradas)
   - Iniciar Gunicorn

### Paso 6 — Verificar el despliegue

El health check está configurado en `/health/` con intervalo de 30 segundos. Puedes verificar el estado en el panel de Dockploy bajo **"Health"**.

### Paso 7 — Actualizaciones futuras

Para desplegar nuevas versiones, simplemente haz push a la rama configurada. Dockploy detectará el cambio y ejecutará un nuevo despliegue automáticamente (si el auto-deploy está activado).

---

## Estructura del Proyecto

```
crm/
├── core/                        # Módulo base: modelos abstractos, mixins, middleware
│   ├── models.py                # BaseModel, AuditLog, ActiveManager
│   ├── mixins.py                # RoleRequiredMixin, PaginationMixin
│   ├── middleware.py            # RequestLoggingMiddleware
│   ├── utils.py                 # sanitize_input, validate_email_format, validate_phone_format
│   ├── exceptions.py            # Excepciones personalizadas del CRM
│   ├── templatetags/            # Tags de Django para cargar componentes UI
│   └── templates/components/   # Componentes reutilizables (button, card, modal, table…)
│
├── users/                       # Autenticación y gestión de usuarios
│   ├── models.py                # CustomUser (roles: admin, supervisor, vendedor)
│   ├── views.py                 # Login, logout, registro, perfil, gestión de usuarios
│   ├── forms.py                 # RegistrationForm, ProfileForm
│   └── urls.py                  # Rutas de autenticación y gestión
│
├── clientes/                    # Módulo de gestión de clientes
│   ├── models.py                # Client, ClientStatusHistory
│   ├── views.py                 # CRUD de clientes, búsqueda, filtros
│   ├── forms.py                 # ClientForm con validaciones
│   └── urls.py                  # Rutas del módulo clientes
│
├── ventas/                      # Módulo de oportunidades de venta
│   ├── models.py                # Opportunity, FollowUp, StageChange
│   ├── views.py                 # CRUD de oportunidades, pipeline, seguimientos
│   ├── services.py              # advance_stage(), get_pipeline_summary()
│   └── urls.py                  # Rutas del módulo ventas
│
├── dashboard/                   # Dashboard con KPIs y gráficos
│   ├── views.py                 # DashboardView, APIs JSON para Chart.js
│   ├── services.py              # get_kpi_data(), get_monthly_revenue(), etc.
│   └── urls.py                  # Rutas del dashboard y endpoints de charts
│
├── notifications/               # Notificaciones y correos automáticos
│   ├── models.py                # Notification, EmailLog
│   ├── views.py                 # Lista de notificaciones, marcar como leída
│   ├── services.py              # create_notification(), send_email_with_retry()
│   ├── management/commands/     # check_reminders (comando de gestión)
│   └── urls.py                  # Rutas del módulo notificaciones
│
├── reports/                     # Generación y exportación de reportes
│   ├── views.py                 # ReportView, ExportPDFView, ExportExcelView, ExportCSVView
│   ├── forms.py                 # ReportFilterForm
│   ├── services.py              # generate_pdf_report(), generate_excel_export(), generate_csv_export()
│   └── urls.py                  # Rutas del módulo reportes
│
├── crm/                         # Configuración principal del proyecto
│   ├── settings/
│   │   ├── base.py              # Configuración compartida
│   │   ├── development.py       # Configuración de desarrollo
│   │   └── production.py        # Configuración de producción
│   ├── urls.py                  # URL raíz del proyecto
│   ├── wsgi.py                  # Punto de entrada WSGI (Gunicorn)
│   └── asgi.py                  # Punto de entrada ASGI
│
├── nginx/                       # Configuración de Nginx
│   ├── nginx.conf               # Configuración principal
│   └── conf.d/crm.conf          # Virtual host del CRM
│
├── static/                      # Archivos estáticos (JS, CSS, imágenes)
│   └── js/
│       ├── form_validation.js   # Validación en tiempo real
│       ├── table_sort.js        # Ordenamiento de tablas
│       └── interactions.js      # Modal, sidebar, alertas
│
├── Dockerfile                   # Imagen Docker de producción (python:3.11-slim + Gunicorn)
├── docker-compose.yml           # Servicios de desarrollo (web + db + redis)
├── docker-compose.prod.yml      # Servicios de producción (web + db + redis + nginx)
├── entrypoint.sh                # Script de inicio: espera DB, migra, collectstatic
├── dockploy.json                # Configuración de despliegue en Dockploy
├── .env.example                 # Plantilla de variables de entorno (desarrollo)
├── .env.prod.example            # Plantilla de variables de entorno (producción)
├── requirements.txt             # Dependencias Python del proyecto
└── manage.py                    # CLI de Django
```

---

## Modelos Principales

El sistema cuenta con los siguientes modelos principales relacionados entre sí:

```
CustomUser
├── role: administrator | supervisor | vendedor
├── supervisor → CustomUser (FK, auto-referencia)
└── team_members ← CustomUser[]

Client  (hereda BaseModel)
├── company_name, contact_name, email (único), phone, address, industry
├── assigned_vendedor → CustomUser (FK)
├── created_by → CustomUser (FK)
└── status_history ← ClientStatusHistory[]

Opportunity  (hereda BaseModel)
├── title, estimated_value, probability (0-100), expected_close_date
├── stage: prospeccion | calificacion | propuesta | negociacion | cierre_ganado | cierre_perdido
├── weighted_value (calculado: estimated_value × probability / 100)
├── actual_close_date, loss_reason
├── client → Client (FK)
├── assigned_vendedor → CustomUser (FK)
├── follow_ups ← FollowUp[]
└── stage_changes ← StageChange[]

FollowUp  (hereda BaseModel)
├── follow_up_type: call | email | meeting | other
├── date, notes (mín. 10 chars), next_action_date
├── opportunity → Opportunity (FK, nullable)
├── client → Client (FK, nullable)
└── created_by → CustomUser (FK)

StageChange  (auditoría, no hereda BaseModel)
├── from_stage, to_stage, changed_at
├── opportunity → Opportunity (FK)
└── changed_by → CustomUser (FK)

Notification  (hereda BaseModel)
├── title, message, is_read, link
├── notification_type: reminder | follow_up | stage_change | inactivity | system
└── recipient → CustomUser (FK)

EmailLog  (hereda BaseModel)
├── recipient_email, subject, status (pending | sent | failed)
├── retry_count, sent_at, error_message

AuditLog  (auditoría del sistema)
├── endpoint, method, timestamp, ip_address, user_agent, status_code
└── user → CustomUser (FK)
```

> **BaseModel** es una clase abstracta que provee `created_at`, `updated_at`, `is_active` y el manager `ActiveManager` (filtra `is_active=True` por defecto) a todos los modelos que la heredan.

---

## Rutas Principales

### Autenticación (`/users/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/users/login/` | GET, POST | Inicio de sesión |
| `/users/logout/` | POST | Cierre de sesión |
| `/users/register/` | GET, POST | Registro de nuevo usuario (solo Admin) |
| `/users/profile/` | GET, POST | Ver y editar perfil propio |
| `/users/password-change/` | GET, POST | Cambiar contraseña |
| `/users/users/` | GET | Lista de usuarios (solo Admin) |
| `/users/users/create/` | GET, POST | Crear usuario (solo Admin) |
| `/users/users/<id>/edit/` | GET, POST | Editar usuario (solo Admin) |
| `/users/users/<id>/deactivate/` | POST | Desactivar usuario (solo Admin) |

### Clientes (`/clientes/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/clientes/` | GET | Lista de clientes (filtrada por rol) |
| `/clientes/nuevo/` | GET, POST | Crear nuevo cliente |
| `/clientes/<id>/` | GET | Detalle del cliente con timeline |
| `/clientes/<id>/editar/` | GET, POST | Editar cliente |
| `/clientes/<id>/eliminar/` | POST | Eliminar cliente (soft delete) |
| `/clientes/buscar/` | GET | Búsqueda inteligente de clientes |

### Ventas (`/ventas/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/ventas/` | GET | Lista de oportunidades (filtrada por rol) |
| `/ventas/nueva/` | GET, POST | Crear oportunidad |
| `/ventas/<id>/` | GET | Detalle de oportunidad con historial |
| `/ventas/<id>/editar/` | GET, POST | Editar oportunidad |
| `/ventas/<id>/eliminar/` | POST | Eliminar oportunidad (soft delete) |
| `/ventas/<id>/cambiar-etapa/` | POST | Avanzar etapa del pipeline |
| `/ventas/pipeline/` | GET | Vista visual del pipeline por etapas |
| `/ventas/seguimiento/nuevo/` | GET, POST | Registrar seguimiento |
| `/ventas/seguimiento/<id>/editar/` | GET, POST | Editar seguimiento |
| `/ventas/seguimiento/<id>/eliminar/` | POST | Eliminar seguimiento |

### Dashboard (`/dashboard/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/dashboard/` | GET | Dashboard principal con KPIs |
| `/dashboard/api/charts/revenue/` | GET | JSON: ingresos mensuales (Chart.js) |
| `/dashboard/api/charts/pipeline/` | GET | JSON: oportunidades por etapa (Chart.js) |
| `/dashboard/api/charts/clients/` | GET | JSON: nuevos clientes por mes (Chart.js) |
| `/dashboard/api/charts/vendedores/` | GET | JSON: top vendedores (Chart.js) |

### Notificaciones (`/notifications/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/notifications/` | GET | Lista de notificaciones del usuario |
| `/notifications/<id>/read/` | POST | Marcar notificación como leída |
| `/notifications/mark-all-read/` | POST | Marcar todas como leídas |
| `/notifications/unread-count/` | GET | JSON: conteo de no leídas (navbar) |

### Reportes (`/reports/`)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/reports/` | GET, POST | Filtros y vista previa del reporte |
| `/reports/exportar/pdf/` | GET | Descargar reporte en PDF |
| `/reports/exportar/excel/` | GET | Descargar reporte en Excel (.xlsx) |
| `/reports/exportar/csv/` | GET | Descargar reporte en CSV |

---

## Roles y Permisos

| Funcionalidad | Administrador | Supervisor | Vendedor |
|---------------|:---:|:---:|:---:|
| Ver todos los clientes | ✅ | ✅ (equipo) | ✅ (propios) |
| Crear clientes | ✅ | ✅ | ✅ |
| Editar clientes | ✅ | ✅ (equipo) | ✅ (propios) |
| Eliminar clientes | ✅ | ✅ (equipo) | ❌ |
| Ver todas las oportunidades | ✅ | ✅ (equipo) | ✅ (propias) |
| Crear oportunidades | ✅ | ✅ | ✅ |
| Avanzar etapa del pipeline | ✅ | ✅ | ✅ (solo avanzar) |
| Retroceder etapa del pipeline | ✅ | ✅ | ❌ |
| Ver reportes | ✅ | ✅ (equipo) | ✅ (propios) |
| Exportar reportes | ✅ | ✅ | ✅ |
| Gestionar usuarios | ✅ | ❌ | ❌ |
| Registrar nuevos usuarios | ✅ | ❌ | ❌ |
| Asignar supervisores | ✅ | ❌ | ❌ |
| Ver dashboard completo | ✅ | ✅ (equipo) | ✅ (propio) |
| Acceder al admin de Django | ✅ | ❌ | ❌ |

---

## Equipo de Desarrollo

| Desarrollador | Módulos Asignados | Rama Git |
|---------------|-------------------|----------|
| **Dev 1** | `core` + `users` (autenticación, roles, componentes UI base) | `feature/core-auth` |
| **Dev 2** | `clientes` (CRUD, búsqueda, filtros, timeline) | `feature/clientes` |
| **Dev 3** | `ventas` (oportunidades, pipeline, seguimientos) | `feature/ventas` |
| **Dev 4** | `dashboard` + `notifications` + `reports` + DevOps | `feature/dashboard-reports` |

### Convención de ramas

```
feature/   → nuevas funcionalidades
fix/       → corrección de bugs
hotfix/    → corrección urgente en producción
release/   → preparación de versión
```

### Convención de commits

```
feat(scope): descripción      → nueva funcionalidad
fix(scope): descripción       → corrección de bug
refactor(scope): descripción  → refactorización
style(scope): descripción     → cambios de estilo/formato
docs(scope): descripción      → documentación
chore(scope): descripción     → tareas de mantenimiento
```

---

## Variables de Entorno

Consulta `.env.example` para desarrollo y `.env.prod.example` para producción. Las variables más importantes son:

| Variable | Descripción | Requerida en prod |
|----------|-------------|:-----------------:|
| `SECRET_KEY` | Clave secreta de Django | ✅ |
| `DEBUG` | Modo debug (`False` en prod) | ✅ |
| `ALLOWED_HOSTS` | Hosts permitidos | ✅ |
| `DATABASE_URL` | URL de conexión a PostgreSQL | ✅ |
| `REDIS_URL` | URL de conexión a Redis | ✅ |
| `EMAIL_HOST_USER` | Cuenta de correo para envíos | ✅ |
| `EMAIL_HOST_PASSWORD` | Contraseña / App Password | ✅ |
| `DJANGO_SUPERUSER_*` | Credenciales del superusuario inicial | Opcional |

> ⚠️ **Nunca** subas los archivos `.env` o `.env.prod` al repositorio. Están incluidos en `.gitignore`.

---

## Comandos Útiles

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear migraciones nuevas
python manage.py makemigrations

# Verificar recordatorios y enviar notificaciones
python manage.py check_reminders

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Abrir shell de Django
python manage.py shell

# Ver logs en Docker
docker-compose logs -f web
docker-compose logs -f db
```

---

## Paleta de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| Azul oscuro | `#1e3a5f` | Sidebar, botones primarios |
| Azul petróleo | `#2c6e8a` | Botones secundarios, acentos |
| Gris grafito | `#4a4a4a` | Texto principal |
| Blanco | `#ffffff` | Fondos, tarjetas |
| Verde esmeralda | `#10b981` | Indicadores positivos, éxito |



---

## Licencia

Este proyecto fue desarrollado como trabajo académico. Todos los derechos reservados.
