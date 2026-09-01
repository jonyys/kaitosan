# なおす II — De SRS a Can-do, con un N5 oficial

> Kaitosan · plan de trabajo · 6 bloques · 18 fases

Sustituir el SRS como **motor de progresión del profesor** por un modelo de
**can-do** (objetivos comunicativos), dejar el temario siendo **exactamente el
N5 oficial**, y **reubicar** el SRS de vocabulario y gramática donde tiene
sentido: un juego web por lecciones, al estilo del de kanji, que Laura maneja
por su cuenta y que el profesor solo **consulta**.

Todo el contenido nuevo (traducciones, notas de uso, textos de can-do) lo
**genera Claude**. Nada se escribe a mano.

Cada fase es un arreglo cerrado, verificable con un comando y commiteable solo.
El orden es por dependencia. La ejecución (agentes, paralelismo, gates) está en
`PLAN_CANDO_N5_EJECUCION.md`; el estado vivo, en `PLAN_CANDO_N5_PROGRESO.md`.

---

## Idea en una frase

El SRS no se elimina: **cambia de dueño**.

| | Hoy | Después |
|---|---|---|
| SRS de **kanji** | lo mueve la práctica web (`/japones/kanjis/practicar`) | **igual, intacto** |
| SRS de **vocabulario / gramática** | lo mueve el profesor al cerrar la sesión (extractor LLM → SM-2) | lo mueve un **juego web por lecciones** (nuevo), como el de kanji |
| Progresión del **profesor** | `reps >= 2` por ítem, `due_count`, `_fraccion_aprendida` | **can-dos** por unidad, calificados por el extractor |
| El profesor y una palabra | la introduce si no está "dominada" en SRS | mira el `estado` del juego: **sabida** → la usa en japonés directamente; **no sabida** → da el significado para andamiar el can-do; **si Laura pregunta** → lo dice igual, como un profesor |
| El temario | 254 palabras + 75 puntos elegidos a mano | **exactamente** la lista N5 oficial; web y `curriculum.py` no pueden divergir |

---

## Qué es "el N5 oficial" aquí

La JLPT no publica listas desde 2010. La referencia es la **reconstrucción de
tanos.co.uk** del listado oficial pre-2010 (nivel 4 ≈ N5), que es lo más cercano
a oficial que existe y de donde derivan casi todos los mazos y cursos.

- **Vocabulario:** `jamsinclair/open-anki-jlpt-decks → src/n5.csv` — 717
  palabras, MIT, derivada de tanos. Trae `expression, reading, meaning, tags`.
- **Gramática:** tanos N5 (~80 puntos) como autoridad de pertenencia, con
  jlptsensei como contraste. No hay fichero limpio: Claude lo ensambla en la
  Fase 01 y lo versiona.

Autoritativo significa: al terminar el Bloque I,
`set(vocab en curriculum.py) == set(lista)` y lo mismo para gramática. Lo que no
está en la lista no está en el proyecto.

---

## Qué campos lleva cada ítem, y por qué

- **`reading` + `meaning`** — imprescindibles. `reading` viene del CSV;
  `meaning` se traduce EN→ES. Sin ellos el profesor no puede construir la frase
  del can-do con Laura.
- **`uso`** (cuándo y con quién se dice) — solo donde el matiz no es obvio:
  partículas, contadores, keigo, frases hechas, verbos de uso no evidente,
  falsos amigos. Lo genera **Claude** (modelo más fuerte que el `gpt-oss-120b`
  que enseña en vivo) y queda cacheado en el temario: es meter el criterio del
  modelo bueno donde lo lea el flojo, que en registro y matiz se equivoca fino
  y Laura no lo caza. Para una palabra transparente (水 = agua) se deja vacío.
- **`ejemplo` / `literal`** — **no** se generan para vocabulario. Kaito los
  improvisa en vivo (un 120B lo hace bien para N5) y el método de 3 pasos ya le
  pide un ejemplo *a medida de Laura*, que es mejor que uno enlatado. Los 254
  ítems que ya los traen se conservan.
- **Gramática** (~80 puntos) — sí lleva los cuatro campos: son pocos, son alto
  valor, y el juego de práctica de gramática necesita el `ejemplo` como pista.

---

## Estado de partida (no se rehace)

- **Modo sensei completo** (`PLAN_MODO_SENSEI.md`, implementado): diales de
  registro y de inmersión 1–4, tipología de corrección, método de 3 pasos,
  memoria episódica (`laura_episodios`, `kaito_anecdotas`), pronunciación Azure.
- **Temario** (`ai/sensei/curriculum.py`): 52 unidades — ~27 de vocab/gramática
  N5 + 11 de kanji N5 + **14 de N4/N3**. Hoy: 254 palabras N5, 75 puntos N5, y
  51 vocab + 80 gramática de N4/N3.
- **Páginas web de temario** (`/japones/vocabulario`, `/japones/gramatica`): de
  consulta, con barra de progreso y botón "marcar como aprendida". Sin práctica.
- **Práctica de kanji** (`japones_kanji_practica.html` +
  `/japones/kanjis/practicar`): canvas, pistas, autocalificación (q5 / q2) →
  `review(id, q, "kanji")`; siguiente ítem por `get_due_items(kind="kanji")`.
  **Es el patrón a copiar.**
- **SM-2** en `ai/sensei/srs.py` + `core/japanese_memory.py`
  (`review`, `get_due_items`). Las tres tablas ya tienen columnas SRS.

---

## Fuera de alcance

**Kanji — intocable.** Ni tablas, ni `kanji_n5.py`, ni rutas `/japones/kanjis*`,
ni su SRS. El juego nuevo copia su mecánica sin compartir código más allá de
`review()`/`get_due_items()`, ya genéricas por `kind`.

**N4 / N3 y superiores — se borran, no se aparcan.**

**Diseño visual de las páginas nuevas.** Heredan de
`partials/admin/_estilos.html` y de las páginas actuales.

**Calificar can-dos turno a turno.** Sigue vía extractor a posteriori.

---

# Bloque I — Reconciliar el temario al N5 oficial

Riesgo bajo, desbloquea todo. Al terminar, `curriculum.py` es la lista N5 y nada
más.

## 01 · 🟢 Fuentes de verdad + validador

**~80 líneas** · `data/` · `scripts/` · `tests/`
*Sin dependencias · bloquea a 02, 03*

- `data/n5_vocab.csv` — copia versionada de `open-anki-jlpt-decks/src/n5.csv`.
- `data/n5_grammar.csv` — Claude ensambla la lista de tanos N5 (~80 puntos:
  `jp` canónico + glosa breve EN), contrastada con jlptsensei. Se versiona.
- `scripts/validar_curriculum.py` — comprueba invariantes del temario y sale con
  código ≠ 0 si algo falla. Lo usarán las fases 02–06. Checks:
  · `jp` único en vocab y en gramática · japonés válido (regex kana/kanji) ·
  todo ítem tiene `kind`, `reading` y `meaning` · todo punto de gramática tiene
  `ejemplo` y `uso` · (tras Fase 06) todo `can_do.id` único.

**Verificación:** `python scripts/validar_curriculum.py` sale 0 sobre el temario
actual (con los checks aún tolerantes). `data/n5_vocab.csv` tiene 717 filas +
cabecera; `data/n5_grammar.csv`, entre 78 y 90.

## 02 · 🔴 Reconciliar el vocabulario del temario a la lista

**~200 líneas de script + regeneración de `curriculum.py`** · `scripts/reconciliar_vocab.py` · `ai/sensei/curriculum.py`
*Después de 01 · bloquea a 04, 05*

`curriculum.py` (parte de vocabulario) pasa a ser **exactamente** las 717
palabras. El script:
1. **Conserva** los ítems actuales cuyo `jp` esté en la lista, con su
   `ejemplo`/`literal`/`uso` escritos hasta ahora.
2. **Elimina** los ítems de vocabulario cuyo `jp` no esté en la lista.
3. **Añade** las palabras que faltan (~450+) con `reading` y `meaning` (traducido
   EN→ES por LLM en lotes). `ejemplo` y `literal` quedan **vacíos** para siempre
   (los improvisa Kaito); `uso` vacío hasta la Fase 05.
4. **Asigna** cada palabra a la unidad temática más afín: el LLM decide con la
   lista de unidades y sus nombres como contexto. Las que no encajen en ninguna
   van a una unidad nueva `vocabulario_n5_extra`.
5. Reescribe el bloque de vocabulario de `curriculum.py` de forma determinista
   (orden estable: por unidad, luego por `jp`). Los campos de texto de los ítems
   que ya existían (`meaning`, `ejemplo`, `literal`, `uso`, `frases_hechas`,
   `funcion`) se copian **carácter a carácter**. El diff sobre esos ítems debe
   ser solo de orden/posición, nunca de contenido.

**Verificación:** `tests/test_n5_reconciliacion.py` —
`set(jp de vocab en CURRICULUM) == set(jp de data/n5_vocab.csv)`; ningún `jp`
duplicado; todo ítem tiene `reading` y `meaning` no vacíos; los ítems que ya
existían y siguen en la lista conservan su `uso` textual.
`python scripts/validar_curriculum.py` → 0.

## 03 · 🟢 Reconciliar la gramática del temario a la lista

**~120 líneas** · `scripts/reconciliar_gram.py` · `ai/sensei/curriculum.py`
*Después de 01 · bloquea a 04, 05, 06*

Igual que 02 para `japanese_grammar` contra `data/n5_grammar.csv`. Los ~75
puntos actuales están bien construidos; esto sobre todo **quita** los de N4/N3 y
**añade** los pocos N5 que falten, con `jp` + `meaning`; `ejemplo`/`literal`/`uso`
vacíos, los rellena la Fase 05.

**Verificación:** `tests/test_n5_reconciliacion.py::test_gramatica` —
`set(grammar_point) == set(data/n5_grammar.csv)`. `validar_curriculum.py` → 0
(con el check de `ejemplo`/`uso` de gramática aún tolerante).

## 04 · 🟢 Borrar unidades vacías y purgar la BD

**~40 líneas** · `ai/sensei/curriculum.py` · `core/japanese_memory.py` · `app.py`
*Después de 02 y 03*

- Tras reconciliar, las 14 unidades N4/N3 se quedan sin ítems. Eliminarlas de
  `CURRICULUM`. Revisar que ningún `prerequisito` apunte a una borrada.
- `app.py:_temario_unidades()`: quitar el arrastre de nivel `N5→N4→N3`
  (`nivel_re`, ~líneas 1082-1089). La web deja de tener selector de nivel y
  **renderiza el temario desde `CURRICULUM`** — web y curriculum no pueden
  divergir.
- `JapaneseMemory.purgar_fuera_de_temario(jps_vocab, jps_gram)`: borra filas de
  `japanese_vocabulary`/`japanese_grammar` cuyo texto no esté en el temario N5
  **y** tengan `first_taught_session_id IS NULL`. Lo que Laura pidió en sesión
  se respeta. Idempotente, se corre una vez al desplegar.

| Fila en BD | ¿Se borra? |
|---|---|
| Ítem del temario N5 (con o sin progreso de Laura) | No |
| Ítem que Laura pidió en sesión (`first_taught_session_id` no nulo) | No — va a "unidad extra" |
| Ítem que solo existía por el temario viejo N4/N3 | Sí |

**Verificación:** `tests/test_n5_reconciliacion.py::test_sin_n4n3` —
`len(CURRICULUM)` == unidades N5 esperadas; ninguna unidad con `items == []`;
ningún nombre de unidad con `N4`/`N3`. Test de `purgar_fuera_de_temario` sobre
una BD sembrada: borra el ítem N4 huérfano, conserva el N5 y el pedido en sesión.
`GET /japones/vocabulario` → 200 sin selector de nivel.

---

# Bloque II — Contenido didáctico, generado por Claude

Una sola fase. Solo `uso` de vocabulario donde el matiz lo pide, y los cuatro
campos de la gramática. Sin `ejemplo`/`literal` de vocabulario, sin intervención
humana.

## 05 · 🔴 Notas de uso del vocabulario + gramática completa

**~150 líneas de script + regeneración** · `scripts/generar_contenido.py` · `ai/sensei/curriculum.py`
*Después de 02 y 03 · bloquea a 12, 13*

**Vocabulario:** para cada ítem N5 sin `uso`, el LLM juzga primero si la palabra
es sensible a matiz/registro (partícula, contador, keigo, frase hecha, expresión,
verbo de uso no obvio, falso amigo). Si lo es → genera `uso` (español, el matiz,
no la traducción). Si es transparente → lo deja vacío. **No** genera `ejemplo`
ni `literal`.

**Gramática:** para cada punto que entró sin ellos en la Fase 03, genera
`meaning` afinado + `ejemplo` (frase N5 que usa el patrón, solo kana/kanji) +
`literal` (desglose con `/`) + `uso`.

**Validación integrada** (no es fase aparte, el volumen es pequeño):
- estructural, sobre todo lo generado: `ejemplo` de gramática contiene el
  patrón; `uso` en español sin japonés fuera de 「」; `meaning` sin inglés.
- LLM-juez (`strict`, modelo principal) **solo** sobre la gramática (~80) y las
  `uso` generadas de vocabulario (no sobre las 717): ¿correcto, de nivel N5,
  aporta algo más que la glosa? `ok` / `regenerar` + motivo.
- Los `regenerar` se rehacen una vez; lo que siga fallando se lista en la salida
  y se acepta (o no) en el informe de la fase.

Se escribe directo a `curriculum.py` (orden determinista, campos existentes
carácter a carácter).

**Verificación:** `tests/test_curriculum_contenido.py` — todo punto de gramática
N5 tiene `ejemplo` y `uso` no vacíos; las `uso` de vocabulario generadas pasan
los checks estructurales. `python scripts/validar_curriculum.py` → 0 (checks de
contenido ya estrictos). `pytest -q` verde.

---

# Bloque III — Motor can-do

Sustituye SM-2 como progresión del profesor. El SRS de vocab/gram deja de
moverlo el profesor (lo recoge el Bloque IV); el de kanji sigue igual.

## 06 · 🟢 Can-dos por unidad (generados)

**~100 líneas** · `scripts/generar_candos.py` · `ai/sensei/curriculum.py`
*Después de 03 · bloquea a 07, 09, 11*

El LLM genera 2–5 can-dos por unidad, adaptando **JF Can-do** (Japan Foundation),
CEFR y ACTFL Can-Do al contenido real de esa unidad. Formato "Puedo…". `id`
estable con prefijo de unidad.

```python
'can_dos': [
  {'id': 'comida_gustos', 'texto': 'Puedo decir qué comida y bebida me gusta y no'},
  {'id': 'comida_pedir',  'texto': 'Puedo pedir algo señalando la carta'},
  {'id': 'comida_precio', 'texto': 'Puedo preguntar cuánto cuesta y entender un precio'},
]
```

Pequeño pase de validación LLM: ¿cada can-do es alcanzable con el vocabulario y
la gramática de su unidad? Si no, lo reescribe.

**Verificación:** `tests/test_cando_motor.py::test_candos` — toda unidad N5 tiene
≥ 2 can-dos; todos los `id` únicos; `validar_curriculum.py` → 0.

## 07 · 🟢 Esquema de BD: progreso de can-dos y estado de ítem

**~60 líneas** · `core/japanese_memory.py` · `tests/`
*Después de 06 · bloquea a 08, 09, 11*

```sql
CREATE TABLE can_do_progreso (
    can_do_id     TEXT PRIMARY KEY,
    estado        TEXT DEFAULT 'no_intentado',  -- no_intentado | en_progreso | dominado
    veces_ok      INTEGER DEFAULT 0,
    ultima_sesion INTEGER,
    nota          TEXT
);
```

- `estado_item(jp, kind) -> 'sabido'|'en_progreso'|'nuevo'` — extraer la lógica
  que ya vive en `app.py:_temario_unidades()` (`aprendida`/`en_curso`/`nueva`
  desde `status`+`reps`) a `japanese_memory.py`, para que la lean también el
  profesor y el boletín. Un solo sitio.
- `set_can_do(id, resultado, session_id)` — reglas: `conseguido` en 2 sesiones
  distintas → `dominado`; `error`/`parcial` tras `dominado` → baja a
  `en_progreso`.
- `can_dos_progreso() -> dict`, `fraccion_can_dos(unit_id) -> float`.

**Verificación:** `tests/test_cando_motor.py::test_set_can_do` —
`set_can_do('x','conseguido',1)` → `en_progreso, veces_ok=1`; repetir con
`session_id=2` → `dominado`; luego `set_can_do('x','error',3)` → `en_progreso`.
`estado_item()` devuelve el mismo string que hoy pinta la página de temario
(test comparativo).

## 08 · 🟢 El extractor califica can-dos, no ítems SRS

**~40 líneas** · `ai/prompts/extraccion_sesion.txt` · `ai/sensei/profesor.py`
*Después de 07*

`extraccion_sesion.txt`: sustituir el campo `reviewed` por

```json
"can_dos": [
  {"id": "comida_pedir", "resultado": "conseguido|parcial|no_intentado",
   "evidencia": "Laura dijo 「コーヒーをください」 sin que Kaito se lo diera"}
]
```

Se le pasan al extractor los can-dos activos de la sesión y se le exige **cita
textual** como `evidencia`.

En `_ejecutar_extraccion()`:
- Fuera el bucle `reviewed` → `_QUALITY_MAP` → `review()`, la "rama de rescate"
  (`review(item,3)`) y el "aprobado de oficio". **Si el extractor no devuelve
  `can_dos`, no se toca ningún can-do.**
- Nuevo bucle: `jap_memory.set_can_do(id, resultado, session_id)` por can-do.
- `new_items`, `sin_corregir`, `episodios`, `kaito_dijo` intactos.

`ai/sensei/srs.py` y `review()`/`get_due_items()` **se quedan** — los usa el
kanji y los usará el Bloque IV. Solo desaparecen sus llamadas desde el profesor.

**Verificación:** `tests/test_cando_extractor.py` — una transcripción sembrada
donde Laura pide comida en japonés deja `comida_pedir` en `en_progreso` con su
`evidencia`. Con `data=None` (extractor caído) ningún can-do cambia y no hay
excepción. `grep` no encuentra `review(` ni `get_due_items(` en el flujo
vocab/gram de `profesor.py`.

## 09 · 🔴 Orquestación del profesor por can-do

**~70 líneas** · `ai/sensei/profesor.py` · `core/config.py`
*Después de 06, 07, 08 · bloquea a 10*

- `_montar_estado()` — el FOCO se reorganiza alrededor del **can-do activo** (el
  primer no dominado de la unidad abierta), no de la cola `due`:
  · unidad abierta y sus can-dos (dominados / en progreso / pendientes),
  · can-do de hoy + los ítems de vocab/gramática que necesita, cada uno con su
    `estado` (`sabido`/`en_progreso`/`nuevo`),
  · puntos débiles (ya existe),
  · cada N sesiones, chequeo de óxido: muestra de ítems `sabido` de unidades
    pasadas.
- `_rotar_due()` y `_foco_due_vocab/_foco_due_gram` → fuera; los sustituye la
  selección de ítems del can-do activo.
- `_nivel_inmersion()` — sigue leyendo `vocab_by_status`, que ahora refleja lo
  llevado a `sabido` en el juego. Umbrales `(15,40,80)` se revisan con datos.
- `THROTTLE_DUE` / `due_count` → tamaño de la lista de puntos débiles.
  `MAX_ITEMS_NUEVOS` limita ítems por can-do.
- `siguiente_items_nuevos()` (curriculum) → devuelve los ítems que pide el
  can-do activo y que Laura no tiene, no un recorrido del temario.
- `unidad_actual()` / `_fraccion_aprendida()` → `fraccion_can_dos(unit_id)`.
  Unidad completa a **≥ 80 %** de can-dos dominados.

**Verificación:** `tests/test_cando_motor.py::test_foco` — con una unidad abierta
y can-dos a 0, `_montar_estado()` devuelve un FOCO que nombra el primer can-do y
sus ítems con marcador de estado, y no menciona "cola de repaso". Sembrando 80 %
de can-dos `dominado`, `unidad_actual()` avanza. `simulate_sensei.py` corre sin
error 5 turnos.

## 10 · 🟢 El profesor trata "sabido" y "no sabido" como un profesor

**~25 líneas de prompt** · `ai/prompts/profesor_japones.txt` · `ai/sensei/profesor.py`
*Después de 09*

En `_lineas_foco()`, añadir a la línea del ítem su marcador `[sabida]` /
`[en progreso]` / `[nueva]`. Regla nueva en `== MÉTODO DE ENSEÑANZA ==`:

```
Cada palabra del FOCO lleva su estado: [sabida] / [en progreso] / [nueva].
  - [sabida] → úsala en japonés directamente, sin decir antes qué significa.
  - [nueva] / [en progreso] → la primera vez que la uses, di qué significa,
    para que Laura pueda construir con ella la frase del can-do.
  - Si Laura pregunta qué significa —da igual el estado— díselo sin rodeos.
    Eres su profesor, no un examen.
```

**Verificación:** `tests/test_cando_motor.py::test_marcador_estado` — el FOCO de
un ítem `sabido` lleva `[sabida]` y el de uno `nuevo` lleva `[nueva]`. Prueba
manual anotada en el informe: sesión forzada, Kaito usa el `sabido` sin traducir
y glosa el `nuevo`.

## 11 · 🟢 Boletín: pantalla de progreso can-do

**~90 líneas** · `app.py` · `templates/japones_boletin.html` · enlace en `japones.html`
*Después de 07 (y 06)*

Ruta `/japones/boletin`, solo lectura:
- can-dos por unidad con estado (○ / ◐ / ●) y sesión en que se consiguió,
- inventario N5: barras `vocabulario sabido / 717`, `gramática / ~80`
  (kanji se enlaza a su página),
- puntos débiles activos.
Reutiliza `.prog` / `.voc-*` de `japones_temario.html`.

**Verificación:** `tests/test_juego_srs_web.py::test_boletin` — `GET
/japones/boletin` → 200; con datos sembrados, el % de can-dos y los contadores
de inventario coinciden con `SELECT COUNT(*)` por `estado`.

---

# Bloque IV — Juego SRS web de vocabulario y gramática, por lecciones

El SRS que el profesor soltó, ahora como juego que Laura maneja sola. Mecánica
calcada del de kanji, organizada por lección.

## 12 · 🔴 Práctica de vocabulario por lección

**~160 líneas** · `app.py` · `templates/japones_vocab_practica.html`
*Después de 05 · bloquea a 14*

Ruta `/japones/vocabulario/practicar?unidad=<id>`, patrón de
`japones_kanji_practica.html`:
- **GET**: siguiente ítem de la unidad por `get_due_items(kind="vocabulario")`
  filtrado a la unidad; si no hay vencidos, uno nunca practicado. Ejercicio
  alternando sentido: ES→japonés y japonés→ES. Pista: lectura (el `ejemplo`
  suele estar vacío, no se depende de él).
- **POST**: autocalificación ("Lo sabía" q5 / "Casi" q3 / "No" q1) →
  `review(item_id, quality, "vocabulario")`; `add_item()` antes si no hay fila.
- Cabecera: "N ítems por repasar en esta lección".
- `japones_temario.html` gana un botón "Practicar" por unidad.

**Verificación:** `tests/test_juego_srs_web.py::test_practica_vocab` — POST de 5
calificaciones cambia `reps`/`interval_days`/`next_review`/`status` según SM-2
(igual que kanji); q1 vuelve a salir; q5 ×3 → `status='learned'`. `GET
...?unidad=<id>` → 200 con un ítem de esa unidad.

## 13 · 🔴 Práctica de gramática por lección

**~130 líneas** · `app.py` · `templates/japones_gram_practica.html`
*Después de 05 · bloquea a 14*

Misma mecánica, ruta `/japones/gramatica/practicar?unidad=<id>`,
`kind="gramatica"`. Ejercicio: frase con hueco o forma base → elegir/escribir la
conjugación o partícula; pista = `uso` + `ejemplo` (aquí sí presentes, Fase 05).
`review(id, q, "gramatica")`.

**Verificación:** `tests/test_juego_srs_web.py::test_practica_gram` — igual que
12 sobre `japanese_grammar`; `mastery` se recalcula.

## 14 · 🟢 Conectar el estado del juego con el profesor

**~20 líneas** · `core/japanese_memory.py` · `app.py`
*Después de 10, 12, 13 — cierra el círculo con el Bloque III*

`estado_item()` (Fase 07) ya deriva de `status`/`reps`, que ahora mueve el
juego. Verificar el circuito completo y quitar duplicación: temario, boletín y
profesor leen `estado_item`.

Los botones "marcar como completa" / "marcar unidad como aprendida"
(`_completar_item`, `_completar_unidad`, `marcar_completo`) **se mantienen**: son
el atajo "ya me lo sé, no me lo preguntes". Escriben el mismo `status` que el
juego, conviven sin conflicto.

**Verificación:** `tests/test_juego_srs_web.py::test_circuito` — llevar un ítem a
`learned` vía POST de práctica y comprobar que `estado_item()` lo da `sabido` y
que aparece `[sabida]` en el FOCO del profesor. Botón `marcar_completo` sobre
otro ítem → mismo `sabido`.

---

# Bloque V — Que se sienta una persona

Los huecos reales tras el modo sensei. Prompt + un campo de BD cada uno.

## 15 · 🟢 Notas del profe

**~20 líneas** · `ai/prompts/extraccion_sesion.txt` · `core/japanese_memory.py` · `ai/sensei/profesor.py`
*Después de 08 (esquema del extractor ya cambiado)*

Campo `nota_profe` en el JSON del extractor: 1–2 frases sobre **cómo va Laura
como alumna** (tendencias, ánimo, ritmo), no qué se trabajó. Columna nueva
`nota_profe` en `japanese_sessions`; las 3 últimas al `RECUERDAS_DE_LAURA` bajo
"Cómo va Laura".

**Verificación:** `tests/test_persona.py::test_nota_profe` — extractor sembrado
con dudas de は/が deja una `nota_profe` no vacía; `_montar_estado()` la incluye
en el bloque de recuerdos.

## 16 · 🟢 Deberes entre sesiones

**~25 líneas** · `ai/prompts/profesor_japones.txt` · `ai/prompts/extraccion_sesion.txt` · `core/japanese_memory.py`
*Después de 15*

Al cerrar, Kaito propone **una** tarea pequeña para la semana. El extractor la
captura en `deberes`, se guarda, y en el siguiente `entrar()` entra primera en
el FOCO: Kaito pregunta qué tal fue antes de nada.

**Verificación:** `tests/test_persona.py::test_deberes` — cerrar sesión guarda
`deberes`; el FOCO de la siguiente sesión lo nombra en primera posición.

## 17 · 🟢 Arco de sesión

**~15 líneas** · `ai/sensei/profesor.py` · `ai/prompts/profesor_japones.txt`
*Después de 09*

`_montar_estado()` añade una pista de fase por número de turno:
`calentamiento` (1–2: charla, deberes, vida de Laura) → `foco` (cuerpo) →
`cierre` (si Laura se despide). El prompt ya tiene el ritual de cierre; esto le
da la entrada suave.

**Verificación:** `tests/test_persona.py::test_arco` — el FOCO de los turnos 1–2
lleva la marca `calentamiento` y no fuerza ejercicio de temario; el del turno 4
lleva `foco`.

---

# Bloque VI — Cierre

## 18 · 🟢 Limpieza final

**~30 líneas netas (borrado)** · varios · tests
*Después de todo lo demás*

- Reescribir `tests/test_foco_nuevos.py`, `tests/test_selector_conexiones.py`,
  `tests/test_rotacion_foco.py` (asumen `due_count`/`reps`/rotación de cola).
- Quitar de `simulate_sensei.py`/`simulate_conv.py` las líneas "Ítems en cola de
  repaso (SRS hoy)".
- `japones.html` (hub): tarjeta `due_today` → "can-dos dominados" o "palabras
  sabidas"; enlazar boletín y prácticas.
- `config.py`: `THROTTLE_DUE` marcado "solo kanji"; revisar
  `NIVEL_INMERSION_UMBRALES`.

**Verificación:** `pytest -q` entero en verde. `grep` sin referencias vivas a
`due_count` en el flujo vocab/gram del profesor. `python simulate_sensei.py`
corre una sesión completa sin error.

---

# Decidido

- **Vocabulario:** las 717 de open-anki, autoritativas. Nada fuera de la lista
  sobrevive en `curriculum.py`.
- **Gramática:** tanos N5 (~80) como autoridad de pertenencia.
- **Campos por ítem:** `reading` + `meaning` siempre; `uso` de vocabulario solo
  donde el matiz lo pide; `ejemplo`/`literal` de vocabulario **no se generan**
  (Kaito los improvisa); gramática lleva los cuatro campos.
- **Todo el contenido lo genera Claude.** Sin escritura manual. La calidad la
  asegura la validación integrada en la Fase 05.
- **`marcar_completo`:** el botón se queda (Fase 14).
- **Borrados:** solo unidades y filas N4/N3 (Fase 04). Lo que Laura pidió en
  sesión se respeta.

# Knobs — se afinan con datos, no ahora

**Chequeo de óxido** (Fase 09): cada cuántas sesiones se cuela vocabulario viejo
`sabido` en el FOCO. Arranca en 1 de cada 5.

**Umbrales de inmersión** (Fase 09): `(15, 40, 80)` — con el juego Laura acumula
`sabido` mucho más rápido, casi seguro suben. No se sabe a cuánto hasta ver el
ritmo real.

**Ítems dudosos que sobrevivan a la validación de la Fase 05:** si tras la
regeneración quedan `uso` o puntos de gramática que el juez marca `regenerar`,
se listan y se aceptan (o no) en el informe de esa fase, no bloquean el plan.

---

*Plan derivado de `main` (0883ef6) con el modo sensei ya implementado.*
*Bloque I: reconciliar · II: contenido · III: motor can-do · IV: juego SRS web · V: persona · VI: cierre.*
*Fuera de alcance por decisión: kanji (intacto), N4/N3 (borrados).*
