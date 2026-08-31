"""Fase 13 — memoria episódica: Laura y Kaito se recuerdan de una sesión a otra."""
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones


def _profesor(jap=None):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    jap = jap or JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def test_resumen_perfil_devuelve_episodios_y_anecdotas():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    jap.guardar_episodios(1, ["fue al médico por el hombro", "  ", None])
    jap.guardar_anecdotas_kaito(1, ["dice que le gusta el ramen"])

    perfil = jap.resumen_perfil()
    assert perfil["episodios_laura"] == ["fue al médico por el hombro"]
    assert perfil["anecdotas_kaito"] == ["dice que le gusta el ramen"]


def test_kaito_saca_lo_personal_sin_que_se_lo_recuerden():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    prof = _profesor(jap)

    prof.entrar()
    prof.mensajes = [{"role": "user", "content": "hoy fui al médico por el hombro"}]
    prof.provider.completar.return_value = json.dumps({
        "summary": "Laura contó que fue al médico.",
        "reviewed": [], "new_items": [], "sin_corregir": [],
        "episodios": ["fue al médico por el hombro"],
        "kaito_dijo": ["dice que le encanta el ramen"],
    })
    prof._ejecutar_extraccion(prof.session_id)

    prof.entrar()  # sesión nueva, sin que nadie se lo recuerde
    recuerdas = prof._montar_estado()[0]
    assert "fue al médico por el hombro" in recuerdas
    assert "dice que le encanta el ramen" in recuerdas


def test_ultimas_sesiones_son_las_tres_mas_recientes_no_solo_una():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    for i in range(4):
        sid = jap.crear_sesion() if hasattr(jap, "crear_sesion") else None
        if sid is None:
            with jap._conectar() as conn:
                cur = conn.execute("INSERT INTO japanese_sessions (started_at) VALUES (datetime('now', ?))",
                                    (f"+{i} seconds",))
                sid = cur.lastrowid
        jap.guardar_resumen_sesion(sid, summary=f"resumen {i}")

    perfil = jap.resumen_perfil()
    assert len(perfil["last_sessions"]) == 3
    assert perfil["last_sessions"][0] == "resumen 3"  # la más reciente primero
    assert "resumen 0" not in perfil["last_sessions"]  # la más vieja no cabe
    assert perfil["last_session_summary"] == "resumen 3"  # compat con la clave vieja


if __name__ == "__main__":
    test_resumen_perfil_devuelve_episodios_y_anecdotas()
    test_kaito_saca_lo_personal_sin_que_se_lo_recuerden()
    test_ultimas_sesiones_son_las_tres_mas_recientes_no_solo_una()
    print("OK")
