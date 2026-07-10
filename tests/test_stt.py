import sys
sys.path.append('/home/kaitosan/robot')

from audio.recorder import Recorder
from ai.speech_to_text import SpeechToText

recorder = Recorder(device=1)
stt = SpeechToText()

print("\n🎤 Grabando 5 segundos...")
archivo = recorder.record(duracion=5)

if archivo:
    texto = stt.transcribir(archivo)
    print(f"\n📝 Texto transcrito: '{texto}'")