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
            data = {"date": "", "tokens": {}, "total_audio_seconds": 0}

        hoy = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") != hoy:
            data = {"date": hoy, "tokens": {}, "total_audio_seconds": 0}

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

    def consultar(self) -> dict:
        self._cargar()
        return self.data