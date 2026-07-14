import sys
sys.path.append('/home/kaitosan/robot')

from audio.recorder import Recorder
import soundfile as sf
import numpy as np

recorder = Recorder(device=1)

# Prueba grabación por tiempo
archivo = recorder.record(duracion=5)

if archivo:
    # Comprobar el volumen
    data, fs = sf.read(archivo)
    print(f"🔊 Nivel de grabación: max={np.max(data):.4f}, min={np.min(data):.4f}")

    if np.max(data) < 0.01:
        print("⚠️ La grabación está casi en silencio. Revisa el micrófono.")
    else:
        print("🔊 Reproduciendo lo grabado...")
        recorder.reproducir(archivo)