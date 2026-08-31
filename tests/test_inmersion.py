"""Fase 12 — nivel de inmersión: cuánto japonés habla Kaito lo marca el progreso."""
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ai.sensei.profesor as prof_mod
from ai.prompts import cargar_prompt
from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones, _nivel_inmersion


def _profesor():
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def test_el_nivel_sube_con_el_vocabulario_dominado():
    def nivel(learned=0, mastered=0):
        return _nivel_inmersion({"vocab_by_status": {"learning": 30,
                                                     "learned": learned,
                                                     "mastered": mastered}})
    assert _nivel_inmersion({}) == 1          # BD vacía
    assert nivel() == 1
    assert nivel(learned=14) == 1
    assert nivel(learned=15) == 2             # umbral justo
    assert nivel(learned=20, mastered=20) == 3
    assert nivel(mastered=80) == 4
    assert nivel(mastered=500) == 4           # no se pasa de 4


def test_el_nivel_llega_al_prompt_y_se_puede_forzar_a_mano():
    prof = _profesor()
    prof.entrar()
    prof.provider.completar.return_value = "vale 【はい】"

    prof.responder_turno("hola")
    sistema = prof.provider.completar.call_args[0][0][0]["content"]
    assert "nivel: 1 (de 4)" in sistema
    assert "{NIVEL_INMERSION}" not in sistema

    prof_mod.NIVEL_INMERSION_FORZADO = 3
    try:
        prof.responder_turno("hola")
        sistema = prof.provider.completar.call_args[0][0][0]["content"]
        assert "nivel: 3 (de 4)" in sistema
    finally:
        prof_mod.NIVEL_INMERSION_FORZADO = None


def test_la_regla_de_oro_ya_no_prohibe_hablar_japones():
    prompt = cargar_prompt("profesor_japones")
    assert "{NIVEL_INMERSION}" in prompt
    assert "Respondes SIEMPRE en español" not in prompt
    assert "1 o 2 expresiones cortas" not in prompt
    # los 【】 siguen siendo obligatorios: el TTS los necesita
    assert "TODO el japonés va dentro de 【】" in prompt


if __name__ == "__main__":
    test_el_nivel_sube_con_el_vocabulario_dominado()
    test_el_nivel_llega_al_prompt_y_se_puede_forzar_a_mano()
    test_la_regla_de_oro_ya_no_prohibe_hablar_japones()
    print("OK")
