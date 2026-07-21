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

            pending_tool_results = []

            for msg in mensajes:
                role = msg.get("role")

                if role == "system":
                    system_prompt += msg["content"] + "\n"

                elif role == "tool":
                    # Acumula resultados de herramientas para fusionarlos con el siguiente turno
                    pending_tool_results.append(msg.get("content", ""))

                elif role == "assistant":
                    content = msg.get("content")
                    if content is None:
                        # Turno de tool-call: el contenido real vendrá en el role:tool siguiente
                        # No añadimos nada todavía; pending_tool_results lo capturará
                        continue
                    # Si hay resultados de herramientas pendientes, los pegamos al assistant
                    if pending_tool_results:
                        content = "[Resultados de búsqueda: " + " | ".join(pending_tool_results) + "]\n" + content
                        pending_tool_results = []
                    historial_gemini.append({
                        "role": "model",
                        "parts": [content]
                    })

                elif role == "user":
                    # Si hay resultados pendientes sin assistant que los consuma, los convertimos en contexto
                    if pending_tool_results:
                        historial_gemini.append({
                            "role": "model",
                            "parts": ["[Resultados obtenidos: " + " | ".join(pending_tool_results) + "]"]
                        })
                        pending_tool_results = []
                    historial_gemini.append({
                        "role": "user",
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