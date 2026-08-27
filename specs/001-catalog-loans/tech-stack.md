# Stack tecnológico — Catálogo y Préstamos de la Biblioteca Municipal

**Feature**: `001-catalog-loans` · **Date**: 2026-08-27 · Complementa [plan.md](./plan.md) y [research.md](./research.md).

Decisiones confirmadas con el usuario (2026-08-27):

1. Empaquetado de escritorio: **pywebview + PyInstaller**.
2. Autenticación: **auth propia de Django para todo** (central con email, operadores sin email).
3. Interfaz: **plantillas Django + HTMX** (CSS Bootstrap 5).
4. Datos: **Supabase = PostgreSQL gestionado**; **Django ORM directo**, migraciones de Django, **sin** SDK de Supabase, **sin** PostgREST, **sin** GoTrue, **sin** RLS.

---

## 1. Runtime y plataforma

| Elemento | Elección | Notas |
|---|---|---|
| Lenguaje | **Python 3.12+** (objetivo 3.13) | En el equipo hay 3.11 y 3.13; `uv` gestiona la versión del proyecto |
| SO objetivo (producción) | **Windows 10/11 x64** | La app corre en cada puesto de mostrador |
| SO desarrollo | Cualquiera | El empaquetado `.exe` se prueba en Windows |
| Zona horaria / idioma | `Europe/Madrid`, `es` | `USE_TZ=True`, fechas `dd/mm/aaaa` |

## 2. Gestión de proyecto y dependencias

| Elemento | Elección | Uso |
|---|---|---|
| Gestor de paquetes/venv | **uv** (ya instalado, 0.11) | `pyproject.toml` (PEP 621) + `uv.lock` (versiones exactas) |
| Rangos en `pyproject.toml` | `~=` (compatible) | El pin exacto vive en `uv.lock` |
| Layout | `src/` con apps Django dentro | `manage.py` en la raíz |

## 3. Framework web y aplicación

| Elemento | Elección | Notas |
|---|---|---|
| Framework | **Django 5.2 LTS** | Soporte extendido; compatible con Python 3.12/3.13 |
| Apps del proyecto | `common`, `cuentas`, `catalogo`, `prestamos`, `configuracion`, `privacidad` | Una por área de dominio (ver plan.md §Project Structure) |
| Configuración | **django-environ** + `.env` | Claves: `DATABASE_URL`, `SECRET_KEY`, `DJANGO_DEBUG`, `APP_ENTORNO` (`dev`\|`desktop`\|`test`), `SESSION_INACTIVIDAD_SEGUNDOS` (def. 1800), `RETENCION_PRESTATARIOS_DIAS` (def. 730) |
| `settings` | Único `gestion_biblioteca/settings.py` gobernado por `APP_ENTORNO` | Sin split de archivos (YAGNI); alterna DEBUG, almacenamiento de estáticos y logging |
| Servidor WSGI (empaquetado) | **waitress** | WSGI puro-Python, estable en Windows; sustituye a `runserver` en el `.exe` |
| Estáticos | **whitenoise** + `ManifestStaticFilesStorage` | Sirve CSS/JS desde el propio `.exe`, sin servidor aparte |

## 4. Base de datos y acceso a datos

| Elemento | Elección | Notas |
|---|---|---|
| Motor | **PostgreSQL** gestionado por **Supabase** (nube) | Se aprovecha de Supabase: Postgres, backups automáticos, panel |
| Acceso | **Django ORM directo** (SQL vía psycopg) | Nada de `supabase-py` / PostgREST / Realtime / GoTrue / RLS |
| Driver | **psycopg 3.2** (`psycopg[binary]`) | Recomendado por Django 5.2 |
| Conexión | **Session pooler** de Supabase, puerto `5432`, `sslmode=require`, `CONN_MAX_AGE=0` | El *transaction pooler* (6543) no sirve: rompe sentencias con estado de sesión |
| Migraciones | **Solo migraciones de Django** | Única fuente del esquema |
| Extensiones PG | `unaccent`, `pg_trgm` | Habilitadas en la 1.ª migración (`CreateExtension`) |
| Entorno de dev | Postgres local (16.x) **o** un proyecto Supabase aparte para dev | Nunca desarrollar contra la BD de producción |
| Tests | BD de test dedicada (`test_postgres`) que crea Django | `pytest-django` |
| Concurrencia | `select_for_update()` + **índice único parcial** "1 préstamo activo por ejemplar" | Garantiza SC-004 (ver data-model.md §Invariantes) |

## 5. Autenticación, autorización y sesión

| Elemento | Elección | Notas |
|---|---|---|
| Framework de auth | **`django.contrib.auth`** (modelo `User` estándar) | Un único sistema de identidad |
| Cuenta central | `User` con `email` + contraseña; perfil `Operador(es_central=True)` | Único usuario con correo |
| Subcuentas de operador | `User` con `username` único, contraseña, `email=''`; `Operador(es_central=False)` | `is_active` = activar/desactivar (FR-030f) |
| Hashing de contraseñas | **argon2-cffi** (Argon2) como principal, PBKDF2 de reserva | `PASSWORD_HASHERS` |
| Política de contraseña | Validadores de Django, mínimo **8** caracteres | Ajustable |
| Bloqueo por intentos fallidos | **django-axes** (bloqueo tras 5 fallos / 10 min) | Puesto compartido: conviene |
| Sesión | Backend en BD; `SESSION_COOKIE_AGE=SESSION_INACTIVIDAD_SEGUNDOS`, `SESSION_SAVE_EVERY_REQUEST=True` | Cierre por inactividad (def. 30 min) |
| Cookies | `SECURE=False` (localhost HTTP en webview), `SAMESITE='Lax'`, `HTTPONLY=True` | |
| Autorización | Permiso `cuentas.gestion` + mixin `SoloCentralMixin` | "Solo central": subcuentas, `ParametrosPrestamo`, anonimización manual |
| CSRF | Middleware de Django en todas las escrituras | |

## 6. Capa de presentación

| Elemento | Elección | Notas |
|---|---|---|
| Plantillas | **Django Template Language** (renderizado en servidor) | |
| Interactividad | **HTMX 2.x** (vendorizado, sin CDN) | Refrescos parciales: búsqueda, contadores de disponibilidad, alta de gestión de reclamación, validación en línea |
| JS a medida | Vanilla, mínimo | Foco del lector de código de barras, atajos de mostrador |
| CSS/Componentes | **Bootstrap 5.3** (vendorizado) | Accesible, familiar, rápido para herramienta interna |
| Iconos | Bootstrap Icons (vendorizado) | Opcional |
| Formularios | Django Forms + **django-crispy-forms** + **crispy-bootstrap5** | Render consistente Bootstrap |
| Assets | Todos **locales** dentro del paquete | La app es de escritorio; sin dependencias de red para la UI |

## 7. Escritorio (empaquetado)

| Elemento | Elección | Notas |
|---|---|---|
| Ventana nativa | **pywebview 5.x** | Usa **WebView2** (Edge/Chromium) de Windows 10/11 |
| Runtime WebView2 | Comprobación en el primer arranque + aviso amable con enlace | No se instala automáticamente |
| Empaquetado | **PyInstaller 6.x**, build *one-dir* → `dist/BibliotecaMunicipal/` | `desktop/build.spec` versionado |
| Arranque | `desktop/launcher.py`: `waitress` en `127.0.0.1:<puerto libre>` en un hilo + `webview.create_window(...)` | Ejecuta `migrate` si el esquema está desactualizado |
| Distribución | Carpeta + acceso directo; **MSI** solo si el Ayuntamiento lo exige | |

## 8. Tareas programadas

| Elemento | Elección | Notas |
|---|---|---|
| Anonimización RGPD (FR-034) | `manage.py anonimizar_prestatarios` vía **Programador de tareas de Windows** (diario) en un puesto designado | Idempotente; escribe `EntradaAuditoria` |
| Cola de tareas / broker | **Ninguno** (sin Celery/Redis) | Escala y necesidades no lo justifican |
| Disparo manual | Botón "Ejecutar ahora" para la cuenta central (`/privacidad/`) | |

## 9. Búsqueda

| Elemento | Elección |
|---|---|
| Coincidencia parcial insensible a mayúsculas/acentos | `pg_trgm` + `unaccent` sobre columna generada `busqueda_norm` con índice **GIN `gin_trgm_ops`** |
| API | `django.contrib.postgres` (`TrigramSimilarity`, lookups `unaccent`) o `LIKE` normalizado | 
| Paginación | 25 resultados/página; autocompletar máx. 10 |

## 10. Observabilidad y errores

| Elemento | Elección | Notas |
|---|---|---|
| Logging | `logging` de Django → fichero rotativo en `%LOCALAPPDATA%\BibliotecaMunicipal\logs\` (+ consola en dev) | |
| Auditoría de negocio | Tabla `EntradaAuditoria` (nivel app) | FR-030d, FR-031, SC-013 |
| Error de conexión | Middleware que captura `OperationalError`/`InterfaceError` y muestra pantalla clara | Edge "sin conexión" |
| Reporte remoto de errores | **Sentry** (`sentry-sdk`) — **opcional, desactivado por defecto** | Sensibilidad on-premise; activable por env |

## 11. Calidad, pruebas y automatización

| Elemento | Elección | Notas |
|---|---|---|
| Test runner | **pytest** + **pytest-django** + **pytest-cov** | |
| Datos de prueba | **factory_boy** + **Faker** | |
| Concurrencia | `TransactionTestCase` para el caso "dos préstamos del mismo ejemplar" | |
| Lint + formato | **ruff** (reemplaza flake8 + isort + black) | `ruff check` y `ruff format` |
| Tipado | Type hints en servicios + **mypy** con **django-stubs** | En CI **no bloqueante** al inicio |
| Hooks | **pre-commit**: ruff, ruff-format, `manage.py check`, `makemigrations --check` | |
| CI | GitHub Actions (si el repo va a GitHub): lint + tests con contenedor Postgres | Opcional hasta que haya remoto |

## 12. Seguridad y secretos

- `SECRET_KEY` desde `.env`, distinta por instalación; nunca en el repositorio.
- `.env` en `.gitignore`; `.env.example` versionado con las claves y sin valores reales.
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`, `DEBUG=False` en el paquete.
- Contraseñas con Argon2; bloqueo con django-axes.
- Dependencias fijadas en `uv.lock`; revisión periódica con `uv lock --upgrade`.
- Copias de seguridad: se confía en los backups automáticos de Supabase; verificación mensual documentada en quickstart (cuestión de fiabilidad marcada como pendiente de bajo impacto).

## 13. Dependencias (resumen para `pyproject.toml`)

**Ejecución**
```
django~=5.2
psycopg[binary]~=3.2
django-environ~=0.11
whitenoise~=6.7
waitress~=3.0
pywebview~=5.3
django-crispy-forms~=2.3
crispy-bootstrap5~=2024.10
django-axes~=6.5
argon2-cffi~=23.1
```
Assets vendorizados (no pip): HTMX 2.x, Bootstrap 5.3, Bootstrap Icons.

**Desarrollo / build**
```
pytest~=8.3
pytest-django~=4.9
pytest-cov~=5.0
factory-boy~=3.3
ruff~=0.6
mypy~=1.11
django-stubs~=5.1
pre-commit~=3.8
pyinstaller~=6.10
```
Opcional: `sentry-sdk` (desactivado por defecto).

## 14. .gitignore (añadir)

```
.env
.venv/
__pycache__/
*.py[cod]
db.sqlite3
/staticfiles/
/media/
/dist/
/build/
htmlcov/
.coverage
.pytest_cache/
.ruff_cache/
.mypy_cache/
.claude/settings.local.json
```
(No ignorar `desktop/build.spec`.)

## 15. Qué NO usamos (y por qué)

| Descartado | Motivo |
|---|---|
| `supabase-py` / PostgREST / Realtime | Duplicaría el modelo, complicaría transacciones multi-tabla y pruebas |
| Supabase Auth (GoTrue) | Los operadores no tienen correo; mezclar dos sistemas de identidad añade fallos |
| Row-Level Security (RLS) | Monoinquilino por instalación; la autorización la aplica Django |
| Celery / Redis | No hay volumen ni necesidad de trabajos asíncronos; Task Scheduler basta |
| SPA (React/Vue) | Sin web pública en alcance; añade código y build sin beneficio |
| CDN para assets | La app es de escritorio; todo debe funcionar sin depender de red para la UI |
