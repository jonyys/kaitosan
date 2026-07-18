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
from core.token_tracker import TokenTracker



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
recorder = Recorder()
stt = SpeechToText()
tts = TextToSpeech()
tts.socketio = socketio


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

        respuesta, lento_extra = brain.responder(mensaje)

        # Emitir mensaje (sin cambiar estado todavía)
        socketio.emit("mensaje", {"texto": respuesta})

        # Callback que se ejecuta cuando el audio empieza de verdad
        def al_iniciar_audio():
            state.cambiar("speaking")
            socketio.emit("estado", {"estado": "speaking"})

        def hablar_y_volver():
            tts.hablar(respuesta, lento_extra=lento_extra, on_start=al_iniciar_audio)
            state.cambiar("idle")
            socketio.emit("estado", {"estado": "idle"})

        threading.Thread(target=hablar_y_volver, daemon=True).start()

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
        # Usar japonés si estamos en modo sensei, español en caso contrario
        idioma_stt = None if brain.profesor.esta_activo() else "es"
        texto = stt.transcribir(archivo, idioma=idioma_stt)

        if not texto:
            state.cambiar("idle")
            return jsonify({"error": "No se entendió nada"}), 400

        # La evaluación de pronunciación vive dentro de
        # ProfesorJapones.responder_turno (no se duplica aquí).

        # Pensando
        state.cambiar("thinking")

        # Responde con Groq (siempre devuelve (respuesta, lento_extra))
        respuesta, lento_extra = brain.responder(texto)

        #state.cambiar("speaking")
        socketio.emit("mensaje", {"texto": respuesta})

        # Hablando
        # Emitir mensaje (sin cambiar estado todavía)
        socketio.emit("mensaje", {"texto": respuesta})

        # Callback que se ejecuta cuando el audio empieza de verdad
        def al_iniciar_audio():
            state.cambiar("speaking")
            socketio.emit("estado", {"estado": "speaking"})

        def hablar_y_volver():
            tts.hablar(respuesta, lento_extra=lento_extra, on_start=al_iniciar_audio)
            state.cambiar("idle")
            socketio.emit("estado", {"estado": "idle"})

        threading.Thread(target=hablar_y_volver, daemon=True).start()

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

    # --- Consultar progreso de japonés ---
    jap_db = brain.jap_memory._conectar()
    
    # Skills
    skills = jap_db.execute("""
        SELECT skill, percentage FROM japanese_skills ORDER BY skill
    """).fetchall()
    jap_skills = [{"skill": r[0], "percentage": r[1]} for r in skills]

    # Vocabulario
    vocab = jap_db.execute("""
        SELECT word, reading, meaning, type, status, confidence, errors,
               last_reviewed, times_reviewed
        FROM japanese_vocabulary
        ORDER BY status, word
    """).fetchall()
    jap_vocab = []
    for r in vocab:
        jap_vocab.append({
            "word": r[0], "reading": r[1], "meaning": r[2], "type": r[3],
            "status": r[4], "confidence": r[5], "errors": r[6],
            "last_reviewed": r[7], "times_reviewed": r[8]
        })

    # Gramática
    grammar = jap_db.execute("""
        SELECT grammar_point, description, mastery, errors, last_used
        FROM japanese_grammar ORDER BY mastery DESC
    """).fetchall()
    jap_grammar = []
    for r in grammar:
        jap_grammar.append({
            "point": r[0], "description": r[1], "mastery": r[2],
            "errors": r[3], "last_used": r[4]
        })

    # Temas
    topics = jap_db.execute("""
        SELECT topic, can_handle FROM japanese_topics ORDER BY topic
    """).fetchall()
    jap_topics = [{"topic": r[0], "can_handle": bool(r[1])} for r in topics]

    # Sesiones de japonés
    sessions_jap = jap_db.execute("""
        SELECT id, started_at, ended_at, words_learned, grammar_practiced,
               errors_noted, summary
        FROM japanese_sessions ORDER BY started_at DESC
    """).fetchall()
    jap_sessions = []
    for r in sessions_jap:
        jap_sessions.append({
            "id": r[0], "started_at": r[1], "ended_at": r[2],
            "words_learned": r[3], "grammar_practiced": r[4],
            "errors_noted": r[5], "summary": r[6]
        })

    # Perfil generado más reciente
    perfil_jap = jap_db.execute("""
        SELECT summary_text, generated_at FROM japanese_profile
        ORDER BY generated_at DESC LIMIT 1
    """).fetchone()
    jap_profile = None
    if perfil_jap:
        jap_profile = {"text": perfil_jap[0], "date": perfil_jap[1]}

    jap_db.close()

    # --- Recordatorios ---
    rem_db = brain.reminder._conectar()
    recordatorios = rem_db.execute("""
        SELECT id, texto, fecha_hora, creado, completado
        FROM reminders
        ORDER BY completado ASC, fecha_hora DESC
    """).fetchall()
    lista_recordatorios = []
    for r in recordatorios:
        lista_recordatorios.append({
            "id": r[0],
            "texto": r[1],
            "fecha_hora": r[2],
            "creado": r[3],
            "completado": bool(r[4])
        })
    rem_db.close()

    tracker = TokenTracker()
    uso = tracker.consultar()
    tokens = uso.get("tokens", {})
    audio = uso.get("total_audio_seconds", 0)

    return render_template("admin.html",
                            perfil=perfil,
                            sesiones=sesiones,
                            mensajes=mensajes,
                            sesion_filtro=sesion_filtro,
                            jap_skills=jap_skills,
                            jap_vocab=jap_vocab,
                            jap_grammar=jap_grammar,
                            jap_topics=jap_topics,
                            jap_sessions=jap_sessions,
                            jap_profile=jap_profile,
                            lista_recordatorios=lista_recordatorios)

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

# TODO(admin-japonés): estas 3 rutas apuntan al esquema VIEJO y están rotas.
# - `registrar_item` no existe en JapaneseMemory (usar `add_item`).
# - las tablas `japanese_progress` y `japanese_goals` fueron eliminadas
#   (el nuevo esquema usa `japanese_vocabulary` / `japanese_grammar` + SRS).
# Fuera del alcance del plan "modo sensei"; reapuntar al nuevo esquema en una
# tarea futura (decisión (b) del plan, Fase 7 punto 7).
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
    # TODO(admin-japonés): esquema viejo; `japanese_progress` ya no existe.
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_progress WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    flash("✅ Ítem borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/japones/borrar-todo", methods=["POST"])
@login_requerido
def admin_japones_borrar_todo():
    # TODO(admin-japonés): esquema viejo; `japanese_progress`/`japanese_goals` ya no existen.
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_progress")
    db.execute("DELETE FROM japanese_goals")
    db.commit()
    db.close()
    flash("✅ Todo el progreso de japonés ha sido borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/recordatorios/borrar/<int:rem_id>", methods=["POST"])
@login_requerido
def admin_rem_borrar(rem_id):
    db = brain.reminder._conectar()
    db.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
    db.commit()
    db.close()
    flash("✅ Recordatorio borrado", "success")
    return redirect(url_for("admin"))

@app.route("/admin/recordatorios/borrar-todo", methods=["POST"])
@login_requerido
def admin_rem_borrar_todo():
    db = brain.reminder._conectar()
    db.execute("DELETE FROM reminders")
    db.commit()
    db.close()
    flash("✅ Todos los recordatorios borrados", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    camera.iniciar()
    detector.iniciar()
    state.cambiar("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)