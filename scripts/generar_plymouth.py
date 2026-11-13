"""Genera el tema de arranque/apagado (Plymouth): el «Anillo» de la pantalla de carga.

Barato para la Pi 4 (Plymouth pinta por software): todo lo fijo va cocido en una imagen (brillos, anillo
turquesa y 海斗) y solo se mueven dos sprites pequeños que dan vueltas por el anillo: la perla (una
imagen) y la tabla (36 imágenes con su giro de 10° ya hecho, para no rotar nada en la Pi).
Plymouth no dibuja las estelas de la versión web.

Salida en deploy/plymouth/kaito/ (se commitea; solo hay que volver a correr esto si cambia el diseño):
  fondo.png  brillos, anillo y 海斗 (arranque)     apagado.png  brillos y «またね» (apagado)
  perla.png  la perla (recortada)
  tabla0.png … tabla35.png  la tabla girada de 10° en 10°      negro.png  velo para el apagado
  kaito.script (con los tamaños de las imágenes)
Requiere fonttools, Pillow y Microsoft Edge (ver generar_splash.py).
"""
import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_arranque import (AMBAR, ANILLO, DEFS, ESC_PERLA, ESC_TABLA, FONDO_CSS, INCL, PERLA, R, TABLA,  # noqa: E402
                              kanji)
from generar_splash import EDGE, FUENTE, RAIZ, TTCollection  # noqa: E402
from fontTools.pens.svgPathPen import SVGPathPen  # noqa: E402
from fontTools.pens.transformPen import TransformPen  # noqa: E402

DEST = os.path.join(RAIZ, "deploy", "plymouth", "kaito")
PASOS = 36  # imágenes de la tabla: una cada 360/PASOS grados

SCRIPT = r'''# Anillo de Kaito (barato para la Pi). Al arrancar: fondo fijo y la perla y la tabla dando vueltas por el anillo.
# Al apagar o reiniciar: solo «mata ne» (en kana) sobre los brillos, que tras unos segundos se apaga a negro.
# La pantalla es de 480x480; se centra por si cambia la resolución.
# Todo el estado va en `global.` (en Plymouth, lo que se asigna dentro de una función es local).
Window.SetBackgroundTopColor(0.043, 0.031, 0.020);
Window.SetBackgroundBottomColor(0.043, 0.031, 0.020);

global.ox = Window.GetWidth() / 2 - 240;
global.oy = Window.GetHeight() / 2 - 240;

fun capa(nombre, z) {
    s = Sprite(Image(nombre));
    s.SetPosition(global.ox, global.oy, z);
    return s;
}

global.velo = capa("negro.png", 9);
global.velo.SetOpacity(0);
global.opacidad_velo = 0;
global.t = 0;

if (Plymouth.GetMode() == "boot") {
    global.fondo = capa("fondo.png", 1);   # con referencia: un sprite suelto puede liberarse y desaparecer
    perla_img = Image("perla.png");
    global.perla = Sprite(perla_img);
    global.pw = perla_img.GetWidth() / 2;
    global.ph = perla_img.GetHeight() / 2;
    global.tablas = [];
    for (i = 0; i < @@PASOS@@; i++) global.tablas[i] = Image("tabla" + i + ".png");
    global.tabla = Sprite(global.tablas[0]);
    global.tw = global.tablas[0].GetWidth() / 2;
    global.th = global.tablas[0].GetHeight() / 2;

}
fun refrescar_arranque() {
        global.t = global.t + 1;
        vuelta = global.t / 200;                                  # una vuelta cada 200 cuadros (~4 s)
        a = vuelta * 2 * Math.Pi;
        global.perla.SetPosition(global.ox + 240 + @@R@@ * Math.Sin(a) - global.pw,
                                 global.oy + 240 - @@R@@ * Math.Cos(a) - global.ph, 4);
        b = a + Math.Pi;                                          # la tabla, enfrente
        global.tabla.SetPosition(global.ox + 240 + @@R@@ * Math.Sin(b) - global.tw,
                                 global.oy + 240 - @@R@@ * Math.Cos(b) - global.th, 3);
        f = vuelta + 0.5;
        f = f - Math.Int(f);
        global.tabla.SetImage(global.tablas[Math.Int(f * @@PASOS@@)]);
}

fun refrescar_apagado() {
    global.t = global.t + 1;
    if (global.t > 150) {                                         # tras ~3 s se apaga a negro
        global.opacidad_velo = global.opacidad_velo + 0.004;
        if (global.opacidad_velo > 1) global.opacidad_velo = 1;
        global.velo.SetOpacity(global.opacidad_velo);
    }
}

if (Plymouth.GetMode() == "boot") Plymouth.SetRefreshFunction(refrescar_arranque);
else {                                                            # apagando o reiniciando
    global.fondo = capa("apagado.png", 1);
    Plymouth.SetRefreshFunction(refrescar_apagado);
}
'''


def texto(cadena, cx, base, px):
    """Cadena en kana con UNA escala común (no la de cada glifo, que las descuadraría), centrada en cx."""
    f = TTCollection(FUENTE).fonts[0]
    gs, cmap, hm = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    esc, hueco = px / f["head"].unitsPerEm, 0.12 * px
    nombres = [cmap[ord(c)] for c in cadena]
    x, out = cx - (sum(hm[n][0] * esc for n in nombres) + hueco * (len(nombres) - 1)) / 2, []
    for n in nombres:
        pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
        gs[n].draw(TransformPen(pen, (esc, 0, 0, -esc, x, base)))
        out.append(pen.getCommands())
        x += hm[n][0] * esc + hueco
    return " ".join(out)


def svg(cuerpo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" width="480" height="480" '
            f'style="position:absolute;left:0;top:0"><defs>{DEFS}</defs>{cuerpo}</svg>')


def raster(contenido, transparente=True):
    """Rasteriza a 480x480 y devuelve la imagen."""
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "x.html")
        open(p, "w", encoding="utf-8").write(
            f'<html><body style="margin:0;background:{"transparent" if transparente else "#000"}">{contenido}</body></html>')
        out = os.path.join(t, "o.png")
        args = [EDGE, "--headless", "--disable-gpu", f"--screenshot={out}", "--window-size=480,480",
                "--hide-scrollbars", "file:///" + p.replace("\\", "/")]
        if transparente:
            args.insert(2, "--default-background-color=00000000")
        subprocess.run(args, capture_output=True, timeout=90, check=True)
        return Image.open(out).convert("RGBA" if transparente else "RGB")


def guardar(im, nombre):
    im.save(os.path.join(DEST, nombre), optimize=True)


if __name__ == "__main__":
    os.makedirs(DEST, exist_ok=True)
    for viejo in glob.glob(os.path.join(DEST, "*.png")):  # fuera lo del diseño anterior
        os.remove(viejo)
    fondo = (f'<div style="position:absolute;left:0;top:0;width:480px;height:480px;background:{FONDO_CSS}"></div>'
             + svg(f'<circle cx="240" cy="240" r="{R}" fill="none" stroke="{ANILLO}" stroke-opacity=".4" stroke-width="2"/>'
                   f'<path fill="{AMBAR}" d="{kanji()}"/>'))
    guardar(raster(fondo, transparente=False), "fondo.png")
    apagado = (f'<div style="position:absolute;left:0;top:0;width:480px;height:480px;background:{FONDO_CSS}"></div>'
               + svg(f'<path fill="{AMBAR}" d="{texto("またね", 240, 276, 92)}"/>'))   # solo los brillos y la despedida
    guardar(raster(apagado, transparente=False), "apagado.png")
    # perla y tabla centradas en (240,240); se recortan a una caja simétrica para poder centrarlas luego
    im = raster(svg(f'<g transform="translate(240 240) scale({ESC_PERLA})">{PERLA}</g>'))
    caja = im.getchannel("A").point(lambda a: 255 if a > 3 else 0).getbbox()
    m = max(240 - caja[0], 240 - caja[1], caja[2] - 240, caja[3] - 240)
    guardar(im.crop((240 - m, 240 - m, 240 + m, 240 + m)), "perla.png")
    im = raster(svg(f'<g transform="translate(240 240) scale({ESC_TABLA}) rotate({INCL})">{TABLA}</g>'))
    ancho = 46  # medio lado de la caja: cabe la tabla entera girada en cualquier ángulo
    base = im.crop((240 - ancho, 240 - ancho, 240 + ancho, 240 + ancho))
    for k in range(PASOS):  # en la órbita, a θ grados en sentido horario la tabla va girada θ
        guardar(base.rotate(-k * 360 / PASOS, resample=Image.BICUBIC), f"tabla{k}.png")
    guardar(raster('<div style="width:480px;height:480px;background:#0b0805"></div>', transparente=False), "negro.png")
    texto = SCRIPT.replace("@@R@@", str(R)).replace("@@PASOS@@", str(PASOS))
    open(os.path.join(DEST, "kaito.script"), "w", encoding="utf-8", newline="\n").write(texto)
    print("ok", len(glob.glob(os.path.join(DEST, "*.png"))), "imágenes")
