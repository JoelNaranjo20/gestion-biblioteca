# Implementation Plan: Catálogo y Préstamos de la Biblioteca Municipal

**Branch**: `001-catalog-loans` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-catalog-loans/spec.md`

## Summary

Aplicación **de escritorio** para el personal de una biblioteca municipal (varios puestos en una única sede) que cubre: catálogo bibliográfico (títulos + ejemplares), búsqueda con disponibilidad, préstamos y devoluciones con fecha límite, consulta de préstamos activos e historial, reclamación de vencidos, corrección/anulación de operaciones, configuración de parámetros de préstamo y anonimización RGPD de prestatarios.

**Enfoque técnico**: proyecto **Django** (Python) servido localmente y presentado en una ventana nativa con **pywebview**, empaquetado para Windows con **PyInstaller**. Persistencia en **PostgreSQL gestionado por Supabase** (en la nube), accedido directamente con el ORM de Django (sin usar PostgREST ni las librerías cliente de Supabase). Autenticación propia de Django: **cuenta central** con correo + contraseña y **subcuentas de operador** con nombre de usuario + contraseña (sin correo); cada operación que crea o modifica datos se atribuye a la subcuenta autenticada. Requiere conexión a Internet (sin modo offline en v1).

## Technical Context

**Stack completo y definitivo**: ver [tech-stack.md](./tech-stack.md) (decisiones confirmadas por el usuario el 2026-08-27). Resumen abajo.

**Language/Version**: Python 3.12+ (objetivo 3.13); gestionado con `uv`.

**Primary Dependencies**: **Django 5.2 LTS** · **psycopg 3.2** · **pywebview 5.x** (ventana de escritorio, WebView2) · **waitress** (servidor WSGI en el paquete) · **PyInstaller 6.x** (empaquetado Windows) · **whitenoise** (estáticos) · **HTMX 2.x** + **Bootstrap 5.3** (UI, vendorizados) · **django-crispy-forms** + **crispy-bootstrap5** · **django-axes** + **argon2-cffi** (auth) · **django-environ** (config) · **pytest/pytest-django/factory_boy** + **ruff** (calidad). Extensiones PostgreSQL: `unaccent`, `pg_trgm`.

**Storage**: PostgreSQL **gestionado por Supabase** (nube), accedido con el **ORM de Django directo** (sin `supabase-py`, PostgREST, Realtime ni GoTrue). El esquema lo poseen y versionan las migraciones de Django. Conexión por el *session pooler* de Supabase (puerto 5432) con `sslmode=require`, `CONN_MAX_AGE=0`. **Sin Row-Level Security** (aplicación monoinquilino por instalación; la autorización la aplica Django).

**Auth**: `django.contrib.auth` para todo — cuenta central con email, subcuentas de operador con `username` sin email; Argon2; bloqueo con django-axes; cierre de sesión por inactividad.

**Testing**: pytest + pytest-django (unitarios de servicios y reglas; integración con base de datos real de pruebas; `TransactionTestCase` para concurrencia; contrato de endpoints; un puñado de extremo a extremo con el cliente de test de Django).

**Target Platform**: Puestos de escritorio Windows 10/11 en la sede de la biblioteca. Necesita conexión a Internet permanente con Supabase.

**Project Type**: Aplicación de escritorio (Django + pywebview empaquetado) con base de datos PostgreSQL en la nube. Estructura de **proyecto único**.

**Performance Goals**: búsqueda en catálogo < 2 s con 20.000 títulos / 50.000 ejemplares (SC-003); el ejemplar devuelto vuelve a "disponible" en la búsqueda en < 2 s (SC-007); registrar un préstamo completo < 1 min (SC-001) y una devolución < 30 s (SC-002). Objetivo interno: consultas indexadas < 300 ms en servidor (excluida latencia de red).

**Constraints**: solo en línea (BD en la nube); residencia de datos en Supabase; lectores de código de barras tratados como entrada de teclado (sin integración); una única sede; decenas de miles de registros de catálogo, cientos de préstamos activos, unas pocas subcuentas de operador y 1–4 puestos concurrentes; RGPD/LOPD (anonimización a los 2 años o a petición); cero descuadres entre estado del ejemplar y préstamos abiertos (SC-004).

**Scale/Scope**: ~20.000–50.000 registros de catálogo; cientos de préstamos activos; ~5–10 subcuentas de operador; ~18–22 pantallas/vistas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` es todavía la plantilla sin rellenar: **no hay principios ratificados ni puertas que exigir**. No se detectan violaciones. La sección Complexity Tracking queda vacía.

**Recomendación**: ejecutar `/speckit-constitution` para fijar principios (p. ej. simplicidad/YAGNI, pruebas antes de implementar, trazabilidad de datos) antes de `/speckit-implement`. No bloquea este plan.

**Evaluación tras Phase 1**: sin cambios — el diseño usa un único proyecto, sin patrones añadidos no justificados (acceso a datos por el ORM, servicios de dominio como funciones/módulos, sin capa de repositorio artificial).

## Project Structure

### Documentation (this feature)

```text
specs/001-catalog-loans/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0 (/speckit-plan)
├── data-model.md        # Fase 1 (/speckit-plan)
├── quickstart.md        # Fase 1 (/speckit-plan)
├── contracts/           # Fase 1 (/speckit-plan)
│   ├── README.md
│   └── operations.md
├── tech-stack.md        # Stack tecnológico definitivo (confirmado 2026-08-27)
├── checklists/
│   └── requirements.md  # Checklist de calidad del spec (/speckit-specify + /speckit-clarify)
└── tasks.md             # Fase 2 (/speckit-tasks — NO lo crea /speckit-plan)
```

### Source Code (repository root)

```text
manage.py
pyproject.toml                     # dependencias y config de herramientas
.env.example                       # DATABASE_URL de Supabase, SECRET_KEY, timeouts…

src/
├── gestion_biblioteca/            # Proyecto Django: settings, urls raíz, wsgi/asgi
├── cuentas/                       # Biblioteca (cuenta central), Operador (subcuenta),
│                                  #   autenticación, permisos, EntradaAuditoria, señales
├── catalogo/                      # Titulo, Ejemplar; alta/edición; retirada/reactivación;
│                                  #   búsqueda de títulos y localización por código
├── prestamos/                     # Prestamo; registrar préstamo y devolución;
│                                  #   lista de activos y de vencidos; historial;
│                                  #   GestionReclamacion; CorreccionOperacion (anular/corregir)
├── configuracion/                 # ParametrosPrestamo (plazo, máximo por persona)
├── privacidad/                    # Servicio y management command de anonimización;
│                                  #   anonimización manual a petición
└── common/                        # Modelo base con timestamps, mixins de auditoría,
                                   #   utilidades (normalización de texto, cálculo de fechas)

desktop/
├── launcher.py                    # Arranca el servidor Django embebido en localhost y
│                                  #   abre la ventana pywebview
└── build.spec                     # Configuración de PyInstaller para Windows

tests/
├── unit/                          # Reglas de dominio: fecha límite, retraso, tope por
│                                  #   persona, transiciones de estado, anonimización
├── integration/                   # Flujos con BD: préstamo/devolución, corrección,
│                                  #   concurrencia (bloqueo + índice único parcial), auditoría
└── contract/                      # Esquemas de endpoints de src/*/urls.py vs contracts/
```

**Structure Decision**: Proyecto Django único con apps por área de dominio (`cuentas`, `catalogo`, `prestamos`, `configuracion`, `privacidad`, `common`). La capa de escritorio (`desktop/`) es una fina envoltura que lanza el servidor local y la ventana; no contiene lógica de negocio. Las reglas de negocio viven en módulos de servicio dentro de cada app (funciones puras + funciones transaccionales), invocadas desde vistas Django que renderizan plantillas del lado servidor y unos pocos endpoints JSON (autocompletar búsqueda).

## Complexity Tracking

> Sin violaciones de la constitución que justificar (no hay constitución ratificada). Tabla vacía.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Phase 0 — Research

Consolidado en [research.md](./research.md). Temas resueltos:

1. Entrega como aplicación de escritorio de un proyecto Django en Windows (pywebview + PyInstaller vs navegador del sistema vs Electron/Tauri).
2. Conexión de Django a PostgreSQL de Supabase: modo de pooler, SSL, propiedad de las migraciones, habilitación de extensiones.
3. Autenticación: cuenta central (correo) + subcuentas de operador sin correo con el sistema de auth de Django; aplicación de permisos "solo central"; cierre de sesión por inactividad.
4. Búsqueda parcial insensible a mayúsculas y acentos en PostgreSQL (`unaccent` + `pg_trgm` + índice GIN).
5. Trabajo programado de anonimización en un despliegue de escritorio (management command + Programador de tareas de Windows; botón "ejecutar ahora" para la cuenta central).
6. Seguridad ante concurrencia en préstamo/devolución (`SELECT … FOR UPDATE` + índice único parcial de "préstamo activo por ejemplar").
7. Gestión de la falta de conexión y UX de error (solo en línea en v1).

**Ninguna cuestión pendiente bloquea el diseño.** Valores por defecto adoptados y anotados en research.md (p. ej. cierre de sesión tras 30 min de inactividad; paginación de resultados a 25).

## Phase 1 — Design & Contracts

- **Modelo de datos**: [data-model.md](./data-model.md) — entidades, campos, relaciones, restricciones, índices, máquinas de estado (Ejemplar, Préstamo, Persona prestataria, Subcuenta), reglas de validación trazadas a FR-xxx, y comportamiento de retención/anonimización y auditoría.
- **Contratos**: [contracts/](./contracts/) — endpoints internos del servidor local que consumen las plantillas y el autocompletar de búsqueda (método, ruta, campos, respuestas, errores, credencial requerida: central u operador). No hay API pública.
- **Guía de validación**: [quickstart.md](./quickstart.md) — alta de proyecto Supabase, variables de entorno, migraciones, creación de la cuenta central y de una subcuenta, arranque de la app de escritorio, y escenarios de validación extremo a extremo mapeados a las historias de usuario y a SC-001…SC-014.

**Re-evaluación de la constitución tras el diseño**: sin gates; sin cambios.

## Next

`/speckit-tasks` para generar `tasks.md` (desglose ejecutable y ordenado por dependencias). Antes de `/speckit-implement`, conviene ejecutar `/speckit-constitution`.
