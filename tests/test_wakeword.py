import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audio.wakeword import _WakeWordListener, WakeWordModel, MODEL_PATH

# Bajo a propósito para calibrar: di "kaito" varias veces y anota la confianza
# real de las detecciones; luego ajusta THRESHOLD en audio/wakeword.py.
THRESHOLD = 0.1


async def main():
    print(f"Cargando modelo: {MODEL_PATH}")
    print(f"Threshold: {THRESHOLD}")
    model = WakeWordModel(models=[MODEL_PATH])

    print("Escuchando wake word 'Kaito'... (Ctrl+C para salir)\n")
    async with _WakeWordListener(model, threshold=THRESHOLD) as listener:
        while True:
            detection = await listener.wait_for_detection()
            print(f"[WAKEWORD] '{detection.name}' | confidence: {detection.confidence:.4f}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDetenido.")
