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


SYSTEM_PROMPT = cargar_prompt("system_prompt")
ROUTER_PROMPT = cargar_prompt("router_prompt")
