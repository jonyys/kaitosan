from core.token_tracker import TokenTracker
import soundfile as sf

class SpeechToText:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.modelo = "whisper-large-v3-turbo"
        self.tracker = TokenTracker()          # ← mismo tracker

    def transcribir(self, archivo_audio: str, idioma: str = None) -> str:
        try:
            if not os.path.exists(archivo_audio):
                print(f"❌ Archivo no encontrado: {archivo_audio}")
                return ""

            # Medir duración del audio
            info = sf.info(archivo_audio)
            segundos = int(info.duration) + 1
            total_audio = self.tracker.añadir_audio(segundos)
            print(f"🎤 Segundos de audio hoy: {total_audio}/7200")

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