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
                CREATE TABLE IF NOT EXISTS japanese_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    item TEXT,
                    detail TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_reviewed DATETIME,
                    times_reviewed INTEGER DEFAULT 0,
                    accuracy REAL
                );
                CREATE TABLE IF NOT EXISTS japanese_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def obtener_progreso(self) -> str:
        """Devuelve un resumen textual del progreso para inyectar en el prompt."""
        with self._conectar() as conn:
            cursor = conn.execute("SELECT category, COUNT(*) FROM japanese_progress GROUP BY category")
            datos = cursor.fetchall()
        resumen = "Progreso de japonés de Laura:\n"
        for cat, count in datos:
            resumen += f"- {cat}: {count} elementos\n"
        # Añadir última lección, errores frecuentes, etc. (simplificado)
        return resumen

    def registrar_item(self, category, item, detail=""):
        with self._conectar() as conn:
            # Verificar si ya existe esa combinación categoría+ítem
            cursor = conn.execute("""
                SELECT id, times_reviewed FROM japanese_progress
                WHERE category = ? AND item = ?
            """, (category, item))
            row = cursor.fetchone()

            if row:
                # Ya existe → actualizar repasos y último repaso
                item_id = row[0]
                new_times = row[1] + 1
                conn.execute("""
                    UPDATE japanese_progress
                    SET detail = ?,
                        last_reviewed = ?,
                        times_reviewed = ?
                    WHERE id = ?
                """, (detail, datetime.now(), new_times, item_id))
                print(f"🎌 Actualizado: {category}/{item} (repasos: {new_times})")
            else:
                # Nuevo ítem
                conn.execute("""
                    INSERT INTO japanese_progress
                        (category, item, detail, last_reviewed, times_reviewed)
                    VALUES (?, ?, ?, ?, 0)
                """, (category, item, detail, datetime.now()))
                print(f"🎌 Nuevo ítem registrado: {category}/{item}")