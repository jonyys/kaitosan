"""Enrutado de comandos del modo sensei (un solo modo).

Regresión: «salir del modo sensei» se despide; no lo caza el disparador de
entrada por contener «sensei».
"""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brain import Brain
from ai.sensei.profesor import SALUDOS, DESPEDIDAS


def _brain(activo):
    b = object.__new__(Brain)
    b.profesor = MagicMock()
    b.profesor.esta_activo.return_value = activo
    b._emitir_desactivar_sensei = False
    return b


def test_salir_del_modo_sensei_se_despide():
    b = _brain(activo=True)
    resp, _ = b._responder("quiero salir del modo sensei")
    assert resp in DESPEDIDAS
    assert b._emitir_desactivar_sensei is True
    b.profesor.salir.assert_called_once()


def test_entrar_al_modo_sensei_saluda():
    b = _brain(activo=False)
    resp, _ = b._responder("ponme en modo sensei")
    assert resp in SALUDOS
    b.profesor.entrar.assert_called_once()


def test_modo_estudio_tambien_entra():
    b = _brain(activo=False)
    resp, _ = b._responder("dame clase, modo estudio")
    assert resp in SALUDOS
    b.profesor.entrar.assert_called_once()


if __name__ == "__main__":
    test_salir_del_modo_sensei_se_despide()
    test_entrar_al_modo_sensei_saluda()
    test_modo_estudio_tambien_entra()
    print("ok")
