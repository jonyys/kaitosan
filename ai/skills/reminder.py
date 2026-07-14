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

    def __init__(self, sample_rate=48000):
        self.sample_rate = sample_rate
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

    def crear_recordatorio(self, texto: str, cuando_str: str) -> str:
        print(f"📌 DEBUG crear_recordatorio: texto='{texto}', cuando_str='{cuando_str}'")

        """
        Crea un recordatorio.
        cuando_str puede ser:
        - "en 30 minutos"
        - "mañana 10:00"
        - "el viernes que viene a las 17:00"
        - "el próximo lunes"
        - "dentro de dos semanas"
        - "el 5 de enero a las 8"
        - "YYYY-MM-DD HH:MM"
        """
        try:
            ahora = datetime.now()
            fecha = self._interpretar_cuando(cuando_str, ahora)

            if fecha is None:
                # Intentar parseo ISO por si el LLM lo pasó así
                try:
                    fecha = datetime.strptime(cuando_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    return "No he entendido la fecha. Prueba con 'mañana a las 10', 'el viernes que viene' o 'en 30 minutos'."

            # Guardar en BD
            with self._conectar() as conn:
                conn.execute(
                    "INSERT INTO reminders (texto, fecha_hora) VALUES (?, ?)",
                    (texto, fecha.strftime("%Y-%m-%d %H:%M"))
                )

            return f"Recordatorio guardado: '{texto}' para el {fecha.strftime('%d/%m a las %H:%M')}."

        except Exception as e:
            print(f"❌ Error creando recordatorio: {e}")
            return "No he podido guardar el recordatorio. ¿Puedes repetirlo?"

    def _comprobar_recordatorios(self):
        """Comprueba si hay recordatorios pendientes cada 30 segundos."""
        while True:
            try:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                with self._conectar() as conn:
                    pendientes = conn.execute(
                        "SELECT id, texto FROM reminders WHERE fecha_hora <= ? AND completado = 0",
                        (ahora,)
                    ).fetchall()

                    for rid, texto in pendientes:
                        print(f"📌 Recordatorio: {texto}")
                        # Marcar como completado
                        conn.execute(
                            "UPDATE reminders SET completado = 1 WHERE id = ?",
                            (rid,)
                        )
            except Exception as e:
                print(f"❌ Error comprobando recordatorios: {e}")

            time.sleep(30)

    def _iniciar_comprobador(self):
        hilo = threading.Thread(target=self._comprobar_recordatorios, daemon=True)
        hilo.start()

    def _interpretar_cuando(self, cuando_str: str, ahora: datetime) -> datetime | None:
        """Convierte una expresión temporal en una fecha concreta."""
        import re
        texto = cuando_str.lower().strip()
        hoy = ahora.date()

        # 1) "mañana", "pasado mañana"
        if "pasado mañana" in texto:
            return ahora + timedelta(days=2)
        if "mañana" in texto:
            return self._extraer_hora(texto, ahora + timedelta(days=1))

        # 2) "el próximo X", "el X que viene", "el X"
        for nombre_dia, num_dia in self.DIAS_SEMANA.items():
            if nombre_dia in texto:
                dias_hasta = (num_dia - hoy.weekday()) % 7
                if dias_hasta == 0 and ("próximo" in texto or "que viene" in texto or "siguiente" in texto):
                    dias_hasta = 7
                elif dias_hasta == 0:
                    dias_hasta = 7  # si es hoy, asumimos la semana que viene
                fecha = ahora + timedelta(days=dias_hasta)
                return self._extraer_hora(texto, fecha)

        # 3) "dentro de X días/semanas/meses"
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

        # 4) "en X minutos/horas" (caso simple)
        if "en" in texto:
            nums = re.findall(r'\d+', texto)
            if nums:
                cantidad = int(nums[0])
                if "hora" in texto:
                    return ahora + timedelta(hours=cantidad)
                if "minuto" in texto:
                    return ahora + timedelta(minutes=cantidad)

        # 5) "el X de mes" o "el X de mes de año"
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

        # 6) "HH:MM" (hoy o mañana)
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
        """Busca una hora en el texto y la aplica a la fecha dada."""
        import re
        match = re.search(r'(\d{1,2})[:h](\d{2})?', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2)) if match.group(2) else 0
            fecha = fecha.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        else:
            fecha = fecha.replace(hour=9, minute=0, second=0, microsecond=0)  # por defecto 9:00
        return fecha

    def _sumar_meses(self, fecha: datetime, meses: int) -> datetime:
        """Suma meses a una fecha (aproximado)."""
        nuevo_mes = fecha.month + meses
        año = fecha.year + (nuevo_mes - 1) // 12
        mes = ((nuevo_mes - 1) % 12) + 1
        # Días del mes
        dias_por_mes = [31, 29 if año % 4 == 0 and (año % 100 != 0 or año % 400 == 0) else 28,
                        31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        dia = min(fecha.day, dias_por_mes[mes - 1])
        return fecha.replace(year=año, month=mes, day=dia)