from groq import Groq
from core.config import GROQ_API_KEY
import os

class SpeechToText:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.modelo = "whisper-large-v3-turbo"

    def transcribir(self, archivo_audio: str) -> str:
        """
        Transcribe un archivo de audio usando Groq Whisper.
        Mucho más rápido que local y no consume RAM de la Pi.
        """
        try:
            if not os.path.exists(archivo_audio):
                print(f"❌ Archivo no encontrado: {archivo_audio}")
                return ""

            print("🔄 Transcribiendo con Groq Whisper...")

            with open(archivo_audio, "rb") as audio:
                transcripcion = self.client.audio.transcriptions.create(
                    model=self.modelo,
                    file=audio,
                    language="es"
                )

            texto = transcripcion.text.strip()
            print(f"✅ Transcripción: {texto}")
            return texto

        except Exception as e:
            print(f"❌ Error transcribiendo: {e}")
            return ""