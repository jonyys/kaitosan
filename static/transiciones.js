// Transiciones de pantalla completa del robot: cara <-> reloj y las que tapan la
// pantalla al cambiar a sensei. Se pintan en una capa encima de todo. El reloj es otra
// página: la capa acaba igual que la primera imagen de la de destino y entonces se
// navega, y el navegador mantiene la imagen hasta pintar la nueva, así que no se nota.
(function () {
  const acota = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const tramo = (p, a, b) => acota((p - a) / (b - a));
  const mezcla = (a, b, t) => a + (b - a) * t;
  const suave = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  const rebota = (t) => 1 + 2.7 * Math.pow(t - 1, 3) + 1.7 * Math.pow(t - 1, 2);
  const canales = (h) => [1, 3, 5].map((i) => parseInt(h.substr(i, 2), 16));
  const mezclaColor = (a, b, t) => {
    const B = canales(b);
    return `rgb(${canales(a).map((v, i) => Math.round(mezcla(v, B[i], t))).join(",")})`;
  };
  const azar = (lista) => lista[Math.floor(Math.random() * lista.length)];

  const OJO = "M 99.4044 60.9612 C 97.3654 96.1972 99.9334 95.9602 56.8394 105.9012 C 13.7454 115.8422 -6.3046 84.4252 1.7444 47.9972 C 9.7934 11.5692 27.9594 1.1052 51.6544 0.0312 C 75.3494 -1.0428 101.4434 25.7252 99.4044 60.9612 Z";
  const CEJA = "M 172.584 177.846 C 170.394 190.376 156.145 183.855 140.547 185.604 C 122.324 187.647 106.408 210.513 105.285 198.601 C 104.162 186.689 132.63 167.536 148.002 166.059 C 163.953 164.527 174.774 165.316 172.584 177.846 Z";
  const BOCA = "M 265.112 239.115 C 265.112 243.048 255.383 247.237 243.382 247.237 C 231.381 247.237 221.652 243.048 221.652 239.115 C 221.652 235.182 230.758 240.737 242.759 240.737 C 254.76 240.737 265.112 235.182 265.112 239.115 Z";
  const BOCA_MINI = "M 247.4 243 C 247.4 245.5 245.6 247.5 243.382 247.5 C 241.1 247.5 239.4 245.5 239.4 243 C 239.4 240.5 241.1 238.5 243.382 238.5 C 245.6 238.5 247.4 240.5 247.4 243 Z";
  const NUM = /-?\d+(?:\.\d+)?/g;
  const OJOS_X = [130, 350];
  const CEJAS_CENTRO = [[110, 110], [370, 110]];
  const FONDO_CARA = "#15100a";
  const DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  const COLORES = {
    dia: { fondo: "#15100a", texto: "#fff3da", suave: "#b99a68" },
    noche: { fondo: "#000000", texto: "#d0d0d0", suave: "#7c7c7c" },
  };
  const RELOJ_GUARDADO = "kaito.reloj";
  // ponytail: medidas de la pantalla de 480 px para el primer paso tras arrancar,
  // antes de haber visto el reloj; si la cara no encaja, ajustar aquí viéndolo en la Pi.
  const RELOJ_POR_DEFECTO = {
    familia: "'M PLUS Rounded 1c', 'Nunito', 'Segoe UI', system-ui, sans-serif",
    peso: "200", tam: 64, espacio: "-2px", arriba: 177.7, alto: 89,
    trozos: [[105.7, 75.4], [181, 21.3], [202.3, 75.4], [277.7, 21.3], [299, 75.4]],
    fecha: { izq: 105.7, ancho: 268.5, arriba: 262.7, tam: "16px", espacio: "1px", familia: "'M PLUS Rounded 1c', 'Nunito', 'Segoe UI', system-ui, sans-serif" },
    aviso: { izq: 0, arriba: 411.6, ancho: 480, tam: "14px", html: "Desliza para ver alarmas y recordatorios" },
  };

  let enCurso = false;

  function dentroDe(html) {
    const capa = document.createElement("div");
    capa.id = "kaitoTransicion";
    capa.style.cssText = "position:fixed;inset:0;z-index:99999;overflow:hidden;contain:strict";
    capa.innerHTML = html;
    document.body.appendChild(capa);
    return capa;
  }

  // El temporizador de reserva asegura que siempre termina, aunque se paren los cuadros
  function correr(ms, pinta) {
    return new Promise((listo) => {
      let acabado = false;
      const t0 = performance.now();
      const acabar = () => {
        if (acabado) return;
        acabado = true;
        pinta(1);
        listo();
      };
      const cuadro = (ahora) => {
        if (acabado) return;
        const t = (ahora - t0) / ms;
        if (t >= 1) return acabar();
        pinta(Math.max(0, t));
        requestAnimationFrame(cuadro);
      };
      pinta(0);
      requestAnimationFrame(cuadro);
      setTimeout(acabar, ms + 400);
    });
  }

  // ── El reloj ───────────────────────────────────────────────────────────────
  function enFranja(noche, d) {
    if (!noche || !noche.enabled) return false;
    const [sh, sm] = noche.start.split(":").map(Number);
    const [eh, em] = noche.end.split(":").map(Number);
    const ahora = d.getHours() * 60 + d.getMinutes();
    const ini = sh * 60 + sm, fin = eh * 60 + em;
    return ini <= fin ? ahora >= ini && ahora < fin : ahora >= ini || ahora < fin;
  }

  function esDeNoche() {
    if (window.__nocheManual != null) return window.__nocheManual;
    return enFranja(window.__kioskoNoche, new Date());
  }

  // Lo llama el reloj al cargar: la cara no puede medirlo, y así acaba clavada en él
  function medirReloj() {
    const hora = document.getElementById("hora");
    const fecha = document.getElementById("fecha");
    const aviso = document.getElementById("scrollHint");
    const texto = hora && hora.firstChild;
    if (!texto || texto.length !== 8 || window.scrollY !== 0) return null;
    const estilo = getComputedStyle(hora);
    const cajaDe = (a, b) => {
      const r = document.createRange();
      r.setStart(texto, a);
      r.setEnd(texto, b);
      return r.getBoundingClientRect();
    };
    const caja = cajaDe(0, 8);
    const estiloFecha = getComputedStyle(fecha);
    const cajaFecha = fecha.getBoundingClientRect();
    const datos = {
      familia: estilo.fontFamily, peso: estilo.fontWeight, tam: parseFloat(estilo.fontSize),
      espacio: estilo.letterSpacing, arriba: caja.top, alto: caja.height,
      trozos: [[0, 2], [2, 3], [3, 5], [5, 6], [6, 8]].map(([a, b]) => {
        const c = cajaDe(a, b);
        return [c.left, c.width];
      }),
      fecha: { izq: cajaFecha.left, ancho: cajaFecha.width, arriba: cajaFecha.top, tam: estiloFecha.fontSize, espacio: estiloFecha.letterSpacing, familia: estiloFecha.fontFamily },
    };
    // Los dos puntos del reloj no están en el centro de la caja de texto: se pintan en un
    // canvas ampliado y se miden (centro, radio y separación de cada punto), para que los
    // ojos acaben justo ahí. Con constantes a ojo se veía un salto de unos píxeles.
    try {
      const E = 8, tam = parseFloat(estilo.fontSize) * E, pad = 4 * E;
      const cv = document.createElement("canvas");
      cv.width = Math.ceil(tam) + 2 * pad;
      cv.height = Math.ceil(tam * 1.6);
      const m = cv.getContext("2d", { willReadFrequently: true });
      m.font = `${estilo.fontWeight} ${tam}px ${estilo.fontFamily}`;
      // Alto de la letra a su tamaño real (a 8x el redondeo de la caja no sería el de la página)
      const m1 = document.createElement("canvas").getContext("2d");
      m1.font = `${estilo.fontWeight} ${estilo.fontSize} ${estilo.fontFamily}`;
      const fm = m1.measureText(":");
      const base0 = Math.round(cv.height * 0.75);
      m.fillText(":", pad, base0);
      const px = m.getImageData(0, 0, cv.width, cv.height).data;
      // Cada punto es una racha de filas con tinta: su centro, su área y dónde cae en x
      const puntos = [];
      let racha = null;
      for (let y = 0; y <= cv.height; y++) {
        let fila = 0, sx = 0;
        if (y < cv.height) for (let x = 0; x < cv.width; x++) { const a = px[(y * cv.width + x) * 4 + 3]; fila += a; sx += a * x; }
        if (fila > 0) {
          racha = racha || { a: 0, sy: 0, sx: 0 };
          racha.a += fila; racha.sy += fila * y; racha.sx += sx;
        } else if (racha) { puntos.push(racha); racha = null; }
      }
      if (puntos.length === 2) {
        const c = puntos.map((q) => [q.sx / q.a, q.sy / q.a, Math.sqrt(q.a / 255 / Math.PI)]);
        const yMedio = (c[0][1] + c[1][1]) / 2 - base0;
        const base = caja.top + (caja.height - (fm.fontBoundingBoxAscent + fm.fontBoundingBoxDescent)) / 2 + fm.fontBoundingBoxAscent;
        datos.baja = base + yMedio / E - (caja.top + caja.height / 2);
        datos.punto = { r: (c[0][2] + c[1][2]) / 2 / E, sep: (c[1][1] - c[0][1]) / 2 / E, dx: (c[0][0] + c[1][0]) / 2 / E - pad / E };
      }
    } catch (e) {}
    if (aviso) {
      const c = aviso.getBoundingClientRect();
      datos.aviso = { izq: c.left, arriba: c.top, ancho: c.width, tam: getComputedStyle(aviso).fontSize, html: aviso.innerHTML };
    }
    return datos;
  }

  function guardarReloj() {
    const datos = medirReloj();
    if (!datos) return;
    try { localStorage.setItem(RELOJ_GUARDADO, JSON.stringify(datos)); } catch (e) {}
  }

  function relojGuardado() {
    try { return JSON.parse(localStorage.getItem(RELOJ_GUARDADO)) || RELOJ_POR_DEFECTO; } catch (e) { return RELOJ_POR_DEFECTO; }
  }

  function horaAhora() {
    const d = new Date();
    const dos = (n) => String(n).padStart(2, "0");
    const dia = DIAS[d.getDay()];
    return {
      trozos: [dos(d.getHours()), ":", dos(d.getMinutes()), ":", dos(d.getSeconds())],
      fecha: `${dia[0].toUpperCase()}${dia.slice(1)}, ${dos(d.getDate())}/${dos(d.getMonth() + 1)}/${d.getFullYear()}`,
    };
  }

  // ── Cara dormida y paso al reloj ────────────────────────────────────────────
  function htmlCara(alto, ancho) {
    const parpados = `<g data-k="sup"><path fill="url(#ktSombra)" d="M -12 -29 Q 50 -7 112 -29 L 112 -15 Q 50 7 -12 -15 Z"/><path fill="url(#ktPiel)" d="M -12 -142 H 112 V -28 Q 50 -6 -12 -28 Z"/><path d="M 2 -46 Q 50 -28 98 -46" fill="none" stroke="#33220f" stroke-width="2.5" stroke-linecap="round"/><path fill="#120b04" d="M -12 -29 Q 50 -7 112 -29 Q 50 2 -12 -29 Z"/></g><g data-k="inf"><path fill="url(#ktInf)" d="M -12 122 Q 50 100 112 122 V 170 H -12 Z"/><path fill="#33220f" d="M -12 122 Q 50 100 112 122 Q 50 105 -12 122 Z"/></g>`;
    const ojo = `<g data-k="ojo"><path d="${OJO}" fill="#fff3da"/><g clip-path="url(#ktOjo)">${parpados}</g></g>`;
    const ceja = (t) => `<g data-k="ceja"><path transform="translate(${t},83.9) scale(${t > 200 ? -1.331 : 1.331},1.331) translate(-105.25,-165.48)" d="${CEJA}" fill="url(#ktCeja)"/></g>`;
    return `<svg style="position:absolute;inset:0" width="${ancho}" height="${alto}" aria-hidden="true">
      <defs>
        <radialGradient id="ktHalo"><stop offset="0" stop-color="#966224" stop-opacity=".34"/><stop offset=".45" stop-color="#966224" stop-opacity=".2"/><stop offset=".75" stop-color="#966224" stop-opacity=".07"/><stop offset="1" stop-color="#966224" stop-opacity="0"/></radialGradient>
        <radialGradient id="ktPiel" cx=".5" cy=".5" r=".62"><stop offset="0" stop-color="#a87c3e"/><stop offset=".55" stop-color="#6e4d25"/><stop offset="1" stop-color="#33220f"/></radialGradient>
        <linearGradient id="ktInf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6e4d25"/><stop offset="1" stop-color="#33220f"/></linearGradient>
        <linearGradient id="ktSombra" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1604" stop-opacity=".55"/><stop offset="1" stop-color="#2a1604" stop-opacity="0"/></linearGradient>
        <linearGradient id="ktCeja" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b98536"/><stop offset="1" stop-color="#7a5220"/></linearGradient>
        <radialGradient id="ktBoca"><stop offset="0" stop-color="#e0a44d"/><stop offset="1" stop-color="#8a5a1e"/></radialGradient>
        <clipPath id="ktOjo"><path d="${OJO}"/></clipPath>
        <clipPath id="ktInunda"><circle data-k="ola" r="0"/><circle data-k="ola" r="0"/></clipPath>
      </defs>
      <rect width="${ancho}" height="${alto}" fill="${FONDO_CARA}"/>
      <g data-k="todo">
        <circle cx="240" cy="230" r="210" fill="url(#ktHalo)"/>
        <g data-k="cara">${ceja(65)}${ceja(415)}${ojo}${ojo}<path data-k="boca" transform="translate(195,334.6) scale(2.07) translate(-221.652,-237.707)" fill="url(#ktBoca)"/></g>
      </g>
      <rect data-k="fondoReloj" width="${ancho}" height="${alto}" clip-path="url(#ktInunda)"/>
      <g data-k="zetas" font-family="Nunito,'Varela Round','DejaVu Sans',sans-serif" font-weight="800" text-anchor="middle"><text font-size="24">z</text><text font-size="32">z</text><text font-size="42">Z</text></g>
      <g data-k="puntos"><circle/><circle/><circle/><circle/></g>
    </svg>`;
  }

  function htmlHora(R, colores, hora) {
    const fecha = R.fecha;
    const aviso = R.aviso;
    const comun = `position:absolute;line-height:1;white-space:pre;opacity:0;will-change:transform`;
    const letra = (f) => f.replace(/"/g, "'"); // van dentro de style="..."
    return hora.trozos.map((t, i) => `<span data-k="trozo" style="${comun};left:${R.trozos[i][0]}px;top:${R.arriba}px;width:${R.trozos[i][1]}px;height:${R.alto}px;font:${R.peso} ${R.tam}px/${R.alto}px ${letra(R.familia)};letter-spacing:${R.espacio};font-variant-numeric:tabular-nums;color:${colores.texto}">${t}</span>`).join("") +
      `<div data-k="fecha" style="${comun};left:${fecha.izq}px;top:${fecha.arriba}px;width:${fecha.ancho}px;text-align:center;font-size:${fecha.tam};letter-spacing:${fecha.espacio};font-family:${letra(fecha.familia)};color:${colores.suave}">${hora.fecha}</div>` +
      (aviso ? `<div data-k="aviso" style="position:absolute;opacity:0;left:${aviso.izq}px;top:${aviso.arriba}px;width:${aviso.ancho}px;text-align:center;font-size:${aviso.tam};font-family:${letra(fecha.familia)};color:${colores.suave}">${aviso.html}</div>` : "");
  }

  // pose: de dónde parte la cara. dormido inclina cejas y cabeza; mini es la boca pequeña.
  function escenaReloj(tipo, R, pose, zetasReales) {
    const ancho = innerWidth, alto = innerHeight;
    const colores = esDeNoche() ? COLORES.noche : COLORES.dia;
    const capa = dentroDe(htmlCara(alto, ancho) + htmlHora(R, colores, horaAhora()));
    const de = (k) => [...capa.querySelectorAll(`[data-k="${k}"]`)];
    const uno = (k) => de(k)[0];
    const todo = uno("todo"), cara = uno("cara"), boca = uno("boca"), fondo = uno("fondoReloj");
    const zetas = uno("zetas"), puntos = uno("puntos"), ojos = de("ojo"), cejas = de("ceja");
    const olas = de("ola"), trozos = de("trozo"), fecha = uno("fecha"), aviso = uno("aviso");
    const NB = BOCA.match(NUM).map(Number), NM = BOCA_MINI.match(NUM).map(Number);
    fondo.setAttribute("fill", colores.fondo);
    todo.setAttribute("transform", `translate(0 ${(alto - 480) / 2})`);
    de("sup").forEach((e) => e.setAttribute("transform", "translate(0 130)"));
    de("inf").forEach((e) => e.setAttribute("transform", "translate(0 -5.1)"));

    const centro = R.trozos.map(([x, w]) => x + w / 2);
    const yDe = R.arriba + R.alto / 2;
    const yPuntos = yDe + (R.baja || 0);
    const punto = R.punto || { r: R.tam * 0.053, sep: R.tam * 0.24, dx: R.trozos[1][1] / 2 };
    const sep = punto.sep, radio = punto.r;
    const xPuntos = [R.trozos[1][0] + punto.dx, R.trozos[3][0] + punto.dx];
    const y0 = (alto - 480) / 2;

    function pintaCara(f, k, op) {
      const d = pose.dormido ? f : 0;
      cara.setAttribute("transform", `translate(${pose.x * f} ${pose.y * f}) rotate(${pose.r * f} 240 240)`);
      ojos.forEach((e, i) => {
        const s = 1.507 * k;
        e.setAttribute("display", k > 0.001 ? "inline" : "none");
        e.setAttribute("transform", `translate(${OJOS_X[i]} 229) rotate(${i ? -12 : 12}) scale(${i ? -s : s} ${s}) translate(-49.76 -53.88)`);
      });
      cejas.forEach((e, i) => {
        const [cx, cy] = CEJAS_CENTRO[i];
        e.setAttribute("opacity", op);
        e.setAttribute("transform", `translate(0 ${4.2 * d}) rotate(${(i ? 3 : -3) * d} ${cx} ${cy}) translate(${cx} ${cy}) scale(1 ${1 - 0.25 * d}) translate(${-cx} ${-cy})`);
      });
      boca.setAttribute("opacity", op);
      const mini = pose.mini ? 1 : 0;
      let j = 0;
      boca.setAttribute("d", BOCA.replace(NUM, () => { const v = mezcla(NB[j], NM[j], mini); j++; return v.toFixed(2); }));
    }

    const pasoZ = (i, seg) => {
      const z = zetasReales[i];
      const fase = (z.fase + seg / 2.4) % 1;
      const e = 1 - Math.pow(1 - fase, 2);
      return {
        x: z.x + 34 * e, y: z.y - 64 * e, s: mezcla(0.4, 1.1, e), r: mezcla(-10, 12, e),
        o: fase < 0.25 ? fase / 0.25 : 1 - (fase - 0.25) / 0.75,
      };
    };

    function ponTrozo(i, transformacion, op) {
      trozos[i].style.transform = transformacion;
      trozos[i].style.opacity = op;
    }
    function ponPie(f) {
      fecha.style.opacity = f;
      fecha.style.transform = `translateY(${10 * (1 - f)}px)`;
      if (aviso) aviso.style.opacity = f;
    }

    function dosPuntos(p, seg, vuelta) {
      pintaCara(1 - suave(tramo(p, 0.02, 0.3)), 1 - suave(tramo(p, 0.05, 0.42)), 1 - tramo(p, 0.04, 0.22));
      zetas.setAttribute("opacity", vuelta ? 0 : 1 - tramo(p, 0.01, 0.12));
      [...zetas.children].forEach((t, i) => {
        const z = pasoZ(i, seg);
        t.setAttribute("fill", "#fff3da");
        t.setAttribute("opacity", z.o);
        t.setAttribute("transform", `translate(${z.x} ${z.y}) rotate(${z.r}) scale(${z.s})`);
      });
      const t = suave(tramo(p, 0.2, 0.6)), s = sep * rebota(tramo(p, 0.38, 0.62));
      const r = p < 0.26 ? 0 : p < 0.4 ? 13 * tramo(p, 0.26, 0.4) : mezcla(13, radio, suave(tramo(p, 0.45, 0.72)));
      const color = mezclaColor("#c89b57", colores.texto, tramo(p, 0.42, 0.58));
      const ola = suave(tramo(p, 0.38, 0.8)) * 1.3 * Math.max(ancho, alto);
      [0, 1].forEach((i) => {
        const x = mezcla(OJOS_X[i], xPuntos[i], t), y = mezcla(232 + y0, yPuntos, t);
        olas[i].setAttribute("cx", x);
        olas[i].setAttribute("cy", y);
        olas[i].setAttribute("r", ola);
        [0, 1].forEach((j) => {
          const c = puntos.children[i * 2 + j];
          c.setAttribute("cx", x);
          c.setAttribute("cy", y + (j ? s : -s));
          c.setAttribute("r", r);
          c.setAttribute("fill", color);
        });
      });
      puntos.setAttribute("opacity", 1 - tramo(p, 0.92, 1));
      ponTrozo(1, "", tramo(p, 0.9, 1));
      ponTrozo(3, "", tramo(p, 0.9, 1));
      const sale = (i, desde, a, b) => {
        const c = rebota(tramo(p, a, b));
        ponTrozo(i, `translateX(${(desde - centro[i]) * (1 - c)}px) scale(${mezcla(0.2, 1, c)})`, tramo(p, a, a + 0.1));
      };
      sale(0, centro[1], 0.56, 0.84);
      sale(2, centro[2], 0.6, 0.88);
      sale(4, centro[3], 0.56, 0.84);
      ponPie(tramo(p, 0.8, 1));
    }

    function zZz(p, seg, vuelta) {
      pintaCara(1, 1, 1);
      todo.setAttribute("opacity", 1 - tramo(p, 0.12, 0.42));
      const ola = suave(tramo(p, 0.24, 0.62)) * 1.1 * Math.max(ancho, alto);
      olas[0].setAttribute("cx", ancho / 2);
      olas[0].setAttribute("cy", yDe);
      olas[0].setAttribute("r", ola);
      puntos.setAttribute("display", "none");
      const e = suave(tramo(p, 0.04, 0.55)), fuera = 1 - tramo(p, 0.5, 0.6);
      // Al volver no le quedan zZz: se despierta en cuanto cargue la cara
      const entran = vuelta ? tramo(p, 0.03, 0.15) : 1;
      [...zetas.children].forEach((t, i) => {
        const z = pasoZ(i, seg), destino = [centro[0], centro[2], centro[4]][i];
        t.setAttribute("fill", mezclaColor("#fff3da", colores.texto, tramo(p, 0.3, 0.5)));
        t.setAttribute("opacity", mezcla(z.o, 1, tramo(p, 0, 0.08)) * fuera * entran);
        t.setAttribute("transform", `translate(${mezcla(z.x, destino, e)} ${mezcla(z.y, yDe + 15, e)}) rotate(${mezcla(z.r, 0, e)}) scale(${mezcla(z.s, 1.5, e)})`);
      });
      [0, 2, 4].forEach((i, n) => {
        const a = 0.5 + n * 0.03;
        ponTrozo(i, `scale(${mezcla(0.55, 1, rebota(tramo(p, a, a + 0.2)))})`, tramo(p, a, a + 0.08));
      });
      ponTrozo(1, "", tramo(p, 0.68, 0.78));
      ponTrozo(3, "", tramo(p, 0.68, 0.78));
      ponPie(tramo(p, 0.8, 1));
    }

    return (p, seg, vuelta) => (tipo === "zetas" ? zZz(p, seg, vuelta) : dosPuntos(p, seg, vuelta));
  }

  function zetasDe(cuando) {
    const defecto = [[372, 128], [382, 108], [364, 122]];
    const y0 = (innerHeight - 480) / 2;
    return [...document.querySelectorAll(".fx-zzz")].concat([null, null, null]).slice(0, 3).map((el, i) => {
      const anim = el && el.getAnimations()[0];
      const prog = anim && anim.effect.getComputedTiming().progress;
      if (prog == null) return { x: defecto[i][0], y: defecto[i][1] + y0, fase: (cuando + i * 0.33) % 1 };
      const e = 1 - Math.pow(1 - prog, 2), c = el.getBoundingClientRect();
      return { x: c.left + c.width / 2 - 34 * e, y: c.top + c.height * 0.8 + 64 * e, fase: prog };
    });
  }

  // Cara -> reloj. La cara llega con los ojos cerrados: se duerme antes, o la cierra
  // quien llama si ha sido un doble toque con él despierto.
  function aReloj({ pose, tipo, velocidad = 1 } = {}) {
    if (enCurso) return Promise.resolve();
    enCurso = true;
    const pinta = escenaReloj(tipo || azar(TIPOS_RELOJ), relojGuardado(), pose, zetasDe(0));
    return correr(2200 / velocidad, (t) => pinta(t, t * 2.2, false));
  }

  // Reloj -> cara: acaba en la misma imagen con la que arranca la cara al despertarse
  function aCara({ tipo, velocidad = 1 } = {}) {
    if (enCurso) return Promise.resolve();
    const medido = medirReloj();
    if (!medido) return Promise.resolve();
    enCurso = true;
    const pose = { x: 0, y: 6, r: 0, dormido: false, mini: true };
    const pinta = escenaReloj(tipo || azar(TIPOS_RELOJ), medido, pose, zetasDe(0));
    return correr(2200 / velocidad, (t) => pinta(1 - t, t * 2.2, true));
  }

  // Al llegar a la página nueva, su primera imagen es la última de la transición (la misma
  // capa, que va debajo de lo real), y se funde: así no hay un corte entre la réplica y la
  // pantalla de verdad, solo un cambio suave aunque no coincidan al píxel.
  function cubrirCara() {
    enCurso = true;
    const pose = { x: 0, y: 6, r: 0, dormido: false, mini: true };
    escenaReloj("puntos", relojGuardado(), pose, zetasDe(0))(0, 0, true);
    document.getElementById("kaitoTransicion").style.pointerEvents = "none";
  }
  function cubrirReloj() {
    enCurso = true;
    escenaReloj("puntos", relojGuardado(), { x: 0, y: 0, r: 0, dormido: false, mini: false }, zetasDe(0))(1, 0, false);
    document.getElementById("kaitoTransicion").style.pointerEvents = "none";
  }
  // Cuando lo de debajo ya se ha pintado (dos cuadros), la capa se funde y se quita
  function quitar(ms = 180) {
    const capa = document.getElementById("kaitoTransicion");
    if (!capa) return;
    capa.removeAttribute("id");
    requestAnimationFrame(() => requestAnimationFrame(() => {
      capa.animate({ opacity: [1, 0] }, { duration: ms, fill: "forwards" }).onfinish = () => { capa.remove(); enCurso = false; };
    }));
  }

  // ── Lo que tapa la pantalla al cambiar de cara ──────────────────────────────
  const TRAZO = "M -300 130 C -50 180 300 270 760 340";
  const KANJI = `font-family="'Noto Serif CJK JP','Noto Sans CJK JP','WenQuanYi Zen Hei',serif" font-weight="700" text-anchor="middle"`;

  function pincel(capa, p) {
    const trazos = capa.querySelectorAll("[data-trazo]");
    const pos = (a, b) => 1 - suave(tramo(p, a, 0.4 + a)) - suave(tramo(p, 0.54 + b, 0.92 + b));
    trazos.forEach((t) => {
      const a = +t.dataset.trazo;
      t.setAttribute("stroke-dashoffset", a < 0 ? pos(0.07, 0) : pos(a, 0.03 + a));
    });
    const kanji = capa.querySelector("[data-kanji]");
    const k = tramo(p, 0.3, 0.4) * (1 - tramo(p, 0.56, 0.66));
    kanji.setAttribute("opacity", k);
    kanji.setAttribute("transform", `translate(240 240) scale(${mezcla(1.4, 1, rebota(tramo(p, 0.3, 0.44)))}) translate(-240 -240)`);
  }

  function htmlPincel() {
    const huecos = [0.03, 0, 0.05, 0.015, 0.04, 0.01, 0.035, 0.005, 0.045, 0.02, 0, 0.05, 0.025, 0.04, 0.01];
    const tonos = ["#c4934c", "#bf8d46", "#ca9a54"];
    const cerdas = huecos.map((a, i) => {
      const n = i * 50 - 350;
      return `<path data-trazo="${a}" transform="translate(${-0.33 * n} ${0.94 * n})" d="${TRAZO}" pathLength="1" stroke="${tonos[i % 3]}" stroke-width="${i % 3 ? 44 : 30}" stroke-dasharray="1 2"/>`;
    }).join("");
    return `<g fill="none" stroke-linecap="round"><path data-trazo="-1" d="${TRAZO}" pathLength="1" stroke="#c4934c" stroke-width="600" stroke-linecap="butt" stroke-dasharray="1 2"/>${cerdas}</g>
      <g data-kanji opacity="0"><text x="240" y="222" font-size="124" fill="${FONDO_CARA}" ${KANJI}>先</text><text x="240" y="346" font-size="124" fill="${FONDO_CARA}" ${KANJI}>生</text></g>`;
  }

  function shoji(capa, p) {
    const x = 240 * (1 - suave(tramo(p, 0, 0.36)) + suave(tramo(p, 0.62, 1))) + 4 * Math.sin(Math.PI * tramo(p, 0.36, 0.46));
    capa.querySelector("[data-puerta='i']").setAttribute("transform", `translate(${-x} 0)`);
    capa.querySelector("[data-puerta='d']").setAttribute("transform", `translate(${x} 0)`);
    // Cerradas del todo no debe asomar la cara por la rendija del rebote
    capa.querySelector("[data-rendija]").setAttribute("opacity", x < 10 ? 1 : 0);
  }

  function htmlShoji() {
    const puerta = (lado, x0, letra, tx) => {
      let lineas = "";
      for (let x = 60; x < 240; x += 60) lineas += `<line x1="${x0 + x}" y1="-400" x2="${x0 + x}" y2="880" stroke="#7a5220" stroke-width="3"/>`;
      for (let y = -320; y < 880; y += 80) lineas += `<line x1="${x0}" y1="${y}" x2="${x0 + 240}" y2="${y}" stroke="#7a5220" stroke-width="3"/>`;
      return `<g data-puerta="${lado}"><rect x="${x0}" y="-400" width="240" height="1280" fill="#f2e4c8"/>${lineas}<rect x="${x0 + 3}" y="-410" width="234" height="1300" fill="none" stroke="#4a3012" stroke-width="7"/><text x="${tx}" y="274" font-size="96" fill="#4a3012" ${KANJI}>${letra}</text></g>`;
    };
    return `<rect data-rendija x="200" y="-400" width="80" height="1280" fill="${FONDO_CARA}" opacity="0"/>${puerta("i", 0, "先", 176)}${puerta("d", 240, "生", 304)}`;
  }

  // Pétalos y humo: muchas piezas, así que no se pintan a mano cada cuadro (la Pi no
  // podía). Cada una es un elemento con su animación de transform/opacity, que va por la
  // GPU sin pasar por JS. trans(i, p) da cómo está la pieza i en el instante p (0..1) y
  // se muestrea en unos cuantos fotogramas clave.
  const frac = (i, k) => (i * k) % 1;
  const base = (w, h) => `position:absolute;left:0;top:0;width:${w}px;height:${h}px;margin:${-h / 2}px 0 0 ${-w / 2}px;will-change:transform`;

  // Pétalos y flores en una ráfaga de viento: 140 piezas, mitad flores de cinco pétalos
  // con contorno y mitad pétalos sueltos. Cruzan la pantalla de izquierda a derecha a la
  // misma velocidad y salen una tras otra, así que sin pararse nunca forman un manto que
  // tapa la pantalla (sin fondo) justo a mitad, cuando cambia la cara.
  const HOJA = "M 0 -10 C 8 -9 9 4 1 11 L 0 7 L -1 11 C -9 4 -8 -9 0 -10 Z";
  const PETALO_FLOR = "M 0 0 C -24 -10 -27 -38 -10 -46 C -5 -48 -2 -45 0 -41 C 2 -45 5 -48 10 -46 C 27 -38 24 -10 0 0 Z";
  const ROSAS = ["#ff8f8f", "#ffb3c1", "#f7798f"];
  const NPIEZAS = 140;
  const PIEZAS = Array.from({ length: NPIEZAS }, (_, n) => {
    const flor = n % 2 === 0;
    return {
      n, flor, sal: (n / NPIEZAS) * 0.5, y: frac(n, 0.618034) * 540 - 30, caida: 40 + frac(n, 0.43) * 40,
      esc: flor ? 0.95 + frac(n, 0.757) * 0.15 : 4.2 + frac(n, 0.757) * 0.8,
      fase: frac(n, 0.53) * 6.28, giro: (flor ? 200 : 520) * (frac(n, 0.29) - 0.2),
    };
  });

  function htmlPetalos() {
    const tinta = "#2b1420";
    const ang = [0, 40, 80, 120, 160, 200, 240, 280, 320].map((a, k) => [Math.cos((a * Math.PI) / 180) * (14 + (k % 3) * 4), Math.sin((a * Math.PI) / 180) * (14 + (k % 3) * 4)]);
    const rayas = ang.map(([x, y]) => `M 0 0 L ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    const puntos = ang.map(([x, y]) => `M ${x.toFixed(1)} ${y.toFixed(1)} h 0`).join(" ");
    const flores = ROSAS.map((c) => `<g fill="${c}" stroke="${tinta}" stroke-width="3" stroke-linejoin="round">${[0, 72, 144, 216, 288].map((a) => `<path transform="rotate(${a})" d="${PETALO_FLOR}"/>`).join("")}</g><path d="${rayas}" fill="none" stroke="${tinta}" stroke-width="1.6" stroke-linecap="round"/><path d="${puntos}" fill="none" stroke="${tinta}" stroke-width="4.4" stroke-linecap="round"/>`);
    return PIEZAS.map((q) => {
      const w = q.flor ? 100 * q.esc : 24 * q.esc;
      const dibujo = q.flor ? flores[q.n % 3] : `<path d="${HOJA}" fill="${["#f7b6c8", "#fbd0dc", "#f29bb3"][q.n % 3]}"/>`;
      const vb = q.flor ? "-50 -50 100 100" : "-12 -12 24 24";
      return `<div data-p style="${base(w, w)}"><svg viewBox="${vb}" width="${w}" height="${w}">${dibujo}</svg></div>`;
    }).join("");
  }

  function transPetalos(i, p) {
    const q = PIEZAS[i], f = tramo(p, q.sal, q.sal + 0.5);
    const x = mezcla(-70, 560, f), y = q.y + 22 * Math.sin(f * 11 + q.fase) + q.caida * (f - 0.5);
    const ay = q.flor ? 1 : 0.75 + 0.25 * Math.cos(f * 16 + q.fase);
    return { transform: `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) rotate(${(q.giro * f).toFixed(0)}deg) scale(1,${ay.toFixed(2)})` };
  }

  // Humo de dibujo: nubes blancas de bordes abollados con sombra azulada abajo a la
  // derecha y unas burbujitas sueltas. Cada bola va dos veces: primero todas las sombras
  // (corridas) y encima todos los cuerpos, así solo asoma una media luna de sombra.
  const NUBES = [[240, 240, 200], [110, 130, 150], [370, 120, 150], [100, 360, 150], [380, 370, 160], [240, 90, 130], [240, 400, 130], [60, 240, 130], [420, 240, 130], [170, 250, 150], [320, 240, 150],
    [175, 170, 90], [310, 175, 90], [190, 330, 95], [300, 320, 95], [60, 90, 60], [420, 60, 60], [60, 430, 60], [425, 430, 60]];
  const BURBUJAS = [[85, 95, 14], [405, 70, 10], [55, 335, 12], [435, 405, 16], [350, 205, 9], [150, 425, 11], [300, 55, 8]];
  const BOLAS = NUBES.concat(BURBUJAS);
  function htmlHumo() {
    const bolas = (color) => BOLAS.map(([, , r]) => `<div data-p style="${base(2 * r, 2 * r)};border-radius:50%;background:${color}"></div>`).join("");
    return `<div data-p style="position:absolute;left:-60px;top:-60px;width:600px;height:600px;background:#f2fafd;opacity:0"></div>${bolas("#b8dbe7")}${bolas("#f2fafd")}`;
  }

  function transHumo(i, p) {
    if (i === 0) return { opacity: tramo(p, 0.4, 0.48) * (1 - tramo(p, 0.54, 0.6)) };
    const k = (i - 1) % BOLAS.length, sombra = i - 1 < BOLAS.length;
    const [x, y, r] = BOLAS[k], burbuja = k >= NUBES.length;
    const crece = (burbuja ? rebota : suave)(tramo(p, burbuja ? 0.2 : 0.03 + (k % 5) * 0.04, 0.5));
    const mengua = suave(tramo(p, 0.55 + (k % 5) * 0.045, 0.82 + (k % 5) * 0.045));
    const sube = suave(tramo(p, 0.55, 1)), f = acota(crece, 0, 1.05);
    const cx = mezcla(240, x, f) + (x - 240) * 0.1 * sube + (sombra ? 7 : 0);
    const cy = mezcla(240, y, f) - 50 * sube + (sombra ? 10 : 0);
    return { transform: `translate(${cx.toFixed(1)}px,${cy.toFixed(1)}px) scale(${Math.max(0, crece * (1 - mengua)).toFixed(3)})` };
  }

  const TAPAS = {
    pincel: { ms: 2300, html: htmlPincel, pinta: pincel },
    shoji: { ms: 2100, html: htmlShoji, pinta: shoji },
    petalos: { ms: 2000, html: htmlPetalos, trans: transPetalos },
    humo: { ms: 1900, html: htmlHumo, trans: transHumo },
  };

  // Cubre la pantalla y, a mitad, con todo tapado, hace el cambio que le pasan
  function tapar(tipo, alCubrir) {
    const tapa = TAPAS[tipo];
    let hecho = false;
    const cambia = () => {
      if (hecho) return;
      hecho = true;
      alCubrir();
    };
    // --cara-ancho: la ventana del robot mide 500 px, pero su pantalla solo enseña 480
    const marco = "position:absolute;left:0;top:0;width:var(--cara-ancho,100%);height:100%";
    const capa = dentroDe(tapa.trans
      ? `<div style="${marco};overflow:hidden"><div data-lienzo style="position:absolute;left:0;top:0;width:480px;height:480px;transform-origin:0 0">${tapa.html()}</div></div>`
      : `<svg style="${marco}" viewBox="0 0 480 480" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${tapa.html()}</svg>`);
    if (tapa.trans) {
      // Lo mismo que hace el svg con "slice": el lienzo de 480 cubre la pantalla, centrado
      const m = capa.firstChild, k = Math.max(m.clientWidth, m.clientHeight) / 480;
      capa.querySelector("[data-lienzo]").style.transform = `translate(${(m.clientWidth - 480 * k) / 2}px,${(m.clientHeight - 480 * k) / 2}px) scale(${k})`;
      capa.querySelectorAll("[data-p]").forEach((e, i) => {
        e.animate(Array.from({ length: 25 }, (_, n) => tapa.trans(i, n / 24)), { duration: tapa.ms, fill: "both" });
      });
    }
    capa.style.pointerEvents = "none";
    return correr(tapa.ms, (p) => {
      if (tapa.pinta) tapa.pinta(capa, p);
      if (p >= 0.5) cambia();
    }).then(() => {
      cambia();
      capa.remove();
    });
  }

  // Quita o deja las que no gusten: se elige una al azar cada vez
  const TIPOS_RELOJ = ["puntos", "zetas"];

  // La primera vez que se usan estas letras la Pi se para medio segundo a cargarlas:
  // mejor al abrir la cara, donde no se nota, que a mitad de una transición.
  addEventListener("load", () => {
    if (!document.getElementById("face")) return;
    const previa = document.createElement("div");
    previa.setAttribute("aria-hidden", "true");
    previa.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0;pointer-events:none";
    previa.innerHTML = `<span style="font:700 96px 'Noto Serif CJK JP','Noto Sans CJK JP','WenQuanYi Zen Hei',serif">先生</span><span style="font:200 64px 'M PLUS Rounded 1c','Nunito',sans-serif;font-variant-numeric:tabular-nums">0123456789:</span>`;
    document.body.appendChild(previa);
    setTimeout(() => previa.remove(), 4000);
  });

  window.KaitoTransicion = { aReloj, aCara, tapar, cubrirCara, cubrirReloj, quitar, guardarReloj, esDeNoche };
})();
