"""Fase 02 — el vocabulario de `curriculum.py` es exactamente la lista N5 oficial.

La Fase 03/04 añadirá aquí `test_gramatica`, `test_sin_n4n3`, etc.

Nota: los ítems de las unidades de kanji también llevan `kind == "vocabulario"`
(reutilizan el mismo SRS) pero se distinguen por `tipo == "kanji"`. El
vocabulario "hablado" del temario es el que NO es kanji.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_N5 = os.path.join(RAIZ, "data", "n5_vocab.csv")
SNAPSHOT = os.path.join(os.path.dirname(__file__), "fixtures", "vocab_pre_fase02.json")

CAMPOS_TEXTO = ("reading", "meaning", "tipo", "ejemplo", "literal", "uso")


def _vocab_items():
    return [
        it
        for u in CURRICULUM
        for it in u["items"]
        if it["kind"] == "vocabulario" and it.get("tipo") != "kanji"
    ]


def _csv_jp():
    with open(CSV_N5, encoding="utf-8", newline="") as f:
        return {fila["expression"] for fila in csv.DictReader(f)}


def test_vocab_es_exactamente_la_lista_n5():
    en_curriculum = {it["jp"] for it in _vocab_items()}
    assert en_curriculum == _csv_jp()


def test_sin_jp_de_vocabulario_duplicado():
    jps = [it["jp"] for it in _vocab_items()]
    dups = sorted({jp for jp in jps if jps.count(jp) > 1})
    assert not dups, dups


def test_todo_item_tiene_reading_y_meaning():
    faltan = [it["jp"] for it in _vocab_items() if not it.get("reading") or not it.get("meaning")]
    assert not faltan, faltan


def test_items_conservados_mantienen_su_texto_verbatim():
    """Los ítems que ya existían y siguen en la lista conservan sus campos de
    texto (uso incluido) carácter a carácter respecto al snapshot pre-Fase 02."""
    snap = json.load(open(SNAPSHOT, encoding="utf-8"))
    actuales = {it["jp"]: it for it in _vocab_items()}
    revisados = 0
    for jp, previo in snap.items():
        if jp not in actuales:
            continue  # se eliminó por no estar en la lista N5: correcto
        revisados += 1
        for campo in CAMPOS_TEXTO:
            assert actuales[jp].get(campo, "") == previo.get(campo, ""), (jp, campo)
    # el snapshot tiene 299 jp; en la lista N5 sobreviven ~202
    assert revisados >= 200, revisados


if __name__ == "__main__":
    test_vocab_es_exactamente_la_lista_n5()
    test_sin_jp_de_vocabulario_duplicado()
    test_todo_item_tiene_reading_y_meaning()
    test_items_conservados_mantienen_su_texto_verbatim()
    print("OK")
