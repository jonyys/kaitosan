"""ProfesorJapones: el modo sensei.

El código decide qué toca y comprueba; el LLM solo habla. Cada can-do (datos en
ai/sensei/candos_clase.json) pasa por fases fijas:
  presentar → practicar (2 aciertos) → tarea (2 aciertos) → conseguido → siguiente.
(Si no ha fallado ni una vez en el can-do, basta 1 acierto en práctica y 1 en tarea.)
Orden de la sesión (_siguiente): primero los pendientes (conseguidos una vez otro
día: repaso, solo tarea en una situación nueva), luego los nuevos de la unidad (y
de la siguiente), con 1 repaso de algo ya dominado cada 4 nuevos. Tras 5 intentos
seguidos sin acierto, Kaito da un modelo y se pasa a lo siguiente.
Las conjugaciones (て, た) las comprueba ai/sensei/conjugar.py y el resto
ai/sensei/clase.py, sin LLM. Al modelo le llega un prompt corto
(ai/prompts/sensei_clase.txt) y una INSTRUCCIÓN por turno.

ponytail: sin frase objetivo para Azure (Laura produce frases suyas, no repite):
la evaluación de pronunciación no tiene con qué comparar.
"""

import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ai.prompts import cargar_prompt
from ai.sensei.clase import (
    ACIERTOS_ANTIGUO,
    cortar_frases,
    ACIERTOS_PRACTICA,
    ACIERTOS_SIN_FALLOS,
    ACIERTOS_TAREA,
    FALLOS_MAX,
    LIBRE_TURNOS_TEMA,
    PEDIR_FRASE,
    NUEVOS_POR_ANTIGUO,
    errores,
    presentar,
    que_hacer,
    tarea,
    tarea_nueva,
    MOTIVOS,
    juez_cumple,
    usa_patron,
)
from ai.sensei.curriculum import CURRICULUM, unidad_actual
from ai.sensei.kana import a_kana, bloques_japones, normalizar_bloques_jp, normalizar_japones, tiene_espanol
from core.config import (
    EXTRACCION_PAUSA_LLAMADAS_SEG,
    EXTRACCION_RETRASO_SEG,
    MAX_TOKENS_EXPLICACION,
    NOMBRES_PROPIOS,
    REASONING_EFFORT_SENSEI,
    TEMPERATURE_SENSEI,
    THROTTLE_DUE,
)

MAX_PALABRAS_VISTAS = 60  # tope de la lista «palabras que Laura ya ha visto» que va en cada turno
MAX_TURNOS = 8  # pares user/assistant conservados en el contexto del LLM
# Laura dice que no sabe / no se acuerda / pide ayuda (en español): hay que ayudarla.
_RE_NO_SE = re.compile(
    r"\bno (lo )?s[eé]\b|no me acuerdo|no recuerdo|no entiendo|expl[ií]ca|ay[uú]da|"
    r"c[oó]mo se (hace|usa)|no s[eé] c[oó]mo|"
    # Quejas de que le pide demasiado («sin habérmelo enseñado», «muchas cosas»): igual.
    r"ense[ñn]ad|muchas cosas|pidiendo mucho|demasiad|dif[ií]cil", re.IGNORECASE)  # «cómo se dice X» es solo vocabulario: no cuenta
# Línea final que el LLM añade para la pizarra: «PIZARRA: kana = significado; kana = significado».
_RE_PIZARRA = re.compile(r"PIZARRA\s*:", re.IGNORECASE)


def _texto_pizarra(entradas):
    """«kana = significado; kana = significado» de una lista [{"jp","es"}] ('' si está vacía)."""
    return "; ".join(f"{e['jp']} = {e['es']}" if e.get("es") else e["jp"] for e in entradas or [])


def _sin_pizarra(texto):
    """Un mensaje del historial sin su línea PIZARRA (para el juez y para el extractor)."""
    return _RE_PIZARRA.split(texto or "", 1)[0].strip()
# Laura quiere pasar a lo siguiente / dice que ya lo sabe: no hay que insistir.
_RE_SIGUIENTE = re.compile(
    r"pas(a|o|ar|emos)( a| con)? (lo|el|la) siguiente|vamos a lo siguiente|"
    r"siguiente (tema|lecci[oó]n|cosa|ejercicio)|\bya (me )?lo s[eé]\b|"
    r"cambia(r|mos)? de (tema|lecci[oó]n)|otra (cosa|lecci[oó]n)", re.IGNORECASE)
# Vocabulario del temario por forma escrita (jp y lectura, sin 〜 ni glosas): sirve para saber qué
# palabras dijo Kaito. ponytail: solo palabras de 2+ kana y como token entero (con o sin partícula
# pegada); las de 1 kana (き, め…) no se detectan.
_PARTICULAS = "をはがにでとものへ"
_RE_BLOQUE_JP = re.compile(r"【(.*?)】")
_VOCAB_POR_FORMA, _CANONICO = {}, {}
for _u in CURRICULUM:
    for _it in _u.get("items", []):
        if _it.get("kind") != "vocabulario" or _it.get("tipo") == "kanji":
            continue
        for _f in (_it.get("jp") or "", _it.get("reading") or ""):
            for _s in re.sub(r"[（(].*?[)）]", "", _f).replace("〜", "").replace("～", "").split(";"):
                _s = _s.strip()
                if len(_s) >= 2:
                    _VOCAB_POR_FORMA.setdefault(_s, _it)
                    if _s != _it["jp"]:
                        _CANONICO.setdefault(_s, _it["jp"])


def _vocab_dicho(mensajes):
    """Palabras del temario que Kaito dijo en sus bloques 【】 durante la clase, sin repetir.
    Se salta el saludo de apertura (lo anterior al primer mensaje de Laura)."""
    primero = next((i for i, m in enumerate(mensajes) if m["role"] == "user"), len(mensajes))
    vistas = {}
    for m in mensajes[primero:]:
        if m["role"] != "assistant":
            continue
        for bloque in _RE_BLOQUE_JP.findall(m["content"]):
            for tok in re.split(r"[\s、。，,．.！!？?・「」]+", bloque):
                # Primero el token entero («こんばんは» no es «こんばん» + は); si no, sin la partícula.
                it = _VOCAB_POR_FORMA.get(tok) or (
                    _VOCAB_POR_FORMA.get(tok[:-1]) if tok[-1:] and tok[-1] in _PARTICULAS else None)
                if it:
                    vistas.setdefault(it["jp"], it)
    return list(vistas.values())


# Todos los can-dos con datos de clase, por id (la cola puede cruzar unidades).
_POR_ID = {cd["id"]: cd for u in CURRICULUM for cd in u.get("can_dos", [])
           if cd.get("explicacion") and cd.get("tarea")}

# Saludo/despedida de apertura: expresión japonesa CORTA + el resto en español,
# para que se entienda sea cual sea el nivel (una frase japonesa entera aquí es
# justo lo que el alumno principiante no pilla).
SALUDOS = [
    "Modo Sensei activado! 【こんにちは】, Laura. ¿Qué tal estás?",
    "Modo Sensei activado! 【おはよう】, Laura. ¿Lista para practicar japonés?",
    "Modo Sensei activado! 【こんばんは】, Laura. ¿Cómo va el día?",
    "Modo Sensei activado! 【やあ】, Laura. ¿Empezamos?",
    "Modo Sensei activado! 【こんにちは】, Laura. Vamos a repasar un poco de japonés.",
]

DESPEDIDAS = [
    "【またね】, Laura.",
    "【じゃあね】, Laura. Nos vemos pronto.",
    "【おつかれさま】. Hasta la próxima.",
    "【さようなら】, Laura. Hasta otro día.",
    "【バイバイ】, Laura. Cuídate.",
]


# Cualquier carácter japonés.
_RE_JP_CHAR = re.compile(r'[぀-ゟ゠-ヿ一-鿿]')

# Fase 17 — arco de sesión. Palabras con que Laura suele despedirse; heurística
# a propósito simple (el gate real es calentamiento vs foco por turno).
_DESPEDIDAS_LAURA = (
    "adiós", "adios", "hasta luego", "hasta la próxima", "hasta la proxima",
    "hasta mañana", "hasta manana", "hasta la semana", "me voy", "nos vemos",
    "lo dejamos", "lo dejo aquí", "lo dejo aqui", "lo dejo por hoy",
    "ya es suficiente", "suficiente por hoy", "ya está bien por hoy",
)


# Cierre de las instrucciones que encadenan dos cosas (felicitar + abrir lo nuevo).
_UNA_PETICION = " Todo el turno acaba con UNA sola petición (la de lo nuevo); nada de «luego» ni segunda tarea."

_EXTRACCION_PROMPT = cargar_prompt("extraccion_sesion")


class ProfesorJapones:

    def __init__(self, jap_memory, provider, memory, socketio):
        """
        jap_memory — JapaneseMemory (capa de datos japonés + SRS)
        provider   — proveedor LLM (ver ai/sensei_provider.py)
        memory     — core.memory.Memory (perfil general de Laura)
        socketio   — instancia Flask-SocketIO para emitir eventos
        """
        self.jap_memory = jap_memory
        self.provider = provider
        self.memory = memory
        self.socketio = socketio

        self.activo = False
        self.timer = None
        self.session_id = None
        # Veredictos del juez adelantados mientras Azure transcribe (precalentar_juez).
        self._juez_previo = {}
        self._falta = ""  # lo que el juez dijo que falta en el turno actual (clase.MOTIVOS)
        self._pool_juez = ThreadPoolExecutor(max_workers=2)
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)
        # Lo lee la pizarra (frases_para_card): lista [{"jp","es"}] de la línea PIZARRA del
        # turno, [] si no hay nada que enseñar, None si el modelo no la puso. Azure no la
        # usa como referencia (ver ponytail del módulo).
        self.ultima_frase_objetivo = None
        # Lo que Laura ve ahora en la pizarra (lista [{"jp","es"}]); Kaito lo sabe en cada turno.
        self.pizarra_actual = []
        # {"cd": id, "fase": presentar|repaso|practicar|tarea|libre, "aciertos": n}
        self.clase = None

        # Unidad abierta e ítems nuevos, resueltos una vez por sesión en entrar()
        # y persistidos al cerrar (_ejecutar_extraccion).
        self._foco_unidad = None
        self._ja_alt = None  # el turno oído forzando japonés (oir_japones), solo para este turno

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    # Un solo modo. Se mantiene el nombre por los call sites de STT
    # (transcribir_para_turno): False = evalúa pronunciación cuando toca.
    modo_conv = False
    juez = staticmethod(juez_cumple)  # los tests lo cambian por None
    # Turno «en español» que puede ser japonés mal transcrito (ver _NOTA_ROMAJI).
    juez_romaji = staticmethod(lambda cd, m, fase, contexto=None:
                               juez_cumple(cd, m, fase, romaji=True, contexto=contexto))

    @staticmethod
    def _clave_juez(texto):
        """Lo mismo dicho por Whisper y por Azure (con o sin puntuación, kanji o kana)."""
        return re.sub(r"[\s、。，．,.!?！？]", "", a_kana(normalizar_japones(texto or "")))

    def precalentar_juez(self, texto):
        """Mientras Azure transcribe, el juez ya valora lo que dijo Whisper. Si Azure
        escribe lo mismo, el veredicto ya está (ahorra ~1 s); si no, se pregunta de nuevo."""
        if not self.espera_japones or not texto:
            return
        cd = self._cd()
        if not cd or cd.get("patron") in ("te", "ta", "tekudasai", "llano"):
            return  # esos los decide el código, sin juez
        fase = self.clase["fase"]
        clave = (cd["id"], fase, self._clave_juez(texto))
        if clave not in self._juez_previo:
            self._juez_previo[clave] = (self._pool_juez.submit(
                self.juez, cd, texto, fase, contexto=self._ultimo_kaito()), texto)

    def oir_japones(self, texto):
        """El STT: este turno, que Whisper tomó por español, oído forzando japonés."""
        self._ja_alt = texto

    def _juzgar(self, cd, mensaje, fase):
        previo = self._juez_previo.get((cd["id"], fase, self._clave_juez(mensaje)))
        if previo is not None:
            fut, texto = previo
            try:
                v = fut.result(timeout=8)
                self._falta = MOTIVOS.get(texto, "")
                return v
            except Exception:  # noqa: BLE001
                pass
        v = self.juez(cd, mensaje, fase, contexto=self._ultimo_kaito())
        self._falta = MOTIVOS.get(mensaje, "")
        return v

    def _ultimo_kaito(self):
        """Lo último que dijo Kaito: la situación a la que responde Laura (para el juez)."""
        return next((_sin_pizarra(m["content"]) for m in reversed(self.mensajes) if m["role"] == "assistant"), None)

    @property
    def espera_japones(self) -> bool:
        """Lo lee el STT antes de grabar: en práctica y tarea Laura contesta en
        japonés, así que su audio puede ir a Azure (pronunciación)."""
        return self.activo and bool(self.clase) and self.clase["fase"] in ("practicar", "tarea")

    def entrar(self):
        """Activa el modo sensei y abre una sesión en la BD."""
        self.activo = True
        self.mensajes = []
        self._juez_previo = {}
        self.ultima_frase_objetivo = None
        self.pizarra_actual = []

        # La unidad abierta se resuelve UNA vez por sesión (no una por turno).
        self._foco_unidad = unidad_actual(self.jap_memory)

        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.jap_memory._conectar() as conn:
            cursor = conn.execute(
                "INSERT INTO japanese_sessions (started_at) VALUES (?)", (now,)
            )
            self.session_id = cursor.lastrowid

        if self.timer:
            self.timer.cancel()
        self._renovar_timer()
        self._empezar_clase()
        self.entrada_ts = time.monotonic()  # la pantalla empieza ahora la animación de la cara
        self.socketio.emit("modo_sensei", {"activo": True})
        print("🎌 Modo Sensei activado")

    def saludo_inicial(self) -> str:
        """Saludo de apertura y lo registra en el historial de la sesión.

        Sin esto el modelo no sabe que ya ha saludado: vuelve a saludar en su
        primer turno y se queda en un bucle de saludos / repetir el saludo en
        vez de entrar en materia. En el historial va sin el prefijo de UI."""
        saludo = random.choice(SALUDOS)
        limpio = saludo.split("! ", 1)[-1] if "! " in saludo else saludo
        self.mensajes.append({"role": "assistant", "content": limpio})
        return saludo

    def salir(self):
        """Desactiva el modo sensei, cancela el timer y cierra la sesión.

        Al salir, brain emite sensei_pizarra_fuera (la pizarra baja y la cara vuelve al
        frente, aún con la cara sensei), Kaito se despide así y el listener/app emite
        modo_sensei activo:False después de que el TTS termine (la animación de salida).
        """
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.activo = False
        # Antes de la extracción (que vacía el estado): la pantalla lo enseña al volver a la cara.
        try:
            self.socketio.emit("sensei_resumen", self.resumen_clase())
        except Exception as e:  # noqa: BLE001 — un resumen fallido no debe romper la despedida
            print(f"⚠️ No se pudo emitir el resumen de la clase: {e}")
        # La extracción tarda entre 5 y 15 s; que no bloquee la despedida.
        self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
        print("🎌 Modo Sensei desactivado")

    def resumen_clase(self) -> dict:
        """Lo que se enseña al acabar la clase: can-dos conseguidos hoy y hasta 5 palabras
        vistas, en kana (nunca kanji). Vacío ({}) si no hubo nada que celebrar."""
        logros = [_POR_ID[i]["texto"] for i in (self.clase or {}).get("logros", []) if i in _POR_ID][:3]
        palabras = []
        for it in _vocab_dicho(self.mensajes or [])[:5]:
            jp = re.sub(r"[（(].*?[)）]", "", it.get("reading") or it["jp"]).replace("〜", "").split(";")[0].strip()
            palabras.append({"jp": a_kana(jp), "es": it.get("meaning", "")})
        if not logros and not palabras:
            return {}
        return {"titulo": "¡Buena clase!", "logros": logros, "palabras": palabras}

    def esta_activo(self) -> bool:
        return self.activo

    def _renovar_timer(self):
        """Reinicia el contador de inactividad de 20 minutos."""
        if self.timer:
            self.timer.cancel()
        def _timeout():
            self.activo = False
            self.timer = None
            # ponytail: DB/LLM writes via managed socketio task, not daemon timer thread
            self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
        self.timer = threading.Timer(20 * 60, _timeout)
        self.timer.daemon = True
        self.timer.start()
    # ── Clase: fases por código ───────────────────────────────────────────────

    def _cds(self):
        return [cd for cd in (self._foco_unidad or {}).get("can_dos", [])
                if cd.get("explicacion") and cd.get("tarea")]

    def _cd(self):
        return _POR_ID.get(self.clase["cd"])

    def _progreso(self):
        prog = self.jap_memory.can_dos_progreso()
        return prog if isinstance(prog, dict) else {}

    def _siguiente(self):
        """Qué toca ahora: (can-do, tipo) o (None, None). Tipos: 'pendiente'
        (conseguido una vez otro día), 'antiguo' (dominado, 1 cada 4 nuevos) y
        'nuevo' (de la unidad abierta o, si se acabó, de la siguiente)."""
        st, prog = self.clase, self._progreso()
        hechos = set(st.get("hechos", []))
        orden = [u for u in CURRICULUM if u.get("can_dos")]
        foco = (self._foco_unidad or {}).get("id")
        idx = next((k for k, u in enumerate(orden) if u["id"] == foco), 0)

        def candidatos(unidades, estado):
            return [cd for u in unidades for cd in u["can_dos"]
                    if cd["id"] in _POR_ID and cd["id"] not in hechos
                    and prog.get(cd["id"], {}).get("estado", "no_intentado") in estado]

        por_fecha = lambda cd: prog.get(cd["id"], {}).get("ultima_sesion") or 0
        pend = sorted(candidatos(orden[:idx + 1], ("en_progreso",)), key=por_fecha)
        if pend:
            return pend[0], "pendiente"
        n = st.get("nuevos", 0)
        if n and n % NUEVOS_POR_ANTIGUO == 0 and st.get("antiguo_en") != n:
            viejos = sorted(candidatos(orden[:idx + 1], ("dominado",)), key=por_fecha)
            if viejos:
                st["antiguo_en"] = n
                return viejos[0], "antiguo"
        nuevos = candidatos(orden[idx:idx + 2], ("no_intentado",))
        return (nuevos[0], "nuevo") if nuevos else (None, None)

    def _abrir(self, cd, tipo):
        """Pone la clase en ese can-do y devuelve qué tiene que hacer Kaito."""
        st = self.clase
        st.update(cd=cd["id"], tipo=tipo, aciertos=0, fallos=0, fallos_cd=0)
        if tipo == "nuevo":
            st["fase"] = "practicar"
            # Boletín: ◐ desde que se empieza a enseñar, no solo al acertar ni al cerrarlo.
            try:
                self.jap_memory.set_can_do(cd["id"], "empezado", self.session_id)
            except Exception as e:  # noqa: BLE001 — guardar el progreso no debe romper el turno
                print(f"⚠️ No se pudo guardar el can-do empezado: {e}")
            return presentar(cd)
        st["fase"] = "tarea"
        return (f"Esto ya lo trabajasteis otro día ({cd['texto']}): dile en media frase que "
                "vais a ver si lo recuerda y, sin explicárselo, " + tarea_nueva(cd)[0].lower()
                + tarea_nueva(cd)[1:])

    def _cerrar_cd(self, cd, resultado):
        """Guarda el resultado del can-do y pasa al siguiente. Devuelve la
        instrucción para abrirlo (o la de charla si no queda nada)."""
        st = self.clase
        self.jap_memory.set_can_do(cd["id"], resultado, self.session_id)
        st.setdefault("hechos", []).append(cd["id"])
        if resultado == "conseguido":
            st.setdefault("logros", []).append(cd["id"])
        if resultado == "conseguido" and st.get("tipo", "nuevo") == "nuevo":
            st["nuevos"] = st.get("nuevos", 0) + 1
        sig, tipo = self._siguiente()
        if not sig:
            st.update(cd=None, fase="libre", aciertos=0)
            return "Luego charla con ella de lo que quiera, usando en japonés solo lo que ya sabe."
        return "Luego: " + self._abrir(sig, tipo) + _UNA_PETICION

    def _fallo(self, cd, instr):
        """Un intento en japonés sin acierto. A los FALLOS_MAX seguidos, en vez de
        insistir: Kaito le da un modelo y se pasa a lo siguiente (se volverá a ver)."""
        st = self.clase
        st["fallos"] = st.get("fallos", 0) + 1
        st["fallos_cd"] = st.get("fallos_cd", 0) + 1  # fallos desde que se abrió este can-do
        if st["fallos"] < FALLOS_MAX:
            return instr
        # Lo dominado que falla baja a en_progreso ('error'); lo demás queda empezado.
        resultado = "error" if st.get("tipo") == "antiguo" else "parcial"
        return ("Laura lleva varios intentos sin conseguirlo. Sin agobiarla: dale tú UNA frase "
                f"modelo corta, correcta y sencilla en japonés que haga esto: {que_hacer(cd)} "
                "Es solo para que la oiga: no le pidas que la repita. "
                "Dile en media frase que lo volveréis a ver otro día y cambia de tema. "
                + self._cerrar_cd(cd, resultado))

    def _empezar_clase(self):
        self.clase = {"cd": None, "fase": "libre", "aciertos": 0, "fallos": 0,
                      "nuevos": 0, "hechos": []}
        cd, tipo = self._siguiente()
        if cd:
            # La fase real se pone al primer turno (_abrir): antes, Laura saluda.
            self.clase.update(cd=cd["id"], tipo=tipo,
                              fase="presentar" if tipo == "nuevo" else "repaso")

    def _instruccion(self, mensaje):
        st, cd = self.clase, self._cd()
        ja_alt, self._ja_alt = self._ja_alt, None  # vale solo para este turno
        self._falta = ""
        if any(d in mensaje.lower() for d in _DESPEDIDAS_LAURA):
            return ("Laura se despide. Despídete con cariño en una o dos frases, recordándole "
                    "en media frase lo que ha practicado hoy. No le pidas nada más.")
        if st["fase"] == "libre" or not cd:
            return self._charla_guiada()
        if (st["fase"] in ("practicar", "tarea") and not _RE_JP_CHAR.search(mensaje)
                and _RE_SIGUIENTE.search(mensaje)):
            # Sin marcarlo como conseguido (no se ha comprobado): queda en progreso y vuelve
            # en un repaso. Un repaso de algo ya dominado no cambia de estado.
            resultado = "no_intentado" if st.get("tipo") == "antiguo" else "parcial"
            return ("Laura quiere pasar a lo siguiente. Dile en media frase que vale, que lo "
                    "volveréis a ver otro día en un repaso rápido, sin discutir ni explicarle nada "
                    "más de esto. " + self._cerrar_cd(cd, resultado))
        if st["fase"] in ("presentar", "repaso"):
            return "Responde en una frase a lo que te diga. Luego: " + self._abrir(
                cd, st.get("tipo") or ("nuevo" if st["fase"] == "presentar" else "pendiente"))

        mensaje = normalizar_japones(mensaje)  # romaji/katakana de Whisper → hiragana
        errs = errores(cd, mensaje)
        if errs:
            dicho, bien, motivo = errs[0]
            return self._fallo(cd, f"Laura ha dicho 【{dicho}】 y lo correcto es 【{bien}】 porque {motivo}. "
                    "Si te ha preguntado algo, contéstalo primero en una frase. Corrige SOLO "
                    "este error diciéndole el porqué (la regla, en español) y pídele que lo "
                    "intente otra vez con otra frase suya (una sola petición, sin darle la frase hecha).")
        if (_RE_JP_CHAR.search(mensaje) and tiene_espanol(mensaje)
                and "?" not in mensaje and "¿" not in mensaje):
            # Mezcla: dice en japonés lo que sabe y rellena en español lo que le
            # falta. No cuenta como acierto, pero es la ocasión de darle la palabra.
            return self._fallo(cd, "Laura ha mezclado: lo que sabe en japonés y en español lo que le falta. "
                    "Dile en media frase que la parte en japonés va bien, dale en japonés solo "
                    "lo que dijo en español (corto) y pídele que diga la frase entera en japonés.")
        if _RE_JP_CHAR.search(mensaje) and usa_patron(
                cd, mensaje, juez=lambda c, m: self._juzgar(c, m, st["fase"])):
            return self._acierto(cd)
        if _RE_JP_CHAR.search(mensaje):
            return self._fallo(cd, self._instr_no_cumple(cd, mensaje))
        if _RE_NO_SE.search(mensaje):
            return self._fallo(cd, self._ayuda(cd))
        # «En español» sin preguntar nada: puede ser su respuesta en japonés que Whisper
        # tomó por español («Ohio por la mañana, con Bangwa por la noche»).
        # Las conjugaciones (te/ta/…) no se pueden juzgar sobre letras mal transcritas.
        if ("?" not in mensaje and "¿" not in mensaje
                and cd.get("patron") not in ("te", "ta", "tekudasai", "llano")
                # Primero lo oído forzando japonés, solo (mezclado con el español el juez
                # se lía); si no, el texto de Whisper con letras españolas.
                and any(self.juez_romaji(cd, m, st["fase"], contexto=self._ultimo_kaito())
                        for m in ([ja_alt] if ja_alt else []) + [mensaje])):
            return self._acierto(cd)
        if st["fase"] != "tarea":
            vuelta = "pídele una frase con lo de hoy. " + PEDIR_FRASE
        else:  # la MISMA situación, no una nueva en cada turno
            vuelta = "vuelve a plantearle la misma situación que le planteaste, sin cambiarla."
        return ("Laura habla en español (o es japonés que el reconocimiento de voz no ha "
                "entendido: si lo que llega no tiene sentido en español, NO le digas que ha "
                "hablado en español; dile que no la has oído bien y que lo repita despacio). "
                "Responde a lo que dice o pregunta, corto (si pregunta algo de japonés, "
                f"explícaselo). Luego retoma: {vuelta}")

    def _historial_llm(self):
        """Los últimos turnos para el LLM. La línea PIZARRA solo en los dos últimos mensajes de Kaito
        (basta para que no pierda el formato; en los demás son tokens de más en cada turno)."""
        out, vistos = [], 0
        for m in reversed(self.mensajes[-(MAX_TURNOS * 2):]):
            if m["role"] == "assistant":
                vistos += 1
                if vistos > 2:
                    m = {**m, "content": _sin_pizarra(m["content"])}
            out.append(m)
        return out[::-1]

    def _instr_no_cumple(self, cd, mensaje):
        """El juez dijo que no. Kaito dice SOLO lo que el juez comprobó que falta. Logs (12-nov
        noche): sin saber qué fallaba, se inventó un «じゃありません» que Laura no dijo y le dio la
        vuelta al orden de lo que dijo."""
        if self._falta:
            causa = f"Falta (comprobado): {self._falta}. Dile solo eso, con el porqué. "
        else:
            causa = "No se ha podido comprobar qué falla: no señales ningún error; pídele que lo repita entero y despacio. "
        return (f"Lo que ha dicho Laura aún no cumple lo de hoy ({cd['texto']}). Dijo, en su orden: "
                f"«{a_kana(mensaje)}». " + causa + "No menciones nada que no esté ahí ni cambies su orden. "
                "Respóndele en una frase (sin decir que está bien) y sin darle la frase hecha.")

    def _acierto(self, cd):
        """Laura ha hecho lo de hoy: cuenta el acierto y dice qué toca después."""
        st = self.clase
        st["aciertos"] += 1
        st["fallos"] = 0
        # Sin ningún fallo en este can-do basta 1 acierto por fase; con fallos, los de siempre.
        limpio = not st.get("fallos_cd")
        if st["fase"] == "practicar" and st["aciertos"] >= (ACIERTOS_SIN_FALLOS if limpio else ACIERTOS_PRACTICA):
            st.update(fase="tarea", aciertos=0)
            return ("Ha acertado. Celébralo en media frase, con calidez y sin repetir "
                    "fórmulas. Luego: " + tarea(cd))
        meta = (ACIERTOS_ANTIGUO if st.get("tipo") == "antiguo"
                else ACIERTOS_SIN_FALLOS if limpio else ACIERTOS_TAREA)
        if st["fase"] == "tarea" and st["aciertos"] >= meta:
            return (f"Felicítala: ya sabe hacer esto: {cd['texto']}. "
                    + self._cerrar_cd(cd, "conseguido"))
        # Logs (12-nov noche): con que_hacer(cd) entero pedía «una cosa que haces cada día Y otra que
        # nunca haces» en el mismo turno: solo UNA de las acciones.
        otra = ("plantéale otra situación distinta y corta, inventada por ti, en la que tenga que (pídele "
                "UNA sola cosa; si aquí hay varias, solo una, y la otra otro día): "
                + que_hacer(cd) if st["fase"] == "tarea"
                else "pídele otra frase con lo mismo, sobre otro tema. " + PEDIR_FRASE)
        return (f"Ha acertado. Celébralo en media frase, con calidez y sin repetir fórmulas, "
                f"y {otra}, sin darle la respuesta (una sola petición, nada de «luego»). Lo que dice Laura viene de reconocimiento "
                "de voz y puede estar mal transcrito: NO corrijas nada más (ni partículas "
                "ni palabras): la corrección de conjugación ya la hace el programa.")

    def _charla_guiada(self):
        """Modo libre: charla que, cada LIBRE_TURNOS_TEMA turnos, empuja a Laura a usar
        un can-do ya trabajado (el más antiguo primero), sin examen ni nota."""
        st = self.clase
        st["libre_turnos"] = st.get("libre_turnos", 0) + 1
        base = ("Ya ha conseguido todo lo que toca por ahora. Charla con ella de lo que quiera, "
                "usando en japonés solo lo que ya sabe.")
        if (st["libre_turnos"] - 1) % LIBRE_TURNOS_TEMA:
            return base
        prog = self._progreso()
        vistos = set(st.get("charlados", []))
        viejos = sorted((cd for u in CURRICULUM for cd in u.get("can_dos", [])
                         if cd["id"] in _POR_ID and cd["id"] not in vistos
                         and prog.get(cd["id"], {}).get("estado") in ("dominado", "en_progreso")),
                        key=lambda cd: prog[cd["id"]].get("ultima_sesion") or 0)
        if not viejos:
            return base
        st.setdefault("charlados", []).append(viejos[0]["id"])
        return (base + f" Lleva la charla hacia algo que le haga usar esto, que ya trabajasteis: "
                f"{viejos[0]['texto']}. Una pregunta abierta sobre su vida, natural, sin anunciarlo "
                "como repaso ni examen y sin explicárselo.")

    def _ayuda(self, cd):
        """Laura dice que no sabe, no se acuerda o pide que se lo expliquen. Un profesor
        da primero lo que falta y simplifica; si era un repaso, vuelve a explicarlo."""
        st = self.clase
        if st.get("tipo") in ("pendiente", "antiguo") and st["fase"] == "tarea":
            st.update(fase="practicar", aciertos=0)  # no se acuerda: se vuelve a presentar
            return ("Laura no se acuerda de esto. Empieza por la palabra o frase que le falte, "
                    "en japonés y en español, y vuelve a explicárselo con calma. "
                    + presentar(cd))
        return ("Laura no sabe cómo hacerlo. Contesta primero a lo que pregunta: dale TÚ la palabra "
                "o la frase que le falte (en japonés, con su significado). Luego simplifica: "
                "pídele UNA sola cosa corta, no varias.")

    # ── Turno de conversación ─────────────────────────────────────────────────

    def _respuesta_en_stream(self, historial, on_frase):
        """Pide la respuesta en streaming y va pasando a `on_frase` cada frase completa.
        Devuelve la respuesta entera, o None si no se pudo (nada se ha dicho todavía:
        el llamante usa el camino normal). Una vez dicha alguna frase, un corte a mitad
        no se repite: se queda con lo recibido."""
        if os.getenv("LLM_STREAMING", "1") == "0" or not hasattr(self.provider, "completar_stream"):
            return None
        total, buf, dichas, cortado = "", "", 0, False

        def decir(f):
            """Habla la frase sin la línea PIZARRA; tras ella no se habla nada más."""
            nonlocal dichas, cortado
            if cortado:
                return
            m = _RE_PIZARRA.search(f)
            if m:
                cortado, f = True, f[:m.start()]
            if f.strip():
                on_frase(normalizar_bloques_jp(f.strip()))
                dichas += 1

        try:
            for trozo in self.provider.completar_stream(
                    historial, max_tokens=MAX_TOKENS_EXPLICACION, temperature=TEMPERATURE_SENSEI,
                    reasoning_effort=REASONING_EFFORT_SENSEI):
                trozo = trozo.replace("**", "")
                total += trozo
                buf += trozo
                frases, buf = cortar_frases(buf)
                for f in frases:
                    decir(f)
        except Exception as e:  # noqa: BLE001
            if dichas == 0:
                print(f"⚠️ Streaming del LLM no disponible ({type(e).__name__}) → respuesta entera")
                return None
            print(f"⚠️ Streaming cortado a mitad ({type(e).__name__}): sigo con lo recibido")
        decir(buf)
        return total.strip() or None  # con la línea PIZARRA: la separa responder_turno


    @staticmethod
    def _separar_pizarra(texto):
        """(texto sin la línea PIZARRA, lista [{"jp","es"}] | None si el modelo no la puso).
        «PIZARRA: -» → []. El japonés va siempre en kana."""
        m = _RE_PIZARRA.search(texto)
        if not m:
            return texto, None
        out = []
        for ent in texto[m.end():].splitlines()[0].split(";"):
            jp, _, es = ent.partition("=")
            jp = a_kana(jp.replace("【", "").replace("】", "").strip())
            if _RE_JP_CHAR.search(jp):
                out.append({"jp": jp, **({"es": es.strip(" .")} if es.strip(" .") else {})})
        return texto[:m.start()].strip(), out[:3]

    def responder_turno(self, mensaje: str, lento_extra: bool = False, pron_contexto: str = None,
                        on_frase=None) -> str:
        """Respuesta del sensei a un turno. No lanza excepciones al exterior:
        ante fallos del proveedor devuelve un mensaje amable.

        `pron_contexto` — resumen de la evaluación de pronunciación de Azure
        para este audio (o None); va al turno, NO al historial limpio.
        `on_frase(frase)` — si se pasa, se llama con cada frase completa según llega
        del LLM (streaming) para ir hablándola; el valor devuelto es la respuesta
        entera, igual que sin streaming. Si el streaming falla antes de dar nada,
        se vuelve al camino normal (y `on_frase` no se llama)."""
        self._renovar_timer()
        self.ultima_frase_objetivo = None  # lo fija el LLM cada turno (línea PIZARRA)
        if self.clase is None:  # instancia sin entrar() (p. ej. tests)
            self._empezar_clase()
        sistema = cargar_prompt("sensei_clase").replace("{RECUERDAS_DE_LAURA}", self._recuerdas())
        instr = self._instruccion(mensaje)
        print(f"🧭 Clase [{self.clase['cd']} · {self.clase['fase']} · {self.clase['aciertos']}]: {instr[:120]}")
        usuario = f"{mensaje}\n\n[INSTRUCCIÓN: {instr}]"
        if pron_contexto:
            usuario += f"\n[Pronunciación (no la menciones como sistema): {pron_contexto}]"
        # Logs (12-nov noche): sin este recordatorio el modelo se olvidaba de la línea PIZARRA en
        # 14 de 17 turnos. Y así sabe qué está viendo Laura ahora mismo.
        ahora = _texto_pizarra(self.pizarra_actual)
        usuario += ("\n[Pizarra: " + (f"Laura ve «{ahora}»" if ahora else "vacía")
                    + ". Cierra con la línea PIZARRA: kana = significado (1-3, lo que pides ahora) o PIZARRA: -]")
        historial = ([{"role": "system", "content": sistema}]
                     + self._historial_llm()
                     + [{"role": "user", "content": usuario}])
        respuesta = self._respuesta_en_stream(historial, on_frase) if on_frase else None
        try:
            if respuesta is None:
                respuesta = self.provider.completar(
                    historial, max_tokens=MAX_TOKENS_EXPLICACION,
                    temperature=TEMPERATURE_SENSEI, reasoning_effort=REASONING_EFFORT_SENSEI,
                ).replace("**", "").strip()  # la voz leería los asteriscos
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."
        # La línea PIZARRA no se habla ni se muestra, pero SÍ va al historial: así el modelo ve su
        # propio formato y recuerda qué puso (el juez y el extractor la quitan: _sin_pizarra).
        respuesta, pizarra = self._separar_pizarra(respuesta)
        respuesta = normalizar_bloques_jp(respuesta)  # japonés suelto → 【】
        if pizarra is None:  # se olvidó de la línea: la pizarra enseña lo último que dijo en japonés
            pizarra = [{"jp": b} for b in bloques_japones(respuesta)[-1:]]
            print("⚠️ El modelo no puso la línea PIZARRA")
        self.ultima_frase_objetivo = self.pizarra_actual = pizarra
        print(f"🧑‍🏫 Pizarra: {pizarra}")  # para revisar en los logs si cuadra con lo pedido
        if not respuesta:
            return "Perdona, se me ha cruzado un cable. ¿Me lo repites? 【もういちど おねがいします】"
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant",
                              "content": f"{respuesta}\nPIZARRA: {_texto_pizarra(pizarra) or '-'}"})
        return respuesta

    # ── Memoria de Laura ──────────────────────────────────────────────────────

    def _recuerdas(self) -> str:
        """Lo que Kaito sabe de Laura: perfil, sesiones, episodios, puntos débiles."""
        try:
            perfil_general = self.memory.obtener_perfil()
        except Exception:
            perfil_general = ""

        perfil_jap = self.jap_memory.resumen_perfil()
        lineas_r = [perfil_general] if perfil_general else []

        if perfil_jap.get("vocab_by_status"):
            estados = ", ".join(
                f"{k}: {v}" for k, v in perfil_jap["vocab_by_status"].items()
            )
            lineas_r.append(f"Vocabulario por estado: {estados}")

        # Qué palabras concretas ha visto: sin esto Kaito le pide frases con palabras
        # que nunca le ha enseñado. Con el tiempo la lista crece: van las MAX_PALABRAS_VISTAS más
        # usadas (en clase y en el juego) y, a igualdad, las más recientes. ponytail: sin filtrar
        # por tema; si hace falta, priorizar las de la unidad abierta.
        try:
            filas = [r for r in self.jap_memory.vocab_rows().values() if r.get("meaning")][::-1]
            filas.sort(key=lambda r: -(r["reps"] + r.get("sensei_usos", 0)))  # estable: recientes antes
            vistas = [f"{a_kana(r['reading'] or r['word'])} ({r['meaning']})"
                      for r in filas[:MAX_PALABRAS_VISTAS]]
            resto = len(filas) - len(vistas)
        except Exception:  # noqa: BLE001 — memoria sin vocabulario (tests, BD vieja)
            vistas, resto = [], 0
        lineas_r.append(
            "Palabras que Laura ya ha visto" + (f" (las {len(vistas)} más usadas; conoce {resto} más)" if resto > 0 else "")
            + ": " + (", ".join(vistas) or "casi ninguna todavía"))

        if perfil_jap.get("last_sessions"):
            lineas_r.append("Últimas sesiones:")
            lineas_r += [f"  - {s}" for s in perfil_jap["last_sessions"]]

        if perfil_jap.get("episodios_laura"):
            lineas_r.append("Lo que Laura ha contado de su vida:")
            lineas_r += [f"  - {e}" for e in perfil_jap["episodios_laura"]]

        if perfil_jap.get("anecdotas_kaito"):
            lineas_r.append("Lo que TÚ (Kaito) ya has contado de ti mismo — no te contradigas:")
            lineas_r += [f"  - {a}" for a in perfil_jap["anecdotas_kaito"]]

        if perfil_jap.get("sin_corregir"):
            lineas_r.append(f"Quedó sin corregir: {perfil_jap['sin_corregir']}")

        if perfil_jap.get("notas_profe"):
            lineas_r.append("Cómo va Laura (notas de sesiones anteriores):")
            lineas_r += [f"  - {n}" for n in perfil_jap["notas_profe"]]

        # THROTTLE_DUE (Fase 09): tamaño máximo de la lista de puntos débiles.
        if perfil_jap.get("weak_points"):
            puntos = ", ".join(
                f"{w['word']} ({w['errors']} errores)"
                for w in perfil_jap["weak_points"][:THROTTLE_DUE]
            )
            lineas_r.append(f"Puntos débiles (vocabulario): {puntos}")

        if perfil_jap.get("weak_grammar"):
            puntos_g = ", ".join(
                f"{g['punto']} ({g['errors']} errores)"
                for g in perfil_jap["weak_grammar"][:THROTTLE_DUE]
            )
            lineas_r.append(f"Puntos débiles (gramática): {puntos_g}")

        return "\n".join(lineas_r)

    # ── Cierre de sesión y extracción (Fase 5) ───────────────────────────────

    def cerrar_sesion_y_extraer(self):
        """Extrae el aprendizaje de la sesión con LLM ligero y actualiza el SRS.

        Corre en segundo plano. Espera EXTRACCION_RETRASO_SEG antes de llamar al
        extractor para no compartir ventana de tokens/min con la despedida.
        Se lleva una copia de mensajes/foco: una sesión nueva puede empezar
        durante la espera y pisar self.*."""
        if not self.session_id:
            return
        session_id = self.session_id
        mensajes = list(self.mensajes)
        foco_unidad = self._foco_unidad
        self.session_id = None  # liberar ya: la sesión siguiente puede abrir mientras esperamos

        self._dormir(EXTRACCION_RETRASO_SEG)

        try:
            self._ejecutar_extraccion(session_id, mensajes, foco_unidad)
        except Exception as e:
            print(f"⚠️ Error inesperado en extracción de sesión {session_id}: {e}")
            try:
                self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            except Exception:
                pass

    def _dormir(self, segundos: int):
        """Pausa cooperativa: usa socketio.sleep si existe (en la simulación es
        un no-op), si no time.sleep. Nunca propaga excepciones."""
        if not segundos or segundos <= 0:
            return
        dormir = getattr(self.socketio, "sleep", None) or time.sleep
        try:
            dormir(segundos)
        except Exception:
            pass

    def _ejecutar_extraccion(self, session_id: int, mensajes=None, foco_unidad=None):
        # Sin argumentos → usa el estado vivo (call sites de tests). Con ellos →
        # la instantánea que tomó cerrar_sesion_y_extraer antes de esperar.
        mensajes = self.mensajes if mensajes is None else mensajes
        if not any(m["role"] == "user" for m in mensajes):
            # Solo el saludo de apertura: no hay nada que extraer.
            self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            return

        unidad = (self._foco_unidad if foco_unidad is None else foco_unidad) or {}

        # Vocabulario: solo lo que Kaito dijo de verdad en la clase (sus bloques 【】), no «los
        # 2 siguientes del can-do» como antes (registraba palabras que nunca se enseñaron).
        for item in _vocab_dicho(mensajes):
            try:
                self.jap_memory.add_item(
                    "vocabulario", item["jp"], reading=item.get("reading"),
                    meaning=item.get("meaning"), tipo=item.get("tipo"), session_id=session_id)
            except Exception as e:  # noqa: BLE001
                print(f"⚠️ Error persistiendo ítem '{item['jp']}': {e}")

        transcript = self._construir_transcript(mensajes)

        # Determinista, no depende de ningún LLM: cuenta como "usado en sensei"
        # cualquier palabra/gramática de la BD que aparezca en el transcript.
        try:
            # solo lo que dice Laura: que Kaito diga una palabra no es que ella la use
            solo_laura = "\n".join(l for l in transcript.splitlines() if l.startswith("Laura:"))
            self.jap_memory.marcar_usos_en_sensei(solo_laura)
        except Exception as e:
            print(f"⚠️ Error marcando usos en sensei: {e}")

        # Nivel 1: resumen en texto libre con cualquier modelo disponible.
        # Se guarda siempre para que la próxima sesión tenga continuidad aunque
        # la extracción completa no sea posible.
        summary_basico = self._extraer_resumen_basico(transcript)

        # Nivel 2: extracción completa (ítems nuevos, episodios, notas). Los
        # can-dos NO: los marca el código durante la clase (_instruccion).
        # Solo con el modelo principal (strict=True): los alternativos producen
        # JSON con japonés corrupto que contamina la BD.
        self._dormir(EXTRACCION_PAUSA_LLAMADAS_SEG)  # separa esta llamada del resumen

        historial = [
            {"role": "system", "content": _EXTRACCION_PROMPT},
            {"role": "user", "content": f"Conversación:\n{transcript}"},
        ]

        data = None
        try:
            texto = self._llamar_extractor(historial)
            data = self._parsear_json_sesion(texto)
        except Exception as e:
            print(f"⚠️ Error en extractor (intento 1): {e}")

        if data is None:
            print("⚠️ JSON inválido / modelo no disponible (intento 1). Reintentando…")
            self._dormir(EXTRACCION_PAUSA_LLAMADAS_SEG)  # deja que la ventana tokens/min se vacíe
            historial_retry = historial + [
                {"role": "user", "content": "Devuelve SOLO el JSON válido, sin ningún texto adicional."},
            ]
            try:
                texto = self._llamar_extractor(historial_retry)
                data = self._parsear_json_sesion(texto)
            except Exception as e:
                print(f"⚠️ Error en extractor (intento 2): {e}")

        if data is None:
            # Guardrail: el modelo fuerte no respondió (rate limit o JSON inválido
            # dos veces). NO se cae a modelos de reserva: producen japonés sucio
            # que corrompe la BD. Solo se guarda el resumen básico.
            print(f"⚠️ Extracción completa no disponible (sesión {session_id}).")
            self.jap_memory.guardar_resumen_sesion(session_id, summary=summary_basico)
            return

        # Ítems nuevos que introdujo la sesión: se registran en la BD de vocab/gram
        # (su progreso SRS ya no lo mueve el profesor — lo hará el juego web).
        for item in data.get("new_items", []):
            jp = _CANONICO.get((item.get("jp") or "").strip(), (item.get("jp") or "").strip())
            es = (item.get("es") or "").strip()
            category = (item.get("category") or "vocabulario").lower()
            if not jp or re.sub(r"(さん|ちゃん|くん)$", "", jp.lower()) in NOMBRES_PROPIOS:
                continue  # los nombres propios no son vocabulario (ジョナサン entró el 12-nov)
            kind = "gramatica" if "gram" in category else "vocabulario"
            try:
                self.jap_memory.add_item(kind, jp, meaning=es, session_id=session_id)
            except Exception as e:
                print(f"⚠️ Error añadiendo ítem '{jp}': {e}")

        self.jap_memory.guardar_resumen_sesion(
            session_id,
            summary=data.get("summary") or summary_basico or None,
            # Lo que Kaito decidió no corregir en el momento: lo recupera
            # la próxima sesión desde RECUERDAS_DE_LAURA.
            errors_noted="; ".join(
                e.strip() for e in data.get("sin_corregir", []) if e and e.strip()
            ),
            # Fase 15: cómo va Laura como alumna. Si no viene, se guarda vacía.
            nota_profe=(data.get("nota_profe") or "").strip(),
        )
        # Memoria episódica: lo que Laura contó de su vida, y lo que Kaito
        # afirmó de sí mismo (para que no se contradiga entre sesiones).
        self.jap_memory.guardar_episodios(session_id, data.get("episodios", []))
        self.jap_memory.guardar_anecdotas_kaito(session_id, data.get("kaito_dijo", []))

    def _construir_transcript(self, mensajes=None) -> str:
        lines = []
        for m in (self.mensajes if mensajes is None else mensajes):
            rol = "Profesor" if m["role"] == "assistant" else "Laura"
            lines.append(f"{rol}: {_sin_pizarra(m['content'])}")
        return "\n".join(lines)

    def _extraer_resumen_basico(self, transcript: str) -> str:
        """Resumen en texto libre usando cualquier modelo disponible.

        No requiere JSON ni japonés correcto — sirve de continuidad mínima
        para la próxima sesión cuando la extracción completa no está disponible.
        """
        historial = [
            {"role": "system", "content": (
                "Resume en 2-3 frases qué vocabulario y estructuras japonesas "
                "se trabajaron en esta clase. Menciona las palabras o expresiones "
                "en japonés que aparecieron. Responde solo en español."
            )},
            {"role": "user", "content": f"Conversación:\n{transcript}"},
        ]
        try:
            return self.provider.completar(historial, max_tokens=150)
        except Exception as e:
            print(f"⚠️ No se pudo generar resumen básico: {e}")
            return None

    def _llamar_extractor(self, historial: list, strict: bool = True) -> str:
        # strict=True: solo el modelo del sensei — es el que da japonés limpio en
        # el JSON. max_tokens=2000: ítems nuevos + episodios + notas en el mismo
        # JSON no cabían en 1000 (JSON válido pero incompleto, sin error).
        return self.provider.completar(
            historial,
            max_tokens=2000,
            response_format={"type": "json_object"},
            strict=strict,
            reasoning_effort="low",
        )

    def _parsear_json_sesion(self, texto: str):
        texto = re.sub(r"```(?:json)?\s*", "", texto).replace("```", "").strip()
        try:
            data = json.loads(texto)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", texto, re.DOTALL)
            if not m:
                return None
            try:
                data = json.loads(m.group())
            except json.JSONDecodeError:
                return None
        if not isinstance(data, dict):
            return None
        data.setdefault("summary", "")
        data.setdefault("new_items", [])
        data.setdefault("sin_corregir", [])
        data.setdefault("episodios", [])
        data.setdefault("kaito_dijo", [])
        return data
