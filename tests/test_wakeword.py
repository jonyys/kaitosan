import asyncio
import os
from livekit.wakeword import WakeWordModel, WakeWordListener

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "audio", "kaito.onnx")
THRESHOLD = 0.1

async def main():
    print(f"Cargando modelo: {MODEL_PATH}")
    print(f"Threshold: {THRESHOLD}")
    model = WakeWordModel(models=[MODEL_PATH])

    print("Escuchando wake word 'Kaito'... (Ctrl+C para salir)\n")
    async with WakeWordListener(model, threshold=THRESHOLD) as listener:
        while True:
            detection = await listener.wait_for_detection()
            print(f"[WAKEWORD] '{detection.name}' | confidence: {detection.confidence:.4f}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDetenido.")
