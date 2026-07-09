from groq import Groq
from core.config import GROQ_API_KEY


class SpeechToText:

    def __init__(self):

        self.client = Groq(api_key=GROQ_API_KEY)

    def transcribe(self, audio_path):

        with open(audio_path, "rb") as audio_file:

            transcription = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="verbose_json",
                language="es",
                temperature=0.0
            )

        return transcription.text