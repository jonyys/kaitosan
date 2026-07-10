from groq import Groq
import os
import time

class Brain:
    def __init__(self, state_manager, socketio):
        self.state = state_manager
        self.socketio = socketio
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.modelo = "llama-3.3-70b-versatile"

        self.historial = [
            {
                "role": "system",
                "content": """Eres Kaitosan, un robot asistente de
                escritorio simpático, cercano y conciso.
                Respondes siempre en español.
                Tus respuestas son cortas y naturales,
                como en una conversación normal."""
            }
        ]

    def responder(self, mensaje: str) -> str:
        try:
            self.historial.append({
                "role": "user",
                "content": mensaje
            })

            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=self.historial,
                max_tokens=200
            )

            respuesta = response.choices[0].message.content

            self.historial.append({
                "role": "assistant",
                "content": respuesta
            })

            return respuesta

        except Exception as e:
            print(f"❌ Error en Groq: {e}")
            raise e

    def saludar(self):
        try:
            self.state.cambiar("thinking")

            # Usa el historial principal ✅
            saludo = self.responder(
                "Acabo de sentarme delante de ti, "
                "salúdame de forma breve y simpática"
            )

            print(f"🤖 Kaitosan: {saludo}")
            self.state.cambiar("speaking")
            self.socketio.emit("mensaje", {"texto": saludo})

            # Tiempo proporcional a la longitud del texto
            tiempo = min(len(saludo) * 0.05, 6)
            time.sleep(tiempo)
            self.state.cambiar("idle")

        except Exception as e:
            print(f"❌ Error saludando: {e}")
            self.state.cambiar("idle")