import threading
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
from dotenv import load_dotenv
from core.camera import Camera
from core.state import StateManager
from core.brain import Brain
from core.detection import PersonDetector
from core.listener import VoiceListener
from core.config import FLASK_SECRET_KEY, ADMIN_PASSWORD
from flask import flash, redirect, url_for, session, request
from functools import wraps
from datetime import timedelta, date
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

voice_listener = VoiceListener(recorder, stt, brain, tts, state, socketio)


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
            if brain._emitir_desactivar_sensei:
                brain._emitir_desactivar_sensei = False
                socketio.emit("modo_sensei", {"activo": False})
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
            if brain._emitir_desactivar_sensei:
                brain._emitir_desactivar_sensei = False
                socketio.emit("modo_sensei", {"activo": False})
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

# ── RELOJ ────────────────────────────────────────

@app.route("/reloj")
def reloj():
    return render_template("reloj.html")

@app.route("/reloj/alarmas", methods=["GET"])
def reloj_alarmas_listar():
    return jsonify(brain.alarm._estado_serializable())

@app.route("/reloj/alarmas", methods=["POST"])
def reloj_alarma_crear():
    data = request.get_json()
    hora = data.get("hora", "")
    if not hora:
        return jsonify({"error": "Falta la hora"}), 400
    resultado = brain.alarm.poner_alarma(hora)
    return jsonify({"mensaje": resultado, **brain.alarm._estado_serializable()})

@app.route("/reloj/alarmas/<int:alarma_id>", methods=["DELETE"])
def reloj_alarma_borrar(alarma_id):
    alarma = next((a for a in brain.alarm.alarmas if a["id"] == alarma_id), None)
    if not alarma:
        return jsonify({"error": "Alarma no encontrada"}), 404
    alarma["timer"].cancel()
    brain.alarm.alarmas.remove(alarma)
    brain.alarm._emitir_estado()
    return jsonify({"mensaje": "Alarma eliminada", **brain.alarm._estado_serializable()})

@app.route("/reloj/alarmas/<int:alarma_id>", methods=["PUT"])
def reloj_alarma_modificar(alarma_id):
    data = request.get_json()
    nueva_hora = data.get("hora", "")
    if not nueva_hora:
        return jsonify({"error": "Falta la nueva hora"}), 400
    alarma = next((a for a in brain.alarm.alarmas if a["id"] == alarma_id), None)
    if not alarma:
        return jsonify({"error": "Alarma no encontrada"}), 404
    alarma["timer"].cancel()
    brain.alarm.alarmas.remove(alarma)
    resultado = brain.alarm.poner_alarma(nueva_hora)
    return jsonify({"mensaje": resultado, **brain.alarm._estado_serializable()})

@app.route("/reloj/temporizadores", methods=["POST"])
def reloj_temporizador_crear():
    data = request.get_json()
    minutos = int(data.get("minutos", 0))
    segundos = int(data.get("segundos", 0))
    if minutos == 0 and segundos == 0:
        return jsonify({"error": "Tiempo inválido"}), 400
    resultado = brain.alarm.poner_temporizador(minutos, segundos)
    return jsonify({"mensaje": resultado, **brain.alarm._estado_serializable()})

@app.route("/reloj/temporizadores/<int:temp_id>", methods=["DELETE"])
def reloj_temporizador_borrar(temp_id):
    temp = next((t for t in brain.alarm.temporizadores if t["id"] == temp_id), None)
    if not temp:
        return jsonify({"error": "Temporizador no encontrado"}), 404
    temp["timer"].cancel()
    brain.alarm.temporizadores.remove(temp)
    brain.alarm._emitir_estado()
    return jsonify({"mensaje": "Temporizador eliminado", **brain.alarm._estado_serializable()})

@app.route("/reloj/recordatorios", methods=["GET"])
def reloj_recordatorios_listar():
    return jsonify(brain.reminder._estado_serializable())

@app.route("/reloj/recordatorios", methods=["POST"])
def reloj_recordatorio_crear():
    data = request.get_json()
    texto = data.get("texto", "").strip()
    fecha_hora = data.get("fecha_hora", "").strip()
    if not texto or not fecha_hora:
        return jsonify({"error": "Faltan campos"}), 400
    # Normalizar: acepta "2026-07-22T10:00" o "2026-07-22 10:00"
    fecha_hora = fecha_hora.replace("T", " ")[:16]
    try:
        from datetime import datetime as _dt
        _dt.strptime(fecha_hora, "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido (usa YYYY-MM-DDTHH:MM)"}), 400
    db = brain.reminder._conectar()
    db.execute("INSERT INTO reminders (texto, fecha_hora) VALUES (?, ?)", (texto, fecha_hora))
    db.commit()
    db.close()
    brain.reminder._emitir_estado()
    return jsonify({"mensaje": "Recordatorio creado", **brain.reminder._estado_serializable()})

@app.route("/reloj/recordatorios/<int:rem_id>", methods=["DELETE"])
def reloj_recordatorio_borrar(rem_id):
    db = brain.reminder._conectar()
    row = db.execute("SELECT texto FROM reminders WHERE id = ?", (rem_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Recordatorio no encontrado"}), 404
    db.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
    db.commit()
    db.close()
    brain.reminder._emitir_estado()
    return jsonify({"mensaje": "Recordatorio eliminado", **brain.reminder._estado_serializable()})

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
                            jap_vocab=jap_vocab,
                            jap_grammar=jap_grammar,
                            jap_sessions=jap_sessions,
                            lista_recordatorios=lista_recordatorios,
                            uso_tokens=tokens,
                            uso_audio=audio)

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

# ── JAPONÉS ──────────────────────────────────────

@app.route("/japones")
@login_requerido
def japones():
    today = date.today().isoformat()
    db = brain.jap_memory._conectar()

    total_vocab = db.execute("SELECT COUNT(*) FROM japanese_vocabulary").fetchone()[0]
    due_today = db.execute(
        "SELECT COUNT(*) FROM japanese_vocabulary WHERE next_review <= ?", (today,)
    ).fetchone()[0]
    vocab_by_status = dict(db.execute(
        "SELECT status, COUNT(*) FROM japanese_vocabulary GROUP BY status"
    ).fetchall())
    total_grammar = db.execute("SELECT COUNT(*) FROM japanese_grammar").fetchone()[0]
    total_sessions = db.execute("SELECT COUNT(*) FROM japanese_sessions").fetchone()[0]

    last_session_row = db.execute("""
        SELECT summary, started_at FROM japanese_sessions
        WHERE summary IS NOT NULL ORDER BY started_at DESC LIMIT 1
    """).fetchone()
    last_session = {"summary": last_session_row[0], "date": last_session_row[1]} if last_session_row else None

    vocab_rows = db.execute("""
        SELECT id, word, meaning, status, reps, ease_factor, interval_days,
               next_review, times_correct, errors, times_reviewed
        FROM japanese_vocabulary ORDER BY next_review ASC, status
    """).fetchall()
    vocab = [{"id": r[0], "word": r[1], "meaning": r[2], "status": r[3],
              "reps": r[4], "ease_factor": r[5], "interval_days": r[6],
              "next_review": r[7], "times_correct": r[8], "errors": r[9],
              "times_reviewed": r[10]} for r in vocab_rows]

    grammar_rows = db.execute("""
        SELECT id, grammar_point, description, mastery, reps, ease_factor,
               interval_days, next_review, times_correct, errors
        FROM japanese_grammar ORDER BY mastery DESC
    """).fetchall()
    grammar = [{"id": r[0], "point": r[1], "description": r[2], "mastery": r[3],
                "reps": r[4], "ease_factor": r[5], "interval_days": r[6],
                "next_review": r[7], "times_correct": r[8], "errors": r[9]} for r in grammar_rows]

    session_rows = db.execute("""
        SELECT id, started_at, ended_at, words_learned, grammar_practiced,
               errors_noted, summary
        FROM japanese_sessions ORDER BY started_at DESC
    """).fetchall()
    sessions = [{"id": r[0], "started_at": r[1], "ended_at": r[2],
                 "words_learned": r[3], "grammar_practiced": r[4],
                 "errors_noted": r[5], "summary": r[6]} for r in session_rows]

    db.close()
    return render_template("japones.html",
        today=today,
        total_vocab=total_vocab,
        due_today=due_today,
        vocab_by_status=vocab_by_status,
        total_grammar=total_grammar,
        total_sessions=total_sessions,
        last_session=last_session,
        vocab=vocab,
        grammar=grammar,
        sessions=sessions,
    )

@app.route("/japones/vocabulario/añadir", methods=["POST"])
@login_requerido
def japones_vocab_añadir():
    jp = request.form.get("jp", "").strip()
    es = request.form.get("es", "").strip()
    if jp and es:
        today = date.today().isoformat()
        db = brain.jap_memory._conectar()
        db.execute("""
            INSERT INTO japanese_vocabulary
                (word, meaning, status, confidence, errors, times_reviewed,
                 reps, ease_factor, interval_days, next_review, times_correct)
            VALUES (?, ?, 'learning', 0, 0, 0, 0, 2.5, 0, ?, 0)
        """, (jp, es, today))
        db.commit()
        db.close()
        flash(f"✅ '{jp}' añadido al vocabulario", "success")
    else:
        flash("❌ La palabra en japonés y el significado son obligatorios", "error")
    return redirect(url_for("japones"))

@app.route("/japones/vocabulario/borrar/<int:item_id>", methods=["POST"])
@login_requerido
def japones_vocab_borrar(item_id):
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_vocabulary WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    flash("✅ Palabra borrada", "success")
    return redirect(url_for("japones"))

@app.route("/japones/vocabulario/borrar-todo", methods=["POST"])
@login_requerido
def japones_vocab_borrar_todo():
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_vocabulary")
    db.commit()
    db.close()
    flash("✅ Todo el vocabulario borrado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/vocabulario/resetear-srs/<int:item_id>", methods=["POST"])
@login_requerido
def japones_vocab_resetear_srs(item_id):
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_vocabulary SET
            reps=0, ease_factor=2.5, interval_days=0,
            next_review=date('now'), status='learning',
            times_reviewed=0, times_correct=0, errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ SRS reseteado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/gramatica/añadir", methods=["POST"])
@login_requerido
def japones_gram_añadir():
    jp = request.form.get("jp", "").strip()
    es = request.form.get("es", "").strip()
    if jp and es:
        today = date.today().isoformat()
        db = brain.jap_memory._conectar()
        db.execute("""
            INSERT INTO japanese_grammar
                (grammar_point, description, mastery, errors,
                 reps, ease_factor, interval_days, next_review, times_seen, times_correct)
            VALUES (?, ?, 0, 0, 0, 2.5, 0, ?, 0, 0)
        """, (jp, es, today))
        db.commit()
        db.close()
        flash(f"✅ '{jp}' añadido a gramática", "success")
    else:
        flash("❌ El punto gramatical y la descripción son obligatorios", "error")
    return redirect(url_for("japones"))

@app.route("/japones/gramatica/borrar/<int:item_id>", methods=["POST"])
@login_requerido
def japones_gram_borrar(item_id):
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_grammar WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    flash("✅ Punto gramatical borrado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/gramatica/borrar-todo", methods=["POST"])
@login_requerido
def japones_gram_borrar_todo():
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_grammar")
    db.commit()
    db.close()
    flash("✅ Toda la gramática borrada", "success")
    return redirect(url_for("japones"))

@app.route("/japones/gramatica/resetear-srs/<int:item_id>", methods=["POST"])
@login_requerido
def japones_gram_resetear_srs(item_id):
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_grammar SET
            reps=0, ease_factor=2.5, interval_days=0,
            next_review=date('now'), mastery=0,
            times_seen=0, times_correct=0, errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ SRS de gramática reseteado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/sesiones/borrar/<int:sesion_id>", methods=["POST"])
@login_requerido
def japones_sesion_borrar(sesion_id):
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_sessions WHERE id = ?", (sesion_id,))
    db.commit()
    db.close()
    flash("✅ Sesión borrada", "success")
    return redirect(url_for("japones"))

@app.route("/japones/sesiones/borrar-todo", methods=["POST"])
@login_requerido
def japones_sesiones_borrar_todo():
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_sessions")
    db.commit()
    db.close()
    flash("✅ Todas las sesiones de japonés borradas", "success")
    return redirect(url_for("japones"))

# ── ADMIN – rutas viejas de japonés (redirigen al panel nuevo) ────────────────

@app.route("/admin/japones/añadir", methods=["POST"])
@login_requerido
def admin_japones_añadir():
    return redirect(url_for("japones"))

@app.route("/admin/japones/borrar/<int:item_id>", methods=["POST"])
@login_requerido
def admin_japones_borrar(item_id):
    return redirect(url_for("japones"))

@app.route("/admin/japones/borrar-todo", methods=["POST"])
@login_requerido
def admin_japones_borrar_todo():
    return redirect(url_for("japones"))

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
    voice_listener.iniciar()
    state.cambiar("idle")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)