from groq import Groq
from core.config import GROQ_API_KEY
import os

class SpeechToText:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.modelo = "whisper-large-v3-turbo"

    def transcribir(self, archivo_audio: str, idioma: str = None) -> str:
        try:
            if not os.path.exists(archivo_audio):
                print(f"❌ Archivo no encontrado: {archivo_audio}")
                return ""

            print("🔄 Transcribiendo con Groq Whisper...")

            with open(archivo_audio, "rb") as audio:
                params = {
                    "model": self.modelo,
                    "file": audio,
                }
                if idioma:
                    params["language"] = idioma
                transcripcion = self.client.audio.transcriptions.create(**params)

            texto = transcripcion.text.strip()
            print(f"✅ Transcripción: {texto}")
            return texto

        except Exception as e:
            print(f"❌ Error transcribiendo: {e}")
            return ""