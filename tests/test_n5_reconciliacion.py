"""Fase 02/03 — vocabulario y gramática de `curriculum.py` son exactamente las
listas N5 oficiales.

La Fase 04 añadirá aquí `test_sin_n4n3`, etc.

Nota: los ítems de las unidades de kanji también llevan `kind == "vocabulario"`
(reutilizan el mismo SRS) pero se distinguen por `tipo == "kanji"`. El
vocabulario "hablado" del temario es el que NO es kanji.
"""
import csv
import json
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_N5 = os.path.join(RAIZ, "data", "n5_vocab.csv")
CSV_GRAM = os.path.join(RAIZ, "data", "n5_grammar.csv")
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


def _csv_jp_gramatica():
    with open(CSV_GRAM, encoding="utf-8") as f:
        return [ln.split(",", 1)[0] for ln in f.read().splitlines()[1:] if ln.strip()]


def _gram_items():
    return [it for u in CURRICULUM for it in u["items"] if it["kind"] == "gramatica"]


def test_gramatica():
    """Fase 03: la gramática del temario es EXACTAMENTE la lista tanos N5."""
    curr = [it["jp"] for it in _gram_items()]
    csv_jp = _csv_jp_gramatica()

    assert len(csv_jp) == len(set(csv_jp)), "data/n5_grammar.csv tiene jp duplicados"
    dups = sorted({jp for jp in curr if curr.count(jp) > 1})
    assert not dups, f"puntos de gramática duplicados en CURRICULUM: {dups}"

    assert set(curr) == set(csv_jp), {
        "sobran_en_curriculum": sorted(set(curr) - set(csv_jp)),
        "faltan_en_curriculum": sorted(set(csv_jp) - set(curr)),
    }


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


# ── Fase 04 ───────────────────────────────────────────────────────────────────

def test_sin_n4n3():
    """Tras Fase 03 había 53 unidades; la Fase 04 borra las 13 que quedaron con
    items == [] (grupos_verbales + 12 unidades N4/N3) → 40 unidades N5."""
    assert len(CURRICULUM) == 40, len(CURRICULUM)
    assert [u["id"] for u in CURRICULUM if not u["items"]] == []
    con_nivel = [
        u["id"] for u in CURRICULUM
        if "n4" in u["id"].lower() or "n3" in u["id"].lower()
        or "N4" in u.get("nombre", "") or "N3" in u.get("nombre", "")
    ]
    assert con_nivel == [], con_nivel


def test_purgar_fuera_de_temario():
    from core.japanese_memory import JapaneseMemory

    jm = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    with jm._conectar() as c:
        c.execute("INSERT INTO japanese_vocabulary (word) VALUES ('水')")  # (a) temario
        c.execute("INSERT INTO japanese_vocabulary (word, first_taught_session_id) "
                  "VALUES ('たぬき', 7)")                                    # (b) pedido en sesión
        c.execute("INSERT INTO japanese_vocabulary (word) VALUES ('狸オバケ')")  # (c) huérfano
        c.execute("INSERT INTO japanese_grammar (grammar_point) VALUES ('〜んです')")
        c.execute("INSERT INTO japanese_grammar (grammar_point) VALUES ('〜べからず')")
        c.execute("INSERT INTO japanese_grammar (grammar_point, first_taught_session_id) "
                  "VALUES ('〜ませ', 3)")

    jps_vocab, jps_gram = {"水"}, {"〜んです"}
    assert jm.purgar_fuera_de_temario(jps_vocab, jps_gram) == (1, 1)
    assert set(jm.vocab_rows()) == {"水", "たぬき"}
    assert set(jm.gram_rows()) == {"〜んです", "〜ませ"}

    # idempotente: segunda pasada no cambia nada
    assert jm.purgar_fuera_de_temario(jps_vocab, jps_gram) == (0, 0)
    assert set(jm.vocab_rows()) == {"水", "たぬき"}
    assert set(jm.gram_rows()) == {"〜んです", "〜ませ"}


if __name__ == "__main__":
    test_vocab_es_exactamente_la_lista_n5()
    test_sin_jp_de_vocabulario_duplicado()
    test_todo_item_tiene_reading_y_meaning()
    test_gramatica()
    test_items_conservados_mantienen_su_texto_verbatim()
    test_sin_n4n3()
    test_purgar_fuera_de_temario()
    print("OK")
