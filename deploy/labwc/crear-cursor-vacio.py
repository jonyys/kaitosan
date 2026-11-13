#!/usr/bin/env python3
"""Crea un tema de cursor transparente (1x1) en la carpeta dada: el robot es táctil y no
debe verse un puntero de ratón al arrancar. Uso: crear-cursor-vacio.py ~/.icons/vacio"""
import os
import struct
import sys

destino = os.path.expanduser(sys.argv[1])
os.makedirs(os.path.join(destino, "cursors"), exist_ok=True)
# Xcursor: cabecera + 1 entrada en la tabla + 1 imagen de 1x1 píxel totalmente transparente
imagen = struct.pack("<9I", 36, 0xFFFD0002, 1, 1, 1, 1, 0, 0, 0) + struct.pack("<I", 0)
datos = b"Xcur" + struct.pack("<3I", 16, 0x10000, 1) + struct.pack("<3I", 0xFFFD0002, 1, 28) + imagen
base = os.path.join(destino, "cursors", "left_ptr")
open(base, "wb").write(datos)
for n in ("default", "arrow", "pointer", "hand1", "hand2", "text", "xterm", "watch", "wait", "crosshair",
          "grab", "grabbing", "fleur", "move", "progress", "help", "not-allowed", "no-drop", "copy",
          "alias", "context-menu", "cell", "vertical-text", "all-scroll", "col-resize", "row-resize",
          "n-resize", "s-resize", "e-resize", "w-resize", "ne-resize", "nw-resize", "se-resize",
          "sw-resize", "ew-resize", "ns-resize", "nesw-resize", "nwse-resize", "zoom-in", "zoom-out",
          "left_ptr_watch", "top_left_arrow", "X_cursor"):
    ruta = os.path.join(destino, "cursors", n)
    if not os.path.lexists(ruta):
        os.symlink("left_ptr", ruta)
open(os.path.join(destino, "index.theme"), "w").write("[Icon Theme]\nName=vacio\nComment=Cursor invisible\n")
print("cursor vacío en", destino)
