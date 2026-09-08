import json
import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_TOKENS = 300
MAX_TOKENS_SENSEI = 2048       # profesor, turno normal (razonamiento gpt-oss + respuesta)
MAX_TOKENS_EXPLICACION = 3072  # profesor, turno de desglose gramatical
TEMPERATURE = 0.7
TEMPERATURE_SENSEI = 0.3  # respuestas del profesor — más deterministas para seguir las reglas

# Modelo del modo sensei. `MODEL_SENSEI` (env) solo se usa como semilla al
# arrancar; en caliente, al activar el modo, se resuelve contra la lista viva de
# api.groq.com/v1/models con MODELOS_SENSEI_PREFERENCIA (ver
# system_settings.modelo_sensei_efectivo). Así el equipo de Laura no depende de
# tocar el .env cuando Groq retira o renombra un modelo.
MODEL_SENSEI = os.getenv("MODEL_SENSEI", "openai/gpt-oss-120b")
REASONING_EFFORT_SENSEI = os.getenv("REASONING_EFFORT_SENSEI", "low")

# Frases que sacan del modo sensei. Se comprueban por subcadena sobre el texto
# en minúsculas. Las usa brain._responder y también speech_to_text para dejar
# salir a Laura aunque el turno esté en modo "repite conmigo" (si no, su español
# iría a Azure ja-JP, saldría como katakana sin sentido y el trigger no saltaría).
TRIGGERS_SALIR_SENSEI = [
    "salir del modo sensei", "sal del modo sensei", "modo sensei off",
    "salir del modo", "sal del modo", "desactivar modo", "desctivar", "desactiva",
]

# Turnos del sensei: por defecto van a Groq (gpt-oss-120b) — más rápido. Pon
# SENSEI_TURNOS_GEMINI=1 para que vayan primero a Gemini (con rotación de
# modelos ante rate limit) y Groq quede solo de reserva.
SENSEI_TURNOS_GEMINI = os.getenv("SENSEI_TURNOS_GEMINI", "0").strip().lower() in (
    "1", "true", "yes", "on",
)

# OpenRouter — proveedor de los TURNOS del sensei (no del extractor). El prompt
# del profesor es grande y ahogaba el tier gratis de Groq/Gemini por límite de
# tokens/min; OpenRouter es pago-por-uso y da acceso a modelos fuertes en seguir
# instrucciones (Qwen, GLM) que es lo que más importa aquí. Con
# OPENROUTER_API_KEY vacía se usa el camino anterior (Gemini/Groq) sin cambios.
# La lista se recorre en orden hasta el primero que responda (rate limit / caído
# → siguiente). El extractor de cierre (strict) NUNCA pasa por aquí.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODELOS_SENSEI = [
    m.strip() for m in os.getenv(
        "OPENROUTER_MODELOS_SENSEI",
        "qwen/qwen3.8-flash,z-ai/glm-5.3-flash,openai/gpt-oss-120b",
    ).split(",") if m.strip()
]

# Orden de preferencia para el modo sensei: se coge el PRIMERO que esté vivo en
# la API. Si ninguno lo está, el primer modelo de chat con contexto suficiente
# que devuelva la lista. gpt-oss va primero porque los qwen del tier gratis dan
# rate limit (429) en casi todos los turnos del sensei (contexto grande); si se
# sube el plan de Groq, subir aquí los qwen.
MODELOS_SENSEI_PREFERENCIA = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
]

# Modelos de reserva (si el principal da rate limit / cae) y modelos aptos para
# tool calls. Son la **semilla de fábrica**: la selección guardada en
# Ajustes → Modelos (clave `groq_models` de app_settings) la sobrescribe.
MODELOS_ALTERNATIVOS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
]
MODELOS_TOOLS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "groq/compound",
]


def groq_seleccion() -> dict:
    """Selección **efectiva** de modelos de Groq (PLAN_AJUSTES §2.1).

    Devuelve `{principal, sensei, alternativos:[...], tools:[...]}`. Lee la clave
    `groq_models` de `app_settings` (la que guarda Ajustes → Modelos) y, para
    cada campo que falte o esté vacío, usa el valor de fábrica de este módulo.
    Nunca lanza: ante cualquier problema devuelve los valores de fábrica.
    """
    fabrica = {
        "principal": DEFAULT_MODEL,
        "sensei": MODEL_SENSEI,
        "alternativos": list(MODELOS_ALTERNATIVOS),
        "tools": list(MODELOS_TOOLS),
    }
    try:
        from core.settings_store import settings_get
        crudo = settings_get("groq_models")
        guardado = json.loads(crudo) if crudo else {}
    except Exception:  # noqa: BLE001 — config nunca debe romper por esto
        return fabrica
    if not isinstance(guardado, dict):
        return fabrica

    sel = dict(fabrica)
    for campo in ("principal", "sensei"):
        v = guardado.get(campo)
        if isinstance(v, str) and v.strip():
            sel[campo] = v.strip()
    for campo in ("alternativos", "tools"):
        v = guardado.get(campo)
        if isinstance(v, list):
            limpio = list(dict.fromkeys(
                m.strip() for m in v if isinstance(m, str) and m.strip()
            ))
            if limpio:
                sel[campo] = limpio
    return sel

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Modelos de Gemini: semilla de fábrica. La selección guardada en
# Ajustes → Modelos (clave `gemini_models` de app_settings) la sobrescribe.
#  - sensei    → modelo primario de los turnos del modo sensei.
#  - reservas  → modelos Gemini a los que rotar (en orden) si el primario da
#                rate limit, ANTES de caer a Groq. El free tier limita a ~20
#                req/día POR MODELO, así que rotar entre varios flash multiplica
#                el aforo diario.
#  - extractor → extracción de cierre de sesión (JSON).
GEMINI_MODEL_SENSEI = os.getenv("GEMINI_MODEL_SENSEI", "gemini-3.6-flash")
GEMINI_MODELOS_RESERVA = ["gemini-3.7-flash", "gemini-3.5-flash"]
GEMINI_MODEL_EXTRACTOR = os.getenv("GEMINI_MODEL_EXTRACTOR", "gemini-3.6-flash")


def gemini_seleccion() -> dict:
    """Selección efectiva de modelos de Gemini: `{sensei, reservas, extractor}`.

    Lee `gemini_models` de `app_settings`; cada campo que falte usa el valor de
    fábrica de este módulo. `reservas` puede quedar en `[]` a propósito. Nunca lanza.
    """
    fabrica = {
        "sensei": GEMINI_MODEL_SENSEI,
        "reservas": list(GEMINI_MODELOS_RESERVA),
        "extractor": GEMINI_MODEL_EXTRACTOR,
    }
    try:
        from core.settings_store import settings_get
        crudo = settings_get("gemini_models")
        guardado = json.loads(crudo) if crudo else {}
    except Exception:  # noqa: BLE001 — config nunca debe romper por esto
        return fabrica
    if not isinstance(guardado, dict):
        return fabrica
    sel = dict(fabrica)
    for campo in ("sensei", "extractor"):
        v = guardado.get(campo)
        if isinstance(v, str) and v.strip():
            sel[campo] = v.strip()
    r = guardado.get("reservas")
    if isinstance(r, list):
        sel["reservas"] = list(dict.fromkeys(
            m.strip() for m in r if isinstance(m, str) and m.strip()
        ))
    return sel


# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_key")
# Usuario/contraseña del panel: solo semilla inicial. En el primer arranque se
# copian (con hash) a la tabla app_settings; a partir de ahí manda la BD y se
# cambian desde Ajustes. Ver core/settings_store.py.
ADMIN_USER = os.getenv("ADMIN_USER", "laura")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kaito123")

# Sensei — ritmo de introducción
MAX_ITEMS_NUEVOS = 2   # ítems (estado 'nuevo') que el can-do activo introduce por sesión
# Fase 09: el profesor ya no orquesta por cola SRS. La cola `due` de vocab/gram
# solo la mueve el juego web (Bloque IV) y el SRS de kanji; el profesor no la
# toca (`due_count` de resumen_perfil vale solo para eso). THROTTLE_DUE ya no
# frena ítems nuevos: hoy es solo el tope de la lista de puntos débiles del FOCO.
THROTTLE_DUE = 12
# Fase 09: chequeo de óxido — cada cuántas sesiones el FOCO incluye una muestra
# de vocabulario ya 'sabido' de unidades pasadas. Knob, se afina con datos.
CHEQUEO_OXIDO_CADA = 5

# Segundos de espera antes de lanzar la extracción al cerrar la sesión. La
# llamada del extractor es grande y, si va pegada al turno de despedida, las dos
# caen en la misma ventana de tokens/min de Groq y salta el rate limit (se
# perdía la calificación de can-dos). Esperar deja que la ventana se vacíe.
EXTRACCION_RETRASO_SEG = int(os.getenv("EXTRACCION_RETRASO_SEG", "45"))

# Segundos entre las llamadas internas de la extracción (resumen básico →
# extractor → reintento). Sin esto se disparan 2-3 llamadas en la misma ventana
# de tokens/min y el modelo fuerte da 429 en todas: la extracción cae al modelo
# de reserva (o falla) y el progreso de la sesión se pierde o se corrompe.
EXTRACCION_PAUSA_LLAMADAS_SEG = int(os.getenv("EXTRACCION_PAUSA_LLAMADAS_SEG", "18"))

# Nivel de inmersión (1→4): cuánto japonés habla Kaito. Se calcula solo a partir
# del vocabulario dominado (learned + mastered); estos son los umbrales de salto.
# NIVEL_INMERSION=3 en el entorno lo fija a mano para probar.
# Knob: pendiente de afinar con el ritmo real del juego web (Bloque IV) — Laura
# acumulará 'sabido' más rápido, así que casi seguro suben. No se cambian ahora,
# se ajustan con datos de uso real.
NIVEL_INMERSION_UMBRALES = (15, 40, 80)
NIVEL_INMERSION_FORZADO = int(os.getenv("NIVEL_INMERSION", "0")) or None

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