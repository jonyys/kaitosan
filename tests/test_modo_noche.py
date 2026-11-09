"""Modo noche del /reloj: validación y persistencia de la franja horaria
(core/system_settings.noche_get/noche_set). El toggle oscuro lo hace el front
del /reloj comparando la hora; aquí solo se prueba el ajuste."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core import settings_store


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_store, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(settings_store, "_inicializada", False)
    from core import system_settings
    return system_settings


def test_defecto(db):
    n = db.noche_get()
    assert n == {"enabled": False, "start": "23:00", "end": "07:00"}


def test_guardar_y_leer(db):
    assert db.noche_set("1", "22:30", "06:45")["ok"] is True
    assert db.noche_get() == {"enabled": True, "start": "22:30", "end": "06:45"}
    # desactivar conserva la franja
    assert db.noche_set("0", "22:30", "06:45")["ok"] is True
    n = db.noche_get()
    assert n["enabled"] is False and n["start"] == "22:30"


@pytest.mark.parametrize("start,end", [
    ("9:00", "07:00"),    # falta el cero
    ("24:00", "07:00"),   # hora fuera de rango
    ("22:00", "22:60"),   # minuto fuera de rango
    ("noche", "mañana"),
])
def test_horas_no_validas_con_activado(db, start, end):
    assert db.noche_set("1", start, end)["ok"] is False


def test_inicio_igual_a_fin(db):
    assert db.noche_set("1", "23:00", "23:00")["ok"] is False


def test_horas_no_validas_no_bloquean_si_desactivado(db):
    # apagar el modo noche no exige horas válidas
    assert db.noche_set("0", "", "")["ok"] is True
    assert db.noche_get()["enabled"] is False


def test_interruptor_manual_y_nivel(db):
    assert db.noche_manual_get() is None
    db.noche_manual_set("1", "0")
    assert db.noche_manual_get() == {"valor": True, "franja": False}
    est = db.noche_estado()
    assert est["manual"] == {"valor": True, "franja": False} and est["nivel"] == 35 and est["enabled"] is False
    db.noche_manual_set("0", "1")
    assert db.noche_manual_get() == {"valor": False, "franja": True}


def test_brillo_suave_no_baja_de_15(db):
    assert db.brillo_suave_get() == 100
    assert db.brillo_suave_set(40)["valor"] == 40 and db.brillo_suave_get() == 40
    assert db.brillo_suave_set(3)["valor"] == 15
    assert db.brillo_suave_set("x")["ok"] is False


def test_no_molestar_se_guarda(db):
    assert db.no_molestar_get() is False
    assert db.no_molestar_set("1")["activo"] is True and db.no_molestar_get() is True
    assert db.no_molestar_set("0")["activo"] is False and db.no_molestar_get() is False
