# Contracts — Catálogo y Préstamos

Esta aplicación es **de escritorio**: un servidor Django embebido en `127.0.0.1` que muestra su UI en una ventana `pywebview`. **No hay API pública ni acceso de red externo.**

Los "contratos" de este directorio son los **endpoints internos** del servidor local que consumen:

- las **plantillas del lado servidor** (formularios HTML `POST` → redirección),
- unos pocos **endpoints JSON** para autocompletar la búsqueda y refrescar contadores.

Sirven como contrato entre las vistas (`src/*/views.py` + `urls.py`) y las plantillas/JS, y como base para los tests de contrato (`tests/contract/`).

- **`operations.md`** — catálogo de endpoints: método, ruta, credencial requerida, entrada, salida, errores.

Convenciones:

- **Auth**: sesión de Django. `central` = solo la cuenta central; `operador` = cualquier subcuenta activa autenticada (la central también puede); `anónimo` = sin sesión (solo alta inicial y login).
- Formularios: `Content-Type: application/x-www-form-urlencoded`; respuesta `302` a la vista de destino con mensajes flash; errores de validación → `200` re-renderizando el formulario con errores de campo.
- JSON: `Content-Type: application/json`; errores → código HTTP + `{ "error": "<mensaje legible>" }`.
- CSRF obligatorio en todas las escrituras (token de Django).
- Toda escritura crea una `EntradaAuditoria` con el operador de la sesión.
