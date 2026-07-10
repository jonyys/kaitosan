import sounddevice as sd
import soundfile as sf
import numpy as np

# Dispositivo 1 = G435 Wireless Gaming Headset
DISPOSITIVO = 1
DURACION = 5
SAMPLE_RATE = 48000

print(f"🎤 Grabando {DURACION} segundos con G435...")
print("¡Habla ahora!")

# Graba
audio = sd.rec(
    int(DURACION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype='float32',
    device=DISPOSITIVO
)
sd.wait()
print("✅ Grabación completada")

# Guarda
sf.write("tests/test_audio.wav", audio, SAMPLE_RATE)
print("✅ Audio guardado en tests/test_audio.wav")

# Reproduce
print("🔊 Reproduciendo...")
data, fs = sf.read("tests/test_audio.wav")
sd.play(data, fs, device=DISPOSITIVO)
sd.wait()
print("✅ Reproducción completada")