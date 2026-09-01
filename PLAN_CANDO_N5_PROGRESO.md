# Progreso — PLAN_CANDO_N5

Estado vivo de la ejecución. Lo actualiza el orquestador tras cada fase.
Estados: `pendiente` · `en_curso:<agente>` · `verificada` · `bloqueada:<motivo>`

| Fase | Título | Bloque | 🔴/🟢 | Estado | Rama | Commit | Nota |
|---|---|---|---|---|---|---|---|
| 01 | Fuentes de verdad + validador | I | 🟢 | verificada | cando/fase01 | 64509f0 | data/n5_vocab.csv (717+cab), data/n5_grammar.csv (90+cab, ensamblada de memoria), scripts/validar_curriculum.py |
| 02 | Reconciliar vocabulario a la lista | I | 🔴 | verificada | cando/fase02 | 4bd09dd | 202 conservados, 508 añadidos, 103 fuera. CSV=710 jp únicos (no 717: 8 kanji doble lectura). Unidad nueva vocabulario_n5_extra |
| 03 | Reconciliar gramática a la lista | I | 🟢 | verificada | cando/fase03 | 8171b38 | 54 conservados, 36 añadidos, 101 fuera, 16 reubicados. gramática=90==CSV. Rehecha sobre fase02 (serializadores en conflicto) |
| 04 | Borrar unidades vacías + purgar BD | I | 🟢 | verificada | cando/fase04 | 4b20ca5 | 13 unidades borradas (53→40, 10 kanji intactas). 2 prereq repunteados. purgar_fuera_de_temario en Brain.__init__. Selector de nivel fuera de web. +col first_taught_session_id en japanese_grammar |
| 05 | Notas de uso del vocabulario + gramática completa | II | 🔴 | en_curso:fase05 | | | |
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
- **2026-09-01** — Fase 05 `en_curso` (subagente `fase05`, rama `cando/fase05`, worktree `../kaitosan-fase05`). Sesión pausada al 93% de tokens de la cuenta; se pidió checkpoint WIP a `origin/cando/fase05`.

### Para retomar (cuando vuelvan los tokens)

1. Sesión orquestadora: `git fetch --all`; mirar `origin/cando/fase05` (¿WIP o completa?).
2. Si Fase 05 quedó a medias: reanudar el subagente `fase05` con `SendMessage` (id interno guardado en el transcript) o lanzar uno nuevo que parta de `origin/cando/fase05` y termine la Fase 05.
3. Verificar gate Fase 05 (validador estricto + `pytest -q` + `git status` limpio + push). Puede cerrar con ítems `regenerar` listados en el informe.
4. Fusionar `cando/fase05` → `main` (`git merge --no-ff`, **sin borrar la rama antes del merge**), `git push origin main`, marcar `verificada` aquí.
5. Seguir en serie: Fase 06 (dep 03) → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18. Una fase por subagente en su worktree. Grupos paralelos del plan: **desactivados por decisión del usuario** (una a una).
6. Protocolo de merge del orquestador: `git worktree add -b cando/faseN ../kaitosan-faseN main` → subagente → verificar gate → `git merge --no-ff cando/faseN` en main → push → `git worktree remove` + `git branch -D` (en ese orden, nunca borrar rama antes de fusionar).
7. Tests: ignorar siempre los 8 módulos rotos preexistentes en `main` por deps no instaladas: `test_audio test_camera test_deteccion test_groq test_recorder test_stt test_tts test_wakeword`. Baseline tras Fase 04 = 36 passed.
