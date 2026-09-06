"""Un solo modo sensei (profe particular medio colega): no hay dial de registro."""
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.prompts import cargar_prompt
from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones


def _profesor(jap=None):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    jap = jap or JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def test_prompt_sin_dial_de_registro():
    prompt = cargar_prompt("profesor_japones")
    assert "{REGISTRO}" not in prompt
    # los tres registros viejos ya no se nombran como modos
    assert "registro clase" not in prompt
    assert "En mixto y charla" not in prompt


def test_el_prompt_llega_al_sistema_sin_placeholders():
    prof = _profesor()
    prof.entrar()
    prof.provider.completar.return_value = "vale 【はい】"
    prof.responder_turno("hola")
    sistema = prof.provider.completar.call_args[0][0][0]["content"]
    assert "{REGISTRO}" not in sistema and "{NIVEL_INMERSION}" not in sistema
    # modo_conv sigue existiendo para el enrutado de STT, y es siempre False
    assert prof.modo_conv is False


def test_explicar_no_esta_vetado():
    prompt = cargar_prompt("profesor_japones")
    assert "Nunca tienes prohibido explicar" in prompt


def test_lo_que_no_se_corrige_vuelve_en_la_sesion_siguiente():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    prof = _profesor(jap)
    prof.entrar()
    prof.mensajes = [{"role": "user", "content": "わたし は のんだ"}]
    prof.provider.completar.return_value = json.dumps(
        {"summary": "Laura practicó el pasado casual.", "reviewed": [], "new_items": [],
         "sin_corregir": ["separó は de わたし"]}
    )
    prof._ejecutar_extraccion(prof.session_id)

    prof.entrar()  # sesión nueva
    recuerdas = prof._montar_estado()[0]
    assert "Quedó sin corregir: separó は de わたし" in recuerdas


if __name__ == "__main__":
    test_prompt_sin_dial_de_registro()
    test_el_prompt_llega_al_sistema_sin_placeholders()
    test_explicar_no_esta_vetado()
    test_lo_que_no_se_corrige_vuelve_en_la_sesion_siguiente()
    print("OK")
