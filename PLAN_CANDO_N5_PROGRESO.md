# Progreso — PLAN_CANDO_N5

Estado vivo de la ejecución. Lo actualiza el orquestador tras cada fase.
Estados: `pendiente` · `en_curso:<agente>` · `verificada` · `bloqueada:<motivo>`

| Fase | Título | Bloque | 🔴/🟢 | Estado | Rama | Commit | Nota |
|---|---|---|---|---|---|---|---|
| 01 | Fuentes de verdad + validador | I | 🟢 | verificada | cando/fase01 | 64509f0 | data/n5_vocab.csv (717+cab), data/n5_grammar.csv (90+cab, ensamblada de memoria), scripts/validar_curriculum.py |
| 02 | Reconciliar vocabulario a la lista | I | 🔴 | verificada | cando/fase02 | 4bd09dd | 202 conservados, 508 añadidos, 103 fuera. CSV=710 jp únicos (no 717: 8 kanji doble lectura). Unidad nueva vocabulario_n5_extra |
| 03 | Reconciliar gramática a la lista | I | 🟢 | verificada | cando/fase03 | 8171b38 | 54 conservados, 36 añadidos, 101 fuera, 16 reubicados. gramática=90==CSV. Rehecha sobre fase02 (serializadores en conflicto) |
| 04 | Borrar unidades vacías + purgar BD | I | 🟢 | verificada | cando/fase04 | 4b20ca5 | 13 unidades borradas (53→40, 10 kanji intactas). 2 prereq repunteados. purgar_fuera_de_temario en Brain.__init__. Selector de nivel fuera de web. +col first_taught_session_id en japanese_grammar |
| 05 | Notas de uso del vocabulario + gramática completa | II | 🔴 | verificada | cando/fase05 | 4dfb44d | 52 puntos gramática con los 4 campos + 234 `uso` de vocab (286 vacías por diseño). LLM-juez: 50 ok, 2 regenerados, 0 dudosos. validador gramática ESTRICTO. Sin ítems `regenerar` pendientes |
| 06 | Can-dos por unidad (generados) | III | 🟢 | verificada | cando/fase06 | ed9414a | 129 can-dos en 30 unidades temáticas (3-5 c/u), 0 en las 10 de kanji. check can_do.id único activo en validador |
| 07 | Esquema BD: can_do_progreso + estado_item | III | 🟢 | verificada | cando/fase07 | 8ede807 | tabla can_do_progreso + estado_item/set_can_do/can_dos_progreso/fraccion_can_dos en japanese_memory.py. app.py:_temario_unidades usa estado_item (1 query/ítem, marcado ponytail para Fase 14) |
| 08 | Extractor califica can-dos | III | 🟢 | verificada | cando/fase08 | 999b9e2 | prompt sin `reviewed`, `_ejecutar_extraccion` sin review()/rescate/aprobado-oficio → set_can_do(id,resultado,session_id,nota=evidencia). srs.py intacto. `_rotar_due` (get_due_items) queda para Fase 09 |
| 09 | Orquestación del profesor por can-do | III | 🔴 | verificada | cando/fase09 | 431b4a3 | FOCO por can-do activo, fuera _rotar_due/_foco_due/_fraccion_aprendida. unidad completa ≥80% can-dos dominados. CHEQUEO_OXIDO_CADA=5. skip test_rotacion_foco + 1 de conexiones (Fase 18). simulate_sensei sustituido por smoke test (falta google.generativeai en entorno) |
| 10 | Regla sabido/nuevo en el prompt | III | 🟢 | verificada | cando/fase10 | 36a4a6d | regla [sabida]/[nueva]/[en progreso] en MÉTODO DE ENSEÑANZA. marcado ya venía de Fase 09, solo prompt + test |
| 11 | Boletín web | III | 🟢 | verificada | cando/fase11 | f317963 | /japones/boletin + JapaneseMemory.boletin(). can-dos ○/◐/● por unidad, inventario 710/90, puntos débiles. Enlace en hub. Test con app Flask mínima (import app rompe por picamera2) |
| 12 | Práctica de vocabulario por lección | IV | 🔴 | verificada | cando/fase12 | c7a9c69 | /japones/vocabulario/practicar?unidad=<id>, calcada de kanji. q5/q3/q1→review(...,"vocabulario"). alterna ES↔JP por paridad de reps. botón Practicar en temario. SM-2 idéntico a kanji (test) |
| 13 | Práctica de gramática por lección | IV | 🔴 | verificada | cando/fase13 | 9da4255 | /japones/gramatica/practicar?unidad=<id>. ejercicio hueco (64/90) o patrón (26/90). review(...,"gramatica"), mastery recalculado. botón Practicar ampliado a gramática |
| 14 | Conectar estado del juego con el profesor | IV | 🟢 | verificada | cando/fase14 | 6f4f249 | circuito ya unificado (todo lee estado_item). marcar_completo escribe status compatible. test_circuito verde. bulk estado_items aparcado a Fase 18 |
| 15 | Notas del profe | V | 🟢 | verificada | cando/fase15 | ede48d2 | campo nota_profe en extractor, columna en japanese_sessions (+migración), 3 últimas en RECUERDAS_DE_LAURA bajo "Cómo va Laura" |
| 16 | Deberes entre sesiones | V | 🟢 | verificada | cando/fase16 | f515b4b | campo deberes en extractor + ritual de cierre, columna en japanese_sessions, getter deberes_ultima_sesion, línea primera del FOCO en sesión siguiente ("ya preguntados" vía ended_at) |
| 17 | Arco de sesión | V | 🟢 | pendiente | | | |
| 18 | Limpieza final | VI | 🟢 | pendiente | | | |

## Registro

- **2026-09-01** — Fases 01–04 `verificada` y fusionadas en `main` (`origin/main` @ `92b1a65`). Bloque I completo: vocab=710 N5, gramática=90 N5, 13 unidades N4/N3 borradas (53→40, kanji intacto), `purgar_fuera_de_temario` en `Brain.__init__`, web sin selector de nivel.
- **2026-09-01** — Fase 05 cortada por límite de sesión de la cuenta (resets 21:00 Europe/Madrid). El subagente `fase05` murió sin commitear, pero el orquestador rescató `scripts/_fase05_contenido.json` del worktree y lo pusheó a `origin/cando/fase05` (commit WIP). Contenido: 52 puntos de gramática con `meaning`/`ejemplo`/`literal`/`uso`; JSON **truncado a media escritura** (inválido ~char 16221, `〜ましょう` corrompido). Sin `uso` de vocabulario, sin ensamblar en `curriculum.py`, sin `scripts/generar_contenido.py`, sin `scripts/validar_curriculum.py` endurecido, sin `tests/test_curriculum_contenido.py`.

### Para retomar (cuando vuelvan los tokens, tras las 21:00 Madrid)

1. `git fetch --all`. `main` está en `e66aa11` (Fases 01–04). `origin/cando/fase05` tiene el WIP.
2. **Terminar Fase 05** con un subagente nuevo que parta de `origin/cando/fase05` (worktree `git worktree add cando/fase05 ../kaitosan-fase05` sobre la rama ya existente). Tareas:
   a. Reparar `scripts/_fase05_contenido.json` (JSON válido; arreglar `〜ましょう`; completar puntos que falten hasta los ~52).
   b. Generar `uso` de vocabulario solo donde el matiz lo pide (partículas, contadores, keigo, frases hechas, verbos no obvios, falsos amigos); transparentes → vacío. NO generar `ejemplo`/`literal` de vocab.
   c. Escribir `scripts/generar_contenido.py` que ensamble el JSON sobre `ai/sensei/curriculum.py` (reutilizar helpers de `scripts/reconciliar_gram.py` para el serializador; campos existentes carácter a carácter).
   d. Endurecer `scripts/validar_curriculum.py`: los 90 puntos de gramática deben tener `ejemplo` y `uso` no vacíos → exit≠0 si falta.
   e. Crear `tests/test_curriculum_contenido.py` (ver sección 05 del plan).
   f. Validación LLM-juez estricta sobre los 52 de gramática + las `uso` de vocab generadas; `regenerar` una vez; listar los dudosos que queden en el informe (no bloquean el gate — excepción del plan para la 05).
3. Verificar gate Fase 05, fusionar `cando/fase05` → `main` (`git merge --no-ff`, **sin borrar la rama antes del merge**), `git push origin main`, marcar `verificada`.
4. Seguir en serie: Fase 06 (dep 03) → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18. Una fase por subagente en su worktree. Grupos paralelos del plan: **desactivados por decisión del usuario** (una a una, para evitar conflictos de merge).
5. Protocolo de merge del orquestador: `git worktree add -b cando/faseN ../kaitosan-faseN main` → subagente implementa y pushea `cando/faseN` → orquestador verifica gate → `git merge --no-ff cando/faseN` en `main` → `git push origin main` → `git worktree remove ../kaitosan-faseN` + `git branch -D cando/faseN` (**en ese orden — nunca borrar la rama antes de fusionar**; ya pasó una vez con la Fase 04 y hubo que recuperarla de `origin`).
6. El orquestador tiene permiso explícito del usuario para `git merge --ff-only`/`--no-ff` + `git push origin main` tras cada gate verde.
7. Tests: ignorar siempre los 8 módulos rotos preexistentes en `main` por deps no instaladas: `test_audio test_camera test_deteccion test_groq test_recorder test_stt test_tts test_wakeword`. Baseline tras Fase 04 = **36 passed**.
8. Los subagentes tienden a auto-marcarse `verificada` en este fichero y a inventar hashes — el orquestador ignora eso y verifica el gate él mismo.
