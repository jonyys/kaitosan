"""Modo charla (SENSEI_CHARLA=1): prompt mínimo, sin can-dos ni instrucción, historial entero y resumen."""
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei import profesor as P
from ai.sensei.profesor import ProfesorJapones


def _prof(monkeypatch, respuestas):
    monkeypatch.setenv("SENSEI_CHARLA", "1")
    monkeypatch.setenv("LLM_STREAMING", "0")
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prov = MagicMock()
    prov.completar.side_effect = respuestas
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    p = ProfesorJapones(jap, prov, memoria, MagicMock())
    p.entrar()
    return p, prov


def test_sin_cando_ni_instruccion(monkeypatch):
    p, prov = _prof(monkeypatch, ["【こんにちは】 Hola.\nPIZARRA: こんにちは = hola"])
    assert p.clase["cd"] is None and p.clase["fase"] == "libre" and not p.espera_japones
    p.responder_turno("hola")
    msgs = prov.completar.call_args[0][0]
    assert "ラウラ" in msgs[0]["content"] and "INSTRUCCIÓN" not in msgs[-1]["content"]
    assert msgs[-1]["content"].startswith("hola")


def test_resume_lo_viejo_y_conserva_el_historial_entero(monkeypatch):
    monkeypatch.setattr(P, "RESUMIR_A", 6)
    monkeypatch.setattr(P, "CONSERVAR", 2)
    p, prov = _prof(monkeypatch, None)
    prov.completar.side_effect = lambda m, **kw: (
        "Laura tiene un gato, Miso" if m[0]["content"].startswith("Resume") else "Vale.\nPIZARRA: -")
    for i in range(4):
        p.responder_turno(f"mensaje {i}")
    p._fut_resumen.result(timeout=5)
    p.responder_turno("mensaje 4")
    msgs = [c[0][0] for c in prov.completar.call_args_list if c[0][0][0]["role"] == "system"][-1]
    assert "Miso" in msgs[0]["content"]                       # el resumen va en el sistema
    assert len(msgs) < 1 + len(p.mensajes)                    # el LLM ve menos que el historial...
    assert len(p.mensajes) == 10                              # ...pero el historial completo se guarda
