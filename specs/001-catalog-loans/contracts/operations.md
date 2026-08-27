# Operations Contract — endpoints internos del servidor local

Rutas relativas a `http://127.0.0.1:<puerto>/`. Credencial: ver `README.md`.
Cada fila enlaza con los FR que cubre. Los tests de contrato verifican método, credencial, campos de entrada y forma de la salida/errores.

## Alta y autenticación

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET/POST | `/inicio/alta-biblioteca/` | anónimo (solo si no existe biblioteca) | `nombre_biblioteca`, `email`, `password`, `password2` | `302 /` con sesión de la cuenta central iniciada | `409` si ya hay biblioteca; validación (email inválido, contraseñas no coinciden, password < 8) | FR-030, FR-030a, US6.1 |
| GET/POST | `/acceso/entrar/` | anónimo | `usuario` (username o email de la central), `password` | `302 /` con sesión | `200` re-render con "credenciales no válidas"; cuenta desactivada → mensaje específico | FR-030c, FR-030f, US6 |
| POST | `/acceso/salir/` | operador | — | `302 /acceso/entrar/` | — | FR-030c |

## Gestión de subcuentas de operador  *(solo central)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET | `/operadores/` | central | — | lista de operadores (username, nombre_visible, estado) | `403` si operador | FR-030e |
| GET/POST | `/operadores/nuevo/` | central | `username`, `nombre_visible?`, `password`, `password2` | `302 /operadores/` con el operador activo | `200` re-render: username duplicado (Edge), password < 8 | FR-030b, US6.2, US6.6, SC-014 |
| POST | `/operadores/<id>/desactivar/` | central | — | `302` con estado `desactivada` | `403`; no permite desactivarse a sí misma la central si es la única | FR-030f, US6.4 |
| POST | `/operadores/<id>/reactivar/` | central | — | `302` con estado `activa` | `403` | FR-030f |
| POST | `/operadores/<id>/restablecer-clave/` | central | `password`, `password2` | `302` con mensaje | `200` re-render password < 8 | FR-030b |

## Catálogo — títulos y ejemplares  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET/POST | `/catalogo/titulos/nuevo/` | operador | `titulo*`, `autor*`, `isbn?`, `editorial?`, `anio?`, `materia?`, y opcional bloque de primer ejemplar `codigo?` | `302` al detalle del título | `200` re-render: faltan `titulo`/`autor` (US1.4); `anio` fuera de rango | FR-001, FR-008, US1.1 |
| GET/POST | `/catalogo/titulos/<id>/editar/` | operador | mismos campos del título | `302` al detalle, ejemplares intactos | validación como alta | FR-002 |
| GET | `/catalogo/titulos/<id>/` | operador | — | título + lista de ejemplares (código, estado; si prestado: fecha límite y persona), totales/disponibles | `404` | FR-011, FR-012, FR-025 |
| POST | `/catalogo/titulos/<id>/ejemplares/nuevo/` | operador | `codigo*`, `ubicacion?` | `302` al detalle; disponible +1 | `200`/`409` código duplicado (US1.5) | FR-003, FR-005, US1.2 |
| POST | `/catalogo/ejemplares/<id>/retirar/` | operador | `motivo_retirada*` | `302`; estado `retirado` | `409` si `prestado` (Edge); `motivo` vacío | FR-006, US1.3 |
| GET | `/catalogo/ejemplares/<id>/historial/` | operador | — | préstamos del ejemplar (recientes→antiguos) con persona/fechas/estado, incluidas operaciones **anuladas** y gestiones/correcciones | `404` | FR-025, FR-041, US2.9 |

## Búsqueda y disponibilidad  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET | `/catalogo/buscar/?q=&campo=titulo\|autor\|isbn\|materia&pagina=` | operador | query string | página (25) de títulos con totales/disponibles; `q` vacío → formulario | mensaje "sin resultados" si 0 (no es error) | FR-009, FR-010, FR-011, FR-013 |
| GET | `/catalogo/buscar.json?q=` (autocompletar) | operador | `q` (≥ 2 chars) | `{ "resultados": [{id, titulo, autor, disponibles, total}] }` (máx. 10) | `{ "error": ... }` `400` si `q` < 2 | FR-009, FR-010 |
| GET | `/catalogo/ejemplar-por-codigo.json?codigo=` | operador | `codigo` | `{ ejemplar_id, titulo, estado, prestamo_activo_id? }` | `404 {error:"código no encontrado"}` (Edge etiqueta ilegible) | FR-009a, FR-009b |

## Préstamos y devoluciones  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET/POST | `/prestamos/nuevo/` | operador | `codigo` **o** `ejemplar_id`; `documento*`, `nombre*`, `contacto?`; `confirmar_nombre_distinto?`, `confirmar_avisos?` | `302` con préstamo creado: ejemplar `prestado`, `fecha_limite` = hoy + `plazo_dias` | `409` ejemplar no disponible (con motivo y tenedor actual, FR-015); `409` tope alcanzado (FR-033, US2.7); `200` aviso "documento con otro nombre" pide `confirmar_nombre_distinto` (FR-022); aviso no bloqueante de vencidos (FR-021) | FR-009b, FR-014–FR-017, FR-021, FR-022, FR-033, US2.1–2.3, US2.7–2.8 |
| GET/POST | `/prestamos/devolver/` | operador | `codigo` **o** `prestamo_id` | `302`: `fecha_devolucion_real`=hoy, `ejemplar` `disponible`, indica si hubo retraso y días | `409` sin préstamo activo para el ejemplar (FR-020, US2.6) | FR-009b, FR-018–FR-020, US2.4–2.5 |
| GET | `/prestamos/activos/?pagina=` | operador | — | lista de activos: ejemplar, título, persona, fecha préstamo, fecha límite; **vencidos** destacados con días de retraso y **fecha/medio de la última reclamación** o "sin reclamar" | — | FR-023, FR-024, FR-026b, SC-006, SC-012 |
| GET | `/prestamos/vencidos/` | operador | — | subconjunto de activos con `fecha_limite < hoy`, ordenado por días de retraso desc | — | FR-024, SC-012 |

## Corrección / anulación de operaciones  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| POST | `/prestamos/<id>/anular/` | operador | `motivo*` | `302`: préstamo `anulado`, ejemplar `disponible`, no cuenta para el tope; queda en historial como anulado | `motivo` vacío; préstamo ya anulado | FR-038–FR-041, US2.9, Edge "anular un préstamo" |
| POST | `/prestamos/<id>/anular-devolucion/` | operador | `motivo*` | `302`: `fecha_devolucion_real`=NULL, ejemplar `prestado`; vencido si procede | `motivo` vacío; el préstamo no está devuelto | FR-038–FR-040, Edge |
| POST | `/prestamos/<id>/corregir-ejemplar/` | operador | `motivo*`, `codigo_correcto` **o** `ejemplar_correcto_id` | `302`: se anula el préstamo del ejemplar erróneo y se crea el del correcto | ejemplar correcto no disponible; `motivo` vacío | FR-038–FR-040, Edge "ejemplar equivocado" |
| POST | `/catalogo/ejemplares/<id>/anular-retirada/` | operador | `motivo*` | `302`: ejemplar vuelve a `disponible` (o `prestado` si tenía préstamo activo) | `motivo` vacío; el ejemplar no está retirado | FR-038–FR-040, Edge "reactivar ejemplar" |

## Reclamación de vencidos  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| POST | `/prestamos/<id>/reclamaciones/nueva/` | operador | `fecha*`, `medio* (telefono\|correo\|presencial\|otro)`, `notas?` | `302`: gestión añadida; la lista de vencidos muestra la nueva "última gestión" | `409` si el préstamo está devuelto o no vencido (Edge); aviso si la persona no tiene contacto | FR-026a, FR-026b, US4.5–4.6 |
| GET | `/prestamos/<id>/` | operador | — | detalle del préstamo con todas sus gestiones de reclamación y correcciones | `404` | FR-026b |

## Historial por persona  *(operador)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET | `/personas/historial/?documento=` | operador | `documento` | préstamos de la persona (activos y pasados), marcando cuáles siguen activos | vacío si la persona está **anonimizada** o no existe (FR-026) | FR-026 |

## Configuración  *(solo central)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET/POST | `/configuracion/prestamos/` | central | `plazo_dias` (≥1), `max_prestamos_persona` (≥1) | `302` con valores nuevos; **no** afecta a préstamos previos | `403` si operador; `200` re-render valor < 1 (US5.3) | FR-027–FR-029, FR-030e, US5 |

## Privacidad / anonimización

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET | `/privacidad/` | central | — | estado: nº de personas anonimizables hoy, última/próxima ejecución del proceso | `403` | FR-034 |
| POST | `/privacidad/ejecutar-ahora/` | central | — | `302`: ejecuta el servicio de anonimización automática (idempotente); resumen de cuántas se anonimizaron | `403` | FR-034 |
| POST | `/privacidad/personas/<id>/anonimizar/` | central | `motivo?` | `302`: persona `anonimizada`, préstamos desligados | `409` si tiene préstamos activos (FR-036); `403` si operador | FR-035, FR-036, FR-037 |

## Auditoría  *(operador ve; nadie edita)*

| Método | Ruta | Cred. | Entrada | Salida OK | Errores | FR |
|---|---|---|---|---|---|---|
| GET | `/auditoria/?entidad=&entidad_id=&pagina=` | operador | filtros opcionales | página de `EntradaAuditoria` (tipo, entidad, actor, fecha/hora) | — | FR-030d, FR-031, SC-013 |

## Management command (fuera de HTTP)

| Comando | Ejecución | Efecto | FR |
|---|---|---|---|
| `python manage.py anonimizar_prestatarios` | Programador de tareas de Windows, diario | Aplica FR-034 a todas las personas que cumplen la ventana de 2 años sin préstamos activos; escribe `EntradaAuditoria(tipo='anonimizacion_automatica')` | FR-034, SC-010 |
