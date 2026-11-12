import asyncio
import edge_tts
import threading
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import tempfile
import re
import subprocess
import threading
import time as tmod
import collections
import hashlib
import queue
import shutil

# Cualquier carácter japonés (kana o kanji).
JP_CHAR = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]'
# Bloque 【...】 con al menos un carácter japonés dentro: la puntuación,
# el 〜 y el texto que lo acompañe viajan con él en vez de romper el
# bloque en trozos.
BLOQUE_JP = r'【[^【】]*' + JP_CHAR + r'[^【】]*】'


def buscar_altavoz():
    # Preferencia de Ajustes (app_settings) antes que AUDIO_OUTPUT_HINT del .env.
    from core.system_settings import audio_salida_preferida
    hint = audio_salida_preferida()

    devs = list(enumerate(sd.query_devices()))
    hints = [hint] if hint else ["hifiberry", "G435"]
    for h in hints:
        for i, d in devs:
            if d["max_output_channels"] > 0 and h.lower() in d["name"].lower():
                return i
    # No encontrado: NO tumbes el arranque (el dispositivo elegido puede estar
    # desconectado). Usa la salida por defecto del sistema, como buscar_microfono().
    print(f"⚠️ Altavoz '{' / '.join(hints)}' no encontrado; usando la salida por defecto")
    return None


class TextToSpeech:
    def __init__(self, device=None):
        self.device = device if device is not None else buscar_altavoz()
        self.sample_rate_device = 48000
        self.voice_es = "es-ES-AlvaroNeural"
        self.voice_ja = "ja-JP-KeitaNeural"
        self._callado = threading.Event()

        try:
            _nom = sd.query_devices(self.device)["name"] if self.device is not None \
                else sd.query_devices(kind="output")["name"]
        except Exception:
            _nom = "por defecto"
        print(f"🔊 Salida de audio: {_nom}")

    def _contiene_japones(self, texto: str) -> bool:
        """Detecta si hay kana/kanji o bloques 【】 en el texto."""
        if re.search(BLOQUE_JP, texto):
            return True
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', texto):
            return True
        return False

    def _limpiar_markdown(self, texto: str) -> str:
        """El TTS lee los símbolos literalmente ('asterisco asterisco...' o
        'tecla de 1' con los emoji de teclado 1️⃣2️⃣...), así que quitamos
        negritas, cursivas, code, viñetas y esos emoji antes de sintetizar."""
        texto = re.sub(r'__([^_]+)__', r'\1', texto)
        texto = re.sub(r'`([^`]+)`', r'\1', texto)
        texto = texto.replace('`', '')
        texto = re.sub(r'(?m)^\s{0,3}[-*#>]+\s+', '', texto)   # viñetas / encabezados
        # Emoji "tecla" (1️⃣ 2️⃣ #️⃣...): dígito/# + variation selector opcional
        # (U+FE0F) + "combining enclosing keycap" (U+20E3). ANTES de tocar los
        # asteriscos: si no, el de un eventual *️⃣ sobreviviría a medias.
        texto = re.sub(r'[0-9#]️?⃣', '', texto)
        # Asteriscos sueltos: el modelo a veces marca negritas o deja un "*"
        # huérfano. No hay ningún uso legítimo de "*" hablado, así que se
        # quitan todos en vez de intentar emparejarlos.
        texto = texto.replace('*', '')
        # "no es / no soy" se lee "barra diagonal" — es el separador de
        # alternativas por escrito, en voz se dice "o" (medio/ambos anchos).
        texto = re.sub(r'\s*[/／]\s*', ' o ', texto)
        texto = re.sub(r'\s*\n\s*', ' ', texto)                # sin saltos de línea
        return texto.strip()

    def _limpiar_para_voz(self, texto: str) -> str:
        """
        Normaliza el texto en español para que la voz española
        pronuncie aproximado al japonés real.
        """
        # Quitar corchetes 【】 (ya los procesamos aparte)
        texto = re.sub(BLOQUE_JP, '', texto)

        # Eliminar restos de kana/kanji sueltos (no deberían aparecer)
        texto = re.sub(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+', '', texto)

        # Normalización fonética
        reemplazos = [
            (r'arigatou', 'arigató'),
            (r'konnichiwa', 'konnichiwa'),
            (r'ohayou', 'ohayó'),
            (r'sayounara', 'sayonara'),
            (r'konbanwa', 'konbanwa'),
            (r'\bdesu\b', 'des'),
            (r'\bmasu\b', 'mas'),
            (r'\bdeshita\b', 'deshta'),
            (r'\bmashita\b', 'mashta'),
            (r'\bshimasu\b', 'shimas'),
            (r'\bgozaimasu\b', 'gozaimas'),
            (r'\bonegaishimasu\b', 'onegaishimas'),
            (r'\bshita\b', 'shta'),
            (r'\bshite\b', 'shte'),
            (r'\bashita\b', 'ashta'),
            (r'[ー一]', ''),
        ]
        for patron, reemplazo in reemplazos:
            texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
        return texto.strip()

    def _dividir_texto(self, texto: str) -> list:
        """
        Divide el texto en segmentos (texto, voz).
        - Los bloques 【japonés】 se envían a la voz japonesa.
        - El resto se envía a la voz española.
        """
        # Normaliza el marcado antes de segmentar: aplana 【】 anidados y envuelve
        # el japonés que el modelo haya dejado suelto fuera de 【】. Sin esto la
        # regex de bloques no casa y el japonés se cuela como "segmento suelto".
        try:
            from ai.sensei.kana import normalizar_bloques_jp
            texto = normalizar_bloques_jp(texto)
        except Exception:
            pass

        # Separar por bloques 【...】
        partes = re.split('(' + BLOQUE_JP + ')', texto)
        segmentos = []

        for parte in partes:
            if not parte.strip():
                continue

            # Bloque japonés entre 【】
            if parte.startswith('【') and parte.endswith('】'):
                contenido = parte[1:-1]  # quitar los corchetes
                if contenido.strip():
                    print(f"🎌 Segmento japonés: '{contenido}'")
                    segmentos.append((contenido, self.voice_ja))
            else:
                # Texto en español (puede contener restos de kana sueltos)
                # Por si acaso, volvemos a dividir por kana/kanji sueltos
                subpartes = re.split(
                    r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+)', parte
                )
                for sp in subpartes:
                    if not sp.strip():
                        continue
                    if re.match(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+', sp):
                        print(f"🎌 Segmento japonés suelto: '{sp}'")
                        segmentos.append((sp, self.voice_ja))
                    else:
                        limpio = self._limpiar_para_voz(sp)
                        if limpio.strip() and len(limpio.strip()) > 2:
                            print(f"🎙️ Segmento español: '{limpio}'")
                            segmentos.append((limpio, self.voice_es))
        return segmentos

    async def _generar_audio_segmento(self, texto: str, voz: str, tmp_path: str):
        """Genera un mp3 para un segmento con una voz específica."""
        tts = edge_tts.Communicate(texto, voice=voz)
        await tts.save(tmp_path)

    def _procesar_segmento(self, seg_path: str, es_japones: bool, *,
                           trim_inicio: bool = True, trim_fin: bool = True,
                           pausa_final: float = 0.0, silencio_inicial: float = 0.0) -> str:
        """Ralentiza la voz japonesa y recorta el silencio de relleno de edge-tts
        SOLO en los bordes internos (entre trozos), nunca al principio del primer
        trozo ni al final del último, para que no arranque/corte a bocajarro.
        Añade `pausa_final` al final (separación entre trozos) y `silencio_inicial`
        al principio. Salida CBR 64k para que el concat con -c copy sea limpio."""
        filtros = []
        if es_japones:
            velocidad = "0.7" if getattr(self, "_lento_extra", False) else "0.85"
            filtros.append(f"atempo={velocidad}")

        _sr = ("silenceremove=start_periods=1:start_duration=0.04:"
               "start_silence=0.06:start_threshold=-50dB:detection=peak")
        partes = []
        if trim_inicio:
            partes.append(_sr)
        if trim_fin:
            partes += ["areverse", _sr, "areverse"]
        if partes:
            filtros.append(",".join(partes))

        if pausa_final and pausa_final > 0:
            filtros.append(f"apad=pad_dur={pausa_final:.3f}")
        if silencio_inicial and silencio_inicial > 0:
            filtros.append(f"adelay={int(silencio_inicial * 1000)}")  # tras el trim

        if not filtros:
            return seg_path  # nada que procesar

        out_path = seg_path.replace(".mp3", "_p.mp3")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", seg_path, "-filter:a", ",".join(filtros),
             "-c:a", "libmp3lame", "-b:a", "64k", "-ar", "24000", "-ac", "1", "-vn", out_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            os.unlink(seg_path)
            return out_path
        return seg_path  # si ffmpeg falla, seguimos con el original

    def _juntar_japones(self, segmentos: list) -> list:
        """Trozos japoneses seguidos (【を】 【ください】) → una sola petición: cada
        petición a edge-tts cuesta ~0,7 s y así se ahorran las de los trozos cortos."""
        out = []
        for txt, voz in segmentos:
            if out and voz == self.voice_ja and out[-1][1] == self.voice_ja:
                out[-1] = (out[-1][0] + "、" + txt, voz)
            else:
                out.append((txt, voz))
        return out

    def _partir_largos(self, segmentos: list, maximo: int = 110) -> list:
        """Un trozo en español largo (~280 caracteres) tardó 7 s en empezar a sonar en la
        Pi: se parte por frases (. ? ! ;) en trozos de hasta `maximo` caracteres para que
        suene la primera enseguida. Los japoneses no se tocan."""
        out = []
        for txt, voz in segmentos:
            if voz == self.voice_ja or len(txt) <= maximo:
                out.append((txt, voz))
                continue
            actual = ""
            for frase in re.split(r"(?<=[.!?;])\s+", txt):
                if actual and len(actual) + 1 + len(frase) > maximo:
                    out.append((actual, voz))
                    actual = frase
                else:
                    actual = (actual + " " + frase).strip()
            if actual:
                out.append((actual, voz))
        return out

    # ── Caché en disco de los trozos que se repiten («¡Qué bien!», 【ました】…) ────────
    CACHE_MAX_CHARS = 90      # solo se guardan trozos cortos: son los que se repiten
    CACHE_MAX_ARCHIVOS = 400  # al pasarse, se borran los menos usados

    def _carpeta_cache(self):
        """Carpeta de la caché (TTS_CACHE_DIR; por defecto audio/tts_cache) o None."""
        if not hasattr(self, "_cache_dir"):
            try:
                d = os.getenv("TTS_CACHE_DIR") or os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio", "tts_cache")
                os.makedirs(d, exist_ok=True)
                self._cache_dir = d
            except OSError:
                self._cache_dir = None
        return self._cache_dir

    def _ruta_cache(self, txt, voz):
        d = self._carpeta_cache()
        if not d or len(txt) > self.CACHE_MAX_CHARS or os.getenv("TTS_CACHE", "1") == "0":
            return None
        return os.path.join(d, hashlib.sha1(f"{voz}|{txt}".encode("utf-8")).hexdigest() + ".mp3")

    def _guardar_cache(self, destino, ruta):
        try:
            shutil.copyfile(ruta, destino + ".tmp")
            os.replace(destino + ".tmp", destino)  # atómico: nunca queda un mp3 a medias
            carpeta = os.path.dirname(destino)
            archivos = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".mp3")]
            if len(archivos) > self.CACHE_MAX_ARCHIVOS:
                for viejo in sorted(archivos, key=os.path.getmtime)[:50]:
                    os.unlink(viejo)
        except OSError as e:
            print(f"⚠️ Caché de voz: {e}")

    def _ajustar_np(self, data, *, trim_inicio, trim_fin, pausa, silencio_inicial):
        """Lo que hacía ffmpeg en los trozos en español, sobre el audio ya decodificado
        (sin lanzar ffmpeg, ~0,4 s menos en el primer trozo): recorta el silencio de relleno
        de edge-tts en los bordes internos y añade la pausa final / el silencio inicial."""
        sr = self.sample_rate_device
        umbral, margen = 10 ** (-50 / 20), int(0.06 * sr)
        con_sonido = np.flatnonzero(np.abs(data) > umbral)
        if con_sonido.size:
            ini = max(0, con_sonido[0] - margen) if trim_inicio else 0
            fin = min(len(data), con_sonido[-1] + 1 + margen) if trim_fin else len(data)
            data = data[ini:fin]
        partes = []
        if silencio_inicial > 0:
            partes.append(np.zeros(int(silencio_inicial * sr), dtype=np.float32))
        partes.append(data)
        if pausa > 0:
            partes.append(np.zeros(int(pausa * sr), dtype=np.float32))
        return np.concatenate(partes) if len(partes) > 1 else data

    def _acortar_primero(self, segmentos, minimo=60, tope=45):
        """El primer trozo en español, si es largo, se corta en una coma/pausa cercana: la
        descarga tarda según el texto, y así el primer sonido llega antes."""
        if not segmentos or segmentos[0][1] == self.voice_ja or len(segmentos[0][0]) <= minimo:
            return segmentos
        txt, voz = segmentos[0]
        corte = max((m.end() for m in re.finditer(r"[,;:.!?¿¡]\s", txt[:tope + 10]) if m.end() >= 12), default=0)
        if not corte:
            corte = txt.rfind(" ", 15, tope)
        if corte <= 0:
            return segmentos
        return [(txt[:corte].strip(), voz), (txt[corte:].strip(), voz)] + segmentos[1:]

    async def _generar_trozos(self, texto: str, base: str, como_audio: bool = False, corto: bool = False):
        """Genera y procesa los trozos de la respuesta y los va devolviendo EN ORDEN,
        cada uno en cuanto está listo. La descarga de todos arranca a la vez (hasta 4
        simultáneas), así el primero suena enseguida y los demás ya están hechos
        cuando les toca. `base` es la ruta (sin extensión) de los temporales.
        Con `como_audio=True` devuelve arrays de audio (los trozos en español se ajustan
        en numpy, sin ffmpeg; los japoneses sí pasan por ffmpeg por el atempo); si no,
        rutas de mp3 ya procesados (para concatenarlos). `corto=True` acorta el primero."""
        from core.config import TTS_PAUSA_SEGMENTOS, TTS_SILENCIO_INICIAL

        segmentos = self._partir_largos(
            self._juntar_japones(self._dividir_texto(self._limpiar_markdown(texto))))
        if corto:
            segmentos = self._acortar_primero(segmentos)
        if not segmentos:
            return
        pausa = TTS_PAUSA_SEGMENTOS  # fija; "más despacio" solo afecta al atempo del japonés
        sem = asyncio.Semaphore(4)

        async def generar(i, txt, voz):
            ruta = f"{base}_seg{i}.mp3"
            en_cache = self._ruta_cache(txt, voz)
            if en_cache and os.path.exists(en_cache):
                shutil.copyfile(en_cache, ruta)
                os.utime(en_cache)  # lo usado hace poco se queda
                return ruta
            async with sem:
                await self._generar_audio_segmento(txt, voz, ruta)
            if en_cache:
                self._guardar_cache(en_cache, ruta)
            return ruta

        tareas = [asyncio.create_task(generar(i, t, v)) for i, (t, v) in enumerate(segmentos)]
        ultimo = len(segmentos) - 1
        try:
            for i, (txt, voz) in enumerate(segmentos):
                ruta = await tareas[i]
                es_ja = voz == self.voice_ja
                if como_audio and not es_ja:
                    data = await asyncio.to_thread(self._cargar_trozo, ruta)
                    yield self._ajustar_np(
                        data, trim_inicio=(i != 0), trim_fin=(i != ultimo),
                        pausa=(pausa if i != ultimo else 0.0),
                        silencio_inicial=(TTS_SILENCIO_INICIAL if i == 0 else 0.0))
                    continue
                ruta = await asyncio.to_thread(
                    self._procesar_segmento, ruta,
                    es_japones=es_ja,
                    trim_inicio=(i != 0),          # el primer trozo conserva su arranque
                    trim_fin=(i != ultimo),        # el último conserva su cola
                    pausa_final=(pausa if i != ultimo else 0.0),
                    silencio_inicial=(TTS_SILENCIO_INICIAL if i == 0 else 0.0),
                )
                yield (await asyncio.to_thread(self._cargar_trozo, ruta)) if como_audio else ruta
        finally:
            for t in tareas:
                t.cancel()
            await asyncio.gather(*tareas, return_exceptions=True)

    async def _generar_audio_completo(self, texto: str, tmp_path: str):
        """
        Genera el audio final uniendo los segmentos español y japonés.
        """
        seg_paths = []
        async for seg_path in self._generar_trozos(texto, tmp_path.replace(".mp3", "")):
            seg_paths.append(seg_path)

        if not seg_paths:
            return

        if len(seg_paths) == 1:
            os.replace(seg_paths[0], tmp_path)
            return

        # Crear archivo de lista para ffmpeg concat
        list_path = tmp_path.replace(".mp3", "_list.txt")
        with open(list_path, "w") as f:
            for sp in seg_paths:
                f.write(f"file '{sp}'\n")

        # Concatenar con ffmpeg
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_path, "-c", "copy", tmp_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Limpiar temporales
        for sp in seg_paths:
            if os.path.exists(sp):
                os.unlink(sp)
        if os.path.exists(list_path):
            os.unlink(list_path)

    def callar(self):
        """Corta la voz al instante, desde cualquier hilo (ver _sonar)."""
        self._callado.set()

    def _sonar(self, data):
        """Reproduce `data` hasta el final o hasta callar(), y no vuelve antes.

        No se usa sd.play + sd.stop: en la Pi, parar o cerrar el stream desde otro
        hilo deja PortAudio bloqueado para siempre (reproducido con stop y con abort).
        Al callar, el propio callback termina el stream, igual que al acabarse el audio.
        """
        from core.system_settings import volumen_factor
        data = data * volumen_factor()
        pos = 0
        terminado = threading.Event()

        def rellenar(salida, frames, _tiempo, _estado):
            nonlocal pos
            trozo = data[pos:pos + frames]
            pos += len(trozo)
            salida[:len(trozo), 0] = trozo
            salida[len(trozo):] = 0
            if self._callado.is_set() or len(trozo) < frames:
                raise sd.CallbackStop

        stream = sd.OutputStream(
            samplerate=self.sample_rate_device, device=self.device, channels=1,
            dtype="float32", callback=rellenar, finished_callback=terminado.set,
        )
        stream.start()
        terminado.wait()
        stream.close()

    def callado(self) -> bool:
        """True si le han mandado callar en este turno."""
        return self._callado.is_set()

    def empezar_turno(self):
        """Una orden de callar solo vale para la respuesta de ese turno."""
        self._callado.clear()

    def hablar(self, texto: str, lento_extra: bool = False, on_start=None, on_stop=None, no_antes_de=None):
        self._lento_extra = lento_extra

        # Le han mandado callar mientras pensaba: ni siquiera genera el audio
        if self._callado.is_set():
            if on_stop:
                on_stop()
            return

        if not texto or not texto.strip():
            print("⚠️ TTS: texto vacío, nada que reproducir")
            if on_stop:
                on_stop()
            return

        if os.getenv("TTS_STREAMING", "1") != "0":  # TTS_STREAMING=0 → como antes
            return self._hablar_por_trozos(texto, on_start, on_stop, no_antes_de)

        try:
            print(f"🔊 Hablando: {texto}")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            asyncio.run(self._generar_audio_completo(texto, tmp_path))

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                print("⚠️ TTS: no se generó audio (texto sin contenido hablable)")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                if on_stop:
                    on_stop()
                return

            data, fs = sf.read(tmp_path)
            os.unlink(tmp_path)

            if data.dtype != np.float32:
                data = data.astype(np.float32)
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            if fs != self.sample_rate_device:
                data = self._convertir_sample_rate(
                    data, orig_sr=fs, target_sr=self.sample_rate_device
                )

            intervalos = self._detectar_intervalos_habla(data)
            
            # Le han mandado callar mientras generaba el audio: nunca llega a "hablando"
            if self._callado.is_set():
                if on_stop:
                    on_stop()
                return

            if on_start:
                on_start()

            self._reproducir_con_control_boca(data, intervalos, on_stop)

        except Exception as e:
            print(f"❌ Error en TTS: {e}")

    def _cargar_trozo(self, ruta: str) -> np.ndarray:
        """mp3 de un trozo → audio mono float32 a la frecuencia del altavoz."""
        data, fs = sf.read(ruta)
        os.unlink(ruta)
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if fs != self.sample_rate_device:
            data = self._convertir_sample_rate(data, orig_sr=fs, target_sr=self.sample_rate_device)
        return data

    def _hablar_por_trozos(self, texto: str, on_start=None, on_stop=None, no_antes_de=None):
        """Como hablar(), pero empieza a sonar en cuanto está el primer trozo y
        reproduce los demás según se generan (ver _generar_trozos)."""
        cola = queue.Queue()
        print(f"🔊 Hablando: {texto}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            base = tmp.name.replace(".mp3", "")
        os.unlink(base + ".mp3")

        def producir():
            async def correr():
                async for audio in self._generar_trozos(texto, base, como_audio=True, corto=True):
                    if self._callado.is_set():
                        break
                    cola.put(audio)
            try:
                asyncio.run(correr())
            except Exception as e:  # noqa: BLE001
                print(f"❌ Error en TTS: {e}")
            finally:
                cola.put(None)

        threading.Thread(target=producir, daemon=True).start()
        self._consumir_cola(cola, on_start, on_stop, no_antes_de)

    def _consumir_cola(self, cola, on_start=None, on_stop=None, no_antes_de=None):
        """Reproduce los trozos de audio que van llegando a `cola` (None = no hay más)."""
        try:
            primero = cola.get()
            if primero is None or self._callado.is_set():
                if primero is None:
                    print("⚠️ TTS: no se generó audio (texto sin contenido hablable)")
                if on_stop:
                    on_stop()
                return
            # `no_antes_de` (time.monotonic): el audio ya está listo pero no suena hasta
            # entonces (p. ej. a que acabe la animación de la cara al entrar en sensei).
            while no_antes_de and tmod.monotonic() < no_antes_de and not self._callado.is_set():
                tmod.sleep(0.03)
            if self._callado.is_set():
                if on_stop:
                    on_stop()
                return
            if on_start:
                on_start()
            self._sonar_por_trozos(primero, cola)
            if on_stop:
                on_stop()
        except Exception as e:  # noqa: BLE001
            print(f"❌ Error en TTS: {e}")

    def hablar_frases(self, frases, lento_extra=False, on_start=None, on_stop=None, no_antes_de=None):
        """Como hablar(), pero el texto llega por frases a la cola `frases` (None = fin)
        mientras el LLM aún escribe: cada frase se sintetiza según llega y suena enseguida."""
        self._lento_extra = lento_extra
        cola = queue.Queue()
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            base = tmp.name.replace(".mp3", "")
        os.unlink(base + ".mp3")

        def producir():
            async def correr():
                n = 0
                while True:
                    frase = await asyncio.to_thread(frases.get)
                    if frase is None:
                        break
                    if self._callado.is_set() or not str(frase).strip():
                        continue  # se sigue vaciando la cola, sin sintetizar
                    print(f"🔊 Hablando: {frase}")
                    async for audio in self._generar_trozos(
                            frase, f"{base}_f{n}", como_audio=True, corto=(n == 0)):
                        if self._callado.is_set():
                            break
                        cola.put(audio)
                    n += 1
            try:
                asyncio.run(correr())
            except Exception as e:  # noqa: BLE001
                print(f"❌ Error en TTS: {e}")
            finally:
                cola.put(None)

        threading.Thread(target=producir, daemon=True).start()
        self._consumir_cola(cola, on_start, on_stop, no_antes_de)

    def _sonar_por_trozos(self, primero, cola):
        """Reproduce `primero` y los trozos que lleguen a `cola` (None = no hay más),
        con UN solo stream de salida; si el siguiente trozo aún no está, suena
        silencio hasta que llegue. Mueve la boca según lo ya reproducido."""
        from core.system_settings import volumen_factor
        vol = volumen_factor()
        sr = self.sample_rate_device
        pendientes = collections.deque()
        estado = {"fin": False, "reproducido": 0, "actual": np.zeros(0, np.float32), "pos": 0}
        intervalos, acum = [], [0.0]

        def anadir(d):
            for a, b in self._detectar_intervalos_habla(d):
                intervalos.append((acum[0] + a, acum[0] + b))
            acum[0] += len(d) / sr
            pendientes.append(d * vol)

        anadir(primero)
        terminado = threading.Event()

        def rellenar(salida, frames, _tiempo, _estado):
            sale = 0
            while sale < frames:
                if estado["pos"] >= len(estado["actual"]):
                    if pendientes:
                        estado["actual"], estado["pos"] = pendientes.popleft(), 0
                        continue
                    break  # hueco (esperando trozo) o fin
                n = min(frames - sale, len(estado["actual"]) - estado["pos"])
                salida[sale:sale + n, 0] = estado["actual"][estado["pos"]:estado["pos"] + n]
                estado["pos"] += n
                estado["reproducido"] += n
                sale += n
            salida[sale:] = 0
            if self._callado.is_set() or (sale < frames and estado["fin"] and not pendientes):
                raise sd.CallbackStop

        stream = sd.OutputStream(
            samplerate=sr, device=self.device, channels=1,
            dtype="float32", callback=rellenar, finished_callback=terminado.set,
        )
        sio = getattr(self, "socketio", None)

        def control_boca():
            abierta = False
            while not terminado.is_set() and not self._callado.is_set():
                ahora = estado["reproducido"] / sr
                debe = any(a <= ahora < b for a, b in list(intervalos))
                if debe != abierta:
                    sio.emit("boca", {"hablado": debe})
                    abierta = debe
                tmod.sleep(0.03)
            if abierta:
                sio.emit("boca", {"hablado": False})

        stream.start()
        if sio:
            threading.Thread(target=control_boca, daemon=True).start()
        while True:  # recoge los trozos según llegan
            d = cola.get()
            if d is None:
                break
            if not self._callado.is_set():
                anadir(d)
        estado["fin"] = True
        terminado.wait()
        stream.close()

    def _convertir_sample_rate(self, audio, orig_sr, target_sr) -> np.ndarray:
        """Convierte sample rate sin librosa."""
        ratio = target_sr / orig_sr
        target_length = int(len(audio) * ratio)
        if target_length == 0:
            return audio
        return np.interp(
            np.linspace(0, len(audio), target_length),
            np.arange(len(audio)),
            audio.flatten()
        ).astype(np.float32)

    def _detectar_intervalos_habla(self, audio: np.ndarray, umbral=0.02, min_silencio=0.25) -> list:
        """
        Detecta segmentos donde hay sonido.
        Devuelve lista de (inicio_segundos, fin_segundos).
        """
        sr = self.sample_rate_device
        ventana = int(sr * 0.05)  # 50ms
        intervalos = []
        hablando = False
        inicio = 0
        silencio_desde = 0

        for i in range(0, len(audio), ventana):
            chunk = audio[i:i+ventana]
            if len(chunk) == 0:
                break
            nivel = np.max(np.abs(chunk))
            tiempo = i / sr

            if nivel > umbral:
                if not hablando:
                    inicio = tiempo
                    hablando = True
                silencio_desde = 0
            else:
                if hablando:
                    silencio_desde += len(chunk) / sr
                    if silencio_desde >= min_silencio:
                        intervalos.append((inicio, tiempo - silencio_desde))
                        hablando = False
        if hablando:
            intervalos.append((inicio, len(audio) / sr))
        return intervalos

    def _reproducir_con_control_boca(self, data, intervalos, on_stop=None):
        import time as tmod

        sio = getattr(self, 'socketio', None)

        # Le han mandado callar justo entre on_start y aquí: ni empieza
        if self._callado.is_set():
            if on_stop:
                on_stop()
            return

        if not sio or not intervalos:
            self._sonar(data)
            if on_stop:
                on_stop()
            return

        inicio = tmod.time()
        duracion_total = len(data) / self.sample_rate_device

        def control_boca():
            boca_abierta = False
            while tmod.time() - inicio < duracion_total and not self._callado.is_set():
                ahora = tmod.time() - inicio

                # Determinar si ahora mismo estamos en un intervalo de habla
                deberia_hablar = any(
                    inicio_seg <= ahora < fin_seg
                    for inicio_seg, fin_seg in intervalos
                )

                if deberia_hablar and not boca_abierta:
                    sio.emit("boca", {"hablado": True})
                    boca_abierta = True
                elif not deberia_hablar and boca_abierta:
                    sio.emit("boca", {"hablado": False})
                    boca_abierta = False

                tmod.sleep(0.03)

            # Cerrar boca al terminar
            if boca_abierta:
                sio.emit("boca", {"hablado": False})

        t = threading.Thread(target=control_boca, daemon=True)
        t.start()
        self._sonar(data)
        if on_stop:
            on_stop()