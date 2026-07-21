import google.generativeai as genai
from core.config import GEMINI_API_KEY

class GeminiProvider:
    def __init__(self, model="gemini-2.0-flash"):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model)

    def completar(self, mensajes: list, max_tokens: int = None, temperature: float = None) -> str:
        """
        Convierte el formato OpenAI (role/content) al formato Gemini
        y devuelve la respuesta.
        """
        try:
            # Gemini no acepta system role como mensaje normal
            system_prompt = ""
            historial_gemini = []

            for msg in mensajes:
                if msg["role"] == "system":
                    system_prompt += msg["content"] + "\n"
                elif msg["role"] == "user":
                    historial_gemini.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                elif msg["role"] == "assistant":
                    historial_gemini.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })

            # Si hay system prompt, lo ponemos como primer mensaje del usuario
            if system_prompt:
                historial_gemini.insert(0, {
                    "role": "user",
                    "parts": [f"Instrucciones del sistema: {system_prompt}"]
                })

            if not historial_gemini:
                return ""

            gen_config = {}
            if max_tokens:
                gen_config["max_output_tokens"] = max_tokens
            if temperature is not None:
                gen_config["temperature"] = temperature
            chat = self.model.start_chat(history=historial_gemini[:-1])
            ultimo = historial_gemini[-1]["parts"][0]
            respuesta = chat.send_message(
                ultimo,
                generation_config=gen_config if gen_config else None,
            )
            return respuesta.text.strip()

        except Exception as e:
            print(f"❌ Error en Gemini: {e}")
            return "Lo siento, estoy teniendo problemas para responder. ¿Podemos intentarlo de nuevo?"