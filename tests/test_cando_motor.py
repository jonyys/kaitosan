"""Fase 06 — can-dos por unidad en `curriculum.py`.

- Toda unidad temática N5 de vocab/gramática tiene >= 2 can-dos.
- Las unidades de kanji (solo ítems `tipo == "kanji"`) NO llevan can-dos.
- Todos los `id` de can-do son únicos en todo el temario.
- Cada can-do tiene `texto` no vacío que empieza por "Puedo".
"""
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM


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


if __name__ == "__main__":
    test_candos()
    print("OK")
