import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import tempfile

class TextToSpeech:
    def __init__(self, device=1):
        self.device = device
        self.sample_rate_device = 48000
        self.voice = "es-ES-ElviraNeural"

    async def _generar_audio(self, texto: str,
                              tmp_path: str):
        """Genera el audio con Edge TTS"""
        tts = edge_tts.Communicate(
            texto,
            voice=self.voice
        )
        await tts.save(tmp_path)

    def hablar(self, texto: str):
        """
        Convierte texto a voz y reproduce
        por el dispositivo de audio.
        """
        try:
            print(f"🔊 Hablando: {texto[:50]}...")

            # Archivo temporal mp3
            with tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False
            ) as tmp:
                tmp_path = tmp.name

            # Genera audio con Edge TTS
            asyncio.run(
                self._generar_audio(texto, tmp_path)
            )

            # Lee el mp3 con soundfile
            data, fs = sf.read(tmp_path)

            # Elimina archivo temporal
            os.unlink(tmp_path)

            # Convierte a float32 si hace falta
            if data.dtype != np.float32:
                data = data.astype(np.float32)

            # Si es estéreo convierte a mono
            if len(data.shape) > 1:
                data = data.mean(axis=1)

            # Convierte sample rate si hace falta
            if fs != self.sample_rate_device:
                data = self._convertir_sample_rate(
                    data,
                    orig_sr=fs,
                    target_sr=self.sample_rate_device
                )

            # Reproduce
            sd.play(
                data,
                self.sample_rate_device,
                device=self.device
            )
            sd.wait()
            print("✅ Reproducción completada")

        except Exception as e:
            print(f"❌ Error en TTS: {e}")

    def _convertir_sample_rate(self, audio,
                                orig_sr,
                                target_sr) -> np.ndarray:
        """Convierte sample rate sin librosa"""
        ratio = target_sr / orig_sr
        target_length = int(len(audio) * ratio)
        if target_length == 0:
            return audio
        return np.interp(
            np.linspace(0, len(audio), target_length),
            np.arange(len(audio)),
            audio.flatten()
        ).astype(np.float32)