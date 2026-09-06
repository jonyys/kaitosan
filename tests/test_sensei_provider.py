"""SenseiProvider: turnos por Gemini con rotación de modelos ante rate limit,
Groq de reserva; el extractor (strict=True) siempre a Groq."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei_provider import SenseiProvider, _es_rate_limit


class _Rate(Exception):
    """Simula un 429 de Gemini."""
    def __str__(self):
        return "429 quota exceeded"


def _provider(*gemini_returns):
    """gemini_returns: por cada modelo, un str a devolver o una Exception a lanzar."""
    sp = SenseiProvider()
    sp.gemini = []
    for i, val in enumerate(gemini_returns):
        gp = MagicMock()
        gp.model_id = f"gemini-fake-{i}"
        if isinstance(val, Exception):
            gp.completar.side_effect = val
        else:
            gp.completar.return_value = val
        sp.gemini.append(gp)
    sp.reserva = MagicMock()
    sp.reserva.completar.return_value = "{} (groq)"
    sp.groq = sp.reserva.groq
    return sp


def test_turno_va_al_primer_gemini():
    sp = _provider("【はい】 g0", "【いいえ】 g1")
    assert sp.completar([{"role": "user", "content": "hola"}]) == "【はい】 g0"
    sp.gemini[0].completar.assert_called_once()
    sp.gemini[1].completar.assert_not_called()
    sp.reserva.completar.assert_not_called()


def test_rate_limit_rota_al_siguiente_gemini():
    sp = _provider(_Rate(), "【はい】 g1")
    assert sp.completar([{"role": "user", "content": "hola"}]) == "【はい】 g1"
    sp.gemini[1].completar.assert_called_once()
    sp.reserva.completar.assert_not_called()


def test_todos_gemini_en_rate_limit_cae_a_groq():
    sp = _provider(_Rate(), _Rate())
    assert sp.completar([{"role": "user", "content": "hola"}]) == "{} (groq)"
    sp.reserva.completar.assert_called_once()
    assert sp.reserva.completar.call_args.kwargs.get("strict") in (None, False)


def test_error_no_429_de_gemini_va_directo_a_groq():
    # un fallo que no es rate limit no debe gastar los otros modelos Gemini
    sp = _provider(ValueError("respuesta vacía"), "no debería usarse")
    assert sp.completar([{"role": "user", "content": "hola"}]) == "{} (groq)"
    sp.gemini[1].completar.assert_not_called()


def test_extractor_strict_solo_groq():
    sp = _provider("no debería usarse")
    out = sp.completar(
        [{"role": "user", "content": "conv"}],
        response_format={"type": "json_object"}, strict=True,
    )
    assert out == "{} (groq)"
    sp.gemini[0].completar.assert_not_called()
    assert sp.reserva.completar.call_args.kwargs.get("strict") is True


def test_es_rate_limit():
    assert _es_rate_limit(Exception("429 RESOURCE_EXHAUSTED"))
    assert _es_rate_limit(Exception("You exceeded your quota"))
    assert not _es_rate_limit(ValueError("finish_reason 2"))


if __name__ == "__main__":
    test_turno_va_al_primer_gemini()
    test_rate_limit_rota_al_siguiente_gemini()
    test_todos_gemini_en_rate_limit_cae_a_groq()
    test_error_no_429_de_gemini_va_directo_a_groq()
    test_extractor_strict_solo_groq()
    test_es_rate_limit()
    print("OK")
