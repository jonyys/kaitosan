"""SenseiProvider: todo por OpenRouter, Groq de reserva; el extractor
(strict=True) llega a Groq con strict."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei_provider import SenseiProvider


def _provider(openrouter=None, extractor=None):
    sp = SenseiProvider()
    sp.openrouter = openrouter
    sp.extractor = extractor
    sp.reserva = MagicMock()
    sp.reserva.completar.return_value = "{} (groq)"
    sp.groq = sp.reserva.groq
    return sp


def test_turno_va_a_openrouter():
    orp = MagicMock()
    orp.completar.return_value = "【はい】 openrouter"
    sp = _provider(orp)
    assert sp.completar([{"role": "user", "content": "hola"}]) == "【はい】 openrouter"
    sp.reserva.completar.assert_not_called()


def test_openrouter_falla_cae_a_groq():
    orp = MagicMock()
    orp.completar.side_effect = Exception("todos los modelos OpenRouter fallaron")
    sp = _provider(orp)
    assert sp.completar([{"role": "user", "content": "hola"}]) == "{} (groq)"
    args = sp.reserva.completar.call_args
    assert args.kwargs.get("strict") in (None, False)


def test_sin_openrouter_va_directo_a_groq():
    sp = _provider(None)
    assert sp.completar([{"role": "user", "content": "hola"}]) == "{} (groq)"


def test_extractor_va_a_openrouter():
    orp, ext = MagicMock(), MagicMock()
    ext.completar.return_value = "{} (luna)"
    sp = _provider(orp, ext)
    out = sp.completar(
        [{"role": "user", "content": "conv"}],
        response_format={"type": "json_object"}, strict=True,
    )
    assert out == "{} (luna)"
    orp.completar.assert_not_called()  # el de los turnos (deepseek) no
    sp.reserva.completar.assert_not_called()


def test_extractor_falla_openrouter_groq_strict():
    ext = MagicMock()
    ext.completar.side_effect = Exception("caído")
    sp = _provider(MagicMock(), ext)
    out = sp.completar([{"role": "user", "content": "conv"}], strict=True)
    assert out == "{} (groq)"
    assert sp.reserva.completar.call_args.kwargs.get("strict") is True


if __name__ == "__main__":
    test_turno_va_a_openrouter()
    test_openrouter_falla_cae_a_groq()
    test_sin_openrouter_va_directo_a_groq()
    test_extractor_va_a_openrouter()
    test_extractor_falla_openrouter_groq_strict()
    print("OK")
