"""
Test de herramientas de Kaito (excluye alarma y recordatorio).

Ejecutar desde la raíz del proyecto:
    python -m tests.test_herramientas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

VERDE = "\033[92m"
ROJO  = "\033[91m"
RESET = "\033[0m"
NEGRITA = "\033[1m"

resultados = []


def ok(nombre, detalle=""):
    msg = f"{VERDE}✅ {nombre}{RESET}"
    if detalle:
        msg += f"\n   → {detalle}"
    print(msg)
    resultados.append((nombre, True, detalle))


def fallo(nombre, detalle=""):
    msg = f"{ROJO}❌ {nombre}{RESET}"
    if detalle:
        msg += f"\n   → {detalle}"
    print(msg)
    resultados.append((nombre, False, detalle))


def seccion(titulo):
    print(f"\n{NEGRITA}── {titulo} ──{RESET}")


# ──────────────────────────────────────────────
# 1. HORA
# ──────────────────────────────────────────────
seccion("Hora actual")
try:
    hora = datetime.now().strftime("%H:%M")
    assert len(hora) == 5 and ":" in hora
    ok("obtener_hora", hora)
except Exception as e:
    fallo("obtener_hora", str(e))


# ──────────────────────────────────────────────
# 2. FECHA
# ──────────────────────────────────────────────
seccion("Fecha actual")
try:
    fecha = datetime.now().strftime("%d de %B de %Y")
    assert len(fecha) > 5
    ok("obtener_fecha", fecha)
except Exception as e:
    fallo("obtener_fecha", str(e))


# ──────────────────────────────────────────────
# 3. CLIMA
# ──────────────────────────────────────────────
seccion("Clima")
try:
    from ai.skills.weather import WeatherSkill
    weather = WeatherSkill()

    resultado = weather.describir_clima(ciudad="Collado Mediano", cuando="ahora")
    if resultado and "°C" in resultado:
        ok("obtener_clima (ahora)", resultado)
    else:
        fallo("obtener_clima (ahora)", f"Respuesta inesperada: {resultado}")

    resultado_manana = weather.describir_clima(ciudad="Madrid", cuando="mañana")
    if resultado_manana and "°C" in resultado_manana:
        ok("obtener_clima (mañana)", resultado_manana)
    else:
        fallo("obtener_clima (mañana)", f"Respuesta inesperada: {resultado_manana}")

except Exception as e:
    fallo("obtener_clima", str(e))


# ──────────────────────────────────────────────
# 4. BÚSQUEDA EN INTERNET
# ──────────────────────────────────────────────
seccion("Búsqueda en internet (Tavily)")
try:
    import requests
    from core.config import TAVILY_API_KEY

    if not TAVILY_API_KEY:
        fallo("buscar_internet", "TAVILY_API_KEY no está definida en config")
    else:
        print(f"   API key: ...{TAVILY_API_KEY[-6:]}")
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"query": "temperatura Madrid hoy", "search_depth": "basic",
                  "include_answer": True, "max_results": 3},
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}",
                     "Content-Type": "application/json"},
            timeout=10
        )
        print(f"   HTTP status: {resp.status_code}")
        data = resp.json()

        if resp.status_code != 200:
            fallo("buscar_internet", f"HTTP {resp.status_code} — {data.get('message', data.get('detail', str(data)))}")
        elif data.get("answer") or data.get("results"):
            from ai.search_provider import SearchProvider
            resultado = SearchProvider().buscar("temperatura Madrid hoy")
            ok("buscar_internet", resultado[:250] + ("..." if len(resultado) > 250 else ""))
        else:
            fallo("buscar_internet", f"Respuesta vacía. JSON recibido: {str(data)[:300]}")

except Exception as e:
    fallo("buscar_internet", str(e))


# ──────────────────────────────────────────────
# 5. BÚSQUEDA EN HISTORIAL
# ──────────────────────────────────────────────
seccion("Búsqueda en historial")
try:
    from core.memory import Memory, DB_PATH
    print(f"   BD: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"   {ROJO}⚠ La base de datos no existe en esta máquina (ejecuta este test en la Raspberry Pi){RESET}")
        resultados.append(("buscar_en_historial", None, "SKIP"))
    else:
        memory = Memory()
        resultado = memory.buscar_en_historial(["japonés"])
        if resultado is not None:
            ok("buscar_en_historial", str(resultado)[:200] if resultado else "Sin resultados para 'japonés' (normal si la BD está vacía)")
        else:
            fallo("buscar_en_historial", "Devolvió None")

except AttributeError:
    fallo("buscar_en_historial", "Memory no tiene método 'buscar_en_historial' — revisar core/memory.py")
except Exception as e:
    fallo("buscar_en_historial", str(e))


# ──────────────────────────────────────────────
# 6. PROGRESO DE JAPONÉS
# ──────────────────────────────────────────────
seccion("Progreso de japonés")
try:
    from core.japanese_memory import JapaneseMemory
    from core.memory import DB_PATH
    print(f"   BD: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"   {ROJO}⚠ La base de datos no existe en esta máquina (ejecuta este test en la Raspberry Pi){RESET}")
        resultados.append(("consultar_progreso_japones", None, "SKIP"))
    else:
        jap = JapaneseMemory(DB_PATH)
        resultado = jap.obtener_perfil_completo()
        if resultado is not None:
            ok("consultar_progreso_japones", str(resultado)[:300] if resultado else "Sin datos todavía (no se ha practicado japonés aún)")
        else:
            fallo("consultar_progreso_japones", "Devolvió None")

except AttributeError:
    fallo("consultar_progreso_japones", "JapaneseMemory no tiene método 'obtener_perfil_completo' — revisar core/japanese_memory.py")
except Exception as e:
    fallo("consultar_progreso_japones", str(e))


# ──────────────────────────────────────────────
# RESUMEN
# ──────────────────────────────────────────────
print(f"\n{NEGRITA}{'─'*40}{RESET}")
ejecutados = [(n, v, d) for n, v, d in resultados if v is not None]
skipped    = [(n, v, d) for n, v, d in resultados if v is None]
pasados    = sum(1 for _, v, _ in ejecutados if v)
fallidos   = sum(1 for _, v, _ in ejecutados if not v)

print(f"{NEGRITA}Resultado: {pasados}/{len(ejecutados)} OK{RESET}", end="")
if skipped:
    print(f"  (omitidos: {len(skipped)})", end="")
if fallidos:
    print(f"  {ROJO}({fallidos} fallido{'s' if fallidos > 1 else ''}){RESET}")
elif not skipped:
    print(f"  {VERDE}✨ Todo funciona{RESET}")
else:
    print()

if fallidos:
    print(f"\n{ROJO}Herramientas con problemas:{RESET}")
    for nombre, ok_val, detalle in ejecutados:
        if not ok_val:
            print(f"  • {nombre}: {detalle}")

if skipped:
    print(f"\n⚠  Omitidos (requieren la Raspberry Pi):")
    for nombre, _, _ in skipped:
        print(f"  • {nombre}")
