"""
core/settings_store.py — Almacén de ajustes de la app (Fase 1, PLAN_AJUSTES §4.1).

Guarda pares clave/valor en la misma BD SQLite que usa el resto del proyecto
(`data/kaito.db`), en una tabla propia:

    CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT);

API pública:
    settings_get(key, default=None) -> str | None
    settings_set(key, value)        -> None

La primera vez que se usa en el proceso se crea la tabla y se siembra desde el
`.env` (retrocompatibilidad). La siembra es idempotente: solo rellena la clave
que aún no existe, nunca sobrescribe lo que ya haya guardado Laura.

    admin_user       <- ADMIN_USER       (por defecto "laura")
    admin_pass_hash  <- hash werkzeug de ADMIN_PASSWORD
    tz_auto          <- "0"
"""

import os
import sqlite3

from core.memory import DB_PATH

_TABLA = "app_settings"
_inicializada = False


def _conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _leer(conn, key, default=None):
    fila = conn.execute(
        f"SELECT value FROM {_TABLA} WHERE key = ?", (key,)
    ).fetchone()
    return default if fila is None else fila[0]


def _escribir(conn, key, value):
    conn.execute(
        f"INSERT INTO {_TABLA} (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, None if value is None else str(value)),
    )


def _hash_password(pwd):
    """Hash werkzeug de la contraseña; None si werkzeug aún no está instalado."""
    try:
        from werkzeug.security import generate_password_hash
    except ImportError:
        return None
    return generate_password_hash(pwd)


def _sembrar_desde_env(conn):
    if _leer(conn, "admin_user") is None:
        _escribir(conn, "admin_user", os.getenv("ADMIN_USER", "laura"))

    if _leer(conn, "admin_pass_hash") is None:
        h = _hash_password(os.getenv("ADMIN_PASSWORD", "kaito123"))
        if h is not None:
            _escribir(conn, "admin_pass_hash", h)

    if _leer(conn, "tz_auto") is None:
        _escribir(conn, "tz_auto", "0")


def _inicializar():
    """Crea la tabla y siembra desde el `.env`. Se ejecuta una vez por proceso."""
    global _inicializada
    if _inicializada:
        return
    with _conectar() as conn:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
            "    key   TEXT PRIMARY KEY,"
            "    value TEXT"
            ")"
        )
        _sembrar_desde_env(conn)
    _inicializada = True


def settings_get(key, default=None):
    """Devuelve el valor guardado para `key` (str) o `default` si no existe."""
    _inicializar()
    with _conectar() as conn:
        return _leer(conn, key, default)


def settings_set(key, value):
    """Guarda `value` bajo `key`, creando o actualizando la fila."""
    _inicializar()
    with _conectar() as conn:
        _escribir(conn, key, value)
