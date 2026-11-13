"""Resumen que se enseña al salir del modo sensei: kana, conseguidos de la sesión, vacío si nada."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.profesor import ProfesorJapones


def _profe():
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p.clase = {"cd": None, "fase": "libre", "hechos": []}
    p.mensajes = []
    return p


def test_resumen_vacio_si_no_hubo_nada():
    assert _profe().resumen_clase() == {}


def test_resumen_con_conseguidos_y_palabras_en_kana():
    p = _profe()
    p.clase["logros"] = ["saludos_saludar"]
    p.mensajes = [{"role": "assistant", "content": "Hola"},
                  {"role": "user", "content": "hola"},
                  {"role": "assistant", "content": "Repite: 【おはようございます】"}]
    r = p.resumen_clase()
    assert r["titulo"] and r["logros"] == ["Puedo saludar y despedirme según la hora del día"]
    assert r["palabras"] == [{"jp": "おはようございます", "es": "buenos días"}]


def test_salir_emite_el_resumen_antes_de_extraer():
    p = _profe()
    p.activo = True
    p.salir()
    assert p.socketio.emit.call_args.args == ("sensei_resumen", {})
    p.socketio.start_background_task.assert_called_once()


def test_cerrar_cd_guarda_solo_los_conseguidos():
    p = _profe()
    p._siguiente = lambda: (None, None)
    p.session_id = 1
    cd = {"id": "saludos_saludar"}
    p._cerrar_cd(cd, "parcial")
    p._cerrar_cd(cd, "conseguido")
    assert p.clase["logros"] == ["saludos_saludar"]
