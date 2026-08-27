# Seguridad — Biblioteca Municipal

Repaso de las medidas implementadas y comprobaciones antes de cada despliegue.

## Autenticación y sesión

- Contraseñas con **Argon2** (`argon2-cffi`), validadores de Django (mínimo 8 caracteres).
- **django-axes**: bloqueo tras 5 intentos fallidos por nombre de usuario, enfriamiento 10 min.
- Sesión en base de datos, **cierre por inactividad** (`SESSION_COOKIE_AGE` +
  `SESSION_SAVE_EVERY_REQUEST`, por defecto 30 min), y al cerrar la ventana.
- Cookies `HttpOnly`, `SameSite=Lax`. `Secure=False` porque el tráfico es `127.0.0.1` dentro
  del webview (no sale a la red).

## Autorización

- Toda vista de datos requiere sesión (`login_required` / `LoginRequiredMixin`).
- Acciones reservadas a la **cuenta central** (crear/editar operadores, configuración de
  préstamo, anonimización): `SoloCentralMixin` / comprobación `es_central`, respuesta `403`.

## Datos y trazabilidad

- **Auditoría** append-only (`EntradaAuditoria`) de toda operación que crea o modifica datos,
  con la subcuenta autora y la marca temporal.
- Invariantes garantizadas en base de datos: índice único parcial "un préstamo activo por
  ejemplar", documento único entre personas activas.
- Sin borrado de historial: bajas por estado (`retirado` / `anonimizada` / `anulado`).
- **RGPD/LOPD**: anonimización automática a los 2 años del último préstamo y a petición;
  los datos identificativos se vacían y los préstamos se conservan sin persona.

## Configuración

- `DEBUG=False` cuando `APP_ENTORNO=desktop` (forzado en `settings.py`).
- `ALLOWED_HOSTS = ["127.0.0.1", "localhost"]`.
- `SECRET_KEY` desde `.env`, distinta por instalación; `.env` fuera del control de versiones
  (`.env.example` sí versionado, sin valores reales).
- Conexión a la BD con `sslmode=require` cuando el host es de Supabase.
- Sin PostgREST/GoTrue/RLS: el único punto de acceso a los datos es la aplicación Django.

## Comprobaciones antes de desplegar

```bash
uv run ruff check src tests
uv run python manage.py check
APP_ENTORNO=desktop uv run python manage.py check --deploy   # revisa cabeceras/cookies
uv run pytest
```

- Revisar que no hay credenciales en el repositorio (`git grep -i "password\|secret" -- ':!*.example' ':!docs'`).
- Revisar dependencias: `uv lock --upgrade --dry-run` y changelog de Django/psycopg.

### Sobre los avisos de `check --deploy`

`manage.py check --deploy` avisa de `SECURE_HSTS_SECONDS` (W004), `SECURE_SSL_REDIRECT`
(W008), `SESSION_COOKIE_SECURE` (W012) y `CSRF_COOKIE_SECURE` (W016). **Son esperados y no
aplican**: la aplicación se sirve sobre `http://127.0.0.1` dentro de una ventana WebView2; el
tráfico no sale del equipo. Activar cookies "solo HTTPS" impediría iniciar sesión. `W009` solo
aparece si la `SECRET_KEY` es de ejemplo; en producción se genera una por instalación en `.env`.

