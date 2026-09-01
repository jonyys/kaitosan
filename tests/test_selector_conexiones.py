"""Fase 10 / 18 — el selector de temario avanza por progreso de can-dos."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.curriculum import CURRICULUM, siguiente_items_nuevos, unidad_actual


def _bd_llena():
    """Todas las unidades marcadas: el caso peor, el que recorre el temario entero."""
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    for unit in CURRICULUM:
        for item in unit["items"]:
            jap.add_item(item["kind"], item["jp"], reading=item.get("reading"),
                         meaning=item.get("meaning"), tipo=item.get("tipo"))
    return jap


def test_con_la_bd_llena_no_quedan_items_nuevos():
    jap = _bd_llena()
    assert siguiente_items_nuevos(jap, 2) == []
    # los ítems están, pero sin repasos: la unidad abierta sigue siendo la primera
    assert unidad_actual(jap)["id"] == CURRICULUM[0]["id"]


def test_unidad_actual_avanza_cuando_los_can_dos_estan_dominados():
    """El modelo can-do: unidad_actual sale de una unidad en cuanto la fracción
    de can-dos 'dominado' llega al umbral (fraccion_can_dos), sin mirar reps."""
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    primera = next(u for u in CURRICULUM if u.get("can_dos"))
    assert unidad_actual(jap)["id"] == primera["id"]

    for cd in primera["can_dos"]:
        jap.set_can_do(cd["id"], "conseguido", "s1")
        jap.set_can_do(cd["id"], "conseguido", "s2")  # 2 sesiones distintas -> dominado

    assert jap.fraccion_can_dos(primera["id"]) == 1.0
    assert unidad_actual(jap)["id"] != primera["id"]


if __name__ == "__main__":
    test_con_la_bd_llena_no_quedan_items_nuevos()
    test_unidad_actual_avanza_cuando_los_can_dos_estan_dominados()
    print("OK")
