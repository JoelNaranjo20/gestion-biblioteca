# Assets vendorizados (tarea T006)

Coloca aquí las versiones locales (sin CDN) de:

- `htmx.min.js` — HTMX 2.x — https://unpkg.com/htmx.org@2/dist/htmx.min.js
- `bootstrap.min.css` y `bootstrap.bundle.min.js` — Bootstrap 5.3
- `bootstrap-icons.css` + fuentes — Bootstrap Icons (opcional)

`base.html` los carga con `{% static %}` si existen. Mientras no estén, la UI usa
`css/app.css` y funciona con recargas de página completa (sin HTMX).
