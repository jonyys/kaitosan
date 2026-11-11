"""Fase 09 — cada unidad dice qué sabrá hacer Laura y con qué frases hechas."""
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.curriculum import CURRICULUM, unidad_actual
from ai.sensei.profesor import ProfesorJapones


def test_las_34_unidades_tienen_funcion_y_frases():
    for unit in CURRICULUM:
        assert unit.get("funcion"), unit["id"]
        frases = unit.get("frases_hechas") or []
        assert len(frases) >= 3, (unit["id"], len(frases))
        for f in frases:
            assert f.get("jp") and f.get("uso"), (unit["id"], f)


def test_unidad_actual_en_bd_limpia_es_la_primera():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    assert unidad_actual(jap)["id"] == "saludos_basicos"


if __name__ == "__main__":
    test_las_34_unidades_tienen_funcion_y_frases()
    test_unidad_actual_en_bd_limpia_es_la_primera()
    print("OK")
