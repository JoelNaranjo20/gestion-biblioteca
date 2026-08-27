# Phase 1 — Data Model: Catálogo y Préstamos de la Biblioteca Municipal

**Feature**: `001-catalog-loans` · **Date**: 2026-08-27 · Fuente: [spec.md](./spec.md) §Key Entities + FR-xxx

Notación: PK = clave primaria; FK = clave foránea; `→` relación. Tipos orientativos (PostgreSQL/Django).
Todas las tablas incluidas por `common.ModeloBase`: `id` (PK, bigint), `creado_en`, `actualizado_en` (timestamptz).

---

## 1. Biblioteca (cuenta central)

Representa la organización usuaria. En v1 hay **una** fila, pero el esquema no lo impide.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `nombre` | texto (200) | obligatorio |
| `contacto` | texto (200) | opcional |
| `creada_por_email` | email | correo con el que se dio de alta (informativo; la credencial vive en `Operador`/`User`) |

Relaciones: `→` 1..N `Operador`; es propietaria lógica de `Titulo`, `Prestamo`, `ParametrosPrestamo` (FK `biblioteca` en cada uno; en v1 con valor único).

Trazabilidad: FR-030, FR-030a.

---

## 2. Operador (subcuenta) — perfil sobre `auth.User`

`OneToOne` con `django.contrib.auth.User`. `User.username` (único global), `User.password` (hash), `User.email` (vacío en operadores; con valor solo en la cuenta central), `User.is_active` = activa/desactivada.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `user` | FK OneToOne → auth.User | obligatorio |
| `biblioteca` | FK → Biblioteca | obligatorio |
| `es_central` | booleano | `True` solo para la cuenta central |
| `nombre_visible` | texto (120) | etiqueta mostrada en historial/auditoría; por defecto = `username` |

Reglas:
- `username` único dentro de la biblioteca (en v1 = único global; validación explícita → FR-030b, Edge "nombre de usuario duplicado").
- Solo `es_central` puede crear/editar/(des)activar `Operador` y editar `ParametrosPrestamo` → FR-030e, US6.5.
- Desactivar = `User.is_active=False`: no puede iniciar sesión, pero la fila permanece para conservar la atribución → FR-030f, Edge "operador desactivado con historial".
- Contraseña mínima 8 caracteres (validadores Django).

Estados (`User.is_active`): `activa → desactivada → activa` (reactivación por la central).

Trazabilidad: FR-030b, FR-030c, FR-030e, FR-030f, SC-014.

---

## 3. Titulo

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK → Biblioteca | obligatorio |
| `titulo` | texto (300) | **obligatorio** (FR-001) |
| `autor` | texto (200) | **obligatorio** (FR-001) |
| `isbn` | texto (20) | opcional; se guarda normalizado sin guiones; **no único** (FR-008, Assumptions) |
| `editorial` | texto (200) | opcional |
| `anio` | entero | opcional; rango 0–2100 |
| `materia` | texto (120) | opcional |
| `busqueda_norm` | texto generado | `lower(immutable_unaccent(titulo||' '||autor||' '||coalesce(materia,'')))`; índice GIN `gin_trgm_ops` (FR-010) |

Reglas:
- Guardado rechazado si falta `titulo` o `autor`, indicando los campos → FR-001, US1.4.
- Al registrar un `isbn` ya presente en otra fila: **aviso**, continúa tras confirmación → FR-008, US-Edge "ISBN duplicado".
- No se puede borrar si tiene `Ejemplar` con `Prestamo` registrado → FR-007 (borrado bloqueado a nivel de servicio; baja vía `Ejemplar.retirado`).

Relaciones: `→` 1..N `Ejemplar`.

Índices: GIN sobre `busqueda_norm`; btree sobre `isbn`.

Trazabilidad: FR-001, FR-002, FR-008, FR-009, FR-010, FR-011, FR-013.

---

## 4. Ejemplar

Copia física de un `Titulo`.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `titulo` | FK → Titulo | obligatorio |
| `codigo` | texto (40) | **único en el catálogo** (FR-003, FR-005); valor del código de barras |
| `estado` | enum `disponible` \| `prestado` \| `retirado` | por defecto `disponible` (FR-004) |
| `motivo_retirada` | texto (200) | obligatorio cuando `estado='retirado'` (FR-006) |
| `ubicacion` | texto (120) | **opcional** (signatura/ubicación; cuestión abierta de research §Cuestiones) |

Máquina de estados (`estado`):

```
disponible ──(registrar préstamo, FR-017)──▶ prestado
prestado ──(registrar devolución, FR-018)──▶ disponible
disponible ──(retirar, FR-006)──▶ retirado         [bloqueado si prestado, Edge]
retirado ──(anular retirada, FR-038/FR-040)──▶ disponible | prestado (si tenía préstamo activo)
prestado ──(anular préstamo, FR-038/FR-040)──▶ disponible
disponible ──(anular devolución, FR-038/FR-040)──▶ prestado
```

Reglas:
- `codigo` duplicado → alta rechazada (FR-005, US1.5).
- No pasar a `retirado` si `estado='prestado'` (FR-006, Edge).
- El `estado` es **derivable** del préstamo activo; se mantiene desnormalizado por rendimiento y se recalcula en toda corrección (FR-040). Invariante verificada por SC-004 y por el índice único parcial de `Prestamo`.

Relaciones: `→` 0..N `Prestamo` a lo largo del tiempo.

Índices: único sobre `codigo`; btree sobre `(titulo, estado)`.

Trazabilidad: FR-003…FR-007, FR-009a, FR-011, FR-012, FR-025, FR-041.

---

## 5. PersonaPrestataria

Directorio reutilizable mínimo (sin carné ni socio).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK → Biblioteca | obligatorio |
| `documento` | texto (40) | **obligatorio** mientras `estado='activa'`; **clave de identificación** (único por biblioteca entre las activas); se vacía al anonimizar |
| `nombre` | texto (200) | **obligatorio** mientras `activa`; se vacía al anonimizar |
| `contacto` | texto (200) | opcional; se vacía al anonimizar |
| `estado` | enum `activa` \| `anonimizada` | por defecto `activa` |
| `fecha_alta` | date | fecha de creación (primer préstamo) |
| `fecha_ultimo_prestamo` | date | se actualiza en cada préstamo; base del cálculo de retención |

Máquina de estados: `activa ──(FR-034 automática | FR-035 manual)──▶ anonimizada` (irreversible).

Reglas:
- Se crea en el **primer** préstamo, identificada por `documento`; se reutiliza después (FR-032).
- Índice único parcial: `UNIQUE (biblioteca, documento) WHERE estado='activa'`.
- Aviso si el `documento` existe con `nombre` distinto → pide confirmar/corregir (FR-022, Edge "mismo documento con nombre distinto").
- No se puede anonimizar con préstamos activos (FR-036, Edge).
- Tras anonimizar: consultas por documento no devuelven nada (FR-026); un préstamo nuevo con ese documento crea **otra** ficha (Edge "préstamo a persona anonimizada").

Relaciones: `→` 0..N `Prestamo`.

Trazabilidad: FR-021, FR-022, FR-026, FR-032, FR-034…FR-037, SC-010.

---

## 6. ParametrosPrestamo

Configuración operativa global (una fila por biblioteca).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK OneToOne → Biblioteca | obligatorio |
| `plazo_dias` | entero | **mínimo 1**; por defecto **15** (FR-027, FR-029) |
| `max_prestamos_persona` | entero | **mínimo 1**; por defecto **3** (FR-027, FR-029, FR-033) |

Reglas:
- Solo la cuenta central puede modificar (FR-030e).
- Valores no válidos (0, negativo, vacío) → rechazo con el mínimo admitido (US5.3).
- Los cambios **no** alteran préstamos existentes ni sus fechas límite (FR-028, US5.2).

Trazabilidad: FR-027, FR-028, FR-029, FR-033, US5.

---

## 7. Prestamo

Entrega temporal de un `Ejemplar` a una `PersonaPrestataria`.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK → Biblioteca | obligatorio |
| `ejemplar` | FK → Ejemplar | obligatorio |
| `persona` | FK → PersonaPrestataria, NULL | se pone NULL al anonimizar (FR-034) |
| `persona_anonimizada` | booleano | `True` tras anonimizar; conserva "hubo persona" sin identificarla |
| `fecha_prestamo` | date | obligatorio (FR-016) |
| `fecha_limite` | date | = `fecha_prestamo + plazo_dias` **vigente al crear** (FR-016); no se recalcula por cambios de config (FR-028) |
| `fecha_devolucion_real` | date, NULL | NULL mientras activo (FR-018) |
| `dias_retraso` | entero | 0 si a tiempo; `>0` calculado al cerrar (FR-019); en activos se calcula al vuelo para listados (FR-024) |
| `estado_registro` | enum `efectivo` \| `anulado` | por defecto `efectivo` (FR-038/FR-039) |
| `registrado_por` | FK → auth.User | operador que registró el préstamo (FR-030d) |
| `devolucion_registrada_por` | FK → auth.User, NULL | operador que registró la devolución (FR-030d) |

Estados derivados (no columna): **activo** (`estado_registro='efectivo'` y `fecha_devolucion_real IS NULL`), **devuelto**, **devuelto con retraso** (`dias_retraso>0`), **anulado**.

Reglas / invariantes:
- Crear solo si `ejemplar.estado='disponible'` (FR-014, FR-015) — comprobado con `select_for_update` (research §6).
- Bloqueo por tope: rechazar si la persona tiene `>= max_prestamos_persona` préstamos activos (incluye vencidos) (FR-033, US2.7, Edge).
- **Índice único parcial**: `UNIQUE (ejemplar) WHERE estado_registro='efectivo' AND fecha_devolucion_real IS NULL` → a lo sumo un préstamo activo por ejemplar (SC-004, research §6).
- Devolución: fija `fecha_devolucion_real`, calcula `dias_retraso`, pasa `ejemplar` a `disponible` (FR-018, FR-019).
- Anulación de préstamo → `estado_registro='anulado'`, `ejemplar` vuelve a `disponible`, deja de contar para el tope y para "préstamos efectivos" (FR-040, Edge "anular un préstamo").
- Anulación de devolución → `fecha_devolucion_real=NULL`, `ejemplar` vuelve a `prestado`; si `fecha_limite<hoy`, vuelve a constar vencido (FR-040, Edge).

Índices: parcial único citado; btree sobre `(ejemplar, fecha_prestamo desc)`, `(persona)`, `(fecha_limite) WHERE fecha_devolucion_real IS NULL AND estado_registro='efectivo'` (lista de vencidos, FR-024).

Trazabilidad: FR-014…FR-021, FR-023…FR-025, FR-030d, FR-033, SC-001…SC-005, SC-007.

---

## 8. CorreccionOperacion

Anulación o rectificación de una operación previa.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK → Biblioteca | obligatorio |
| `tipo` | enum `anulacion` \| `correccion` | obligatorio |
| `operacion` | enum `prestamo` \| `devolucion` \| `retirada` | qué se corrige (FR-038) |
| `prestamo` | FK → Prestamo, NULL | referencia cuando aplica |
| `ejemplar` | FK → Ejemplar, NULL | referencia cuando aplica (retirada) |
| `motivo` | texto (300) | **obligatorio** (FR-038) |
| `realizada_por` | FK → auth.User | operador que corrige (FR-030d) |
| `fecha_hora` | timestamptz | obligatorio (FR-039) |

Reglas:
- La operación original **no se borra**: se marca `anulada` (FR-039).
- Tras aplicar, recalcular estado del ejemplar y datos derivados de los préstamos afectados y el recuento por persona (FR-040).
- Visible en el historial del ejemplar como "anulada" (FR-041, US2.9).

Trazabilidad: FR-038…FR-041, SC-011, US2.8–2.9, Edges de anulación.

---

## 9. GestionReclamacion

Intento de contacto con el prestatario por un préstamo vencido.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `prestamo` | FK → Prestamo | obligatorio; debe estar **activo y vencido** al crear (FR-026a) |
| `fecha` | date | obligatorio |
| `medio` | enum `telefono` \| `correo` \| `presencial` \| `otro` | obligatorio |
| `notas` | texto (500) | opcional |
| `registrada_por` | FK → auth.User | operador (FR-030d) |

Reglas:
- No se pueden añadir gestiones a un préstamo **cerrado**; las previas se conservan (Edge "gestión sobre préstamo devuelto").
- Si la persona no tiene `contacto`, se permite igualmente (p. ej. `presencial`) con aviso (Edge "reclamación sin datos de contacto").
- La lista de vencidos y el detalle muestran fecha y medio de la **última** gestión, o "sin reclamar" (FR-026b, SC-012).
- El sistema **no** envía comunicaciones (FR-026c).
- Se anonimiza junto con la persona (FR-026d).

Trazabilidad: FR-026a…FR-026d, SC-012, US4.5–4.6.

---

## 10. EntradaAuditoria

Registro de cada operación que crea o modifica datos (FR-030d, FR-031).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `biblioteca` | FK → Biblioteca | obligatorio |
| `tipo_operacion` | texto (60) | p. ej. `alta_titulo`, `edicion_titulo`, `alta_ejemplar`, `retirada_ejemplar`, `reactivacion_ejemplar`, `prestamo`, `devolucion`, `correccion`, `reclamacion`, `anonimizacion_manual`, `anonimizacion_automatica`, `cambio_configuracion`, `alta_operador`, `baja_operador` |
| `entidad` | texto (40) | `ejemplar` \| `titulo` \| `prestamo` \| `persona` \| `configuracion` \| `operador` |
| `entidad_id` | bigint, NULL | id de la fila afectada |
| `actor` | FK → auth.User, NULL | subcuenta autora; NULL solo para el proceso automático de anonimización (o un usuario "sistema" dedicado) |
| `fecha_hora` | timestamptz | obligatorio |
| `detalle` | jsonb | opcional; resumen legible del cambio |

Reglas:
- Solo inserciones (append-only); nunca se edita ni se borra.
- Consultable por ejemplar (alimenta FR-025/FR-041) y por préstamo.

Trazabilidad: FR-030d, FR-031, SC-013.

---

## Resumen de relaciones

```
Biblioteca 1─N Operador (perfil de auth.User)
Biblioteca 1─N Titulo 1─N Ejemplar 1─N Prestamo N─1 PersonaPrestataria
Biblioteca 1─1 ParametrosPrestamo
Prestamo 1─N GestionReclamacion
Prestamo 1─N CorreccionOperacion   (o Ejemplar 1─N CorreccionOperacion para 'retirada')
Biblioteca 1─N EntradaAuditoria   (actor → auth.User)
Prestamo.registrado_por / devolucion_registrada_por → auth.User
```

## Invariantes globales

1. Un `Ejemplar` tiene **como máximo un** `Prestamo` activo (índice único parcial) — soporta SC-004.
2. `Ejemplar.estado='prestado'` ⟺ existe un `Prestamo` activo para él (mantenido por servicios + recálculo en correcciones).
3. `PersonaPrestataria.estado='anonimizada'` ⟹ `documento/nombre/contacto` vacíos y todos sus `Prestamo` con `persona IS NULL, persona_anonimizada=True`.
4. Ninguna fila con historial de préstamos se borra; las bajas son `estado='retirado'` (ejemplar) o `anonimizada` (persona) o `anulado` (préstamo).
5. Toda escritura de negocio produce una `EntradaAuditoria` con `actor` (salvo la anonimización automática, atribuida al proceso).
