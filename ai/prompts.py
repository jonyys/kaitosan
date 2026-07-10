import os

def cargar_prompt(nombre: str) -> str:
    """Carga un prompt desde ai/prompts/"""
    ruta = os.path.join(
        os.path.dirname(__file__),
        "prompts",
        f"{nombre}.txt"
    )
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Prompt '{nombre}' no encontrado en {ruta}")
        return ""

def construir_system_prompt(contexto_memoria: str = "") -> str:
    """
    Construye el system prompt completo
    combinando el base con la memoria
    """
    base = cargar_prompt("system_prompt")

    if contexto_memoria:
        return f"{base}\n\n{contexto_memoria}"

    return base

SYSTEM_PROMPT = cargar_prompt("system_prompt")