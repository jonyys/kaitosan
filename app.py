from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

estado_robot = {"estado": "idle"}

@app.route("/")
def index():
    return render_template("face.html")

def cambiar_estado(nuevo_estado):
    estado_robot["estado"] = nuevo_estado
    socketio.emit("estado", {"estado": nuevo_estado})

def demo_estados():
    time.sleep(3)
    while True:
        print("→ IDLE")
        cambiar_estado("idle")
        time.sleep(4)

        print("→ ESCUCHANDO")
        cambiar_estado("listening")
        time.sleep(3)

        print("→ PENSANDO")
        cambiar_estado("thinking")
        time.sleep(3)

        print("→ HABLANDO")
        cambiar_estado("speaking")
        time.sleep(3)

        print("→ FELIZ")
        cambiar_estado("happy")
        time.sleep(3)

if __name__ == "__main__":
    hilo = threading.Thread(target=demo_estados)
    hilo.daemon = True
    hilo.start()
    socketio.run(app, host="0.0.0.0", port=5000)