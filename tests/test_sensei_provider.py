"""SenseiProvider: Gemini primero en los turnos, Groq de reserva; el extractor
(strict=True) siempre a Groq."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei_provider import SenseiProvider


def _provider(gemini_side_effect=None, gemini_return="【はい】 (gemini)"):
    sp = SenseiProvider()
    sp.gemini = MagicMock()
    if gemini_side_effect is not None:
        sp.gemini.completar.side_effect = gemini_side_effect
    else:
        sp.gemini.completar.return_value = gemini_return
    sp.reserva = MagicMock()
    sp.reserva.completar.return_value = "{} (groq)"
    sp.groq = sp.reserva.groq
    return sp


def test_turno_va_a_gemini():
    sp = _provider()
    out = sp.completar([{"role": "user", "content": "hola"}], max_tokens=100)
    assert out == "【はい】 (gemini)"
    sp.gemini.completar.assert_called_once()
    sp.reserva.completar.assert_not_called()


def test_turno_cae_a_groq_si_gemini_falla():
    sp = _provider(gemini_side_effect=RuntimeError("429"))
    out = sp.completar([{"role": "user", "content": "hola"}])
    assert out == "{} (groq)"
    sp.reserva.completar.assert_called_once()
    # a la reserva NO se le pasa strict=True en un turno normal
    assert sp.reserva.completar.call_args.kwargs.get("strict") in (None, False)


def test_extractor_strict_solo_groq():
    sp = _provider()
    out = sp.completar(
        [{"role": "user", "content": "conv"}],
        response_format={"type": "json_object"}, strict=True,
    )
    assert out == "{} (groq)"
    sp.gemini.completar.assert_not_called()
    assert sp.reserva.completar.call_args.kwargs.get("strict") is True


if __name__ == "__main__":
    test_turno_va_a_gemini()
    test_turno_cae_a_groq_si_gemini_falla()
    test_extractor_strict_solo_groq()
    print("OK")
