#!/usr/bin/env python
"""Fase 02 — reconcilia el vocabulario de `ai/sensei/curriculum.py` con la lista
oficial N5 de `data/n5_vocab.csv` (717/718 filas, 710 `jp` únicos).

Qué hace, de forma determinista:
  1. CONSERVA los ítems de vocabulario cuyo `jp` está en el CSV, con sus campos
     de texto (`meaning`, `ejemplo`, `literal`, `uso`, `tipo`, ...) intactos
     carácter a carácter. Si un `jp` aparecía dos veces en el temario, se queda
     la primera aparición (orden de unidades) y se descarta la segunda.
  2. ELIMINA los ítems de vocabulario cuyo `jp` no está en el CSV (incluye los
     de N4/N3; las unidades que queden sin ítems las borra la Fase 04).
  3. AÑADE las palabras que faltan (508) con `reading` (del CSV), `meaning`
     (traducido EN->ES por Claude, en `scripts/_vocab_nuevo_overrides.json`) y
     `tipo`. `ejemplo` y `literal` quedan vacíos para siempre; `uso` vacío hasta
     la Fase 05.
  4. ASIGNA cada palabra nueva a la unidad temática más afín (decidido por
     Claude en el JSON de overrides). Las que no encajan van a una unidad nueva
     `vocabulario_n5_extra`.
  5. REESCRIBE el literal `CURRICULUM` de `curriculum.py`: en cada unidad, los
     ítems de gramática quedan en su orden original y detrás van los de
     vocabulario (conservados + nuevos) ordenados por `jp`. Solo se toca el
     literal; el resto del fichero (imports, inyección de kanji, funciones)
     queda igual.

Generador de un solo uso: se corre una vez contra el `curriculum.py` anterior a
la Fase 02. Vuelve a correrlo sobre un `curriculum.py` ya reconciliado aborta
(no encuentra las 508 palabras "nuevas"): para regenerarlo, primero
`git checkout ai/sensei/curriculum.py`.

Uso: `python scripts/reconciliar_vocab.py`  (--check para no escribir, solo avisar)
"""
import ast
import csv
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # consola Windows cp1252 -> utf-8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
CURRICULUM_PY = RAIZ / "ai" / "sensei" / "curriculum.py"
CSV_N5 = RAIZ / "data" / "n5_vocab.csv"
OVERRIDES = Path(__file__).resolve().parent / "_vocab_nuevo_overrides.json"

EXTRA_ID = "vocabulario_n5_extra"
EXTRA_UNIT_META = {
    "id": EXTRA_ID,
    "nombre": "Vocabulario N5 — Cajón de sastre",
    "funcion": (
        "manejar el vocabulario N5 que no cae en una unidad temática concreta: "
        "escuela, medios, animales, países y palabras de andamiaje para preguntar "
        "por otras palabras"
    ),
    "frases_hechas": [
        {"jp": "それはどういう意味ですか",
         "uso": "para preguntar qué significa una palabra que no conoces"},
        {"jp": "日本語で何と言いますか",
         "uso": "para preguntar cómo se dice algo en japonés"},
        {"jp": "もう一回言ってください",
         "uso": "para pedir que repitan algo que no has captado"},
        {"jp": "ゆっくりお願いします",
         "uso": "para pedir que hablen más despacio"},
    ],
    "prerequisito": "comparaciones_deseos",
    "umbral_prereq": 0.75,
}
# Punto de inserción: justo antes de la primera unidad N4 (la inyección de kanji
# corta también aquí, con lo que `vocabulario_n5_extra` queda como último bloque
# N5 hablado antes de los kanji).
ANCLA_N4 = "forma_potencial"


def extraer_literal_curriculum(fuente):
    """Devuelve (idx_ini, idx_fin, lista) del literal `CURRICULUM = [ ... ]`.

    El literal es puro (str/list/dict/None): `ast.literal_eval` es seguro y no
    ejecuta la inyección de kanji que vive más abajo en el módulo.
    """
    marca = "CURRICULUM = ["
    ini = fuente.index(marca) + len("CURRICULUM = ")
    profundidad = 0
    en_cadena = None
    escapado = False
    i = ini
    while i < len(fuente):
        c = fuente[i]
        if en_cadena:
            if escapado:
                escapado = False
            elif c == "\\":
                escapado = True
            elif c == en_cadena:
                en_cadena = None
        else:
            if c in ("'", '"'):
                en_cadena = c
            elif c == "[":
                profundidad += 1
            elif c == "]":
                profundidad -= 1
                if profundidad == 0:
                    fin = i
                    break
        i += 1
    else:
        raise RuntimeError("no se encontró el cierre del literal CURRICULUM")
    return ini, fin + 1, ast.literal_eval(fuente[ini:fin + 1])


def cargar_csv():
    """{jp: reading} con las lecturas de las filas duplicadas unidas por ' / '."""
    lecturas = {}
    with open(CSV_N5, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            jp = fila["expression"]
            rd = (fila["reading"] or "").replace("; ", " / ").strip()
            if jp in lecturas:
                if rd and rd not in lecturas[jp]:
                    lecturas[jp] = f"{lecturas[jp]} / {rd}"
            else:
                lecturas[jp] = rd
    return lecturas


def formatear(valor, sangria):
    """Serializador determinista y legible para el literal CURRICULUM.

    dicts: una clave por línea, en el orden en que vienen (los ítems se
    construyen aquí con un orden de claves fijo). Sin dependencia de `black`.
    """
    pad = " " * sangria
    pad2 = " " * (sangria + 2)
    if isinstance(valor, dict):
        if not valor:
            return "{}"
        hojas = all(v is None or isinstance(v, (str, int, float, bool)) for v in valor.values())
        inline = "{" + ", ".join(f"{repr(k)}: {repr(v)}" for k, v in valor.items()) + "}"
        if hojas and len(pad) + len(inline) <= 100:
            return inline
        lineas = [f"{pad2}{repr(k)}: {formatear(v, sangria + 2)}" for k, v in valor.items()]
        return "{\n" + ",\n".join(lineas) + "\n" + pad + "}"
    if isinstance(valor, list):
        if not valor:
            return "[]"
        lineas = [f"{pad2}{formatear(v, sangria + 2)}" for v in valor]
        return "[\n" + ",\n".join(lineas) + "\n" + pad + "]"
    return repr(valor)


def item_vocab(jp, reading, meaning, tipo, ejemplo="", literal="", uso=""):
    """Orden de claves fijo -> diff estable."""
    return {
        "kind": "vocabulario",
        "jp": jp,
        "reading": reading,
        "meaning": meaning,
        "tipo": tipo,
        "ejemplo": ejemplo,
        "literal": literal,
        "uso": uso,
    }


def main():
    solo_check = "--check" in sys.argv
    fuente = CURRICULUM_PY.read_text(encoding="utf-8")
    ini, fin, curriculum = extraer_literal_curriculum(fuente)
    lecturas_csv = cargar_csv()
    objetivo = set(lecturas_csv)                       # 710 jp únicos

    # --- 1 + 2: conservar / eliminar -------------------------------------------
    conservados_por_unidad = {}      # unit_id -> [item, ...]  (solo vocab)
    reclamados = set()
    n_conservados = n_eliminados = 0
    for unidad in curriculum:
        vivos = []
        for it in unidad["items"]:
            if it["kind"] != "vocabulario":
                continue
            jp = it["jp"]
            if jp in objetivo and jp not in reclamados:
                reclamados.add(jp)
                vivos.append(it)
                n_conservados += 1
            else:
                n_eliminados += 1
        if vivos:
            conservados_por_unidad[unidad["id"]] = vivos

    # --- 3 + 4: añadir las que faltan ----------------------------------------
    nuevas_jp = sorted(objetivo - reclamados)
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if len(overrides) != len(nuevas_jp):
        raise SystemExit(
            f"overrides ({len(overrides)}) != palabras nuevas ({len(nuevas_jp)}); "
            "regenera scripts/_vocab_nuevo_overrides.json"
        )
    nuevos_por_unidad = {}
    for jp, ov in zip(nuevas_jp, overrides):
        nuevos_por_unidad.setdefault(ov["u"], []).append(
            item_vocab(jp, lecturas_csv[jp], ov["m"], ov["t"])
        )
    n_anadidos = len(nuevas_jp)

    unidades_validas = {u["id"] for u in curriculum} | {EXTRA_ID}
    fuera = sorted(set(nuevos_por_unidad) - unidades_validas)
    if fuera:
        raise SystemExit(f"overrides apuntan a unidades inexistentes: {fuera}")

    # --- unidad nueva vocabulario_n5_extra -----------------------------------
    if nuevos_por_unidad.get(EXTRA_ID) and not any(u["id"] == EXTRA_ID for u in curriculum):
        extra = dict(EXTRA_UNIT_META)
        extra["items"] = []
        corte = next(i for i, u in enumerate(curriculum) if u["id"] == ANCLA_N4)
        curriculum.insert(corte, extra)

    # --- 5: reescribir los items de cada unidad ----------------------------
    for unidad in curriculum:
        gram = [it for it in unidad["items"] if it["kind"] != "vocabulario"]
        vocab = conservados_por_unidad.get(unidad["id"], []) + nuevos_por_unidad.get(unidad["id"], [])
        vocab.sort(key=lambda it: it["jp"])
        unidad["items"] = gram + vocab

    # --- validación rápida interna ----------------------------------------
    jp_final = [it["jp"] for u in curriculum for it in u["items"] if it["kind"] == "vocabulario"]
    assert set(jp_final) == objetivo, "el set de jp no coincide con el CSV"
    assert len(jp_final) == len(set(jp_final)), "jp de vocabulario duplicado"
    for u in curriculum:
        for it in u["items"]:
            if it["kind"] == "vocabulario":
                assert it.get("reading") and it.get("meaning"), it["jp"]

    # `ini` apunta al '[' inicial; `fin` al carácter tras el ']' de cierre.
    salida = fuente[:ini] + formatear(curriculum, 0) + fuente[fin:]

    print(f"conservados: {n_conservados}  eliminados: {n_eliminados}  añadidos: {n_anadidos}")
    print(f"vocabulario final: {len(jp_final)} ítems (esperado {len(objetivo)})")
    print(f"unidades: {len(curriculum)}")

    if solo_check:
        print("--check: no se escribe curriculum.py")
        return 0

    CURRICULUM_PY.write_text(salida, encoding="utf-8")
    print(f"escrito {CURRICULUM_PY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
