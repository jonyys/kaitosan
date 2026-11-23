"""La clase abre repasando lo anterior (un dominado si no hay pendientes) y retoma lo guardado."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM
from ai.sensei.profesor import ProfesorJapones
from core.japanese_memory import JapaneseMemory

CD = "saludos_gracias"  # items: ありがとう, どうも, いいえ, どうぞ


def _profe(tmp_path):
    jm = JapaneseMemory(str(tmp_path / "j.db"))
    p = ProfesorJapones(jm, MagicMock(), MagicMock(), MagicMock())
    p.session_id = 7
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "saludos_basicos")
    return jm, p


def test_abre_con_un_dominado_y_retoma_solo_lo_guardado(tmp_path):
    jm, p = _profe(tmp_path)
    for s in (1, 2, 3):
        jm.set_can_do("saludos_saludar", "conseguido", s)
    assert jm.can_dos_progreso()["saludos_saludar"]["estado"] == "dominado"
    p._empezar_clase()
    assert (p.clase["cd"], p.clase["tipo"]) == ("saludos_saludar", "antiguo")
    assert "según tus notas" not in p._instruccion("hola")  # nada guardado: nada que retomar

    # con datos guardados, nueva clase
    sid = 9
    with jm._conectar() as c:
        c.execute("INSERT INTO japanese_sessions (id, started_at, errors_noted, nota_profe) VALUES (?, '2026-01-01', ?, ?)",
                  (sid, "confunde は y が", "va bien"))
    p._empezar_clase()
    out = p._instruccion("hola")
    assert "según tus notas de la última clase: confunde は y が; va bien" in out and "no lo menciones" in out
    # una vez cerrado cuenta en hechos y no se repite
    p._cerrar_cd(next(c for c in p._cds() if c["id"] == "saludos_saludar"), "conseguido")
    assert "saludos_saludar" in p.clase["hechos"] and p.clase["cd"] != "saludos_saludar"
