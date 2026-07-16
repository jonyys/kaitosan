import sqlite3
from datetime import datetime
from ai.sensei.srs import sm2


class JapaneseMemory:
    def __init__(self, db_path):
        self.db_path = db_path
        self._inicializar_tablas()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _inicializar_tablas(self):
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS japanese_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill TEXT UNIQUE,
                    percentage REAL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    reading TEXT,
                    meaning TEXT,
                    type TEXT,
                    status TEXT DEFAULT 'learning',
                    confidence REAL DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    last_reviewed DATETIME,
                    times_reviewed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_grammar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grammar_point TEXT NOT NULL,
                    description TEXT,
                    mastery REAL DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE,
                    can_handle BOOLEAN DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_text TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    words_learned INTEGER DEFAULT 0,
                    grammar_practiced TEXT,
                    errors_noted TEXT,
                    summary TEXT
                );
            """)
        self._migrar_srs()

    def _migrar_srs(self):
        """Migración idempotente: añade columnas SRS si no existen."""
        vocab_cols = {
            "reps": "INTEGER DEFAULT 0",
            "ease_factor": "REAL DEFAULT 2.5",
            "interval_days": "INTEGER DEFAULT 0",
            "next_review": "TEXT",
            "times_correct": "INTEGER DEFAULT 0",
            "first_taught_session_id": "INTEGER",
        }
        grammar_cols = {
            "reps": "INTEGER DEFAULT 0",
            "ease_factor": "REAL DEFAULT 2.5",
            "interval_days": "INTEGER DEFAULT 0",
            "next_review": "TEXT",
            "times_seen": "INTEGER DEFAULT 0",
            "times_correct": "INTEGER DEFAULT 0",
        }
        with self._conectar() as conn:
            self._add_columns_if_missing(conn, "japanese_vocabulary", vocab_cols)
            self._add_columns_if_missing(conn, "japanese_grammar", grammar_cols)
            conn.execute(
                "UPDATE japanese_vocabulary SET next_review = date('now') WHERE next_review IS NULL"
            )
            conn.execute(
                "UPDATE japanese_grammar SET next_review = date('now') WHERE next_review IS NULL"
            )

    def _add_columns_if_missing(self, conn, table, columns):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for col, definition in columns.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

    # ── Métodos SRS nuevos ──────────────────────────────────────────────────

    def add_item(self, kind, jp, reading=None, meaning=None, tipo=None, session_id=None):
        """Inserta un ítem nuevo si no existe; si existe, no duplica.

        kind: "vocabulario" | "gramatica"
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if kind == "vocabulario":
            with self._conectar() as conn:
                existing = conn.execute(
                    "SELECT id FROM japanese_vocabulary WHERE word = ?", (jp,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO japanese_vocabulary
                           (word, reading, meaning, type, status, confidence,
                            reps, ease_factor, interval_days, next_review,
                            times_reviewed, times_correct, first_taught_session_id)
                           VALUES (?, ?, ?, ?, 'learning', 0,
                                   0, 2.5, 0, ?,
                                   0, 0, ?)""",
                        (jp, reading, meaning, tipo, today, session_id),
                    )
        elif kind == "gramatica":
            with self._conectar() as conn:
                existing = conn.execute(
                    "SELECT id FROM japanese_grammar WHERE grammar_point = ?", (jp,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO japanese_grammar
                           (grammar_point, description, mastery,
                            reps, ease_factor, interval_days, next_review,
                            times_seen, times_correct)
                           VALUES (?, ?, 0,
                                   0, 2.5, 0, ?,
                                   0, 0)""",
                        (jp, meaning, today),
                    )

    def get_due_items(self, limit=5, kind="vocabulario"):
        """Devuelve ítems cuyo next_review <= hoy, ordenados por fecha."""
        today = datetime.now().strftime("%Y-%m-%d")
        if kind == "vocabulario":
            query = """
                SELECT id, word AS jp, reading, meaning, type,
                       reps, ease_factor, interval_days, next_review, status
                FROM japanese_vocabulary
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """
            col_jp = "word"
        else:
            query = """
                SELECT id, grammar_point AS jp, description AS meaning,
                       reps, ease_factor, interval_days, next_review, mastery
                FROM japanese_grammar
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """
            col_jp = "grammar_point"

        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (today, limit)).fetchall()
            return [dict(r) for r in rows]

    def review(self, item_id, quality, kind="vocabulario"):
        """Aplica SM-2 al ítem y actualiza la BD."""
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().isoformat(sep=" ", timespec="seconds")

        if kind == "vocabulario":
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT reps, ease_factor, interval_days FROM japanese_vocabulary WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if not row:
                    return
                reps, ease, interval = sm2(quality, row[0], row[1], row[2])
                from datetime import timedelta
                next_review = (
                    datetime.now() + timedelta(days=max(interval, 1))
                ).strftime("%Y-%m-%d")

                if interval >= 21:
                    status = "mastered"
                elif interval >= 7:
                    status = "learned"
                else:
                    status = "learning"

                conn.execute(
                    """UPDATE japanese_vocabulary SET
                           reps = ?, ease_factor = ?, interval_days = ?,
                           next_review = ?, status = ?,
                           times_reviewed = times_reviewed + 1,
                           times_correct = times_correct + ?,
                           errors = errors + ?,
                           last_reviewed = ?
                       WHERE id = ?""",
                    (
                        reps, round(ease, 4), interval,
                        next_review, status,
                        1 if quality >= 3 else 0,
                        1 if quality < 3 else 0,
                        now, item_id,
                    ),
                )
        elif kind == "gramatica":
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT reps, ease_factor, interval_days FROM japanese_grammar WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if not row:
                    return
                reps, ease, interval = sm2(quality, row[0], row[1], row[2])
                from datetime import timedelta
                next_review = (
                    datetime.now() + timedelta(days=max(interval, 1))
                ).strftime("%Y-%m-%d")

                mastery = min(100.0, interval / 21.0 * 100)

                conn.execute(
                    """UPDATE japanese_grammar SET
                           reps = ?, ease_factor = ?, interval_days = ?,
                           next_review = ?, mastery = ?,
                           times_seen = times_seen + 1,
                           times_correct = times_correct + ?,
                           errors = errors + ?,
                           last_used = ?
                       WHERE id = ?""",
                    (
                        reps, round(ease, 4), interval,
                        next_review, round(mastery, 2),
                        1 if quality >= 3 else 0,
                        1 if quality < 3 else 0,
                        now, item_id,
                    ),
                )

    def get_item_id(self, jp: str, kind: str = "vocabulario"):
        """Devuelve el id de un ítem por su texto en japonés, o None si no existe."""
        if kind == "vocabulario":
            table, col = "japanese_vocabulary", "word"
        else:
            table, col = "japanese_grammar", "grammar_point"
        with self._conectar() as conn:
            row = conn.execute(
                f"SELECT id FROM {table} WHERE {col} = ?", (jp,)
            ).fetchone()
        return row[0] if row else None

    def guardar_resumen_sesion(self, session_id, summary, words_learned=0,
                               grammar_practiced="", errors_noted=""):
        """Actualiza el resumen de una sesión al cerrarla."""
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                """UPDATE japanese_sessions SET
                       ended_at = ?, summary = ?,
                       words_learned = ?, grammar_practiced = ?, errors_noted = ?
                   WHERE id = ?""",
                (now, summary, words_learned, grammar_practiced, errors_noted, session_id),
            )

    def resumen_perfil(self) -> dict:
        """Versión ligera de obtener_perfil_completo para el orquestador."""
        with self._conectar() as conn:
            skills = conn.execute(
                "SELECT skill, percentage FROM japanese_skills"
            ).fetchall()
            vocab_counts = conn.execute(
                """SELECT status, COUNT(*) FROM japanese_vocabulary GROUP BY status"""
            ).fetchall()
            due_count = conn.execute(
                "SELECT COUNT(*) FROM japanese_vocabulary WHERE next_review <= date('now')"
            ).fetchone()[0]
            last_session = conn.execute(
                """SELECT summary FROM japanese_sessions
                   WHERE summary IS NOT NULL ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
            weak = conn.execute(
                "SELECT word, errors FROM japanese_vocabulary WHERE errors > 2 ORDER BY errors DESC LIMIT 5"
            ).fetchall()

        return {
            "skills": dict(skills),
            "vocab_by_status": dict(vocab_counts),
            "due_count": due_count,
            "last_session_summary": last_session[0] if last_session else None,
            "weak_points": [{"word": w, "errors": e} for w, e in weak],
        }

    # ── Perfil para el agente general ───────────────────────────────────────
    # `obtener_perfil_completo` sigue en uso: lo llama el agente general de
    # brain.py (flujo `consultar_progreso`), que es independiente del modo
    # sensei. El orquestador sensei usa `resumen_perfil()` en su lugar.

    def obtener_perfil_completo(self) -> str:
        """Genera el perfil actual de Laura para el prompt del profesor."""
        with self._conectar() as conn:
            skills = conn.execute(
                "SELECT skill, percentage FROM japanese_skills"
            ).fetchall()
            vocab_count = conn.execute(
                "SELECT COUNT(*) FROM japanese_vocabulary WHERE status IN ('learned','mastered')"
            ).fetchone()[0]
            grammar = conn.execute(
                "SELECT grammar_point, mastery FROM japanese_grammar ORDER BY mastery DESC"
            ).fetchall()
            topics = conn.execute(
                "SELECT topic FROM japanese_topics WHERE can_handle=1"
            ).fetchall()
            errors = conn.execute(
                "SELECT word, errors FROM japanese_vocabulary WHERE errors>2 ORDER BY errors DESC LIMIT 5"
            ).fetchall()

        perfil = "=== PERFIL ACTUAL DE LAURA (JAPONÉS) ===\n"
        perfil += f"Palabras dominadas: {vocab_count}\n"
        perfil += "Competencias:\n"
        for s, p in skills:
            perfil += f"- {s}: {p}%\n"
        perfil += "Gramática:\n"
        for g, m in grammar:
            perfil += f"- {g}: {m:.0f}% dominio\n"
        if topics:
            perfil += "Temas que maneja:\n"
            for (t,) in topics:
                perfil += f"- {t}\n"
        if errors:
            perfil += "Puntos débiles:\n"
            for w, e in errors:
                perfil += f"- {w}: {e} errores\n"
        perfil += "\nInstrucciones:\n"
        perfil += "- No enseñes saludos ni vocabulario ya dominado.\n"
        perfil += "- Refuerza las estructuras con errores frecuentes.\n"
        return perfil
