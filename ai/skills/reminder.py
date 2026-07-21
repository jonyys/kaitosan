import sqlite3
import threading
import time
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "kaito.db")

class ReminderSkill:

    DIAS_SEMANA = {
        "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
    }

    MESES = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12
    }

    def __init__(self, sample_rate=48000, socketio=None):
        self.sample_rate = sample_rate
        self.socketio = socketio
        self._inicializar_tabla()
        self._iniciar_comprobador()

    def _conectar(self):
        return sqlite3.connect(DB_PATH)

    def _inicializar_tabla(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    texto TEXT NOT NULL,
                    fecha_hora DATETIME NOT NULL,
                    creado DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completado BOOLEAN DEFAULT 0
                )
            """)

    def _emitir_estado(self):
        if self.socketio:
            try:
                self.socketio.emit("actualizar_recordatorios", self._estado_serializable())
            except Exception as e:
                print(f"⚠️ Error emitiendo actualizar_recordatorios: {e}")

    def _estado_serializable(self):
        with self._conectar() as conn:
            rows = conn.execute(
                "SELECT id, texto, fecha_hora, creado, completado FROM reminders ORDER BY completado ASC, fecha_hora ASC"
            ).fetchall()
        return {
            "recordatorios": [
                {
                    "id": r[0],
                    "texto": r[1],
                    "fecha_hora": r[2],
                    "creado": r[3],
                    "completado": bool(r[4])
                }
                for r in rows
            ]
        }

    def crear_recordatorio(self, texto: str, cuando_str: str) -> str:
        print(f"📌 DEBUG crear_recordatorio: texto='{texto}', cuando_str='{cuando_str}'")
        try:
            ahora = datetime.now()
            fecha = self._interpretar_cuando(cuando_str, ahora)

            if fecha is None:
                try:
                    fecha = datetime.strptime(cuando_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    return "No he entendido la fecha. Prueba con 'mañana a las 10', 'el viernes que viene' o 'en 30 minutos'."

            with self._conectar() as conn:
                conn.execute(
                    "INSERT INTO reminders (texto, fecha_hora) VALUES (?, ?)",
                    (texto, fecha.strftime("%Y-%m-%d %H:%M"))
                )

            self._emitir_estado()
            return f"Recordatorio guardado: '{texto}' para el {fecha.strftime('%d/%m a las %H:%M')}."

        except Exception as e:
            print(f"❌ Error creando recordatorio: {e}")
            return "No he podido guardar el recordatorio. ¿Puedes repetirlo?"

    def cancelar_recordatorio(self, id: int) -> str:
        try:
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT texto FROM reminders WHERE id = ? AND completado = 0", (id,)
                ).fetchone()
                if not row:
                    return "No encontré ese recordatorio pendiente."
                conn.execute("DELETE FROM reminders WHERE id = ?", (id,))
            self._emitir_estado()
            return f"Recordatorio '{row[0]}' eliminado."
        except Exception as e:
            print(f"❌ Error cancelando recordatorio: {e}")
            return "No pude cancelar el recordatorio."

    def cancelar_recordatorio_por_texto(self, texto: str) -> str:
        """Cancela el recordatorio pendiente cuyo texto contenga la palabra clave dada."""
        try:
            with self._conectar() as conn:
                rows = conn.execute(
                    "SELECT id, texto FROM reminders WHERE completado = 0"
                ).fetchall()
            if not rows:
                return "No hay recordatorios pendientes que cancelar."
            texto_lower = texto.lower()
            coincidencias = [(r[0], r[1]) for r in rows if texto_lower in r[1].lower()]
            if not coincidencias:
                todos = ", ".join(f"'{r[1]}'" for r in rows)
                return f"No encontré ningún recordatorio con '{texto}'. Los pendientes son: {todos}."
            if len(coincidencias) > 1:
                lista = ", ".join(f"'{c[1]}'" for c in coincidencias)
                return f"Hay varios recordatorios que coinciden: {lista}. ¿Cuál quieres eliminar?"
            rid, rtexto = coincidencias[0]
            with self._conectar() as conn:
                conn.execute("DELETE FROM reminders WHERE id = ?", (rid,))
            self._emitir_estado()
            return f"Recordatorio '{rtexto}' eliminado."
        except Exception as e:
            print(f"❌ Error cancelando recordatorio por texto: {e}")
            return "No pude cancelar el recordatorio."

    def listar_recordatorios(self) -> str:
        with self._conectar() as conn:
            rows = conn.execute(
                "SELECT texto, fecha_hora FROM reminders WHERE completado = 0 ORDER BY fecha_hora ASC"
            ).fetchall()
        if not rows:
            return "No hay recordatorios pendientes."
        partes = [f"'{r[0]}' el {r[1]}" for r in rows]
        return "Recordatorios pendientes: " + "; ".join(partes) + "."

    def _comprobar_recordatorios(self):
        while True:
            try:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                with self._conectar() as conn:
                    pendientes = conn.execute(
                        "SELECT id, texto FROM reminders WHERE fecha_hora <= ? AND completado = 0",
                        (ahora,)
                    ).fetchall()

                    if pendientes:
                        for rid, texto in pendientes:
                            print(f"📌 Recordatorio: {texto}")
                            conn.execute(
                                "UPDATE reminders SET completado = 1 WHERE id = ?",
                                (rid,)
                            )
                        self._emitir_estado()
            except Exception as e:
                print(f"❌ Error comprobando recordatorios: {e}")

            time.sleep(30)

    def _iniciar_comprobador(self):
        hilo = threading.Thread(target=self._comprobar_recordatorios, daemon=True)
        hilo.start()

    def _interpretar_cuando(self, cuando_str: str, ahora: datetime) -> datetime | None:
        import re
        texto = cuando_str.lower().strip()
        hoy = ahora.date()

        if "pasado mañana" in texto:
            return ahora + timedelta(days=2)
        if "mañana" in texto:
            return self._extraer_hora(texto, ahora + timedelta(days=1))

        for nombre_dia, num_dia in self.DIAS_SEMANA.items():
            if nombre_dia in texto:
                dias_hasta = (num_dia - hoy.weekday()) % 7
                if dias_hasta == 0 and ("próximo" in texto or "que viene" in texto or "siguiente" in texto):
                    dias_hasta = 7
                elif dias_hasta == 0:
                    dias_hasta = 7
                fecha = ahora + timedelta(days=dias_hasta)
                return self._extraer_hora(texto, fecha)

        nums = re.findall(r'\d+', texto)
        if nums:
            cantidad = int(nums[0])
            if "semana" in texto:
                return ahora + timedelta(weeks=cantidad)
            if "mes" in texto:
                return self._sumar_meses(ahora, cantidad)
            if "día" in texto or "dia" in texto:
                return ahora + timedelta(days=cantidad)
            if "hora" in texto:
                return ahora + timedelta(hours=cantidad)
            if "minuto" in texto:
                return ahora + timedelta(minutes=cantidad)

        if "en" in texto:
            nums = re.findall(r'\d+', texto)
            if nums:
                cantidad = int(nums[0])
                if "hora" in texto:
                    return ahora + timedelta(hours=cantidad)
                if "minuto" in texto:
                    return ahora + timedelta(minutes=cantidad)

        match = re.search(r'(\d{1,2})\s+de\s+(\w+)', texto)
        if match:
            dia = int(match.group(1))
            mes_nombre = match.group(2)
            mes = self.MESES.get(mes_nombre)
            if mes:
                año = ahora.year
                match_año = re.search(r'de\s+(\d{4})', texto)
                if match_año:
                    año = int(match_año.group(1))
                fecha = datetime(año, mes, dia)
                return self._extraer_hora(texto, fecha)

        match = re.search(r'(\d{1,2})[:h](\d{2})?', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2)) if match.group(2) else 0
            fecha = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if fecha <= ahora:
                fecha += timedelta(days=1)
            return fecha

        return None

    def _extraer_hora(self, texto: str, fecha: datetime) -> datetime:
        import re
        match = re.search(r'(\d{1,2})[:h](\d{2})?', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2)) if match.group(2) else 0
            fecha = fecha.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        else:
            fecha = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        return fecha

    def _sumar_meses(self, fecha: datetime, meses: int) -> datetime:
        nuevo_mes = fecha.month + meses
        año = fecha.year + (nuevo_mes - 1) // 12
        mes = ((nuevo_mes - 1) % 12) + 1
        dias_por_mes = [31, 29 if año % 4 == 0 and (año % 100 != 0 or año % 400 == 0) else 28,
                        31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        dia = min(fecha.day, dias_por_mes[mes - 1])
        return fecha.replace(year=año, month=mes, day=dia)
