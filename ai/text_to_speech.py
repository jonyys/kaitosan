import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import tempfile
import re


class TextToSpeech:
    def __init__(self, device=1):
        self.device = device
        self.sample_rate_device = 48000
        self.voice = "es-ES-AlvaroNeural"

    def _limpiar_para_voz(self, texto: str) -> str:
        """
        Prepara el texto para que la voz española lo lea bien:
        - Elimina fragmentos en kana/kanji entre paréntesis.
        - Normaliza romaji (desu→des, masu→mas, etc.).
        """
        # Quitar paréntesis con contenido japonés: (です) o （です）
        texto = re.sub(r'[（(][\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+[）)]', '', texto)

        # Quitar fragmentos sueltos de kana/kanji sin paréntesis (opcional, cuidado)
        # texto = re.sub(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+', '', texto)

        # ── Normalización fonética japonés real ──
        reemplazos = [
            (r'arigatou', 'arigató'),
            (r'konnichiwa', 'konnichiwa'),
            (r'ohayou', 'ohayó'),
            (r'sayounara', 'sayonara'),
            (r'konbanwa', 'konbanwa'),
            # Terminaciones formales (ensordecimiento de u)
            (r'\bdesu\b', 'des'),
            (r'\bmasu\b', 'mas'),
            (r'\bdeshita\b', 'deshta'),
            (r'\bmashita\b', 'mashta'),
            (r'\bshimasu\b', 'shimas'),
            (r'\bgozaimasu\b', 'gozaimas'),
            (r'\bonegaishimasu\b', 'onegaishimas'),
            # Vocales ensordecidas entre sordas
            (r'\bikimasu\b', 'ikimas'),
            (r'\bkimasu\b', 'kimas'),
            (r'\bhanashimasu\b', 'hanashimas'),
            (r'\btabemasu\b', 'tabemas'),
            (r'\bnomimasu\b', 'nomimas'),
            (r'\bmimasu\b', 'mimas'),
            (r'\bkaerimasu\b', 'kaerimas'),
            # Forma te (て) → suena como "te" o "de"
            # Forma ta (た) → "ta", pero en pasado a menudo se contrae
            (r'\bshita\b', 'shta'),
            (r'\bshite\b', 'shte'),
            (r'\btsuite\b', 'tsuite'),
            (r'\bmotte\b', 'motte'),
            (r'\batte\b', 'atte'),
            (r'\bitte\b', 'itte'),
            # Contracciones típicas
            (r'\bwatashi wa\b', 'watashi wa'),
            (r'\bwatashi\b', 'watashi'),
            # Ashita / ashta
            (r'\bashita\b', 'ashta'),
            # Palabras con hi → suena casi como shi en boca de hispanohablante
            (r'\bhitotsu\b', 'shtotsu'),
            (r'\bfutatsu\b', 'futatsu'),
            # Alargamientos (ー) → no se leen como letra
            (r'[ー一]', ''),
            # Pequeñas pausas con punto o coma añadimos espacio extra
            # Las comas y puntos ya las gestiona el TTS
        ]
        for patron, reemplazo in reemplazos:
                    texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)

        # Añadir pausas sutiles entre frases japonesas y español
        # Insertar una coma antes de cambiar de idioma
        texto = re.sub(
            r'([a-záéíóúñ]+)\s+([a-záéíóúñ]+)',
            r'\1 \2', texto
        )
        # Añadir pausa después de palabra japonesa seguida de español
        texto = re.sub(
            r'\b(des|mas|shta|ashta|ne|yo|ka|wa|ga|no|ni|de|wo|e|to|mo)\b\s+([A-ZÁÉÍÓÚÑa-záéíóúñ])',
            r'\1, \2', texto
        )

        return texto.strip()

    async def _generar_audio(self, texto: str, tmp_path: str):
        texto_limpio = self._limpiar_para_voz(texto)
        print(f"🎙️ Texto enviado a TTS: {texto_limpio}")
        tts = edge_tts.Communicate(texto_limpio, voice=self.voice)
        await tts.save(tmp_path)

    def hablar(self, texto: str):
        try:
            print(f"🔊 Hablando: {texto}")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            asyncio.run(self._generar_audio(texto, tmp_path))

            data, fs = sf.read(tmp_path)
            os.unlink(tmp_path)

            if data.dtype != np.float32:
                data = data.astype(np.float32)

            if len(data.shape) > 1:
                data = data.mean(axis=1)

            if fs != self.sample_rate_device:
                data = self._convertir_sample_rate(data, orig_sr=fs, target_sr=self.sample_rate_device)

            sd.play(data, self.sample_rate_device, device=self.device)
            sd.wait()
            print("✅ Reproducción completada")

        except Exception as e:
            print(f"❌ Error en TTS: {e}")

    def _convertir_sample_rate(self, audio, orig_sr, target_sr) -> np.ndarray:
        ratio = target_sr / orig_sr
        target_length = int(len(audio) * ratio)
        if target_length == 0:
            return audio
        return np.interp(
            np.linspace(0, len(audio), target_length),
            np.arange(len(audio)),
            audio.flatten()
        ).astype(np.float32)