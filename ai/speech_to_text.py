import base64
import json
import os
import tempfile

import soundfile as sf
from groq import Groq

from core.config import (
    AZURE_PRON_EN_CHARLA,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    AZURE_STT_LIMITE_SEG_MES,
    GROQ_API_KEY,
)
from core.token_tracker import TokenTracker


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
    def transcribir_con_pronunciacion(self, archivo_audio: str) -> dict | None:
        """Envía el audio a Azure Speech (japonés) y devuelve un dict:

            {"texto": "<transcripción>", "pron": "<resumen legible o None>"}

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

            pron_cfg = base64.b64encode(json.dumps({
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
            texto = (best.get("Display") or best.get("Lexical") or "").strip()
            pron = self._resumir_pronunciacion(best)
            print(f"✅ Transcripción (Azure): {texto}")
            if pron:
                print(f"🗣️  Pronunciación: {pron.replace(chr(10), ' | ')}")
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
    def _resumir_pronunciacion(best: dict) -> str | None:
        """Convierte la respuesta de Azure en un resumen breve para el profesor."""
        pa = best.get("PronunciationAssessment") or {}
        acc = pa.get("AccuracyScore")
        flu = pa.get("FluencyScore")
        pro = pa.get("ProsodyScore")
        if acc is None and flu is None:
            return None

        partes = []
        if acc is not None:
            partes.append(f"Precisión: {acc:.0f}/100")
        if flu is not None:
            partes.append(f"Fluidez: {flu:.0f}/100")
        if pro is not None:
            partes.append(f"Prosodia: {pro:.0f}/100")
        lineas = [" · ".join(partes)]

        # Fonemas más flojos (puntuación < 60), como mucho 3.
        flojos = []
        for w in best.get("Words", []) or []:
            palabra = w.get("Word", "")
            for ph in w.get("Phonemes", []) or []:
                score = (ph.get("PronunciationAssessment") or {}).get("AccuracyScore")
                if score is not None and score < 60:
                    flojos.append((score, ph.get("Phoneme", ""), palabra))
        flojos.sort(key=lambda x: x[0])
        if flojos:
            detalle = ", ".join(
                f"{ph} en 「{palabra}」 ({score:.0f})" for score, ph, palabra in flojos[:3]
            )
            lineas.append(f"Sonidos flojos: {detalle}")
        elif acc is not None and acc >= 80:
            lineas.append("Sin errores destacables.")

        return "\n".join(lineas)


def transcribir_para_turno(stt: SpeechToText, archivo: str, *, sensei_activo: bool, modo_conv: bool):
    """Enruta la transcripción de un turno.

    - Sensei estructurado (activo y no charla): intenta Azure para obtener
      también la evaluación de pronunciación; si Azure no está disponible o sin
      cuota, cae a Groq Whisper con autodetección de idioma.
    - Sensei charla: igual que estructurado solo si AZURE_PRON_EN_CHARLA está
      activo; si no, Groq Whisper con autodetección y sin pronunciación.
    - Fuera de sensei: Groq Whisper en español.

    Devuelve `(texto, pron_contexto)` donde `pron_contexto` es un string con el
    resumen de pronunciación o None.
    """
    if sensei_activo and (not modo_conv or AZURE_PRON_EN_CHARLA):
        res = stt.transcribir_con_pronunciacion(archivo)
        if res is not None:
            return res["texto"], res.get("pron")
        return stt.transcribir(archivo, idioma=None), None

    if sensei_activo:
        return stt.transcribir(archivo, idioma=None), None

    return stt.transcribir(archivo, idioma="es"), None
