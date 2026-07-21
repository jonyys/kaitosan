import asyncio
import os
from livekit.wakeword import WakeWordModel, WakeWordListener

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "audio", "kaito.onnx")

async def main():
    print(f"Cargando modelo: {MODEL_PATH}")
    model = WakeWordModel(models=[MODEL_PATH])

    print("Escuchando wake word 'Kaito'... (Ctrl+C para salir)")
    async with WakeWordListener(model, threshold=0.5) as listener:
        while True:
            detection = await listener.wait_for_detection()
            print(f"[WAKEWORD] Wake word detectado: '{detection.name}' (score: {detection.score:.3f})")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Detenido.")
