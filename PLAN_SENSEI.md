# Plan de mejora del modo Sensei (Kaitosan)

> **Cómo usar este documento.** Cada fase está pensada para ejecutarse de forma
> **independiente por un agente con contexto vacío**, en orden (Fase 1 → 7). Antes
> de ejecutar cualquier fase, el agente **debe leer la sección "0. Contexto compartido"**
> y luego la fase concreta. Cada fase indica qué archivos leer, el estado de partida
> (qué dejó hecho la fase anterior), los cambios paso a paso y cómo verificar.
>
> **Decisiones ya tomadas (firmes, no reabrir):**
> - **Eliminar `japanese_skills`** y basar el desbloqueo del temario en el SRS real.
> - **Eliminar TODAS las tablas zombi**: `japanese_skills`, `japanese_topics`, `japanese_profile`.
> - **Gating por prerequisito al 0.75**: una unidad se abre cuando el 75 % de su unidad
>   prerequisito está "aprendida" (`reps >= 2`).
> - **Ampliar el currículo** cubriendo N5 → N4 → N3 siguiendo la secuencia de libros
>   oficiales (Genki I/II para N5-N4; listas estándar N3).
> - **Eliminar la evaluación de pronunciación**: con Whisper el transcript siempre llega
>   bien escrito (kanji/kana correctos), así que comparar IPA no aporta señal útil.
> - **Ítems nuevos por sesión: 2 (configurable hasta 3).**
> - **Profesor particular**: durante la sesión manda Laura. El profesor atiende sus peticiones
>   (aprender algo concreto, reforzar lo que le cuesta, explorar un tema que le interese) y enseña
>   el vocabulario que surja **igual** que uno del temario (método de 3 pasos + SRS). Retoma la
>   lección normal cuando Laura ya lo domina o quiere cambiar. (Fase 8.)

---

## 0. Contexto compartido (leer SIEMPRE antes de cualquier fase)

**Qué es.** Kaitosan es un robot con IA (Flask + SocketIO) que, entre otras cosas, tiene un
"modo sensei": un profesor de japonés conversacional y **hablado** para una usuaria llamada
Laura. La app arranca en `app.py`; el orquestador de conversación es `core/brain.py`.

**Piezas del modo sensei:**
- `ai/sensei/profesor.py` — clase `ProfesorJapones`: ciclo de vida (`entrar`/`salir`), turno de
  conversación (`responder_turno`), y cierre con extracción por LLM (`cerrar_sesion_y_extraer`).
- `ai/sensei/curriculum.py` — `CURRICULUM` (temario maestro por unidades) y
  `siguiente_item_nuevo()` (elige el próximo ítem nuevo a enseñar).
- `ai/sensei/srs.py` — algoritmo SM-2 (`sm2`) para repetición espaciada.
- `core/japanese_memory.py` — capa de datos SQLite del japonés (vocabulario, gramática,
  sesiones) + SRS (`add_item`, `review`, `get_due_items`, `get_item_id`, `resumen_perfil`,
  `obtener_perfil_completo`, `guardar_resumen_sesion`).
- `ai/prompts/profesor_japones.txt` — prompt del profesor (voice-first, sin romaji/kana fuera de 【】).
- `ai/pronunciation.py` + `ai/japanese_ipa.py` — evaluación de pronunciación por IPA (se ELIMINA en la Fase 3).
- `simulate_sensei.py` — **banco de pruebas sin Flask**: simula una sesión completa e imprime
  el estado de la BD antes/después. Es la herramienta principal de verificación.

**Flujo de una sesión sensei (resumido):**
1. `brain.responder()` detecta "modo sensei" → `profesor.entrar()` abre fila en `japanese_sessions`.
2. Cada turno: `profesor.responder_turno(msg)` monta el estado (RECUERDAS + FOCO) y llama al LLM.
   El "FOCO" incluye repasos SRS vencidos + un ítem nuevo de `siguiente_item_nuevo()`.
3. Al despedirse: `profesor.salir()` → `cerrar_sesion_y_extraer()` → un LLM extrae del transcript
   un JSON (`summary`, `reviewed[]`, `new_items[]`) y actualiza el SRS.

**Base de datos:** `data/kaito.db` (SQLite). Las tablas japonesas se crean en
`JapaneseMemory._inicializar_tablas()`.

**Cómo verificar cualquier cambio (comando base):**
```bash
python simulate_sensei.py --clean      # borra datos japoneses y simula una sesión completa
python simulate_sensei.py              # simula sin borrar (acumula progreso entre ejecuciones)
```
Requiere `.env` con `GROQ_API_KEY` (y opcionalmente `GEMINI_API_KEY`). Si no hay red/LLM,
las partes de estructura de BD y currículo se pueden validar igualmente leyendo el código y la BD.

**Tests relevantes:** `python -m pytest tests/test_herramientas.py` (usa `obtener_perfil_completo`).

**Nota sobre números de línea:** las referencias `archivo:línea` de este plan son aproximadas
y pueden haberse desplazado por fases anteriores. Confirma siempre con lectura/grep antes de editar.

**Restricción de diseño (voice-first):** el profesor NUNCA menciona texto escrito, kana ni romaji;
todo japonés va entre 【】. La enseñanza de escritura/lectura de kana/kanji está **fuera de alcance**.

---

## Diagnóstico (resumen de los problemas que este plan resuelve)

| # | Problema | Fase |
|---|----------|------|
| 1 | `japanese_skills` se lee pero nunca se escribe → currículo congelado en la Unidad 0 (solo saludos). | Fase 1 |
| 2 | Tablas muertas `japanese_skills`, `japanese_topics`, `japanese_profile` (se leen y se pasan a `admin.html`, pero **ningún template las renderiza**; topics/profile tampoco se escriben nunca). | Fase 1 |
| 3 | Currículo corto (solo parte de N5) y sin cobertura N4/N3. | Fase 2 |
| 4 | Pronunciación inútil: Whisper ya normaliza la escritura, así que comparar IPA no detecta errores. | Fase 3 |
| 5 | `add_item`/`review` viven dentro de la extracción; si el JSON falla, no entra nada al SRS. | Fase 4 |
| 6 | 1 solo ítem nuevo por sesión, sin balance repaso/nuevo. | Fase 5 |
| 7 | `weak_points = errors>2` absoluto; `mastery` confuso; extracción en hilo de timer. | Fase 6 |
| 8 | `provider_ligero` vestigial; conversación de `simulate` irreal. | Fase 7 |
| 9 | El prompt prohíbe salir del temario y redirige las peticiones de Laura → no actúa como profesor particular. | Fase 8 |

---

# FASE 1 — Desbloquear la progresión (eliminar tablas zombi + gating por prerequisito 0.75)

**Objetivo.** Que el temario avance más allá de los saludos. Se eliminan las tres tablas zombi
(`japanese_skills`, `japanese_topics`, `japanese_profile`) y se sustituye el gating por porcentaje
inexistente por un gating derivado del SRS real: una unidad se abre cuando el **75 %** de su unidad
prerequisito está "aprendida".

**Estado de partida.** Código original, sin cambios previos.

**Archivos a leer primero.**
- `ai/sensei/curriculum.py` (completo)
- `core/japanese_memory.py` (`_inicializar_tablas`, `resumen_perfil`, `obtener_perfil_completo`)
- `app.py` (ruta `/admin`, aprox. líneas 288-433)
- `ai/tools.py` (`consultar_progreso_japones`, aprox. línea 238)
- `simulate_sensei.py` (`limpiar_datos_japones`, aprox. línea 255)

### Paso 1.1 — Rediseñar el esquema de unidades y el gating en `curriculum.py`

En cada unidad de `CURRICULUM`, **sustituir** los campos `skill_requerida` y `umbral` por:
- `prerequisito`: `id` de la unidad que debe estar dominada antes (o `None` para la primera).
- `umbral_prereq`: fracción requerida (por defecto `0.75`).

Encadenar las unidades **secuencialmente** por ahora (cada unidad tiene como prerequisito la
anterior; `saludos_basicos` → `prerequisito: None`). La Fase 2 refinará estas cadenas.

**Reemplazar** `_gate_met` (y añadir el helper) por:

```python
UMBRAL_PREREQ_DEFECTO = 0.75

def _fraccion_aprendida(jap_memory, unit_id):
    """Fracción de ítems de una unidad que el alumno tiene 'aprendidos' (reps >= 2)."""
    unit = next((u for u in CURRICULUM if u["id"] == unit_id), None)
    if not unit or not unit["items"]:
        return 0.0
    aprendidas = 0
    with jap_memory._conectar() as conn:
        for item in unit["items"]:
            if item["kind"] == "vocabulario":
                row = conn.execute(
                    "SELECT reps FROM japanese_vocabulary WHERE word = ?", (item["jp"],)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT reps FROM japanese_grammar WHERE grammar_point = ?", (item["jp"],)
                ).fetchone()
            if row and (row[0] or 0) >= 2:
                aprendidas += 1
    return aprendidas / len(unit["items"])

def _gate_met(jap_memory, unit):
    prereq = unit.get("prerequisito")
    if not prereq:
        return True
    return _fraccion_aprendida(jap_memory, prereq) >= unit.get("umbral_prereq", UMBRAL_PREREQ_DEFECTO)
```

> "Aprendida" = `reps >= 2` (en SM-2 equivale a haber superado el ítem al menos dos veces,
> intervalo ≥ 6 días). Es uniforme para vocabulario y gramática y se deriva de datos reales.

`siguiente_item_nuevo()` no cambia: sigue devolviendo el primer ítem no enseñado de la primera
unidad cuya puerta esté abierta.

### Paso 1.2 — Eliminar `japanese_skills`, `japanese_topics`, `japanese_profile` de `japanese_memory.py`
- En `_inicializar_tablas()`: borrar los tres `CREATE TABLE IF NOT EXISTS` (`japanese_skills`,
  `japanese_topics`, `japanese_profile`).
- En `resumen_perfil()`: eliminar la query `SELECT skill, percentage ...` y la clave `"skills"`
  del dict devuelto (nadie la consume: `_montar_estado` en `profesor.py` no usa `skills`).

### Paso 1.3 — Reescribir `obtener_perfil_completo()` en `japanese_memory.py`
Esta función la usa el agente general vía `ai/tools.py` (`consultar_progreso_japones`) cuando
Laura pregunta "¿cómo voy?". Quitar las secciones de skills y de topics. Dejar el perfil basado en:
vocabulario dominado, gramática y su dominio, y puntos débiles. Ejemplo de objetivo:

```python
def obtener_perfil_completo(self) -> str:
    with self._conectar() as conn:
        vocab_count = conn.execute(
            "SELECT COUNT(*) FROM japanese_vocabulary WHERE status IN ('learned','mastered')"
        ).fetchone()[0]
        grammar = conn.execute(
            "SELECT grammar_point, mastery FROM japanese_grammar ORDER BY mastery DESC"
        ).fetchall()
        errors = conn.execute(
            "SELECT word, errors FROM japanese_vocabulary WHERE errors>2 ORDER BY errors DESC LIMIT 5"
        ).fetchall()

    perfil = "=== PERFIL ACTUAL DE LAURA (JAPONÉS) ===\n"
    perfil += f"Palabras dominadas: {vocab_count}\n"
    perfil += "Gramática:\n"
    for g, m in grammar:
        perfil += f"- {g}: {m:.0f}% dominio\n"
    if errors:
        perfil += "Puntos débiles:\n"
        for w, e in errors:
            perfil += f"- {w}: {e} errores\n"
    perfil += "\nInstrucciones:\n"
    perfil += "- No enseñes vocabulario ya dominado.\n"
    perfil += "- Refuerza las estructuras con errores frecuentes.\n"
    return perfil
```

### Paso 1.4 — Limpiar la ruta `/admin` en `app.py`
- Eliminar las queries de `japanese_skills`, `japanese_topics`, `japanese_profile`.
- Quitar los kwargs `jap_skills=`, `jap_topics=`, `jap_profile=` del `render_template("admin.html", ...)`.
- **No hay cambios de frontend**: ningún template referencia esas variables (confirmado con grep).

### Paso 1.5 — Limpiar `simulate_sensei.py`
En `limpiar_datos_japones()` eliminar las líneas `DELETE FROM japanese_skills;`,
`DELETE FROM japanese_topics;`, `DELETE FROM japanese_profile;`.

### Verificación Fase 1
- [ ] `python -m pytest tests/test_herramientas.py` pasa.
- [ ] `python simulate_sensei.py --clean` arranca sin errores; `/admin` y `/japones` cargan.
- [ ] Simular varias sesiones: al superar el 75 % de los saludos, el FOCO debe empezar a introducir
  ítems de la **siguiente** unidad (partículas), no solo saludos.
- [ ] `grep -ri "japanese_skills\|japanese_topics\|japanese_profile" .` no devuelve referencias vivas
  (salvo, si acaso, comentarios).

---

# FASE 2 — Ampliar el currículo N5 → N4 → N3 (libros oficiales)

**Objetivo.** Que el temario cubra de forma completa y ordenada N5, luego N4 y luego N3, siguiendo
la secuencia con que lo presentan los libros oficiales de referencia (Genki I para N5, Genki II
para N4, y listas estándar de gramática/vocabulario N3 tipo Tobira/Shin Kanzen/JLPT), **adaptado a
un profesor hablado** (vocabulario y gramática; nada de ejercicios de escritura de kana/kanji).

**Estado de partida.** Fase 1 completada: las unidades ya tienen el esquema
`prerequisito` / `umbral_prereq` y `_gate_met` funciona por fracción aprendida.

**Archivos a leer primero.**
- `ai/sensei/curriculum.py` (estructura de `CURRICULUM` tras la Fase 1).
- `ai/prompts/profesor_japones.txt` (para respetar el estilo voice-first al elegir ítems).

### Alcance y fuentes de referencia
- **N5** — cobertura tipo **Genki I (cap. 1-12)** + listas JLPT N5: partículas básicas, です/ます,
  verbos る/う e irregulares, adjetivos い/な, forma て, ～ない, ～たい, contadores básicos,
  vocabulario cotidiano (familia, tiempo/lugar, comida, números, transporte).
- **N4** — cobertura tipo **Genki II (cap. 13-23)**: potencial, volitiva, condicionales
  (ば/たら/と/なら), ～たことがある, transitividad, honoríficos básicos (敬語 intro),
  causativo/pasivo intro, ～そう/～よう/～らしい, vocabulario N4.
- **N3** — listas estándar N3 (Tobira / Shin Kanzen Master N3): keigo (尊敬語/謙譲語),
  causativo-pasivo, ～わけ/～はず/～べき/～ため, expresiones de matiz, conjunciones avanzadas,
  vocabulario N3.

### Reglas de autoría (obligatorias)
1. **Mantener EXACTAMENTE el formato** del dict existente. Ejemplo de ítem de vocabulario:
   `{"kind": "vocabulario", "jp": "食べる", "reading": "たべる", "meaning": "comer", "tipo": "verbo"}`
   y de gramática:
   `{"kind": "gramatica", "jp": "〜たら", "meaning": "condicional: 'si / cuando ocurre X'"}`.
2. **`reading` obligatorio y correcto** en todo vocabulario (necesario para el TTS japonés y para
   el panel de admin, que muestra la lectura).
3. **Ordenar las unidades** por nivel (N5 → N4 → N3) y, dentro de cada nivel, en el orden del libro.
4. **Encadenar `prerequisito`**: cada unidad apunta a la anterior en la secuencia; `umbral_prereq: 0.75`.
   El salto de nivel (última unidad N5 → primera N4) usa el mismo mecanismo.
5. **Sin duplicados**: no repetir un `jp` que ya exista en una unidad anterior.
6. **Tamaño de unidad**: 8-15 ítems por unidad (coherente con las existentes) para que el gating
   del 75 % tenga grano razonable.
7. **Verificar el japonés**: kana/kanji, lectura y significado correctos. Ante duda, confirmar la
   lectura estándar del ítem.
8. **Voice-first**: elegir ítems que tengan sentido hablados; evitar ítems cuyo valor sea solo
   ortográfico.

### Sugerencia de ejecución (por el volumen)
Autor por bloques: primero **completar N5**, verificar, commit; luego **N4**, verificar, commit;
luego **N3**. Tras cada bloque, correr la verificación de abajo. (Si se dispone de orquestación
multi-agente, se puede paralelizar por nivel, pero cada bloque debe pasar la verificación antes
de integrarse: japonés incorrecto en el currículo contamina todo el SRS aguas abajo.)

### Verificación Fase 2
- [ ] `python -c "import ai.sensei.curriculum"` sin errores de sintaxis.
- [ ] Script rápido que recorra `CURRICULUM` y verifique: todos los `jp` únicos, todo vocabulario
  con `reading`, todo `prerequisito` apunta a un `id` existente, y `umbral_prereq` presente.
- [ ] `python simulate_sensei.py --clean` sigue funcionando y `siguiente_item_nuevo` recorre las
  unidades nuevas al ir superando prerequisitos.

---

# FASE 3 — Eliminar la evaluación de pronunciación

**Objetivo.** Retirar por completo la evaluación de pronunciación. Con Whisper (STT) el texto de
Laura siempre llega bien escrito (kanji/kana correctos), así que comparar IPA con Levenshtein no
puede detectar errores de pronunciación reales: es complejidad muerta.

**Estado de partida.** Fases 1-2 completadas.

**Archivos a leer primero.**
- `ai/sensei/profesor.py` (`__init__`, `entrar`, `responder_turno`, `_extraer_frase_objetivo`).
- `ai/pronunciation.py`, `ai/japanese_ipa.py` (para confirmar que no se usan en otro sitio).
- `app.py` (comentario en la ruta `/grabar`, aprox. líneas 120-121).

### Cambios (dependencias confirmadas con grep; están todas contenidas aquí)
1. **Borrar los archivos** `ai/pronunciation.py` y `ai/japanese_ipa.py`
   (`japanese_ipa.py` solo lo importa `pronunciation.py`; nada más los usa).
2. En `ai/sensei/profesor.py`:
   - En `__init__` y en `entrar()`: eliminar `self.ultima_frase_objetivo = None`.
   - En `responder_turno`: eliminar todo el bloque `contexto_pronunciacion` (el `if
     self.ultima_frase_objetivo:` con el `import comparar_pronunciacion`, aprox. líneas 159-175).
   - En `responder_turno`: sustituir `contenido_usuario = mensaje + contexto_pronunciacion if ...`
     por simplemente usar `mensaje` como contenido del usuario.
   - En `responder_turno`: eliminar el bloque final que llama a `_extraer_frase_objetivo` y fija
     `self.ultima_frase_objetivo` (aprox. líneas 221-224).
   - Eliminar el método `_extraer_frase_objetivo` completo (aprox. líneas 293-303).
   - **No** eliminar `import re`: lo sigue usando `_parsear_json_sesion`.
3. En `app.py`: actualizar/eliminar el comentario de `/grabar` que dice que la evaluación de
   pronunciación vive dentro de `responder_turno` (aprox. líneas 120-121).

### Verificación Fase 3
- [ ] `grep -ri "pronunciacion\|pronunciation\|texto_a_ipa\|japanese_ipa\|frase_objetivo" .`
  no devuelve referencias vivas.
- [ ] `python simulate_sensei.py --clean` corre sin errores (el turno de conversación funciona igual,
  sin el contexto de pronunciación).

---

# FASE 4 — No perder sesiones (persistencia resiliente en el SRS)

**Objetivo.** Que el aprendizaje de una sesión **no dependa** de que el LLM extractor devuelva JSON
válido. Hoy `add_item` (ítems nuevos) y `review` (SRS) están dentro de `_ejecutar_extraccion`; si los
dos intentos de JSON fallan, no entra nada al SRS.

**Estado de partida.** Fases 1-3 completadas.

**Archivos a leer primero.**
- `ai/sensei/profesor.py` (`responder_turno`, `cerrar_sesion_y_extraer`, `_ejecutar_extraccion`,
  `_montar_estado`).
- `core/japanese_memory.py` (`add_item`, `review`, `guardar_resumen_sesion`).

### Cambios
1. **Registrar los ítems nuevos cuando se introducen**, no solo al cerrar. Cuando `_montar_estado`
   selecciona un ítem nuevo (`siguiente_item_nuevo`) y el profesor lo trabaja en el turno, persistirlo
   con `add_item(...)` (con `first_taught_session_id = session_id`) en ese momento. Así el FOCO del
   día queda en la BD aunque la extracción final falle.
   - Cuidado con duplicados: `add_item` ya es idempotente (no inserta si existe). Verificarlo.
2. **Cierre resiliente**: en `_ejecutar_extraccion`, si el JSON completo no está disponible tras los
   reintentos, además de guardar el `summary_basico`, aplicar `review` sobre los ítems del FOCO que
   se trabajaron esa sesión (marcándolos al menos como vistos) en lugar de descartar todo.
3. Garantizar que `guardar_resumen_sesion(...)` (con `ended_at`) se llama **siempre**, incluso ante
   excepción (ya hay un `except` que lo intenta; reforzarlo).

### Verificación Fase 4
- [ ] Forzar fallo del extractor (p. ej. temporalmente con `strict=True` y un modelo inexistente, o
  simulando excepción en `_llamar_extractor`) y comprobar con `simulate_sensei.py` que el vocabulario
  del FOCO de esa sesión **sí** aparece en `japanese_vocabulary` y que `japanese_sessions.ended_at`
  queda relleno.
- [ ] En condiciones normales, el comportamiento no cambia (los ítems nuevos no se duplican).

---

# FASE 5 — Ritmo y balance de introducción

**Objetivo.** Progresión realista: más de un ítem nuevo por sesión, pero sin saturar de repasos.

**Estado de partida.** Fases 1-4 completadas.

**Archivos a leer primero.**
- `ai/sensei/profesor.py` (`_montar_estado`).
- `ai/sensei/curriculum.py` (`siguiente_item_nuevo`).
- `core/config.py` (para añadir la constante configurable).

### Cambios
1. **2 ítems nuevos por sesión** por defecto (configurable hasta 3). Añadir una constante, p. ej.
   `MAX_ITEMS_NUEVOS = 2` en `core/config.py`.
   - `siguiente_item_nuevo` debe poder devolver los N primeros ítems no enseñados de las unidades
     abiertas (aceptar un parámetro `n` o una lista de exclusión).
2. **Throttle por carga de repaso**: si `resumen_perfil()["due_count"]` supera un umbral
   (p. ej. 12), **no** introducir ítems nuevos ese día; el FOCO prioriza consolidar los repasos
   vencidos. Reflejarlo en el texto del FOCO.
3. Ajustar `_montar_estado` para exponer el balance resultante al prompt.

### Verificación Fase 5
- [ ] `simulate_sensei.py --clean`: una sesión introduce hasta 2 (o 3) ítems nuevos.
- [ ] Con muchos repasos vencidos (simular acumulando ítems con `next_review` pasado), el FOCO deja
  de introducir nuevos y se centra en repasar.

---

# FASE 6 — Calidad de datos y robustez

**Objetivo.** Métricas de progreso más honestas y cierre de sesión sin condiciones de carrera.

**Estado de partida.** Fases 1-5 completadas.

**Archivos a leer primero.**
- `core/japanese_memory.py` (`resumen_perfil` → `weak_points`; `review` → `mastery`).
- `ai/sensei/profesor.py` (`_renovar_timer`, `salir`, `cerrar_sesion_y_extraer`).

### Cambios
1. **`weak_points` por tasa reciente, no absoluta.** Cambiar el criterio `errors > 2` por una tasa
   (p. ej. `errors / max(times_reviewed, 1) > 0.4` con un mínimo de repasos), para que un ítem ya
   dominado deje de marcarse como débil.
2. **`mastery` de gramática.** Hoy es `interval/21*100`, que confunde intervalo de repaso con dominio.
   Separarlo (p. ej. basar mastery en `times_correct / times_seen`) o documentarlo claramente como proxy.
3. **Extracción fuera del hilo del timer.** Que `threading.Timer` de inactividad no ejecute
   directamente `salir()` (que hace escrituras SQLite + LLM). El timer debería marcar "inactivo" y el
   cierre real ocurrir en el flujo principal, evitando escrituras concurrentes al cerrar la app.

### Verificación Fase 6
- [ ] Un ítem con muchos repasos correctos y pocos errores **no** aparece en `weak_points`.
- [ ] `mastery` refleja aciertos, no el calendario de repaso.
- [ ] Cierre por inactividad no produce escrituras en el hilo del timer (revisión de código + prueba).

---

# FASE 7 — Limpieza final

**Objetivo.** Quitar lo vestigial y dejar el banco de pruebas realista.

**Estado de partida.** Fases 1-6 completadas.

**Archivos a leer primero.**
- `ai/sensei/profesor.py` (`__init__`, usos de `provider_ligero`).
- `core/brain.py` (aprox. línea 41, construcción de `ProfesorJapones`).
- `simulate_sensei.py` (`TURNOS_PREDEFINIDOS`, construcción de providers).

### Cambios
1. **Eliminar `provider_ligero`.** Ya es vestigial: la extracción usa el provider principal con
   `strict=True`. Quitarlo del constructor de `ProfesorJapones` y de sus llamadas en
   `brain.py` y `simulate_sensei.py`. Verificar que nada más lo usa (`grep provider_ligero`).
2. **Conversación realista en `simulate_sensei.py`.** Reescribir `TURNOS_PREDEFINIDOS` para ejercitar
   las ramas que hoy nunca se prueban: incluir al menos un **error** (que produzca `duda`/`mal` →
   ejercita el reinicio de `reps` en SM-2) y un **repaso** de un ítem previo. Así la simulación cubre
   el ciclo completo, no solo aciertos.

### Verificación Fase 7
- [ ] `grep -r "provider_ligero" .` no devuelve usos.
- [ ] `python simulate_sensei.py --clean` corre y en la BD final aparecen ítems con estados
  variados (algún error, algún repaso), no solo aciertos.

---

# FASE 8 — Profesor particular: atender las peticiones de Laura

**Objetivo.** Que el profesor actúe como un **tutor particular**: el temario (FOCO) es el plan por
defecto, pero durante la sesión las peticiones de Laura tienen prioridad. Si Laura quiere aprender
algo concreto, reforzar lo que le cuesta, o explorar un tema que le interese, el profesor le hace
caso y enseña ese contenido **igual** que uno del temario (método de 3 pasos + entrada al SRS).
Cuando Laura ya lo domina o quiere cambiar, el profesor retoma la lección normal.

**Estado de partida.** Fases 1-7 completadas. En particular: SRS resiliente (Fase 4), throttle de
ítems nuevos (Fase 5) y sin evaluación de pronunciación (Fase 3).

**Contexto clave (leer antes).** Hoy el prompt **prohíbe** salir del temario: regla crítica 5
("Solo trabaja ítems del FOCO. Nunca introduzcas vocabulario adicional fuera de él.") y la sección
RESTRICCIONES ("Si Laura pregunta algo fuera del FOCO, responde brevemente y redirige…"). Esta fase
**cambia esa política**. Mecánicamente el SRS ya NO está atado al currículo: `add_item` y el
`new_items[]` del extractor guardan cualquier palabra que aparezca; el bloqueo es solo del prompt.

**Archivos a leer primero.**
- `ai/prompts/profesor_japones.txt` (completo).
- `ai/sensei/profesor.py` (`_ejecutar_extraccion`, `_montar_estado`, persistencia de la Fase 4).
- `core/japanese_memory.py` (`add_item`) — solo si se opta por etiquetar el origen (paso 8.4).

### Paso 8.1 — Reescribir la política del prompt (`profesor_japones.txt`)
Sustituir la lógica "solo FOCO / redirigir" por comportamiento de tutor particular:
- **Prioridad a Laura durante la sesión.** Si Laura pide aprender una palabra/expresión, reforzar
  algo que le cuesta, o hablar de un tema que le interesa, el profesor **le hace caso** en lugar de
  redirigir.
- **Enseñar lo pedido como el temario.** El vocabulario o estructura que surja de una petición se
  enseña con el mismo método de 3 pasos (DESGLOSE → CONTEXTO → PRODUCCIÓN), a lo largo de varios
  turnos, igual que un ítem del FOCO.
- **El FOCO es el plan por defecto**, no una cárcel: se usa cuando Laura no tiene una petición
  concreta, y se **retoma** cuando Laura ya domina lo pedido o quiere cambiar de tema.
- **Mantener el resto de límites pedagógicos**: voz-first (todo japonés entre 【】), UNA sola
  actividad/pregunta por turno, explicar antes de pedir producción, no encadenar preguntas,
  tolerancia plain/polite. Estos NO cambian.
- Reformular en consecuencia la regla crítica 5 y las restricciones de "no salir del FOCO".

### Paso 8.2 — Asegurar que lo enseñado a petición entra al SRS
- El extractor de cierre ya captura cualquier ítem nuevo del transcript (`new_items[]`) y lo mete
  con `add_item`, esté o no en el currículo. Verificar que sigue así tras las fases anteriores.
- **Coherencia con la Fase 4 (cierre resiliente):** si la extracción completa falla, hoy solo se
  garantizan los ítems del FOCO. Los ítems ad-hoc dependen del extractor. Documentarlo como
  degradación aceptable, o —opcional— registrar en memoria los ítems que el profesor marcó como
  enseñados esa sesión para persistirlos aunque el JSON falle.

### Paso 8.3 — Coherencia con el throttle de la Fase 5
- El límite `MAX_ITEMS_NUEVOS` gobierna la **introducción proactiva del temario**, NO las peticiones
  explícitas de Laura. Un ítem que Laura pide expresamente **no** cuenta contra ese límite ni contra
  el throttle por carga de repaso. Ajustar el texto del FOCO/prompt para dejarlo claro.

### Paso 8.4 — (Opcional) Etiquetar el origen
- Si se quiere distinguir en los paneles: añadir columna `origen` (`'curriculum'` | `'ad-hoc'`) a
  `japanese_vocabulary`/`japanese_grammar` vía migración idempotente (`_add_columns_if_missing`),
  rellenarla en `add_item`, y mostrarla en `/japones` y `/admin`. No es imprescindible para el
  comportamiento; solo para visibilidad.

### Verificación Fase 8
- [ ] En `simulate_sensei.py`, añadir un turno donde Laura pida algo fuera del temario
  (p. ej. "quiero aprender a decir mariposa") y comprobar que el profesor lo **enseña** (no redirige)
  con el método de 3 pasos, y que la palabra acaba en `japanese_vocabulary` con SRS activo
  (`next_review`, `reps`, etc.).
- [ ] Comprobar que, tras trabajar lo pedido, el profesor **retoma** el FOCO del temario.
- [ ] El temario del día sigue existiendo y funcionando cuando Laura no pide nada concreto.

---

## Apéndice — Tabla de archivos por fase

| Archivo | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 |
|---------|----|----|----|----|----|----|----|----|
| `ai/sensei/curriculum.py` | ✏️ gating | ✏️ contenido | | | ✏️ ritmo | | | |
| `core/japanese_memory.py` | ✏️ quitar tablas, perfil | | | ✏️ persistencia | ✏️ due_count | ✏️ weak/mastery | | ✏️ origen (opc.) |
| `ai/sensei/profesor.py` | | | ✏️ quitar pronunciación | ✏️ persistencia | ✏️ ritmo | ✏️ timer | ✏️ provider_ligero | (verificar) |
| `ai/pronunciation.py` / `ai/japanese_ipa.py` | | | 🗑️ borrar | | | | | |
| `ai/prompts/profesor_japones.txt` | | (leer) | | | | | | ✏️ política tutor |
| `app.py` | ✏️ /admin | | ✏️ comentario | | | | | ✏️ origen (opc.) |
| `core/brain.py` | | | | | | | ✏️ provider_ligero | |
| `core/config.py` | | | | | ✏️ constante | | | |
| `ai/tools.py` | (verificar) | | | | | | | |
| `simulate_sensei.py` | ✏️ DELETEs | (verificar) | (verificar) | (verificar) | (verificar) | | ✏️ turnos | ✏️ turno petición |
| `tests/test_herramientas.py` | (verificar) | | | | | | | |
| `templates/**` | sin cambios | | | | | | | (opc. origen) |
</content>
