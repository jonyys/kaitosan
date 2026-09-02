import atexit
import hashlib
import os
import random
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
from flask import Flask, render_template, request, jsonify, Response, send_file, abort
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
from core import japanese_items
from flask import flash, redirect, url_for, session, request
from functools import wraps
from datetime import timedelta, date
from audio.recorder import Recorder
from ai.speech_to_text import SpeechToText, transcribir_para_turno
from ai.text_to_speech import TextToSpeech
from ai.sensei.kana import bloques_japones, romaji
from ai.sensei.kanji_n5 import KANJI_N5
from ai.sensei.curriculum import CURRICULUM
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
    return render_template("reloj.html", noche=system_settings.noche_get())


# ── KIOSKO: gestos y ajustes rápidos de la pantalla del propio robot ──────────
# Sin login (es la pantalla del aparato), pero las escrituras solo desde
# localhost: un móvil en la LAN usa /admin/ajustes con contraseña.

def _solo_local():
    return request.remote_addr in ("127.0.0.1", "::1")


def _kiosko_config():
    b = system_settings.brillo_get()
    pct = round(b["valor"] / b["max"] * 100) if b.get("max") else 0
    return {
        "screensaver_min": system_settings.pantalla_inactividad_get(),
        "volumen": system_settings.volumen_get(),
        "brillo": {"soportado": bool(b.get("soportado")), "pct": pct},
        "noche": system_settings.noche_get(),
    }


@app.route("/kiosko/config")
def kiosko_config():
    return jsonify(_kiosko_config())


@app.route("/kiosko/volumen", methods=["POST"])
def kiosko_volumen():
    if not _solo_local():
        abort(403)
    r = system_settings.volumen_set(request.form.get("v", ""))
    return jsonify(r), (200 if r.get("ok") else 400)


@app.route("/kiosko/brillo", methods=["POST"])
def kiosko_brillo():
    if not _solo_local():
        abort(403)
    r = system_settings.brillo_set(request.form.get("v", ""))
    return jsonify(r), (200 if r.get("ok") else 400)


@app.route("/kiosko/noche", methods=["POST"])
def kiosko_noche():
    if not _solo_local():
        abort(403)
    n = system_settings.noche_get()
    r = system_settings.noche_set(request.form.get("enabled", ""), n["start"], n["end"])
    return jsonify(r), (200 if r.get("ok") else 400)

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


@app.errorhandler(404)
def _error_404(e):
    return render_template("error.html", codigo=404, titulo="No encontrado",
                           mensaje="Esta página no existe o se ha movido."), 404


@app.errorhandler(500)
def _error_500(e):
    return render_template("error.html", codigo=500, titulo="Algo ha fallado",
                           mensaje="Error interno. Inténtalo de nuevo en un momento."), 500

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
        noche=system_settings.noche_get(),
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

@app.route("/admin/ajustes/pantalla/noche", methods=["POST"])
@login_requerido
def ajustes_pantalla_noche():
    _flash_resultado(
        system_settings.noche_set(
            request.form.get("enabled", ""),
            request.form.get("start", ""),
            request.form.get("end", "")),
        "Modo noche actualizado")
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
    can_dos_dominados = db.execute(
        "SELECT COUNT(*) FROM can_do_progreso WHERE estado = 'dominado'"
    ).fetchone()[0]
    vocab_by_status = dict(db.execute(
        "SELECT status, COUNT(*) FROM japanese_vocabulary GROUP BY status"
    ).fetchall())
    total_kanji = db.execute("SELECT COUNT(*) FROM japanese_kanji").fetchone()[0]
    kanji_by_status = dict(db.execute(
        "SELECT status, COUNT(*) FROM japanese_kanji GROUP BY status"
    ).fetchall())
    total_grammar = db.execute("SELECT COUNT(*) FROM japanese_grammar").fetchone()[0]
    total_sessions = db.execute("SELECT COUNT(*) FROM japanese_sessions").fetchone()[0]

    # Denominador de las barras de progreso: TODO lo que hay que aprender
    # (temario + lo que Laura haya metido en BD), no solo lo que ya tiene ficha.
    _curr_vocab = {str(e.get("jp") or "").strip()
                   for u in CURRICULUM for e in u.get("items", [])
                   if e.get("kind") == "vocabulario" and e.get("tipo") != "kanji"
                   and str(e.get("jp") or "").strip()}
    _db_vocab = {r[0] for r in db.execute(
        "SELECT word FROM japanese_vocabulary WHERE type IS NULL OR type != 'kanji'")}
    vocab_corpus = len(_curr_vocab | _db_vocab) or 1
    _db_kanji = {r[0] for r in db.execute("SELECT kanji FROM japanese_kanji")}
    kanji_corpus = len({k["jp"] for k in KANJI_N5} | _db_kanji) or 1
    _curr_gram = {str(e.get("jp") or "").strip()
                  for u in CURRICULUM for e in u.get("items", [])
                  if e.get("kind") == "gramatica" and str(e.get("jp") or "").strip()}
    _db_gram = {r[0] for r in db.execute("SELECT grammar_point FROM japanese_grammar")}
    gram_corpus = len(_curr_gram | _db_gram) or 1

    # La gramática no tiene columna status; se deriva de reps / mastery / intervalo.
    g_learning = g_learned = g_mastered = 0
    for reps, interval, mastery in db.execute(
        "SELECT COALESCE(reps,0), COALESCE(interval_days,0), COALESCE(mastery,0) "
        "FROM japanese_grammar"
    ):
        if mastery >= 100 or interval >= 21:
            g_mastered += 1
        elif interval >= 7 or reps >= 2:
            g_learned += 1
        else:
            g_learning += 1
    grammar_by_status = {"learning": g_learning, "learned": g_learned, "mastered": g_mastered}

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
        vocab_corpus=vocab_corpus,
        can_dos_dominados=can_dos_dominados,
        vocab_by_status=vocab_by_status,
        total_kanji=total_kanji,
        kanji_corpus=kanji_corpus,
        kanji_by_status=kanji_by_status,
        total_grammar=total_grammar,
        gram_corpus=gram_corpus,
        grammar_by_status=grammar_by_status,
        total_sessions=total_sessions,
        last_session=last_session,
        vocab=vocab,
        kanji=kanji,
        grammar=grammar,
        sessions=sessions,
    )

@app.route("/japones/kanjis")
@login_requerido
def japones_kanjis():
    selected = request.args.get("kanji", "").strip()
    mnemos_laura = brain.jap_memory.get_mnemos()
    dominados = brain.jap_memory.dominados("kanji")
    kanjis = []
    categorias = []
    for item in KANJI_N5:
        cat_id = item.get("categoria", "")
        if cat_id and not any(c["id"] == cat_id for c in categorias):
            categorias.append({
                "id": cat_id,
                "nombre": item.get("categoria_nombre", cat_id).split("—")[-1].strip(),
            })
        kanjis.append({
            "kanji": item.get("jp", ""),
            "dominado": item.get("jp", "") in dominados,
            "meaning": item.get("meaning", ""),
            "reading": item.get("reading", "") or item.get("kun", "") or item.get("on", ""),
            "reading_card": item.get("reading_card", ""),
            "on": item.get("on", ""),
            "kun": item.get("kun", ""),
            "trazos": item.get("trazos", ""),
            "radical": item.get("radical", ""),
            "literal": item.get("literal", ""),
            "ejemplo": item.get("ejemplo", ""),
            "mnemo": mnemos_laura.get(item.get("jp", "")) or item.get("mnemo", ""),
            "mnemo_default": item.get("mnemo", ""),
            "mnemo_propia": item.get("jp", "") in mnemos_laura,
            "uso": item.get("uso", ""),
            "vocab_ejemplo": item.get("vocab_ejemplo", ""),
            "categoria": cat_id,
        })
    for c in categorias:
        suyos = [k for k in kanjis if k["categoria"] == c["id"]]
        c["total"] = len(suyos)
        c["hechos"] = sum(1 for k in suyos if k["dominado"])
    total_dom = sum(1 for k in kanjis if k["dominado"])
    if selected:
        selected_item = next((k for k in kanjis if k["kanji"] == selected), kanjis[0] if kanjis else None)
    else:
        selected_item = kanjis[0] if kanjis else None
    return render_template("japones_kanjis.html", kanjis=kanjis,
                           categorias=categorias, selected=selected_item,
                           total_dom=total_dom)


_TEMARIO_TITULOS = {"vocabulario": "Vocabulario N5", "gramatica": "Gramática N5"}
_TEMARIO_EXTRA = {"vocabulario": "Vocabulario extra (sesiones)",
                  "gramatica": "Gramática extra (sesiones)"}


_AUDIO_JP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "static", "audio", "jp")


def _audio_clave(texto: str) -> str:
    return hashlib.md5((texto or "").strip().encode("utf-8")).hexdigest()


@app.template_global()
def audio_url(texto: str) -> str:
    """Ruta web del mp3 pregrabado de `texto` (japonés), o '' si no existe.
    Los mp3 los genera scripts/generar_audio.py con esta misma clave y se
    commitean; el kiosko debe sonar offline tras un git pull."""
    if not (texto or "").strip():
        return ""
    nombre = _audio_clave(texto) + ".mp3"
    if os.path.exists(os.path.join(_AUDIO_JP_DIR, nombre)):
        return "/static/audio/jp/" + nombre
    return ""


def _temario_unidades(kind):
    """Unidades del temario para `kind` ('vocabulario' | 'gramatica') + una fila
    'extra' con lo que Laura haya metido en sesiones y no esté en el temario.
    Cada ítem trae su estado ('aprendida' | 'en_curso' | 'nueva') y cada unidad
    su progreso."""
    db_rows = (brain.jap_memory.gram_rows() if kind == "gramatica"
               else brain.jap_memory.vocab_rows())

    # Estado del ítem: fuente única en JapaneseMemory.estado_item (Fase 07). La
    # página conserva su vocabulario propio ('aprendida'/'en_curso'/'nueva').
    _MAP = {"sabido": "aprendida", "en_progreso": "en_curso", "nuevo": "nueva"}
    _jps = {str(e.get("jp") or "").strip()
            for u in CURRICULUM for e in u.get("items", [])
            if e.get("kind") == kind and str(e.get("jp") or "").strip()}
    _jps |= set(db_rows)
    _estados = brain.jap_memory.estado_items_bulk((jp, kind) for jp in _jps)
    _norm = "gramatica" if kind == "gramatica" else "vocabulario"

    def estado(jp):
        return _MAP[_estados.get((jp, _norm), "nuevo")]

    # El temario es exactamente el N5 (Fase 04): se renderiza tal cual sale de
    # CURRICULUM, sin selector de nivel ni arrastre N5→N4→N3.
    unidades, vistos = [], set()
    for u in CURRICULUM:
        items = []
        for e in u.get("items", []):
            # los kanji entran como kind 'vocabulario' pero tienen su propia página
            if e.get("kind") != kind or (kind == "vocabulario" and e.get("tipo") == "kanji"):
                continue
            jp = str(e.get("jp") or "").strip()
            if not jp or jp in vistos:
                continue
            vistos.add(jp)
            reading = (e.get("reading") or "").strip()
            items.append({
                "jp": jp,
                "reading": reading if reading and reading != jp else "",
                "romaji": romaji(reading or jp),
                "meaning": (e.get("meaning") or "").strip(),
                "tipo": (e.get("tipo") or "").strip(),
                "ejemplo": (e.get("ejemplo") or "").strip(),
                "literal": (e.get("literal") or "").strip(),
                "uso": (e.get("uso") or "").strip(),
                "estado": estado(jp),
            })
        if items:
            unidades.append({"id": u["id"], "nombre": u.get("nombre", "N5"),
                             "items": items})

    _mean_key = "description" if kind == "gramatica" else "meaning"
    extra = [{
        "jp": jp,
        "reading": "",
        "romaji": romaji(jp),
        "meaning": (r[_mean_key] or "").strip(),
        "tipo": "" if kind == "gramatica" else (r["type"] or "").strip(),
        "ejemplo": "", "literal": "", "uso": "",
        "estado": estado(jp),
    } for jp, r in db_rows.items()
        if jp not in vistos and (kind == "gramatica" or r["type"] != "kanji")]
    if extra:
        unidades.append({"id": "_extra", "nombre": _TEMARIO_EXTRA[kind],
                         "items": extra})

    for u in unidades:
        u["total"] = len(u["items"])
        u["hechas"] = sum(1 for it in u["items"] if it["estado"] == "aprendida")
        u["pct"] = round(u["hechas"] * 100 / u["total"]) if u["total"] else 0
    return unidades


def _render_temario(kind):
    return render_template("japones_temario.html", kind=kind,
                           titulo=_TEMARIO_TITULOS[kind],
                           unidades=_temario_unidades(kind))


def _completar_item(kind, jp):
    e = next((it for u in CURRICULUM for it in u.get("items", [])
              if it.get("kind") == kind and str(it.get("jp") or "").strip() == jp), {}) or {}
    brain.jap_memory.marcar_completo(
        jp, kind,
        reading=(e.get("reading") or "").strip() or jp,
        meaning=(e.get("meaning") or "").strip(),
        tipo=(e.get("tipo") or "").strip() or kind,
    )


def _completar_unidad(kind, uid):
    curr = {str(e.get("jp") or "").strip()
            for u in CURRICULUM for e in u.get("items", []) if e.get("kind") == kind}
    if uid == "_extra":
        rows = brain.jap_memory.gram_rows() if kind == "gramatica" else brain.jap_memory.vocab_rows()
        objetivo = [(jp, {}) for jp in rows if jp not in curr]
    else:
        u = next((x for x in CURRICULUM if x["id"] == uid), None)
        if not u:
            return 0
        objetivo = [(str(e.get("jp") or "").strip(), e) for e in u.get("items", [])
                    if e.get("kind") == kind and str(e.get("jp") or "").strip()]
    for jp, e in objetivo:
        brain.jap_memory.marcar_completo(
            jp, kind,
            reading=(e.get("reading") or "").strip() or jp,
            meaning=(e.get("meaning") or "").strip(),
            tipo=(e.get("tipo") or "").strip() or kind,
        )
    return len(objetivo)


@app.route("/japones/vocabulario")
@login_requerido
def japones_vocabulario():
    return _render_temario("vocabulario")


@app.route("/japones/gramatica")
@login_requerido
def japones_gramatica():
    return _render_temario("gramatica")


def _vocab_items_unidad(uid):
    """(nombre, [ítems]) de vocabulario (no kanji) de una unidad del temario por
    su `id`. nombre None si la unidad no existe. Cada ítem: jp/reading/meaning/
    ejemplo."""
    u = next((x for x in CURRICULUM if x.get("id") == uid), None)
    if not u:
        return None, []
    items, vistos = [], set()
    for e in u.get("items", []):
        if e.get("kind") != "vocabulario" or e.get("tipo") == "kanji":
            continue
        jp = str(e.get("jp") or "").strip()
        if not jp or jp in vistos:
            continue
        vistos.add(jp)
        items.append({
            "jp": jp,
            "reading": (e.get("reading") or "").strip(),
            "meaning": (e.get("meaning") or "").strip(),
            "ejemplo": (e.get("ejemplo") or "").strip(),
        })
    return u.get("nombre", "N5"), items


@app.route("/japones/vocabulario/practicar", methods=["GET", "POST"])
@login_requerido
def japones_vocabulario_practicar():
    """Práctica SRS de vocabulario por lección (Fase 12). Calcada de
    /japones/kanjis/practicar: autocalificación -> review(id, q, 'vocabulario'),
    siguiente ítem por get_due_items(kind='vocabulario') filtrado a la unidad."""
    uid = (request.values.get("unidad") or "").strip()
    nombre, items = _vocab_items_unidad(uid)
    if nombre is None:
        return redirect(url_for("japones_vocabulario"))
    por_jp = {it["jp"]: it for it in items}

    if request.method == "POST":
        jp = (request.form.get("word") or "").strip()
        try:
            quality = int(request.form.get("quality", 3))
        except ValueError:
            quality = 3
        quality = max(0, min(5, quality))
        it = por_jp.get(jp)
        if it:
            item_id = brain.jap_memory.get_item_id(jp, "vocabulario")
            if item_id is None:
                brain.jap_memory.add_item(
                    "vocabulario", jp,
                    reading=it["reading"], meaning=it["meaning"], tipo="vocabulario",
                )
                item_id = brain.jap_memory.get_item_id(jp, "vocabulario")
            if item_id is not None:
                brain.jap_memory.review(item_id, quality, "vocabulario")
        return redirect(url_for("japones_vocabulario_practicar", unidad=uid))

    # GET: siguiente ítem de la unidad — vencidos primero, luego nunca practicado
    due = [d for d in brain.jap_memory.get_due_items(limit=500, kind="vocabulario")
           if d["jp"] in por_jp]
    rows = brain.jap_memory.vocab_rows()
    nuevos = [jp for jp in por_jp
              if jp not in rows or (rows[jp].get("reps") or 0) == 0]

    if due:
        jp, reps = due[0]["jp"], (due[0].get("reps") or 0)
    elif nuevos:
        jp, reps = random.choice(nuevos), 0
    else:
        return render_template("japones_vocab_practica.html", unidad=uid,
                               unidad_nombre=nombre, pendientes=0,
                               al_dia=True, v=None)

    it = por_jp[jp]
    # Alterna el sentido de forma estable por paridad de reps: par -> ES→JP
    # (muestra el significado, pide el japonés), impar -> JP→ES.
    sentido = "es_jp" if reps % 2 == 0 else "jp_es"
    reading = it["reading"] if it["reading"] and it["reading"] != jp else ""
    v = {
        "jp": jp,
        "reading": reading,
        "meaning": it["meaning"],
        "ejemplo": it["ejemplo"],
        "sentido": sentido,
        "pregunta": it["meaning"] if sentido == "es_jp" else jp,
        "respuesta": jp if sentido == "es_jp" else it["meaning"],
    }
    return render_template("japones_vocab_practica.html", unidad=uid,
                           unidad_nombre=nombre, pendientes=len(due),
                           al_dia=False, v=v)


_GRAM_TILDE = "〜～"  # 〜 ～ : marcan "se engancha a una raíz", no forman parte del hueco


def _gram_items_unidad(uid):
    """(nombre, [ítems]) de gramática de una unidad del temario por su `id`.
    nombre None si la unidad no existe. Cada ítem: jp/meaning/ejemplo/literal/uso."""
    u = next((x for x in CURRICULUM if x.get("id") == uid), None)
    if not u:
        return None, []
    items, vistos = [], set()
    for e in u.get("items", []):
        if e.get("kind") != "gramatica":
            continue
        jp = str(e.get("jp") or "").strip()
        if not jp or jp in vistos:
            continue
        vistos.add(jp)
        items.append({
            "jp": jp,
            "meaning": (e.get("meaning") or "").strip(),
            "ejemplo": (e.get("ejemplo") or "").strip(),
            "literal": (e.get("literal") or "").strip(),
            "uso": (e.get("uso") or "").strip(),
        })
    return u.get("nombre", "N5"), items


def _gram_ejercicio(it):
    """Ejercicio de hueco a partir del `ejemplo`. Si el patrón (sin la tilde ～)
    aparece literal y entero en la frase, se tapa con ＿＿＿ y la respuesta es ese
    fragmento. Si no encaja limpiamente (patrón con hueco interno, forma que no
    figura tal cual), se muestra `meaning` + `literal` y se pide el patrón `jp`."""
    jp, ej = it["jp"], it["ejemplo"]
    core = jp.strip(_GRAM_TILDE)
    if core and ej and not any(t in core for t in _GRAM_TILDE) and core in ej:
        return {"modo": "hueco", "pregunta": ej.replace(core, "＿＿＿", 1),
                "respuesta": core, "patron": jp}
    return {"modo": "patron",
            "pregunta": it["meaning"] + (" — " + it["literal"] if it["literal"] else ""),
            "respuesta": jp, "patron": jp}


@app.route("/japones/gramatica/practicar", methods=["GET", "POST"])
@login_requerido
def japones_gramatica_practicar():
    """Práctica SRS de gramática por lección (Fase 13). Gemela de
    /japones/vocabulario/practicar: autocalificación -> review(id, q, 'gramatica'),
    siguiente ítem por get_due_items(kind='gramatica') filtrado a la unidad. El
    ejercicio es la frase-ejemplo con el patrón tapado (hueco)."""
    uid = (request.values.get("unidad") or "").strip()
    nombre, items = _gram_items_unidad(uid)
    if nombre is None:
        return redirect(url_for("japones_gramatica"))
    por_jp = {it["jp"]: it for it in items}

    if request.method == "POST":
        jp = (request.form.get("word") or "").strip()
        try:
            quality = int(request.form.get("quality", 3))
        except ValueError:
            quality = 3
        quality = max(0, min(5, quality))
        it = por_jp.get(jp)
        if it:
            item_id = brain.jap_memory.get_item_id(jp, "gramatica")
            if item_id is None:
                brain.jap_memory.add_item("gramatica", jp, meaning=it["meaning"])
                item_id = brain.jap_memory.get_item_id(jp, "gramatica")
            if item_id is not None:
                brain.jap_memory.review(item_id, quality, "gramatica")
        return redirect(url_for("japones_gramatica_practicar", unidad=uid))

    # GET: siguiente ítem de la unidad — vencidos primero, luego nunca practicado
    due = [d for d in brain.jap_memory.get_due_items(limit=500, kind="gramatica")
           if d["jp"] in por_jp]
    rows = brain.jap_memory.gram_rows()
    nuevos = [jp for jp in por_jp
              if jp not in rows or (rows[jp].get("reps") or 0) == 0]

    if due:
        jp = due[0]["jp"]
    elif nuevos:
        jp = random.choice(nuevos)
    else:
        return render_template("japones_gram_practica.html", unidad=uid,
                               unidad_nombre=nombre, pendientes=0,
                               al_dia=True, v=None)

    it = por_jp[jp]
    ej = _gram_ejercicio(it)
    v = {
        "jp": jp,
        "meaning": it["meaning"],
        "literal": it["literal"],
        "uso": it["uso"],
        "ejemplo": it["ejemplo"],
        "modo": ej["modo"],
        "pregunta": ej["pregunta"],
        "respuesta": ej["respuesta"],
        "patron": ej["patron"],
    }
    return render_template("japones_gram_practica.html", unidad=uid,
                           unidad_nombre=nombre, pendientes=len(due),
                           al_dia=False, v=v)


@app.route("/japones/boletin")
@login_requerido
def japones_boletin():
    # Boletín can-do (Fase 11): solo lectura. Contexto en JapaneseMemory.boletin.
    return render_template("japones_boletin.html", **brain.jap_memory.boletin())


@app.route("/japones/vocabulario/completar", methods=["POST"])
@login_requerido
def japones_vocabulario_completar():
    jp = (request.form.get("word") or "").strip()
    if jp:
        _completar_item("vocabulario", jp)
    return redirect(url_for("japones_vocabulario"))


@app.route("/japones/gramatica/completar", methods=["POST"])
@login_requerido
def japones_gramatica_completar():
    jp = (request.form.get("word") or "").strip()
    if jp:
        _completar_item("gramatica", jp)
    return redirect(url_for("japones_gramatica"))


@app.route("/japones/vocabulario/completar-unidad", methods=["POST"])
@login_requerido
def japones_vocabulario_completar_unidad():
    n = _completar_unidad("vocabulario", (request.form.get("unidad") or "").strip())
    flash(f"✅ Unidad marcada como aprendida ({n} palabras)", "success")
    return redirect(url_for("japones_vocabulario"))


@app.route("/japones/gramatica/completar-unidad", methods=["POST"])
@login_requerido
def japones_gramatica_completar_unidad():
    n = _completar_unidad("gramatica", (request.form.get("unidad") or "").strip())
    flash(f"✅ Unidad marcada como aprendida ({n} puntos)", "success")
    return redirect(url_for("japones_gramatica"))


@app.route("/japones/kanjis/practicar", methods=["GET", "POST"])
@login_requerido
def japones_kanjis_practicar():
    """Práctica SRS de kanji, opcionalmente acotada a una categoría (?categoria=).
    Gemela de /japones/vocabulario/practicar (que filtra por unidad): sin categoría
    (o 'all') practica todo el N5, como antes."""
    cat = (request.values.get("categoria") or "").strip()
    pool = [k for k in KANJI_N5 if cat in ("", "all") or k.get("categoria") == cat]
    if cat not in ("", "all") and not pool:
        return redirect(url_for("japones_kanjis"))
    jps_pool = {k.get("jp") for k in pool}
    cat_nombre = (pool[0].get("categoria_nombre", cat).split("—")[-1].strip()
                  if cat not in ("", "all") and pool else "")

    if request.method == "POST":
        kanji = (request.form.get("kanji") or "").strip()
        try:
            quality = int(request.form.get("quality", 2))
        except ValueError:
            quality = 2
        quality = max(0, min(5, quality))
        item = next((k for k in pool if k.get("jp") == kanji), None)
        if item:
            item_id = brain.jap_memory.get_item_id(kanji, "kanji")
            if item_id is None:
                brain.jap_memory.add_item(
                    "kanji", kanji,
                    reading=(item.get("reading") or item.get("kun") or item.get("on") or "").strip(),
                    meaning=(item.get("meaning") or "").strip(),
                    tipo="kanji",
                )
                item_id = brain.jap_memory.get_item_id(kanji, "kanji")
            if item_id is not None:
                brain.jap_memory.review(item_id, quality, "kanji")
        return redirect(url_for("japones_kanjis_practicar", categoria=cat or None))

    # GET: siguiente kanji por SRS (vencidos primero, luego nunca practicados)
    due = [d["jp"] for d in brain.jap_memory.get_due_items(limit=500, kind="kanji")
           if d["jp"] in jps_pool]
    practicados = brain.jap_memory.get_practiced_set("kanji")
    nuevos = [k["jp"] for k in pool if k.get("jp") not in practicados]

    if due:
        jp = due[0]
    elif nuevos:
        jp = random.choice(nuevos)
    else:
        return render_template("japones_kanji_practica.html", k=None,
                               categoria=cat, categoria_nombre=cat_nombre,
                               pendientes=0, al_dia=True)

    item = next(k for k in pool if k.get("jp") == jp)
    k = dict(item)
    k["mnemo"] = brain.jap_memory.get_mnemos().get(jp) or item.get("mnemo", "")
    return render_template("japones_kanji_practica.html", k=k,
                           categoria=cat, categoria_nombre=cat_nombre,
                           pendientes=len(due) + len(nuevos), al_dia=False)


@app.route("/japones/kanjis/mnemo", methods=["POST"])
@login_requerido
def japones_kanjis_mnemo():
    kanji = (request.form.get("kanji") or "").strip()
    texto = request.form.get("mnemo") or ""
    if not kanji or not any(k.get("jp") == kanji for k in KANJI_N5):
        flash("❌ Ese kanji no existe en el proyecto", "error")
        return redirect(url_for("japones_kanjis"))
    brain.jap_memory.set_mnemo(kanji, texto)
    # sin flash ni ?kanji=: no queremos popup de confirmación al volver
    return redirect(url_for("japones_kanjis"))


@app.route("/japones/kanjis/completar", methods=["POST"])
@login_requerido
def japones_kanjis_completar():
    kanji = (request.form.get("kanji") or "").strip()
    item = next((k for k in KANJI_N5 if k.get("jp") == kanji), None)
    if not item:
        flash("❌ Ese kanji no existe en el proyecto", "error")
        return redirect(url_for("japones_kanjis"))
    brain.jap_memory.marcar_completo(
        kanji, "kanji",
        reading=(item.get("reading") or item.get("kun") or item.get("on") or "").strip(),
        meaning=(item.get("meaning") or "").strip(),
        tipo="kanji",
    )
    return redirect(url_for("japones_kanjis"))


@app.route("/japones/kanjis/completar-categoria", methods=["POST"])
@login_requerido
def japones_kanjis_completar_categoria():
    cat = (request.form.get("categoria") or "").strip()
    objetivo = [k for k in KANJI_N5
                if cat in ("all", "") or k.get("categoria") == cat]
    for item in objetivo:
        brain.jap_memory.marcar_completo(
            item["jp"], "kanji",
            reading=(item.get("reading") or item.get("kun") or item.get("on") or "").strip(),
            meaning=(item.get("meaning") or "").strip(),
            tipo="kanji",
        )
    flash(f"✅ {len(objetivo)} kanji marcados como dominados", "success")
    return redirect(url_for("japones_kanjis"))


# ── Vocabulario / kanji / gramática: alta y mantenimiento manual desde el panel ─
#
# 5 operaciones × 3 tipos. El SQL vive una sola vez en core/japanese_items.py;
# aquí se registran las 15 URLs (sin cambio de ruta) y cada vista solo hace
# flash + redirect. Rutas: /japones/<tipo>/{añadir,borrar/<id>,borrar-todo,
# resetear-srs/<id>,marcar-aprendido/<id>}, tipo ∈ vocabulario|kanji|gramatica.

_ITEM_MSGS = {
    "vocabulario": {
        "add_ok": "✅ '{jp}' añadido al vocabulario",
        "add_err": "❌ La palabra en japonés y el significado son obligatorios",
        "del": "✅ Palabra borrada",
        "del_all": "✅ Todo el vocabulario borrado",
        "reset": "✅ SRS reseteado",
        "master": "✅ Marcada como aprendida",
    },
    "kanji": {
        "add_ok": "✅ '{jp}' añadido a kanjis",
        "add_err": "❌ El kanji y su significado son obligatorios",
        "del": "✅ Kanji borrado",
        "del_all": "✅ Todos los kanjis borrados",
        "reset": "✅ SRS de kanji reseteado",
        "master": "✅ Kanji marcado como aprendido",
    },
    "gramatica": {
        "add_ok": "✅ '{jp}' añadido a gramática",
        "add_err": "❌ El punto gramatical y la descripción son obligatorios",
        "del": "✅ Punto gramatical borrado",
        "del_all": "✅ Toda la gramática borrada",
        "reset": "✅ SRS de gramática reseteado",
        "master": "✅ Marcada como aprendida",
    },
}


def _wire_item_routes(kind):
    msgs = _ITEM_MSGS[kind]

    @login_requerido
    def añadir():
        jp = request.form.get("jp", "").strip()
        es = request.form.get("es", "").strip()
        if japanese_items.añadir(brain.jap_memory, kind, jp, es):
            flash(msgs["add_ok"].format(jp=jp), "success")
        else:
            flash(msgs["add_err"], "error")
        return redirect(url_for("japones"))

    @login_requerido
    def borrar(item_id):
        japanese_items.borrar(brain.jap_memory, kind, item_id)
        flash(msgs["del"], "success")
        return redirect(url_for("japones"))

    @login_requerido
    def borrar_todo():
        japanese_items.borrar_todo(brain.jap_memory, kind)
        flash(msgs["del_all"], "success")
        return redirect(url_for("japones"))

    @login_requerido
    def resetear_srs(item_id):
        japanese_items.resetear_srs(brain.jap_memory, kind, item_id)
        flash(msgs["reset"], "success")
        return redirect(url_for("japones"))

    @login_requerido
    def marcar_aprendido(item_id):
        japanese_items.marcar_aprendido(brain.jap_memory, kind, item_id)
        flash(msgs["master"], "success")
        return redirect(url_for("japones"))

    base = f"/japones/{kind}"
    app.add_url_rule(f"{base}/añadir", f"japones_item_{kind}_add",
                     añadir, methods=["POST"])
    app.add_url_rule(f"{base}/borrar/<int:item_id>", f"japones_item_{kind}_del",
                     borrar, methods=["POST"])
    app.add_url_rule(f"{base}/borrar-todo", f"japones_item_{kind}_del_all",
                     borrar_todo, methods=["POST"])
    app.add_url_rule(f"{base}/resetear-srs/<int:item_id>",
                     f"japones_item_{kind}_reset", resetear_srs, methods=["POST"])
    app.add_url_rule(f"{base}/marcar-aprendido/<int:item_id>",
                     f"japones_item_{kind}_master", marcar_aprendido,
                     methods=["POST"])


for _k in japanese_items.KINDS:
    _wire_item_routes(_k)

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