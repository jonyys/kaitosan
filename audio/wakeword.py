import asyncio
import concurrent.futures
import threading
import time
import os
from collections import deque
from dataclasses import dataclass

import numpy as np
import pyaudio
from livekit.wakeword import WakeWordModel

MODEL_PATH = os.path.join(os.path.dirname(__file__), "kaito.onnx")
THRESHOLD = 0.1

_RATE_DEVICE = 44100
_RATE_MODEL = 16000
_FRAME_MS = 0.08
_FRAME_DEVICE = int(_FRAME_MS * _RATE_DEVICE)  # 3528 samples
_FRAME_MODEL = int(_FRAME_MS * _RATE_MODEL)    # 1280 samples
_CHUNK_FRAMES = 25  # 25 × 80ms = 2s


@dataclass
class Detection:
    name: str
    confidence: float
    timestamp: float


def _resample(audio: np.ndarray) -> np.ndarray:
    return np.interp(
        np.linspace(0, _FRAME_DEVICE, _FRAME_MODEL),
        np.arange(_FRAME_DEVICE),
        audio
    ).astype(np.int16)


class _WakeWordListener:
    """WakeWordListener que captura a 44100 Hz y resamplea a 16000 Hz para el modelo."""

    def __init__(self, model: WakeWordModel, threshold: float = 0.5, debounce: float = 2.0):
        self._model = model
        self._threshold = threshold
        self._debounce = debounce
        self._running = False
        self._stream = self._pa = self._task = self._executor = None
        self._last_detection_time = 0.0
        self._detection_queue: asyncio.Queue = asyncio.Queue()
        self._listening = asyncio.Event()
        self._done_event = asyncio.Event()
        self._error = None
        self._frame_buffer: deque = deque(maxlen=_CHUNK_FRAMES)

    async def __aenter__(self):
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=_RATE_DEVICE,
            input=True,
            frames_per_buffer=_FRAME_DEVICE,
        )
        self._running = True
        self._listening.set()
        self._done_event.clear()
        self._error = None
        self._frame_buffer.clear()
        self._detection_queue = asyncio.Queue()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._task = asyncio.create_task(self._audio_loop())
        return self

    async def __aexit__(self, *_):
        self._running = False
        self._listening.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()

    async def _audio_loop(self):
        loop = asyncio.get_event_loop()
        try:
            while self._running:
                await self._listening.wait()
                if not self._running:
                    break

                data = await loop.run_in_executor(
                    self._executor,
                    lambda: self._stream.read(_FRAME_DEVICE, exception_on_overflow=False),
                )
                if not self._running:
                    break

                frame = _resample(np.frombuffer(data, dtype=np.int16))
                self._frame_buffer.append(frame)

                if len(self._frame_buffer) < _CHUNK_FRAMES:
                    continue

                chunk = np.concatenate(list(self._frame_buffer))
                scores = await loop.run_in_executor(self._executor, self._model.predict, chunk)
                if not self._running:
                    break

                now = time.monotonic()
                for name, score in scores.items():
                    if score >= self._threshold:
                        if now - self._last_detection_time >= self._debounce:
                            self._last_detection_time = now
                            self._listening.clear()
                            self._frame_buffer.clear()
                            await self._detection_queue.put(
                                Detection(name=name, confidence=score, timestamp=now)
                            )
                            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._error = exc
        finally:
            self._done_event.set()

    async def wait_for_detection(self) -> Detection:
        self._listening.set()
        queue_waiter = asyncio.ensure_future(self._detection_queue.get())
        done_waiter = asyncio.ensure_future(self._done_event.wait())
        done, pending = await asyncio.wait(
            {queue_waiter, done_waiter}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if queue_waiter in done:
            return queue_waiter.result()
        if not self._detection_queue.empty():
            return self._detection_queue.get_nowait()
        if self._error:
            raise RuntimeError(f"Audio loop crashed: {self._error}") from self._error
        raise RuntimeError("Audio loop ended unexpectedly")


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
                async with _WakeWordListener(model, threshold=THRESHOLD) as listener:
                    detection = await listener.wait_for_detection()
                print(f"[WAKEWORD] '{detection.name}' detectado (confidence: {detection.confidence:.3f})")
                await loop.run_in_executor(None, self._on_detected)
            except Exception as e:
                print(f"⚠️ WakeWord error: {e}")
                await asyncio.sleep(1)
