# Biblioteca Municipal — Catálogo y Préstamos

Aplicación **de escritorio** (Django + pywebview) para el personal de la biblioteca municipal:
catálogo bibliográfico, préstamos y devoluciones, búsqueda con disponibilidad, consulta de
activos e historial, reclamación de vencidos, corrección de operaciones, configuración y
anonimización RGPD de prestatarios.

- Especificación y diseño: [`specs/001-catalog-loans/`](specs/001-catalog-loans/)
  (`spec.md`, `plan.md`, `tech-stack.md`, `data-model.md`, `contracts/`, `quickstart.md`,
  `tasks.md`).
- Principios del proyecto: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).
- Despliegue y operación: [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) ·
  Seguridad: [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md).

## Stack

Python 3.12+ · Django 5.2 LTS · PostgreSQL gestionado por Supabase (vía ORM de Django) ·
pywebview + PyInstaller · HTMX + Bootstrap 5 · `django.contrib.auth` · django-axes · Argon2.
Detalle en `specs/001-catalog-loans/tech-stack.md`.

## Puesta en marcha (desarrollo)

```bash
uv sync
cp .env.example .env          # ajusta DATABASE_URL (Postgres local o proyecto Supabase de dev)
python manage.py makemigrations   # reconcilia las migraciones con los modelos
python manage.py migrate
python manage.py crear_biblioteca --nombre "Biblioteca Municipal" --email admin@ejemplo.org
python manage.py crear_operador --username mostrador1
python manage.py runserver          # o: python desktop/launcher.py  (ventana de escritorio)
```

Pruebas (requieren PostgreSQL; los tests usan features de PostgreSQL):

```bash
createdb biblioteca_test
pytest
```

## Empaquetado para Windows

```bash
pyinstaller desktop/build.spec     # -> dist/BibliotecaMunicipal/
```

## Anonimización RGPD (producción)

Programar a diario en el Programador de tareas de Windows:

```
manage.exe anonimizar_prestatarios
```

## Estado de la implementación

**83/83 tareas** completadas (ver [`specs/001-catalog-loans/tasks.md`](specs/001-catalog-loans/tasks.md)).

- ✅ Setup + Foundational, US1 (catálogo), US2 (préstamos/devoluciones/correcciones),
  US3 (búsqueda), US4 (activos/vencidos/historial/reclamación), US5 (configuración),
  US6 (cuentas y operadores), anonimización RGPD (servicio + comando + panel).
- ✅ HTMX 2 y Bootstrap 5.3 vendorizados (sin CDN).
- ✅ **80 pruebas en verde** (unitarias + integración + concurrencia + contrato) contra
  PostgreSQL 16; `ruff` limpio; `manage.py check` sin incidencias; migraciones aplican.
- ✅ `sembrar_datos_demo`: 20.000 títulos / 40.000 ejemplares en ~3 s; búsqueda < 40 ms
  (holgado frente a los 2 s de SC-003).
- ✅ Empaquetado: comprobación de WebView2 y soporte de icono en el lanzador.
- ✅ Docs de despliegue y seguridad (`docs/`).
