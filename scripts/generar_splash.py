"""Genera la imagen de arranque de Kaito (480x480, pantalla redonda) y sus derivados.

Salida (se commitea, no hace falta volver a correr esto salvo que cambie el diseño):
  deploy/splash/kaito-arranque.svg      logo completo, fondo ámbar oscuro
  deploy/plymouth/kaito/logo.png        el SVG sin la perla (la perla late aparte)
  deploy/plymouth/kaito/pearl.png       la perla sola, con transparencia
Requiere: fonttools, Pillow y Microsoft Edge (para rasterizar). Los kanji salen
de la fuente Yu Gothic Bold de Windows convertidos a trazos, así que el resultado
no depende de fuentes del robot.
"""
import os
import subprocess
import sys
import tempfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTCollection

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FUENTE = r"C:\Windows\Fonts\YuGothB.ttc"
AMBAR, FONDO_C, FONDO_B = "#f0b24a", "#4a2f12", "#150c05"
PERLA = (190, 346)


def glifo(fuente, ch, x, base, alto):
    """Trazo SVG del carácter `ch` con su caja de `alto` px, esquina izq. en x."""
    gs = fuente.getGlyphSet()
    g = fuente.getBestCmap()[ord(ch)]
    b = BoundsPen(gs)
    gs[g].draw(b)
    x0, y0, x1, y1 = b.bounds
    s = alto / (y1 - y0)
    pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x - x0 * s, base + y0 * s)))
    return pen.getCommands(), (x1 - x0) * s


def svg(con_perla=True, solo_perla=False):
    f = TTCollection(FUENTE).fonts[0]
    d1, w1 = glifo(f, "海", 0, 0, 104)
    d2, w2 = glifo(f, "斗", 0, 0, 104)
    gap = 22
    x0 = 240 - (w1 + gap + w2) / 2
    k1, _ = glifo(f, "海", x0, 255, 104)
    k2, _ = glifo(f, "斗", x0 + w1 + gap, 255, 104)
    px, py = PERLA
    perla = f'''<g id="perla" fill="none" stroke="{AMBAR}" stroke-linecap="round">
    <circle cx="{px}" cy="{py}" r="25" stroke-width="3.5"/>
    <circle cx="{px}" cy="{py}" r="18" stroke-width="2" opacity=".7"/>
    <path d="M{px-12} {py-6} Q{px-7} {py-12} {px} {py-12}" stroke-width="3"/>
  </g>'''
    resto = f'''
  <g fill="{AMBAR}"><path d="{k1}"/><path d="{k2}"/></g>
  <g transform="rotate(-33 300 338)" fill="none" stroke="{AMBAR}" stroke-linecap="round">
    <ellipse cx="300" cy="338" rx="66" ry="19" stroke-width="3.5"/>
    <line x1="262" y1="338" x2="332" y2="338" stroke-width="2.5" opacity=".8"/>
  </g>
  <path d="M150 396 C185 377 222 405 262 392 S335 376 376 392 C338 396 305 411 262 404 S185 392 150 396 Z" fill="{AMBAR}"/>'''
    cuerpo = ("" if solo_perla else resto) + (perla if (con_perla or solo_perla) else "")
    fondo = "" if solo_perla else f'''<defs><radialGradient id="f" cx="50%" cy="45%" r="62%">
    <stop offset="0" stop-color="{FONDO_C}"/><stop offset="1" stop-color="{FONDO_B}"/></radialGradient></defs>
  <rect width="480" height="480" fill="url(#f)"/>'''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" width="480" height="480">'
            f"{fondo}{cuerpo}\n</svg>\n")


def png(contenido, destino, transparente=False):
    with tempfile.TemporaryDirectory() as t:
        h = os.path.join(t, "x.html")
        bg = "transparent" if transparente else "#000"
        open(h, "w", encoding="utf-8").write(
            f'<html><body style="margin:0;background:{bg}">{contenido}</body></html>')
        out = os.path.join(t, "o.png")
        args = [EDGE, "--headless", "--disable-gpu", f"--screenshot={out}",
                "--window-size=480,480", "--hide-scrollbars", "file:///" + h.replace("\\", "/")]
        if transparente:
            args.insert(2, "--default-background-color=00000000")
        subprocess.run(args, capture_output=True, timeout=90, check=True)
        os.replace(out, destino)


if __name__ == "__main__":
    os.makedirs(os.path.join(RAIZ, "deploy", "splash"), exist_ok=True)
    pl = os.path.join(RAIZ, "deploy", "plymouth", "kaito")
    os.makedirs(pl, exist_ok=True)
    open(os.path.join(RAIZ, "deploy", "splash", "kaito-arranque.svg"), "w", encoding="utf-8").write(svg())
    png(svg(con_perla=False), os.path.join(pl, "logo.png"))
    png(svg(solo_perla=True), os.path.join(pl, "pearl.png"), transparente=True)
    print("ok")
