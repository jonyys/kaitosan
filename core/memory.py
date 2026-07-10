import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "kaito.db")

class Memory:
    def __init__(self):
        self.db_path = DB_PATH
        self._inicializar_db()
        self._cargar_perfil_inicial()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _inicializar_db(self):
        """Crea las tablas solo si no existen"""
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at    DATETIME,
                    messages    INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  INTEGER REFERENCES sessions(id),
                    role        TEXT,
                    content     TEXT,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    key         TEXT UNIQUE,
                    value       TEXT,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
        print("✅ Base de datos lista")

    def _cargar_perfil_inicial(self):
        """
        Carga el perfil de Laura solo si no existe.
        INSERT OR IGNORE → nunca sobreescribe datos existentes
        """
        perfil = {
            "nombre": "Laura",
            "apellido": "Hernández",
            "apodo": "Laurius, así la llaman sus amigas de Collado Mediano",
            "edad": "26 años",
            "fecha_nacimiento": "10 de mayo del 2000",
            "hermana": "Una",
            "padre": "José",
            "madre": "Marisa",
            "trabajo": "Programadora frontend en Net Data para el cliente Iberdrola",
            "gustos": "Anime, Japón, está aprendiendo japonés",
            "viajes": "Fuimos a Japón juntos este año",
            "nombre_robot": "Kaito, porque su primer crush fue Kaito de Pichi Pichi Pitch",
            "novio": "Jonathan, vive en Móstoles y le está haciendo este robot",
            "perros": "Troy y Thor",
            "aniversario": "7 de julio, empezamos en 2023",
            "casa": "Compramos una casa en Navalcarnero, nos la dan a principios de 2029 o finales de 2028",
            "ciudad": "Laura vive en Alcorcón"
        }

        with self._conectar() as conn:
            for key, value in perfil.items():
                conn.execute("""
                    INSERT OR IGNORE INTO user_profile (key, value)
                    VALUES (?, ?)
                """, (key, value))

        print("✅ Perfil de Laura cargado")

    # ── SESIONES ────────────────────────────────

    def iniciar_sesion(self) -> int:
        """Crea una nueva sesión y devuelve su ID"""
        with self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO sessions (started_at)
                VALUES (?)
            """, (datetime.now(),))
            return cursor.lastrowid

    def cerrar_sesion(self, session_id: int):
        """Cierra la sesión y guarda cuántos mensajes tuvo"""
        with self._conectar() as conn:
            conn.execute("""
                UPDATE sessions
                SET ended_at = ?,
                    messages = (
                        SELECT COUNT(*) FROM messages
                        WHERE session_id = ?
                    )
                WHERE id = ?
            """, (datetime.now(), session_id, session_id))
        print(f"✅ Sesión {session_id} cerrada")

    # ── MENSAJES ────────────────────────────────

    def guardar_mensaje(self, session_id: int,
                        role: str, content: str):
        """Guarda un mensaje en la BD"""
        with self._conectar() as conn:
            conn.execute("""
                INSERT INTO messages (session_id, role, content)
                VALUES (?, ?, ?)
            """, (session_id, role, content))

    def obtener_ultimas_sesiones(self, limite=3) -> list:
        """
        Obtiene mensajes de las últimas N sesiones.
        Solo se llama cuando Laura pregunta por el pasado.
        """
        with self._conectar() as conn:
            cursor = conn.execute("""
                SELECT m.role, m.content, m.created_at
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE s.id IN (
                    SELECT id FROM sessions
                    ORDER BY started_at DESC
                    LIMIT ?
                )
                AND m.role != 'system'
                ORDER BY m.created_at ASC
            """, (limite,))
            return cursor.fetchall()

    # ── PERFIL ──────────────────────────────────

    def obtener_perfil(self) -> str:
        """
        Devuelve el perfil de Laura como texto
        para incluir en el system prompt
        """
        with self._conectar() as conn:
            cursor = conn.execute("""
                SELECT key, value FROM user_profile
                ORDER BY id ASC
            """)
            datos = cursor.fetchall()

        if not datos:
            return ""

        perfil_texto = "=== INFORMACIÓN SOBRE LAURA ===\n"
        for key, value in datos:
            perfil_texto += f"- {key}: {value}\n"

        return perfil_texto

    def actualizar_perfil(self, key: str, value: str):
        """Actualiza o añade un dato del perfil"""
        with self._conectar() as conn:
            conn.execute("""
                INSERT INTO user_profile (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value, datetime.now()))
        print(f"✅ Perfil actualizado: {key} = {value}")

    def obtener_historial_reciente(self) -> str:
        """
        Devuelve las últimas sesiones como texto.
        Solo se usa cuando Laura pregunta por conversaciones pasadas.
        """
        sesiones = self.obtener_ultimas_sesiones(limite=3)

        if not sesiones:
            return ""

        historial_texto = "=== CONVERSACIONES RECIENTES ===\n"
        for role, content, created_at in sesiones:
            quien = "Laura" if role == "user" else "Kaito"
            historial_texto += f"[{created_at}] {quien}: {content}\n"

        return historial_texto

    def buscar_en_historial(self, terminos: list) -> str:
        """
        Busca mensajes relevantes en la BD
        por términos clave.
        Se usa siempre antes de responder.
        """
        if not terminos:
            return ""

        resultados = []

        with self._conectar() as conn:
            for termino in terminos:
                cursor = conn.execute("""
                    SELECT m.role, m.content, m.created_at
                    FROM messages m
                    WHERE m.content LIKE ?
                    AND m.role != 'system'
                    ORDER BY m.created_at DESC
                    LIMIT 5
                """, (f"%{termino}%",))
                resultados.extend(cursor.fetchall())

        if not resultados:
            return ""

        # Elimina duplicados
        vistos = set()
        unicos = []
        for r in resultados:
            if r[1] not in vistos:
                vistos.add(r[1])
                unicos.append(r)

        texto = "=== MENSAJES RELEVANTES DEL PASADO ===\n"
        for role, content, created_at in unicos:
            quien = "Laura" if role == "user" else "Kaito"
            texto += f"[{created_at}] {quien}: {content}\n"

        return texto