from flask_socketio import SocketIO

class StateManager:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.estado = "idle"

    def cambiar(self, nuevo_estado: str):
        self.estado = nuevo_estado
        self.socketio.emit("estado", {"estado": nuevo_estado})
        print(f"→ Estado: {nuevo_estado}")

    def get(self) -> str:
        return self.estado

    def es(self, estado: str) -> bool:
        return self.estado == estado