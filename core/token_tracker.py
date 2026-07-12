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
            data = {"date": "", "total_tokens": 0, "total_audio_seconds": 0}

        hoy = datetime.now().strftime("%Y-%m-%d")
        if data["date"] != hoy:
            data = {"date": hoy, "total_tokens": 0, "total_audio_seconds": 0}

        self.data = data

    def _guardar(self):
        with open(TRACKER_FILE, "w") as f:
            json.dump(self.data, f)

    def añadir_tokens(self, tokens: int) -> int:
        self._cargar()
        self.data["total_tokens"] += tokens
        self._guardar()
        return self.data["total_tokens"]

    def añadir_audio(self, segundos: int) -> int:
        self._cargar()
        self.data["total_audio_seconds"] += segundos
        self._guardar()
        return self.data["total_audio_seconds"]

    def consultar(self) -> dict:
        self._cargar()
        return self.data