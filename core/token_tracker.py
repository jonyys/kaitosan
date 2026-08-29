import json
import os
from datetime import datetime

TRACKER_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "token_usage.json"
)

class TokenTracker:
    def __init__(self):
        self._cargar()

    def _cargar(self):
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {"date": "", "tokens": {}, "total_audio_seconds": 0, "monthly": {}}

        hoy = datetime.now().strftime("%Y-%m-%d")
        mes = hoy[:7]
        monthly = data.get("monthly", {})

        # Reset diario: tokens y audio de Groq se ponen a cero cada día,
        # pero el acumulado MENSUAL (Azure) sobrevive al cambio de día.
        if data.get("date") != hoy:
            data = {"date": hoy, "tokens": {}, "total_audio_seconds": 0, "monthly": monthly}

        # Solo conservamos el mes en curso: al cambiar de mes el contador
        # de Azure arranca de nuevo en 0.
        data["monthly"] = {mes: monthly.get(mes, {})}
        self.data = data

    def _guardar(self):
        with open(TRACKER_FILE, "w") as f:
            json.dump(self.data, f)

    def añadir_tokens(self, modelo: str, tokens: int) -> dict:
        self._cargar()
        if "tokens" not in self.data:
            self.data["tokens"] = {}
        self.data["tokens"][modelo] = self.data["tokens"].get(modelo, 0) + tokens
        self._guardar()
        return self.data

    def añadir_audio(self, segundos: int) -> int:
        self._cargar()
        if "total_audio_seconds" not in self.data:
            self.data["total_audio_seconds"] = 0
        self.data["total_audio_seconds"] += segundos
        self._guardar()
        return self.data["total_audio_seconds"]

    # ── Azure Speech: cuota mensual de pronunciación ─────────────────────────
    def añadir_azure_stt(self, segundos: int) -> int:
        """Suma segundos de audio enviados a Azure este mes. Devuelve el acumulado."""
        self._cargar()
        mes = self.data["date"][:7]
        bucket = self.data["monthly"].setdefault(mes, {})
        bucket["azure_stt_seconds"] = bucket.get("azure_stt_seconds", 0) + segundos
        self._guardar()
        return bucket["azure_stt_seconds"]

    def azure_stt_segundos_mes(self) -> int:
        self._cargar()
        mes = self.data["date"][:7]
        return self.data["monthly"].get(mes, {}).get("azure_stt_seconds", 0)

    def consultar(self) -> dict:
        self._cargar()
        return self.data
