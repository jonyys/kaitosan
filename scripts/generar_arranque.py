"""Genera deploy/arranque/index.html: la pantalla de carga animada de Kaito (idea «Anillo»).

海斗 en el centro, sobre los brillos ámbar y turquesa del robot, dentro de un anillo turquesa por el
que dan vueltas la perla rosa y la tabla (una enfrente de la otra, cada una con su estela). Cuando el
servicio responde, el giro frena con la perla arriba y la tabla abajo, 海斗 se apaga, funde a negro y
pasa a la cara.
Con --demo RUTA escribe además una página autónoma que repite el ciclo solo con CSS
(sin servidor ni JavaScript), para verla en cualquier navegador.
Con ?fps en la URL mide cuadros por segundo y los manda a /fps del servicio (se ve en su log).

Hecha para la Pi 4 (Chromium con accesibilidad forzada, sin GPU potente): mientras carga solo gira UNA
capa (transform, a 24 cuadros/s). Sin filtros, recortes redondos ni gradientes animados.
Los kanji van como trazos (Yu Gothic Bold): no dependen de fuentes del robot.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_splash import glifo, TTCollection, FUENTE, RAIZ  # noqa: E402

R = 212  # radio del anillo
ANILLO = "#7fe3d8"
AMBAR = "#f0b24a"
# Mismos colores que los brillos de las pantallas del robot (_kiosko.html: ámbar arriba a la derecha, turquesa
# abajo a la izquierda), pero a propósito NO iguales: aquí el ámbar sube desde abajo y el turquesa va arriba a la izquierda.
FONDO_CSS = ("radial-gradient(300px 220px at 50% 106%, rgba(224, 164, 77, .26), transparent 72%), "
             "radial-gradient(250px 250px at 20% 18%, rgba(79, 209, 197, .17), transparent 70%), #0b0805")

DEFS = '''<radialGradient id="pg" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="#ffc9e1"/><stop offset=".7" stop-color="#ff8fc0"/><stop offset="1" stop-color="#7a2a55"/></radialGradient>
<radialGradient id="ph"><stop offset="0" stop-color="#ff8fc0" stop-opacity=".5"/><stop offset="1" stop-color="#ff8fc0" stop-opacity="0"/></radialGradient>'''

# perla y tabla centradas en (0,0); la tabla lleva la inclinación de -7° que tenía en la demo
PERLA = ('<circle r="34" fill="url(#ph)"/><circle r="13" fill="url(#pg)"/>'
         '<ellipse cx="-4" cy="-5" rx="3.6" ry="2.1" fill="#fff" opacity=".85" transform="rotate(-30 -4 -5)"/>')
TABLA = ('<ellipse rx="58" ry="16" fill="#7a4a12" stroke="#f6c063" stroke-width="3"/>'
         '<line x1="-32" x2="32" stroke="#f6c063" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>')
ESC_PERLA, ESC_TABLA, INCL = .6, .5, -7


def estela(color):
    """Tres arcos que acaban arriba (12 en punto): lo que deja atrás lo que gira en sentido horario."""
    out = []
    for a, o in zip((42, 26, 12), (.12, .22, .4)):
        x, y = 240 - R * math.sin(math.radians(a)), 240 - R * math.cos(math.radians(a))
        out.append(f'<path d="M{x:.1f} {y:.1f} A{R} {R} 0 0 1 240 {240 - R}" fill="none" stroke="{color}" '
                   f'stroke-opacity="{o}" stroke-width="3" stroke-linecap="round"/>')
    return "".join(out)


def orbita():
    """La perla arriba y la tabla abajo, con sus estelas; la capa entera gira alrededor del centro."""
    arriba = 240 - R
    return (estela("#ff8fc0") + f'<g transform="translate(240 {arriba}) scale({ESC_PERLA})">{PERLA}</g>'
            + '<g transform="rotate(180 240 240)">' + estela("#f0b24a")
            + f'<g transform="translate(240 {arriba}) scale({ESC_TABLA}) rotate({INCL})">{TABLA}</g></g>')


def kanji():
    f = TTCollection(FUENTE).fonts[0]
    _, w1 = glifo(f, "海", 0, 0, 100)
    _, w2 = glifo(f, "斗", 0, 0, 100)
    gap = 20
    x0 = 240 - (w1 + gap + w2) / 2
    k1, _ = glifo(f, "海", x0, 290, 100)
    k2, _ = glifo(f, "斗", x0 + w1 + gap, 290, 100)
    return k1 + " " + k2


CSS = r'''
  html, body { margin: 0; height: 100%; background: #0b0805; overflow: hidden; cursor: none; }
  body { display: flex; align-items: center; justify-content: center; }
  #stage { position: relative; width: 480px; height: 480px; flex: none; overflow: hidden; background: @@FONDO@@; }
  #stage > * { position: absolute; left: 0; top: 0; width: 480px; height: 480px; }
  /* lo único que se mueve mientras carga: la capa de la perla y la tabla (a 24 cuadros/s: en la Pi cada cuadro cuesta) */
  #orbita { transform-origin: 240px 240px; will-change: transform; animation: giro 4s steps(96) infinite; }
  @keyframes giro { to { transform: rotate(360deg); } }
  #kanji { will-change: opacity; }
  #fin { background: #0b0805; opacity: 0; z-index: 9; will-change: opacity; }
  /* cargado: el giro frena (lo hace el script) y 海斗 se apaga; luego fundido a negro */
  #stage.cargado #kanji { opacity: 0; transition: opacity 1.2s ease-in-out 2.4s; }
  #stage.cerrando #fin { opacity: 1; transition: opacity .8s; }
'''

DEMO_CSS = r'''
  /* DEMO solo con CSS: ciclo de 12 s (unos 6 s cargando, el giro frena, fundido) */
  #orbita { animation: d-orb 12s infinite; }
  @keyframes d-orb { 0% { transform: rotate(0); animation-timing-function: linear; }
    55% { transform: rotate(720deg); animation-timing-function: cubic-bezier(.2,.6,.3,1); } 68%, 100% { transform: rotate(1080deg); } }
  #kanji { animation: d-kanji 12s infinite; }
  @keyframes d-kanji { 0%, 66% { opacity: 1; } 78%, 97% { opacity: 0; } 97.1%, 100% { opacity: 1; } }
  #fin { animation: d-fin 12s infinite; }
  @keyframes d-fin { 0%, 80% { opacity: 0; } 86%, 96% { opacity: 1; } 100% { opacity: 0; } }
'''

CUERPO = r'''<div id="stage">
  <svg id="anillo" viewBox="0 0 480 480"><circle cx="240" cy="240" r="@@R@@" fill="none" stroke="@@ANILLO@@" stroke-opacity=".4" stroke-width="2"/></svg>
  <svg id="kanji" viewBox="0 0 480 480"><path fill="@@AMBAR@@" d="@@KANJI@@"/></svg>
  <svg id="orbita" viewBox="0 0 480 480"><defs>@@DEFS@@</defs>@@ORBITA@@</svg>
  <div id="fin"></div>
</div>'''

SCRIPT_REAL = r'''<script>
  var stage = document.getElementById("stage"), orbita = document.getElementById("orbita");
  function ajustar() { // la pantalla es de 480x480; en otras ventanas se escala
    var s = Math.min(innerWidth, innerHeight) / 480;
    if (Math.abs(s - 1) < 0.01) return;
    stage.style.transform = "scale(" + s + ")";
    stage.style.margin = (-(480 - 480 * s) / 2) + "px";
  }
  addEventListener("resize", ajustar); ajustar();

  var URL_KAITO = "http://localhost:5000";
  var FPS = /[?&]fps/.test(location.search); // medición: cuadros/s al log del servicio, sin salir
  function terminar(fn) { // el giro frena con la perla arriba; 海斗 se apaga; fundido
    var m = new DOMMatrix(getComputedStyle(orbita).transform);
    var a = Math.atan2(m.b, m.a) * 180 / Math.PI; if (a < 0) a += 360;
    orbita.style.animation = "none"; orbita.style.transform = "rotate(" + a + "deg)";
    orbita.getBoundingClientRect(); // fija el punto de partida antes de la transición
    orbita.style.transition = "transform 3s cubic-bezier(.2, .6, .3, 1)";
    orbita.style.transform = "rotate(720deg)"; // un múltiplo de 360: acaba con la perla arriba
    stage.classList.add("cargado");
    setTimeout(function () { stage.classList.add("cerrando"); }, 4200);
    setTimeout(fn, 5100);
  }
  function reiniciar() { orbita.style.cssText = ""; stage.className = ""; }
  if (FPS) {
    var n = 0, t0 = performance.now();
    (function tic() { n++; requestAnimationFrame(tic); })();
    setInterval(function () {
      var dt = (performance.now() - t0) / 1000;
      new Image().src = URL_KAITO + "/fps?fase=" + (stage.classList.contains("cargado") ? "frenada" : "carga") +
                        "&fps=" + (n / dt).toFixed(1);
      n = 0; t0 = performance.now();
    }, 1000);
    (function ciclo() {
      reiniciar();
      setTimeout(function () { terminar(function () { setTimeout(ciclo, 300); }); }, 4000);
    })();
  } else {
    var minimo = Date.now() + 3000; // que se vea el anillo al menos un momento
    (function probar() {
      fetch(URL_KAITO, { mode: "no-cors", cache: "no-store" }).then(function () {
        setTimeout(function () { terminar(function () { location.replace(URL_KAITO); }); },
                   Math.max(0, minimo - Date.now()));
      }).catch(function () { setTimeout(probar, 1000); });
    })();
  }
</script>'''


def cuerpo():
    return (CUERPO.replace("@@R@@", str(R)).replace("@@ANILLO@@", ANILLO).replace("@@AMBAR@@", AMBAR)
            .replace("@@KANJI@@", kanji()).replace("@@DEFS@@", DEFS).replace("@@ORBITA@@", orbita()))


def css():
    return CSS.replace("@@FONDO@@", FONDO_CSS)


def pagina_real():
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>Kaito</title>\n<style>{css()}</style>\n</head>\n<body>\n{cuerpo()}\n{SCRIPT_REAL}\n</body>\n</html>\n')


def pagina_demo():
    c = re.sub(r"  html, body \{.*?\}\n  body \{.*?\}\n", "", css(), count=1, flags=re.S)
    c = c.replace("#stage { position: relative; width: 480px; height: 480px; flex: none; overflow: hidden;",
                  "#stage { position: absolute; left: 0; top: 0; transform-origin: 0 0; width: 480px; height: 480px;"
                  " overflow: hidden; border-radius: 50%;")
    return f'''<meta charset="utf-8">
<title>Arranque de Kaito</title>
<style>
  :root {{ --bg: #0b0805; --fg: #f3e6cf; --soft: #b9a68a; color-scheme: dark; }}
  body {{ background: var(--bg); color: var(--fg); font-family: system-ui, sans-serif;
         padding-block: 24px; padding-left: max(16px, env(safe-area-inset-left, 0px));
         padding-right: max(16px, env(safe-area-inset-right, 0px)); display: flex; flex-direction: column;
         align-items: center; gap: 14px; min-height: 100vh; box-sizing: border-box; }}
  #marco {{ position: relative; flex: none; }}
  p {{ margin: 0; font-size: 14px; color: var(--soft); text-align: center; max-width: 44ch; text-wrap: balance; }}
{c}{DEMO_CSS}
</style>
<div id="marco">
{cuerpo()}
</div>
<p>Bucle de 12 s: la perla y la tabla dan vueltas por el anillo y, al terminar, frenan con la perla arriba.</p>
<script>
  var stage = document.getElementById("stage"), marco = document.getElementById("marco");
  function ajustar() {{
    var s = Math.max(0.3, Math.min(innerWidth - 32, innerHeight - 110, 640) / 480);
    marco.style.width = marco.style.height = (480 * s) + "px";
    stage.style.transform = "scale(" + s + ")";
  }}
  addEventListener("resize", ajustar); ajustar();
</script>
'''


if __name__ == "__main__":
    os.makedirs(os.path.join(RAIZ, "deploy", "arranque"), exist_ok=True)
    open(os.path.join(RAIZ, "deploy", "arranque", "index.html"), "w", encoding="utf-8").write(pagina_real())
    if "--demo" in sys.argv:
        ruta = sys.argv[sys.argv.index("--demo") + 1]
        open(ruta, "w", encoding="utf-8").write(pagina_demo())
    print("ok")
