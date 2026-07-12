import threading
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
from dotenv import load_dotenv
from core.camera import Camera
from core.state import StateManager
from core.brain import Brain
from core.detection import PersonDetector
from core.config import FLASK_SECRET_KEY, ADMIN_PASSWORD
from flask import flash, redirect, url_for, session, request
from functools import wraps
from datetime import timedelta
from audio.recorder import Recorder
from ai.speech_to_text import SpeechToText
from ai.text_to_speech import TextToSpeech
from ai.pronunciation import comparar_pronunciacion



load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

app.secret_key = FLASK_SECRET_KEY
# Sesión caduca después de 30 minutos de inactividad
app.permanent_session_lifetime = timedelta(minutes=30)

# Inicializar módulos
camera = Camera()
state = StateManager(socketio)
brain = Brain(state, socketio)
detector = PersonDetector(camera, state, brain)
recorder = Recorder(device=1)
stt = SpeechToText()
tts = TextToSpeech(device=1)

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

        # Habla la respuesta en hilo separado
        def hablar_y_volver():
            tts.hablar(respuesta)
            state.cambiar("idle")

        threading.Thread(
            target=hablar_y_volver,
            daemon=True
        ).start()

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

@app.route("/grabar", methods=["POST"])
def grabar():
    try:
        # Escuchando
        state.cambiar("listening")

        # Graba
        archivo = recorder.record(duracion=5)
        if not archivo:
            state.cambiar("error")
            return jsonify({"error": "Error grabando"}), 500

        # Transcribe
        texto = stt.transcribir(archivo)
        if not texto:
            state.cambiar("idle")
            return jsonify({"error": "No se entendió nada"}), 400

        # Emite transcripción a la web
        socketio.emit("transcripcion", {"texto": texto})

        # ── Evaluar pronunciación si hay frase objetivo ──
        if brain.ultima_frase_objetivo:
            evaluacion = comparar_pronunciacion(
                brain.ultima_frase_objetivo, texto
            )
            print(f"🎌 Evaluación: {evaluacion['precision']}% - {evaluacion['feedback']}")
            # Limpiar para no evaluar mensajes posteriores
            brain.ultima_frase_objetivo = None

        # Pensando
        state.cambiar("thinking")

        # Responde con Groq
        respuesta = brain.responder(texto)

        # Hablando
        state.cambiar("speaking")
        socketio.emit("mensaje", {"texto": respuesta})

        # Habla la respuesta en hilo separado
        def hablar_y_volver():
            tts.hablar(respuesta)
            state.cambiar("idle")

        threading.Thread(
            target=hablar_y_volver,
            daemon=True
        ).start()

        return jsonify({
            "transcripcion": texto,
            "respuesta": respuesta,
            "estado": "ok"
        })

    except Exception as e:
        state.cambiar("error")
        return jsonify({"error": str(e)}), 500

# ── ADMIN ────────────────────────────────────────

def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session.permanent = True
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return render_template("admin_login.html",
                               error="Contraseña incorrecta")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@login_requerido
def admin():
    db = brain.memory._conectar()
    sesion_filtro = request.args.get("sesion_id", "")

    perfil = db.execute("""
        SELECT id, key, value FROM user_profile
        ORDER BY id ASC
    """).fetchall()

    perfil = [{"id": r[0], "key": r[1], "value": r[2]}
              for r in perfil]

    sesiones = db.execute("""
        SELECT id, started_at, ended_at, messages
        FROM sessions ORDER BY started_at DESC
    """).fetchall()

    sesiones = [{"id": r[0], "started_at": r[1],
                 "ended_at": r[2], "messages": r[3]}
                for r in sesiones]

    if sesion_filtro:
        mensajes = db.execute("""
            SELECT id, session_id, role, content, created_at
            FROM messages WHERE session_id = ?
            AND role != 'system'
            ORDER BY created_at ASC
        """, (sesion_filtro,)).fetchall()
    else:
        mensajes = db.execute("""
            SELECT id, session_id, role, content, created_at
            FROM messages WHERE role != 'system'
            ORDER BY created_at DESC LIMIT 100
        """).fetchall()

    mensajes = [{"id": r[0], "session_id": r[1],
                 "role": r[2], "content": r[3],
                 "created_at": r[4]}
                for r in mensajes]

    db.close()

    # --- consultar progreso de japonés ---
    jap_db = brain.jap_memory._conectar()
    jap_progreso = jap_db.execute("""
        SELECT id, category, item, detail, added_at,
               last_reviewed, times_reviewed, accuracy
        FROM japanese_progress
        ORDER BY added_at DESC
    """).fetchall()

    japones_progreso = []
    for r in jap_progreso:
        japones_progreso.append({
            "id": r[0],
            "category": r[1],
            "item": r[2],
            "detail": r[3],
            "added_at": r[4],
            "last_reviewed": r[5],
            "times_reviewed": r[6],
            "accuracy": r[7]
        })
    jap_db.close()

    return render_template("admin.html",
                           perfil=perfil,
                           sesiones=sesiones,
                           mensajes=mensajes,
                           sesion_filtro=sesion_filtro,
                           japones_progreso=japones_progreso)

@app.route("/admin/perfil/añadir", methods=["POST"])
@login_requerido
def admin_perfil_añadir():
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "").strip()
    if key and value:
        brain.memory.actualizar_perfil(key, value)
        flash("✅ Dato guardado correctamente", "success")
    else:
        flash("❌ Clave y valor son obligatorios", "error")
    return redirect(url_for("admin"))

@app.route("/admin/perfil/borrar/<int:item_id>",
           methods=["POST"])
@login_requerido
def admin_perfil_borrar(item_id):
    db = brain.memory._conectar()
    db.execute("DELETE FROM user_profile WHERE id = ?",
               (item_id,))
    db.commit()
    db.close()
    flash("✅ Dato borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/perfil/borrar-todo", methods=["POST"])
@login_requerido
def admin_perfil_borrar_todo():
    db = brain.memory._conectar()
    db.execute("DELETE FROM user_profile")
    db.commit()
    db.close()
    flash("✅ Perfil borrado completamente", "success")
    return redirect(url_for("admin"))

@app.route("/admin/sesiones/borrar/<int:sesion_id>",
           methods=["POST"])
@login_requerido
def admin_sesion_borrar(sesion_id):
    db = brain.memory._conectar()
    db.execute("DELETE FROM messages WHERE session_id = ?",
               (sesion_id,))
    db.execute("DELETE FROM sessions WHERE id = ?",
               (sesion_id,))
    db.commit()
    db.close()
    flash("✅ Sesión borrada", "success")
    return redirect(url_for("admin"))

@app.route("/admin/sesiones/borrar-todo", methods=["POST"])
@login_requerido
def admin_sesiones_borrar_todo():
    db = brain.memory._conectar()
    db.execute("DELETE FROM messages")
    db.execute("DELETE FROM sessions")
    db.commit()
    db.close()
    flash("✅ Todas las sesiones borradas", "success")
    return redirect(url_for("admin"))

@app.route("/admin/mensajes/borrar/<int:mensaje_id>",
           methods=["POST"])
@login_requerido
def admin_mensaje_borrar(mensaje_id):
    db = brain.memory._conectar()
    db.execute("DELETE FROM messages WHERE id = ?",
               (mensaje_id,))
    db.commit()
    db.close()
    flash("✅ Mensaje borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/japones/añadir", methods=["POST"])
@login_requerido
def admin_japones_añadir():
    category = request.form.get("category", "").strip()
    item = request.form.get("item", "").strip()
    detail = request.form.get("detail", "").strip()
    if category and item:
        brain.jap_memory.registrar_item(category, item, detail)
        flash("✅ Ítem añadido al progreso de japonés", "success")
    else:
        flash("❌ Categoría y elemento son obligatorios", "error")
    return redirect(url_for("admin"))

@app.route("/admin/japones/borrar/<int:item_id>", methods=["POST"])
@login_requerido
def admin_japones_borrar(item_id):
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_progress WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    flash("✅ Ítem borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/japones/borrar-todo", methods=["POST"])
@login_requerido
def admin_japones_borrar_todo():
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_progress")
    db.execute("DELETE FROM japanese_goals")
    db.commit()
    db.close()
    flash("✅ Todo el progreso de japonés ha sido borrado", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    camera.iniciar()
    detector.iniciar()
    state.cambiar("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)