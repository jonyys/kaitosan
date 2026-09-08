"""Proveedor OpenRouter para los TURNOS del modo sensei.

Por qué: el prompt del profesor es grande y cada turno rozaba el límite de
tokens/min del tier gratis de Groq/Gemini (429 constante). OpenRouter es
pago-por-uso y enruta a modelos fuertes en *seguir instrucciones* (Qwen, GLM),
que es el cuello de botella real del sensei. El extractor de cierre NO pasa por
aquí — sigue en Groq (ver `sensei_provider.SenseiProvider.completar`, rama
`strict`).

API compatible con OpenAI (`/chat/completions`). Se usa `requests` (ya es
dependencia) en vez del SDK de OpenAI para no añadir nada.

`OPENROUTER_MODELOS_SENSEI` se recorre en orden: el primero que responda gana;
rate limit / modelo caído / respuesta vacía → siguiente.
"""
import requests

from core.config import (
    OPENROUTER_API_KEY, OPENROUTER_MODELOS_SENSEI, MAX_TOKENS, TEMPERATURE,
)
from core.token_tracker import TokenTracker

_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT = 60


class OpenRouterProvider:
    def __init__(self, modelos=None):
        self.modelos = list(modelos or OPENROUTER_MODELOS_SENSEI)
        self.tracker = TokenTracker()

    @staticmethod
    def _saltar_modelo(status: int, cuerpo: str) -> bool:
        """True si conviene pasar al siguiente modelo de la lista en vez de fallar."""
        s = (cuerpo or "").lower()
        return (
            status in (402, 404, 429, 502, 503) or
            "rate limit" in s or "rate_limit" in s or "quota" in s or
            "not found" in s or "no endpoints" in s or "no allowed providers" in s
        )

    def completar(self, mensajes, max_tokens=None, response_format=None,
                  temperature=None, reasoning_effort=None) -> str:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY no configurada")
        if not self.modelos:
            raise RuntimeError("OpenRouter sin modelos configurados")

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "X-Title": "Kaitosan",
        }
        ultimo = None
        for modelo in self.modelos:
            payload = {
                "model": modelo,
                "messages": mensajes,
                "max_tokens": max_tokens or MAX_TOKENS,
                "temperature": temperature if temperature is not None else TEMPERATURE,
            }
            if response_format:
                payload["response_format"] = response_format
            # reasoning_effort solo tiene sentido en los gpt-oss; en Qwen/GLM
            # flash no aplica. Formato OpenRouter: reasoning.effort.
            if reasoning_effort and "gpt-oss" in modelo:
                payload["reasoning"] = {"effort": reasoning_effort}

            try:
                r = requests.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT)
            except requests.RequestException as e:
                print(f"⚠️ OpenRouter {modelo} error de red ({type(e).__name__}), probando otro...")
                ultimo = e
                continue

            if r.status_code != 200:
                if self._saltar_modelo(r.status_code, r.text):
                    print(f"⚠️ OpenRouter {modelo} no disponible ({r.status_code}), probando otro...")
                    ultimo = Exception(f"{r.status_code}: {r.text[:200]}")
                    continue
                raise Exception(f"OpenRouter {modelo} {r.status_code}: {r.text[:300]}")

            data = r.json()
            clave = f"openrouter/{modelo}"
            try:
                tokens = int(data.get("usage", {}).get("total_tokens", 0) or 0)
                if tokens:
                    d = self.tracker.añadir_tokens(clave, tokens)
                    print(f"📊 Tokens {clave}: {tokens} "
                          f"(hoy: {d['tokens'][clave]} este modelo, "
                          f"{sum(d['tokens'].values())} total)")
            except Exception as e:  # noqa: BLE001 — el tracking nunca debe romper el turno
                print(f"⚠️ Error guardando tokens: {e}")

            contenido = ((data.get("choices") or [{}])[0]
                         .get("message", {}).get("content") or "")
            if not contenido.strip():
                print(f"⚠️ OpenRouter {modelo} respuesta vacía, probando otro...")
                ultimo = Exception("respuesta vacía")
                continue
            if modelo != self.modelos[0]:
                print(f"⚠️ Usando modelo alternativo OpenRouter: {modelo}")
            return contenido

        raise Exception(f"Todos los modelos OpenRouter fallaron. Último error: {ultimo}")
