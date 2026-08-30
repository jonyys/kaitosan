import asyncio
import concurrent.futures
import threading
import time
import os
from collections import deque
from dataclasses import dataclass

import numpy as np
import pyaudio
from livekit.wakeword import WakeWordModel  # re-exportado (lo usan los tests)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "kaito.onnx")
THRESHOLD = 0.1

# WAKEWORD_DEBUG=true imprime la puntuación máxima de cada ventana de 2 s para
# ver en los logs si el modelo te está oyendo (aunque no llegue al umbral).
_DEBUG = os.getenv("WAKEWORD_DEBUG", "false").strip().lower() in ("1", "true", "yes", "on")

# El modelo es "stateless": hay que re-inferir sobre TODA la ventana de 2 s cada
# vez, y cada inferencia son ~17 pasadas ONNX. Hacerlo en cada frame de 80 ms
# (~12/s) reparte 3+ núcleos de una Pi 4 y la calienta. Con hop=3 se infiere
# cada ~240 ms: 1/3 de carga y solo ~160 ms más de latencia (imperceptible).
_HOP = max(1, int(os.getenv("WAKEWORD_HOP_FRAMES", "3")))
# Núcleos que ONNX Runtime puede usar por inferencia. 1 = un solo núcleo; sube
# la latencia por inferencia pero evita clavar toda la CPU.
_ORT_THREADS = max(1, int(os.getenv("WAKEWORD_ORT_THREADS", "1")))

_RATE_MODEL = 16000
_FRAME_MS = 0.08
_FRAME_MODEL = int(_FRAME_MS * _RATE_MODEL)    # 1280 samples
_CHUNK_FRAMES = 25  # 25 × 80ms = 2s

# Sample rates a probar, en orden de preferencia: 16 kHz es el nativo del modelo
# (sin resampleo). Los demás son fallback si el micro no acepta 16 kHz.
_RATES_FALLBACK = (16000, 48000, 44100, 32000)


def _cargar_modelo():
    """Construye el WakeWordModel limitando los hilos de cada sesión ONNX a
    _ORT_THREADS. La librería crea las InferenceSession sin opciones (usan todos
    los núcleos), así que parcheamos el constructor mientras se carga."""
    import onnxruntime as ort
    from livekit.wakeword import WakeWordModel

    _orig = ort.InferenceSession

    def _patched(*args, **kwargs):
        if "sess_options" not in kwargs:
            so = ort.SessionOptions()
            so.intra_op_num_threads = _ORT_THREADS
            so.inter_op_num_threads = 1
            kwargs["sess_options"] = so
        return _orig(*args, **kwargs)

    ort.InferenceSession = _patched
    try:
        return WakeWordModel(models=[MODEL_PATH])
    finally:
        ort.InferenceSession = _orig


@dataclass
class Detection:
    name: str
    confidence: float
    timestamp: float


def _resample(audio: np.ndarray) -> np.ndarray:
    """Resamplea un frame de captura (longitud variable) a _FRAME_MODEL samples."""
    src_len = len(audio)
    if src_len == _FRAME_MODEL:
        return audio.astype(np.int16)
    return np.interp(
        np.linspace(0, src_len, _FRAME_MODEL),
        np.arange(src_len),
        audio,
    ).astype(np.int16)


def _resolver_entrada(pa: pyaudio.PyAudio):
    """Resuelve el micro elegido en Ajustes (o AUDIO_INPUT_HINT) a un índice de
    dispositivo PyAudio y su sample rate. Devuelve (index, rate, nombre).

    Si no hay ninguno que encaje, cae al dispositivo de entrada por defecto."""
    try:
        from core.system_settings import audio_entrada_preferida
        hint = (audio_entrada_preferida() or "").strip()
    except Exception:  # noqa: BLE001
        hint = os.getenv("AUDIO_INPUT_HINT", "").strip()

    hints = [hint] if hint else ["AB17X", "G435"]
    for h in hints:
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) <= 0:
                continue
            if h.lower() in info.get("name", "").lower():
                rate = int(info.get("defaultSampleRate") or 0) or _RATE_MODEL
                return i, rate, info.get("name", f"#{i}")

    # Fallback: dispositivo por defecto del sistema.
    try:
        info = pa.get_default_input_device_info()
        rate = int(info.get("defaultSampleRate") or 0) or _RATE_MODEL
        print(f"⚠️ WakeWord: micro '{' / '.join(hints)}' no encontrado, "
              f"usando el de por defecto ({info.get('name', '?')})")
        return info.get("index"), rate, info.get("name", "default")
    except Exception:  # noqa: BLE001
        print(f"⚠️ WakeWord: micro '{' / '.join(hints)}' no encontrado y sin "
              f"dispositivo por defecto; usando 16 kHz genérico")
        return None, _RATE_MODEL, "default"


class _WakeWordListener:
    """WakeWordListener que captura del micro elegido en Ajustes y resamplea a
    16000 Hz para el modelo."""

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
        self._rate_device = _RATE_MODEL
        self._frame_device = _FRAME_MODEL
        self._frames_desde_infer = 0

    def _abrir_stream(self):
        """Abre el stream de captura probando el sample rate del dispositivo y,
        si falla, una lista de rates habituales."""
        index, rate, nombre = _resolver_entrada(self._pa)
        # 16 kHz primero: es el nativo del modelo y evita resamplear en cada
        # frame. Luego el rate declarado por el dispositivo y el resto.
        candidatos = []
        for r in (_RATE_MODEL, rate, *_RATES_FALLBACK):
            if r and r not in candidatos:
                candidatos.append(r)
        ultimo_error = None
        for r in candidatos:
            try:
                stream = self._pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=r,
                    input=True,
                    input_device_index=index,
                    frames_per_buffer=int(_FRAME_MS * r),
                )
                self._rate_device = r
                self._frame_device = int(_FRAME_MS * r)
                print(f"🎙️ WakeWord: capturando de '{nombre}' a {r} Hz "
                      f"(threshold={self._threshold})")
                return stream
            except Exception as exc:  # noqa: BLE001
                ultimo_error = exc
        raise RuntimeError(
            f"No se pudo abrir el micro '{nombre}' a ningún sample rate "
            f"({candidatos}): {ultimo_error}"
        )

    async def __aenter__(self):
        self._pa = pyaudio.PyAudio()
        self._stream = self._abrir_stream()
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
                    lambda: self._stream.read(self._frame_device, exception_on_overflow=False),
                )
                if not self._running:
                    break

                frame = _resample(np.frombuffer(data, dtype=np.int16))
                self._frame_buffer.append(frame)
                self._frames_desde_infer += 1

                if len(self._frame_buffer) < _CHUNK_FRAMES:
                    continue

                # Solo se infiere cada _HOP frames (por defecto cada 240 ms) para
                # no clavar la CPU con una inferencia completa cada 80 ms.
                if self._frames_desde_infer < _HOP:
                    continue
                self._frames_desde_infer = 0

                chunk = np.concatenate(list(self._frame_buffer))
                scores = await loop.run_in_executor(self._executor, self._model.predict, chunk)
                if not self._running:
                    break

                if _DEBUG and scores:
                    top = max(scores.items(), key=lambda kv: kv[1])
                    print(f"[WAKEWORD] score max: {top[0]}={top[1]:.3f} "
                          f"(umbral {self._threshold})")

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
        model = _cargar_modelo()
        print(f"🎙️ WakeWord: hop={_HOP} frames (~{_HOP * 80} ms), "
              f"ONNX threads={_ORT_THREADS}")
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
