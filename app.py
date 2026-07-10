from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
from dotenv import load_dotenv
from core.camera import Camera
from core.state import StateManager
from core.brain import Brain
from core.detection import PersonDetector

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Inicializar módulos
camera = Camera()
state = StateManager(socketio)
brain = Brain(state, socketio)
detector = PersonDetector(camera, state, brain)

@app.route("/")
def index():
    return render_template("face.html")

@app.route("/video")
def video():
    return Response(
        camera.generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")

        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400

        state.cambiar("listening")
        state.cambiar("thinking")

        respuesta = brain.responder(mensaje)

        state.cambiar("speaking")
        socketio.emit("mensaje", {"texto": respuesta})

        import threading, time
        def volver_idle():
            tiempo = min(len(respuesta) * 0.05, 6)
            time.sleep(tiempo)
            state.cambiar("idle")

        threading.Thread(target=volver_idle, daemon=True).start()

        return jsonify({
            "respuesta": respuesta,
            "estado": "ok"
        })

    except Exception as e:
        state.cambiar("error")
        return jsonify({"error": str(e)}), 500

@app.route("/estado", methods=["GET"])
def get_estado():
    return jsonify({"estado": state.get()})

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    camera.iniciar()
    detector.iniciar()
    state.cambiar("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)