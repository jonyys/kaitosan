import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "llama-3.3-70b-versatile"
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