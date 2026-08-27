---

description: "Task list — Catálogo y Préstamos de la Biblioteca Municipal"
---

# Tasks: Catálogo y Préstamos de la Biblioteca Municipal

**Input**: Design documents from `specs/001-catalog-loans/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [tech-stack.md](./tech-stack.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/operations.md](./contracts/operations.md), [quickstart.md](./quickstart.md)

**Tests**: INCLUIDOS. El feature define pruebas explícitamente (Independent Test por historia, escenarios E1–E11 del quickstart, y stack de pruebas en tech-stack.md §11): contrato, integración, concurrencia y unitarias de reglas.

**Organization**: tareas agrupadas por historia de usuario para implementar y validar cada una de forma independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario a la que pertenece (US1…US6)
- Rutas relativas a la raíz del repo. Estructura de proyecto único: `src/<app>/`, `tests/`, `desktop/`

---

## Phase 1: Setup (infraestructura compartida)

**Purpose**: inicialización del proyecto y estructura base

- [ ] T001 Crear la estructura del repo según plan.md: `manage.py`, `pyproject.toml`, `src/` con apps `common cuentas catalogo prestamos configuracion privacidad`, `desktop/`, `tests/{unit,integration,contract}/`
- [ ] T002 Inicializar el proyecto Python con `uv`; declarar en `pyproject.toml` las dependencias de ejecución (django~=5.2, psycopg[binary]~=3.2, django-environ, whitenoise, waitress, pywebview, django-crispy-forms, crispy-bootstrap5, django-axes, argon2-cffi) y generar `uv.lock`
- [ ] T003 [P] Configurar **ruff** (lint + formato) en `pyproject.toml` y `.pre-commit-config.yaml` con hooks: ruff, ruff-format, `manage.py check`, `makemigrations --check`
- [ ] T004 [P] Configurar **pytest** en `pyproject.toml`/`pytest.ini`: pytest-django, pytest-cov, factory_boy, Faker; `DJANGO_SETTINGS_MODULE` de test y `--reuse-db`
- [ ] T005 [P] Crear `.env.example` (DATABASE_URL, SECRET_KEY, DJANGO_DEBUG, APP_ENTORNO, SESSION_INACTIVIDAD_SEGUNDOS=1800, RETENCION_PRESTATARIOS_DIAS=730) y `src/gestion_biblioteca/settings.py` gobernado por `APP_ENTORNO` (dev/desktop/test) con `LANGUAGE_CODE='es'`, `TIME_ZONE='Europe/Madrid'`, `USE_TZ=True`
- [ ] T006 [P] Vendorizar HTMX 2.x, Bootstrap 5.3 (CSS/JS) y Bootstrap Icons en `src/common/static/vendor/`; configurar whitenoise + `ManifestStaticFilesStorage` en settings
- [ ] T007 Crear el proyecto Django `gestion_biblioteca` y registrar las 6 apps vacías en `INSTALLED_APPS`

---

## Phase 2: Foundational (prerrequisitos bloqueantes)

**Purpose**: infraestructura que DEBE existir antes de cualquier historia de usuario

**⚠️ CRITICAL**: ninguna historia puede empezar hasta terminar esta fase

- [ ] T008 Configurar la conexión a **Supabase (session pooler)** en settings: `DATABASE_URL` con `sslmode=require`, puerto 5432, `CONN_MAX_AGE=0`, driver psycopg 3; documentar en `.env.example`
- [ ] T009 Crear la app `common`: modelo abstracto `ModeloBase` (id, `creado_en`, `actualizado_en`) en `src/common/models.py`
- [ ] T010 [P] Migración inicial que habilita las extensiones PostgreSQL `unaccent` y `pg_trgm` (`CreateExtension`) y crea el wrapper SQL `immutable_unaccent` (IMMUTABLE) en `src/common/migrations/0001_extensiones.py`
- [ ] T011 [P] Utilidades en `src/common/utils.py`: `normalizar_texto()` (lower + unaccent) y `sumar_dias_naturales(fecha, dias)`; tests en `tests/unit/test_utils.py`
- [ ] T012 [P] Middleware de error de conexión (`OperationalError`/`InterfaceError` → página "sin conexión con la base de datos") en `src/common/middleware.py` + plantilla `src/common/templates/common/sin_conexion.html`
- [ ] T013 [P] Configurar logging a fichero rotativo (`%LOCALAPPDATA%/BibliotecaMunicipal/logs/`) + consola en dev, en `src/gestion_biblioteca/settings.py`
- [ ] T014 Crear `Biblioteca` (nombre, contacto, `creada_por_email`) en `src/cuentas/models.py` + migración
- [ ] T015 Crear `Operador` (OneToOne `auth.User`, FK `biblioteca`, `es_central`, `nombre_visible`) en `src/cuentas/models.py` + migración
- [ ] T016 Configurar auth en settings: `PASSWORD_HASHERS` con Argon2, validadores (mínimo 8), sesiones en BD con cierre por inactividad (`SESSION_COOKIE_AGE`, `SESSION_SAVE_EVERY_REQUEST=True`), cookies (`SECURE=False` localhost, `SAMESITE='Lax'`, `HTTPONLY=True`), e integrar **django-axes** (bloqueo 5 intentos / 10 min)
- [ ] T017 [P] `SoloCentralMixin` + permiso `cuentas.gestion` en `src/cuentas/permissions.py`
- [ ] T018 Crear `EntradaAuditoria` (biblioteca, `tipo_operacion`, entidad, `entidad_id`, actor→User, `fecha_hora`, `detalle` jsonb) en `src/cuentas/models.py` + migración
- [ ] T019 Servicio de auditoría `registrar_auditoria(actor, tipo, entidad, entidad_id, detalle=None)` y mixin/decorador `ConAuditoria` para vistas de escritura en `src/cuentas/services.py` (append-only)
- [ ] T020 Vistas y plantillas de acceso: `/inicio/alta-biblioteca/` (solo si no hay `Biblioteca`), `/acceso/entrar/`, `/acceso/salir/`, más flujo "cambiar de operador" y aviso de cierre por inactividad, en `src/cuentas/views.py` + `src/cuentas/urls.py` + `src/cuentas/templates/cuentas/`
- [ ] T021 [P] Management commands `crear_biblioteca` y `crear_operador` en `src/cuentas/management/commands/`
- [ ] T022 Crear `ParametrosPrestamo` (OneToOne `biblioteca`, `plazo_dias=15`, `max_prestamos_persona=3`) en `src/configuracion/models.py` + migración + helper `get_parametros()` (get-or-create)
- [ ] T023 Plantilla base `src/common/templates/common/base.html` (Bootstrap + HTMX, barra con operador actual y "salir", zona de mensajes, indicador de estado de conexión) y `urls.py` raíz con endpoint de *ping* de conexión en `src/gestion_biblioteca/urls.py`
- [ ] T024 `desktop/launcher.py` (waitress en `127.0.0.1:<puerto libre>` en un hilo + ventana `pywebview`; ejecuta `migrate` si el esquema está desactualizado) y `desktop/build.spec` (PyInstaller *one-dir*)

**Checkpoint**: base lista — las historias de usuario pueden empezar

---

## Phase 3: User Story 1 — Mantener el catálogo bibliográfico (Priority: P1) 🎯 MVP

**Goal**: el personal da de alta y edita títulos y ejemplares, retira/reactiva ejemplares y ve recuentos correctos.

**Independent Test**: crear títulos con ejemplares, editarlos, retirar un ejemplar con motivo y comprobar los recuentos; rechazo al faltar título/autor (US1.4) y al repetir código de ejemplar (US1.5).

### Tests for User Story 1

- [ ] T025 [P] [US1] Tests de contrato de `/catalogo/titulos/*` y `/catalogo/ejemplares/*` en `tests/contract/test_catalogo.py`
- [ ] T026 [P] [US1] Test de integración del ciclo de catálogo (alta título+ejemplar, edición, retirada, recuentos) en `tests/integration/test_us1_catalogo.py`

### Implementation for User Story 1

- [ ] T027 [P] [US1] Modelo `Titulo` (título*, autor*, isbn, editorial, anio, materia; columna generada `busqueda_norm` con `immutable_unaccent`; índice GIN `gin_trgm_ops`; índice btree en `isbn`) en `src/catalogo/models.py` + migración
- [ ] T028 [P] [US1] Modelo `Ejemplar` (`codigo` único, `estado` enum disponible/prestado/retirado, `motivo_retirada`, `ubicacion` opcional; índice `(titulo, estado)`) en `src/catalogo/models.py` + migración
- [ ] T029 [P] [US1] Factories de `Titulo` y `Ejemplar` en `tests/factories.py`
- [ ] T030 [US1] Servicios de catálogo en `src/catalogo/services.py`: `crear_titulo`/`editar_titulo` (validan título+autor; avisan de ISBN duplicado y continúan tras confirmación), `crear_ejemplar` (rechaza código duplicado), `retirar_ejemplar` (bloquea si `prestado`), anotación de recuento total/disponibles
- [ ] T031 [US1] Guard de borrado: impedir eliminar `Titulo`/`Ejemplar` con préstamos registrados (FR-007) en `src/catalogo/services.py`
- [ ] T032 [US1] Vistas de título (`nuevo`, `editar`, `detalle` con lista de ejemplares y totales/disponibles) y de ejemplar (`añadir`, `retirar` con motivo) en `src/catalogo/views.py` + `src/catalogo/urls.py`
- [ ] T033 [P] [US1] Plantillas: formulario de título, detalle de título con ejemplares, modal de retirada (Bootstrap/crispy) en `src/catalogo/templates/catalogo/`
- [ ] T034 [US1] Registrar auditoría de escrituras de catálogo (`alta_titulo`, `edicion_titulo`, `alta_ejemplar`, `retirada_ejemplar`) vía `ConAuditoria`

**Checkpoint**: US1 funcional y testeable de forma independiente

---

## Phase 4: User Story 2 — Prestar y devolver ejemplares (Priority: P1)

**Goal**: registrar préstamos y devoluciones con fecha límite, cambios de estado, marca de retraso, tope por persona y anulación/corrección de operaciones.

**Independent Test**: con un ejemplar disponible, registrar préstamo (estado `prestado`, `fecha_limite = hoy + plazo`), rechazar segundo préstamo, devolver (estado `disponible`, retraso si procede), rechazar devolución sin préstamo activo, alcanzar el tope → bloqueo; anular un préstamo y ver el ejemplar disponible y el registro anulado en el historial.

### Tests for User Story 2

- [ ] T035 [P] [US2] Tests de contrato de `/prestamos/nuevo`, `/prestamos/devolver`, `/prestamos/<id>/anular`, `/prestamos/<id>/anular-devolucion`, `/prestamos/<id>/corregir-ejemplar`, `/catalogo/ejemplares/<id>/anular-retirada` en `tests/contract/test_prestamos.py`
- [ ] T036 [P] [US2] Tests de integración: préstamo→devolución, devolución con retraso, bloqueo por tope, anular préstamo/devolución/retirada, corrección de ejemplar equivocado en `tests/integration/test_us2_prestamos.py`
- [ ] T037 [P] [US2] Test de concurrencia (`TransactionTestCase`): dos préstamos simultáneos del mismo ejemplar → exactamente uno tiene éxito, sin dos préstamos activos, en `tests/integration/test_us2_concurrencia.py`

### Implementation for User Story 2

- [ ] T038 [P] [US2] Modelo `PersonaPrestataria` (documento, nombre, contacto, `estado` activa/anonimizada, `fecha_alta`, `fecha_ultimo_prestamo`; índice único parcial `(biblioteca, documento) WHERE estado='activa'`) en `src/prestamos/models.py` + migración
- [ ] T039 [P] [US2] Modelo `Prestamo` (FKs ejemplar/persona nullable, `persona_anonimizada`, fechas, `dias_retraso`, `estado_registro` efectivo/anulado, `registrado_por`/`devolucion_registrada_por`; **índice único parcial** `(ejemplar) WHERE estado_registro='efectivo' AND fecha_devolucion_real IS NULL`; índices para historial y lista de vencidos) en `src/prestamos/models.py` + migración
- [ ] T040 [P] [US2] Modelo `CorreccionOperacion` (tipo, operación, FK prestamo/ejemplar, motivo*, `realizada_por`, `fecha_hora`) en `src/prestamos/models.py` + migración
- [ ] T041 [P] [US2] Reglas de dominio puras en `src/prestamos/rules.py`: `calcular_fecha_limite`, `calcular_dias_retraso`, `cuenta_prestamos_activos`, `valida_tope`; tests en `tests/unit/test_reglas_prestamo.py`
- [ ] T042 [US2] Servicio `registrar_prestamo` en `src/prestamos/services.py`: `select_for_update` sobre `Ejemplar`, verificación `disponible` + tope, get-or-create de `PersonaPrestataria` por documento, aviso de nombre distinto (FR-022), aviso no bloqueante de vencidos (FR-021)
- [ ] T043 [US2] Servicio `registrar_devolucion` en `src/prestamos/services.py`: localizar préstamo activo por código o id, fijar `fecha_devolucion_real`, calcular `dias_retraso`, ejemplar → `disponible`
- [ ] T044 [US2] Servicios de corrección en `src/prestamos/services.py`: `anular_prestamo`, `anular_devolucion`, `corregir_ejemplar`, `anular_retirada` (motivo obligatorio; recálculo de estado del ejemplar, datos derivados y recuento por persona; FR-040)
- [ ] T045 [US2] Vistas de préstamo y devolución (`/prestamos/nuevo`, `/prestamos/devolver`) con selección por código o desde la búsqueda y flujos de confirmación (nombre distinto / avisos) en `src/prestamos/views.py` + `src/prestamos/urls.py`
- [ ] T046 [US2] Vistas de corrección (`anular`, `anular-devolucion`, `corregir-ejemplar`, `anular-retirada`) con motivo obligatorio en `src/prestamos/views.py` + `src/prestamos/urls.py`
- [ ] T047 [P] [US2] Plantillas: formulario de préstamo (lectura de código + datos de persona + avisos), formulario de devolución, modales de corrección en `src/prestamos/templates/prestamos/`
- [ ] T048 [US2] Registrar auditoría de `prestamo`, `devolucion` y `correccion` vía `ConAuditoria`

**Checkpoint**: US2 funcional — **MVP = Setup + Foundational + US1 + US2** (con acceso sembrado por management command)

---

## Phase 5: User Story 6 — Alta de la biblioteca y gestión de operadores (Priority: P1)

**Goal**: la cuenta central registra la biblioteca y gestiona subcuentas de operador; toda operación queda atribuida y es consultable.

**Independent Test**: crear la cuenta central, añadir una subcuenta de operador (sin correo, < 1 min), iniciar sesión con ella, realizar una operación y verla atribuida en el historial y en la auditoría; desactivar la subcuenta → no puede iniciar sesión pero sus operaciones anteriores siguen atribuidas; un operador no puede tocar configuración ni subcuentas.

### Tests for User Story 6

- [ ] T049 [P] [US6] Tests de contrato de `/inicio/alta-biblioteca/`, `/acceso/entrar/`, `/operadores/*` en `tests/contract/test_cuentas.py`
- [ ] T050 [P] [US6] Test de integración: alta biblioteca → crear operador → login operador → atribución en `EntradaAuditoria`; desactivar → login falla; operador → 403 en configuración, en `tests/integration/test_us6_cuentas.py`

### Implementation for User Story 6

- [ ] T051 [US6] Vistas de gestión de operadores (listar, crear con validación de nombre de usuario único, desactivar/reactivar, restablecer contraseña) protegidas por `SoloCentralMixin` en `src/cuentas/views.py` + `src/cuentas/urls.py`
- [ ] T052 [P] [US6] Plantillas de gestión de operadores (lista + formulario, validación de nombre de usuario en línea con HTMX) en `src/cuentas/templates/cuentas/`
- [ ] T053 [P] [US6] Vista de auditoría `/auditoria/` con filtros `entidad`/`entidad_id` y paginación 25 + plantilla en `src/cuentas/`
- [ ] T054 [US6] Reglas de visibilidad de navegación y aplicación de "solo central" (403 amable) en configuración y operadores; enlazar auditoría `alta_operador`/`baja_operador`

**Checkpoint**: US6 funcional; auditoría y atribución completas de extremo a extremo

---

## Phase 6: User Story 3 — Buscar en el catálogo y comprobar disponibilidad (Priority: P2)

**Goal**: buscar títulos por título/autor/ISBN/materia (insensible a mayúsculas y acentos, parcial), ver totales y disponibles, y localizar un ejemplar por su código.

**Independent Test**: con catálogo variado, buscar por cada criterio y verificar recuentos; localización por código; mensaje de "sin resultados".

### Tests for User Story 3

- [ ] T055 [P] [US3] Tests de contrato de `/catalogo/buscar/`, `/catalogo/buscar.json`, `/catalogo/ejemplar-por-codigo.json` en `tests/contract/test_busqueda.py`
- [ ] T056 [P] [US3] Test de integración: búsqueda parcial insensible a acentos/mayúsculas + recuentos con ejemplares en 3 estados en `tests/integration/test_us3_busqueda.py`

### Implementation for User Story 3

- [ ] T057 [US3] Servicio de búsqueda en `src/catalogo/services.py`: trigram/`unaccent` sobre `busqueda_norm`, ISBN exacto normalizado (sin guiones), paginación 25, anotaciones de total/disponibles
- [ ] T058 [US3] Vistas `/catalogo/buscar/` (HTML paginado), `/catalogo/buscar.json` (autocompletar ≤ 10) y `/catalogo/ejemplar-por-codigo.json` (404 si no existe) en `src/catalogo/views.py` + `src/catalogo/urls.py`
- [ ] T059 [P] [US3] Plantillas + HTMX: formulario de búsqueda, parcial de resultados con auto-refresco al teclear, mensaje "sin resultados" en `src/catalogo/templates/catalogo/`
- [ ] T060 [P] [US3] Vista y plantilla `/catalogo/ejemplares/<id>/historial/` (incluye operaciones anuladas) en `src/catalogo/`

**Checkpoint**: US1, US2, US3 y US6 funcionan de forma independiente

---

## Phase 7: User Story 4 — Consultar préstamos activos, historial y reclamación (Priority: P2)

**Goal**: lista de préstamos activos (vencidos destacados con estado de reclamación), historial por ejemplar y por persona, y registro de gestiones de reclamación.

**Independent Test**: tras varios préstamos y devoluciones, la lista de activos solo muestra los no devueltos; los vencidos aparecen destacados con días de retraso; historial por ejemplar y por documento; registrar una gestión de reclamación y verla reflejada en la lista de vencidos.

### Tests for User Story 4

- [ ] T061 [P] [US4] Tests de contrato de `/prestamos/activos`, `/prestamos/vencidos`, `/prestamos/<id>/`, `/prestamos/<id>/reclamaciones/nueva`, `/personas/historial` en `tests/contract/test_consultas.py`
- [ ] T062 [P] [US4] Test de integración: listas de activos/vencidos, historial por ejemplar y por persona, visibilidad de la última gestión, rechazo de gestión sobre préstamo cerrado, en `tests/integration/test_us4_consultas.py`

### Implementation for User Story 4

- [ ] T063 [P] [US4] Modelo `GestionReclamacion` (FK prestamo, fecha, `medio` enum, notas, `registrada_por`) en `src/prestamos/models.py` + migración
- [ ] T064 [US4] Servicios de consulta en `src/prestamos/services.py`: `prestamos_activos` (con retraso calculado y última gestión), `prestamos_vencidos`, `historial_ejemplar`, `historial_persona` (vacío si la persona está anonimizada)
- [ ] T065 [US4] Servicio de reclamación en `src/prestamos/services.py`: solo préstamo activo y vencido; aviso si la persona no tiene contacto; bloqueo si el préstamo está cerrado
- [ ] T066 [US4] Vistas `/prestamos/activos`, `/prestamos/vencidos`, `/prestamos/<id>/` (detalle con gestiones y correcciones), `/prestamos/<id>/reclamaciones/nueva`, `/personas/historial` en `src/prestamos/views.py` + `src/prestamos/urls.py`
- [ ] T067 [P] [US4] Plantillas: listas de activos/vencidos (destacado de vencidos + última gestión), detalle de préstamo, formulario de reclamación (HTMX), historial de persona en `src/prestamos/templates/prestamos/`
- [ ] T068 [US4] Registrar auditoría de `reclamacion` vía `ConAuditoria`

**Checkpoint**: todas las historias P1 y P2 funcionan de forma independiente

---

## Phase 8: User Story 5 — Configurar parámetros de préstamo (Priority: P3)

**Goal**: la cuenta central consulta y modifica `plazo_dias` y `max_prestamos_persona`; los cambios solo afectan a préstamos nuevos.

**Independent Test**: cambiar el plazo → un préstamo nuevo lo usa y los anteriores no cambian; cambiar el tope → la validación usa el nuevo valor; rechazar valores < 1.

### Tests for User Story 5

- [ ] T069 [P] [US5] Test de contrato de `/configuracion/prestamos/` (GET/POST; 403 para operador) en `tests/contract/test_configuracion.py`
- [ ] T070 [P] [US5] Test de integración: el cambio de plazo solo afecta a préstamos nuevos; el cambio de tope afecta a la validación; valores inválidos rechazados, en `tests/integration/test_us5_configuracion.py`

### Implementation for User Story 5

- [ ] T071 [US5] Formulario y servicio de configuración (validación mínimo 1) y vista `/configuracion/prestamos/` protegida por `SoloCentralMixin` en `src/configuracion/views.py` + `src/configuracion/urls.py`
- [ ] T072 [P] [US5] Plantilla del formulario de configuración en `src/configuracion/templates/configuracion/`
- [ ] T073 [US5] Verificar que `registrar_prestamo`/`valida_tope` leen siempre `ParametrosPrestamo` vigente; registrar auditoría `cambio_configuracion`

**Checkpoint**: todas las historias de usuario completas

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: privacidad/retención (RGPD), rendimiento, empaquetado, seguridad y validación final. Sin etiqueta de historia.

### Privacidad y retención (RGPD/LOPD — FR-034…FR-037)

- [ ] T074 [P] Servicios de anonimización en `src/privacidad/services.py`: `anonimizar_persona(persona)` y `anonimizar_vencidas()` (desligar `Prestamo.persona`, vaciar documento/nombre/contacto, `estado='anonimizada'`, bloquear si hay préstamos activos)
- [ ] T075 Management command `anonimizar_prestatarios` (idempotente; escribe `EntradaAuditoria` `anonimizacion_automatica`) en `src/privacidad/management/commands/anonimizar_prestatarios.py`
- [ ] T076 [P] Vistas `/privacidad/` (estado: anonimizables hoy, última/próxima ejecución), `/privacidad/ejecutar-ahora/` y `/personas/<id>/anonimizar/` (SoloCentralMixin; 409 si hay préstamos activos) + plantillas en `src/privacidad/`
- [ ] T077 [P] Test de integración de anonimización (ventana de 2 años, bloqueo FR-036, conservación del historial FR-037, historial de persona vacío tras anonimizar) en `tests/integration/test_privacidad.py`

### Rendimiento, empaquetado y seguridad

- [ ] T078 [P] Tests unitarios de reglas de dominio (fecha límite, días de retraso, tope, normalización de texto, ventana de retención) en `tests/unit/`
- [ ] T079 Management command `sembrar_datos_demo` (20.000 títulos / 50.000 ejemplares) en `src/catalogo/management/commands/` y verificación de que la búsqueda responde < 2 s (SC-003) y la disponibilidad se refleja < 2 s (SC-007); revisar `select_related`/`prefetch_related` y los índices
- [ ] T080 [P] Finalizar el empaquetado de escritorio: comprobación del runtime WebView2 con mensaje amable, `migrate` en el primer arranque, icono de la app; documentar la opción MSI en `docs/`
- [ ] T081 [P] Repaso de seguridad: `ALLOWED_HOSTS`, `DEBUG=False` en `desktop`, configuración de django-axes, gestión de `SECRET_KEY`, `.env.example` completo
- [ ] T082 [P] Documentación en `docs/` y `README.md` raíz: instalación, alta del proyecto Supabase, Programador de tareas de Windows para la anonimización, verificación mensual de copias de seguridad
- [ ] T083 Ejecutar los escenarios E1–E11 de [quickstart.md](./quickstart.md) y corregir desviaciones

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias — empieza de inmediato
- **Foundational (Phase 2)**: depende de Setup — **BLOQUEA todas las historias**
- **User Stories (Phases 3–8)**: todas dependen de Foundational
  - Orden recomendado por prioridad: US1 → US2 → US6 (P1) → US3 → US4 (P2) → US5 (P3)
  - Con equipo, US1/US2/US6 pueden ir en paralelo tras Foundational; US3/US4 dependen de que existan `Titulo`/`Ejemplar`/`Prestamo` (creados en US1/US2)
- **Polish (Phase 9)**: depende de US2 y US4 (usa `PersonaPrestataria`, `Prestamo`, historial)

### User Story Dependencies

- **US1 (P1)**: solo Foundational. Sin dependencias de otras historias.
- **US2 (P1)**: solo Foundational. Usa `Ejemplar` de US1 en pruebas de extremo a extremo, pero sus modelos y servicios son propios; testeable con un ejemplar de fixture.
- **US6 (P1)**: solo Foundational (auth ya está ahí). Añade la UI de gestión y la vista de auditoría.
- **US3 (P2)**: Foundational + modelos de US1 (`Titulo`/`Ejemplar`). Independiente de US2/US4.
- **US4 (P2)**: Foundational + `Prestamo` de US2. Añade `GestionReclamacion`.
- **US5 (P3)**: Foundational + `ParametrosPrestamo` (Foundational). Independiente.

### Within Each User Story

- Los tests se escriben primero y deben FALLAR antes de implementar.
- Modelos → servicios → vistas/endpoints → integración → auditoría.
- Completar la historia antes de pasar a la siguiente prioridad.

### Parallel Opportunities

- Setup: T003, T004, T005, T006 en paralelo.
- Foundational: T010, T011, T012, T013 en paralelo; T017, T021 en paralelo.
- Modelos dentro de una historia marcados [P] (p. ej. T027/T028, T038/T039/T040) en paralelo.
- Tests marcados [P] de una misma historia en paralelo.
- Con equipo: US1, US2 y US6 en paralelo tras Foundational.

---

## Parallel Example: User Story 2

```bash
# Tests de US2 juntos:
Task: "Tests de contrato en tests/contract/test_prestamos.py"
Task: "Tests de integración en tests/integration/test_us2_prestamos.py"
Task: "Test de concurrencia en tests/integration/test_us2_concurrencia.py"

# Modelos de US2 juntos:
Task: "PersonaPrestataria en src/prestamos/models.py"
Task: "Prestamo en src/prestamos/models.py"
Task: "CorreccionOperacion en src/prestamos/models.py"
Task: "Reglas de dominio en src/prestamos/rules.py"
```

---

## Implementation Strategy

### MVP (mínimo desplegable)

1. Phase 1 (Setup) → Phase 2 (Foundational).
2. Phase 3 (US1) + Phase 4 (US2). Acceso sembrado con `crear_biblioteca` / `crear_operador`.
3. **PARAR Y VALIDAR**: préstamo y devolución completos con catálogo real (Independent Test de US1 y US2; escenarios E2, E4, E5, E6).
4. Demostrar en un puesto real con la BD de Supabase.

### Entrega incremental

1. Setup + Foundational → base lista.
2. + US1 + US2 → MVP (catálogo + circulación).
3. + US6 → gestión de operadores y auditoría completas (E1).
4. + US3 → búsqueda ágil en mostrador (E3).
5. + US4 → seguimiento de activos, vencidos y reclamación (E7, E8).
6. + US5 → parámetros configurables (E5).
7. + Phase 9 → anonimización RGPD (E9), rendimiento (E3.4, E10), empaquetado y validación E1–E11.

### Equipo en paralelo

Tras Foundational: Dev A → US1; Dev B → US2; Dev C → US6. Luego US3/US4/US5 según disponibilidad. Phase 9 al final entre todos.

---

## Notes

- `[P]` = archivos distintos, sin dependencias pendientes.
- La etiqueta `[Story]` mapea la tarea a su historia para trazabilidad.
- Verificar que los tests fallan antes de implementar.
- Commit tras cada tarea o grupo lógico.
- Parar en cualquier checkpoint para validar la historia de forma independiente.
- Antes de `/speckit-implement` conviene ejecutar `/speckit-constitution` (el plan lo recomienda).
