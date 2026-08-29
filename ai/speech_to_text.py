import base64
import json
import os
import tempfile

import soundfile as sf
from groq import Groq

from core.config import (
    AZURE_PRON_DEBUG,
    AZURE_PRON_EN_CHARLA,
    AZURE_PRON_UMBRAL_BIEN,
    AZURE_PRON_UMBRAL_PALABRA,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    AZURE_STT_LIMITE_SEG_MES,
    GROQ_API_KEY,
)
from core.token_tracker import TokenTracker

# Signos que no cuentan al comparar lo pedido con lo dicho.
_PUNT_JP = "。、，．・…！？「」『』（）()【】　 \t\n"


def _num(d: dict, clave: str):
    """Lee una puntuación esté plana en el dict o anidada en PronunciationAssessment."""
    v = d.get(clave)
    if v is not None:
        return v
    return (d.get("PronunciationAssessment") or {}).get(clave)


def _norm_jp(s: str) -> str:
    return "".join(c for c in (s or "") if c not in _PUNT_JP)


class SpeechToText:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.modelo = "whisper-large-v3-turbo"
        self.tracker = TokenTracker()          # ← mismo tracker

    # ── Groq Whisper (ruta por defecto y fallback) ──────────────────────────
    def transcribir(self, archivo_audio: str, idioma: str = None) -> str:
        try:
            if not os.path.exists(archivo_audio):
                print(f"❌ Archivo no encontrado: {archivo_audio}")
                return ""

            # Medir duración del audio
            info = sf.info(archivo_audio)
            segundos = int(info.duration) + 1
            total_audio = self.tracker.añadir_audio(segundos)
            print(f"🎤 Segundos de audio hoy: {total_audio}/7200")

            print("🔄 Transcribiendo con Groq Whisper...")

            with open(archivo_audio, "rb") as audio:
                params = {
                    "model": self.modelo,
                    "file": audio,
                }
                if idioma:
                    params["language"] = idioma
                transcripcion = self.client.audio.transcriptions.create(**params)

            texto = transcripcion.text.strip()
            print(f"✅ Transcripción: {texto}")
            return texto

        except Exception as e:
            print(f"❌ Error transcribiendo: {e}")
            return ""

    # ── Azure Speech: transcripción + evaluación de pronunciación ────────────
    def transcribir_con_pronunciacion(self, archivo_audio: str, referencia: str = None) -> dict | None:
        """Envía el audio a Azure Speech (japonés) y devuelve un dict:

            {"texto": "<transcripción>", "pron": "<resumen legible o None>"}

        Evaluación en modo *libre* (sin ReferenceText): así `Display` es la
        transcripción real de lo que dijo Laura (en modo scripted Azure devuelve
        el texto de referencia y no se sabe qué dijo de verdad). `referencia`, si
        se pasa, solo se usa para comparar el objetivo con lo que se entendió.

        Devuelve None si Azure no está configurado, si se ha agotado la cuota
        mensual del tier gratuito, o si la llamada falla por cualquier motivo
        (el llamante debe caer entonces a `transcribir`).
        """
        if not AZURE_SPEECH_KEY:
            return None

        usado = self.tracker.azure_stt_segundos_mes()
        if usado >= AZURE_STT_LIMITE_SEG_MES:
            print(f"⚠️ Cuota mensual de Azure agotada ({usado}s ≥ {AZURE_STT_LIMITE_SEG_MES}s). Uso Groq Whisper.")
            return None

        if not os.path.exists(archivo_audio):
            print(f"❌ Archivo no encontrado: {archivo_audio}")
            return None

        try:
            import requests
        except ImportError:
            print("⚠️ 'requests' no instalado; Azure Speech desactivado. Uso Groq Whisper.")
            return None

        tmp_pcm = None
        try:
            # Reencodar a WAV PCM 16-bit mono (lo que Azure espera). El recorder
            # guarda float32, que Azure puede rechazar como audio/pcm.
            data, sr = sf.read(archivo_audio, dtype="float32")
            if getattr(data, "ndim", 1) > 1:
                data = data.mean(axis=1)
            segundos = int(len(data) / sr) + 1

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
                tmp_pcm = t.name
            sf.write(tmp_pcm, data, sr, subtype="PCM_16")

            ref = (referencia or "").strip()
            pron_cfg = base64.b64encode(json.dumps({
                # Vacío = evaluación libre: Display = lo que Laura dijo de verdad.
                "ReferenceText": "",
                "GradingSystem": "HundredMark",
                "Granularity": "Phoneme",
                "Dimension": "Comprehensive",
                # La prosodia solo está soportada en algunos locales (no ja-JP a
                # día de hoy); si se activa para un locale que la admita, el
                # resumen ya la incluye automáticamente.
                "EnableProsodyAssessment": False,
            }).encode("utf-8")).decode("ascii")

            url = (
                f"https://{AZURE_SPEECH_REGION}.stt.speech.microsoft.com"
                "/speech/recognition/conversation/cognitiveservices/v1"
                "?language=ja-JP&format=detailed"
            )
            headers = {
                "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
                "Content-Type": f"audio/wav; codecs=audio/pcm; samplerate={sr}",
                "Pronunciation-Assessment": pron_cfg,
                "Accept": "application/json",
            }

            if ref:
                print(f"🔄 Transcribiendo con Azure Speech (pronunciación, objetivo 「{ref}」)...")
            else:
                print("🔄 Transcribiendo con Azure Speech (pronunciación)...")
            with open(tmp_pcm, "rb") as f:
                audio_bytes = f.read()
            resp = requests.post(url, headers=headers, data=audio_bytes, timeout=15)

            if resp.status_code == 403:
                print("⚠️ Azure devolvió 403 (cuota F0 agotada). Uso Groq Whisper.")
                # Marcar la cuota como consumida para no reintentar todo el mes.
                self.tracker.añadir_azure_stt(AZURE_STT_LIMITE_SEG_MES)
                return None
            resp.raise_for_status()
            body = resp.json()

            if body.get("RecognitionStatus") != "Success" or not body.get("NBest"):
                print(f"⚠️ Azure sin reconocimiento útil: {body.get('RecognitionStatus')}. Uso Groq Whisper.")
                return None

            total = self.tracker.añadir_azure_stt(segundos)
            print(f"🎌 Azure este mes: {total}/{AZURE_STT_LIMITE_SEG_MES}s")

            best = body["NBest"][0]
            if AZURE_PRON_DEBUG:
                print("🔬 Azure NBest[0]:", json.dumps(best, ensure_ascii=False))
            texto = (best.get("Display") or best.get("Lexical") or "").strip()
            pron = self._resumir_pronunciacion(best, referencia=ref, oido=texto)
            print(f"✅ Transcripción (Azure): {texto}")
            print(f"🗣️  Pronunciación: {pron.replace(chr(10), '  |  ') if pron else 'sin datos de evaluación en la respuesta de Azure'}")
            return {"texto": texto, "pron": pron}

        except Exception as e:
            print(f"❌ Error con Azure Speech: {e}. Uso Groq Whisper.")
            return None
        finally:
            if tmp_pcm and os.path.exists(tmp_pcm):
                try:
                    os.unlink(tmp_pcm)
                except OSError:
                    pass

    @staticmethod
    def _resumir_pronunciacion(best: dict, referencia: str = "", oido: str = "") -> str | None:
        """Convierte la respuesta de Azure en un resumen legible para el profesor
        (y para la consola). Lee el formato PLANO del endpoint REST: las
        puntuaciones cuelgan de `best` y de cada palabra directamente
        (`best["AccuracyScore"]`, `word["ErrorType"]`), no de
        `best["PronunciationAssessment"]` como en el SDK."""

        acc = _num(best, "AccuracyScore")
        flu = _num(best, "FluencyScore")
        comp = _num(best, "CompletenessScore")
        pron = _num(best, "PronScore")
        palabras = best.get("Words") or []

        if acc is None and flu is None and not palabras:
            return None

        overall = pron if pron is not None else acc

        # Palabras con problema REAL: Omission/Insertion, o puntuación por debajo
        # del umbral (Azure ja-JP castiga la 'r' española aunque sea aceptable,
        # así que no marcamos "Mispronunciation" a 50/100 como fallo).
        malas = []
        for w in palabras:
            palabra = w.get("Word", "")
            etype = w.get("ErrorType") or (w.get("PronunciationAssessment") or {}).get("ErrorType") or "None"
            wscore = _num(w, "AccuracyScore")
            if etype in ("Omission", "Insertion"):
                malas.append(f"【{palabra}】 ({etype})")
            elif wscore is not None and wscore < AZURE_PRON_UMBRAL_PALABRA:
                malas.append(f"【{palabra}】 ({wscore:.0f}/100)")

        # ¿Dijo algo distinto a lo pedido?
        ref_n, oido_n = _norm_jp(referencia), _norm_jp(oido)
        dijo_otra_cosa = bool(ref_n) and bool(oido_n) and ref_n != oido_n

        # Veredicto (para que el LLM no tenga que interpretar los números).
        if dijo_otra_cosa:
            veredicto = "MAL — ha dicho algo distinto a lo pedido"
        elif overall is not None and overall < 55:
            veredicto = f"MAL (global {overall:.0f}/100)"
        elif malas:
            veredicto = "REGULAR — hay palabras que corregir"
        elif overall is not None and overall >= AZURE_PRON_UMBRAL_BIEN:
            veredicto = f"BIEN (global {overall:.0f}/100)"
        elif overall is not None:
            veredicto = f"ACEPTABLE (global {overall:.0f}/100)"
        else:
            veredicto = "sin datos claros"

        lineas = [f"Veredicto: {veredicto}"]

        detalle = []
        if overall is not None:
            detalle.append(f"global {overall:.0f}")
        if acc is not None:
            detalle.append(f"precisión {acc:.0f}")
        if flu is not None:
            detalle.append(f"fluidez {flu:.0f}")
        if comp is not None:
            detalle.append(f"completitud {comp:.0f}")
        if detalle:
            lineas.append("Puntuaciones: " + " · ".join(detalle))

        if malas:
            lineas.append("Palabras con problema: " + ", ".join(malas))

        if referencia and ref_n:
            if dijo_otra_cosa:
                lineas.append(f"Se pidió 「{referencia}」 pero se ha oído 「{oido}」")
            elif not malas:
                lineas.append(f"Ha dicho la frase pedida 「{referencia}」.")

        return "\n".join(lineas)


def transcribir_para_turno(stt: SpeechToText, archivo: str, *, sensei_activo: bool,
                           modo_conv: bool, referencia: str = None):
    """Enruta la transcripción de un turno.

    - Sensei estructurado (activo y no charla): intenta Azure para obtener
      también la evaluación de pronunciación (contra `referencia` si la hay); si
      Azure no está disponible o sin cuota, cae a Groq Whisper con autodetección.
    - Sensei charla: igual que estructurado solo si AZURE_PRON_EN_CHARLA está
      activo; si no, Groq Whisper con autodetección y sin pronunciación.
    - Fuera de sensei: Groq Whisper en español.

    Devuelve `(texto, pron_contexto)` donde `pron_contexto` es un string con el
    resumen de pronunciación o None.
    """
    if sensei_activo and (not modo_conv or AZURE_PRON_EN_CHARLA):
        res = stt.transcribir_con_pronunciacion(archivo, referencia=referencia)
        if res is not None:
            return res["texto"], res.get("pron")
        return stt.transcribir(archivo, idioma=None), None

    if sensei_activo:
        return stt.transcribir(archivo, idioma=None), None

    return stt.transcribir(archivo, idioma="es"), None
