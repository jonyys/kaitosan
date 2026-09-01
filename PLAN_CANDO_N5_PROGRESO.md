# Progreso — PLAN_CANDO_N5

Estado vivo de la ejecución. Lo actualiza el orquestador tras cada fase.
Estados: `pendiente` · `en_curso:<agente>` · `verificada` · `bloqueada:<motivo>`

| Fase | Título | Bloque | 🔴/🟢 | Estado | Rama | Commit | Nota |
|---|---|---|---|---|---|---|---|
| 01 | Fuentes de verdad + validador | I | 🟢 | verificada | cando/fase01 | 64509f0 | data/n5_vocab.csv (717+cab), data/n5_grammar.csv (90+cab, ensamblada de memoria), scripts/validar_curriculum.py |
| 02 | Reconciliar vocabulario a la lista | I | 🔴 | verificada | cando/fase02 | 4bd09dd | 202 conservados, 508 añadidos, 103 fuera. CSV=710 jp únicos (no 717: 8 kanji doble lectura). Unidad nueva vocabulario_n5_extra |
| 03 | Reconciliar gramática a la lista | I | 🟢 | verificada | cando/fase03 | 8171b38 | 54 conservados, 36 añadidos, 101 fuera, 16 reubicados. gramática=90==CSV. Rehecha sobre fase02 (serializadores en conflicto) |
| 04 | Borrar unidades vacías + purgar BD | I | 🟢 | verificada | cando/fase04 | 4b20ca5 | 13 unidades borradas (53→40, 10 kanji intactas). 2 prereq repunteados. purgar_fuera_de_temario en Brain.__init__. Selector de nivel fuera de web. +col first_taught_session_id en japanese_grammar |
| 05 | Notas de uso del vocabulario + gramática completa | II | 🔴 | pendiente | | | |
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

_(el orquestador añade aquí una línea por fase cerrada: fecha, agente, salida de la verificación, decisiones)_
