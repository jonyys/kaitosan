import asyncio
import threading
import os
from livekit.wakeword import WakeWordModel, WakeWordListener

MODEL_PATH = os.path.join(os.path.dirname(__file__), "kaito.onnx")
THRESHOLD = 0.1


class WakeWordDetector:
    def __init__(self, on_detected):
        self._on_detected = on_detected
        self._stop_event = threading.Event()
        self._thread = None

    def iniciar(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("🎙️ WakeWord detector iniciado")

    def detener(self):
        self._stop_event.set()

    def _run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        model = WakeWordModel(models=[MODEL_PATH])
        loop = asyncio.get_running_loop()
        while not self._stop_event.is_set():
            try:
                async with WakeWordListener(model, threshold=THRESHOLD) as listener:
                    detection = await listener.wait_for_detection()
                # El micrófono queda libre al salir del context manager
                print(f"[WAKEWORD] '{detection.name}' detectado (confidence: {detection.confidence:.3f})")
                await loop.run_in_executor(None, self._on_detected)
            except Exception as e:
                print(f"⚠️ WakeWord error: {e}")
                await asyncio.sleep(1)
