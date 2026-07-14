import threading
import time
import numpy as np
import sounddevice as sd

class AlarmSkill:
    def __init__(self, sample_rate=48000):
        self.sample_rate = sample_rate
        self.alarmas = []          # lista de alarmas activas
        self.temporizadores = []   # lista de temporizadores activos

    def _generar_sonido(self, duracion=0.5, frecuencia=880):
        """Genera un pitido simple y lo reproduce."""
        t = np.linspace(0, duracion, int(self.sample_rate * duracion), False)
        onda = 0.3 * np.sin(2 * np.pi * frecuencia * t)  # volumen moderado
        sd.play(onda, samplerate=self.sample_rate)
        sd.wait()

    def _alarma_sonar(self, hora_str: str):
        """Suena la alarma cuando llega la hora."""
        print(f"⏰ ¡Alarma! Son las {hora_str}")
        for _ in range(3):
            self._generar_sonido(0.3, 880)
            time.sleep(0.2)

    def poner_alarma(self, hora: str, minuto: int = 0) -> str:
        """
        Programa una alarma para una hora concreta (formato HH:MM o "7:00").
        Devuelve un mensaje de confirmación.
        """
        try:
            # Parsear hora
            partes = hora.replace(".", ":").split(":")
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else minuto

            ahora = time.localtime()
            hora_actual = ahora.tm_hour * 3600 + ahora.tm_min * 60 + ahora.tm_sec
            hora_alarma = h * 3600 + m * 60

            # Si la hora ya pasó hoy, programar para mañana
            if hora_alarma <= hora_actual:
                hora_alarma += 24 * 3600

            retraso = hora_alarma - hora_actual

            # Programar hilo
            timer = threading.Timer(retraso, self._alarma_sonar, args=[f"{h:02d}:{m:02d}"])
            timer.daemon = True
            timer.start()

            # Guardar en lista
            alarma_info = {
                "hora": f"{h:02d}:{m:02d}",
                "timer": timer,
                "activa": True
            }
            self.alarmas.append(alarma_info)

            return f"Alarma puesta para las {h:02d}:{m:02d}."

        except Exception as e:
            print(f"❌ Error programando alarma: {e}")
            return "No he podido programar la alarma. ¿Puedes repetir la hora?"

    def poner_temporizador(self, minutos: int = 0, segundos: int = 0) -> str:
        """
        Programa un temporizador que sonará después de X minutos/segundos.
        Devuelve un mensaje de confirmación.
        """
        retraso = minutos * 60 + segundos
        if retraso <= 0:
            return "Necesito un tiempo válido para el temporizador."

        def sonar_temporizador():
            print(f"⏲️ ¡Temporizador! Han pasado {minutos}m {segundos}s")
            for _ in range(2):
                self._generar_sonido(0.5, 440)
                time.sleep(0.3)

        timer = threading.Timer(retraso, sonar_temporizador)
        timer.daemon = True
        timer.start()

        temp_info = {
            "minutos": minutos,
            "segundos": segundos,
            "timer": timer,
            "activo": True
        }
        self.temporizadores.append(temp_info)

        if minutos > 0 and segundos > 0:
            return f"Temporizador de {minutos} minutos y {segundos} segundos puesto."
        elif minutos > 0:
            return f"Temporizador de {minutos} minutos puesto."
        else:
            return f"Temporizador de {segundos} segundos puesto."