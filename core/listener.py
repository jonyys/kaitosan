import time
import threading
from audio.wakeword import WakeWordDetector


class VoiceListener:
    def __init__(self, recorder, stt, brain, tts, state, socketio):
        self.recorder = recorder
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.state = state
        self.socketio = socketio
        self._detector = WakeWordDetector(on_detected=self._on_wakeword)

    def iniciar(self):
        self._detector.iniciar()

    def detener(self):
        self._detector.detener()

    def procesar_voz(self):
        """Graba con VAD, transcribe, responde y habla. Bloqueante hasta que termina el TTS."""
        if self.state.get() != "idle":
            return

        self.state.cambiar("listening")
        archivo = self.recorder.record_vad()
        if not archivo:
            self.state.cambiar("idle")
            return

        idioma_stt = None if self.brain.profesor.esta_activo() else "es"
        texto = self.stt.transcribir(archivo, idioma=idioma_stt)
        if not texto:
            self.state.cambiar("idle")
            return

        self.state.cambiar("thinking")
        respuesta, lento_extra = self.brain.responder(texto)
        self.socketio.emit("mensaje", {"texto": respuesta})

        def al_iniciar_audio():
            self.state.cambiar("speaking")
            self.socketio.emit("estado", {"estado": "speaking"})

        def hablar_y_volver():
            self.tts.hablar(respuesta, lento_extra=lento_extra, on_start=al_iniciar_audio)
            if self.brain._emitir_desactivar_sensei:
                self.brain._emitir_desactivar_sensei = False
                self.socketio.emit("modo_sensei", {"activo": False})
            self.state.cambiar("idle")
            self.socketio.emit("estado", {"estado": "idle"})

        threading.Thread(target=hablar_y_volver, daemon=True).start()

        while self.state.get() != "idle":
            time.sleep(0.2)

    def _on_wakeword(self):
        self.procesar_voz()
