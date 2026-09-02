"""Rutas /kiosko/* (Fase 3): ajustes rápidos de la pantalla del robot, sin
login pero con escritura solo desde localhost. `import app` no arranca aquí
(deps de la Pi): se monta una app Flask mínima con el MISMO cuerpo que app.py
sobre `system_settings` real en modo simulado (AJUSTES_FAKE)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["AJUSTES_FAKE"] = "1"

import pytest
from flask import Flask, abort, jsonify, request

from core import settings_store


@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_store, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(settings_store, "_inicializada", False)
    from core import system_settings

    app = Flask("kiosko_test")

    def solo_local():
        return request.remote_addr in ("127.0.0.1", "::1")

    @app.route("/kiosko/config")
    def cfg():
        b = system_settings.brillo_get()
        pct = round(b["valor"] / b["max"] * 100) if b.get("max") else 0
        return jsonify({
            "screensaver_min": system_settings.pantalla_inactividad_get(),
            "volumen": system_settings.volumen_get(),
            "brillo": {"soportado": bool(b.get("soportado")), "pct": pct},
            "noche": system_settings.noche_get(),
        })

    @app.route("/kiosko/volumen", methods=["POST"])
    def vol():
        if not solo_local():
            abort(403)
        r = system_settings.volumen_set(request.form.get("v", ""))
        return jsonify(r), (200 if r.get("ok") else 400)

    @app.route("/kiosko/noche", methods=["POST"])
    def noche():
        if not solo_local():
            abort(403)
        n = system_settings.noche_get()
        r = system_settings.noche_set(request.form.get("enabled", ""), n["start"], n["end"])
        return jsonify(r), (200 if r.get("ok") else 400)

    return app.test_client()


def test_config_shape(cli):
    d = cli.get("/kiosko/config").get_json()
    assert set(d) == {"screensaver_min", "volumen", "brillo", "noche"}
    assert 1 <= d["screensaver_min"] <= 120
    assert set(d["brillo"]) == {"soportado", "pct"}
    assert set(d["noche"]) == {"enabled", "start", "end"}


def test_escritura_local_ok(cli):
    # volumen/brillo no persisten en modo simulado (no hay ALSA); basta con que
    # el handler acepte y devuelva ok.
    r = cli.post("/kiosko/volumen", data={"v": "40"})
    assert r.status_code == 200 and r.get_json()["ok"] is True

    # el modo noche sí persiste (app_settings), así que se comprueba el ciclo
    assert cli.post("/kiosko/noche", data={"enabled": "1"}).status_code == 200
    assert cli.get("/kiosko/config").get_json()["noche"]["enabled"] is True
    assert cli.post("/kiosko/noche", data={"enabled": "0"}).status_code == 200
    assert cli.get("/kiosko/config").get_json()["noche"]["enabled"] is False


def test_valor_invalido_400(cli):
    assert cli.post("/kiosko/volumen", data={"v": "no"}).status_code == 400


def test_escritura_remota_403(cli):
    r = cli.post("/kiosko/volumen", data={"v": "30"},
                 environ_overrides={"REMOTE_ADDR": "192.168.1.55"})
    assert r.status_code == 403


def test_config_es_publico(cli):
    r = cli.get("/kiosko/config", environ_overrides={"REMOTE_ADDR": "192.168.1.55"})
    assert r.status_code == 200
