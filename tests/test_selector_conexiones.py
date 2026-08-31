"""Fase 10 — el selector de temario resuelve el recorrido en memoria."""
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


def _contando_conexiones(jap):
    original, jap.conexiones = jap._conectar, 0

    def espia():
        jap.conexiones += 1
        return original()

    jap._conectar = espia
    return jap


def test_recorrido_completo_son_dos_conexiones():
    jap = _contando_conexiones(_bd_llena())
    unidad_actual(jap)
    siguiente_items_nuevos(jap, 2)
    assert jap.conexiones == 2, jap.conexiones


def test_con_la_bd_llena_no_quedan_items_nuevos():
    jap = _bd_llena()
    assert siguiente_items_nuevos(jap, 2) == []
    # los ítems están, pero sin repasos: la unidad abierta sigue siendo la primera
    assert unidad_actual(jap)["id"] == CURRICULUM[0]["id"]


if __name__ == "__main__":
    test_recorrido_completo_son_dos_conexiones()
    test_con_la_bd_llena_no_quedan_items_nuevos()
    print("OK")
