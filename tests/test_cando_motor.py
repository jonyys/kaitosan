"""Fase 06 — can-dos por unidad en `curriculum.py`.

- Toda unidad temática N5 de vocab/gramática tiene >= 2 can-dos.
- Las unidades de kanji (solo ítems `tipo == "kanji"`) NO llevan can-dos.
- Todos los `id` de can-do son únicos en todo el temario.
- Cada can-do tiene `texto` no vacío que empieza por "Puedo".
"""
import os
import sys
import tempfile
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM
from core.japanese_memory import JapaneseMemory


def _es_tematica(unidad):
    return any(
        it["kind"] == "gramatica"
        or (it["kind"] == "vocabulario" and it.get("tipo") != "kanji")
        for it in unidad["items"]
    )


def test_candos():
    tematicas = [u for u in CURRICULUM if _es_tematica(u)]
    kanji = [u for u in CURRICULUM if not _es_tematica(u)]
    assert tematicas, "no hay unidades temáticas"

    sin_candos = [u["id"] for u in tematicas if len(u.get("can_dos", [])) < 2]
    assert not sin_candos, f"unidades temáticas con < 2 can-dos: {sin_candos}"

    kanji_con_candos = [u["id"] for u in kanji if u.get("can_dos")]
    assert not kanji_con_candos, f"unidades de kanji con can-dos: {kanji_con_candos}"

    ids = [cd["id"] for u in CURRICULUM for cd in u.get("can_dos", [])]
    dups = sorted({i for i, n in Counter(ids).items() if n > 1})
    assert not dups, f"can_do.id duplicados: {dups}"

    for u in CURRICULUM:
        for cd in u.get("can_dos", []):
            texto = (cd.get("texto") or "").strip()
            assert texto.startswith("Puedo"), (u["id"], cd.get("id"), texto)
            # id estable con prefijo de la unidad (o de un alias corto de ella)
            assert cd["id"] and cd["id"] == cd["id"].strip()


def _jm():
    return JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))


def test_set_can_do():
    jm = _jm()

    jm.set_can_do("x", "conseguido", 1)
    p = jm.can_dos_progreso()["x"]
    assert p["estado"] == "en_progreso" and p["veces_ok"] == 1

    jm.set_can_do("x", "conseguido", 2)
    assert jm.can_dos_progreso()["x"]["estado"] == "dominado"

    jm.set_can_do("x", "error", 3)
    p = jm.can_dos_progreso()["x"]
    assert p["estado"] == "en_progreso"
    assert p["ultima_sesion"] == 3

    # dos 'conseguido' en la MISMA sesión no bastan para dominar
    jm2 = _jm()
    jm2.set_can_do("y", "conseguido", 7)
    jm2.set_can_do("y", "conseguido", 7)
    p = jm2.can_dos_progreso()["y"]
    assert p["estado"] == "en_progreso" and p["veces_ok"] == 1


# Oráculo: transcripción textual de las clausuras `estado()` originales de
# `app.py:_temario_unidades()` (commit ae32cc8), con el renombrado 1:1 de la
# Fase 07. Se replican aquí en vez de importar app.py (que arrastra Flask+brain).
def _oraculo(kind, row):
    """row = (reps, status|mastery) o None."""
    if row is None:
        return "nueva"
    a, b = row
    if kind == "gramatica":
        aprendida = (a or 0) >= 2 or (b or 0) >= 100
    else:
        aprendida = (a or 0) >= 2 or b in ("learned", "mastered")
    return "aprendida" if aprendida else "en_curso"


_MAP = {"aprendida": "sabido", "en_curso": "en_progreso", "nueva": "nuevo"}


def test_estado_item_igual_que_pagina():
    jm = _jm()
    with jm._conectar() as c:
        # (reps, status) -> word
        vocab = {
            "v_learning": (0, "learning"),
            "v_reps2": (2, "learning"),
            "v_learned": (0, "learned"),
            "v_mastered": (0, "mastered"),
            "v_reps1": (1, "learning"),
        }
        for w, (reps, status) in vocab.items():
            c.execute(
                "INSERT INTO japanese_vocabulary (word, reps, status) VALUES (?, ?, ?)",
                (w, reps, status),
            )
        gram = {
            "g_cero": (0, 0),
            "g_reps2": (2, 0),
            "g_mastery100": (0, 100),
            "g_reps1": (1, 50),
        }
        for gp, (reps, mastery) in gram.items():
            c.execute(
                "INSERT INTO japanese_grammar (grammar_point, reps, mastery) VALUES (?, ?, ?)",
                (gp, reps, mastery),
            )

    for w, row in {**vocab, "v_ausente": None}.items():
        assert jm.estado_item(w, "vocabulario") == _MAP[_oraculo("vocabulario", row)], w
    for gp, row in {**gram, "g_ausente": None}.items():
        assert jm.estado_item(gp, "gramatica") == _MAP[_oraculo("gramatica", row)], gp


def test_fraccion_can_dos():
    unidad = next(u for u in CURRICULUM if len(u.get("can_dos", [])) == 4)
    ids = [cd["id"] for cd in unidad["can_dos"]]
    jm = _jm()

    assert jm.fraccion_can_dos(unidad["id"]) == 0.0
    assert jm.fraccion_can_dos("unidad_inexistente") == 0.0

    for cid in ids[:2]:
        jm.set_can_do(cid, "conseguido", 1)
        jm.set_can_do(cid, "conseguido", 2)
    assert jm.fraccion_can_dos(unidad["id"]) == 0.5


if __name__ == "__main__":
    test_candos()
    test_set_can_do()
    test_estado_item_igual_que_pagina()
    test_fraccion_can_dos()
    print("OK")
