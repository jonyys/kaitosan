from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from groq import Groq
from dotenv import load_dotenv
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

def cambiar_estado(nuevo_estado):
    """Cambia el estado de la cara del robot"""
    estado_robot["estado"] = nuevo_estado
    socketio.emit("estado", {"estado": nuevo_estado})

@app.route("/")
def index():
    return render_template("face.html")

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

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    cambiar_estado("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)