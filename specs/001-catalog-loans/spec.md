# Feature Specification: Catálogo y Préstamos de la Biblioteca Municipal

**Feature Branch**: `001-catalog-loans`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "Sistema interno de gestión de la biblioteca municipal, de uso exclusivo para el personal de la biblioteca (no hay acceso del público). Funcionalidad central: (1) Mantener el catálogo bibliográfico: registrar títulos con sus datos (título, autor, ISBN, editorial, año, materia/categoría) y los ejemplares físicos asociados a cada título, cada uno con un código de ejemplar y su estado (disponible, prestado, retirado/dado de baja). (2) Buscar en el catálogo por título, autor, ISBN o materia, y ver qué ejemplares hay y cuáles están disponibles. (3) Registrar préstamos: el personal presta un ejemplar disponible a una persona identificada por su documento y nombre, el sistema asigna una fecha límite de devolución según un plazo configurable, y marca el ejemplar como prestado. (4) Registrar devoluciones: al devolver, el sistema marca el ejemplar como disponible de nuevo y guarda la fecha real de devolución, indicando si hubo retraso. (5) Consultar los préstamos activos y el historial de préstamos de un ejemplar y de una persona. Fuera de alcance en esta versión: portal público / web para usuarios, módulo de gestión de socios con carné, reservas de ejemplares en cola, y cálculo o cobro de multas."

## Clarifications

### Session 2026-08-27

- Q: ¿Identificación del personal — cuentas individuales o puesto compartido? → A: Puesto compartido, sin inicio de sesión individual; el sistema registra la fecha y hora de cada operación pero no la persona que la realiza, y no aplica control de acceso por rol.
- Q: ¿Registro de personas prestatarias — ficha reutilizable o datos por préstamo? → A: Directorio reutilizable mínimo (documento y nombre obligatorios, contacto opcional); la ficha se crea en el primer préstamo, identificada por el documento, y se reutiliza en los siguientes. Sin carné ni estado de socio.
- Q: ¿Límite de préstamos simultáneos por persona? → A: Sí, tope configurable con valor por defecto de 3 préstamos activos por persona.
- Q: ¿Cuánto tiempo se conservan los datos personales de prestatarios y su historial, y qué pasa al vencer el plazo? → A: Se anonimizan automáticamente los datos identificativos de la persona a los 2 años desde su último préstamo (sin préstamos activos ni nuevos en ese periodo); los préstamos se conservan de forma anonimizada. El personal también puede anonimizar manualmente a petición.
- Q: ¿La puesta en marcha necesita importar un catálogo o préstamos existentes, o se parte de cero? → A: Desde cero. No hay sistema de préstamos previo; el catálogo, los prestatarios y los préstamos se crean mediante entrada manual. La importación/migración masiva queda fuera de alcance en esta versión.
- Q: ¿Cómo se corrigen los errores del personal al registrar una operación (préstamo/devolución/retirada)? → A: El personal puede anular o corregir una operación reciente indicando un motivo; la corrección se registra con fecha y hora, la operación original se marca como anulada (no se borra) y el estado del ejemplar se recalcula.
- Q: ¿Cómo localiza el personal el ejemplar para prestar o devolver? → A: Indistintamente por código de ejemplar (tecleado o escaneado con lector de código de barras) o por búsqueda de título/autor. El código de barras se introduce como texto, sin integración especial; los ejemplares pueden etiquetarse progresivamente.
- Q: Con los préstamos vencidos, ¿solo listarlos o también apoyar la reclamación? → A: Listar los vencidos y permitir registrar manualmente las gestiones de reclamación por préstamo (fecha, medio, notas). El sistema no genera ni envía comunicaciones a los prestatarios.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mantener el catálogo bibliográfico (Priority: P1)

El personal de la biblioteca da de alta y actualiza los títulos del fondo (título, autor, ISBN, editorial, año y materia) y registra los ejemplares físicos de cada título, cada uno con un código único y un estado (disponible, prestado, retirado).

**Why this priority**: Sin un catálogo con ejemplares no se puede buscar ni prestar nada; es la base del resto de funciones. Por sí sola ya aporta valor: sustituye a un inventario en papel o en hoja de cálculo.

**Independent Test**: Se prueba dando de alta varios títulos con sus ejemplares, editándolos, cambiando un ejemplar a "retirado" y comprobando que el catálogo refleja los datos y los recuentos correctos, sin necesidad de préstamos.

**Acceptance Scenarios**:

1. **Given** que el título no existe en el catálogo, **When** el personal lo registra con sus datos obligatorios y al menos un ejemplar, **Then** el título queda guardado y el ejemplar aparece como "disponible".
2. **Given** un título existente, **When** el personal añade un ejemplar con un código nuevo, **Then** el título pasa a tener un ejemplar más y el recuento de disponibles aumenta en uno.
3. **Given** un ejemplar "disponible", **When** el personal lo marca como "retirado" indicando el motivo, **Then** el ejemplar deja de contar como disponible y no puede prestarse.
4. **Given** un título al que le falta el título o el autor, **When** el personal intenta guardarlo, **Then** el sistema rechaza el guardado e indica qué campos faltan.
5. **Given** un código de ejemplar que ya existe, **When** el personal intenta registrar otro ejemplar con ese mismo código, **Then** el sistema rechaza el alta e informa del duplicado.

---

### User Story 2 - Prestar y devolver ejemplares (Priority: P1)

El personal presta un ejemplar disponible a una persona identificada por documento y nombre; el sistema fija la fecha límite según el plazo vigente y marca el ejemplar como prestado. Al devolverlo, el personal registra la devolución, el ejemplar vuelve a estar disponible y queda constancia de la fecha real y de si hubo retraso.

**Why this priority**: Es la razón de ser del sistema: controlar qué ejemplares están fuera, quién los tiene y cuándo deben volver. Junto con un catálogo mínimo constituye el MVP.

**Independent Test**: Con al menos un ejemplar disponible, se registra un préstamo, se verifica que el ejemplar queda "prestado" con fecha límite, se registra la devolución y se comprueba que vuelve a "disponible" con fecha real y marca de retraso cuando corresponde.

**Acceptance Scenarios**:

1. **Given** un ejemplar "disponible", **When** el personal registra un préstamo indicando documento y nombre de la persona, **Then** el ejemplar pasa a "prestado", se guarda la fecha de préstamo y se calcula la fecha límite sumando el plazo vigente.
2. **Given** un ejemplar "prestado", **When** el personal intenta prestarlo de nuevo, **Then** el sistema impide el préstamo e informa de que no está disponible y de quién lo tiene.
3. **Given** un ejemplar "retirado", **When** el personal intenta prestarlo, **Then** el sistema impide el préstamo e informa de que está dado de baja.
4. **Given** un ejemplar "prestado", **When** el personal registra la devolución, **Then** el ejemplar vuelve a "disponible", se guarda la fecha real de devolución y el préstamo queda cerrado.
5. **Given** un préstamo con la fecha límite ya superada, **When** el personal registra la devolución, **Then** el préstamo se cierra marcado como devuelto con retraso, indicando los días de demora.
6. **Given** un ejemplar que no está prestado, **When** el personal intenta registrar una devolución, **Then** el sistema informa de que no hay ningún préstamo activo para ese ejemplar.
7. **Given** una persona con 3 préstamos activos y un tope configurado de 3, **When** el personal intenta registrarle un cuarto préstamo, **Then** el sistema lo impide e informa de que se ha alcanzado el máximo de préstamos por persona.
8. **Given** un ejemplar localizado por su código (tecleado o escaneado), **When** el personal registra el préstamo, **Then** el sistema opera igual que si el ejemplar se hubiera localizado por búsqueda de título.
9. **Given** un préstamo registrado por error, **When** el personal lo anula indicando el motivo, **Then** el ejemplar vuelve a "disponible", el préstamo queda marcado como anulado y deja de contar para el tope de la persona, y el registro anulado se conserva en el historial del ejemplar.

---

### User Story 3 - Buscar en el catálogo y comprobar disponibilidad (Priority: P2)

El personal busca en el catálogo por título, autor, ISBN o materia y, para cada resultado, ve cuántos ejemplares hay y cuántos están disponibles, además del detalle de cada ejemplar y su estado.

**Why this priority**: Acelera la atención en el mostrador (saber al instante si hay un ejemplar libre), pero con un fondo pequeño se puede operar sin ella; de ahí P2.

**Independent Test**: Con varios títulos y ejemplares en distintos estados, se busca por cada criterio y se comprueba que resultados y recuentos de disponibles coinciden con el estado real del catálogo.

**Acceptance Scenarios**:

1. **Given** varios títulos en el catálogo, **When** el personal busca por una palabra del título, **Then** el sistema muestra los títulos cuyo título contiene esa palabra, con su recuento de ejemplares totales y disponibles.
2. **Given** un título con 3 ejemplares, 1 prestado y 1 retirado, **When** el personal lo consulta, **Then** el sistema muestra 3 ejemplares totales y 1 disponible.
3. **Given** una búsqueda por ISBN exacto, **When** existe un título con ese ISBN, **Then** el sistema lo muestra como resultado.
4. **Given** un criterio de búsqueda sin coincidencias, **When** el personal ejecuta la búsqueda, **Then** el sistema muestra un resultado vacío con un mensaje claro de que no se han encontrado títulos.

---

### User Story 4 - Consultar préstamos activos e historial (Priority: P2)

El personal consulta la lista de préstamos activos (con fecha límite y aviso de vencidos), el historial de préstamos de un ejemplar concreto y de una persona concreta, y registra las gestiones de reclamación de los préstamos vencidos.

**Why this priority**: Necesario para el seguimiento de devoluciones, la reclamación de vencidos y la resolución de incidencias ("¿quién tuvo este libro?"), pero la operativa diaria de prestar y devolver puede funcionar sin estas vistas al principio.

**Independent Test**: Tras registrar varios préstamos y devoluciones, se abre la lista de activos y se comprueba que solo aparecen los no devueltos; se consulta el historial por ejemplar y por persona; y se registra una gestión de reclamación sobre un préstamo vencido comprobando que queda reflejada en la lista de vencidos.

**Acceptance Scenarios**:

1. **Given** varios préstamos, algunos devueltos y otros no, **When** el personal abre la lista de préstamos activos, **Then** solo se muestran los préstamos sin fecha real de devolución.
2. **Given** la lista de préstamos activos, **When** algún préstamo tiene la fecha límite superada, **Then** ese préstamo aparece destacado como vencido con los días de retraso.
3. **Given** un ejemplar con varios préstamos a lo largo del tiempo, **When** el personal consulta su historial, **Then** se muestran todos sus préstamos del más reciente al más antiguo, con persona, fechas y estado.
4. **Given** una persona con préstamos previos, **When** el personal consulta su historial por documento, **Then** se muestran todos sus préstamos y cuáles siguen activos.
5. **Given** un préstamo vencido sin gestiones previas, **When** el personal registra una gestión de reclamación con fecha y medio, **Then** la gestión queda guardada y la lista de préstamos vencidos muestra la fecha de esa última gestión para ese préstamo.
6. **Given** un préstamo vencido que ya se ha reclamado antes, **When** el personal abre la lista de vencidos, **Then** ese préstamo muestra la fecha y el medio de la gestión más reciente.

---

### User Story 5 - Configurar el plazo de préstamo (Priority: P3)

El personal de la biblioteca define el plazo de préstamo (en días naturales) y el número máximo de préstamos activos por persona; el sistema usa esos parámetros al registrar los nuevos préstamos.

**Why this priority**: Aporta flexibilidad, pero el sistema puede arrancar con los valores por defecto (15 días de plazo, 3 préstamos por persona); ajustarlos es una mejora, no un bloqueo.

**Independent Test**: Se cambia el plazo configurado, se registra un préstamo nuevo y se comprueba que la fecha límite usa el nuevo plazo, sin que se alteren los préstamos ya existentes; y se cambia el tope de préstamos por persona comprobando que la validación usa el nuevo valor.

**Acceptance Scenarios**:

1. **Given** un plazo configurado de 15 días, **When** el personal lo cambia a 21 días, **Then** los préstamos registrados a partir de ese momento usan 21 días para la fecha límite.
2. **Given** un cambio de plazo, **When** existen préstamos anteriores al cambio, **Then** sus fechas límite no se modifican.
3. **Given** un valor de plazo no válido (cero, negativo o vacío), **When** se intenta guardar, **Then** el sistema rechaza el cambio e informa del valor mínimo admitido.
4. **Given** un tope de préstamos por persona configurado en 3, **When** el personal lo cambia a 5, **Then** a partir de ese momento se permite a cada persona tener hasta 5 préstamos activos.

---

### Edge Cases

- **Ejemplar no disponible**: intento de préstamo de un ejemplar "prestado" o "retirado" → el sistema lo impide con un mensaje que explica el motivo.
- **Devolución sin préstamo**: intento de devolver un ejemplar que consta como "disponible" → el sistema avisa de que no hay préstamo activo.
- **Código de ejemplar duplicado**: alta de un ejemplar con un código ya usado → el sistema rechaza el alta.
- **ISBN duplicado**: alta de un título con un ISBN ya presente → el sistema avisa, pero permite continuar (puede haber ediciones o registros distintos con el mismo ISBN, y el fondo antiguo puede carecer de ISBN).
- **Baja de un ejemplar prestado**: intento de marcar como "retirado" un ejemplar que está prestado → el sistema lo impide hasta que se registre la devolución.
- **Eliminación de registros con historial**: no se permite borrar un título o un ejemplar con préstamos registrados; el ejemplar se marca como "retirado" para conservar la trazabilidad.
- **Persona con préstamos vencidos**: al iniciar un préstamo para una persona que ya tiene ejemplares vencidos, el sistema muestra un aviso con esos préstamos, pero no bloquea la operación (las sanciones están fuera de alcance).
- **Fecha límite en día no laborable o festivo**: el plazo se cuenta en días naturales; el sistema no ajusta la fecha límite por fines de semana ni festivos en esta versión.
- **Búsqueda con acentos o mayúsculas**: la búsqueda por texto no distingue mayúsculas/minúsculas ni acentos.
- **Mismo documento con nombre distinto**: si se registra un préstamo con un documento ya visto pero un nombre diferente, el sistema avisa de la discrepancia y pide confirmar o corregir.
- **Tope de préstamos alcanzado**: intento de registrar un préstamo a una persona que ya tiene el máximo configurado de préstamos activos → el sistema lo impide e indica cuántos préstamos activos tiene y el tope vigente. Los préstamos vencidos también cuentan para el tope.
- **Anonimización con préstamos activos**: no se puede anonimizar (ni automática ni manualmente) a una persona con préstamos sin devolver; la anonimización queda pendiente hasta que devuelva todo.
- **Préstamo a una persona anonimizada**: al introducir el documento de una persona anonimizada en un préstamo nuevo, el sistema no recupera datos anteriores y trata la operación como una persona nueva (nueva ficha).
- **Historial de un ejemplar con préstamos anonimizados**: el historial del ejemplar sigue mostrando fechas y estado de esos préstamos, pero sin datos de la persona.
- **Anular un préstamo**: el ejemplar vuelve a "disponible", el préstamo se marca como anulado y deja de contar para el tope por persona y para el historial de préstamos efectivos.
- **Anular una devolución registrada por error**: el préstamo vuelve a estado activo y el ejemplar a "prestado"; si la fecha límite ya pasó, se vuelve a marcar como vencido.
- **Corregir un préstamo con el ejemplar equivocado**: se anula el préstamo del ejemplar erróneo (vuelve a "disponible") y se registra el préstamo del ejemplar correcto.
- **Reactivar un ejemplar retirado por error**: al anular la retirada, el ejemplar vuelve a "disponible" (o a "prestado" si tenía un préstamo activo en curso).
- **Código de ejemplar no encontrado o etiqueta ilegible**: si el código introducido no existe o no se puede leer, el sistema lo indica y el personal recurre a la búsqueda por título para localizar el ejemplar.
- **Gestión de reclamación sobre un préstamo ya devuelto**: no se pueden añadir gestiones a un préstamo cerrado; las registradas antes de la devolución se conservan en el historial.
- **Reclamación sin datos de contacto**: si la persona no tiene contacto guardado, el sistema permite igualmente registrar una gestión (p. ej. "presencial") pero avisa de que no hay teléfono ni correo.

## Requirements *(mandatory)*

### Functional Requirements

**Catálogo**

- **FR-001**: El sistema MUST permitir registrar un título con título y autor obligatorios y, opcionalmente, ISBN, editorial, año de publicación y materia/categoría.
- **FR-002**: El sistema MUST permitir editar los datos de un título existente conservando sus ejemplares asociados.
- **FR-003**: El sistema MUST permitir registrar uno o varios ejemplares físicos para un título, cada uno con un código de ejemplar único en todo el catálogo.
- **FR-004**: El sistema MUST asignar a cada ejemplar uno de estos estados: "disponible", "prestado" o "retirado".
- **FR-005**: El sistema MUST impedir registrar dos ejemplares con el mismo código y avisar del duplicado.
- **FR-006**: El sistema MUST permitir cambiar un ejemplar a estado "retirado" indicando un motivo, y MUST impedirlo si el ejemplar está "prestado".
- **FR-007**: El sistema MUST impedir el borrado de títulos y ejemplares que tengan préstamos registrados; la baja se realiza mediante el estado "retirado".
- **FR-008**: El sistema MUST avisar cuando se registre un título con un ISBN que ya existe en el catálogo, permitiendo continuar tras confirmación.

**Búsqueda y disponibilidad**

- **FR-009**: El sistema MUST permitir buscar títulos por título, autor, ISBN o materia.
- **FR-009a**: El sistema MUST permitir localizar un ejemplar directamente por su código de ejemplar, tanto tecleado como introducido mediante un lector de código de barras que lo transcribe como texto (sin integración específica con el dispositivo).
- **FR-009b**: Para registrar un préstamo o una devolución, el sistema MUST permitir seleccionar el ejemplar indistintamente por su código de ejemplar o desde la búsqueda de título/autor; en la devolución, a partir del código MUST recuperar automáticamente el préstamo activo del ejemplar.
- **FR-010**: La búsqueda por texto MUST ignorar mayúsculas/minúsculas y acentos y MUST admitir coincidencias parciales en título y autor.
- **FR-011**: Para cada título, el sistema MUST mostrar el número total de ejemplares y el número de ejemplares disponibles en ese momento.
- **FR-012**: El sistema MUST permitir ver el detalle de los ejemplares de un título con su código y estado actual y, para los prestados, la fecha límite y la persona que lo tiene.
- **FR-013**: Cuando una búsqueda no tenga resultados, el sistema MUST mostrar un mensaje explícito de "sin resultados".

**Préstamos y devoluciones**

- **FR-014**: El sistema MUST permitir registrar un préstamo de un ejemplar en estado "disponible" a una persona identificada por documento y nombre.
- **FR-015**: El sistema MUST impedir el préstamo de un ejemplar que no esté "disponible" e informar del motivo (prestado o retirado) y, si está prestado, de quién lo tiene y desde cuándo.
- **FR-016**: Al registrar un préstamo, el sistema MUST guardar la fecha de préstamo y MUST calcular la fecha límite de devolución sumando el plazo de préstamo vigente a la fecha de préstamo.
- **FR-017**: Al registrar un préstamo, el sistema MUST cambiar el estado del ejemplar a "prestado".
- **FR-018**: El sistema MUST permitir registrar la devolución de un ejemplar "prestado", guardando la fecha real de devolución, cerrando el préstamo y devolviendo el ejemplar a "disponible".
- **FR-019**: Al cerrar un préstamo, el sistema MUST indicar si la devolución se ha producido con retraso y cuántos días de demora acumula.
- **FR-020**: El sistema MUST impedir registrar una devolución para un ejemplar que no tenga un préstamo activo e informar de ello.
- **FR-021**: El sistema MUST mostrar un aviso, al iniciar un préstamo, si la persona prestataria tiene préstamos vencidos, sin bloquear la operación.
- **FR-022**: El sistema MUST avisar si el documento de la persona prestataria ya se ha usado antes con un nombre distinto, pidiendo confirmar o corregir.

**Consultas**

- **FR-023**: El sistema MUST ofrecer una lista de préstamos activos (no devueltos) con ejemplar, título, persona, fecha de préstamo y fecha límite.
- **FR-024**: En la lista de préstamos activos, el sistema MUST distinguir los préstamos vencidos e indicar los días de retraso.
- **FR-025**: El sistema MUST mostrar el historial de préstamos de un ejemplar, ordenado del más reciente al más antiguo, con persona, fechas y estado (activo / devuelto / devuelto con retraso).
- **FR-026**: El sistema MUST mostrar el historial de préstamos de una persona a partir de su documento, indicando cuáles siguen activos. Esta consulta solo devuelve resultados para personas no anonimizadas.

**Reclamación de vencidos**

- **FR-026a**: El sistema MUST permitir registrar, para un préstamo activo vencido, una o varias gestiones de reclamación, cada una con fecha, medio (teléfono / correo electrónico / presencial / otro) y notas opcionales.
- **FR-026b**: El sistema MUST mostrar, en la lista de préstamos vencidos y en el detalle de cada préstamo, la fecha y el medio de la última gestión de reclamación registrada, o indicar que aún no se ha reclamado.
- **FR-026c**: El sistema MUST NOT generar ni enviar comunicaciones a los prestatarios; la reclamación se realiza fuera del sistema y este solo conserva su rastro.
- **FR-026d**: Las gestiones de reclamación forman parte del préstamo a efectos de conservación y se anonimizan junto con la persona (FR-034).

**Configuración**

- **FR-027**: El sistema MUST permitir consultar y modificar los parámetros de préstamo: (a) el plazo de préstamo en días naturales (mínimo 1) y (b) el número máximo de préstamos activos por persona (mínimo 1).
- **FR-028**: Los cambios en los parámetros de préstamo MUST aplicarse solo a los préstamos registrados después del cambio, sin alterar los existentes ni sus fechas límite.
- **FR-029**: El sistema MUST usar, mientras no se configuren otros valores, un plazo de préstamo por defecto de 15 días naturales y un máximo de 3 préstamos activos por persona.

**Trazabilidad y acceso**

- **FR-030**: El sistema MUST registrar, para cada préstamo y cada devolución, la fecha y hora en que se registró la operación.
- **FR-031**: El acceso al sistema MUST estar restringido al personal de la biblioteca; el público no tiene acceso. El sistema se usa en puestos de trabajo compartidos del personal, sin inicio de sesión individual; en consecuencia, cada operación registra la fecha y hora (FR-030) pero no la persona que la realizó, y el sistema no restringe funciones por rol de usuario.
- **FR-032**: El sistema MUST mantener un directorio de personas prestatarias con documento identificativo y nombre obligatorios y contacto opcional. La ficha se crea automáticamente la primera vez que se presta a esa persona (identificada por su documento) y se reutiliza en préstamos posteriores. El directorio NO incluye carné, cuota ni estado de socio.
- **FR-033**: El sistema MUST impedir registrar un préstamo cuando la persona ya tiene un número de préstamos activos igual o superior al máximo configurado (por defecto 3), contando también los préstamos vencidos, e informar del número de préstamos activos y del tope vigente.

**Protección de datos (RGPD/LOPD)**

- **FR-034**: El sistema MUST anonimizar automáticamente los datos identificativos de una persona prestataria (documento, nombre y contacto) cuando hayan transcurrido 2 años desde su último préstamo sin que en ese periodo haya tenido préstamos activos ni nuevos. Tras la anonimización, sus préstamos se conservan sin datos identificativos y el vínculo préstamo-persona se elimina.
- **FR-035**: El sistema MUST permitir al personal anonimizar manualmente los datos de una persona prestataria a petición de esta (derecho de supresión), con el mismo efecto que la anonimización automática.
- **FR-036**: El sistema MUST impedir la anonimización (automática o manual) de una persona que tenga préstamos activos; la anonimización queda pendiente hasta que se registren todas las devoluciones.
- **FR-037**: Tras anonimizar a una persona, el sistema MUST seguir mostrando sus préstamos en el historial del ejemplar (FR-025) con fechas y estado, pero sin ningún dato que permita identificar a la persona.

**Corrección de operaciones**

- **FR-038**: El sistema MUST permitir al personal anular o corregir una operación registrada recientemente sobre un ejemplar (préstamo, devolución o retirada), indicando obligatoriamente un motivo.
- **FR-039**: Cada anulación o corrección MUST quedar registrada con su fecha y hora y su motivo; la operación original NO se borra, se marca como "anulada".
- **FR-040**: Tras una anulación o corrección, el sistema MUST recalcular el estado del ejemplar (disponible / prestado / retirado) y, cuando proceda, el estado, las fechas y el indicador de retraso de los préstamos afectados, así como el recuento de préstamos activos de la persona (FR-033).
- **FR-041**: El historial del ejemplar (FR-025) MUST mostrar las operaciones anuladas identificadas como tales, de forma que se vea qué se registró y qué se corrigió.

### Key Entities *(include if feature involves data)*

- **Título**: obra catalogada. Atributos: título, autor, ISBN (opcional), editorial (opcional), año (opcional), materia/categoría (opcional). Relación: tiene uno o varios Ejemplares.
- **Ejemplar**: copia física de un Título. Atributos: código de ejemplar (único en el catálogo), estado (disponible / prestado / retirado), motivo de retirada (cuando aplica). Relación: pertenece a un Título; participa en cero o varios Préstamos a lo largo del tiempo.
- **Persona prestataria**: quien recibe un ejemplar en préstamo. Atributos: documento identificativo (clave de identificación), nombre, contacto (opcional), estado (activa / anonimizada), fecha del último préstamo. La ficha se crea en el primer préstamo y se reutiliza; pasa a "anonimizada" a los 2 años sin préstamos (FR-034) o a petición (FR-035). No incluye carné ni estado de socio.
- **Préstamo**: entrega temporal de un Ejemplar a una Persona prestataria. Atributos: fecha de préstamo, fecha límite de devolución, fecha real de devolución (vacía mientras está activo), indicador y días de retraso, marca temporal de registro de cada operación, estado del registro (efectivo / anulado). Relación: vincula un Ejemplar y una Persona prestataria; el vínculo con la persona se elimina cuando esta se anonimiza, y el préstamo se conserva sin identificación.
- **Corrección de operación**: anulación o rectificación de una operación previa (préstamo, devolución o retirada). Atributos: tipo (anulación / corrección), motivo, fecha y hora. Relación: referencia a la operación original, que queda marcada como "anulada".
- **Gestión de reclamación**: intento de contacto con el prestatario por un préstamo vencido. Atributos: fecha, medio (teléfono / correo electrónico / presencial / otro), notas (opcional). Relación: pertenece a un Préstamo; se anonimiza con la persona.
- **Configuración de préstamo**: parámetros operativos globales. Atributos: plazo de préstamo en días naturales (por defecto 15), número máximo de préstamos activos por persona (por defecto 3).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El personal puede registrar un préstamo completo (localizar ejemplar disponible + identificar persona + confirmar) en menos de 1 minuto.
- **SC-002**: El personal puede registrar una devolución en menos de 30 segundos desde que localiza el ejemplar.
- **SC-003**: Una búsqueda en el catálogo devuelve resultados en menos de 2 segundos con un fondo de al menos 20.000 títulos y 50.000 ejemplares.
- **SC-004**: En todo momento, la lista de préstamos activos coincide exactamente con los ejemplares en estado "prestado" (cero descuadres entre estado del ejemplar y préstamos abiertos).
- **SC-005**: El 100 % de los préstamos registrados tienen fecha límite calculada automáticamente; el personal no introduce fechas límite a mano.
- **SC-006**: El personal identifica los préstamos vencidos del día en una sola pantalla, sin exportar ni cruzar datos manualmente.
- **SC-007**: Tras registrar una devolución, el ejemplar vuelve a aparecer como disponible en la búsqueda en menos de 2 segundos.
- **SC-008**: Una persona recién incorporada al personal completa las tareas básicas (alta de título, préstamo y devolución) tras menos de 30 minutos de formación.
- **SC-009**: Ningún título o ejemplar con préstamos previos puede eliminarse del sistema (cero pérdidas del historial de préstamos del ejemplar).
- **SC-010**: Transcurridos 2 años desde el último préstamo de una persona sin préstamos activos, el sistema no conserva ningún dato que permita identificarla; sus préstamos anteriores siguen disponibles de forma anonimizada en el historial del ejemplar.
- **SC-011**: El personal corrige una operación mal registrada (préstamo, devolución o retirada) desde la propia aplicación, sin intervención técnica, y el estado del ejemplar queda correcto de inmediato, conservándose el rastro de la operación anulada.
- **SC-012**: Para cada préstamo vencido, el personal ve en la propia lista de vencidos si ya se ha reclamado y la fecha de la última gestión, sin abrir otra pantalla.

## Assumptions

- El sistema es una aplicación interna de la biblioteca; no hay portal ni acceso para el público en esta versión.
- Quedan fuera de alcance: gestión de socios con carné y su ciclo de vida, reservas de ejemplares en cola, renovaciones de préstamo, cálculo o cobro de multas y sanciones, importación/migración masiva de datos desde ficheros o sistemas externos, y generación o envío de comunicaciones/avisos a prestatarios.
- La reclamación de préstamos vencidos (llamadas, correos, cartas) se realiza fuera del sistema; este solo registra que se hizo, cuándo y por qué medio.
- No existe un sistema de préstamos previo: el catálogo (títulos y ejemplares), los prestatarios y los préstamos se crean desde cero mediante entrada manual en el sistema. Se asume una carga inicial del fondo hecha a mano por el personal.
- Los ejemplares llevan un código impreso/etiquetado. El sistema admite lectores de código de barras que introducen ese código como texto, sin integración específica con el dispositivo. El etiquetado del fondo es responsabilidad del personal y puede hacerse de forma progresiva; los ejemplares aún sin etiqueta se localizan por búsqueda de título.
- El plazo de préstamo es un único valor global en días naturales (por defecto 15) y no varía por tipo de material ni por perfil de persona en esta versión.
- Las fechas límite se calculan en días naturales, sin ajustar por fines de semana ni festivos.
- El ISBN puede faltar (fondo antiguo) y no se exige que sea único; el sistema solo avisa de posibles duplicados.
- Los datos mínimos de la persona prestataria son documento y nombre; el contacto es opcional. Una persona se identifica de forma unívoca por su documento.
- La conservación de datos personales se rige por RGPD/LOPD: los datos identificativos de prestatarios se anonimizan a los 2 años del último préstamo (o antes, a petición), y los registros de préstamo se conservan de forma anonimizada con fines estadísticos y de trazabilidad del ejemplar.
- Las personas con préstamos vencidos pueden seguir tomando prestados ejemplares mientras no superen el tope de préstamos activos; el sistema muestra un aviso de los vencidos, pero el bloqueo solo se aplica por cantidad (FR-033), no por retraso.
- El sistema se usa en puestos de trabajo compartidos sin inicio de sesión individual; no hay control de acceso por usuario ni por rol dentro del sistema. El acceso al equipo y la asignación de tareas del personal se gestionan fuera del sistema.
- La biblioteca opera en una única sede; no hay gestión multi-sucursal ni traslados de ejemplares entre sedes.
- El volumen esperado es del orden de decenas de miles de títulos y ejemplares y de cientos de préstamos activos simultáneos.
- Los parámetros de préstamo (plazo y máximo por persona) son un único juego de valores global; cambiarlos es una tarea de administración que el sistema no restringe por rol.
