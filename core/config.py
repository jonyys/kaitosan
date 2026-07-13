import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 300
TEMPERATURE = 0.7

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kaito123")

# Busqueda en internet
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")