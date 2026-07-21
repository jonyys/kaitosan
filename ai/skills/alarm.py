import threading
import time
import numpy as np
import sounddevice as sd

class AlarmSkill:
    def __init__(self, sample_rate=48000, socketio=None):
        self.sample_rate = sample_rate
        self.alarmas = []
        self.temporizadores = []
        self.socketio = socketio
        self._next_id = 1

    def _siguiente_id(self):
        id_actual = self._next_id
        self._next_id += 1
        return id_actual

    def _emitir_estado(self):
        if self.socketio:
            self.socketio.emit("actualizar_reloj", self._estado_serializable())

    def _estado_serializable(self):
        return {
            "alarmas": [
                {"id": a["id"], "hora": a["hora"], "activa": a["activa"]}
                for a in self.alarmas
            ],
            "temporizadores": [
                {
                    "id": t["id"],
                    "minutos": t["minutos"],
                    "segundos": t["segundos"],
                    "duracion_total": t["duracion_total"],
                    "inicio": t["inicio"],
                    "activo": t["activo"]
                }
                for t in self.temporizadores
            ]
        }

    def _generar_sonido(self, duracion=0.5, frecuencia=880):
        t = np.linspace(0, duracion, int(self.sample_rate * duracion), False)
        onda = 0.3 * np.sin(2 * np.pi * frecuencia * t)
        sd.play(onda, samplerate=self.sample_rate)
        sd.wait()

    def _alarma_sonar(self, hora_str: str, alarma_id: int):
        print(f"⏰ ¡Alarma! Son las {hora_str}")
        for _ in range(3):
            self._generar_sonido(0.3, 880)
            time.sleep(0.2)
        # Marcar como inactiva y emitir actualización
        for a in self.alarmas:
            if a["id"] == alarma_id:
                a["activa"] = False
                break
        self._emitir_estado()

    def poner_alarma(self, hora: str, minuto: int = 0) -> str:
        try:
            partes = hora.replace(".", ":").split(":")
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else minuto

            ahora = time.localtime()
            hora_actual = ahora.tm_hour * 3600 + ahora.tm_min * 60 + ahora.tm_sec
            hora_alarma = h * 3600 + m * 60

            if hora_alarma <= hora_actual:
                hora_alarma += 24 * 3600

            retraso = hora_alarma - hora_actual
            alarma_id = self._siguiente_id()

            timer = threading.Timer(retraso, self._alarma_sonar, args=[f"{h:02d}:{m:02d}", alarma_id])
            timer.daemon = True
            timer.start()

            alarma_info = {
                "id": alarma_id,
                "hora": f"{h:02d}:{m:02d}",
                "timer": timer,
                "activa": True
            }
            self.alarmas.append(alarma_info)
            self._emitir_estado()

            return f"Alarma puesta para las {h:02d}:{m:02d}."

        except Exception as e:
            print(f"❌ Error programando alarma: {e}")
            return "No he podido programar la alarma. ¿Puedes repetir la hora?"

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
        resultado_cancelar = self.cancelar_alarma(hora=hora_actual)
        if "cancelada" in resultado_cancelar:
            return self.poner_alarma(nueva_hora)
        return resultado_cancelar

    def listar_alarmas(self) -> str:
        activas = [a for a in self.alarmas if a["activa"]]
        if not activas:
            return "No hay alarmas programadas."
        lista = ", ".join(a["hora"] for a in activas)
        return f"Alarmas activas: {lista}."

    def poner_temporizador(self, minutos: int = 0, segundos: int = 0) -> str:
        retraso = minutos * 60 + segundos
        if retraso <= 0:
            return "Necesito un tiempo válido para el temporizador."

        temp_id = self._siguiente_id()
        inicio = time.time()

        def sonar_temporizador():
            print(f"⏲️ ¡Temporizador! Han pasado {minutos}m {segundos}s")
            for _ in range(2):
                self._generar_sonido(0.5, 440)
                time.sleep(0.3)
            for t in self.temporizadores:
                if t["id"] == temp_id:
                    t["activo"] = False
                    break
            self._emitir_estado()

        timer = threading.Timer(retraso, sonar_temporizador)
        timer.daemon = True
        timer.start()

        temp_info = {
            "id": temp_id,
            "minutos": minutos,
            "segundos": segundos,
            "duracion_total": retraso,
            "inicio": inicio,
            "timer": timer,
            "activo": True
        }
        self.temporizadores.append(temp_info)
        self._emitir_estado()

        if minutos > 0 and segundos > 0:
            return f"Temporizador de {minutos} minutos y {segundos} segundos puesto."
        elif minutos > 0:
            return f"Temporizador de {minutos} minutos puesto."
        else:
            return f"Temporizador de {segundos} segundos puesto."

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
