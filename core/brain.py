from ai.groq_provider import GroqProvider
from ai.prompts import SYSTEM_PROMPT
import time

class Brain:
    def __init__(self, state_manager, socketio):
        self.state = state_manager
        self.socketio = socketio
        self.provider = GroqProvider()
        self.historial = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def responder(self, mensaje: str) -> str:
        """Añade el mensaje al historial y devuelve respuesta"""
        self.historial.append({
            "role": "user",
            "content": mensaje
        })

        respuesta = self.provider.completar(self.historial)

        self.historial.append({
            "role": "assistant",
            "content": respuesta
        })

        return respuesta

    def saludar(self):
        """Saluda cuando detecta una persona"""
        try:
            self.state.cambiar("thinking")

            saludo = self.responder(
                "Acabo de sentarme delante de ti, "
                "salúdame de forma breve y simpática"
            )

            print(f"🤖 Kaito: {saludo}")
            self.state.cambiar("speaking")
            self.socketio.emit("mensaje", {"texto": saludo})

            tiempo = min(len(saludo) * 0.05, 6)
            time.sleep(tiempo)
            self.state.cambiar("idle")

        except Exception as e:
            print(f"❌ Error saludando: {e}")
            self.state.cambiar("idle")

    def limpiar_historial(self):
        """Resetea el historial manteniendo el system prompt"""
        self.historial = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        print("🧹 Historial limpiado")