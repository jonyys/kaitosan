import os
import queue
import re
import time
import threading
import unicodedata
from audio.wakeword import WakeWordDetector
from ai.speech_to_text import transcribir_para_turno
from ai.sensei.kana import frases_para_card
from core.config import TRIGGERS_DESPEDIDA
from core.red import VigilanteRed
from core.emociones import es_solo_gracias, gesto_para_gracias

TIMEOUT_CONVERSACION_SEG = 3
# La animación de la cara al entrar en sensei dura 1,9-2,3 s: el saludo no suena hasta que acaba.
SENSEI_ENTRADA_SEG = float(os.getenv("SENSEI_ENTRADA_SEG", "2.4"))
# Al salir: la despedida no suena hasta que la pizarra ha bajado y la cara está al frente
# (~0,75 s). La animación de salida va después de la despedida.
SENSEI_SALIDA_SEG = float(os.getenv("SENSEI_SALIDA_SEG", "0.9"))


def _normalizar(texto: str) -> str:
    """minúsculas, sin tildes, sin puntuación — para comparar por igualdad."""
    sin_tildes = ''.join(
        c for c in unicodedata.normalize('NFD', texto.strip().lower())
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r'[^\w\s]', '', sin_tildes).strip()


def _esperar_hasta(momento):
    """Duerme hasta `momento` (time.monotonic). None o ya pasado: no espera."""
    if momento:
        time.sleep(max(0.0, momento - time.monotonic()))


class VoiceListener:
    def __init__(self, recorder, stt, brain, tts, state, socketio):
        self.recorder = recorder
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.state = state
        self.socketio = socketio
        self._detector = WakeWordDetector(on_detected=self._on_wakeword)
        self._red = VigilanteRed(socketio)

    def iniciar(self):
        self._red.iniciar()  # idempotente
        self._detector.iniciar()

    def _emitir_nivel(self, n):
        """Volumen de la voz para el aro de la cara; nunca debe romper la grabación."""
        try:
            self.socketio.emit("nivel_micro", {"n": round(n, 2)})
        except Exception:  # noqa: BLE001
            pass

    def detener(self):
        self._detector.detener()

    def set_no_molestar(self, activo: bool):
        """Con "no molestar" Kaito deja de escuchar el wakeword: solo responde al botón."""
        if activo:
            self._detector.pausar()
        else:
            self._detector.reanudar()
        print(f"🔕 No molestar {'activado' if activo else 'desactivado'}")

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
        Retorna True si se procesó algo y toca seguir escuchando; False si no
        hubo voz, el sistema estaba ocupado, o el turno acaba de salir del
        modo sensei (esa despedida cierra la conversación, no la alarga).
        """
        if self.state.get() != "idle":
            return False

        self.state.cambiar("listening")
        archivo = self.recorder.record_vad(timeout_inicio_seg=timeout_inicio_seg, al_nivel=self._emitir_nivel)
        if not archivo:
            self.state.cambiar("idle")
            return False

        texto, pron_ctx = transcribir_para_turno(
            self.stt, archivo,
            sensei_activo=self.brain.profesor.esta_activo(),
            modo_conv=self.brain.profesor.modo_conv,
            espera_japones=self.brain.profesor.espera_japones,
            al_oir=self.brain.profesor.precalentar_juez,
            al_oir_ja=self.brain.profesor.oir_japones,
            segundos_desde_turno=time.monotonic() - self.brain.ultimo_turno_ts,
        )
        if not texto:
            self.state.cambiar("idle")
            return False

        if _normalizar(texto) in TRIGGERS_DESPEDIDA:
            print(f"🤫 Despedida detectada ({texto!r}) — silencio")
            self.state.cambiar("idle")
            return False

        # Un "gracias" suelto se contesta solo con la cara, sin voz ni LLM.
        # En sensei no: ahí "arigatou" puede ser la frase que está practicando.
        if not self.brain.profesor.esta_activo() and es_solo_gracias(texto):
            gesto = gesto_para_gracias()
            print(f"🥰 Agradecimiento ({texto!r}) — solo cara: {gesto}")
            self.state.cambiar("idle")
            self.socketio.emit("gesto", {"gesto": gesto})
            return False

        self.tts.empezar_turno()
        self.state.cambiar("thinking")
        sensei_estaba_activo = self.brain.profesor.esta_activo()

        # Streaming del LLM: en sensei, la voz empieza con la primera frase mientras el
        # modelo aún escribe (LLM_STREAMING=0 lo apaga). Fuera de sensei, o si el modelo no
        # llega a dar frases (despedida, fallo), se habla la respuesta entera como siempre.
        en_directo = sensei_estaba_activo and os.getenv("LLM_STREAMING", "1") != "0"
        frases, dichas = queue.Queue(), []
        datos = {}                      # respuesta, en_sensei, objetivo (cuando el LLM acaba)
        iniciado, mostrado, cerrojo = threading.Event(), [], threading.Lock()

        def on_frase(frase, lento):
            dichas.append(frase)
            self.tts._lento_extra = lento
            frases.put(re.sub(r'https?://\S+', '', frase).strip())

        def mostrar():
            # El texto y la tarjeta de kana salen cuando EMPIEZA la voz Y ya está toda la
            # respuesta: si se ven antes, parece que Kaito se ha quedado pillado.
            with cerrojo:
                if mostrado or not datos:
                    return
                mostrado.append(True)
            self.socketio.emit("mensaje", {"texto": datos["respuesta"]})
            if datos["en_sensei"]:
                # En modo sensei, muestra en la cara la frase objetivo (o los 【…】
                # sueltos si no hay), siempre en solo kana (nunca kanji).
                self.socketio.emit(
                    "sensei_japones",
                    {"frases": frases_para_card(datos["respuesta"], datos["objetivo"])},
                )

        def al_iniciar_audio():
            iniciado.set()
            mostrar()
            self.state.cambiar("speaking")
            self.socketio.emit("estado", {"estado": "speaking"})

        def hablar_y_volver():
            try:
                if en_directo:
                    self.tts.hablar_frases(frases, on_start=al_iniciar_audio)
                else:
                    texto_audio = re.sub(r'https?://\S+', '', datos["respuesta"]).strip()
                    self.tts.hablar(texto_audio, lento_extra=datos["lento_extra"], on_start=al_iniciar_audio,
                                    no_antes_de=datos.get("no_antes_de"))
            except Exception as e:  # noqa: BLE001 — pase lo que pase, vuelve a idle (el ciclo espera)
                print(f"❌ Error al hablar: {e}")
            mostrar()  # si no llegó a sonar (error, callado), que al menos se vea
            # Salir del sensei: la animación a la cara normal va DESPUÉS de la despedida
            if self.brain._emitir_desactivar_sensei:
                self.brain._emitir_desactivar_sensei = False
                self.socketio.emit("modo_sensei", {"activo": False})
            self.state.cambiar("idle")
            self.socketio.emit("estado", {"estado": "idle"})

        voz = threading.Thread(target=hablar_y_volver, daemon=True)
        if en_directo:
            voz.start()  # espera las frases; suena con la primera
        try:
            respuesta, lento_extra = self.brain.responder(
                texto, pron_contexto=pron_ctx, on_frase=on_frase if en_directo else None)
        except BaseException:
            if en_directo:
                frases.put(None)  # que el hilo de voz no se quede esperando
            raise
        # Salir del modo sensei es una despedida: no sigas escuchando encadenado
        # como en modo conversación normal — que se calle y quede en idle hasta
        # el próximo "kaito".
        salio_de_sensei = sensei_estaba_activo and not self.brain.profesor.esta_activo()
        # (sin tarjeta en el saludo de entrada: el modo no estaba activo al empezar el turno)
        datos.update(
            respuesta=respuesta, lento_extra=lento_extra,
            en_sensei=self.brain.profesor.esta_activo() and sensei_estaba_activo,
            objetivo=getattr(self.brain.profesor, "ultima_frase_objetivo", None))
        # Acaba de entrar en sensei: la voz espera a que termine la animación de la cara
        entrada = getattr(self.brain.profesor, "entrada_ts", None)
        if not sensei_estaba_activo and self.brain.profesor.esta_activo() and isinstance(entrada, (int, float)):
            datos["no_antes_de"] = entrada + SENSEI_ENTRADA_SEG
        # Acaba de salir (despedida): la cara ya volvió a la normal al decidirlo (brain)
        if salio_de_sensei:
            datos["no_antes_de"] = self.brain.salida_ts + SENSEI_SALIDA_SEG
        if en_directo:
            if not dichas:  # no hubo streaming: se habla entera
                _esperar_hasta(datos.get("no_antes_de"))  # la despedida en streaming no puede llevar la espera al hilo de voz
                frases.put(re.sub(r'https?://\S+', '', respuesta).strip())
            frases.put(None)
            if iniciado.is_set():
                mostrar()  # la voz ya había empezado: ahora que está toda la respuesta, se ve
        else:
            voz.start()

        while self.state.get() != "idle":
            time.sleep(0.2)

        if self.tts.callado():
            print("🤐 Le han mandado callar: no sigue escuchando")
            return False
        if self.brain.asunto_cerrado:
            print("🏁 Asunto cerrado: no sigue escuchando")
            return False
        return not salio_de_sensei
