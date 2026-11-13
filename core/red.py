"""Vigila si el robot tiene internet (sin él no hay voz ni LLM) y avisa a la pantalla."""
import socket
import threading
import time

DESTINOS = (("1.1.1.1", 53), ("8.8.8.8", 53))
CADA_SEG = 20        # cada cuánto se comprueba
REEMITIR_SEG = 60    # y se repite el estado, para que una página recién cargada se entere


def hay_internet() -> bool:
    for destino in DESTINOS:
        try:
            socket.create_connection(destino, timeout=2).close()
            return True
        except OSError:
            continue
    return False


class VigilanteRed:
    def __init__(self, socketio):
        self.socketio = socketio
        self._hilo = None

    def iniciar(self):
        if self._hilo:
            return
        self._hilo = threading.Thread(target=self._bucle, daemon=True, name="vigilante-red")
        self._hilo.start()

    def _bucle(self):
        ultimo, desde_emision = None, 0
        while True:
            internet = hay_internet()
            if internet != ultimo or desde_emision >= REEMITIR_SEG:
                try:
                    self.socketio.emit("red", {"internet": internet})
                except Exception as e:  # noqa: BLE001 — avisar es opcional
                    print(f"⚠️ No se pudo emitir el estado de la red: {e}")
                ultimo, desde_emision = internet, 0
            desde_emision += CADA_SEG
            time.sleep(CADA_SEG)
