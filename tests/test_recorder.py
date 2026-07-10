import sys
sys.path.append('/home/kaitosan/robot')

from audio.recorder import Recorder

recorder = Recorder(device=1)

# Prueba grabación por tiempo
archivo = recorder.record(duracion=5)

if archivo:
    print("🔊 Reproduciendo lo grabado...")
    recorder.reproducir(archivo)