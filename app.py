from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
from groq import Groq
from dotenv import load_dotenv
from picamera2 import Picamera2
import cv2
import numpy as np
import threading
import os

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

# Instancia global de la cámara
picam = None

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

            # Captura frame
            frame = picam.capture_array()

            # Convierte de XBGR a BGR para OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)


            # Codifica como JPEG
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

# ── ESTADO ──────────────────────────────────────

def cambiar_estado(nuevo_estado):
    """Cambia el estado de la cara del robot"""
    estado_robot["estado"] = nuevo_estado
    socketio.emit("estado", {"estado": nuevo_estado})
    print(f"→ Estado: {nuevo_estado}")

# ── RUTAS ───────────────────────────────────────

@app.route("/")
def index():
    return render_template("face.html")

@app.route("/video")
def video():
    """Stream en directo de la cámara"""
    return Response(
        generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Obtener mensaje del usuario
        data = request.get_json()
        mensaje = data.get("mensaje", "")

        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400

        # Cara en modo escuchando
        cambiar_estado("listening")

        # Añadir mensaje al historial
        historial.append({
            "role": "user",
            "content": mensaje
        })

        # Cara en modo pensando
        cambiar_estado("thinking")

        # Llamar a Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=historial,
            max_tokens=200
        )

        # Obtener respuesta
        respuesta = response.choices[0].message.content

        # Añadir respuesta al historial
        historial.append({
            "role": "assistant",
            "content": respuesta
        })

        # Cara en modo hablando
        cambiar_estado("speaking")

        # Volver a idle después de la respuesta
        def volver_idle():
            import time
            time.sleep(3)
            cambiar_estado("idle")

        hilo = threading.Thread(target=volver_idle)
        hilo.daemon = True
        hilo.start()

        return jsonify({
            "respuesta": respuesta,
            "estado": "ok"
        })

    except Exception as e:
        cambiar_estado("error")
        return jsonify({"error": str(e)}), 500

@app.route("/estado", methods=["GET"])
def get_estado():
    """Devuelve el estado actual del robot"""
    return jsonify(estado_robot)

# ── MAIN ────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    iniciar_camara()
    cambiar_estado("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)