import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_TOKENS = 300
MAX_TOKENS_SENSEI = 500   # respuestas del profesor — más largas que el router/tareas
TEMPERATURE = 0.7
TEMPERATURE_SENSEI = 0.3  # respuestas del profesor — más deterministas para seguir las reglas

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kaito123")

# Sensei — ritmo de introducción
MAX_ITEMS_NUEVOS = 2   # ítems nuevos por sesión (configurable hasta 3)
THROTTLE_DUE = 12      # si hay ≥ N repasos vencidos, no introducir ítems nuevos

# Busqueda en internet
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Azure Speech — evaluación de pronunciación en modo sensei (tier gratuito F0)
# F0 da 5 h de audio STT/pronunciación al mes. Dejamos margen: ~4 h 40 min.
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westeurope")
AZURE_STT_LIMITE_SEG_MES = int(os.getenv("AZURE_STT_LIMITE_SEG_MES", "16800"))
# Por defecto la pronunciación solo se evalúa en modo sensei estructurado.
# Ponlo a true para evaluarla también en el modo charla (gasta cuota más rápido).
AZURE_PRON_EN_CHARLA = os.getenv("AZURE_PRON_EN_CHARLA", "false").strip().lower() in (
    "1", "true", "yes", "si", "sí", "on",
)