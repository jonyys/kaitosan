"""Fase 02 — la despedida no espera al extractor."""
import os
import sys
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.profesor import ProfesorJapones


def test_salir_vuelve_al_instante():
    pendientes = []
    socketio = MagicMock()
    socketio.start_background_task = lambda fn, *a: pendientes.append(fn)

    prof = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), socketio)
    prof.activo = True
    prof.session_id = 1

    # extractor lento: 5 s, como el real
    prof.cerrar_sesion_y_extraer = lambda: time.sleep(5)

    t0 = time.perf_counter()
    prof.salir()
    tardanza = time.perf_counter() - t0

    assert tardanza < 0.1, f"salir() bloqueó {tardanza:.2f}s"
    assert pendientes, "la extracción no se encoló en segundo plano"
    assert prof.activo is False


if __name__ == "__main__":
    test_salir_vuelve_al_instante()
    print("✅ Fase 02 OK: salir() vuelve al instante y encola la extracción")
