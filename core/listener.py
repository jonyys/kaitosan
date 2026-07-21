import re
import time
import threading
from audio.wakeword import WakeWordDetector

TIMEOUT_CONVERSACION_SEG = 3


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
        """Punto de entrada público para un único ciclo (usado por /grabar)."""
        self._ciclo_voz()

    def _on_wakeword(self):
        # Primera interacción activada por wakeword
        if not self._ciclo_voz():
            return

        # Modo conversación: sigue escuchando tras cada respuesta
        print("💬 Modo conversación activo")
        while True:
            if not self._ciclo_voz(timeout_inicio_seg=TIMEOUT_CONVERSACION_SEG):
                print("💬 Fin de conversación (sin respuesta)")
                break

    def _ciclo_voz(self, timeout_inicio_seg=0) -> bool:
        """
        Un ciclo completo: graba → transcribe → responde → habla.
        Retorna True si se procesó algo, False si no hubo voz o el sistema estaba ocupado.
        """
        if self.state.get() != "idle":
            return False

        self.state.cambiar("listening")
        archivo = self.recorder.record_vad(timeout_inicio_seg=timeout_inicio_seg)
        if not archivo:
            self.state.cambiar("idle")
            return False

        idioma_stt = None if self.brain.profesor.esta_activo() else "es"
        texto = self.stt.transcribir(archivo, idioma=idioma_stt)
        if not texto:
            self.state.cambiar("idle")
            return False

        self.state.cambiar("thinking")
        respuesta, lento_extra = self.brain.responder(texto)
        self.socketio.emit("mensaje", {"texto": respuesta})

        def al_iniciar_audio():
            self.state.cambiar("speaking")
            self.socketio.emit("estado", {"estado": "speaking"})

        def hablar_y_volver():
            texto_audio = re.sub(r'https?://\S+', '', respuesta).strip()
            self.tts.hablar(texto_audio, lento_extra=lento_extra, on_start=al_iniciar_audio)
            if self.brain._emitir_desactivar_sensei:
                self.brain._emitir_desactivar_sensei = False
                self.socketio.emit("modo_sensei", {"activo": False})
            self.state.cambiar("idle")
            self.socketio.emit("estado", {"estado": "idle"})

        threading.Thread(target=hablar_y_volver, daemon=True).start()

        while self.state.get() != "idle":
            time.sleep(0.2)

        return True
