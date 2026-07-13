import sqlite3
from datetime import datetime

class JapaneseMemory:
    def __init__(self, db_path):
        self.db_path = db_path
        self._inicializar_tablas()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _inicializar_tablas(self):
        with self._conectar() as conn:
            conn.executescript("""
                -- Competencias globales
                CREATE TABLE IF NOT EXISTS japanese_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill TEXT UNIQUE,        -- 'hiragana', 'katakana', 'kanji_n5', etc.
                    percentage REAL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Vocabulario con estado detallado
                CREATE TABLE IF NOT EXISTS japanese_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    reading TEXT,             -- lectura en kana
                    meaning TEXT,             -- significado
                    type TEXT,                -- 'sustantivo', 'verbo', 'adjetivo', etc.
                    status TEXT DEFAULT 'learning',  -- 'learning', 'learned', 'mastered'
                    confidence REAL DEFAULT 0,       -- 0-100
                    errors INTEGER DEFAULT 0,
                    last_reviewed DATETIME,
                    times_reviewed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Gramática
                CREATE TABLE IF NOT EXISTS japanese_grammar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grammar_point TEXT NOT NULL,  -- '～ます', '～たい', '～ている'
                    description TEXT,
                    mastery REAL DEFAULT 0,       -- 0-100
                    errors INTEGER DEFAULT 0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Temas de conversación que domina
                CREATE TABLE IF NOT EXISTS japanese_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE,           -- 'familia', 'comida', 'trabajo'
                    can_handle BOOLEAN DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Perfil resumido (se regenera al final de cada sesión)
                CREATE TABLE IF NOT EXISTS japanese_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_text TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Registro de sesiones de japonés
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

    def registrar_vocabulario(self, word, reading=None, meaning=None, word_type=None):
        """Registra una nueva palabra o actualiza una existente."""
        with self._conectar() as conn:
            # Verificar si ya existe
            cursor = conn.execute(
                "SELECT id, errors FROM japanese_vocabulary WHERE word = ?",
                (word,)
            )
            row = cursor.fetchone()
            if row:
                # Actualizar repaso
                conn.execute(
                    """UPDATE japanese_vocabulary 
                       SET last_reviewed = ?, times_reviewed = times_reviewed + 1
                       WHERE id = ?""",
                    (datetime.now(), row[0])
                )
                print(f"🎌 Actualizado repaso de vocabulario: {word}")
            else:
                # Nuevo vocabulario
                conn.execute(
                    """INSERT INTO japanese_vocabulary 
                       (word, reading, meaning, type, status, confidence, last_reviewed, times_reviewed)
                       VALUES (?, ?, ?, ?, 'learning', 0, ?, 1)""",
                    (word, reading, meaning, word_type, datetime.now())
                )
                print(f"🎌 Nuevo vocabulario registrado: {word}")

    def registrar_gramatica(self, grammar_point, description=None):
        """Registra una estructura gramatical nueva o actualiza su uso."""
        with self._conectar() as conn:
            cursor = conn.execute(
                "SELECT id FROM japanese_grammar WHERE grammar_point = ?",
                (grammar_point,)
            )
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "UPDATE japanese_grammar SET last_used = ? WHERE id = ?",
                    (datetime.now(), row[0])
                )
            else:
                conn.execute(
                    """INSERT INTO japanese_grammar (grammar_point, description, mastery, last_used)
                       VALUES (?, ?, 0, ?)""",
                    (grammar_point, description, datetime.now())
                )
                print(f"🎌 Nueva gramática registrada: {grammar_point}")