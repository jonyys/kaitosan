"""ProfesorJapones: el modo sensei.

El código decide qué toca y comprueba; el LLM solo habla. Cada can-do (datos en
ai/sensei/candos_clase.json) pasa por fases fijas:
  presentar → practicar (2 aciertos) → tarea (2 aciertos) → conseguido → siguiente.
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
    ACIERTOS_TAREA,
    FALLOS_MAX,
    LIBRE_TURNOS_TEMA,
    NUEVOS_POR_ANTIGUO,
    errores,
    presentar,
    que_hacer,
    tarea,
    tarea_nueva,
    juez_cumple,
    usa_patron,
)
from ai.sensei.curriculum import CURRICULUM, siguiente_items_nuevos, unidad_actual
from ai.sensei.kana import a_kana, normalizar_bloques_jp, normalizar_japones, tiene_espanol
from core.config import (
    EXTRACCION_PAUSA_LLAMADAS_SEG,
    EXTRACCION_RETRASO_SEG,
    MAX_ITEMS_NUEVOS,
    MAX_TOKENS_EXPLICACION,
    REASONING_EFFORT_SENSEI,
    TEMPERATURE_SENSEI,
    THROTTLE_DUE,
)

MAX_TURNOS = 8  # pares user/assistant conservados en el contexto del LLM
# Laura dice que no sabe / no se acuerda / pide ayuda (en español): hay que ayudarla.
_RE_NO_SE = re.compile(
    r"\bno (lo )?s[eé]\b|no me acuerdo|no recuerdo|no entiendo|expl[ií]ca|ay[uú]da|"
    r"c[oó]mo se (hace|usa)|no s[eé] c[oó]mo", re.IGNORECASE)  # «cómo se dice X» es solo vocabulario: no cuenta
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
        self._pool_juez = ThreadPoolExecutor(max_workers=2)
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)
        # Lo leen la cara y el STT (ReferenceText de Azure). Siempre None: Laura
        # produce frases suyas, no repite una dada (ver ponytail del módulo).
        self.ultima_frase_objetivo = None
        # {"cd": id, "fase": presentar|repaso|practicar|tarea|libre, "aciertos": n}
        self.clase = None

        # Unidad abierta e ítems nuevos, resueltos una vez por sesión en entrar()
        # y persistidos al cerrar (_ejecutar_extraccion).
        self._foco_nuevos = []
        self._foco_unidad = None

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    # Un solo modo. Se mantiene el nombre por los call sites de STT
    # (transcribir_para_turno): False = evalúa pronunciación cuando toca.
    modo_conv = False
    juez = staticmethod(juez_cumple)  # los tests lo cambian por None

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
            self._juez_previo[clave] = self._pool_juez.submit(self.juez, cd, texto, fase)

    def _juzgar(self, cd, mensaje, fase):
        fut = self._juez_previo.get((cd["id"], fase, self._clave_juez(mensaje)))
        if fut is not None:
            try:
                return fut.result(timeout=8)
            except Exception:  # noqa: BLE001
                pass
        return self.juez(cd, mensaje, fase)

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

        # La unidad abierta y los ítems nuevos del can-do activo se resuelven UNA
        # vez por sesión (no una por turno). Los nuevos se persisten al cerrar
        # (_ejecutar_extraccion), no aquí. MAX_ITEMS_NUEVOS limita cuántos.
        self._foco_unidad = unidad_actual(self.jap_memory)
        self._foco_nuevos = siguiente_items_nuevos(self.jap_memory, MAX_ITEMS_NUEVOS)

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

        El evento modo_sensei activo:False lo emite app.py después de que el
        TTS termine, para que la despedida se pronuncie con la cara sensei.
        """
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.activo = False
        # La extracción tarda entre 5 y 15 s; que no bloquee la despedida.
        self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
        print("🎌 Modo Sensei desactivado")

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
        st.update(cd=cd["id"], tipo=tipo, aciertos=0, fallos=0)
        if tipo == "nuevo":
            st["fase"] = "practicar"
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
        if resultado == "conseguido" and st.get("tipo", "nuevo") == "nuevo":
            st["nuevos"] = st.get("nuevos", 0) + 1
        sig, tipo = self._siguiente()
        if not sig:
            st.update(cd=None, fase="libre", aciertos=0)
            return "Luego charla con ella de lo que quiera, usando en japonés solo lo que ya sabe."
        return "Luego: " + self._abrir(sig, tipo)

    def _fallo(self, cd, instr):
        """Un intento en japonés sin acierto. A los FALLOS_MAX seguidos, en vez de
        insistir: Kaito le da un modelo y se pasa a lo siguiente (se volverá a ver)."""
        st = self.clase
        st["fallos"] = st.get("fallos", 0) + 1
        if st["fallos"] < FALLOS_MAX:
            return instr
        # Lo dominado que falla baja a en_progreso ('error'); lo demás queda empezado.
        resultado = "error" if st.get("tipo") == "antiguo" else "parcial"
        return ("Laura lleva varios intentos sin conseguirlo. Sin agobiarla: dale tú UNA frase "
                f"modelo corta, correcta y sencilla en japonés que haga esto: {que_hacer(cd)} "
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
        if any(d in mensaje.lower() for d in _DESPEDIDAS_LAURA):
            return ("Laura se despide. Despídete con cariño en una o dos frases, recordándole "
                    "en media frase lo que ha practicado hoy. No le pidas nada más.")
        if st["fase"] == "libre" or not cd:
            return self._charla_guiada()
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
                    "intente otra vez con otra frase suya.")
        if (_RE_JP_CHAR.search(mensaje) and tiene_espanol(mensaje)
                and "?" not in mensaje and "¿" not in mensaje):
            # Mezcla: dice en japonés lo que sabe y rellena en español lo que le
            # falta. No cuenta como acierto, pero es la ocasión de darle la palabra.
            return self._fallo(cd, "Laura ha mezclado: lo que sabe en japonés y en español lo que le falta. "
                    "Dile en media frase que la parte en japonés va bien, dale en japonés solo "
                    "lo que dijo en español (corto) y pídele que diga la frase entera en japonés.")
        # Solo si hay japonés: con un mensaje en español no hay nada que juzgar (y el
        # juez cuesta ~1 s por turno).
        if _RE_JP_CHAR.search(mensaje) and usa_patron(
                cd, mensaje, juez=lambda c, m: self._juzgar(c, m, st["fase"])):
            st["aciertos"] += 1
            st["fallos"] = 0
            if st["fase"] == "practicar" and st["aciertos"] >= ACIERTOS_PRACTICA:
                st.update(fase="tarea", aciertos=0)
                return ("Ha acertado. Celébralo en media frase, con calidez y sin repetir "
                        "fórmulas. Luego: " + tarea(cd))
            meta = ACIERTOS_ANTIGUO if st.get("tipo") == "antiguo" else ACIERTOS_TAREA
            if st["fase"] == "tarea" and st["aciertos"] >= meta:
                return (f"Felicítala: ya sabe hacer esto: {cd['texto']}. "
                        + self._cerrar_cd(cd, "conseguido"))
            otra = ("plantéale otra situación distinta y corta, inventada por ti, en la que tenga que: "
                    + que_hacer(cd) if st["fase"] == "tarea"
                    else "pídele otra frase con lo mismo, sobre otro tema (sin repetir «dime una frase tuya»)")
            return (f"Ha acertado. Celébralo en media frase, con calidez y sin repetir fórmulas, "
                    f"y {otra}, sin darle la respuesta. Lo que dice Laura viene de reconocimiento "
                    "de voz y puede estar mal transcrito: NO corrijas nada más (ni partículas "
                    "ni palabras): la corrección de conjugación ya la hace el programa.")
        if _RE_JP_CHAR.search(mensaje):
            return self._fallo(cd, "Lo que ha dicho Laura aún no cumple lo de hoy "
                    f"({cd['texto']}): o no lo usa, o falla justo en eso. Responde a lo que dice en "
                    "una frase; si se ha equivocado en lo de hoy, corrígeselo con el porqué; si no "
                    "lo ha usado, anímala a hacerlo, sin darle la frase hecha.")
        if _RE_NO_SE.search(mensaje):
            return self._fallo(cd, self._ayuda(cd))
        if st["fase"] != "tarea":
            vuelta = "pídele una frase suya con lo de hoy."
        else:  # la MISMA situación, no una nueva en cada turno
            vuelta = "vuelve a plantearle la misma situación que le planteaste, sin cambiarla."
        return ("Laura habla en español: responde a lo que dice o pregunta, corto (si pregunta "
                f"algo de japonés, explícaselo). Luego retoma: {vuelta}")

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
        total, buf, dichas = "", "", 0
        try:
            for trozo in self.provider.completar_stream(
                    historial, max_tokens=MAX_TOKENS_EXPLICACION, temperature=TEMPERATURE_SENSEI,
                    reasoning_effort=REASONING_EFFORT_SENSEI):
                trozo = trozo.replace("**", "")
                total += trozo
                buf += trozo
                frases, buf = cortar_frases(buf)
                for f in frases:
                    on_frase(normalizar_bloques_jp(f))
                    dichas += 1
        except Exception as e:  # noqa: BLE001
            if dichas == 0:
                print(f"⚠️ Streaming del LLM no disponible ({type(e).__name__}) → respuesta entera")
                return None
            print(f"⚠️ Streaming cortado a mitad ({type(e).__name__}): sigo con lo recibido")
        resto = buf.strip()
        if resto:
            on_frase(normalizar_bloques_jp(resto))
        respuesta = normalizar_bloques_jp(total.strip())
        return respuesta or None


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
        if self.clase is None:  # instancia sin entrar() (p. ej. tests)
            self._empezar_clase()
        sistema = cargar_prompt("sensei_clase").replace("{RECUERDAS_DE_LAURA}", self._recuerdas())
        instr = self._instruccion(mensaje)
        print(f"🧭 Clase [{self.clase['cd']} · {self.clase['fase']} · {self.clase['aciertos']}]: {instr[:120]}")
        usuario = f"{mensaje}\n\n[INSTRUCCIÓN: {instr}]"
        if pron_contexto:
            usuario += f"\n[Pronunciación (no la menciones como sistema): {pron_contexto}]"
        historial = ([{"role": "system", "content": sistema}]
                     + self.mensajes[-(MAX_TURNOS * 2):]
                     + [{"role": "user", "content": usuario}])
        respuesta = self._respuesta_en_stream(historial, on_frase) if on_frase else None
        try:
            if respuesta is None:
                respuesta = self.provider.completar(
                    historial, max_tokens=MAX_TOKENS_EXPLICACION,
                    temperature=TEMPERATURE_SENSEI, reasoning_effort=REASONING_EFFORT_SENSEI,
                ).replace("**", "").strip()  # la voz leería los asteriscos
                respuesta = normalizar_bloques_jp(respuesta)  # japonés suelto → 【】
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."
        if not respuesta:
            return "Perdona, se me ha cruzado un cable. ¿Me lo repites? 【もういちど おねがいします】"
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant", "content": respuesta})
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
        foco_nuevos = list(self._foco_nuevos)
        foco_unidad = self._foco_unidad
        self.session_id = None  # liberar ya: la sesión siguiente puede abrir mientras esperamos

        self._dormir(EXTRACCION_RETRASO_SEG)

        try:
            self._ejecutar_extraccion(session_id, mensajes, foco_nuevos, foco_unidad)
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

    def _ejecutar_extraccion(self, session_id: int, mensajes=None,
                             foco_nuevos=None, foco_unidad=None):
        # Sin argumentos → usa el estado vivo (call sites de tests). Con ellos →
        # la instantánea que tomó cerrar_sesion_y_extraer antes de esperar.
        mensajes = self.mensajes if mensajes is None else mensajes
        if not any(m["role"] == "user" for m in mensajes):
            # Solo el saludo de apertura: no hay nada que extraer.
            self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            return

        foco_nuevos = list(self._foco_nuevos if foco_nuevos is None else foco_nuevos)
        unidad = (self._foco_unidad if foco_unidad is None else foco_unidad) or {}

        # Persistir aquí los ítems nuevos de la sesión.
        for nuevo in foco_nuevos:
            try:
                self.jap_memory.add_item(
                    nuevo["kind"], nuevo["jp"],
                    reading=nuevo.get("reading"),
                    meaning=nuevo.get("meaning"),
                    tipo=nuevo.get("tipo"),
                    session_id=session_id,
                )
            except Exception as e:
                print(f"⚠️ Error persistiendo ítem nuevo '{nuevo['jp']}': {e}")

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
            jp = (item.get("jp") or "").strip()
            es = (item.get("es") or "").strip()
            category = (item.get("category") or "vocabulario").lower()
            if not jp:
                continue
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
            lines.append(f"{rol}: {m['content']}")
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
