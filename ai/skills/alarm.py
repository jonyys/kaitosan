import threading
import time
from datetime import datetime, timedelta
import numpy as np
import os
import sounddevice as sd
import soundfile as sf

RUTA_ALARMA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "audio", "alarma.flac")

# Suena en bucle hasta que lo paren; por si nadie está, se calla solo pasado este tiempo.
MAX_SONANDO_SEG = 300
POSPONER_MIN = 5

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def segundos_hasta(h, m, dias=None, ahora=None):
    """Segundos hasta la próxima vez que son las h:m (en uno de `dias`, 0 = lunes, si hay)."""
    ahora = ahora or datetime.now()
    for d in range(8):
        c = (ahora + timedelta(days=d)).replace(hour=h, minute=m, second=0, microsecond=0)
        if c > ahora and (not dias or c.weekday() in dias):
            return (c - ahora).total_seconds()


def texto_dias(dias):
    if not dias or len(dias) == 7:
        return "todos los días" if dias else ""
    if dias == [0, 1, 2, 3, 4]:
        return "de lunes a viernes"
    return ", ".join(DIAS_SEMANA[d] for d in dias)

class AlarmSkill:
    def __init__(self, sample_rate=48000, socketio=None):
        self.sample_rate = sample_rate
        self.alarmas = []
        self.temporizadores = []
        self.socketio = socketio
        self._next_id = 1
        self.sonando = None          # {"tipo": "alarma"|"temporizador", "texto": ...} mientras suena
        self._parar = threading.Event()

    def _siguiente_id(self):
        id_actual = self._next_id
        self._next_id += 1
        return id_actual

    def _emitir_estado(self):
        if self.socketio:
            try:
                self.socketio.emit("actualizar_reloj", self._estado_serializable())
            except Exception as e:
                print(f"⚠️ Error emitiendo actualizar_reloj: {e}")

    def _estado_serializable(self):
        return {
            "alarmas": [
                {"id": a["id"], "hora": a["hora"], "activa": a["activa"], "dias": a.get("dias", [])}
                for a in self.alarmas
            ],
            "temporizadores": [
                {
                    "id": t["id"],
                    "minutos": t["minutos"],
                    "segundos": t["segundos"],
                    "duracion_total": t["duracion_total"],
                    "inicio": t["inicio"],
                    "activo": t["activo"],
                    "pausado": t.get("pausado", False),
                    "restante": t.get("restante", t["duracion_total"])
                }
                for t in self.temporizadores
            ]
        }

    def _sonar(self):
        """Reproduce audio/alarma.flac (48 kHz estéreo) en bucle por el altavoz, con el volumen de
        Kaito, hasta parar() o MAX_SONANDO_SEG. Se corta desde el propio callback, no con sd.stop():
        parar un stream desde otro hilo bloquea PortAudio en la Pi (ver TextToSpeech._sonar)."""
        from ai.text_to_speech import buscar_altavoz
        from core.system_settings import volumen_factor
        data, sr = sf.read(RUTA_ALARMA, dtype="float32")
        data = data * volumen_factor()
        pos = 0
        limite = time.monotonic() + MAX_SONANDO_SEG
        terminado = threading.Event()

        def rellenar(salida, frames, _tiempo, _estado):
            nonlocal pos
            if self._parar.is_set() or time.monotonic() > limite:
                raise sd.CallbackStop
            salida[:] = data[(pos + np.arange(frames)) % len(data)]
            pos = (pos + frames) % len(data)

        stream = sd.OutputStream(
            samplerate=sr, device=buscar_altavoz(), channels=data.shape[1],
            dtype="float32", callback=rellenar, finished_callback=terminado.set,
        )
        stream.start()
        terminado.wait()
        stream.close()

    def _emitir_sonando(self):
        if self.socketio:
            try:
                self.socketio.emit("sonando", self.sonando or {"tipo": None})
            except Exception as e:
                print(f"⚠️ Error emitiendo sonando: {e}")

    def _empezar_a_sonar(self, info):
        # ponytail: si ya suena otra cosa, esta se pierde (alarma y temporizador a la vez, caso raro)
        if self.sonando:
            return
        self._parar.clear()
        self.sonando = info
        self._emitir_sonando()
        try:
            self._sonar()
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Error sonando: {e}")
        finally:
            if self.sonando is info:  # si parar() ya lo quitó, no se avisa dos veces
                self.sonando = None
                self._emitir_sonando()

    def parar(self):
        """Apaga lo que suena (alarma o temporizador)."""
        self._parar.set()
        if self.sonando:
            self.sonando = None
            self._emitir_sonando()

    def posponer(self, minutos=POSPONER_MIN):
        """Apaga la alarma que suena y la vuelve a sonar dentro de `minutos`."""
        info = self.sonando
        self.parar()
        if info and info["tipo"] == "alarma":
            timer = threading.Timer(minutos * 60, self._empezar_a_sonar, args=[dict(info)])
            timer.daemon = True
            timer.start()

    def _alarma_sonar(self, hora_str: str, alarma_id: int):
        print(f"⏰ ¡Alarma! Son las {hora_str}")
        # Sin días es de una sola vez: queda inactiva. Con días, se vuelve a programar para el siguiente
        for a in self.alarmas:
            if a["id"] == alarma_id:
                if a.get("dias"):
                    h, m = (int(x) for x in a["hora"].split(":"))
                    a["timer"] = self._programar(h, m, a["dias"], alarma_id)
                else:
                    a["activa"] = False
                break
        self._emitir_estado()
        self._empezar_a_sonar({"tipo": "alarma", "texto": hora_str})

    def _programar(self, h, m, dias, alarma_id):
        timer = threading.Timer(segundos_hasta(h, m, dias), self._alarma_sonar, args=[f"{h:02d}:{m:02d}", alarma_id])
        timer.daemon = True
        timer.start()
        return timer

    def poner_alarma(self, hora: str, minuto: int = 0, dias=None) -> str:
        try:
            partes = hora.replace(".", ":").split(":")
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else minuto
            dias = sorted({int(d) for d in (dias or []) if 0 <= int(d) <= 6})

            alarma_id = self._siguiente_id()
            alarma_info = {
                "id": alarma_id,
                "hora": f"{h:02d}:{m:02d}",
                "timer": self._programar(h, m, dias, alarma_id),
                "activa": True,
                "dias": dias,
            }
            self.alarmas.append(alarma_info)
            self._emitir_estado()

            cuando = f" {texto_dias(dias)}" if dias else ""
            return f"Alarma puesta para las {h:02d}:{m:02d}{cuando}."

        except Exception as e:
            print(f"❌ Error programando alarma: {e}")
            return "No he podido programar la alarma. ¿Puedes repetir la hora?"

    def activar_alarma(self, alarma_id: int, activa: bool) -> str:
        """Enciende o apaga una alarma sin borrarla (el interruptor de la pantalla del reloj)."""
        a = next((x for x in self.alarmas if x["id"] == alarma_id), None)
        if not a:
            return "No encontré esa alarma."
        if activa and not a["activa"]:
            h, m = (int(x) for x in a["hora"].split(":"))
            a["timer"] = self._programar(h, m, a.get("dias", []), alarma_id)
            a["activa"] = True
        elif not activa:
            a["timer"].cancel()
            a["activa"] = False
        self._emitir_estado()
        return f"Alarma de las {a['hora']} {'activada' if activa else 'desactivada'}."

    def cancelar_alarma(self, hora: str = None, indice: int = None) -> str:
        activas = [a for a in self.alarmas if a["activa"]]

        if hora:
            hora_norm = hora.replace(".", ":").strip()
            partes = hora_norm.split(":")
            if len(partes) == 2:
                hora_norm = f"{int(partes[0]):02d}:{int(partes[1]):02d}"
            for a in self.alarmas:
                if a["hora"] == hora_norm and a["activa"]:
                    a["timer"].cancel()
                    self.alarmas.remove(a)
                    self._emitir_estado()
                    return f"Alarma de las {hora_norm} cancelada."
            return f"No encontré una alarma activa para las {hora_norm}."

        # Si solo hay una activa, cancelar esa
        if len(activas) == 1:
            activas[0]["timer"].cancel()
            self.alarmas.remove(activas[0])
            self._emitir_estado()
            return f"Alarma de las {activas[0]['hora']} cancelada."

        if indice is not None:
            idx = indice - 1
            if 0 <= idx < len(activas):
                alarma = activas[idx]
                alarma["timer"].cancel()
                self.alarmas.remove(alarma)
                self._emitir_estado()
                return f"Alarma de las {alarma['hora']} cancelada."
            return "No encontré esa alarma."

        if not activas:
            return "No hay alarmas activas que cancelar."
        lista = ", ".join(a["hora"] for a in activas)
        return f"¿Cuál alarma quieres cancelar? Hay varias: {lista}"

    def modificar_alarma(self, hora_actual: str, nueva_hora: str) -> str:
        previa = next((a for a in self.alarmas if a["hora"] == hora_actual.replace(".", ":").strip() and a["activa"]), None)
        dias = previa.get("dias") if previa else None
        resultado_cancelar = self.cancelar_alarma(hora=hora_actual)
        if "cancelada" in resultado_cancelar:
            return self.poner_alarma(nueva_hora, dias=dias)
        return resultado_cancelar

    def listar_alarmas(self) -> str:
        activas = [a for a in self.alarmas if a["activa"]]
        if not activas:
            return "No hay alarmas programadas."
        lista = ", ".join(a["hora"] for a in activas)
        return f"Alarmas activas: {lista}."

    def _programar_temporizador(self, temp_id, segundos):
        timer = threading.Timer(segundos, self._temporizador_sono, args=[temp_id])
        timer.daemon = True
        timer.start()
        return timer

    def _temporizador_sono(self, temp_id):
        t = next((x for x in self.temporizadores if x["id"] == temp_id), None)
        if not t:
            return
        print(f"⏲️ ¡Temporizador! Han pasado {t['minutos']}m {t['segundos']}s")
        t["activo"] = False
        self._emitir_estado()
        duracion = " ".join(x for x in (f"{t['minutos']} min" if t["minutos"] else "",
                                         f"{t['segundos']} s" if t["segundos"] else "") if x)
        self._empezar_a_sonar({"tipo": "temporizador", "texto": duracion})

    def poner_temporizador(self, minutos: int = 0, segundos: int = 0) -> str:
        retraso = minutos * 60 + segundos
        if retraso <= 0:
            return "Necesito un tiempo válido para el temporizador."

        temp_id = self._siguiente_id()
        temp_info = {
            "id": temp_id,
            "minutos": minutos,
            "segundos": segundos,
            "duracion_total": retraso,
            "inicio": time.time(),
            "timer": self._programar_temporizador(temp_id, retraso),
            "activo": True,
            "pausado": False,
            "restante": retraso,
        }
        self.temporizadores.append(temp_info)
        self._emitir_estado()

        if minutos > 0 and segundos > 0:
            return f"Temporizador de {minutos} minutos y {segundos} segundos puesto."
        elif minutos > 0:
            return f"Temporizador de {minutos} minutos puesto."
        else:
            return f"Temporizador de {segundos} segundos puesto."

    def estado_temporizador(self, temp_id: int, accion: str) -> str:
        """Pausa, reanuda o detiene (vuelve a la duración entera, parado) un temporizador."""
        t = next((x for x in self.temporizadores if x["id"] == temp_id and x["activo"]), None)
        if not t:
            return "No encontré ese temporizador."
        total = t["duracion_total"]
        if accion == "pausar" and not t["pausado"]:
            t["timer"].cancel()
            t["restante"] = max(0, total - (time.time() - t["inicio"]))
            t["pausado"] = True
        elif accion == "reanudar" and t["pausado"]:
            # inicio se retrasa lo ya gastado: la cuenta atrás de la pantalla sigue valiendo igual
            t["inicio"] = time.time() - (total - t["restante"])
            t["timer"] = self._programar_temporizador(temp_id, t["restante"])
            t["pausado"] = False
        elif accion == "detener":
            t["timer"].cancel()
            t["restante"] = total
            t["pausado"] = True
        self._emitir_estado()
        return "Temporizador pausado." if t["pausado"] else "Temporizador en marcha."

    def cancelar_temporizador(self, indice: int = 1) -> str:
        activos = [t for t in self.temporizadores if t["activo"]]
        if not activos:
            return "No hay temporizadores activos."

        if len(activos) == 1:
            t = activos[0]
            t["timer"].cancel()
            self.temporizadores.remove(t)
            self._emitir_estado()
            return "Temporizador cancelado."

        idx = indice - 1
        if 0 <= idx < len(activos):
            t = activos[idx]
            t["timer"].cancel()
            self.temporizadores.remove(t)
            self._emitir_estado()
            return "Temporizador cancelado."
        return "No encontré ese temporizador."

    def listar_temporizadores(self) -> str:
        activos = [t for t in self.temporizadores if t["activo"]]
        if not activos:
            return "No hay temporizadores activos."
        partes = []
        for t in activos:
            restante = max(0, t["duracion_total"] - (time.time() - t["inicio"]))
            m = int(restante // 60)
            s = int(restante % 60)
            partes.append(f"{m}m {s}s restantes")
        return "Temporizadores: " + ", ".join(partes) + "."
