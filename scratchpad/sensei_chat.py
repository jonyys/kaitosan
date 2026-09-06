#!/usr/bin/env python3
"""sensei_chat.py — driver de sesiones largas del modo Sensei, sin Flask.

Habla con ProfesorJapones turno a turno contra una COPIA de data/kaito.db
(data/kaito_sim.db). Nunca toca la BD real.

Comandos:
  python scratchpad/sensei_chat.py start [--keep]
      Copia la BD (salvo --keep), abre sesión y guarda el saludo.
  python scratchpad/sensei_chat.py say "<frase de Laura>"
      sleep 30s (ventana TPM de Groq) + un turno. Marca el modelo que respondió
      si NO fue el principal del sensei.
  python scratchpad/sensei_chat.py end
      profesor.salir() (extracción síncrona con MockSocketIO) y vuelca de la
      copia: fila de japanese_sessions, can_do_progreso entero y el vocab tocado.

Estado entre invocaciones: scratchpad/sensei_chat_state.json
"""

import argparse
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from contextlib import redirect_stdout

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))

REAL_DB = os.path.join(ROOT, "data", "kaito.db")
COPY_DB = os.path.join(ROOT, "data", "kaito_sim.db")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensei_chat_state.json")
SLEEP_SAY = 45  # ventana tokens/min de Groq (free tier gpt-oss-120b ~8k/min):
#                 a ~7k tokens por turno hay que espaciar bien más de 30 s

from core.memory import Memory  # noqa: E402
from core.japanese_memory import JapaneseMemory  # noqa: E402
from ai.fallback_provider import FallbackProvider  # noqa: E402
from ai.sensei_provider import SenseiProvider  # noqa: E402  (Gemini turnos + Groq reserva/extractor)
from ai.sensei.profesor import ProfesorJapones  # noqa: E402
from ai.sensei.curriculum import (  # noqa: E402
    CURRICULUM, UMBRAL_UNIDAD_COMPLETA, unidad_actual,
)

_RE_MODEL = re.compile(r"Tokens (\S+):")


class MockSocketIO:
    """Sin Flask. start_background_task corre en primer plano; sleep es no-op
    (el retraso de EXTRACCION_RETRASO_SEG no aplica en simulación)."""

    def emit(self, *a, **k):
        pass

    def start_background_task(self, fn, *a, **k):
        fn(*a, **k)

    def sleep(self, _s):
        pass


def _load_state():
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)


def _save_state(st):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def _build_profesor(db_path, provider="groq"):
    jm = JapaneseMemory(db_path)
    mem = Memory()
    mem.db_path = db_path  # que ni siquiera lea la BD real
    prov = SenseiProvider() if provider == "gemini" else FallbackProvider()
    prof = ProfesorJapones(
        jap_memory=jm, provider=prov, memory=mem, socketio=MockSocketIO(),
    )
    return prof, jm


def _restore(prof, st):
    """Deja la instancia como la dejó el comando anterior, sin abrir sesión."""
    prof.activo = True
    prof.session_id = st["session_id"]
    prof.mensajes = st["mensajes"]
    prof._foco_nuevos = st["foco_nuevos"]
    prof._foco_unidad = next(
        (u for u in CURRICULUM if u["id"] == st["foco_unidad_id"]), None
    )
    try:
        prof._resolver_modelo()  # mantiene el sensei en gpt-oss-120b
    except Exception as e:  # noqa: BLE001
        print(f"  (no se pudo resolver modelo: {e})")


def _run_capturing(fn):
    """Ejecuta fn capturando su stdout: lo re-imprime con sangría y devuelve
    (valor_de_retorno, [modelos que registraron tokens])."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = fn()
    texto = buf.getvalue()
    for line in texto.splitlines():
        print(f"  | {line}")
    return out, _RE_MODEL.findall(texto)


def cmd_start(args):
    if args.keep:
        if not os.path.exists(COPY_DB):
            sys.exit("--keep pero no existe la copia; lanza sin --keep primero.")
        print(f"--keep: se reutiliza {COPY_DB} (parte del estado de la sesión anterior)")
    else:
        shutil.copy2(REAL_DB, COPY_DB)
        print(f"BD copiada: {REAL_DB} -> {COPY_DB}")

    prev_ids = []
    if args.keep and os.path.exists(STATE):
        prev_ids = _load_state().get("sim_session_ids", [])

    provider = "gemini" if args.gemini else "groq"
    prof, jm = _build_profesor(COPY_DB, provider)
    _run_capturing(prof.entrar)
    saludo = prof.saludo_inicial()
    if prof.timer:
        prof.timer.cancel()

    model_sensei = (prof.provider.gemini[0].model_id if provider == "gemini"
                    else prof.provider.groq.model)
    st = {
        "db_path": COPY_DB,
        "session_id": prof.session_id,
        "sim_session_ids": prev_ids + [prof.session_id],
        "provider": provider,
        "model_sensei": model_sensei,
        "mensajes": prof.mensajes,
        "foco_nuevos": prof._foco_nuevos,
        "foco_unidad_id": (prof._foco_unidad or {}).get("id"),
        "turnos": [],
    }
    _save_state(st)

    print(f"\nsession_id   = {prof.session_id}")
    print(f"modelo sensei = {st['model_sensei']}")
    print(f"unidad        = {st['foco_unidad_id']}")
    print(f"ítems nuevos  = {[n['jp'] for n in prof._foco_nuevos]}")
    print(f"\n🎌 Profesor (saludo): {saludo}")


def cmd_say(args):
    st = _load_state()
    if st.get("provider", "groq") != "gemini":
        print(f"⏳ sleep {SLEEP_SAY}s (ventana TPM de Groq)…")
        time.sleep(SLEEP_SAY)

    prof, _ = _build_profesor(st["db_path"], st.get("provider", "groq"))
    _restore(prof, st)

    n = len(st["turnos"]) + 1
    print(f"\n[Turno {n}]  👤 Laura: {args.text}\n")
    buf = io.StringIO()
    with redirect_stdout(buf):
        resp = prof.responder_turno(args.text)
    log = buf.getvalue()
    for line in log.splitlines():
        print(f"  | {line}")
    if prof.timer:
        prof.timer.cancel()

    modelos = _RE_MODEL.findall(log)
    if modelos:                       # Groq imprime "📊 Tokens <modelo>:"
        modelo_turno = modelos[-1]
    elif st.get("provider") == "gemini" and "Gemini falló" not in log:
        modelo_turno = st["model_sensei"]          # Gemini no imprime contador
    else:
        modelo_turno = "reserva/desconocido"
    alt = "" if modelo_turno == st["model_sensei"] else "   ⚠️ NO es el modelo primario"
    print(f"\n🎌 Profesor [{modelo_turno}]{alt}:\n{resp}")

    st["mensajes"] = prof.mensajes
    st["turnos"].append({
        "n": n, "modelo": modelo_turno,
        "laura": args.text, "profesor": resp,
    })
    _save_state(st)


def cmd_end(args):
    st = _load_state()
    prof, jm = _build_profesor(st["db_path"], st.get("provider", "groq"))
    _restore(prof, st)
    sid = st["session_id"]

    print(f"Cerrando sesión {sid} → profesor.salir() (extracción síncrona)\n")
    _run_capturing(prof.salir)
    if prof.timer:
        prof.timer.cancel()

    con = sqlite3.connect(st["db_path"])
    con.row_factory = sqlite3.Row

    print("\n=== japanese_sessions — fila de esta sesión ===")
    r = con.execute("SELECT * FROM japanese_sessions WHERE id = ?", (sid,)).fetchone()
    for k in r.keys():
        print(f"  {k:16} {r[k]}")

    print("\n=== can_do_progreso (entero) ===")
    for r in con.execute("SELECT * FROM can_do_progreso ORDER BY can_do_id"):
        print(f"  {r['can_do_id']:22} {r['estado']:12} "
              f"veces_ok={r['veces_ok']}  ult_sesion={r['ultima_sesion']}")
        if r["nota"]:
            print(f"      nota: {r['nota']}")

    sim_ids = st.get("sim_session_ids", [sid])
    ph = ",".join("?" * len(sim_ids))

    print("\n=== vocab tocado (first_taught_session_id de esta simulación) ===")
    rows = con.execute(
        f"SELECT word, meaning, status, first_taught_session_id "
        f"FROM japanese_vocabulary WHERE first_taught_session_id IN ({ph}) "
        f"ORDER BY id", sim_ids,
    ).fetchall()
    for r in rows or []:
        print(f"  {r['word']:16} {(r['meaning'] or ''):32} "
              f"[{r['status']}] sesión {r['first_taught_session_id']}")
    if not rows:
        print("  (ninguno)")

    print("\n=== grammar (todas las filas) ===")
    rows = con.execute(
        "SELECT grammar_point, description, reps, mastery FROM japanese_grammar "
        "ORDER BY id"
    ).fetchall()
    for r in rows or []:
        print(f"  {r['grammar_point']:18} {r['description'] or ''} "
              f"(reps={r['reps']}, mastery={r['mastery']})")
    if not rows:
        print("  (ninguna)")

    u = unidad_actual(jm)
    frac = jm.fraccion_can_dos(st["foco_unidad_id"])
    print(f"\n=== unidad ===")
    print(f"  foco de la sesión : {st['foco_unidad_id']}  "
          f"(fracción dominada = {frac:.2f} / umbral avance = {UMBRAL_UNIDAD_COMPLETA})")
    print(f"  unidad_actual ahora: {u['id']} — {u['nombre']}")
    print("  → la unidad AVANZÓ" if u["id"] != st["foco_unidad_id"]
          else "  → la unidad NO avanzó todavía")

    con.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("start")
    ps.add_argument("--keep", action="store_true",
                    help="no recopiar la BD: parte del estado de la sesión previa")
    ps.add_argument("--gemini", action="store_true",
                    help="turnos del sensei con Gemini en vez de Groq gpt-oss")
    ps.set_defaults(fn=cmd_start)
    psay = sub.add_parser("say")
    psay.add_argument("text")
    psay.set_defaults(fn=cmd_say)
    pe = sub.add_parser("end")
    pe.set_defaults(fn=cmd_end)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
