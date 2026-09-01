#!/usr/bin/env python
"""Fase 06 del plan can-do N5 — escribe los `can_dos` por unidad (generados por
Claude, `scripts/_fase06_candos.json`) en `ai/sensei/curriculum.py`.

Uso: `python scripts/generar_candos.py [--check]`

Determinista. `_fase06_candos.json` es {unit_id: [{"id", "texto"}, ...]}. Para
cada unidad temática de vocab/gramática N5 (las que tienen al menos un ítem que
no es kanji) se inserta la clave `can_dos` justo antes de `items`. Las unidades
de kanji (solo ítems `tipo == "kanji"`) NO llevan can-dos: el kanji tiene su
propio flujo y está fuera de alcance.

El literal `CURRICULUM = [...]` se extrae y se reescribe con el mismo
serializador determinista de la Fase 02/03/05
(`reconciliar_vocab.extraer_literal_curriculum` / `formatear`): el diff toca
SOLO la clave nueva `can_dos`; ítems y metadatos quedan byte a byte iguales.

Con `--check`: no escribe; sale != 0 si el JSON no cuadra con el curriculum
(unidad inexistente, unidad de kanji con can-dos, unidad temática sin >= 2
can-dos) o si algún `can_do.id` se repite.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Consola Windows por defecto = cp1252; forzamos UTF-8 para imprimir japonés.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconciliar_vocab import extraer_literal_curriculum, formatear  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CURRICULUM_PY = RAIZ / "ai" / "sensei" / "curriculum.py"
CANDOS_JSON = Path(__file__).resolve().parent / "_fase06_candos.json"


def es_tematica(unidad):
    """Unidad de vocab/gramática N5: tiene al menos un ítem que no es kanji.
    Las unidades de kanji (solo `tipo == 'kanji'`) quedan fuera."""
    return any(
        it["kind"] == "gramatica"
        or (it["kind"] == "vocabulario" and it.get("tipo") != "kanji")
        for it in unidad["items"]
    )


def aplicar(units, candos):
    problemas = []
    ids_json = set(candos)
    tematicas = {u["id"] for u in units if es_tematica(u)}
    kanji = {u["id"] for u in units if not es_tematica(u)}

    faltan_json = tematicas - ids_json
    if faltan_json:
        problemas.append(f"unidades temáticas sin can-dos en el JSON: {sorted(faltan_json)}")
    sobran_json = ids_json - {u["id"] for u in units}
    if sobran_json:
        problemas.append(f"claves del JSON sin unidad: {sorted(sobran_json)}")
    kanji_con_candos = ids_json & kanji
    if kanji_con_candos:
        problemas.append(f"unidades de kanji con can-dos (fuera de alcance): {sorted(kanji_con_candos)}")

    for uid, lista in candos.items():
        if len(lista) < 2:
            problemas.append(f"{uid}: solo {len(lista)} can-dos (mínimo 2)")
        for cd in lista:
            if set(cd) != {"id", "texto"}:
                problemas.append(f"{uid}: can-do con claves {sorted(cd)} (se esperaba id/texto)")
            if not cd.get("texto", "").strip():
                problemas.append(f"{uid}: can-do {cd.get('id')!r} con texto vacío")

    todos_ids = [cd["id"] for lista in candos.values() for cd in lista]
    dups = sorted(x for x, n in Counter(todos_ids).items() if n > 1)
    if dups:
        problemas.append(f"can_do.id duplicados: {dups}")

    n = 0
    for u in units:
        if u["id"] not in candos:
            continue
        lista = [{"id": cd["id"], "texto": cd["texto"]} for cd in candos[u["id"]]]
        # reconstruir el dict con `can_dos` justo antes de `items` (orden estable)
        nuevo = {}
        for k, v in u.items():
            if k == "items":
                nuevo["can_dos"] = lista
            nuevo[k] = v
        u.clear()
        u.update(nuevo)
        n += len(lista)

    return n, problemas


def main():
    check = "--check" in sys.argv[1:]
    src = CURRICULUM_PY.read_text(encoding="utf-8")
    ini, fin, units = extraer_literal_curriculum(src)
    candos = json.loads(CANDOS_JSON.read_text(encoding="utf-8"))

    n_candos, problemas = aplicar(units, candos)

    con = sum(1 for u in units if "can_dos" in u)
    print(f"unidades con can-dos: {con}  ·  can-dos escritos: {n_candos}")

    if problemas:
        for p in problemas:
            print(f"ERROR: {p}")
        return 1

    if check:
        print("\nOK (--check): el JSON cuadra con el curriculum. No se ha escrito nada.")
        return 0

    cuerpo = formatear(units, 0)
    # `formatear` no emite coma tras el último elemento; el literal actual sí la
    # lleva (herencia de la Fase 04). Se conserva para que el diff sea mínimo.
    if re.search(r",\s*\]\s*\Z", src[ini:fin]):
        cuerpo = re.sub(r"\}\s*\]\s*\Z", "},\n]", cuerpo)
    nuevo_src = src[:ini] + cuerpo + src[fin:]
    if nuevo_src == src:
        print("\nSin cambios: curriculum.py ya tiene los can-dos de la Fase 06.")
        return 0
    CURRICULUM_PY.write_text(nuevo_src, encoding="utf-8")
    print(f"\nOK: {CURRICULUM_PY} reescrito.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
