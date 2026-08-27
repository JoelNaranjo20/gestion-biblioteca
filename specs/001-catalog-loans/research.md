# Phase 0 — Research: Catálogo y Préstamos de la Biblioteca Municipal

**Feature**: `001-catalog-loans` · **Date**: 2026-08-27 · Input: [plan.md](./plan.md), [spec.md](./spec.md)

Formato por tema: **Decisión** / **Motivo** / **Alternativas descartadas** / **Notas**.

---

## 1. Entrega como aplicación de escritorio de un proyecto Django (Windows)

**Decisión**: Un único proyecto Django que se ejecuta en cada puesto como servidor local (`127.0.0.1`, puerto efímero) y se muestra en una ventana nativa con **pywebview**. Empaquetado para Windows con **PyInstaller** (un `.exe` + carpeta de recursos). El módulo `desktop/launcher.py` arranca el servidor (WSGI en un hilo) y abre la ventana.

**Motivo**:
- Reutiliza todo Django: ORM, migraciones, `django.contrib.auth`, formularios, panel de administración, plantillas del lado servidor.
- Experiencia "de escritorio" (icono, ventana propia, sin barra del navegador) sin introducir un segundo lenguaje ni framework de UI.
- pywebview usa el WebView2 (Edge/Chromium) ya presente en Windows 10/11; huella pequeña.
- Varios puestos = varias instalaciones del mismo `.exe` apuntando a la misma base de datos en la nube; la coherencia la garantiza PostgreSQL, no la app.

**Alternativas descartadas**:
- **Servidor local + navegador del sistema**: más simple aún, pero no cumple la expectativa de "aplicación de escritorio" (pestañas, favoritos, cierres accidentales). Se mantiene como plan B de contingencia.
- **Electron / Tauri + API Django separada**: dos bases de código y dos lenguajes; sobredimensionado para el alcance y el equipo.
- **Framework de escritorio puro (PySide/Tkinter) con acceso directo a BD**: perderíamos plantillas, formularios y admin de Django y habría que reconstruir validación y renderizado.

**Notas**: fijar `ALLOWED_HOSTS=['127.0.0.1','localhost']`, `DEBUG=False` en el empaquetado, y servir estáticos con `whitenoise`. El primer arranque ejecuta `migrate` automáticamente si la BD está vacía o desactualizada.

---

## 2. Conexión de Django a PostgreSQL de Supabase

**Decisión**: `DATABASE_URL` apuntando al **session pooler** de Supabase (puerto `5432`, host `...pooler.supabase.com`), driver **psycopg 3**, `sslmode=require`, `CONN_MAX_AGE=0` (sin conexiones persistentes entre peticiones; el pooler las reutiliza). Las **migraciones de Django son la única fuente del esquema**. Las extensiones `unaccent` y `pg_trgm` se habilitan con una migración inicial (`CREATE EXTENSION IF NOT EXISTS …` vía `django.contrib.postgres.operations.CreateExtension` / `TrigramExtension` + `UnaccentExtension`).

**Motivo**:
- El *transaction pooler* (puerto 6543) no admite sentencias con estado de sesión (`SET`, `search_path`, cursores con nombre) que Django y algunas migraciones usan; el *session pooler* sí y evita agotar conexiones directas.
- psycopg 3 es el driver recomendado por Django 5 y soporta pipeline/tipos modernos.
- No usamos PostgREST ni `supabase-py`: mantiene la app como un Django estándar, testeable con `pytest-django` y sin acoplarse a la API de Supabase.

**Alternativas descartadas**:
- **Conexión directa (no pooler)**: límite bajo de conexiones concurrentes en el plan gestionado; frágil con varios puestos + tareas.
- **Supabase client (`supabase-py`) / PostgREST**: duplicaría el modelo de datos, complicaría transacciones multi-tabla (préstamo = actualizar ejemplar + crear préstamo + auditoría) y las pruebas.
- **RLS (Row-Level Security)**: innecesario — un solo inquilino por instalación y todo el acceso pasa por Django, que ya aplica autenticación y permisos. (Si en el futuro hubiera varias bibliotecas en la misma BD, se revisaría.)

**Notas**: guardar credenciales en `.env` (no versionado); `.env.example` documenta las claves. Copia de seguridad: se confía en los backups automáticos de Supabase; documentar en quickstart cómo verificarlos (cuestión de fiabilidad marcada como pendiente de bajo impacto en el spec).

---

## 3. Autenticación: cuenta central + subcuentas de operador (sin correo)

**Decisión**: Usar `django.contrib.auth` con el modelo `User` estándar.
- **Cuenta central**: `User` con `email` y contraseña; marca `es_central=True` (campo en un perfil `Operador` con `OneToOne` a `User`, o `AbstractUser` extendido). Se crea en el alta de la biblioteca.
- **Subcuentas de operador**: `User` con `username` (único), contraseña y `email=''`; perfil `Operador(es_central=False)`. `is_active` implementa activar/desactivar. Las crea y gestiona **solo** la cuenta central.
- **Atribución**: cada servicio de escritura recibe `actor: User` y escribe `registrado_por` en la fila afectada y una fila en `EntradaAuditoria`. Se implementa con un parámetro explícito en los servicios (no `threadlocals`), y las vistas pasan `request.user`.
- **Permisos**: un único permiso de negocio "gestión" (crear subcuentas, cambiar `ParametrosPrestamo`, lanzar anonimización manual) concedido solo a `es_central`. El resto de operaciones: cualquier operador activo autenticado. Se aplica con un mixin `SoloCentralMixin` en las vistas de gestión.
- **Sesión**: auth por sesión de Django. `SESSION_COOKIE_AGE = 1800` (30 min) + `SESSION_SAVE_EVERY_REQUEST = True` → cierre de sesión por inactividad. "Cambiar de operador" = logout + login. Botón visible de cerrar sesión.

**Motivo**: el modelo `User` de Django ya separa `username` (obligatorio) de `email` (opcional) — encaja exactamente con "subcuentas sin correo". Hashing de contraseñas, throttling de login (`django-axes` opcional), y gestión de sesión vienen resueltos. Evita añadir Supabase Auth (GoTrue), que es email/OAuth-céntrico y obligaría a mantener dos sistemas de identidad.

**Alternativas descartadas**:
- **Supabase Auth para todo**: los operadores no tienen correo; GoTrue no modela bien usuarios "hijos" sin email ni la relación con una cuenta central.
- **Auth de Supabase para la central + Django para operadores**: dos sistemas, dos tablas de identidad, doble punto de fallo.
- **PIN de 4 dígitos por operador**: cómodo en mostrador pero débil; se deja como posible mejora (campo "PIN rápido" adicional a la contraseña) fuera de v1.

**Notas** (valores por defecto adoptados, ajustables):
- Inactividad de sesión: **30 min**.
- Política mínima de contraseña de operador: **8+ caracteres** (validadores de Django).
- La cuenta central también puede operar en mostrador (no se le prohíbe registrar préstamos).

---

## 4. Búsqueda parcial insensible a mayúsculas y acentos (FR-010)

**Decisión**: Extensiones `unaccent` + `pg_trgm`. En `Titulo`, columna generada `busqueda_norm` = `lower(unaccent(titulo || ' ' || autor || ' ' || coalesce(materia,'')))` con **índice GIN `gin_trgm_ops`**. Búsqueda de texto: `busqueda_norm LIKE '%' || lower(unaccent(:q)) || '%'`. Búsqueda por ISBN: igualdad exacta normalizada (sin guiones). Localización por **código de ejemplar**: igualdad exacta sobre `Ejemplar.codigo` (índice único). Resultados paginados a **25** por página, con recuento de ejemplares totales/disponibles calculado por anotación (`Count` con `filter`).

**Motivo**: `pg_trgm` da coincidencia parcial eficiente (`LIKE %term%`) con índice; `unaccent` normaliza acentos; combinarlos en una columna generada evita repetir `unaccent()` en cada consulta y permite indexar. Volumen (20k/50k) es pequeño para trigramas GIN → < 300 ms en servidor, holgado para SC-003.

**Alternativas descartadas**:
- **`ILIKE` sin índice**: escaneo secuencial; a 20k filas todavía rápido pero no deja margen y empeora con crecimiento.
- **`tsvector` / full-text search**: orientado a palabras y ranking; peor para prefijos/subcadenas y códigos; más complejidad de la necesaria.
- **Búsqueda en la app (Python)**: traería todo el catálogo a memoria; descartado.

**Notas**: `unaccent` no es *immutable* por defecto; para la columna generada se usa un wrapper `immutable_unaccent` (función SQL `IMMUTABLE` creada en migración) o se materializa vía trigger. Se elige el wrapper `IMMUTABLE` documentado por la comunidad.

---

## 5. Anonimización programada (FR-034)

**Decisión**: Lógica de anonimización en un **servicio Django** (`privacidad/services.py`) y un **management command** `anonimizar_prestatarios` que lo invoca. Programación: **Programador de tareas de Windows** en un único puesto designado (o el "servidor" de la biblioteca), ejecución **diaria**. Además, la cuenta central dispone de un botón **"Ejecutar anonimización ahora"** y de un indicador de "próxima ejecución / última ejecución". El command es idempotente y registra una `EntradaAuditoria` de tipo `anonimizacion_automatica`.

Reglas (trazadas a FR-034/FR-036/FR-037):
- Selecciona `PersonaPrestataria` con `estado='activa'`, sin `Prestamo` activo (efectivo y sin `fecha_devolucion_real`) y con `max(fecha_prestamo) <= hoy - 2 años` (o sin préstamos y `fecha_alta <= hoy - 2 años`).
- Por cada una: vacía `documento`, `nombre`, `contacto`; pone `estado='anonimizada'`; en sus `Prestamo` pone `persona=NULL` y marca `persona_anonimizada=True`; conserva fechas, retraso y `GestionReclacion`.

**Motivo**: mantener la lógica en un solo sitio testeable (unit + integration) en vez de duplicarla en SQL. El Programador de tareas evita depender de que la app esté abierta. El botón manual cubre despliegues sin tarea programada y el "derecho de supresión" urgente (FR-035 usa el mismo servicio con una persona concreta).

**Alternativas descartadas**:
- **`pg_cron` en Supabase con función PL/pgSQL**: divide la lógica de negocio entre Python y SQL; más difícil de testear y de mantener coherente con las reglas de FR-036.
- **Ejecutar al arranque de la app**: no fiable (puede pasar días sin abrirse un puesto concreto) y añade latencia al inicio.

**Notas**: la ventana de retención (2 años) se implementa como constante configurable en settings (`RETENCION_PRESTATARIOS_DIAS = 730`) por si el Ayuntamiento la ajusta; el spec la fija en 2 años.

---

## 6. Concurrencia en préstamo y devolución (SC-004, FR-015, FR-020)

**Decisión**: Doble salvaguarda.
1. **Bloqueo de fila**: la transacción de préstamo hace `Ejemplar.objects.select_for_update().get(pk=…)`, re-verifica `estado == 'disponible'` y el tope por persona; si no, aborta con el mensaje de FR-015/FR-033. La devolución hace lo mismo sobre el `Prestamo` activo.
2. **Índice único parcial** en `Prestamo`: `UNIQUE (ejemplar_id) WHERE estado_registro = 'efectivo' AND fecha_devolucion_real IS NULL`. Garantiza a nivel de BD "como máximo un préstamo activo por ejemplar", aunque fallara la comprobación de aplicación.

**Motivo**: `select_for_update` serializa a los operadores que tocan el mismo ejemplar (poca contención: 1–4 puestos). El índice único parcial es la red que hace imposible el descuadre de SC-004 incluso ante errores de código o condiciones de carrera raras.

**Alternativas descartadas**:
- **Solo comprobación en aplicación**: ventana de carrera entre `SELECT` y `INSERT`.
- **Bloqueo optimista con campo `version`**: válido, pero el índice único parcial es más simple y expresa directamente la invariante.
- **`SERIALIZABLE` en toda la app**: reintentos y complejidad innecesarios para este nivel de concurrencia.

**Notas**: el *session pooler* de Supabase mantiene la sesión durante la transacción, por lo que `SELECT … FOR UPDATE` funciona con normalidad.

---

## 7. Falta de conexión y UX de error

**Decisión**: **Solo en línea en v1** (declarado en el spec). Middleware ligero que captura `OperationalError`/`InterfaceError` de la BD y renderiza una pantalla clara ("Sin conexión con la base de datos. No se pueden registrar operaciones. Reintentar."). Las operaciones de escritura son transaccionales: si la conexión cae a mitad, la transacción no se confirma y el ejemplar no queda en estado inconsistente. Un indicador de estado de conexión visible en la cabecera (ping ligero a la BD cada N segundos).

**Motivo**: implementar sincronización offline (cola local + resolución de conflictos) es un proyecto en sí mismo y contradice "sin modo offline en v1". Lo esencial es no corromper datos y comunicar el fallo con claridad.

**Alternativas descartadas**:
- **Caché local de solo lectura (SQLite espejo)**: útil para consultar el catálogo sin red, pero añade sincronización y expectativas de escritura offline; fuera de alcance.

**Notas**: recomendar en quickstart una conexión cableada y un SAI en el puesto "servidor" si se centraliza la tarea de anonimización.

---

## Cuestiones abiertas (no bloquean; a decidir en `/speckit-tasks` o durante la implementación)

| Tema | Estado | Propuesta por defecto |
|------|--------|-----------------------|
| Valor exacto de inactividad de sesión | abierto, bajo impacto | 30 min |
| Copia de seguridad / RPO-RTO (fiabilidad del spec, pendiente) | abierto, bajo-medio | Backups automáticos de Supabase + verificación mensual documentada |
| Signatura topográfica / ubicación física como campo del ejemplar | abierto, bajo-medio | Añadir campo opcional `ubicacion` en `Ejemplar` (barato, no bloquea) |
| Nivel de permisos: ¿un solo tipo de operador o varios? | asumido "uno" en el spec | `es_central` (gestión) vs operador; ampliable con un modelo de roles |
| Empaquetado: `.exe` único vs instalador (MSI) | abierto | PyInstaller onedir + acceso directo; MSI si el Ayuntamiento lo exige |
