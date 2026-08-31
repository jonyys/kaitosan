# なおす — Reparación del Modo Sensei

> Kaitosan · plan de trabajo · 13 fases

Trece fases, cada una un arreglo cerrado que se puede commitear solo. El orden no es por gravedad sino por dependencia: cada fase deja el terreno preparado para la siguiente, y ninguna necesita que la posterior esté hecha para funcionar.

---

## Fuera de alcance, por decisión tuya

**Disparadores de modo amplios** (`brain.py:65, 75, 84`) — se quedan como están. Ninguna fase toca la detección de modo por subcadena.

**Aprobado de oficio cuando el extractor falla** (`profesor.py:444-457`) — se mantiene el comportamiento. Ojo, porque tiene consecuencia directa sobre la Fase 1: ese bloque y el de las líneas 503-510 hacen `get_item_id()` sobre ítems que hoy están en la BD porque los metió `_montar_estado()`. Al quitar esa inserción temprana devolverían `None` y el aprobado dejaría de aplicarse **en silencio**. La Fase 1 incluye el `add_item()` que hace falta para que siga funcionando igual que ahora.

> **Efecto secundario que te interesa:** hoy el aprobado de oficio califica hasta 12 ítems fantasma; después de la Fase 1 calificará solo los 2 reales de la sesión. El comportamiento es el mismo, el daño colateral desaparece.

---

# Bloque I — Integridad de los datos

Nada de lo pedagógico tiene sentido mientras el modelo de progreso de Laura sea ficción. Este bloque es corto y de riesgo bajo.

## 01 · Los ítems nuevos se seleccionan una vez y se guardan al cerrar

**~40 líneas** · `ai/sensei/profesor.py` · `entrar()` · `_montar_estado()` · `_ejecutar_extraccion()`
*Sin dependencias · bloquea a 04, 12 y 13*

Tres movimientos. **Uno**, la selección pasa a `entrar()`, una sola vez por sesión, no una vez por turno. **Dos**, `_montar_estado()` pasa a ser de solo lectura: lee `self._foco_nuevos` y no escribe nada. **Tres**, la persistencia baja al cierre.

```python
# entrar() — una sola selección por sesión
due = self.jap_memory.resumen_perfil()["due_count"]
self._foco_nuevos = ([] if due >= THROTTLE_DUE
                     else siguiente_items_nuevos(self.jap_memory,
                                                 MAX_ITEMS_NUEVOS))

# _montar_estado() — solo lee
nuevos = self._foco_nuevos          # ← fuera el bucle de add_item()

# _ejecutar_extraccion() — persistir aquí, y ANTES de review()
for nuevo in self._foco_nuevos:
    self.jap_memory.add_item(nuevo["kind"], nuevo["jp"],
                             reading=nuevo.get("reading"),
                             meaning=nuevo.get("meaning"),
                             tipo=nuevo.get("tipo"),
                             session_id=session_id)   # ← el que salva
                                                      #   el aprobado de oficio
```

Ese último `add_item()` va tanto en la rama de rescate como antes del bloque de las líneas 503-510. Sin él, las dos rutas de calificación quedan mudas.

> **Cuidado:** `_foco_nuevos` se resetea en `entrar()` pero `_ejecutar_extraccion()` puede correr en segundo plano (Fase 2). Cópialo a una variable local al principio de la extracción, igual que ya se hace con `session_id`, o una sesión nueva puede pisárselo a la anterior.

**Verificación:** diez turnos contra una BD limpia deben dejar `vocab = 2` y `due_count = 2`, no 12. Tengo la sonda escrita del análisis anterior; se ejecuta en un segundo y no gasta API.

## 02 · La despedida no espera al extractor

**~3 líneas** · `ai/sensei/profesor.py:184-195` · `salir()`
*Independiente · conviene hacerla junto a la 01, tocan la misma función*

Cambiar la llamada síncrona por la misma tarea de fondo que ya usa el temporizador de inactividad en `_renovar_timer()`. Es copiar un patrón que ya existe tres líneas más arriba en el mismo fichero.

```diff
 def salir(self):
     if self.timer:
         self.timer.cancel(); self.timer = None
     self.activo = False
-    self.cerrar_sesion_y_extraer()
+    self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
```

**Verificación:** decir «sal del modo sensei» y cronometrar: la despedida debe volver al instante en vez de tardar entre 5 y 15 segundos. El resumen aparece en la BD unos segundos después.

## 03 · Una respuesta, un mensaje en el chat

**2 líneas** · `app.py:136-141`
*Independiente*

Borrar el `socketio.emit("mensaje", …)` de la línea 137 y el `#state.cambiar("speaking")` comentado de la 136. La ruta `/chat` ya lo hace bien; solo sobra en `/grabar`.

**Verificación:** hablar por micrófono y comprobar que la respuesta aparece una sola vez en la cara.

## 04 · La gramática cuenta en el perfil de Laura

**~25 líneas** · `core/japanese_memory.py:260-284` · `resumen_perfil()` · `ai/sensei/profesor.py:302-327`
*Después de 01 — antes, `due_count` es basura y sumar gramática solo suma más basura*

Dos consultas nuevas sobre `japanese_grammar`, con la salvedad de que la columna de conteo se llama `times_seen`, no `times_reviewed`. Después, volcar los puntos débiles gramaticales en `RECUERDAS_DE_LAURA` junto a los de vocabulario.

```sql
-- due_count deja de ser solo vocabulario
-- due_vocab + due_gram → due_count

-- puntos débiles de gramática, misma lógica
SELECT grammar_point, errors FROM japanese_grammar
 WHERE times_seen >= 3
   AND CAST(errors AS REAL) / times_seen > 0.4
 ORDER BY 2 DESC LIMIT 5
```

Esto cambia el comportamiento de `THROTTLE_DUE`: al contar más ítems, el freno de ítems nuevos salta antes. Es lo correcto, pero revisa si 12 sigue siendo el número adecuado ahora que cuenta las dos tablas.

**Verificación:** meter a mano un punto de gramática con errores en la BD y comprobar que aparece en el bloque de puntos débiles del prompt.

---

# Bloque II — La voz y el turno

Preparar el canal antes de pedirle a Kaito que hable más japonés. Si el Bloque IV llega antes que esto, los fallos de voz se multiplican en vez de notarse menos.

## 05 · Un bloque 【】 es un solo segmento de voz

**~10 líneas** · `ai/text_to_speech.py:36-40, 60-63, 95`
*Independiente · bloquea a 09*

Las tres expresiones regulares del TTS exigen que todo el contenido entre 【】 sea kana o kanji. Se sustituyen por la permisiva que ya usa `profesor.py:59`: al menos un carácter japonés, y lo que haya alrededor viaja con él.

```python
JP = r'[぀-ゟ゠-ヿ一-鿿]'

r'(【' + JP + r'+】)'                    # ← hoy
r'(【[^【】]*' + JP + r'[^【】]*】)'      # ← permisiva
```

| Caso | Hoy | Después |
|---|---|---|
| 【ねこ】 | ✓ | ✓ |
| 【〜ます】 | ✗ | ✓ (el 〜 ya no se descarta) |
| 【みずをください。】 | ✗ | ✓ |
| 【こんにちは、ラウラさん】 | 2 trozos | 1 |

El punto clave es 〜: más de la mitad de los puntos de gramática del temario lo llevan, y hoy se pierde en cada uno.

**Verificación:** un test sobre `_dividir_texto()` con los cuatro casos de arriba: cada uno debe dar exactamente un segmento con la voz japonesa.

## 06 · La producción explícita gana a la pista de comprensión

**~8 líneas** · `ai/sensei/profesor.py:93-124` · `_extraer_frase_objetivo()`
*Independiente · bloquea a 12*

Invertir el orden de las dos comprobaciones: hoy la de comprensión se evalúa primero y veta a la de producción, así que «Repite conmigo, ¿vale?» pierde la frase objetivo. Además, sacar `"¿vale?"` y `"¿de acuerdo?"` de `_PISTAS_COMPRENSION`: son muletillas de cierre, no preguntas.

```python
# hoy
if any(p in bajo for p in _PISTAS_COMPRENSION): return None
if not any(p in bajo for p in _PISTAS_PRODUCCION): return None

# después
produce   = any(p in bajo for p in _PISTAS_PRODUCCION)
comprende = any(p in bajo for p in _PISTAS_COMPRENSION)
if not produce: return None            # sin petición, no hay objetivo
if comprende and not produce: return None
```

**Verificación:** los cuatro casos del análisis: los dos que ya funcionaban siguen igual, y «Repite conmigo, ¿vale?: 【ねこ】» pasa de `None` a ねこ.

## 07 · Presupuesto de tokens por tipo de turno

**~15 líneas** · `core/config.py:10` · `ai/sensei/profesor.py:270-285`
*Independiente · bloquea a 08, 09 y 10 — sin espacio no hay explicación posible*

Subir `MAX_TOKENS_SENSEI` de 1024 a 2048 y añadir un segundo techo más alto para los turnos de explicación. Con `reasoning_effort="low"` el coste extra es marginal, y la rama de «respuesta vacía» de la línea 283 debería dejar de dispararse.

```python
MAX_TOKENS_SENSEI      = 2048   # turno normal
MAX_TOKENS_EXPLICACION = 3072   # desglose gramatical
```

De momento basta con el techo alto por defecto; la selección por tipo de turno se puede afinar en la Fase 12, cuando el prompt ya distinga registros.

**Verificación:** una sesión de 10 turnos sin que aparezca ni una vez «Respuesta vacía del LLM en modo sensei» en consola.

---

# Bloque III — Material didáctico

El bloque que más mueve la aguja sobre «que enseñe idioma y no vocabulario». Es trabajo de contenido, no de arquitectura: se toca `curriculum.py` y poco más.

## 08 · Cada ítem lleva ejemplo, literal y uso

**330 ítems** · `ai/sensei/curriculum.py` · `ai/sensei/profesor.py:352-378`
*Después de 07 · bloquea a 09*

Hoy el prompt recibe `【食べる】 comer` y nada más, así que todo lo que Kaito enseña por encima de la glosa se lo inventa. Tres campos por ítem lo cambian:

```python
{"kind": "gramatica", "jp": "〜ている",
 "meaning": "acción en progreso o estado resultante",
 "ejemplo": "いま ごはんを たべています",
 "literal": "ahora / comida-OBJ / estar-comiendo",
 "uso": "para lo que pasa ahora mismo, y también para "
        "estados: 「けっこんしています」 es 'estoy casado', "
        "no 'me estoy casando'"}
```

`uso` es el campo importante: es donde vive la diferencia entre saber la traducción y saber cuándo se dice. Luego, en `_montar_estado()`, el FOCO pasa a incluir los tres campos en vez de solo la glosa.

No hace falta rellenar los 330 de golpe. Con las unidades 0 a 5 —lo que Laura va a tocar en meses— ya se nota, y el resto se completa según avance.

**Verificación:** imprimir el FOCO generado y comprobar que un ítem de gramática llega al prompt con frase de ejemplo. Después, una sesión real: la explicación debería dejar de ser genérica.

## 09 · Funciones comunicativas y frases del día a día

**34 unidades** · `ai/sensei/curriculum.py` · `ai/prompts/profesor_japones.txt`
*Después de 05, 07 y 08*

Dos campos por unidad. `funcion` dice qué sabrá hacer Laura al terminarla, y le da a Kaito un objetivo del que hablar en vez de una lista que recitar. `frases_hechas` mete lo que no se deduce de la gramática y es justo lo que hace que alguien suene natural.

```python
{"id": "comida_bebida",
 "nombre": "Comida y bebida",
 "funcion": "pedir en un restaurante, decir qué te gusta "
            "y qué no, y preguntar el precio",
 "frases_hechas": [
   {"jp": "いただきます",   "uso": "antes de comer, siempre"},
   {"jp": "おいしそう",     "uso": "al ver la comida, antes de probarla"},
   {"jp": "これ、ください", "uso": "señalando la carta"},
   {"jp": "ちょっと…",      "uso": "para decir que no sin decir no"}],
 "items": [...]}
```

Un puñado de expresiones como 【おつかれさま】, 【なるほど】, 【よろしくお願いします】 o 【ちょっと…】 enseñan más sobre cómo se habla japonés de verdad que veinte sustantivos. Ahora mismo no están en ninguna parte del repo.

**Verificación:** Kaito debería poder responder a «¿qué estoy aprendiendo ahora?» con la función de la unidad, no con una lista de palabras.

## 10 · El selector de temario deja de abrir una conexión por ítem

**~20 líneas** · `ai/sensei/curriculum.py:691-733`
*Después de 08 y 09 — se hace al final para no reescribirlo mientras cambia la estructura del temario*

Cargar una vez los conjuntos de `word` y `grammar_point` que ya están en la BD, pasarlos por parámetro y resolver `_already_taught` y `_fraccion_aprendida` en memoria. Hoy el recorrido completo son unas 360 conexiones SQLite por turno, en una Raspberry Pi y con Laura esperando; ahora no se nota porque el bucle corta pronto, pero se notará en cuanto avance de unidad.

**Verificación:** contar conexiones con la BD llena (todas las unidades marcadas): de ~360 a 2.

---

# Bloque IV — Que se sienta una persona

Aquí es donde deja de parecer un sistema. Va al final porque toca prompts y tablas nuevas, y porque se apoya en todo lo anterior.

## 11 · Un solo prompt con diales en vez de dos personalidades

**reescritura** · `ai/prompts/profesor_japones.txt` + `profesor_japones_conv.txt` → `profesor_japones.txt` · `ai/sensei/profesor.py:229-249`
*Después de 07 · bloquea a 12 y 13 — va primero del bloque para no escribir las mismas reglas dos veces*

Fusionar los dos ficheros en uno. Identidad, reglas de voz y formato 【】 son comunes; lo que cambia entre clase y charla es la densidad de ejercicio, no quién es Kaito. Eso pasa a ser un dial:

```
{REGISTRO}  clase | mixto | charla

clase   → el FOCO manda, ejercicio explícito, corrección directa
mixto   → conversación con el FOCO colado de forma natural
charla  → sin temario; Kaito puede explicar si Laura pregunta
```

El detalle que arregla esto: hoy el modo charla tiene prohibido explicar («no uses estructura de clase»), así que si Laura pregunta algo de gramática mientras charlan, Kaito está instruido para esquivarlo. Con el dial, «espera, que esto te lo explico» deja de estar vetado en ningún registro.

`self.modo_conv` pasa de booleano a `self.registro` con tres valores. Los disparadores de `brain.py` se quedan como están y simplemente mapean a `clase` o `charla`; `mixto` queda disponible para que Kaito lo elija según el momento.

**Verificación:** en registro `charla`, preguntar «¿por qué aquí va が y no は?» y comprobar que responde en vez de redirigir a la conversación.

## 12 · Nivel de inmersión: que pueda hablar japonés de verdad

**~30 líneas** · `ai/prompts/profesor_japones.txt` · `ai/sensei/profesor.py:300-327` · `core/japanese_memory.py`
*Después de 05, 06, 07 y 11 — es la fase con más precondiciones del plan*

La regla de oro actual («SIEMPRE en español», «como mucho 1 o 2 expresiones cortas», «PROHIBIDO oraciones en japonés») hace imposible por construcción lo que pediste. Se sustituye por un dial derivado del progreso real de Laura:

```
{NIVEL_INMERSION}  1 → 4  (de vocab dominado + unidades abiertas)

1  como ahora: español con palabras sueltas entre 【】
2  saludos, ánimos y despedida en japonés
3  preguntas completas en japonés con apoyo en español detrás
4  juego de rol seguido; traducción solo si Laura la pide
```

Los bloques 【】 se mantienen —el TTS los necesita— pero dejan de estar limitados a una o dos expresiones cortas: pueden ser frases enteras y varias por turno. Por eso la Fase 05 va antes: en cuanto Kaito escriba 【うちに ねこが いますか。】, el fallo de puntuación del TTS pasa de anécdota a problema en cada turno.

El nivel se calcula, no se configura: algo como palabras en estado `learned` más `mastered` contra umbrales, para que suba solo según Laura avanza.

**Verificación:** forzar `NIVEL_INMERSION = 3` a mano y comprobar que Kaito abre el turno con una pregunta completa en japonés y la apoya después en español, sin pedir permiso.

## 13 · Memoria episódica: que recuerde a Laura y a sí mismo

**~50 líneas** · `core/japanese_memory.py` · `ai/prompts/extraccion_sesion.txt` · `ai/sensei/profesor.py:302-327`
*Después de 01 y 11*

Dos tablas pequeñas y un campo más en el JSON del extractor, que ya está leyendo la transcripción entera y no cuesta nada más.

| Tabla | Qué guarda |
|---|---|
| `laura_episodios` | qué contó de su vida en la sesión (el viaje, los perros, cómo le fue la semana) |
| `kaito_anecdotas` | qué ha afirmado Kaito sobre sí mismo, con la sesión en que lo dijo |

`kaito_anecdotas` arregla una contradicción que hoy está en el prompt: le pide inventarse anécdotas «divertidas y **consistentes**» sin darle dónde guardarlas, así que cada sesión se inventa un pasado nuevo que choca con el anterior.

Y en `RECUERDAS_DE_LAURA`, pasar de un resumen a los tres últimos, más los episodios. Eso es lo que permite abrir con «¿qué tal salió lo del médico que me contaste?» en vez de con «hoy repasamos みず».

**Verificación:** contar algo personal en una sesión, cerrarla, y comprobar en la siguiente que Kaito lo saca sin que se lo recuerdes.

---

# Pendiente — lo que este plan no cierra

Dos huecos del análisis que dejo fuera a propósito, para que no se pierdan.

**Corrección y bucle de repaso.** La tipología de corrección (qué se corrige y cuánto se interrumpe, con los errores no comentados guardados de una sesión a la siguiente) encaja de forma natural dentro de la Fase 11, porque es reescribir las mismas reglas del mismo fichero. La he dejado fuera como fase propia para no inflar el plan, pero si al llegar a la 11 quieres que la incluya, es media hora más ahí mismo.

Cerrar el bucle de repaso —calificar los ítems en el turno en que ocurren, en vez de reconstruirlo al final desde la transcripción— es el cambio más grande que queda y el único que replantea cómo funciona el SRS. Tiene sentido después de la 13, cuando el resto esté asentado y se pueda medir si el extractor a posteriori sigue fallando lo suficiente como para justificarlo.

---

*Plan derivado de la auditoría estática sobre `main` (1e62afa).*

*Fases 1 a 4: integridad de datos · 5 a 7: canal de voz y turno · 8 a 10: material didáctico · 11 a 13: personalidad y memoria.*

*Fuera de alcance por decisión: disparadores de modo amplios y aprobado de oficio del extractor.*
