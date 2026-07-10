import sounddevice as sd
import soundfile as sf
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_PATH = os.path.join(BASE_DIR, "audio", "input.wav")

class Recorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def record(self, filename=DEFAULT_PATH) -> str:
        """
        Graba audio hasta que el usuario pulsa ENTER.
        Devuelve la ruta del archivo grabado.
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
                callback=callback
            ):
                input()

            if not recording:
                print("❌ No se grabó nada")
                return None

            audio = np.concatenate(recording, axis=0)
            sf.write(filename, audio, self.sample_rate)
            print(f"✅ Audio guardado en: {filename}")
            return filename

        except sd.PortAudioError as e:
            print(f"❌ Error de micrófono: {e}")
            return None
        except Exception as e:
            print(f"❌ Error grabando: {e}")
            return None

    def dispositivos_disponibles(self):
        """Muestra los dispositivos de audio disponibles"""
        print(sd.query_devices())