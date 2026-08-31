"""El FOCO de due items rota dentro de la sesión: el SRS no se recalifica hasta
cerrar, así que sin rotación el mismo lote se repetiría toda la clase."""
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones, TURNOS_POR_ITEM_FOCO


def _profesor_con_vocab(n):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    for i in range(n):
        jap.add_item("vocabulario", f"palabra{i}", meaning=f"meaning{i}")
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())
    prof.entrar()
    return prof


def _en_lista_de_repaso(foco, jp):
    """True si jp aparece como ítem 'para repasar' (no solo mencionado en la
    línea de 'ya trabajados')."""
    return f"- 【{jp}】" in foco


def test_tras_N_turnos_el_item_cede_paso_al_siguiente():
    prof = _profesor_con_vocab(6)  # más que el límite de 5 por turno

    _, foco_1 = prof._montar_estado()
    assert _en_lista_de_repaso(foco_1, "palabra0")

    # Sigue arriba mientras no llegue al umbral
    for _ in range(TURNOS_POR_ITEM_FOCO - 1):
        _, foco = prof._montar_estado()
        assert _en_lista_de_repaso(foco, "palabra0")

    # En el turno TURNOS_POR_ITEM_FOCO cede el sitio al siguiente due
    _, foco_final = prof._montar_estado()
    assert not _en_lista_de_repaso(foco_final, "palabra0")
    assert _en_lista_de_repaso(foco_final, "palabra5")  # el 6º, que antes no cabía en el límite de 5


def test_los_agotados_se_listan_para_no_perderse_del_contexto():
    prof = _profesor_con_vocab(1)
    for _ in range(TURNOS_POR_ITEM_FOCO):
        prof._montar_estado()

    _, foco = prof._montar_estado()
    assert "Ya trabajados en esta sesión" in foco
    assert "palabra0" in foco  # sigue mencionado, aunque ya no esté "para repasar"


def test_la_rotacion_se_reinicia_en_una_sesion_nueva():
    prof = _profesor_con_vocab(1)
    for _ in range(TURNOS_POR_ITEM_FOCO + 1):
        prof._montar_estado()
    assert prof._foco_agotados  # se agotó en la sesión anterior

    prof.entrar()  # sesión nueva
    _, foco = prof._montar_estado()
    assert "palabra0" in foco
    assert "Ya trabajados en esta sesión" not in foco


if __name__ == "__main__":
    test_tras_N_turnos_el_item_cede_paso_al_siguiente()
    test_los_agotados_se_listan_para_no_perderse_del_contexto()
    test_la_rotacion_se_reinicia_en_una_sesion_nueva()
    print("OK")
