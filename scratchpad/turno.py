# -*- coding: utf-8 -*-
import sys, os, io, json, time, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from core.memory import Memory
from core.japanese_memory import JapaneseMemory
from ai.sensei_provider import SenseiProvider
from ai.sensei.profesor import ProfesorJapones

STATE_PATH = "data/_test_dinamico_state.json"
DB_PATH = "data/kaito_test_dinamico.db"


class MockSocketIO:
    def emit(self, *a, **k): pass
    def start_background_task(self, fn, *a, **k): fn(*a, **k)


def _guardar(prof):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": prof.session_id,
            "mensajes": prof.mensajes,
            "nivel_inmersion": prof.nivel_inmersion,
            "ultima_frase_objetivo": prof.ultima_frase_objetivo,
            "foco_nuevos": prof._foco_nuevos,
            "foco_unidad": prof._foco_unidad,
        }, f, ensure_ascii=False)


import base64
mensaje = base64.b64decode(sys.argv[1]).decode("utf-8") if len(sys.argv) > 1 else None
memory = Memory()

if mensaje is None:
    # Primer turno: sesión nueva contra una COPIA de la BD real.
    if os.path.exists(DB_PATH):
        os.unlink(DB_PATH)
    shutil.copy("data/kaito.db", DB_PATH)
    jap = JapaneseMemory(DB_PATH)
    prof = ProfesorJapones(jap, SenseiProvider(), memory, MockSocketIO())
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    saludo = prof.saludo_inicial()
    print(f"[Sesion iniciada, id={prof.session_id}, juez={prof._provider_juez is not None}]")
    print(f"Kaito: {saludo}")
    _guardar(prof)
else:
    jap = JapaneseMemory(DB_PATH)
    prof = ProfesorJapones(jap, SenseiProvider(), memory, MockSocketIO())
    with open(STATE_PATH, encoding="utf-8") as f:
        st = json.load(f)
    prof.activo = True
    prof.session_id = st["session_id"]
    prof.mensajes = st["mensajes"]
    prof.nivel_inmersion = st["nivel_inmersion"]
    prof.ultima_frase_objetivo = st["ultima_frase_objetivo"]
    prof._foco_nuevos = st["foco_nuevos"]
    prof._foco_unidad = st["foco_unidad"]

    t0 = time.time()
    respuesta = prof.responder_turno(mensaje)
    dt = time.time() - t0
    print(f"Laura: {mensaje}")
    print(f"Kaito ({dt:.1f}s): {respuesta}")

    if prof.timer:
        prof.timer.cancel()
    _guardar(prof)
