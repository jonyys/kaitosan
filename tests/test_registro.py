"""Fase 11 — un solo prompt con dial de registro, y la corrección que no se pierde."""
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.prompts import cargar_prompt
from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones, REGISTROS


def _profesor(jap=None):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    jap = jap or JapaneseMemory(os.path.join(tempfile.mkdtemp(), "test.db"))
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def test_solo_queda_un_prompt_de_profesor():
    assert "{REGISTRO}" in cargar_prompt("profesor_japones")
    try:
        cargar_prompt("profesor_japones_conv")
        assert False, "el prompt de charla debería haber desaparecido"
    except Exception:
        pass


def test_el_registro_llega_al_sistema_y_modo_conv_sigue_funcionando():
    prof = _profesor()
    for registro in REGISTROS:
        prof.entrar(registro=registro)
        prof.provider.completar.return_value = "vale 【はい】"
        prof.responder_turno("hola")
        sistema = prof.provider.completar.call_args[0][0][0]["content"]
        assert f"registro: {registro}" in sistema, registro
        assert "{REGISTRO}" not in sistema
        assert prof.modo_conv == (registro == "charla")

    # los disparadores viejos siguen mapeando a clase / charla
    prof.set_modo_conv(True)
    assert prof.registro == "charla" and prof.modo_conv
    prof.set_modo_conv(False)
    assert prof.registro == "clase" and not prof.modo_conv


def test_explicar_no_esta_vetado_en_ningun_registro():
    prompt = cargar_prompt("profesor_japones")
    assert "En NINGÚN registro tienes prohibido explicar" in prompt
    # la vieja prohibición del prompt de charla no vuelve por la puerta de atrás
    assert "estructura de clase" not in prompt


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
    test_solo_queda_un_prompt_de_profesor()
    test_el_registro_llega_al_sistema_y_modo_conv_sigue_funcionando()
    test_explicar_no_esta_vetado_en_ningun_registro()
    test_lo_que_no_se_corrige_vuelve_en_la_sesion_siguiente()
    print("OK")
