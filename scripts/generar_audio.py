#!/usr/bin/env python3
"""Pregenera un mp3 por palabra de vocabulario N5 y por kanji, para el botón
"escuchar" (icono de sonido) de las fichas del temario y de los kanji.

    python scripts/generar_audio.py [--voz ja-JP-KeitaNeural] [--force]

Reejecutable e incremental: salta los mp3 que ya existen (--force los rehace).
Necesita internet (edge-tts, sin coste). Los mp3 van a static/audio/jp/ con el
nombre = md5(texto) y SE COMMITEAN: el kiosko tiene que sonar offline tras un
git pull. La clave md5 es la misma que usa app.py:audio_url().
"""
import argparse
import asyncio
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM
from ai.sensei.kanji_n5 import KANJI_N5

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "static", "audio", "jp")
VOZ = "ja-JP-KeitaNeural"  # la misma que habla Kaito (ai/text_to_speech.py)


def clave(texto: str) -> str:
    return hashlib.md5(texto.strip().encode("utf-8")).hexdigest()


def textos():
    """Textos japoneses únicos que llevan audio, en el mismo criterio que el
    front (app.py / plantillas):
      - vocabulario N5 (no kanji): la lectura kana si existe y ≠ jp, si no el jp.
      - kanji: reading_card, o reading si no hay.
    """
    vistos = set()
    for u in CURRICULUM:
        for e in u.get("items", []):
            if e.get("kind") != "vocabulario" or e.get("tipo") == "kanji":
                continue
            jp = str(e.get("jp") or "").strip()
            if not jp:
                continue
            rd = str(e.get("reading") or "").strip()
            t = rd if rd and rd != jp else jp
            if t not in vistos:
                vistos.add(t)
                yield t
    for k in KANJI_N5:
        t = str(k.get("reading_card") or k.get("reading") or "").strip()
        if t and t not in vistos:
            vistos.add(t)
            yield t


async def sintetizar(texto: str, voz: str, ruta: str):
    import edge_tts

    com = edge_tts.Communicate(texto, voz)
    with open(ruta, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
    if os.path.getsize(ruta) == 0:
        os.remove(ruta)
        raise RuntimeError("mp3 vacío (edge-tts no devolvió audio)")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", default=VOZ)
    ap.add_argument("--force", action="store_true",
                    help="rehace también los que ya existen")
    args = ap.parse_args()

    os.makedirs(DESTINO, exist_ok=True)
    pendientes = []
    for t in textos():
        ruta = os.path.join(DESTINO, clave(t) + ".mp3")
        if args.force or not os.path.exists(ruta):
            pendientes.append((t, ruta))

    total = len(pendientes)
    print(f"{total} audios por generar (voz {args.voz}) -> {DESTINO}")
    fallos = 0
    for i, (t, ruta) in enumerate(pendientes, 1):
        for intento in range(3):
            try:
                await sintetizar(t, args.voz, ruta)
                break
            except Exception as e:  # transitorios de red: reintenta
                if intento == 2:
                    fallos += 1
                    print(f"  ✗ {t!r}: {e}")
                else:
                    await asyncio.sleep(1.5)
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total}")
    print(f"listo ({total - fallos} ok, {fallos} fallos)")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    asyncio.run(main())
