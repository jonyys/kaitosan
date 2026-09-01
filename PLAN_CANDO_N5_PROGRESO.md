# Progreso — PLAN_CANDO_N5

Estado vivo de la ejecución. Lo actualiza el orquestador tras cada fase.
Estados: `pendiente` · `en_curso:<agente>` · `verificada` · `bloqueada:<motivo>`

| Fase | Título | Bloque | 🔴/🟢 | Estado | Rama | Commit | Nota |
|---|---|---|---|---|---|---|---|
| 01 | Fuentes de verdad + validador | I | 🟢 | verificada | cando/fase01 | 64509f0 | data/n5_vocab.csv (717+cab), data/n5_grammar.csv (90+cab, ensamblada de memoria), scripts/validar_curriculum.py |
| 02 | Reconciliar vocabulario a la lista | I | 🔴 | verificada | cando/fase02 | 4bd09dd | 202 conservados, 508 añadidos, 103 fuera. CSV=710 jp únicos (no 717: 8 kanji doble lectura). Unidad nueva vocabulario_n5_extra |
| 03 | Reconciliar gramática a la lista | I | 🟢 | verificada | cando/fase03 | 8171b38 | 54 conservados, 36 añadidos, 101 fuera, 16 reubicados. gramática=90==CSV. Rehecha sobre fase02 (serializadores en conflicto) |
| 04 | Borrar unidades vacías + purgar BD | I | 🟢 | verificada | cando/fase04 | 4b20ca5 | 13 unidades borradas (53→40, 10 kanji intactas). 2 prereq repunteados. purgar_fuera_de_temario en Brain.__init__. Selector de nivel fuera de web. +col first_taught_session_id en japanese_grammar |
| 05 | Notas de uso del vocabulario + gramática completa | II | 🔴 | WIP:fase05 | cando/fase05 | (WIP) | Subagente cortado por límite de sesión. `scripts/_fase05_contenido.json` pusheado: 52 puntos de gramática con los 4 campos generados, JSON truncado/inválido al final. Falta: reparar JSON, `uso` de vocab, ensamblar, validar |
| 06 | Can-dos por unidad (generados) | III | 🟢 | pendiente | | | |
| 07 | Esquema BD: can_do_progreso + estado_item | III | 🟢 | pendiente | | | |
| 08 | Extractor califica can-dos | III | 🟢 | pendiente | | | |
| 09 | Orquestación del profesor por can-do | III | 🔴 | pendiente | | | |
| 10 | Regla sabido/nuevo en el prompt | III | 🟢 | pendiente | | | |
| 11 | Boletín web | III | 🟢 | pendiente | | | |
| 12 | Práctica de vocabulario por lección | IV | 🔴 | pendiente | | | |
| 13 | Práctica de gramática por lección | IV | 🔴 | pendiente | | | |
| 14 | Conectar estado del juego con el profesor | IV | 🟢 | pendiente | | | |
| 15 | Notas del profe | V | 🟢 | pendiente | | | |
| 16 | Deberes entre sesiones | V | 🟢 | pendiente | | | |
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
