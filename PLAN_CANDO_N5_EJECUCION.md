# Ejecución del plan CANDO_N5

Cómo se ejecuta `PLAN_CANDO_N5.md` de principio a fin con agentes, con cada fase
verificada antes de pasar a la siguiente y sin malgastar contexto.

---

## Cómo arrancar

Abre el repo con `claude` y pega **este mensaje**:

> Ejecuta el plan completo de `PLAN_CANDO_N5.md` siguiendo el protocolo de
> `PLAN_CANDO_N5_EJECUCION.md`. Lleva el estado en `PLAN_CANDO_N5_PROGRESO.md`.
> Empieza por la primera fase pendiente cuyas dependencias estén todas
> `verificada`. No avances de fase hasta que la actual quede `verificada`.
> Cuando todas estén `verificada`, para y dame el resumen.

Esa sesión es el **orquestador**. No escribe código: reparte fases a subagentes,
espera su informe, comprueba el gate y actualiza el progreso.

Para acelerar con paralelismo, añade al mensaje:
`Lanza en paralelo los grupos marcados como paralelizables, cada subagente en su
git worktree.`

---

## Ficheros

| Fichero | Qué es |
|---|---|
| `PLAN_CANDO_N5.md` | el plan: 18 fases, cada una con su comando de verificación |
| `PLAN_CANDO_N5_EJECUCION.md` | este: protocolo, dependencias, gates |
| `PLAN_CANDO_N5_PROGRESO.md` | estado vivo, una línea por fase. Lo actualiza el orquestador |

---

## Roles

### Orquestador (la sesión principal)

1. Lee `PLAN_CANDO_N5_PROGRESO.md`.
2. Elige la(s) siguiente(s) fase(s): `pendiente` con **todas** sus dependencias
   en `verificada`.
3. Por cada fase, lanza un **subagente fresco** (`Agent`, tipo `general-purpose`,
   sin heredar contexto — eso es la limpieza de contexto: el churn de ficheros
   del subagente no entra en el contexto del orquestador).
4. Espera el informe (≤ 10 líneas).
5. Comprueba el **gate** (abajo). Si pasa → marca `verificada` en el progreso con
   rama y commit. Si no → marca `bloqueada` con el error, **para** y avisa.
6. Vuelve a 2 hasta que no queden `pendiente`.
7. Resumen final: fases hechas, commits, ítems dudosos aceptados en Fase 05,
   knobs pendientes de afinar.

El orquestador **nunca** implementa una fase él mismo, ni salta el gate, ni
sigue tras una `bloqueada`.

### Subagente de fase

Prompt que le pasa el orquestador:

> Eres un subagente de implementación. Haz **solo** la Fase N de
> `PLAN_CANDO_N5.md` (léela entera, y las secciones "Estado de partida", "Qué
> campos lleva cada ítem" y "Fuera de alcance"). Repo: rama nueva `cando/faseN`
> desde `main` (o el worktree que te indico).
> Al terminar: ejecuta el comando de verificación de la fase **y** `pytest -q`.
> Los dos tienen que salir en verde y el árbol limpio y commiteado.
> Si la verificación falla, arréglalo. Si no lo consigues en tu turno, deja la
> rama como esté, no la mezcles, y responde con el error exacto.
> Informe final (≤ 10 líneas): qué tocaste, salida de la verificación, hash del
> commit, cualquier decisión o desviación.

Un subagente puede **encadenar varias fases 🟢** consecutivas y sin dependencias
cruzadas en un solo turno (p. ej. 15→16, o 10 tras 09) si el orquestador se lo
pide explícitamente. Las fases 🔴 van **una por subagente**.

---

## Gate de verificación

Una fase pasa a `verificada` solo si las tres cosas:

1. El **comando de verificación** de la fase (en `PLAN_CANDO_N5.md`) sale con
   código 0.
2. `pytest -q` completo en verde (ninguna regresión en el resto del proyecto).
3. `git status` limpio y el trabajo commiteado en su rama.

Excepción única: Fase 05 puede cerrar con ítems `uso`/gramática marcados
`regenerar` restantes si el informe los lista y el orquestador los registra en
el resumen. Cualquier otra fase, verde o `bloqueada`, sin término medio.

---

## Dependencias y paralelismo

| Fase | Depende de | 🔴/🟢 | Paralelizable con |
|---|---|---|---|
| 01 | — | 🟢 | — |
| 02 | 01 | 🔴 | 03 |
| 03 | 01 | 🟢 | 02 |
| 04 | 02, 03 | 🟢 | — |
| 05 | 02, 03 | 🔴 | 06 |
| 06 | 03 | 🟢 | 05 |
| 07 | 06 | 🟢 | — |
| 08 | 07 | 🟢 | — |
| 09 | 06, 07, 08 | 🔴 | 11 |
| 10 | 09 | 🟢 | 11 |
| 11 | 06, 07 | 🟢 | 09, 10 |
| 12 | 05 | 🔴 | 13 |
| 13 | 05 | 🔴 | 12 |
| 14 | 10, 12, 13 | 🟢 | — |
| 15 | 08 | 🟢 | 17 |
| 16 | 15 | 🟢 | 17 |
| 17 | 09 | 🟢 | 15, 16 |
| 18 | todo lo demás | 🟢 | — |

**Grupos que se pueden lanzar a la vez** (ficheros disjuntos, cada subagente en
su worktree, merge cuando ambos verifican):
- `{02, 03}`
- `{05, 06}` (05 espera a que 02 y 03 verifiquen; 06 solo a 03)
- `{09+10}` y `{11}`
- `{12, 13}`
- `{15+16}` y `{17}`

Camino crítico (lo que marca la duración): `01 → 02 → 05 → 12 → 14 → 15 → 16`
(el otro brazo, `06→07→08→09→10`, corre en paralelo y se junta en 14). Bloque VI
(18) siempre al final.

---

## Contexto y tokens

- Cada fase = subagente fresco. El orquestador solo acumula informes de ≤ 10
  líneas, así que aguanta las 18 fases sin llenarse.
- Las fases 🔴 son las que mueven mucho fichero (regenerar `curriculum.py`,
  generar contenido, páginas web nuevas): al ir en subagente propio, ese
  volumen **nunca** toca el contexto del orquestador.
- Si aun así el orquestador se satura, el harness lo resume solo y sigue. No
  hace falta `/clear` manual ni cerrar la sesión.
- No relanzar un subagente ya terminado con `Agent`: si hay que continuar uno,
  `SendMessage` a su nombre.

---

## Si algo se tuerce

- **Verificación falla y el subagente no lo arregla** → fase `bloqueada`,
  orquestador para. Tú miras el error, decides (ajustar el plan, hacerlo a mano,
  saltar), y relanzas el arranque.
- **Dos fases en paralelo chocan al hacer merge** → el orquestador rehace la
  segunda sobre la primera ya mezclada, en subagente nuevo.
- **`pytest` global rojo por una fase anterior ya marcada `verificada`** →
  regresión tardía: `bloqueada` la fase actual, se arregla la causa antes de
  seguir.

---

## Hecho

Todas las fases `verificada`, `PLAN_CANDO_N5_PROGRESO.md` sin `pendiente` ni
`bloqueada`, `pytest -q` verde, `python simulate_sensei.py` corre una sesión
entera. El orquestador da el resumen y para.
