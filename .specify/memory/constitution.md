<!--
SYNC IMPACT REPORT
==================
Versión: (plantilla sin versión) → 1.0.0
Tipo de cambio: adopción inicial (MAJOR — primera ratificación)

Principios definidos (nuevos):
  I.   Desarrollo dirigido por especificación
  II.  Pruebas antes de implementar (NO NEGOCIABLE)
  III. Simplicidad y YAGNI
  IV.  Integridad y trazabilidad de datos
  V.   Privacidad por diseño (RGPD/LOPD)

Secciones añadidas:
  - Restricciones Adicionales
  - Flujo de Desarrollo
  - Governance

Secciones eliminadas: ninguna

Plantillas / archivos dependientes:
  ✅ specs/001-catalog-loans/plan.md — sección "Constitution Check" ya alineada
     (menciona simplicidad/YAGNI, pruebas antes de implementar, trazabilidad)
  ✅ specs/001-catalog-loans/tasks.md — pruebas de contrato/integración/unitarias por historia
  ✅ specs/001-catalog-loans/data-model.md — invariantes en BD (índices únicos parciales)
  ⚠️ .specify/templates/plan-template.md — placeholder genérico "[Gates determined based on
     constitution file]"; sin cambios requeridos (se resuelve en cada /speckit-plan)

TODOs diferidos: ninguno (fecha de ratificación proporcionada: 2026-08-27)
-->

# Biblioteca Municipal — Catálogo y Préstamos · Constitución

## Core Principles

### I. Desarrollo dirigido por especificación

Todo cambio de comportamiento MUST poder trazarse a un requisito funcional (`FR-xxx`) o a una
historia de usuario (`US`) de `specs/<feature>/spec.md`. El orden de trabajo MUST ser
`specify → clarify → plan → tasks → implement`; no se escribe código de una funcionalidad
antes de que su `spec.md` esté sin marcadores `[NEEDS CLARIFICATION]` y su `plan.md` y
`tasks.md` existan. Cualquier necesidad nueva descubierta durante la implementación MUST
volver al `spec.md` (o abrir uno nuevo) antes de codificarse; no se añaden funciones "sobre
la marcha".

**Rationale**: mantiene el producto anclado a decisiones acordadas y deja un rastro auditable
entre lo pedido, lo diseñado y lo construido.

### II. Pruebas antes de implementar (NO NEGOCIABLE)

Cada historia de usuario MUST tener pruebas de **contrato** (endpoints de `contracts/`) y de
**integración** (recorrido de la historia) antes de su implementación. Las **reglas de dominio**
(cálculo de fecha límite, días de retraso, tope por persona, normalización de texto, ventana de
retención) MUST tener pruebas **unitarias**. Las pruebas se escriben primero y se MUST comprobar
que fallan antes de codificar la solución. La invariante "un solo préstamo activo por ejemplar"
MUST tener además una prueba de concurrencia. No se marca una tarea como completa si sus pruebas
no están en verde.

**Rationale**: el sistema es un registro operativo (circulación, auditoría, RGPD); una regresión
silenciosa descuadra el inventario o incumple la ley.

### III. Simplicidad y YAGNI

La solución MUST ser un único proyecto Django con acceso a datos por el ORM. NO se introducen
capas de repositorio, buses de eventos, colas de tareas, microservicios ni SDKs de terceros
(incluidos PostgREST, GoTrue o el cliente de Supabase) salvo que un requisito lo exija de forma
demostrable. Toda dependencia nueva y toda estructura que se aparte de "modelos → servicios →
vistas" MUST justificarse en la tabla **Complexity Tracking** del `plan.md` con la alternativa
más simple y por qué se rechaza. Ante dos diseños que cumplen los FR, se elige el más simple.

**Rationale**: el equipo es pequeño y el mantenimiento a largo plazo lo hace la propia
biblioteca; cada pieza extra es coste permanente.

### IV. Integridad y trazabilidad de datos

Ningún registro con historial de préstamos se borra: las bajas se modelan por estado
(`retirado` para ejemplares, `anonimizada` para personas, `anulado` para préstamos y
operaciones). Toda operación que crea o modifica datos MUST quedar atribuida a una subcuenta
autenticada y registrada en `EntradaAuditoria` (append-only), salvo el proceso automático de
anonimización, atribuido al proceso. Las invariantes críticas —"un préstamo activo por
ejemplar", "documento único entre personas activas"— MUST garantizarse también a nivel de base
de datos con restricciones/índices, no solo en código de aplicación.

**Rationale**: el descuadre entre estado del ejemplar y préstamos abiertos (SC-004) y la
pérdida de historial son fallos inaceptables para un servicio público.

### V. Privacidad por diseño (RGPD/LOPD)

Solo se almacenan los datos personales imprescindibles de la persona prestataria (documento,
nombre y, opcionalmente, contacto). Los datos identificativos MUST anonimizarse automáticamente
a los 2 años del último préstamo sin préstamos activos, y MUST poder anonimizarse a petición
(derecho de supresión), conservando los registros de préstamo de forma anonimizada. Ninguna
funcionalidad nueva MUST introducir datos personales adicionales sin una justificación de
necesidad recogida en el `spec.md`. Los registros de auditoría no almacenan datos personales de
prestatarios más allá de la referencia a la entidad afectada.

**Rationale**: la biblioteca es administración pública y trata datos de ciudadanía; el
cumplimiento se diseña desde el modelo de datos, no se añade después.

## Restricciones Adicionales

- **Stack tecnológico**: fijado en `specs/001-catalog-loans/tech-stack.md` y de obligado
  cumplimiento — Python 3.12+, **Django 5.2 LTS**, **PostgreSQL de Supabase** accedido por el
  ORM de Django (migraciones de Django como única fuente del esquema; sin RLS), **pywebview +
  PyInstaller** para el empaquetado de escritorio en Windows, **HTMX + Bootstrap 5** (assets
  vendorizados, sin CDN), y **`django.contrib.auth`** como único sistema de identidad.
  Cambiar cualquiera de estas elecciones es una enmienda a esta constitución.
- **Aplicación solo en línea**: no hay modo sin conexión en la versión actual; los fallos de
  conexión con la base de datos MUST comunicarse con claridad y NO dejar operaciones a medias.
- **Idioma y localización**: interfaz y contenidos en **es-ES**; zona horaria
  **Europe/Madrid**; fechas en formato `dd/mm/aaaa`; `USE_TZ = True`.
- **Autorización**: solo la cuenta central gestiona subcuentas de operador y la configuración
  de préstamo; el resto de operaciones las realiza cualquier operador activo autenticado.
- **Secretos**: nunca en el repositorio; `.env` ignorado por git, `.env.example` versionado.

## Flujo de Desarrollo

- **Calidad de código**: `ruff` (lint + formato) y `pre-commit` (ruff, `manage.py check`,
  `makemigrations --check`) MUST pasar antes de cada commit.
- **Commits**: uno por tarea de `tasks.md` o por grupo lógico; el mensaje referencia la tarea
  (`Txxx`) y/o el FR/US.
- **Migraciones**: cada cambio de modelo lleva su migración en el mismo commit; no se edita una
  migración ya aplicada en otro entorno.
- **Validación de entrega**: antes de cerrar una historia se ejecuta su *Independent Test*;
  antes de cerrar la feature se ejecutan los escenarios `E1–E11` de
  `specs/001-catalog-loans/quickstart.md`.
- **Revisión**: todo cambio se revisa contra estos principios; una desviación sin justificar en
  `Complexity Tracking` es motivo de rechazo.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Las **enmiendas**
requieren: (1) una propuesta escrita con motivo e impacto, (2) actualización de este documento
con su Sync Impact Report, y (3) revisión de `plan.md`/`tasks.md` de las features en curso para
detectar conflictos.

**Versionado** (semántico):
- **MAJOR**: se elimina o redefine de forma incompatible un principio o regla de gobierno.
- **MINOR**: se añade un principio o sección, o se amplía materialmente una guía.
- **PATCH**: aclaraciones, redacción, correcciones sin cambio semántico.

**Cumplimiento**: cada `/speckit-plan` completa su "Constitution Check" contra este documento;
cada revisión de cambios verifica el cumplimiento de los cinco principios. Las cuestiones
abiertas de bajo impacto se registran en `research.md` y no bloquean, pero MUST resolverse
antes de que la feature se declare terminada.

**Version**: 1.0.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-08-27
