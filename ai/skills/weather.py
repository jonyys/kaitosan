import time

import requests

# Alcorcón (las de antes eran las de Madrid centro)
ALCORCON = (40.3458, -3.8249)

# Código WMO de Open-Meteo → estado que pinta el reloj (lo que no está aquí cuenta como nublado)
_ESTADOS = (
    ({0, 1}, "soleado"),
    ({51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}, "lluvia"),
    ({71, 73, 75, 77, 85, 86}, "nieve"),
    ({95, 96, 99}, "tormenta"),
)


class WeatherSkill:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        self._resumen = None       # último dato bueno del reloj
        self._resumen_ts = 0.0

    def resumen_alcorcon(self) -> dict | None:
        """Tiempo de Alcorcón para el reloj, con caché de 10 min; si falla la red, el último bueno (o None)."""
        if self._resumen and time.time() - self._resumen_ts < 600:
            return self._resumen
        try:
            params = {
                "latitude": ALCORCON[0], "longitude": ALCORCON[1],
                "current": "temperature_2m,weather_code,is_day",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "Europe/Madrid", "forecast_days": 1,
            }
            d = requests.get(self.base_url, params=params, timeout=5).json()
            cur, dia = d["current"], d["daily"]
            codigo = cur["weather_code"]
            self._resumen = {
                "temp": round(cur["temperature_2m"]),
                "max": round(dia["temperature_2m_max"][0]),
                "min": round(dia["temperature_2m_min"][0]),
                "lluvia": round(dia["precipitation_probability_max"][0] or 0),
                "estado": next((e for cs, e in _ESTADOS if codigo in cs), "nublado"),
                "es_dia": bool(cur["is_day"]),
            }
            self._resumen_ts = time.time()
        except Exception as e:
            print(f"❌ Error obteniendo el tiempo para el reloj: {e}")
        return self._resumen

    def _geocodificar(self, ciudad: str) -> dict | None:
        """Convierte un nombre de ciudad español en coordenadas."""
        try:
            params = {"name": ciudad, "count": 1, "language": "es"}
            r = requests.get(self.geo_url, params=params, timeout=5)
            data = r.json()
            results = data.get("results", [])
            if results:
                return {
                    "lat": results[0]["latitude"],
                    "lon": results[0]["longitude"],
                    "nombre": results[0].get("name", ciudad)
                }
        except Exception as e:
            print(f"❌ Error geocodificando {ciudad}: {e}")
        return None

    def _obtener_clima_raw(self, lat: float, lon: float, dias: int = 1, incluir_actual: bool = False) -> dict:
        """Obtiene pronóstico. Si incluir_actual=True, añade current_weather."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode",
            "timezone": "Europe/Madrid",
            "forecast_days": min(dias, 7)
        }
        if incluir_actual:
            params["current_weather"] = True

        try:
            r = requests.get(self.base_url, params=params, timeout=5)
            return r.json()
        except Exception as e:
            print(f"❌ Error obteniendo clima: {e}")
            return {}

    def describir_clima(self, ciudad: str = None, cuando: str = "ahora") -> str:
        # --- Coordenadas ---
        if ciudad:
            geo = self._geocodificar(ciudad)
            if not geo:
                return f"No he encontrado {ciudad} en el mapa."
            lat, lon, nombre = geo["lat"], geo["lon"], geo["nombre"]
        else:
            (lat, lon), nombre = ALCORCON, "Alcorcón"

        # --- Interpretar "cuando" ---
        dias = 1
        dia_idx = 0
        incluir_actual = False       # ← siempre inicializada

        if cuando in ("ahora", "hoy"):
            dias, dia_idx = 1, 0
            incluir_actual = True
        elif cuando == "mañana":
            dias, dia_idx = 2, 1
        elif cuando == "pasado mañana":
            dias, dia_idx = 3, 2
        elif "finde" in cuando or "fin de semana" in cuando:
            dias, dia_idx = 3, None
        elif "noche" in cuando:
            dias, dia_idx = 1, 0
        # cualquier otro valor queda con los defaults (hoy, sin actual)

        # --- Obtener datos ---
        data = self._obtener_clima_raw(lat, lon, dias, incluir_actual)

        # --- Respuesta con temperatura actual (si se pidió) ---
        if incluir_actual and "current_weather" in data:
            cw = data["current_weather"]
            temp = cw["temperature"]
            codigo = cw["weathercode"]
            desc = self._codigo_a_texto(codigo)
            return f"Ahora mismo en {nombre} hace {temp}°C, está {desc}."

        # --- Respuesta con pronóstico diario ---
        daily = data.get("daily", {})
        if not daily:
            return "No he podido consultar el clima ahora mismo."

        if dia_idx is not None:
            t_max = daily["temperature_2m_max"][dia_idx]
            t_min = daily["temperature_2m_min"][dia_idx]
            codigo = daily["weathercode"][dia_idx]
            desc = self._codigo_a_texto(codigo)
            return f"En {nombre} {cuando} hará entre {t_min:.0f}°C y {t_max:.0f}°C, {desc}."
        else:
            # finde → varios días
            nombres_dias = ["hoy", "mañana", "pasado mañana"]
            frases = []
            for i in range(min(len(daily["time"]), 3)):
                t_max = daily["temperature_2m_max"][i]
                t_min = daily["temperature_2m_min"][i]
                codigo = daily["weathercode"][i]
                desc = self._codigo_a_texto(codigo)
                frases.append(f"{nombres_dias[i]}: {t_min:.0f}°C – {t_max:.0f}°C, {desc}")
            return f"Pronóstico para {nombre}:\n" + "\n".join(frases)

    def _codigo_a_texto(self, codigo: int) -> str:
        descripciones = {
            0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
            3: "nublado", 45: "niebla", 48: "escarcha",
            51: "llovizna ligera", 53: "llovizna", 55: "llovizna intensa",
            61: "lluvia ligera", 63: "lluvia", 65: "lluvia intensa",
            71: "nieve ligera", 73: "nieve", 75: "nieve intensa",
            95: "tormenta", 96: "tormenta con granizo", 99: "tormenta con granizo intenso"
        }
        return descripciones.get(codigo, "con condiciones variables")