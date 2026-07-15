import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import tempfile
import re
import subprocess
import threading
import time as tmod


class TextToSpeech:
    def __init__(self, device=1):
        self.device = device
        self.sample_rate_device = 48000
        self.voice_es = "es-ES-AlvaroNeural"
        self.voice_ja = "ja-JP-KeitaNeural"

    def _contiene_japones(self, texto: str) -> bool:
        """Detecta si hay kana/kanji o bloques 【】 en el texto."""
        if re.search(r'【[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+】', texto):
            return True
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', texto):
            return True
        return False

    def _limpiar_para_voz(self, texto: str) -> str:
        """
        Normaliza el texto en español para que la voz española
        pronuncie aproximado al japonés real.
        """
        # Quitar corchetes 【】 (ya los procesamos aparte)
        texto = re.sub(r'【[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+】', '', texto)

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
        # Separar por bloques 【...】
        partes = re.split(r'(【[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+】)', texto)
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

    async def _generar_audio_completo(self, texto: str, tmp_path: str):
        """
        Genera el audio final uniendo los segmentos español y japonés.
        """
        segmentos = self._dividir_texto(texto)

        if not segmentos:
            return

        # Si solo hay un segmento, lo generamos directamente
        if len(segmentos) == 1:
            txt, voz = segmentos[0]
            await self._generar_audio_segmento(txt, voz, tmp_path)
            return

        # Generar cada segmento por separado
        seg_paths = []
        for i, (txt, voz) in enumerate(segmentos):
            seg_path = tmp_path.replace(".mp3", f"_seg{i}.mp3")
            await self._generar_audio_segmento(txt, voz, seg_path)
            
            # Ralentizar voz japonesa con ffmpeg
            if voz == self.voice_ja:
                    velocidad = "0.7" if self._lento else "0.85"
                    slowed_path = seg_path.replace(".mp3", "_slow.mp3")
                    subprocess.run([
                        "ffmpeg", "-y", "-i", seg_path,
                        "-filter:a", f"atempo={velocidad}",
                        "-vn", slowed_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.unlink(seg_path)
                    seg_path = slowed_path

            seg_paths.append(seg_path)

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

    def hablar(self, texto: str, lento_extra: bool = False, on_start=None, on_stop=None):
        self._lento_extra = lento_extra
        try:
            print(f"🔊 Hablando: {texto}")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            asyncio.run(self._generar_audio_completo(texto, tmp_path))

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
            
            if on_start:
                on_start()

            self._reproducir_con_control_boca(data, intervalos, on_stop)

        except Exception as e:
            print(f"❌ Error en TTS: {e}")

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
        import threading
        import time as tmod

        sio = getattr(self, 'socketio', None)
        
        if not sio or not intervalos:
            sd.play(data, self.sample_rate_device, device=self.device)
            sd.wait()
            if on_stop:
                on_stop()
            return

        sd.play(data, self.sample_rate_device, device=self.device)
        inicio = tmod.time()
        duracion_total = len(data) / self.sample_rate_device

        def control_boca():
            boca_abierta = False
            while tmod.time() - inicio < duracion_total:
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
        sd.wait()
        if on_stop:
            on_stop()