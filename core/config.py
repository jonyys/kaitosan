import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_TOKENS = 300
MAX_TOKENS_SENSEI = 1024  # profesor: margen para razonamiento interno + respuesta (gpt-oss)
TEMPERATURE = 0.7
TEMPERATURE_SENSEI = 0.3  # respuestas del profesor — más deterministas para seguir las reglas

# Modelo y esfuerzo de razonamiento del modo sensei (configurable por si gpt-oss
# se enrolla: p.ej. MODEL_SENSEI=qwen/qwen3.8-27b).
MODEL_SENSEI = os.getenv("MODEL_SENSEI", "openai/gpt-oss-120b")
REASONING_EFFORT_SENSEI = os.getenv("REASONING_EFFORT_SENSEI", "low")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_key")
# Usuario/contraseña del panel: solo semilla inicial. En el primer arranque se
# copian (con hash) a la tabla app_settings; a partir de ahí manda la BD y se
# cambian desde Ajustes. Ver core/settings_store.py.
ADMIN_USER = os.getenv("ADMIN_USER", "laura")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kaito123")

# Sensei — ritmo de introducción
MAX_ITEMS_NUEVOS = 2   # ítems nuevos por sesión (configurable hasta 3)
THROTTLE_DUE = 12      # si hay ≥ N repasos vencidos, no introducir ítems nuevos

# Busqueda en internet
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# TTS: pausa (segundos) entre cada trozo de voz al alternar español/japonés.
# Súbelo si lo dice demasiado seguido, bájalo (o 0) si hay huecos largos.
TTS_PAUSA_SEGMENTOS = float(os.getenv("TTS_PAUSA_SEGMENTOS", "0.3"))
# Silencio (segundos) al principio del todo, para que no arranque de golpe.
TTS_SILENCIO_INICIAL = float(os.getenv("TTS_SILENCIO_INICIAL", "0.15"))

# Audio: subcadena para forzar el dispositivo de salida/entrada por nombre.
# Vacío = autodetección (salida: hifiberry → G435; entrada: AB17X → G435).
# Ej.: AUDIO_OUTPUT_HINT=G435 para escuchar por los cascos.
AUDIO_OUTPUT_HINT = os.getenv("AUDIO_OUTPUT_HINT", "").strip()
AUDIO_INPUT_HINT = os.getenv("AUDIO_INPUT_HINT", "").strip()

# Azure Speech — evaluación de pronunciación en modo sensei (tier gratuito F0)
# F0 da 5 h de audio STT/pronunciación al mes. Dejamos margen: ~4 h 40 min.
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westeurope")
AZURE_STT_LIMITE_SEG_MES = int(os.getenv("AZURE_STT_LIMITE_SEG_MES", "16800"))
# Vuelca en consola el JSON de evaluación que devuelve Azure (para depurar).
AZURE_PRON_DEBUG = os.getenv("AZURE_PRON_DEBUG", "false").strip().lower() in (
    "1", "true", "yes", "si", "sí", "on",
)
# Tolerancia de la evaluación de pronunciación (Azure ja-JP es duro con la 'r'):
#  - una palabra solo se marca como fallo si baja de este umbral (o es Omission/Insertion)
#  - a partir de este global (PronScore) sin fallos reales, el veredicto es BIEN
AZURE_PRON_UMBRAL_PALABRA = int(os.getenv("AZURE_PRON_UMBRAL_PALABRA", "40"))
AZURE_PRON_UMBRAL_BIEN = int(os.getenv("AZURE_PRON_UMBRAL_BIEN", "75"))
# Por defecto la pronunciación solo se evalúa en modo sensei estructurado.
# Ponlo a true para evaluarla también en el modo charla (gasta cuota más rápido).
AZURE_PRON_EN_CHARLA = os.getenv("AZURE_PRON_EN_CHARLA", "false").strip().lower() in (
    "1", "true", "yes", "si", "sí", "on",
)