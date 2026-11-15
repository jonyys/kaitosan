"""Proveedor del modo sensei.

- Turnos (y resumen básico de cierre): si hay `OPENROUTER_API_KEY`, van a
  OpenRouter (`openrouter_modelos_sensei()` en orden). Es pago-por-uso y da
  modelos fuertes en seguir el prompt (Qwen, GLM) sin el rate limit por
  tokens/min del tier gratis. Si OpenRouter falla del todo (o no está
  configurado), se cae a Groq `gpt-oss-120b` como último recurso.
- Extractor de cierre (`strict=True`): OpenRouter con `EXTRACTOR_MODELO` (gpt-6-luna); Groq gpt-oss-120b
  solo de reserva y sin rotar a sus modelos alternativos. Si ninguno responde, el
  guardrail de `profesor.py` guarda solo el resumen.

Modelos de OpenRouter: `openrouter_modelos_sensei()` (Ajustes → Modelos).
"""

from ai.fallback_provider import FallbackProvider
from ai.openrouter_provider import OpenRouterProvider
import os

from core.config import OPENROUTER_API_KEY, groq_seleccion

EXTRACTOR_MODELO = os.getenv("EXTRACTOR_MODELO", "openai/gpt-6-luna")


class SenseiProvider:

    def __init__(self):
        self.openrouter = OpenRouterProvider() if OPENROUTER_API_KEY else None
        # El extractor de cierre va siempre a este modelo (15-nov: deepseek devolvía vacío
        # con json_object en una clase de 40 min; gpt-6-luna dio JSON válido en 14 s).
        self.extractor = (OpenRouterProvider(modelos=[EXTRACTOR_MODELO])
                          if OPENROUTER_API_KEY else None)
        self.reserva = FallbackProvider(model=groq_seleccion()["sensei"])
        # `getattr(provider, "groq", None)` sigue funcionando por si algo lo mira.
        self.groq = self.reserva.groq

    def completar(self, mensajes, max_tokens=None, response_format=None,
                  temperature=None, strict=False, reasoning_effort=None):
        # Todo (turnos, resumen y extractor) por OpenRouter primero; si falla, Groq
        # gpt-oss-120b. El extractor pasa strict=True: en Groq no rota a modelos de
        # reserva (JSON con japonés sucio) y lanza (lo recoge el guardrail).
        # Antes el extractor iba solo a Groq: una clase de 35-40 min pide ~8k tokens y
        # el límite de 8000 TPM la rechazaba siempre (413).
        prov = self.extractor if strict else self.openrouter
        if prov:
            try:
                return prov.completar(
                    mensajes, max_tokens=max_tokens, response_format=response_format,
                    temperature=temperature, reasoning_effort=reasoning_effort,
                )
            except Exception as e:  # noqa: BLE001
                print(f"⚠️ OpenRouter falló ({type(e).__name__}: {e}) → Groq")

        return self.reserva.completar(
            mensajes, max_tokens=max_tokens, response_format=response_format,
            temperature=temperature, strict=strict, reasoning_effort=reasoning_effort,
        )

    def completar_stream(self, mensajes, max_tokens=None, temperature=None, reasoning_effort=None):
        """Texto de la respuesta según llega (OpenRouter). Si OpenRouter no está o falla antes
        de dar nada, lanza la excepción: el llamante vuelve a `completar` (con su reserva)."""
        if not self.openrouter:
            raise RuntimeError("sin OpenRouter: no hay streaming")
        yield from self.openrouter.completar_stream(
            mensajes, max_tokens=max_tokens, temperature=temperature,
            reasoning_effort=reasoning_effort)
