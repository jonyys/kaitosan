#!/usr/bin/env python
"""Fase 01 del plan can-do N5 — invariantes del temario (`ai/sensei/curriculum.py`).

Uso: `python scripts/validar_curriculum.py`. Sale con código != 0 si algún
check DURO falla. No modifica `curriculum.py`.

Checks duros (fallan hoy si se rompen):
  - todo `jp` es japonés válido (contiene al menos un carácter kana/kanji).

Checks duros de contenido (Fase 05 en adelante):
  - todo punto de gramática tiene `ejemplo` y `uso` no vacíos (los 90).
  - `meaning` sin inglés en gramática y en el vocabulario que lleva `uso`.
  - si un ítem de vocabulario lleva `uso`, no está vacío de texto español.

Checks tolerantes (solo avisan por stdout):
  - `jp` único dentro de vocabulario y dentro de gramática por separado.
  - todo ítem de vocabulario tiene `kind`, `reading` y `meaning` no vacíos.
  - `uso` de vocabulario con japonés fuera de 「」 (las notas anteriores a la
    Fase 05 lo usan como estilo de casa; las nuevas no).

Checks duros de can-dos (Fase 06 en adelante):
  - todo `can_do['id']` es único en todo el `CURRICULUM`.
  - todo can-do tiene `texto` no vacío.
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


# Palabras función inglesas que delatan una glosa EN->ES sin traducir.
INGLES_RE = re.compile(
    r"\b(the|and|of|is|are|was|were|with|for|you|your|yours|that|this|these|those|"
    r"they|them|their|there|what|when|where|which|who|whom|whose|from|have|has|"
    r"had|will|would|should|could|about|into|than|then|because|its|it's)\b",
    re.IGNORECASE,
)
# Letras del español; si el `uso` no tiene ninguna, no es una nota en español.
ES_LETRA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")


def sin_citas(texto):
    return re.sub("「[^」]*」", "", texto or "")


def tiene_ingles(texto):
    return bool(INGLES_RE.search(sin_citas(texto)))


def japones_fuera_de_cita(texto):
    return bool(JP_CHAR_RE.search(sin_citas(texto)))


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

    # --- gramática: ejemplo/uso no vacíos (DURO desde Fase 05) ---
    incompletos_gram = [
        it["jp"] for it in gram_items
        if not (it.get("ejemplo") or "").strip() or not (it.get("uso") or "").strip()
    ]
    if incompletos_gram:
        errores.append(
            f"gramatica: {len(incompletos_gram)} puntos sin ejemplo/uso: {incompletos_gram}"
        )

    # --- meaning sin inglés: gramática (todos) + vocab que lleva uso (DURO) ---
    meaning_ingles = [
        f"{it['kind']}:{it['jp']}" for it in gram_items + vocab_items
        if (it["kind"] == "gramatica" or (it.get("uso") or "").strip())
        and tiene_ingles(it.get("meaning", ""))
    ]
    if meaning_ingles:
        errores.append(
            f"{len(meaning_ingles)} meaning con inglés sin traducir: {meaning_ingles}"
        )

    # --- uso de vocabulario: opcional, pero si está debe ser español (DURO) ---
    uso_no_es = [
        it["jp"] for it in vocab_items
        if (it.get("uso") or "").strip() and not ES_LETRA_RE.search(sin_citas(it["uso"]))
    ]
    if uso_no_es:
        errores.append(f"vocabulario: {len(uso_no_es)} `uso` sin texto en español: {uso_no_es}")

    # --- uso de vocabulario con japonés fuera de 「」 (TOLERANTE: estilo de casa) ---
    uso_jp_suelto = [
        it["jp"] for it in vocab_items
        if (it.get("uso") or "").strip() and japones_fuera_de_cita(it["uso"])
    ]
    if uso_jp_suelto:
        avisos.append(
            f"vocabulario: {len(uso_jp_suelto)} `uso` con japonés fuera de 「」 "
            f"(las notas previas a la Fase 05 lo usan como estilo de casa)"
        )

    # --- can-dos: id único en todo el temario + texto no vacío (DURO, Fase 06) ---
    can_do_ids = [
        cd.get("id") for u in CURRICULUM for cd in u.get("can_dos", [])
    ]
    dup_can_do = sorted({i for i, n in Counter(can_do_ids).items() if n > 1})
    if dup_can_do:
        errores.append(f"can_do.id duplicados en el temario: {dup_can_do}")
    can_do_sin_texto = [
        cd.get("id") for u in CURRICULUM for cd in u.get("can_dos", [])
        if not (cd.get("texto") or "").strip()
    ]
    if can_do_sin_texto:
        errores.append(f"can-dos con texto vacío: {can_do_sin_texto}")

    print(f"Unidades: {len(CURRICULUM)} · vocabulario: {len(vocab_items)} · gramatica: {len(gram_items)} · can-dos: {len(can_do_ids)}")

    for aviso in avisos:
        print(f"AVISO (tolerado): {aviso}")

    if errores:
        print(f"\n{len(errores)} ERROR(ES):")
        for e in errores:
            print(f"  - {e}")
        return 1

    print("\nOK: validar_curriculum.py sin errores duros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
