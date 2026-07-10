import sounddevice as sd
import soundfile as sf
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_PATH = os.path.join(BASE_DIR, "audio", "input.wav")

# Sample rate del G435
SAMPLE_RATE_DEVICE = 48000
# Sample rate para Whisper STT
SAMPLE_RATE_STT = 16000

class Recorder:
    def __init__(self, device=1,
                 sample_rate=SAMPLE_RATE_DEVICE):
        self.device = device
        self.sample_rate = sample_rate

    def record(self, filename=DEFAULT_PATH,
               duracion=5) -> str:
        """
        Graba audio durante X segundos.
        Devuelve la ruta del archivo grabado.
        """
        try:
            print(f"🎤 Grabando {duracion} segundos...")
            print("¡Habla ahora!")

            audio = sd.rec(
                int(duracion * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=self.device
            )
            sd.wait()

            # Amplifica el volumen
            audio = audio * 3.0
            audio = np.clip(audio, -1.0, 1.0)

            # Convierte a 16000Hz para Whisper
            audio_16k = self._convertir_sample_rate(
                audio,
                orig_sr=self.sample_rate,
                target_sr=SAMPLE_RATE_STT
            )

            sf.write(filename, audio_16k, SAMPLE_RATE_STT)
            print(f"✅ Audio guardado en: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error grabando: {e}")
            return None

    def record_hasta_enter(self,
                           filename=DEFAULT_PATH) -> str:
        """
        Graba hasta que el usuario pulsa ENTER.
        """
        try:
            input("🎤 Pulsa ENTER para empezar a grabar...")
            print("🔴 Grabando... Pulsa ENTER para terminar.")

            recording = []

            def callback(indata, frames, time, status):
                if status:
                    print(f"⚠️ {status}")
                recording.append(indata.copy())

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=self.device,
                callback=callback
            ):
                input()

            if not recording:
                print("❌ No se grabó nada")
                return None

            audio = np.concatenate(recording, axis=0)

            # Amplifica el volumen
            audio = audio * 3.0
            audio = np.clip(audio, -1.0, 1.0)

            # Convierte a 16000Hz para Whisper
            audio_16k = self._convertir_sample_rate(
                audio,
                orig_sr=self.sample_rate,
                target_sr=SAMPLE_RATE_STT
            )

            sf.write(filename, audio_16k, SAMPLE_RATE_STT)
            print(f"✅ Audio guardado en: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error grabando: {e}")
            return None

    def _convertir_sample_rate(self, audio,
                                orig_sr=48000,
                                target_sr=16000) -> np.ndarray:
        """Convierte el sample rate sin librosa"""
        ratio = target_sr / orig_sr
        target_length = int(len(audio) * ratio)
        convertido = np.interp(
            np.linspace(0, len(audio), target_length),
            np.arange(len(audio)),
            audio.flatten()
        )
        return convertido.reshape(-1, 1)

    def reproducir(self, filename=DEFAULT_PATH):
        """
        Reproduce un archivo de audio.
        Convierte a 48000Hz si es necesario.
        """
        try:
            data, fs = sf.read(filename)

            # Si el archivo es 16000Hz
            # convertir a 48000Hz para el G435
            if fs != self.sample_rate:
                print(f"🔄 Convirtiendo {fs}Hz → {self.sample_rate}Hz")
                data = self._convertir_sample_rate(
                    data,
                    orig_sr=fs,
                    target_sr=self.sample_rate
                )
                fs = self.sample_rate

            sd.play(data, fs, device=self.device)
            sd.wait()
            print("✅ Reproducción completada")

        except Exception as e:
            print(f"❌ Error reproduciendo: {e}")

    def dispositivos_disponibles(self):
        """Muestra los dispositivos de audio disponibles"""
        print(sd.query_devices())