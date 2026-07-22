#!/usr/bin/env python3
"""
simulate_sensei.py — Simulación completa del Profesor Japonés (Kaitosan)

Ejecuta una sesión de práctica con el ProfesorJapones sin arrancar Flask:
  1. Muestra el estado de la BD y el contexto antes de la sesión.
  2. Simula una conversación (turnos predefinidos o interactivos).
  3. Cierra la sesión: el LLM ligero extrae el JSON de resumen y lo guarda en BD.
  4. Muestra lo que quedó guardado en la BD.
  5. Muestra cómo iniciará la PRÓXIMA sesión (contexto regenerado).

Uso:
  python simulate_sensei.py                  # turnos predefinidos
  python simulate_sensei.py --interactive    # tú escribes cada turno
  python simulate_sensei.py --clean          # borra datos japoneses y relanza
"""

import sys
import os
import argparse
import sqlite3
import time

# Forzar UTF-8 en la salida estándar (necesario en Windows con cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── PATH: añadir raíz del proyecto ────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Cargar .env antes de importar config (GROQ_API_KEY, etc.)
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ── Crear directorio de datos si no existe ────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "kaito.db")

# ── Imports del proyecto ──────────────────────────────────────────────────────
from core.memory import Memory
from core.japanese_memory import JapaneseMemory
from ai.fallback_provider import FallbackProvider
from ai.sensei.profesor import ProfesorJapones

# ── Consola ───────────────────────────────────────────────────────────────────
W = 72
SEP_DOBLE = "═" * W
SEP_SIMPLE = "─" * W


def titulo(texto: str):
    print(f"\n{SEP_DOBLE}")
    print(f"  {texto}")
    print(SEP_DOBLE)


def seccion(texto: str):
    print(f"\n{SEP_SIMPLE}")
    print(f"  {texto}")
    print(SEP_SIMPLE)


def linea(texto: str = ""):
    print(f"  {texto}")


# ── Mock SocketIO (evita depender de Flask) ───────────────────────────────────
class MockSocketIO:
    def emit(self, event: str, data=None):
        print(f"  [socket] {event} → {data}")

    def start_background_task(self, fn, *args, **kwargs):
        fn(*args, **kwargs)


# ── Turnos predefinidos (simulan a Laura) ─────────────────────────────────────
# 5 turnos: un error (duda), una corrección (bien), un error grave (mal),
# una corrección + repaso (bien), y despedida. Cubre las tres ramas del SM-2
# con el mínimo de tokens para no exceder 6000 tpm en el modelo principal.
TURNOS_PREDEFINIDOS = [
    # Error adj-い: Laura añade い de más → duda
    "このレストランはたかいくないです",   # correcto: たかくないです
    # Corrección aceptada → bien
    "わかった、たかくないです。ありがとう！",
    # Error grave ます: Laura conjuga る動詞 como si fuera う → mal
    "食べるのます形は食べいます？",      # correcto: 食べます
    # Corrección + repaso (repite たかくない visto antes) → bien
    "食べます！それと、さっきのたかくない、もう一度言える？",
    # Petición fuera del temario (Fase 8): el profesor debe enseñarlo, no redirigir
    "Oye, ¿cómo se dice mariposa en japonés? Me encantaría saberlo",
    # Producción del ítem pedido por Laura
    "Ah, entonces se dice 【ちょうちょ】, ¿verdad?",
    # Despedida
    "Creo que ya es suficiente por hoy, gracias",
]

# Pausa entre turnos para no superar 6000 tpm (el contexto crece cada turno)
SLEEP_ENTRE_TURNOS = 12  # segundos


# ── Helpers de visualización BD ──────────────────────────────────────────────

def mostrar_bd_japonesa(jap_memory: JapaneseMemory, titulo_sec: str):
    seccion(titulo_sec)

    perfil = jap_memory.resumen_perfil()

    linea(f"📊  Ítems en cola de repaso (SRS hoy): {perfil['due_count']}")

    if perfil["vocab_by_status"]:
        linea("📚  Vocabulario por estado:")
        for estado, n in sorted(perfil["vocab_by_status"].items()):
            linea(f"    • {estado:<12} {n}")
    else:
        linea("📚  Sin vocabulario registrado")

    if perfil["last_session_summary"]:
        linea(f"\n📝  Última sesión (resumen guardado):")
        for frag in _wrap(perfil["last_session_summary"], 60):
            linea(f"    {frag}")
    else:
        linea("\n📝  Sin sesiones previas con resumen")

    if perfil["weak_points"]:
        linea("\n⚠️   Puntos débiles:")
        for wp in perfil["weak_points"]:
            linea(f"    • {wp['word']}  ({wp['errors']} errores)")

    due_v = jap_memory.get_due_items(8, kind="vocabulario")
    due_g = jap_memory.get_due_items(5, kind="gramatica")

    if due_v:
        linea(f"\n🔄  Vocabulario para repasar ({len(due_v)} ítems):")
        for it in due_v:
            jp = it.get("jp") or it.get("word", "")
            meaning = it.get("meaning", "")
            status = it.get("status", "")
            linea(f"    • 【{jp}】  {meaning}  [{status}]")
    if due_g:
        linea(f"\n🔄  Gramática para repasar ({len(due_g)} ítems):")
        for it in due_g:
            jp = it.get("jp") or it.get("grammar_point", "")
            meaning = it.get("meaning") or it.get("description", "")
            linea(f"    • 【{jp}】  {meaning}")


def mostrar_contexto_profesor(profesor: ProfesorJapones, etiqueta: str):
    seccion(etiqueta)
    recuerdas, foco = profesor._montar_estado()

    linea("── [RECUERDAS DE LAURA] ──────────────────────────────────────")
    for l in recuerdas.splitlines():
        linea(l)

    linea("\n── [FOCO DE HOY] ────────────────────────────────────────────")
    for l in foco.splitlines():
        linea(l)


def mostrar_sesiones_bd(jap_memory: JapaneseMemory):
    seccion("SESIONES GUARDADAS EN BD  (japanese_sessions)")
    with jap_memory._conectar() as conn:
        rows = conn.execute(
            """SELECT id, started_at, ended_at, words_learned,
                      grammar_practiced, errors_noted, summary
               FROM japanese_sessions ORDER BY id DESC LIMIT 8"""
        ).fetchall()

    if not rows:
        linea("Sin sesiones registradas.")
        return

    for r in rows:
        sid, start, end, words, gram, errors, summary = r
        linea(f"\n  Sesión #{sid}")
        linea(f"    Inicio:              {start}")
        linea(f"    Fin:                 {end or '(abierta)'}")
        linea(f"    Palabras aprendidas: {words or 0}")
        linea(f"    Gramática practicada:{gram or '—'}")
        linea(f"    Errores notados:     {errors or '—'}")
        linea(f"    Resumen:")
        if summary:
            for frag in _wrap(summary, 58):
                linea(f"      {frag}")
        else:
            linea("      (sin resumen)")


def mostrar_vocabulario_bd(jap_memory: JapaneseMemory):
    seccion("VOCABULARIO EN BD  (japanese_vocabulary)")
    with jap_memory._conectar() as conn:
        rows = conn.execute(
            """SELECT word, meaning, status, reps, ease_factor,
                      interval_days, next_review, times_correct, errors
               FROM japanese_vocabulary ORDER BY id"""
        ).fetchall()

    if not rows:
        linea("Sin vocabulario registrado.")
        return

    header = f"  {'Palabra':<14} {'Significado':<18} {'Estado':<11} " \
             f"{'Reps':>4} {'EF':>5} {'Intv':>5} {'Próx.Repaso':<13} " \
             f"{'OK':>3} {'Err':>4}"
    print(header)
    print("  " + "─" * (len(header) - 2))
    for r in rows:
        word, meaning, status, reps, ef, intv, nxt, ok, err = r
        meaning = (meaning or "")[:17]
        print(f"  {word:<14} {meaning:<18} {(status or ''):<11} "
              f"{(reps or 0):>4} {(ef or 2.5):>5.2f} {(intv or 0):>5} "
              f"{(nxt or ''):13} {(ok or 0):>3} {(err or 0):>4}")


def mostrar_gramatica_bd(jap_memory: JapaneseMemory):
    seccion("GRAMÁTICA EN BD  (japanese_grammar)")
    with jap_memory._conectar() as conn:
        rows = conn.execute(
            """SELECT grammar_point, description, mastery, reps,
                      interval_days, next_review, times_correct, errors
               FROM japanese_grammar ORDER BY id"""
        ).fetchall()

    if not rows:
        linea("Sin gramática registrada.")
        return

    for r in rows:
        gp, desc, mastery, reps, intv, nxt, ok, err = r
        linea(f"  【{gp}】  {desc or ''}")
        linea(f"    dominio={mastery or 0:.0f}%  reps={reps or 0}  "
              f"interval={intv or 0}d  próximo={nxt or '—'}  "
              f"aciertos={ok or 0}  errores={err or 0}")


def mostrar_transcript(profesor: ProfesorJapones):
    seccion("TRANSCRIPT COMPLETO (lo que ve el LLM extractor)")
    transcript = profesor._construir_transcript()
    if not transcript:
        linea("(sin mensajes)")
        return
    for l in transcript.splitlines():
        print(f"  {l}")


# ── Utilidad ──────────────────────────────────────────────────────────────────

def _wrap(texto: str, ancho: int) -> list:
    """Parte texto largo en líneas de `ancho` caracteres máx."""
    palabras = texto.split()
    lineas, actual = [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > ancho:
            if actual:
                lineas.append(actual)
            actual = p
        else:
            actual = (actual + " " + p).strip()
    if actual:
        lineas.append(actual)
    return lineas or [""]


def limpiar_datos_japones():
    """Borra las tablas japonesas para empezar desde cero."""
    if not os.path.exists(DB_PATH):
        print("  No existe la BD, nada que limpiar.")
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            DELETE FROM japanese_vocabulary;
            DELETE FROM japanese_grammar;
            DELETE FROM japanese_sessions;
        """)
    print("  🗑️  Datos japoneses borrados (tablas generales intactas).")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Simula una sesión completa con el Profesor Japonés de Kaitosan"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interactivo: escribe tú cada mensaje de Laura"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Borra los datos japoneses de la BD antes de ejecutar"
    )
    args = parser.parse_args()

    titulo("SIMULACIÓN COMPLETA — PROFESOR JAPONÉS  (Kaitosan)")
    from datetime import datetime
    linea(f"Fecha/Hora : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linea(f"BD         : {DB_PATH}")
    linea(f"Modo       : {'interactivo' if args.interactive else 'automático (turnos predefinidos)'}")

    if args.clean:
        seccion("LIMPIANDO DATOS JAPONESES")
        limpiar_datos_japones()

    # ── Inicializar componentes ──────────────────────────────────────────────
    seccion("INICIALIZANDO COMPONENTES")
    memory = Memory()
    jap_memory = JapaneseMemory(DB_PATH)
    provider = FallbackProvider()   # llama-3.3-70b; también actúa como extractor con strict=True
    socketio_mock = MockSocketIO()

    profesor = ProfesorJapones(
        jap_memory=jap_memory,
        provider=provider,
        memory=memory,
        socketio=socketio_mock,
    )
    linea("✅ Todos los componentes listos")

    # ── Estado de la BD antes de la sesión ──────────────────────────────────
    mostrar_bd_japonesa(jap_memory, "ESTADO DE LA BD  —  ANTES DE LA SESIÓN")

    # ── Contexto que verá el profesor al iniciar ─────────────────────────────
    mostrar_contexto_profesor(profesor, "CONTEXTO QUE VE EL PROFESOR AL INICIO")

    # ── Activar modo sensei ──────────────────────────────────────────────────
    seccion("ACTIVANDO MODO SENSEI")
    profesor.entrar()
    linea(f"Session ID en japanese_sessions: {profesor.session_id}")
    linea("Timer de inactividad (20 min) activo — se cancela al salir")

    # ── Conversación ─────────────────────────────────────────────────────────
    seccion("CONVERSACIÓN")

    if args.interactive:
        linea("Escribe el mensaje de Laura en cada turno.")
        linea("Escribe  'salir'  para terminar la sesión.\n")
        turno = 1
        while True:
            try:
                msg = input(f"  [Turno {turno}] 👤 Laura: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not msg:
                continue
            if msg.lower() in ("salir", "exit", "quit", "bye"):
                break
            print(f"  [Turno {turno}] 🎌 Profesor: ", end="", flush=True)
            respuesta = profesor.responder_turno(msg)
            print(respuesta)
            print()
            turno += 1
    else:
        total = len(TURNOS_PREDEFINIDOS)
        for i, msg in enumerate(TURNOS_PREDEFINIDOS, 1):
            linea(f"[Turno {i}/{total}]")
            linea(f"  👤 Laura:    {msg}")
            respuesta = profesor.responder_turno(msg)
            # Mostrar respuesta (recortada si es muy larga)
            if len(respuesta) > 450:
                preview = respuesta[:450] + " … [truncado]"
            else:
                preview = respuesta
            linea(f"  🎌 Profesor: {preview}")
            print()
            if i < total:
                linea(f"  ⏳ Esperando {SLEEP_ENTRE_TURNOS}s (rate limit)…")
                time.sleep(SLEEP_ENTRE_TURNOS)

    # ── Transcript antes de cerrar ────────────────────────────────────────────
    mostrar_transcript(profesor)

    # ── Cerrar sesión → extracción en dos niveles ───────────────────────────
    seccion("CERRANDO SESIÓN  →  EXTRACCIÓN EN DOS NIVELES")
    linea("Nivel 1: resumen en texto libre con el provider principal (cualquier modelo disponible).")
    linea("  Sirve de continuidad mínima si la extracción completa falla.")
    linea("Nivel 2: extracción JSON completa (strict=True, solo modelo principal):")
    linea("  • summary     — 2-3 frases sobre qué se trabajó")
    linea("  • reviewed[]  — cada ítem intentado: bien / duda / mal")
    linea("  • new_items[] — ítems introducidos por primera vez")
    linea("")
    linea("Llamando al LLM… (puede tardar unos segundos)")

    # salir() cancela el timer internamente y llama a cerrar_sesion_y_extraer()
    profesor.salir()   # ← aquí suceden la extracción y el guardado en BD

    # ── Resultados guardados en BD ────────────────────────────────────────────
    mostrar_sesiones_bd(jap_memory)
    mostrar_vocabulario_bd(jap_memory)
    mostrar_gramatica_bd(jap_memory)
    mostrar_bd_japonesa(jap_memory, "ESTADO DE LA BD  —  DESPUÉS DE LA SESIÓN")

    # ── Cómo iniciará la PRÓXIMA sesión ──────────────────────────────────────
    seccion("ASÍ EMPIEZA LA PRÓXIMA SESIÓN  (contexto regenerado desde BD)")
    linea("Se crea una instancia nueva del profesor y se regenera el contexto.")
    linea("Esto es exactamente lo que verá el LLM en su primer turno.\n")

    profesor_siguiente = ProfesorJapones(
        jap_memory=jap_memory,
        provider=provider,
        memory=memory,
        socketio=socketio_mock,
    )
    mostrar_contexto_profesor(
        profesor_siguiente,
        "CONTEXTO PRÓXIMA SESIÓN  —  [RECUERDAS DE LAURA] + [FOCO DE HOY]"
    )

    titulo("FIN DE LA SIMULACIÓN")
    linea("Los datos han quedado guardados en data/kaito.db")
    linea("Para inspeccionar manualmente:")
    linea("  sqlite3 data/kaito.db  \".headers on\"  \".mode column\"")
    linea("  SELECT * FROM japanese_sessions;")
    linea("  SELECT word, meaning, status, next_review FROM japanese_vocabulary;")
    print()


if __name__ == "__main__":
    main()
