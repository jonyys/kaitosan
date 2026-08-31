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


def test_el_foco_abre_con_la_funcion_de_la_unidad():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())

    prof.entrar()
    foco = prof._montar_estado()[1]
    lineas = foco.split("\n")

    unidad = CURRICULUM[0]
    assert lineas[0] == f"Unidad actual: {unidad['nombre']}"
    assert unidad["funcion"] in lineas[1]
    assert "【おつかれさま】" in foco
    # y los ítems del temario siguen ahí, detrás de la cabecera
    assert "Ítems nuevos a introducir" in foco


if __name__ == "__main__":
    test_las_34_unidades_tienen_funcion_y_frases()
    test_unidad_actual_en_bd_limpia_es_la_primera()
    test_el_foco_abre_con_la_funcion_de_la_unidad()
    print("OK")
