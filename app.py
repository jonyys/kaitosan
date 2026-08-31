import atexit
import os
import signal
import sys
import tempfile
import threading
import time

# stdout/stderr en line-buffering: bajo systemd, Python usa búfer de bloque
# (~8 KB) y los print() de la conversación no llegan al journal hasta que se
# llena o el proceso reinicia. Así aparecen al instante en `journalctl -u kaito`.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(line_buffering=True)
from flask import Flask, render_template, request, jsonify, Response, send_file
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from dotenv import load_dotenv
from core.camera import Camera
from core.state import StateManager
from core.brain import Brain
from core.detection import PersonDetector
from core.listener import VoiceListener
from core.button import PowerButton
from core.config import FLASK_SECRET_KEY
from werkzeug.security import check_password_hash, generate_password_hash
from core.settings_store import settings_get, settings_set
from core import system_settings
from flask import flash, redirect, url_for, session, request
from functools import wraps
from datetime import timedelta, date
from audio.recorder import Recorder
from ai.speech_to_text import SpeechToText, transcribir_para_turno
from ai.text_to_speech import TextToSpeech
from ai.sensei.kana import bloques_japones
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


def emitir_japones_sensei(respuesta: str):
    """En modo sensei, manda a la cara los trozos 【…】 en solo kana (hiragana/
    katakana, nunca kanji) para mostrarlos en una card. Fuera de sensei, nada."""
    if not brain.profesor.esta_activo():
        return
    socketio.emit("sensei_japones", {"frases": bloques_japones(respuesta)})


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
        emitir_japones_sensei(respuesta)

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

        # Transcribe. En modo sensei estructurado se usa Azure (pronunciación);
        # en charla y fuera de sensei, Groq Whisper.
        texto, pron_ctx = transcribir_para_turno(
            stt, archivo,
            sensei_activo=brain.profesor.esta_activo(),
            modo_conv=brain.profesor.modo_conv,
            referencia=getattr(brain.profesor, "ultima_frase_objetivo", None),
            segundos_desde_turno=time.monotonic() - brain.ultimo_turno_ts,
        )

        if not texto:
            state.cambiar("idle")
            return jsonify({"error": "No se entendió nada"}), 400

        # Pensando
        state.cambiar("thinking")

        # Responde con Groq (siempre devuelve (respuesta, lento_extra))
        respuesta, lento_extra = brain.responder(texto, pron_contexto=pron_ctx)

        # Emitir mensaje (sin cambiar estado todavía)
        socketio.emit("mensaje", {"texto": respuesta})
        emitir_japones_sensei(respuesta)

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
        user = request.form.get("user", "").strip()
        pwd = request.form.get("password", "")
        pass_hash = settings_get("admin_pass_hash")
        if user == settings_get("admin_user") and pass_hash \
                and check_password_hash(pass_hash, pwd):
            session.permanent = True
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return render_template("admin_login.html",
                               error="Usuario o contraseña incorrectos")
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

    # --- Alarmas (en memoria, mismo origen que /reloj/alarmas) ---
    lista_alarmas = brain.alarm._estado_serializable()["alarmas"]

    tracker = TokenTracker()
    uso = tracker.consultar()
    tokens = uso.get("tokens", {})
    audio = uso.get("total_audio_seconds", 0)
    azure_mes = tracker.azure_stt_segundos_mes()

    return render_template("admin.html",
                            sistema=system_settings.sistema_info(),
                            perfil=perfil,
                            sesiones=sesiones,
                            mensajes=mensajes,
                            sesion_filtro=sesion_filtro,
                            jap_vocab=jap_vocab,
                            jap_grammar=jap_grammar,
                            jap_sessions=jap_sessions,
                            lista_recordatorios=lista_recordatorios,
                            lista_alarmas=lista_alarmas,
                            uso_tokens=tokens,
                            uso_audio=audio,
                            uso_azure=azure_mes)

@app.route("/admin/ajustes")
@login_requerido
def ajustes():
    # Fase 5: página + ruta GET (lecturas de la capa de sistema, Fase 3).
    # Fase 6: escrituras estáticas (hora, zona, volumen, brillo) -> rutas POST
    # más abajo. En el portátil todo son datos simulados y no se toca el sistema.
    return render_template(
        "ajustes.html",
        wifi=system_settings.wifi_estado(),
        bt=system_settings.bt_estado(),
        hora=system_settings.hora_estado(),
        zonas=system_settings.zona_listar(),
        volumen=system_settings.volumen_get(),
        brillo=system_settings.brillo_get(),
        inactividad_min=system_settings.pantalla_inactividad_get(),
        salud=system_settings.salud(),
        admin_user=settings_get("admin_user"),
        audio_salidas=system_settings.audio_salidas(),
        audio_entradas=system_settings.audio_entradas(),
        audio_output=settings_get("audio_output"),
        audio_input=settings_get("audio_input"),
        micro_ganancia=system_settings.micro_ganancia_get(),
        wakeword_umbral=system_settings.wakeword_umbral_get(),
    )


def _flash_resultado(resultado, ok_msg):
    """Traduce el `dict` de `system_settings` a un `flash()` (§7.2, bloque estático)."""
    if resultado.get("ok"):
        flash("✅ " + ok_msg, "success")
    else:
        flash("❌ " + resultado.get("error", "no se pudo completar la acción"), "error")


@app.route("/admin/ajustes/hora", methods=["POST"])
@login_requerido
def ajustes_hora():
    if request.form.get("modo") == "manual":
        system_settings.hora_set_ntp(False)
        fecha = request.form.get("datetime", "").strip()
        if fecha:
            _flash_resultado(system_settings.hora_set_manual(fecha), "Hora actualizada")
        else:
            flash("✅ Hora automática (NTP) desactivada", "success")
    else:
        _flash_resultado(system_settings.hora_set_ntp(True),
                         "Hora automática (NTP) activada")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/zona", methods=["POST"])
@login_requerido
def ajustes_zona():
    if request.form.get("auto"):
        _flash_resultado(system_settings.zona_auto(True),
                         "Zona horaria automática activada")
    else:
        system_settings.zona_auto(False)
        _flash_resultado(system_settings.zona_set(request.form.get("tz", "")),
                         "Zona horaria fijada")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/volumen", methods=["POST"])
@login_requerido
def ajustes_volumen():
    _flash_resultado(system_settings.volumen_set(request.form.get("volumen", "")),
                     "Volumen actualizado")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/brillo", methods=["POST"])
@login_requerido
def ajustes_brillo():
    _flash_resultado(system_settings.brillo_set(request.form.get("brillo", "")),
                     "Brillo actualizado")
    return redirect(url_for("ajustes"))

@app.route("/admin/ajustes/pantalla/inactividad", methods=["POST"])
@login_requerido
def ajustes_pantalla_inactividad():
    _flash_resultado(
        system_settings.pantalla_inactividad_set(request.form.get("minutos", "")),
        "Tiempo de inactividad actualizado")
    return redirect(url_for("ajustes"))

@app.route("/admin/ajustes/audio/salida", methods=["POST"])
@login_requerido
def ajustes_audio_salida():
    _flash_resultado(system_settings.audio_salida_set(request.form.get("id", "")),
                     "Altavoz actualizado")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/audio/entrada", methods=["POST"])
@login_requerido
def ajustes_audio_entrada():
    _flash_resultado(system_settings.audio_entrada_set(request.form.get("id", "")),
                     "Micrófono actualizado")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/audio/micro-ganancia", methods=["POST"])
@login_requerido
def ajustes_audio_micro_ganancia():
    _flash_resultado(system_settings.micro_ganancia_set(request.form.get("ganancia", "")),
                     "Ganancia del micrófono actualizada")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/audio/wakeword-umbral", methods=["POST"])
@login_requerido
def ajustes_audio_wakeword_umbral():
    _flash_resultado(system_settings.wakeword_umbral_set(request.form.get("umbral", "")),
                     "Umbral de activación de «Kaito» actualizado")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/audio/probar", methods=["POST"])
@login_requerido
def ajustes_audio_probar():
    tipo = (request.get_json(silent=True) or {}).get("tipo", "salida")
    resultado = (system_settings.audio_probar_micro() if tipo == "micro"
                 else system_settings.audio_probar_salida())
    return jsonify(resultado)


@app.route("/admin/ajustes/modelos")
@login_requerido
def ajustes_modelos():
    # Fase 9: lista en vivo desde api.groq.com + selección guardada (§7.2).
    return jsonify({
        "disponibles": system_settings.groq_modelos(),
        "seleccion": system_settings.groq_seleccion_get(),
    })


@app.route("/admin/ajustes/modelos", methods=["POST"])
@login_requerido
def ajustes_modelos_guardar():
    datos = request.get_json(silent=True) or {}
    sel = {
        "principal": datos.get("principal", ""),
        "sensei": datos.get("sensei", ""),
        "alternativos": datos.get("alternativos", []),
        "tools": datos.get("tools", []),
    }
    return jsonify(system_settings.groq_seleccion_set(sel))


# --- WiFi (Fase 13): API JSON + fetch. Cambiar de red tumba la sesión, así que
# `conectar` responde ANTES y el watchdog de reversión va en un hilo (§7.2, §7.4). --- #

@app.route("/admin/ajustes/wifi")
@login_requerido
def ajustes_wifi():
    return jsonify({
        "estado": system_settings.wifi_estado(),
        "guardadas": system_settings.wifi_guardadas(),
    })


@app.route("/admin/ajustes/wifi/escanear")
@login_requerido
def ajustes_wifi_escanear():
    return jsonify(system_settings.wifi_escanear())


@app.route("/admin/ajustes/wifi/conectar", methods=["POST"])
@login_requerido
def ajustes_wifi_conectar():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.wifi_conectar(
        datos.get("ssid", ""), datos.get("psk", "")))


@app.route("/admin/ajustes/wifi/olvidar", methods=["POST"])
@login_requerido
def ajustes_wifi_olvidar():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.wifi_olvidar(datos.get("ssid", "")))


@app.route("/admin/ajustes/wifi/portal", methods=["POST"])
@login_requerido
def ajustes_wifi_portal():
    return jsonify(system_settings.wifi_abrir_portal())


# --- Bluetooth (Fase 14): mismo patrón que WiFi — API JSON + fetch (§7.2). El
# escaneo y el emparejado son asíncronos, así que van por fetch, no form-POST. --- #

@app.route("/admin/ajustes/bluetooth")
@login_requerido
def ajustes_bluetooth():
    return jsonify({
        "estado": system_settings.bt_estado(),
        "emparejados": system_settings.bt_emparejados(),
    })


@app.route("/admin/ajustes/bluetooth/escanear")
@login_requerido
def ajustes_bluetooth_escanear():
    try:
        seg = int(request.args.get("seg", 10))
    except ValueError:
        seg = 10
    return jsonify(system_settings.bt_escanear(seg))


@app.route("/admin/ajustes/bluetooth/conectar", methods=["POST"])
@login_requerido
def ajustes_bluetooth_conectar():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.bt_conectar(datos.get("mac", "")))


@app.route("/admin/ajustes/bluetooth/desconectar", methods=["POST"])
@login_requerido
def ajustes_bluetooth_desconectar():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.bt_desconectar(datos.get("mac", "")))


@app.route("/admin/ajustes/bluetooth/olvidar", methods=["POST"])
@login_requerido
def ajustes_bluetooth_olvidar():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.bt_olvidar(datos.get("mac", "")))


@app.route("/admin/ajustes/bluetooth/radio", methods=["POST"])
@login_requerido
def ajustes_bluetooth_radio():
    datos = request.get_json(silent=True) or {}
    return jsonify(system_settings.bt_radio(bool(datos.get("on"))))


@app.route("/admin/ajustes/cuenta", methods=["POST"])
@login_requerido
def ajustes_cuenta():
    # Cambiar usuario y contraseña del panel (§4.5). Verifica la contraseña
    # actual, guarda `admin_user` y `admin_pass_hash` en app_settings.
    user = request.form.get("user", "").strip()
    actual = request.form.get("password_actual", "")
    nueva = request.form.get("password_nueva", "")

    pass_hash = settings_get("admin_pass_hash")
    if not pass_hash or not check_password_hash(pass_hash, actual):
        flash("❌ La contraseña actual no es correcta", "error")
        return redirect(url_for("ajustes"))
    if not user:
        flash("❌ El usuario no puede estar vacío", "error")
        return redirect(url_for("ajustes"))

    settings_set("admin_user", user)
    if nueva:
        settings_set("admin_pass_hash", generate_password_hash(nueva))
        flash("✅ Usuario y contraseña actualizados", "success")
    else:
        flash("✅ Usuario actualizado", "success")
    return redirect(url_for("ajustes"))


# --- Mantenimiento (Fase 10): salud, logs y copia de seguridad (§7.2) --- #

def _resp_logs(texto: str, descargar: bool, nombre: str) -> Response:
    cab = {"Content-Disposition": f"attachment; filename={nombre}"} if descargar else {}
    return Response(texto, mimetype="text/plain; charset=utf-8", headers=cab)


@app.route("/admin/ajustes/sistema/logs")
@login_requerido
def ajustes_sistema_logs():
    descargar = bool(request.args.get("descargar"))
    n = 2000 if descargar else 500
    return _resp_logs(system_settings.logs(n), descargar, "kaito-servicio.log")


@app.route("/admin/ajustes/sistema/logs-conversacion")
@login_requerido
def ajustes_sistema_logs_conversacion():
    return _resp_logs(system_settings.logs_conversacion(),
                      bool(request.args.get("descargar")), "kaito-conversacion.log")


@app.route("/admin/ajustes/sistema/backup")
@login_requerido
def ajustes_sistema_backup():
    ruta = system_settings.backup_bd()
    return send_file(ruta, as_attachment=True, download_name="kaito.db")


@app.route("/admin/ajustes/sistema/restaurar", methods=["POST"])
@login_requerido
def ajustes_sistema_restaurar():
    subido = request.files.get("bd")
    if not subido or not subido.filename:
        flash("❌ Elige un fichero .db para restaurar", "error")
        return redirect(url_for("ajustes"))

    tmp = os.path.join(tempfile.gettempdir(),
                       "kaito-restore-" + (secure_filename(subido.filename) or "subida.db"))
    subido.save(tmp)
    try:
        resultado = system_settings.restaurar_bd(tmp)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    if resultado.get("ok"):
        flash("✅ BD restaurada. " + resultado.get("aviso", ""), "success")
    else:
        flash("❌ " + resultado.get("error", "no se pudo restaurar"), "error")
    return redirect(url_for("ajustes"))


@app.route("/admin/ajustes/sistema/diagnostico")
@login_requerido
def ajustes_sistema_diagnostico():
    ruta = system_settings.diagnostico_zip()
    return send_file(ruta, as_attachment=True,
                     download_name=os.path.basename(ruta))


# --- Mantenimiento (Fase 11): actualizar / reiniciar servicio / reset (§7.2) --- #
# Todas son fetch/JSON: la sesión se cae al reiniciar el servicio, así que la
# respuesta se manda ANTES (el trabajo real va en un hilo daemon, ver
# system_settings).

@app.route("/admin/ajustes/sistema/actualizar", methods=["POST"])
@login_requerido
def ajustes_sistema_actualizar():
    return jsonify(system_settings.actualizar())


@app.route("/admin/ajustes/sistema/reiniciar-servicio", methods=["POST"])
@login_requerido
def ajustes_sistema_reiniciar_servicio():
    return jsonify(system_settings.reiniciar_servicio())


@app.route("/admin/ajustes/sistema/reset", methods=["POST"])
@login_requerido
def ajustes_sistema_reset():
    return jsonify(system_settings.reset_fabrica())


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
    due_today = (
        db.execute(
            "SELECT COUNT(*) FROM japanese_vocabulary WHERE next_review <= ?", (today,)
        ).fetchone()[0]
        + db.execute(
            "SELECT COUNT(*) FROM japanese_kanji WHERE next_review <= ?", (today,)
        ).fetchone()[0]
    )
    vocab_by_status = dict(db.execute(
        "SELECT status, COUNT(*) FROM japanese_vocabulary GROUP BY status"
    ).fetchall())
    total_kanji = db.execute("SELECT COUNT(*) FROM japanese_kanji").fetchone()[0]
    kanji_by_status = dict(db.execute(
        "SELECT status, COUNT(*) FROM japanese_kanji GROUP BY status"
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

    kanji_rows = db.execute("""
        SELECT id, kanji, meaning, status, reps, ease_factor, interval_days,
               next_review, times_correct, errors, times_reviewed
        FROM japanese_kanji ORDER BY next_review ASC, status
    """).fetchall()
    kanji = [{"id": r[0], "kanji": r[1], "meaning": r[2], "status": r[3],
              "reps": r[4], "ease_factor": r[5], "interval_days": r[6],
              "next_review": r[7], "times_correct": r[8], "errors": r[9],
              "times_reviewed": r[10]} for r in kanji_rows]

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
        total_kanji=total_kanji,
        kanji_by_status=kanji_by_status,
        total_grammar=total_grammar,
        total_sessions=total_sessions,
        last_session=last_session,
        vocab=vocab,
        kanji=kanji,
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

@app.route("/japones/vocabulario/marcar-aprendido/<int:item_id>", methods=["POST"])
@login_requerido
def japones_vocab_marcar_aprendido(item_id):
    # Aprendida al 100%: fuera de la cola de repaso (next_review a 100 años vista).
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_vocabulary SET
            status='mastered', reps=8, ease_factor=2.5, interval_days=36500,
            next_review=date('now','+36500 days'), errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ Marcada como aprendida", "success")
    return redirect(url_for("japones"))

@app.route("/japones/kanji/añadir", methods=["POST"])
@login_requerido
def japones_kanji_añadir():
    jp = request.form.get("jp", "").strip()
    es = request.form.get("es", "").strip()
    if jp and es:
        today = date.today().isoformat()
        db = brain.jap_memory._conectar()
        db.execute("""
            INSERT INTO japanese_kanji
                (kanji, meaning, status, confidence, errors, times_reviewed,
                 reps, ease_factor, interval_days, next_review, times_correct)
            VALUES (?, ?, 'learning', 0, 0, 0, 0, 2.5, 0, ?, 0)
        """, (jp, es, today))
        db.commit()
        db.close()
        flash(f"✅ '{jp}' añadido a kanjis", "success")
    else:
        flash("❌ El kanji y su significado son obligatorios", "error")
    return redirect(url_for("japones"))

@app.route("/japones/kanji/borrar/<int:item_id>", methods=["POST"])
@login_requerido
def japones_kanji_borrar(item_id):
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_kanji WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    flash("✅ Kanji borrado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/kanji/borrar-todo", methods=["POST"])
@login_requerido
def japones_kanji_borrar_todo():
    db = brain.jap_memory._conectar()
    db.execute("DELETE FROM japanese_kanji")
    db.commit()
    db.close()
    flash("✅ Todos los kanjis borrados", "success")
    return redirect(url_for("japones"))

@app.route("/japones/kanji/resetear-srs/<int:item_id>", methods=["POST"])
@login_requerido
def japones_kanji_resetear_srs(item_id):
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_kanji SET
            reps=0, ease_factor=2.5, interval_days=0,
            next_review=date('now'), status='learning',
            times_reviewed=0, times_correct=0, errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ SRS de kanji reseteado", "success")
    return redirect(url_for("japones"))

@app.route("/japones/kanji/marcar-aprendido/<int:item_id>", methods=["POST"])
@login_requerido
def japones_kanji_marcar_aprendido(item_id):
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_kanji SET
            status='mastered', reps=8, ease_factor=2.5, interval_days=36500,
            next_review=date('now','+36500 days'), errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ Kanji marcado como aprendido", "success")
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

@app.route("/japones/gramatica/marcar-aprendido/<int:item_id>", methods=["POST"])
@login_requerido
def japones_gram_marcar_aprendido(item_id):
    # Aprendida al 100%: mastery a tope y fuera de la cola de repaso.
    db = brain.jap_memory._conectar()
    db.execute("""
        UPDATE japanese_grammar SET
            mastery=100, reps=8, ease_factor=2.5, interval_days=36500,
            next_review=date('now','+36500 days'), errors=0
        WHERE id=?
    """, (item_id,))
    db.commit()
    db.close()
    flash("✅ Marcada como aprendida", "success")
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

@app.route("/admin/alarmas/borrar/<int:alarma_id>", methods=["POST"])
@login_requerido
def admin_alarma_borrar(alarma_id):
    alarma = next((a for a in brain.alarm.alarmas if a["id"] == alarma_id), None)
    if not alarma:
        flash("❌ Alarma no encontrada", "error")
        return redirect(url_for("admin"))
    if alarma.get("timer"):
        alarma["timer"].cancel()
    brain.alarm.alarmas.remove(alarma)
    brain.alarm._emitir_estado()
    flash("✅ Alarma borrada", "success")
    return redirect(url_for("admin"))

@app.route("/admin/alarmas/borrar-todo", methods=["POST"])
@login_requerido
def admin_alarma_borrar_todo():
    for a in list(brain.alarm.alarmas):
        if a.get("timer"):
            a["timer"].cancel()
    brain.alarm.alarmas.clear()
    brain.alarm._emitir_estado()
    flash("✅ Todas las alarmas borradas", "success")
    return redirect(url_for("admin"))

_apagado = False


def _apagar():
    """Cierre ordenado: vuelca a la BD la sesión sensei en curso (SRS + resumen)
    y cierra la sesión general. Idempotente."""
    global _apagado
    if _apagado:
        return
    _apagado = True
    try:
        if brain.profesor.esta_activo():
            print("🎌 Cerrando la sesión de sensei antes de salir…")
            brain.profesor.salir()
        else:
            brain.profesor.cerrar_sesion_y_extraer()  # por si quedó abierta sin 'activo'
    except Exception as e:
        print(f"⚠️ Error cerrando la sesión de sensei: {e}")
    try:
        brain.cerrar_sesion()
    except Exception as e:
        print(f"⚠️ Error cerrando la sesión general: {e}")


def _on_sigterm(signum, frame):
    # systemd/kill mandan SIGTERM: lo convertimos en salida limpia para que corra _apagar.
    raise SystemExit(0)


atexit.register(_apagar)
signal.signal(signal.SIGTERM, _on_sigterm)


if __name__ == "__main__":
    print("🤖 Kaitosan arrancando...")
    camera.iniciar()
    detector.iniciar()
    voice_listener.iniciar()
    PowerButton(on_short_press=voice_listener._on_wakeword)
    state.cambiar("idle")
    try:
        # allow_unsafe_werkzeug: bajo systemd no hay TTY y Flask-SocketIO se niega
        # a usar el servidor Werkzeug sin este flag (a mano sí arranca). Kaito es
        # un aparato de un solo usuario en la LAN, el server de Werkzeug basta.
        # FLASK_DEBUG controla el modo debug del servidor (por defecto activado).
        _debug = os.getenv("FLASK_DEBUG", "true").strip().lower() in ("1", "true", "yes", "on")
        socketio.run(app, host="0.0.0.0", port=5000, debug=_debug,
                     use_reloader=False, allow_unsafe_werkzeug=True)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        _apagar()