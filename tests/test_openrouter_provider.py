"""OpenRouterProvider: recorre la lista de modelos hasta el primero que responde;
rate limit / caído / vacío → siguiente."""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ai.openrouter_provider as orp
from ai.openrouter_provider import OpenRouterProvider

# La key se lee en core.config al importar; si el proceso de test la tiene vacía,
# la fijamos en el namespace del proveedor (es donde la mira `completar`).
orp.OPENROUTER_API_KEY = "test-key"


class _Resp:
    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def _ok(content, tokens=1234):
    return _Resp(200, {
        "choices": [{"message": {"content": content}}],
        "usage": {"total_tokens": tokens},
    })


def _provider():
    p = OpenRouterProvider(modelos=["a/uno", "b/dos", "c/tres"])
    p.tracker = type("T", (), {"añadir_tokens": lambda self, k, n: {"tokens": {k: n}}})()
    return p


def test_primer_modelo_responde():
    p = _provider()
    with patch.object(orp.requests, "post", return_value=_ok("【はい】")) as post:
        assert p.completar([{"role": "user", "content": "hola"}]) == "【はい】"
    assert post.call_count == 1
    assert post.call_args.kwargs["json"]["model"] == "a/uno"


def test_429_rota_al_siguiente():
    p = _provider()
    respuestas = [_Resp(429, text="rate limited"), _ok("【いいえ】")]
    with patch.object(orp.requests, "post", side_effect=respuestas) as post:
        assert p.completar([{"role": "user", "content": "hola"}]) == "【いいえ】"
    assert post.call_count == 2
    assert post.call_args.kwargs["json"]["model"] == "b/dos"


def test_respuesta_vacia_rota():
    p = _provider()
    respuestas = [_ok(""), _ok("   "), _ok("bien")]
    with patch.object(orp.requests, "post", side_effect=respuestas):
        assert p.completar([{"role": "user", "content": "hola"}]) == "bien"


def test_todos_fallan_lanza():
    p = _provider()
    with patch.object(orp.requests, "post", return_value=_Resp(429, text="rate")):
        try:
            p.completar([{"role": "user", "content": "hola"}])
            assert False, "debería haber lanzado"
        except Exception as e:
            assert "OpenRouter" in str(e)


def test_enruta_por_throughput():
    p = _provider()
    with patch.object(orp.requests, "post", return_value=_ok("x")) as post:
        p.completar([{"role": "user", "content": "h"}])
    assert post.call_args.kwargs["json"]["provider"] == {"sort": "throughput"}


def test_400_por_reasoning_reintenta_sin_el_param():
    p = OpenRouterProvider(modelos=["z-ai/glm-5.3-flash"])
    p.tracker = type("T", (), {"añadir_tokens": lambda self, k, n: {"tokens": {k: n}}})()
    respuestas = [_Resp(400, text="reasoning.enabled is not supported"), _ok("ok glm")]
    with patch.object(orp.requests, "post", side_effect=respuestas) as post:
        assert p.completar([{"role": "user", "content": "h"}]) == "ok glm"
    assert post.call_count == 2
    assert "reasoning" not in post.call_args.kwargs["json"]  # el reintento va sin él


def test_error_no_recuperable_lanza_sin_rotar():
    p = _provider()
    with patch.object(orp.requests, "post", return_value=_Resp(400, text="bad request")) as post:
        try:
            p.completar([{"role": "user", "content": "hola"}])
            assert False, "debería haber lanzado"
        except Exception as e:
            assert "400" in str(e)
    assert post.call_count == 1


def _tracker():
    return type("T", (), {"añadir_tokens": lambda self, k, n: {"tokens": {k: n}},
                          "añadir_coste": lambda self, k, n: None})()


def test_reasoning_qwen_glm_segun_OPENROUTER_REASONING():
    p = OpenRouterProvider(modelos=["qwen/qwen3.7-flash"])
    p.tracker = _tracker()

    # low (por defecto) → effort:low
    with patch.object(orp, "OPENROUTER_REASONING", "low"), \
         patch.object(orp.requests, "post", return_value=_ok("x")) as post:
        p.completar([{"role": "user", "content": "h"}])
    assert post.call_args.kwargs["json"]["reasoning"] == {"effort": "low"}

    # off → thinking desactivado
    with patch.object(orp, "OPENROUTER_REASONING", "off"), \
         patch.object(orp.requests, "post", return_value=_ok("x")) as post:
        p.completar([{"role": "user", "content": "h"}])
    assert post.call_args.kwargs["json"]["reasoning"] == {"enabled": False}


def test_reasoning_gpt_oss_usa_el_effort_del_turno():
    p = OpenRouterProvider(modelos=["openai/gpt-oss-120b"])
    p.tracker = _tracker()
    with patch.object(orp.requests, "post", return_value=_ok("x")) as post:
        p.completar([{"role": "user", "content": "h"}], reasoning_effort="low")
    assert post.call_args.kwargs["json"]["reasoning"] == {"effort": "low"}


if __name__ == "__main__":
    test_primer_modelo_responde()
    test_429_rota_al_siguiente()
    test_respuesta_vacia_rota()
    test_todos_fallan_lanza()
    test_enruta_por_throughput()
    test_400_por_reasoning_reintenta_sin_el_param()
    test_error_no_recuperable_lanza_sin_rotar()
    test_reasoning_qwen_glm_segun_OPENROUTER_REASONING()
    test_reasoning_gpt_oss_usa_el_effort_del_turno()
    print("OK")
