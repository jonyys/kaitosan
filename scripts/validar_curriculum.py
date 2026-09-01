#!/usr/bin/env python
"""Fase 01 del plan can-do N5 — invariantes del temario (`ai/sensei/curriculum.py`).

Uso: `python scripts/validar_curriculum.py`. Sale con código != 0 si algún
check DURO falla. No modifica `curriculum.py`.

Checks duros (fallan hoy si se rompen):
  - todo `jp` es japonés válido (contiene al menos un carácter kana/kanji).

Checks tolerantes (solo avisan por stdout; se endurecen en fases 02/03/05,
cuando `curriculum.py` ya está reconciliado con `data/n5_vocab.csv` y
`data/n5_grammar.csv`):
  - `jp` único dentro de vocabulario y dentro de gramática por separado.
  - todo ítem de vocabulario tiene `kind`, `reading` y `meaning` no vacíos.
  - todo punto de gramática tiene `ejemplo` y `uso` no vacíos.

TODO (Fase 06): cuando el curriculum tenga `can_do` por unidad, añadir aquí
el check de `can_do.id` único en todo el temario.
"""
import re
import sys
from collections import Counter
from pathlib import Path

# La consola de Windows por defecto (cmd, codepage cp1252/cp437) revienta al
# imprimir jp japonés. Forzamos stdout/stderr a UTF-8 en vez de depender de
# PYTHONIOENCODING en el entorno de quien ejecute el script.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.sensei.curriculum import CURRICULUM

# Al menos un carácter hiragana/katakana/kanji en alguna parte del string.
# Deliberadamente NO exige que el string sea *solo* japonés: bastante de la
# gramática N5 ya en curriculum.py anota alternativas o notas entre paréntesis
# en caracteres latinos (p.ej. "〜ため(に)", "つ (serie general)").
JP_CHAR_RE = re.compile(r"[぀-ヿ㐀-鿿豈-﫿]")


def es_japones_valido(jp):
    return bool(jp and jp.strip() and JP_CHAR_RE.search(jp))


def main():
    errores = []   # checks duros -> exit != 0
    avisos = []    # checks tolerantes -> solo se imprimen

    vocab_items = [it for u in CURRICULUM for it in u["items"] if it["kind"] == "vocabulario"]
    gram_items = [it for u in CURRICULUM for it in u["items"] if it["kind"] == "gramatica"]

    # --- japonés válido (duro) ---
    for it in vocab_items + gram_items:
        jp = it.get("jp")
        if not es_japones_valido(jp):
            errores.append(f"jp inválido o vacío: {jp!r} (kind={it.get('kind')})")

    # --- jp único por separado en vocab / gram (tolerante en Fase 01) ---
    for nombre, items in (("vocabulario", vocab_items), ("gramatica", gram_items)):
        contador = Counter(it["jp"] for it in items)
        dups = sorted(jp for jp, n in contador.items() if n > 1)
        if dups:
            avisos.append(
                f"{nombre}: {len(dups)} jp duplicados (se corrige en Fase 02/03): {dups}"
            )

    # --- vocabulario: kind/reading/meaning no vacíos (tolerante en Fase 01) ---
    incompletos_vocab = [
        it["jp"] for it in vocab_items
        if not it.get("kind") or not it.get("reading") or not it.get("meaning")
    ]
    if incompletos_vocab:
        avisos.append(
            f"vocabulario: {len(incompletos_vocab)} ítems sin kind/reading/meaning "
            f"(se corrige en Fase 02): {incompletos_vocab}"
        )

    # --- gramática: ejemplo/uso no vacíos (tolerante en Fase 01, se endurece en 05) ---
    incompletos_gram = [
        it["jp"] for it in gram_items
        if not it.get("ejemplo") or not it.get("uso")
    ]
    if incompletos_gram:
        avisos.append(
            f"gramatica: {len(incompletos_gram)} puntos sin ejemplo/uso "
            f"(se corrige en Fase 05): {incompletos_gram[:15]}"
            + (" ..." if len(incompletos_gram) > 15 else "")
        )

    print(f"Unidades: {len(CURRICULUM)} · vocabulario: {len(vocab_items)} · gramatica: {len(gram_items)}")

    for aviso in avisos:
        print(f"AVISO (tolerado en Fase 01): {aviso}")

    if errores:
        print(f"\n{len(errores)} ERROR(ES):")
        for e in errores:
            print(f"  - {e}")
        return 1

    print("\nOK: validar_curriculum.py sin errores duros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
