from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
from groq import Groq
from dotenv import load_dotenv
from picamera2 import Picamera2
import cv2
import threading
import os
import time

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Historial de conversación
historial = [
    {
        "role": "system",
        "content": """Eres Kaitosan, un robot asistente de 
        escritorio simpático, cercano y conciso. 
        Respondes siempre en español.
        Tus respuestas son cortas y naturales,
        como en una conversación normal."""
    }
]

# Estado actual del robot
estado_robot = {"estado": "idle"}

# Estado de detección de persona
deteccion = {
    "hay_persona": False,
    "activo": True
}

# Instancia global de la cámara
picam = None

# Detector de caras preentrenado
detector_caras = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ── CÁMARA ──────────────────────────────────────

def iniciar_camara():
    global picam
    try:
        picam = Picamera2()
        config = picam.create_preview_configuration(
            main={"size": (640, 480)}
        )
        picam.configure(config)
        picam.start()
        print("✅ Cámara iniciada")
    except Exception as e:
        print(f"❌ Error iniciando cámara: {e}")
        picam = None

def generar_frames():
    global picam
    while True:
        try:
            if picam is None:
                break

            frame = picam.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            ret, buffer = cv2.imencode('.jpg', frame_bgr)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n'
                   + frame_bytes + b'\r\n')

        except Exception as e:
            print(f"❌ Error generando frame: {e}")
            break

# ── DETECCIÓN DE PERSONAS ────────────────────────

def detectar_personas():
    global picam
    print("👁️ Detección de personas iniciada")

    while deteccion["activo"]:
        try:
            if picam is None:
                time.sleep(1)
                continue

            frame = picam.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            gris = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            caras = detector_caras.detectMultiScale(
                gris,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            hay_persona_ahora = len(caras) > 0

            if hay_persona_ahora and not deteccion["hay_persona"]:
                print("✅ ¡Persona detectada!")
                deteccion["hay_persona"] = True

                if estado_robot["estado"] == "idle":
                    cambiar_estado("happy")
                    threading.Thread(
                        target=saludar_persona,
                        daemon=True
                    ).start()

            elif not hay_persona_ahora and deteccion["hay_persona"]:
                print("👋 Persona se ha ido")
                deteccion["hay_persona"] = False

                if estado_robot["estado"] not in ["thinking", "speaking"]:
                    cambiar_estado("idle")

        except Exception as e:
            print(f"❌ Error en detección: {e}")

        time.sleep(0.5)

def saludar_persona():
    try:
        cambiar_estado("thinking")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Eres Kaitosan, un robot asistente simpático. Respondes en español."
                },
                {
                    "role": "user",
                    "content": "Acabo de sentarme delante de ti, salúdame de forma breve y simpática"
                }
            ],
            max_tokens=100
        )

        saludo = response.choices[0].message.content
        print(f"🤖 Kaitosan: {saludo}")

        cambiar_estado("speaking")
        socketio.emit("mensaje", {"texto": saludo})

        time.sleep(3)
        cambiar_estado("idle")

    except Exception as e:
        print(f"❌ Error saludando: {e}")
        cambiar_estado("idle")

# ── ESTADO ──────────────────────────────────────

def cambiar_estado(nuevo_estado):
    estado_robot["estado"] = nuevo_estado
    socketio.emit("estado", {"estado": nuevo_estado})
    print(f"→ Estado: {nuevo_estado}")

# ── RUTAS ───────────────────────────────────────

@app.route("/")
def index():
    return render_template("face.html")

@app.route("/video")
def video():
    return Response(
        generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")

        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400

        cambiar_estado("listening")

        historial.append({
            "role": "user",
            "content": mensaje
        })

        cambiar_estado("thinking")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=historial,
            max_tokens=200
        )

        respuesta = response.choices[0].message.content

        historial.append({
            "role": "assistant",
            "content": respuesta
        })

        cambiar_estado("speaking")
        socketio.emit("mensaje", {"texto": respuesta})

        def volver_idle():
            time.sleep(3)
            cambiar_estado("idle")

        threading.Thread(target=volver_idle, daemon=True).start()

        return jsonify({
            "respuesta": respuesta,
            "estado": "ok"
        })

    except Exception as e:
        cambiar_estado("error")
        return jsonify({"error": str(e)}), 500

@app.route("/estado", methods=["GET"])
def get_estado():
    return jsonify(estado_robot)

# ── MAIN ────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    iniciar_camara()

    hilo_deteccion = threading.Thread(
        target=detectar_personas,
        daemon=True
    )
    hilo_deteccion.start()

    cambiar_estado("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)