#!/usr/bin/env python
"""Fase 05 del plan can-do N5 — ensambla el contenido didáctico generado por
Claude (`scripts/_fase05_contenido.json`) sobre `ai/sensei/curriculum.py`.

Uso: `python scripts/generar_contenido.py [--check]`

Determinista. Dos bloques de `_fase05_contenido.json`:

  · "gramatica": para los ~52 puntos de gramática N5 que entraron sin contenido
    en la Fase 03 (los que hoy tienen `ejemplo` vacío), fija `meaning` afinado +
    `ejemplo` (frase N5 que usa el patrón, solo kana/kanji) + `literal` (desglose
    con `/`) + `uso` (matiz/registro, japonés solo dentro de 「」). Los ~38 puntos
    que ya traían los 4 campos NO se tocan.

  · "vocabulario": para los ítems de vocabulario N5 (no kanji) SIN `uso`, y solo
    donde el matiz lo pide, fija `uso` (español; japonés solo dentro de 「」). NO
    se generan `ejemplo` ni `literal` de vocabulario. Los ítems que ya tenían
    `uso` quedan intactos.

El literal `CURRICULUM = [...]` se extrae y se reescribe con el mismo
serializador determinista de la Fase 02/03 (`reconciliar_vocab.extraer_literal_curriculum`
/ `formatear`), de modo que el diff toca solo los campos que cambian.

Con `--check`: no escribe; sale != 0 si el JSON no cuadra con el curriculum
(claves que no corresponden a un ítem rellenable) o si el resultado dejaría
algún punto de gramática sin `ejemplo`/`uso`.
"""
import json
import re
import sys
from pathlib import Path

# Consola Windows por defecto = cp1252; forzamos UTF-8 para imprimir japonés.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconciliar_vocab import extraer_literal_curriculum, formatear  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CURRICULUM_PY = RAIZ / "ai" / "sensei" / "curriculum.py"
CONTENIDO_JSON = Path(__file__).resolve().parent / "_fase05_contenido.json"

CAMPOS_GRAM = ("meaning", "ejemplo", "literal", "uso")


def aplicar(units, contenido):
    gram_json = contenido.get("gramatica", {})
    vocab_json = contenido.get("vocabulario", {})

    problemas = []
    n_gram = n_vocab = 0
    gram_pendientes = set(gram_json)
    vocab_pendientes = set(vocab_json)

    for u in units:
        for it in u["items"]:
            jp = it.get("jp")
            if it["kind"] == "gramatica" and jp in gram_json:
                if it.get("ejemplo", "").strip():
                    problemas.append(
                        f"gramatica {jp!r} ya tenía ejemplo; el JSON no debería tocarlo"
                    )
                    continue
                datos = gram_json[jp]
                for c in CAMPOS_GRAM:
                    if not datos.get(c, "").strip():
                        problemas.append(f"gramatica {jp!r}: campo {c} vacío en el JSON")
                    it[c] = datos[c]
                gram_pendientes.discard(jp)
                n_gram += 1
            elif it["kind"] == "vocabulario" and it.get("tipo") != "kanji" and jp in vocab_json:
                if it.get("uso", "").strip():
                    problemas.append(
                        f"vocabulario {jp!r} ya tenía uso; el JSON no debería tocarlo"
                    )
                    continue
                it["uso"] = vocab_json[jp]
                vocab_pendientes.discard(jp)
                n_vocab += 1

    if gram_pendientes:
        problemas.append(
            f"claves de gramatica en el JSON sin ítem rellenable: {sorted(gram_pendientes)}"
        )
    if vocab_pendientes:
        problemas.append(
            f"claves de vocabulario en el JSON sin ítem rellenable: {sorted(vocab_pendientes)}"
        )

    # invariante final: los 90 puntos de gramática con ejemplo y uso
    sin_contenido = [
        it["jp"] for u in units for it in u["items"]
        if it["kind"] == "gramatica" and (not it.get("ejemplo", "").strip()
                                          or not it.get("uso", "").strip())
    ]
    if sin_contenido:
        problemas.append(f"puntos de gramática sin ejemplo/uso tras aplicar: {sin_contenido}")

    return n_gram, n_vocab, problemas


def main():
    check = "--check" in sys.argv[1:]
    src = CURRICULUM_PY.read_text(encoding="utf-8")
    ini, fin, units = extraer_literal_curriculum(src)
    contenido = json.loads(CONTENIDO_JSON.read_text(encoding="utf-8"))

    n_gram, n_vocab, problemas = aplicar(units, contenido)

    gram_total = sum(1 for u in units for it in u["items"] if it["kind"] == "gramatica")
    print(f"gramática rellenada: {n_gram}  ·  vocabulario con uso nuevo: {n_vocab}")
    print(f"puntos de gramática en el temario: {gram_total}")

    if problemas:
        for p in problemas:
            print(f"ERROR: {p}")
        return 1

    if check:
        print("\nOK (--check): el JSON cuadra con el curriculum. No se ha escrito nada.")
        return 0

    cuerpo = formatear(units, 0)
    # `formatear` no emite coma tras el último elemento; el literal actual de
    # curriculum.py sí la lleva (la dejó el cirujano de texto de la Fase 04 al
    # borrar la última unidad). Se conserva para que el diff sea solo contenido.
    if re.search(r",\s*\]\s*\Z", src[ini:fin]):
        cuerpo = re.sub(r"\}\s*\]\s*\Z", "},\n]", cuerpo)
    nuevo_src = src[:ini] + cuerpo + src[fin:]
    if nuevo_src == src:
        print("\nSin cambios: curriculum.py ya tiene el contenido de la Fase 05.")
        return 0
    CURRICULUM_PY.write_text(nuevo_src, encoding="utf-8")
    print(f"\nOK: {CURRICULUM_PY} reescrito.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
