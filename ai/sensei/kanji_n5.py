"""Los 108 kanji del JLPT N5, en formato de ítem del temario.

Cada kanji es un ítem `vocabulario` con `tipo: "kanji"`, así que entra en el
SRS por la tabla `japanese_vocabulary` sin tocar el esquema, y `_lineas_foco`
ya sabe leer su `ejemplo` / `literal` / `uso`.

Los datos extra (lecturas separadas, trazos, radical, mnemotecnia, vocabulario
de ejemplo) se guardan tal cual EN el ítem y además se resumen en `uso`, que
es el único campo que hoy llega al prompt.
"""

# (kanji, significado, on, kun, trazos, radical, ejemplo, literal, mnemotecnia, aparece_en)
_CATEGORIAS = [
    (
        "kanji_numeros", "Kanjis N5 — Números y cantidad",
        "leer precios, fechas y cantidades escritas: un ticket, un cartel de rebajas, un calendario",
        [
            {"jp": "何人ですか", "uso": "'¿cuántos sois?'; el 人 de la cuenta se lee にん"},
            {"jp": "おいくらですか", "uso": "'¿cuánto es?' en versión educada, con お delante"},
            {"jp": "ちょうどです", "uso": "'justo'; al pagar el importe exacto"},
        ],
        [
            ("一", "uno", "イチ・イツ", "ひと(つ)", 1, "一 (いち)", "一つ ください", "uno / por-favor",
             "un dedo tumbado sobre la mesa: el trazo único del 1", "一人 ひとり una persona · 一日 ついたち el día 1"),
            ("二", "dos", "ニ", "ふた(つ)", 2, "二 (に)", "二つ あります", "dos / hay",
             "dos dedos tumbados, uno sobre otro: el 2", "二人 ふたり dos personas · 二月 にがつ febrero"),
            ("三", "tres", "サン", "み(っつ)", 3, "一 (いち)", "三つ ください", "tres / por-favor",
             "tres dedos en fila: la serie 一二三 se lee de un vistazo", "三人 さんにん tres personas · 三日 みっか el día 3"),
            ("四", "cuatro", "シ", "よ・よん・よっ(つ)", 5, "囗 (くにがまえ)", "四時に あいましょう", "4h-A / quedemos",
             "una ventana (口) con las cortinas recogidas dentro: por sus 4 esquinas entra la luz", "四時 よじ las 4 · 四月 しがつ abril"),
            ("五", "cinco", "ゴ", "いつ(つ)", 4, "二 (に)", "五百円です", "500-yenes-es",
             "una mano que se cierra atrapada entre el techo y el suelo: quedan los 5 dedos dentro", "五時 ごじ las 5 · 五日 いつか el día 5"),
            ("六", "seis", "ロク", "むっ(つ)", 4, "八 (はち)", "六時に おきます", "6h-A / me-levanto",
             "un tejadillo (亠) con dos patas: una casa de juguete de 6 caras", "六月 ろくがつ junio · 六つ むっつ seis"),
            ("七", "siete", "シチ", "なな(つ)", 2, "一 (いち)", "今 七時です", "ahora / 7h-es",
             "una hoz que corta en diagonal: siega 7 espigas de una pasada", "七月 しちがつ julio · 七つ ななつ siete"),
            ("八", "ocho", "ハチ", "やっ(つ)", 2, "八 (はち)", "八百円 でした", "800-yenes / fue",
             "dos trazos que se abren hacia abajo: el 8 se ensancha y por eso da suerte", "八月 はちがつ agosto · 八百屋 やおや verdulería"),
            ("九", "nueve", "キュウ・ク", "ここの(つ)", 2, "乙 (おつ)", "九時に ねます", "9h-A / me-acuesto",
             "un brazo estirándose para tocar el 十 y que no llega: se queda en 9", "九月 くがつ septiembre (¡く, no きゅう!) · 九つ ここのつ nueve"),
            ("十", "diez", "ジュウ・ジッ", "とお", 2, "十 (じゅう)", "十人 います", "10-personas / hay",
             "los dos ejes cruzados y completos: la decena redonda", "十月 じゅうがつ octubre · 二十歳 はたち 20 años"),
            ("百", "cien", "ヒャク", "—", 6, "白 (しろ)", "三百円です", "300-yenes-es",
             "un 一 (uno) sentado sobre 白 (blanco): una sola cosa tan enorme y limpia que ya son 100", "百 ひゃく cien · 三百 さんびゃく 300 (¡suena びゃく!)"),
            ("千", "mil", "セン", "ち", 3, "十 (じゅう)", "千円 ください", "1000-yenes / por-favor",
             "un 十 (diez) con flequillo (ノ): diez multiplicado da 1000", "千円 せんえん 1000 yenes · 三千 さんぜん 3000 (¡ぜん!)"),
            ("万", "diez mil", "マン・バン", "—", 3, "一 (いち)", "一万円です", "10000-yenes-es",
             "un techo con un gancho que lo sujeta todo: debajo caben 10.000 cosas; en japonés se cuenta de 万 en 万", "一万 いちまん 10.000 · 万年筆 まんねんひつ pluma"),
            ("円", "yen / círculo", "エン", "まる(い)", 4, "冂 (けいがまえ)", "いくらですか。五百円です", "¿cuánto-es? / 500-yenes-es",
             "un marco (冂) con una moneda de canto dentro: el yen", "円 えん yen · 百円玉 ひゃくえんだま moneda de 100"),
        ],
    ),
    (
        "kanji_elementos", "Kanjis N5 — Elementos naturales",
        "los cinco elementos (火水木金土): con 曜日 detrás nombran los días de la semana, y sueltos salen en decenas de palabras del día a día",
        [
            {"jp": "花火を 見に 行きました", "uso": "'fuimos a ver fuegos artificiales'; 花 (flor) + 火 (fuego)"},
            {"jp": "お金を おろします", "uso": "'voy a sacar dinero'; el 金 de お金 es el de 金曜日"},
            {"jp": "木の 下で 休みましょう", "uso": "'descansemos bajo el árbol'"},
        ],
        [
            ("火", "fuego", "カ", "ひ", 4, "火 (ひ)", "火曜日は やすみです", "martes-TEMA / descanso-es",
             "una hoguera: el leño central y dos chispas saltando a los lados", "火曜日 かようび martes · 花火 はなび fuegos artificiales"),
            ("水", "agua", "スイ", "みず", 4, "水 (みず)", "お水を ください", "agua-OBJ / por-favor",
             "un chorro central con salpicaduras a ambos lados: agua que cae", "水 みず agua · 水曜日 すいようび miércoles"),
            ("木", "árbol / madera", "モク・ボク", "き", 4, "木 (きへん)", "木の 下で まっています", "árbol-DE / debajo-EN / estoy-esperando",
             "un tronco con dos ramas arriba y dos raíces abajo: un árbol", "木 き árbol · 木曜日 もくようび jueves"),
            ("金", "oro / dinero", "キン", "かね", 8, "金 (かねへん)", "お金が ありません", "dinero-SUJ / no-hay",
             "un tejado (𠆢) sobre lingotes (王) enterrados y dos pepitas (丷): un tesoro guardado", "お金 おかね dinero · 金曜日 きんようび viernes"),
            ("土", "tierra", "ド", "つち", 3, "土 (つちへん)", "土曜日に 行きます", "sábado-A / voy",
             "una estaca clavada en el suelo (la raya de abajo): así marcas tu trozo de tierra", "土曜日 どようび sábado · 土 つち tierra"),
        ],
    ),
    (
        "kanji_tiempo", "Kanjis N5 — Tiempo y calendario",
        "leer un horario, un calendario y los carteles de apertura de una tienda",
        [
            {"jp": "何曜日ですか", "uso": "'¿qué día de la semana es?'; se responde con un elemento + 曜日 (月火水木金土日)"},
            {"jp": "今日は 何日ですか", "uso": "'¿a qué día del mes estamos?'"},
            {"jp": "時間が ないんです", "uso": "'es que no tengo tiempo'; excusa educada y comodín"},
        ],
        [
            ("日", "día / sol", "ニチ・ジツ", "ひ・か", 4, "日 (ひへん)", "今日は いい 日ですね", "hoy-TEMA / buen / día-es-¿verdad?",
             "un recuadro con una raya en medio: el disco del sol con su mancha; cuando sale, empieza el día", "日本 にほん Japón · 三日 みっか el día 3 · 日曜日 にちようび domingo"),
            ("月", "mes / luna", "ゲツ・ガツ", "つき", 4, "月 (つきへん)", "月曜日に あいます", "lunes-A / quedamos",
             "una ventana estrecha con dos baldas: por ella asoma la luna, y una luna llena marca un mes", "月曜日 げつようび lunes · 一月 いちがつ enero · 今月 こんげつ este mes"),
            ("曜", "día de la semana", "ヨウ", "—", 18, "日 (ひへん)", "何曜日ですか", "¿qué-día-de-la-semana-es?",
             "cada día es un elemento + 曜日: 月(luna) 火 水 木 金 土 日(sol). 曜 es 日 (sol) con alas (羽) y un pájaro (隹), y solo vive en 〜曜日",
             "月曜日 げつようび lunes · 火曜日 かようび martes · 水曜日 すいようび miércoles · 木曜日 もくようび jueves · 金曜日 きんようび viernes · 土曜日 どようび sábado · 日曜日 にちようび domingo"),
            # los 7 días como palabra: cada uno su tarjeta, para practicarlos por separado
            ("月曜日", "lunes", "—", "げつようび", 26, "—", "月曜日に あいましょう", "lunes-EN / quedemos",
             "月 (luna) + 曜日: el día de la Luna; aquí 月 se lee げつ", "月曜日 げつようび lunes · 毎週月曜日 まいしゅうげつようび todos los lunes"),
            ("火曜日", "martes", "—", "かようび", 26, "—", "火曜日は やすみです", "martes-TEMA / descanso-es",
             "火 (fuego) + 曜日: el día del Fuego (Marte)", "火曜日 かようび martes · 火曜 かよう martes (informal)"),
            ("水曜日", "miércoles", "—", "すいようび", 26, "—", "水曜日に テストが あります", "miércoles-EN / examen-SUJ / hay",
             "水 (agua) + 曜日: el día del Agua (Mercurio)", "水曜日 すいようび miércoles · 水曜 すいよう miércoles (informal)"),
            ("木曜日", "jueves", "—", "もくようび", 26, "—", "木曜日まで まって ください", "jueves-HASTA / espera / por-favor",
             "木 (árbol) + 曜日: el día de la Madera (Júpiter)", "木曜日 もくようび jueves · 木曜 もくよう jueves (informal)"),
            ("金曜日", "viernes", "—", "きんようび", 30, "—", "金曜日の 夜は ひまです", "viernes-DE / noche-TEMA / libre-estoy",
             "金 (oro) + 曜日: el día del Metal (Venus); aquí 金 se lee きん", "金曜日 きんようび viernes · 花金 はなきん 'por fin viernes' (coloquial)"),
            ("土曜日", "sábado", "—", "どようび", 25, "—", "土曜日に かいものを します", "sábado-EN / compras-OBJ / hago",
             "土 (tierra) + 曜日: el día de la Tierra (Saturno); aquí 土 se lee ど", "土曜日 どようび sábado · 土曜 どよう sábado (informal)"),
            ("日曜日", "domingo", "—", "にちようび", 26, "—", "日曜日は 休みます", "domingo-TEMA / descanso",
             "日 (sol) + 曜日: el día del Sol; aquí 日 se lee にち", "日曜日 にちようび domingo · 日曜 にちよう domingo (informal)"),
            ("年", "año", "ネン", "とし", 6, "干 (かん)", "来年 日本に 行きます", "año-que-viene / Japón-A / voy",
             "alguien cargando al hombro una espiga (禾): una cosecha recogida = un año", "今年 ことし este año · 去年 きょねん el año pasado"),
            ("時", "hora / momento", "ジ", "とき", 10, "日 (ひへん)", "今 何時ですか", "ahora / ¿qué-hora-es?",
             "el sol (日) al lado de un templo (寺): el reloj de sol del templo da la hora", "時間 じかん tiempo · 一時 いちじ la 1 · 時々 ときどき a veces"),
            ("分", "minuto / dividir", "フン・ブン", "わ(ける)・わ(かる)", 4, "刀 (かたな)", "十分 まって ください", "10-minutos / espera / por-favor",
             "un cuchillo (刀) que parte algo en dos (八): trocear la hora en minutos, o dividir cualquier cosa", "五分 ごふん 5 min · 分かる わかる entender"),
            ("半", "mitad", "ハン", "なか(ば)", 5, "十 (じゅう)", "二時半に あいましょう", "2h-y-media-A / quedemos",
             "una res (de 牛) partida por el eje vertical: media vaca = la mitad", "半分 はんぶん la mitad · 二時半 にじはん las 2:30"),
            ("今", "ahora", "コン", "いま", 4, "人 (ひとやね)", "今 行きます", "ahora / voy",
             "un tejado (亼) sobre una viga: aquí debajo, en este preciso instante = ahora", "今日 きょう hoy · 今年 ことし este año · 今 いま ahora"),
            ("週", "semana", "シュウ", "—", 11, "辵 (しんにょう)", "来週 あいましょう", "semana-que-viene / quedemos",
             "un pie que anda (辶) llevando una vuelta completa (周): siete días dan la vuelta = una semana", "今週 こんしゅう esta semana · 週末 しゅうまつ fin de semana"),
            ("間", "intervalo / entre", "カン", "あいだ", 12, "門 (もんがまえ)", "三時間 べんきょうしました", "3-horas / estudié",
             "el sol (日) colándose por la rendija de un portón (門): el hueco, el rato entre dos cosas", "時間 じかん tiempo · 人間 にんげん ser humano"),
            ("毎", "cada", "マイ", "—", 6, "毋 (なかれ)", "毎日 日本語を べんきょうします", "cada-día / japonés-OBJ / estudio",
             "una madre (母) con un sombrero puesto (𠂉): mamá hace lo mismo un día y otro = cada día", "毎日 まいにち todos los días · 毎朝 まいあさ cada mañana"),
            ("午", "mediodía", "ゴ", "—", 4, "十 (じゅう)", "午後 あいましょう", "por-la-tarde / quedemos",
             "un poste de sombra clavado: al mediodía su sombra es la más corta; solo aparece en 午前 / 午後", "午前 ごぜん a.m. · 午後 ごご p.m."),
            ("前", "antes / delante", "ゼン", "まえ", 9, "刀 (りっとう)", "駅の 前で まってます", "estación-DE / delante-EN / estoy-esperando",
             "una luna de carne (月) y un cuchillo (刂) bajo un tejadillo: lo que va cortado por delante, en el sitio y en el tiempo", "名前 なまえ nombre · 午前 ごぜん a.m. · 前 まえ delante"),
            ("後", "después / detrás", "ゴ・コウ", "あと・うし(ろ)", 9, "彳 (ぎょうにんべん)", "後で 電話します", "después-EN / llamo",
             "un caminito (彳) con los pies enredados en hilos (幺夂): quien se enreda llega detrás y más tarde", "午後 ごご p.m. · 後ろ うしろ detrás · 後で あとで luego"),
        ],
    ),
    (
        "kanji_posicion", "Kanjis N5 — Posición y direcciones",
        "leer indicaciones, planos y nombres de estación: saber a qué lado y hacia dónde",
        [
            {"jp": "この 先です", "uso": "'un poco más adelante'; lo oirás al preguntar por una dirección"},
            {"jp": "つきあたりを 右", "uso": "'al fondo, a la derecha'"},
            {"jp": "反対がわです", "uso": "'está en el lado contrario'; típico en el andén"},
        ],
        [
            ("上", "arriba / encima", "ジョウ", "うえ・あ(がる)", 3, "一 (いち)", "つくえの 上に あります", "mesa-DE / encima-EN / está",
             "una línea de suelo con un trazo que sube desde ella: lo que queda por encima", "上 うえ encima · 上手 じょうず hábil"),
            ("下", "abajo / debajo", "カ・ゲ", "した・さ(がる)", 3, "一 (いち)", "いすの 下に ねこが います", "silla-DE / debajo-EN / gato-SUJ / hay",
             "una línea de techo con un trazo que cuelga: lo que queda por debajo; es 上 del revés", "下 した debajo · 下手 へた torpe · 地下鉄 ちかてつ metro"),
            ("中", "dentro / en medio", "チュウ", "なか", 4, "丨 (たてぼう)", "かばんの 中に あります", "bolso-DE / dentro-EN / está",
             "una flecha que atraviesa una caja justo por el centro: en medio, dentro", "中 なか dentro · 中国 ちゅうごく China · 一日中 いちにちじゅう todo el día"),
            ("外", "fuera / exterior", "ガイ", "そと", 5, "夕 (ゆうべ)", "外は さむいですよ", "fuera-TEMA / frío-es-¡eh!",
             "la tarde (夕) más la vara de adivinar (卜): los augurios se echaban de noche y fuera de casa", "外 そと fuera · 外国 がいこく extranjero · 外国人 がいこくじん extranjero"),
            ("右", "derecha", "ウ・ユウ", "みぎ", 5, "口 (くち)", "つぎの かどを 右に まがって ください", "siguiente / esquina-OBJ / derecha-A / gira / por-favor",
             "una mano (𠂇) sobre una boca (口): con la mano derecha te llevas la comida a la boca", "右 みぎ derecha · 右手 みぎて mano derecha"),
            ("左", "izquierda", "サ", "ひだり", 5, "工 (たくみ)", "左の 店です", "izquierda-DE / tienda-es",
             "una mano (𠂇) sobre una herramienta (工): la izquierda es la que sujeta mientras la derecha trabaja", "左 ひだり izquierda · 左手 ひだりて mano izquierda"),
            ("東", "este", "トウ", "ひがし", 8, "木 (き)", "東京に すんでいます", "Tokio-EN / vivo",
             "el sol (日) atrapado tras un árbol (木): amanece, o sea, sale por el este", "東京 とうきょう Tokio · 東 ひがし este"),
            ("西", "oeste", "セイ・サイ", "にし", 6, "西 (にし)", "西の そらが あかいです", "oeste-DE / cielo-SUJ / rojo-es",
             "un pájaro metiéndose en el nido: se recoge al atardecer, cuando el sol se pone por el oeste", "西 にし oeste · 関西 かんさい la región de Kansai"),
            ("南", "sur", "ナン", "みなみ", 9, "十 (じゅう)", "南は あたたかいです", "sur-TEMA / cálido-es",
             "un invernadero con una planta dentro: la pared sur recibe el sol y todo brota", "南 みなみ sur · 南口 みなみぐち salida sur"),
            ("北", "norte", "ホク", "きた", 5, "匕 (さじのひ)", "北は さむいです", "norte-TEMA / frío-es",
             "dos personas sentadas espalda contra espalda: se protegen del frío que viene del norte", "北 きた norte · 北海道 ほっかいどう Hokkaido"),
        ],
    ),
    (
        "kanji_personas", "Kanjis N5 — Personas, familia y escuela",
        "leer nombres, carteles de aula y formularios donde te preguntan quién eres",
        [
            {"jp": "お名前を お願いします", "uso": "'su nombre, por favor'; lo dicen en cualquier mostrador"},
            {"jp": "ご家族は", "uso": "'¿y tu familia?'"},
            {"jp": "先生に 聞いてみます", "uso": "'se lo preguntaré al profe'"},
        ],
        [
            ("人", "persona", "ジン・ニン", "ひと", 2, "人 (ひと)", "あの 人は だれですか", "aquella / persona-TEMA / ¿quién-es?",
             "dos piernas dando un paso: una persona andando", "人 ひと persona · 日本人 にほんじん japonés · 三人 さんにん tres personas"),
            ("男", "hombre", "ダン", "おとこ", 7, "田 (た)", "男の 人が 二人 います", "hombre-DE / persona-SUJ / dos / hay",
             "un campo (田) encima de la fuerza (力): el que echa los riñones en el campo", "男 おとこ hombre · 男の子 おとこのこ niño"),
            ("女", "mujer", "ジョ", "おんな", 3, "女 (おんな)", "女の 人と はなしました", "mujer-DE / persona-CON / hablé",
             "una figura sentada con las piernas y los brazos recogidos", "女 おんな mujer · 女の子 おんなのこ niña · 彼女 かのじょ ella"),
            ("子", "niño / hijo", "シ", "こ", 3, "子 (こへん)", "子どもが 三人 います", "niños-SUJ / tres / hay",
             "una cabeza grande y dos bracitos abiertos, envuelto en una manta: un bebé", "子ども こども niño · 女子 じょし chica · 息子 むすこ hijo"),
            ("母", "madre (propia)", "ボ", "はは", 5, "毋 (なかれ)", "母は 元気です", "madre-TEMA / bien-está",
             "una mujer con dos puntos marcados: los pechos con que amamanta = madre", "母 はは mi madre · お母さん おかあさん su madre"),
            ("父", "padre (propio)", "フ", "ちち", 4, "父 (ちち)", "父は 会社に います", "padre-TEMA / empresa-EN / está",
             "dos manos cruzadas empuñando un hacha: el que sale a bregar = padre", "父 ちち mi padre · お父さん おとうさん su padre"),
            ("友", "amigo", "ユウ", "とも", 4, "又 (また)", "友だちと 会います", "amigo-CON / quedo",
             "dos manos (𠂇 y 又) que se estrechan: un apretón = un amigo", "友だち ともだち amigo · 友人 ゆうじん amistad (formal)"),
            ("先", "antes / previo / punta", "セン", "さき", 6, "儿 (にんにょう)", "お先に しつれいします", "antes-que-usted / me-retiro",
             "un pie (儿) con la punta asomando por delante (𠂉): el que va primero, el que se adelanta", "先生 せんせい profesor · 先週 せんしゅう la semana pasada"),
            ("生", "vida / nacer / crudo", "セイ・ショウ", "う(まれる)・い(きる)・なま", 5, "生 (うまれる)", "私は 学生です", "yo-TEMA / estudiante-soy",
             "un brote (屮) empujando hacia arriba desde la tierra (土): algo que nace y crece", "学生 がくせい estudiante · 生ビール なまビール cerveza de barril"),
            ("学", "estudiar / ciencia", "ガク", "まな(ぶ)", 8, "子 (こ)", "日本語を 学んでいます", "japonés-OBJ / estoy-estudiando",
             "un niño (子) bajo un tejado con destellos (⺍): el aula donde al crío se le encienden las ideas", "学校 がっこう escuela · 大学 だいがく universidad · 学生 がくせい estudiante"),
            ("校", "escuela", "コウ", "—", 10, "木 (きへん)", "学校に 行きます", "escuela-A / voy",
             "un árbol (木) cruzado con otro (交): troncos cruzados formando la valla del colegio", "学校 がっこう escuela · 高校 こうこう instituto"),
            ("名", "nombre", "メイ", "な", 6, "口 (くち)", "お名前は", "¿su-nombre-TEMA?",
             "la noche (夕) más una boca (口): a oscuras no te ven, así que dices tu nombre en voz alta", "名前 なまえ nombre · 有名 ゆうめい famoso"),
        ],
    ),
    (
        "kanji_cuerpo", "Kanjis N5 — Cuerpo",
        "leer un cartel de farmacia o de clínica y señalar por escrito qué te duele",
        [
            {"jp": "どこが 痛いですか", "uso": "'¿dónde le duele?'; te lo preguntarán en la consulta"},
            {"jp": "手を あらってください", "uso": "'lávate las manos'"},
            {"jp": "足もとに ご注意", "uso": "'cuidado con el escalón'; cartel omnipresente"},
        ],
        [
            ("口", "boca / entrada", "コウ", "くち", 3, "口 (くち)", "口を あけて ください", "boca-OBJ / abre / por-favor",
             "un cuadrado abierto: una boca vista de frente", "口 くち boca · 入口 いりぐち entrada · 出口 でぐち salida"),
            ("目", "ojo", "モク", "め", 5, "目 (め)", "目が いたいです", "ojo-SUJ / duele",
             "un ojo puesto de pie: el marco y, dentro, las dos rayas del iris", "目 め ojo · 一つ目 ひとつめ el primero"),
            ("耳", "oreja / oído", "ジ", "みみ", 6, "耳 (みみへん)", "耳が よく 聞こえません", "oído-SUJ / bien / no-oigo",
             "el contorno de una oreja de perfil, con el lóbulo colgando abajo", "耳 みみ oreja"),
            ("手", "mano", "シュ", "て", 4, "手 (てへん)", "手を あらいます", "manos-OBJ / me-lavo",
             "una muñeca con los dedos abiertos: una mano en alto", "手 て mano · 上手 じょうず hábil · 切手 きって sello"),
            ("足", "pie / pierna / bastar", "ソク", "あし・た(りる)", 7, "足 (あしへん)", "足が つかれました", "piernas-SUJ / se-cansaron",
             "una rodilla (口) con un pie (止) debajo: la pierna entera; y también 'bastar', ya tienes patas para llegar", "足 あし pie · 足りる たりる ser suficiente"),
        ],
    ),
    (
        "kanji_acciones", "Kanjis N5 — Acciones",
        "reconocer escritos los verbos que ya sabes decir: un menú, un cartel, un botón",
        [
            {"jp": "何と 書いてありますか", "uso": "'¿qué pone ahí?'; para preguntar por un cartel"},
            {"jp": "読めません", "uso": "'no sé leerlo'; sin vergüenza, lo dice todo el mundo"},
            {"jp": "見て 見て！", "uso": "'¡mira, mira!', informal"},
        ],
        [
            ("行", "ir", "コウ", "い(く)・おこな(う)", 6, "行 (ぎょうがまえ)", "学校に 行きます", "escuela-A / voy",
             "un cruce de calles visto desde arriba: desde ahí puedes ir a cualquier parte", "行く いく ir · 銀行 ぎんこう banco · 旅行 りょこう viaje"),
            ("来", "venir", "ライ", "く(る)", 7, "木 (き)", "友だちが 来ます", "amigo-SUJ / viene",
             "un árbol (木) del camino con dos personitas (𠆢) acercándose: vienen hacia aquí", "来る くる venir · 来年 らいねん el año que viene"),
            ("見", "ver / mirar", "ケン", "み(る)", 7, "見 (みる)", "テレビを 見ます", "tele-OBJ / veo",
             "un ojo enorme (目) con piernas (儿): el ojo que se acerca a mirar", "見る みる ver · 見せる みせる mostrar · 花見 はなみ ver los cerezos"),
            ("聞", "escuchar / preguntar", "ブン・モン", "き(く)", 14, "耳 (みみ)", "音楽を 聞きます", "música-OBJ / escucho",
             "una oreja (耳) pegada a un portón (門): escuchar lo que suena al otro lado", "聞く きく escuchar · 新聞 しんぶん periódico"),
            ("読", "leer", "ドク", "よ(む)", 14, "言 (ごんべん)", "本を 読みます", "libro-OBJ / leo",
             "palabras (言) puestas a la venta (売): leer es hacer que las palabras circulen", "読む よむ leer · 読書 どくしょ lectura"),
            ("書", "escribir", "ショ", "か(く)", 10, "曰 (ひらび)", "名前を 書いて ください", "nombre-OBJ / escribe / por-favor",
             "un pincel (聿) goteando tinta sobre una hoja (曰): trazar letras", "書く かく escribir · 辞書 じしょ diccionario · 図書館 としょかん biblioteca"),
            ("話", "hablar / historia", "ワ", "はな(す)・はなし", 13, "言 (ごんべん)", "日本語を 話します", "japonés-OBJ / hablo",
             "palabras (言) que salen de la lengua (舌): conversar, contar algo", "話す はなす hablar · 電話 でんわ teléfono · お話 おはなし cuento"),
            ("言", "decir", "ゲン・ゴン", "い(う)", 7, "言 (ことば)", "何と 言いましたか", "qué-QUE / ¿dijiste?",
             "una boca (口) con las palabras saliendo en capas hacia arriba", "言う いう decir · 言葉 ことば palabra"),
            ("食", "comer", "ショク", "た(べる)", 9, "食 (しょくへん)", "ごはんを 食べます", "comida-OBJ / como",
             "un tejado (𠆢) sobre un cuenco de arroz servido: sentarse a comer", "食べる たべる comer · 食堂 しょくどう comedor · 食事 しょくじ comida"),
            ("飲", "beber", "イン", "の(む)", 12, "食 (しょくへん)", "お茶を 飲みます", "té-OBJ / bebo",
             "comida (食) más una boca muy abierta (欠): echar la cabeza atrás para tragar líquido", "飲む のむ beber · 飲み物 のみもの bebida"),
            ("買", "comprar", "バイ", "か(う)", 12, "貝 (かい)", "パンを 買います", "pan-OBJ / compro",
             "una red (罒) cae sobre unas conchas (貝): las conchas eran monedas; atrapas lo que compras al pagar", "買う かう comprar · 買い物 かいもの la compra"),
            ("出", "salir / sacar", "シュツ", "で(る)・だ(す)", 5, "凵 (かんにょう)", "八時に 家を 出ます", "8h-A / casa-OBJ / salgo",
             "dos montículos apilados (山 sobre 山): algo que brota y asoma hacia fuera", "出る でる salir · 出口 でぐち salida · 出す だす sacar"),
            ("入", "entrar / meter", "ニュウ", "はい(る)・い(れる)", 2, "入 (いる)", "店に 入ります", "tienda-A / entro",
             "una boca de cueva con el trazo largo a la izquierda: se mete hacia dentro; no lo confundas con 人", "入る はいる entrar · 入口 いりぐち entrada"),
            ("立", "estar de pie", "リツ", "た(つ)", 5, "立 (たつ)", "ここに 立って ください", "aquí-EN / ponte-de-pie / por-favor",
             "una persona (大) firme sobre una línea de suelo: plantada, de pie", "立つ たつ ponerse de pie · 立派 りっぱ espléndido"),
            ("休", "descansar", "キュウ", "やす(む)", 6, "人 (にんべん)", "日曜日は 休みます", "domingo-TEMA / descanso",
             "una persona (亻) apoyada en un árbol (木): pararse a la sombra a descansar", "休む やすむ descansar · 休み やすみ descanso · 昼休み ひるやすみ pausa"),
        ],
    ),
    (
        "kanji_naturaleza", "Kanjis N5 — Naturaleza y objetos",
        "leer la previsión del tiempo, un nombre de sitio y los carteles de la calle",
        [
            {"jp": "いい 天気ですね", "uso": "'qué buen tiempo'; el arranque de conversación por excelencia"},
            {"jp": "雨が ふりそう", "uso": "'parece que va a llover'"},
            {"jp": "気を つけて", "uso": "'ten cuidado'; con el mismo 気 de 元気"},
        ],
        [
            ("山", "montaña", "サン", "やま", 3, "山 (やま)", "山に のぼります", "montaña-A / subo",
             "tres picos, el del centro más alto: una sierra vista de frente", "山 やま montaña · 富士山 ふじさん el monte Fuji · 火山 かざん volcán"),
            ("川", "río", "セン", "かわ", 3, "巛 (かわ)", "川で およぎました", "río-EN / nadé",
             "tres líneas de corriente bajando en paralelo: el cauce de un río", "川 かわ río · 小川 おがわ arroyo"),
            ("天", "cielo", "テン", "あま", 4, "大 (だい)", "天気が いいですね", "tiempo-SUJ / bueno-es-¿verdad?",
             "una persona 大 con el techo del mundo encima", "天気 てんき el tiempo · 天ぷら てんぷら tempura"),
            ("気", "ánimo / aire / energía", "キ・ケ", "—", 6, "气 (きがまえ)", "お元気ですか", "¿está-usted-bien?",
             "vapor saliendo de una olla: lo invisible que se nota", "元気 げんき con energía · 天気 てんき el tiempo · 気持ち きもち sentimiento"),
            ("雨", "lluvia", "ウ", "あめ", 8, "雨 (あめかんむり)", "雨が ふっています", "lluvia-SUJ / está-cayendo",
             "una ventana con gotas cayendo", "雨 あめ lluvia · 大雨 おおあめ lluvia fuerte"),
            ("電", "electricidad", "デン", "—", 13, "雨 (あめかんむり)", "電車で 行きます", "tren-EN / voy",
             "雨 (lluvia) + un rayo: la tormenta eléctrica", "電車 でんしゃ tren · 電話 でんわ teléfono · 電気 でんき la luz"),
            ("車", "coche / vehículo", "シャ", "くるま", 7, "車 (くるまへん)", "車で 行きましょう", "coche-EN / vayamos",
             "un carro visto desde arriba, con el eje y las ruedas", "車 くるま coche · 電車 でんしゃ tren · 自転車 じてんしゃ bici"),
            ("花", "flor", "カ", "はな", 7, "艸 (くさかんむり)", "花が きれいですね", "flores-SUJ / bonitas-son-¿verdad?",
             "la くさかんむり (hierba) corona siempre lo vegetal", "花 はな flor · 花見 はなみ ver los cerezos · 花火 はなび fuegos"),
            ("魚", "pez / pescado", "ギョ", "さかな", 11, "魚 (うおへん)", "魚を 食べます", "pescado-OBJ / como",
             "una cabeza, un cuerpo y cuatro puntos de cola", "魚 さかな pescado · 金魚 きんぎょ pez de colores"),
            ("空", "cielo / vacío", "クウ", "そら・あ(く)・から", 8, "穴 (あなかんむり)", "空が 青いです", "cielo-SUJ / azul-es",
             "あなかんむり (cueva) sobre 工: el hueco donde no hay nada", "空 そら cielo · 空港 くうこう aeropuerto · 空気 くうき aire"),
            ("田", "arrozal / campo", "デン", "た", 5, "田 (た)", "田んぼで はたらきます", "arrozal-EN / trabajo",
             "una parcela de tierra dividida en cuatro", "田んぼ たんぼ arrozal · 田舎 いなか el campo · 山田 やまだ apellido"),
        ],
    ),
    (
        "kanji_lugares", "Kanjis N5 — Lugares",
        "orientarte por escrito: encontrar la estación, la tienda y la salida correcta",
        [
            {"jp": "駅は どこですか", "uso": "'¿dónde está la estación?'"},
            {"jp": "この 道を まっすぐ", "uso": "'todo recto por esta calle'"},
            {"jp": "本日 休業", "uso": "'hoy cerrado'; cartel de tienda, muy frecuente"},
        ],
        [
            ("国", "país", "コク", "くに", 8, "囗 (くにがまえ)", "どこの 国から 来ましたか", "qué-DE / país-DESDE / ¿viniste?",
             "un tesoro 玉 dentro de una muralla 囗", "国 くに país · 外国 がいこく extranjero · 中国 ちゅうごく China"),
            ("本", "libro / origen", "ホン", "もと", 5, "木 (き)", "本を 読みます", "libro-OBJ / leo",
             "un árbol 木 con la raíz marcada: el origen", "本 ほん libro · 日本 にほん Japón · 本当 ほんとう de verdad"),
            ("社", "empresa / santuario", "シャ", "やしろ", 7, "示 (しめすへん)", "会社に 行きます", "empresa-A / voy",
             "しめすへん es el radical de lo sagrado", "会社 かいしゃ empresa · 神社 じんじゃ santuario · 社長 しゃちょう jefe"),
            ("会", "reunirse / encuentro", "カイ", "あ(う)", 6, "人 (ひとやね)", "友だちに 会います", "amigo-CON / quedo",
             "un tejado sobre gente reunida; ojo: 会う lleva に, no を", "会う あう encontrarse · 会社 かいしゃ empresa · 会議 かいぎ reunión"),
            ("店", "tienda", "テン", "みせ", 8, "广 (まだれ)", "その 店は しまっています", "esa / tienda-TEMA / está-cerrada",
             "まだれ es un edificio con la fachada abierta a la calle", "店 みせ tienda · 喫茶店 きっさてん cafetería · 売店 ばいてん quiosco"),
            ("駅", "estación de tren", "エキ", "—", 14, "馬 (うまへん)", "駅は どこですか", "estación-TEMA / ¿dónde-está?",
             "馬 (caballo): la posta de caballos antes del tren", "駅 えき estación · 駅前 えきまえ delante de la estación"),
            ("道", "camino / vía", "ドウ", "みち", 12, "辵 (しんにょう)", "この 道を まっすぐ 行って ください", "este / camino-POR / recto / ve / por-favor",
             "しんにょう (movimiento) + 首 (cabeza): ir de cabeza", "道 みち calle · 北海道 ほっかいどう Hokkaido · 柔道 じゅうどう yudo"),
            ("町", "pueblo / barrio", "チョウ", "まち", 7, "田 (た)", "この 町は しずかです", "este / pueblo-TEMA / tranquilo-es",
             "田 (campo) + 丁 (parcela): campos ordenados en manzanas", "町 まち pueblo · 下町 したまち barrio viejo · 町内 ちょうない el vecindario"),
        ],
    ),
    (
        "kanji_adjetivos", "Kanjis N5 — Adjetivos",
        "leer etiquetas y anuncios: qué es nuevo, qué es barato y qué es grande",
        [
            {"jp": "安いですね", "uso": "'qué barato'; se dice en voz alta en cualquier tienda"},
            {"jp": "大丈夫です", "uso": "con el 大 de 'grande'; sirve para 'estoy bien' y para 'no, gracias'"},
            {"jp": "新しいの ありますか", "uso": "'¿tienen uno nuevo?'"},
        ],
        [
            ("大", "grande", "ダイ・タイ", "おお(きい)", 3, "大 (だい)", "大きい 家ですね", "grande / casa-es-¿verdad?",
             "una persona con los brazos muy abiertos", "大きい おおきい grande · 大学 だいがく universidad · 大丈夫 だいじょうぶ tranquilo"),
            ("小", "pequeño", "ショウ", "ちい(さい)・こ", 3, "小 (しょう)", "小さい 声で はなして ください", "pequeña / voz-CON / habla / por-favor",
             "algo partido en trocitos", "小さい ちいさい pequeño · 小学校 しょうがっこう primaria"),
            ("高", "alto / caro", "コウ", "たか(い)", 10, "高 (たかい)", "この 時計は 高いです", "este / reloj-TEMA / caro-es",
             "una torre de varios pisos: 'alto' y 'caro' son la misma palabra", "高い たかい alto/caro · 高校 こうこう instituto"),
            ("安", "barato / tranquilo", "アン", "やす(い)", 6, "宀 (うかんむり)", "スーパーは 安いです", "súper-TEMA / barato-es",
             "una mujer 女 bajo un techo 宀: la casa tranquila", "安い やすい barato · 安心 あんしん tranquilidad"),
            ("新", "nuevo", "シン", "あたら(しい)", 13, "斤 (おのづくり)", "新しい かばんを 買いました", "nueva / bolsa-OBJ / compré",
             "un hacha 斤 cortando madera fresca", "新しい あたらしい nuevo · 新聞 しんぶん periódico · 新幹線 しんかんせん el bala"),
            ("古", "viejo / antiguo", "コ", "ふる(い)", 5, "口 (くち)", "この ビルは 古いです", "este / edificio-TEMA / viejo-es",
             "十 (diez) + 口 (bocas): lo que pasó por diez generaciones", "古い ふるい viejo · 中古 ちゅうこ de segunda mano"),
            ("長", "largo / jefe", "チョウ", "なが(い)", 8, "長 (ながい)", "長い 話でした", "larga / charla-fue",
             "un anciano con el pelo largo", "長い ながい largo · 社長 しゃちょう jefe · 校長 こうちょう director"),
            ("白", "blanco", "ハク", "しろ(い)", 5, "白 (しろ)", "白い くつを 買いました", "blancos / zapatos-OBJ / compré",
             "un rayo de sol 日 con una chispa encima", "白い しろい blanco · 白 しろ el blanco · 面白い おもしろい interesante"),
            ("多", "mucho / abundante", "タ", "おお(い)", 6, "夕 (ゆうべ)", "人が 多いです", "gente-SUJ / mucha-es",
             "dos 夕 (tarde) apiladas: noche tras noche se acumulan", "多い おおい mucho · 多分 たぶん quizá"),
            ("少", "poco / escaso", "ショウ", "すく(ない)・すこ(し)", 4, "小 (しょう)", "お金が 少ないです", "dinero-SUJ / poco-es",
             "小 (pequeño) con un trazo que se escapa: aún menos", "少ない すくない poco · 少し すこし un poco"),
        ],
    ),
    (
        "kanji_lengua", "Kanjis N5 — Lengua y escritura",
        "hablar del propio idioma y preguntar por lo que está escrito",
        [
            {"jp": "日本語で 何と 言いますか", "uso": "'¿cómo se dice en japonés?'"},
            {"jp": "この 字は 何ですか", "uso": "'¿qué carácter es este?'"},
            {"jp": "漢字は むずかしいです", "uso": "'los kanji son difíciles'; te dará la razón cualquier japonés"},
        ],
        [
            ("何", "qué / cuánto", "カ", "なに・なん", 7, "人 (にんべん)", "これは 何ですか", "esto-TEMA / ¿qué-es?",
             "なに solo; なん delante de contador: 何時 なんじ, 何人 なんにん", "何 なに qué · 何時 なんじ qué hora · 何人 なんにん cuántas personas"),
            ("語", "idioma / palabra", "ゴ", "かた(る)", 14, "言 (ごんべん)", "日本語を 話します", "japonés-OBJ / hablo",
             "país + 語 da su idioma: 英語, スペイン語", "日本語 にほんご japonés · 英語 えいご inglés · 単語 たんご vocabulario"),
            ("文", "texto / frase", "ブン", "ふみ", 4, "文 (ぶん)", "文を 書いて ください", "frase-OBJ / escribe / por-favor",
             "un dibujo tatuado en un pecho: la primera escritura", "文 ぶん frase · 文化 ぶんか cultura · 作文 さくぶん redacción"),
            ("字", "carácter / letra", "ジ", "あざ", 6, "子 (こ)", "字が きれいですね", "letra-SUJ / bonita-es-¿verdad?",
             "un niño 子 bajo un techo 宀: donde se aprenden las letras", "漢字 かんじ kanji · 字 じ letra · ローマ字 ローマじ romaji"),
        ],
    ),
]


# Palabras y carteles de viaje (Japón en abril). NO entran en el temario del sensei
# (`unidades_kanji` solo mira _CATEGORIAS): solo en la página de kanjis y su práctica.
# Compuestos: on "—", kun = lectura entera en hiragana, trazos = solo los de los kanji.
_CATEGORIAS_VIAJE = [
    (
        "viaje_estacion", "Kanjis de viaje — Estación y transporte",
        "moverte en tren y metro: salidas, andenes, billetes y tipos de tren",
        [],
        [
            ("出口", "salida", "—", "でぐち", 8, "—", "出口は どこですか", "salida-TEMA / ¿dónde-está?",
             "出 (salir) + 口 (boca): la boca por la que sales", "出口 でぐち salida · 東口 ひがしぐち salida este · 非常口 ひじょうぐち salida de emergencia"),
            ("入口", "entrada", "—", "いりぐち", 5, "—", "入口は あちらです", "entrada-TEMA / por-allí-es",
             "入 (entrar) + 口 (boca): la boca que te traga hacia dentro", "入口 いりぐち entrada · 入場 にゅうじょう entrar al recinto"),
            ("改札", "puerta de validación", "—", "かいさつ", 12, "—", "改札を 出ます", "puerta-de-validación-OBJ / salgo",
             "改 (cambiar) + 札 (ficha): ahí cambias tu billete por pasar al andén", "改札口 かいさつぐち zona de torniquetes · 北改札 きたかいさつ torniquetes norte"),
            ("乗り場", "andén / parada (de subida)", "—", "のりば", 21, "—", "バスの 乗り場は どこですか", "bus-DE / parada-TEMA / ¿dónde-está?",
             "乗 (subir) + り + 場 (lugar): el sitio donde te subes", "乗る のる subir (a un vehículo) · 乗り場 のりば andén/parada · 場所 ばしょ lugar"),
            ("乗り換え", "transbordo", "—", "のりかえ", 21, "—", "新宿で 乗り換えます", "Shinjuku-EN / hago-transbordo",
             "乗 (subir) + 換 (cambiar): subirte a otro; el cartel de los pasillos entre líneas", "乗り換え のりかえ transbordo · 乗換案内 のりかえあんない guía de transbordos"),
            ("切符", "billete", "—", "きっぷ", 15, "—", "切符を 買います", "billete-OBJ / compro",
             "切 (cortar) + 符 (ficha): el trozo de papel que te cortan y te permite pasar", "切符 きっぷ billete · 切符売り場 きっぷうりば taquilla · 切手 きって sello"),
            ("券売機", "máquina expendedora de billetes", "—", "けんばいき", 31, "—", "券売機で 切符を 買います", "máquina-EN / billete-OBJ / compro",
             "券 (billete) + 売 (vender) + 機 (máquina): la máquina que vende billetes", "券 けん billete/ticket · 売る うる vender · 機械 きかい máquina"),
            ("特急", "tren exprés limitado", "—", "とっきゅう", 19, "—", "特急に 乗ります", "exprés-A / me-subo",
             "特 (especial) + 急 (prisa): el tren especial con prisa que no para en todas", "特急 とっきゅう exprés · 急行 きゅうこう expreso · 急ぐ いそぐ darse prisa"),
            ("普通", "tren local / ordinario", "—", "ふつう", 22, "—", "普通は 駅ごとに 止まります", "local-TEMA / estación-cada / para",
             "普 (general) + 通 (pasar): el tren corriente que pasa por todas las estaciones", "普通 ふつう normal · 普通列車 ふつうれっしゃ tren local"),
            ("新幹線", "tren bala", "—", "しんかんせん", 41, "—", "新幹線で 京都へ 行きます", "tren-bala-EN / Kioto-A / voy",
             "新 (nuevo) + 幹 (tronco) + 線 (línea): la línea nueva y principal, el tronco del país", "新幹線 しんかんせん tren bala · 新宿 しんじゅく Shinjuku · 山手線 やまのてせん línea Yamanote"),
            ("番線", "número de andén", "—", "ばんせん", 27, "—", "三番線から でます", "andén-3-DESDE / sale",
             "番 (número) + 線 (línea): el número de la vía; 3番線 さんばんせん", "一番線 いちばんせん andén 1 · 番号 ばんごう número"),
            ("行き", "con destino a", "—", "ゆき", 6, "—", "東京行きの 電車です", "Tokio-destino-DE / tren-es",
             "行 (ir) + き: 'que va a'; el destino se pone delante: 東京行き", "東京行き とうきょうゆき con destino a Tokio · 行く いく ir"),
            ("終電", "último tren", "—", "しゅうでん", 24, "—", "終電に まにあいました", "último-tren-A / llegué-a-tiempo",
             "終 (fin) + 電 (tren eléctrico): el tren del final de la noche", "終電 しゅうでん último tren · 終点 しゅうてん última parada · 始発 しはつ primer tren"),
            ("時刻表", "horario de trenes", "—", "じこくひょう", 26, "—", "時刻表を 見ます", "horario-OBJ / miro",
             "時 (hora) + 刻 (grabar) + 表 (tabla): la tabla con las horas grabadas", "時刻 じこく hora · 時刻表 じこくひょう horario · 表 ひょう tabla"),
            ("地下鉄", "metro", "—", "ちかてつ", 22, "—", "地下鉄で 行きましょう", "metro-EN / vayamos",
             "地 (tierra) + 下 (debajo) + 鉄 (hierro): el hierro que corre bajo tierra", "地下鉄 ちかてつ metro · 地下 ちか sótano · 鉄道 てつどう ferrocarril"),
            ("精算", "ajuste de tarifa", "—", "せいさん", 28, "—", "精算機で お金を 払います", "máquina-de-ajuste-EN / dinero-OBJ / pago",
             "精 (preciso) + 算 (calcular): calcular al detalle lo que falta si pasaste de estación", "精算機 せいさんき máquina de ajuste · 計算 けいさん cálculo"),
            ("指定席", "asiento reservado", "—", "していせき", 27, "—", "指定席を お願いします", "asiento-reservado-OBJ / por-favor",
             "指 (señalar) + 定 (fijar) + 席 (asiento): el asiento que te señalan y queda fijado", "指定席 していせき reservado · 自由席 じゆうせき no reservado · 席 せき asiento"),
            ("自由席", "asiento libre (sin reserva)", "—", "じゆうせき", 21, "—", "自由席は 何号車ですか", "asiento-libre-TEMA / ¿qué-vagón-es?",
             "自 (uno mismo) + 由 (razón) + 席 (asiento): te sientas donde tú quieras", "自由 じゆう libre · 自由席 じゆうせき no reservado"),
            ("優先席", "asiento preferente", "—", "ゆうせんせき", 33, "—", "優先席に 座りません", "asiento-preferente-EN / no-me-siento",
             "優 (amable) + 先 (primero) + 席 (asiento): el asiento amable que se cede primero a quien lo necesita", "優先席 ゆうせんせき asiento preferente · 優しい やさしい amable"),
            ("空港", "aeropuerto", "—", "くうこう", 20, "—", "空港まで 電車で 行きます", "aeropuerto-HASTA / tren-EN / voy",
             "空 (cielo) + 港 (puerto): el puerto del cielo", "空港 くうこう aeropuerto · 港 みなと puerto"),
        ],
    ),
    (
        "viaje_tiendas", "Kanjis de viaje — Tiendas y precios",
        "entender los carteles de tienda, las etiquetas de precio y qué estás pagando",
        [],
        [
            ("営業中", "abierto (en horario)", "—", "えいぎょうちゅう", 29, "—", "この 店は 営業中です", "esta / tienda-TEMA / abierta-es",
             "営 (gestionar) + 業 (negocio) + 中 (en curso): el negocio está funcionando ahora", "営業中 えいぎょうちゅう abierto · 営業時間 えいぎょうじかん horario"),
            ("準備中", "cerrado (preparando)", "—", "じゅんびちゅう", 29, "—", "まだ 準備中です", "todavía / en-preparación-es",
             "準 (preparar) + 備 (disponer) + 中 (en curso): aún están poniendo la tienda a punto, así que no abre", "準備中 じゅんびちゅう preparando · 準備 じゅんび preparativo"),
            ("定休日", "día de cierre semanal", "—", "ていきゅうび", 18, "—", "定休日は 水曜日です", "día-de-cierre-TEMA / miércoles-es",
             "定 (fijo) + 休 (descanso) + 日 (día): el día de descanso que siempre es el mismo", "定休日 ていきゅうび día de cierre · 年中無休 ねんじゅうむきゅう abierto todo el año"),
            ("本日休業", "hoy cerrado", "—", "ほんじつきゅうぎょう", 28, "—", "本日休業の はりがみ", "hoy-cerrado-DE / cartel",
             "本日 (hoy, formal) + 休業 (negocio en descanso): cartel de persiana bajada", "本日 ほんじつ hoy · 休業 きゅうぎょう cierre temporal"),
            ("営業時間", "horario comercial", "—", "えいぎょうじかん", 47, "—", "営業時間は 何時から ですか", "horario-TEMA / ¿desde-qué-hora-es?",
             "営業 (negocio) + 時間 (tiempo): el tiempo en que el negocio está abierto", "営業 えいぎょう negocio · 時間 じかん tiempo"),
            ("税込", "IVA incluido", "—", "ぜいこみ", 17, "—", "税込で 千円です", "con-impuestos / 1000-yenes-es",
             "税 (impuesto) + 込 (meter dentro): el impuesto ya está metido en el precio", "税込 ぜいこみ IVA incluido · 税抜 ぜいぬき sin IVA · 消費税 しょうひぜい impuesto al consumo"),
            ("割引", "descuento", "—", "わりびき", 16, "—", "割引は ありますか", "descuento-TEMA / ¿hay?",
             "割 (partir) + 引 (tirar): del precio se parte un trozo y se tira hacia abajo", "割引 わりびき descuento · 二割引 にわりびき 20% de descuento"),
            ("半額", "mitad de precio", "—", "はんがく", 23, "—", "全部 半額です", "todo / mitad-de-precio-es",
             "半 (mitad) + 額 (importe): el importe partido por la mitad", "半額 はんがく mitad de precio · 金額 きんがく importe"),
            ("特売", "oferta especial", "—", "とくばい", 17, "—", "今日は 特売です", "hoy-TEMA / oferta-es",
             "特 (especial) + 売 (vender): venta especial, el cartel rojo de los súpers", "特売 とくばい oferta · 特急 とっきゅう exprés"),
            ("無料", "gratis", "—", "むりょう", 22, "—", "この 水は 無料です", "esta / agua-TEMA / gratis-es",
             "無 (sin) + 料 (tarifa): sin tarifa, no pagas", "無料 むりょう gratis · 料金 りょうきん tarifa"),
            ("有料", "de pago", "—", "ゆうりょう", 16, "—", "ここは 有料です", "aquí-TEMA / de-pago-es",
             "有 (tener) + 料 (tarifa): tiene tarifa; es el opuesto de 無料", "有料 ゆうりょう de pago · 有料道路 ゆうりょうどうろ autopista de peaje"),
            ("現金", "efectivo", "—", "げんきん", 19, "—", "現金だけ です", "efectivo-solo / es",
             "現 (presente) + 金 (dinero): el dinero que tienes a mano ahora", "現金 げんきん efectivo · 現在 げんざい ahora"),
            ("両替", "cambio de divisas", "—", "りょうがえ", 18, "—", "両替は どこですか", "cambio-de-divisas-TEMA / ¿dónde-está?",
             "両 (los dos) + 替 (reemplazar): cambias una moneda por la otra, de dos en dos", "両替 りょうがえ cambio de divisas · 両替所 りょうがえじょ casa de cambio"),
            ("免税", "libre de impuestos", "—", "めんぜい", 20, "—", "免税の カウンターは どこですか", "libre-de-impuestos-DE / mostrador-TEMA / ¿dónde-está?",
             "免 (eximir) + 税 (impuesto): te libras del impuesto, el cartel Tax-free para turistas", "免税 めんぜい libre de impuestos · 免税店 めんぜいてん tienda tax-free"),
            ("会計", "caja / la cuenta", "—", "かいけい", 15, "—", "お会計を お願いします", "la-cuenta-OBJ / por-favor",
             "会 (reunir) + 計 (contar): se reúne y se cuenta todo lo consumido", "会計 かいけい caja · お会計 おかいけい la cuenta · 計算 けいさん cálculo"),
            ("入場料", "precio de entrada", "—", "にゅうじょうりょう", 24, "—", "入場料は 五百円です", "precio-de-entrada-TEMA / 500-yenes-es",
             "入 (entrar) + 場 (lugar) + 料 (tarifa): lo que pagas por entrar al sitio; en templos, museos y jardines", "入場料 にゅうじょうりょう entrada · 入場 にゅうじょう acceso · 入場無料 entrada gratis"),
            ("売り切れ", "agotado", "—", "うりきれ", 11, "—", "すみません、売り切れです", "perdone / agotado-es",
             "売る (vender) + 切れる (cortarse): se vendió hasta que se cortó, ya no queda", "売り切れ うりきれ agotado · 完売 かんばい todo vendido"),
            ("予約", "reserva", "—", "よやく", 13, "—", "予約して いません", "reserva-haciendo / no-estoy",
             "予 (antes) + 約 (promesa): una promesa hecha antes de llegar", "予約 よやく reserva · 予約席 よやくせき mesa reservada · 予約制 solo con reserva"),
        ],
    ),
    (
        "viaje_comida", "Kanjis de viaje — Comida y menús",
        "pedir y leer una carta o un cartel de restaurante sin tener foto",
        [],
        [
            ("定食", "menú del día / set", "—", "ていしょく", 17, "—", "焼き魚定食を ください", "pescado-a-la-plancha-menú / por-favor",
             "定 (fijo) + 食 (comida): comida fija, ya viene con arroz, sopa y encurtidos", "定食 ていしょく menú · 定食屋 ていしょくや restaurante de menús"),
            ("丼", "bol de arroz con encima", "トン・ドン", "どんぶり", 5, "丶 (てん)", "牛丼を ください", "bol-de-ternera / por-favor",
             "un pozo (井) con una gota (丶) cayendo dentro: el cuenco hondo donde cae la comida sobre el arroz", "牛丼 ぎゅうどん bol de ternera · 親子丼 おやこどん bol de pollo y huevo · 天丼 てんどん bol de tempura"),
            ("大盛り", "ración grande", "—", "おおもり", 14, "—", "大盛りに できますか", "ración-grande-A / ¿se-puede?",
             "大 (grande) + 盛 (colmar): se llena el plato hasta arriba", "大盛り おおもり ración grande · 特盛 とくもり ración extra · 並盛 なみもり ración normal"),
            ("食べ放題", "todo lo que puedas comer", "—", "たべほうだい", 35, "—", "食べ放題は 九十分です", "buffet-libre-TEMA / 90-minutos-es",
             "食べ (comer) + 放題 (a discreción): sueltas el apetito sin límite", "食べ放題 たべほうだい buffet libre · 食べる たべる comer · 放題 ほうだい a discreción"),
            ("飲み放題", "barra libre", "—", "のみほうだい", 38, "—", "飲み放題を つけます", "barra-libre-OBJ / añado",
             "飲み (beber) + 放題 (a discreción): bebes sin límite durante un tiempo", "飲み放題 のみほうだい barra libre · 飲む のむ beber"),
            ("生ビール", "cerveza de barril", "—", "なまビール", 5, "—", "生ビールを 二つ ください", "cerveza-de-barril-OBJ / dos / por-favor",
             "生 (crudo/fresco) + ビール: cerveza sin pasteurizar, recién sacada del barril", "生ビール なまビール cerveza de barril · 生 なま crudo · 生卵 なまたまご huevo crudo"),
            ("焼肉", "carne a la parrilla", "—", "やきにく", 18, "—", "焼肉を 食べに 行きましょう", "carne-a-la-parrilla-OBJ / comer-a / vayamos",
             "焼 (asar) + 肉 (carne): carne asada ante tus ojos en la mesa", "焼肉 やきにく carne a la parrilla · 焼き鳥 やきとり brocheta de pollo"),
            ("刺身", "sashimi", "—", "さしみ", 15, "—", "刺身は 好きですか", "sashimi-TEMA / ¿te-gusta?",
             "刺 (pinchar) + 身 (carne): el pescado se pincha en la bandeja como carne cruda", "刺身 さしみ sashimi · 刺身定食 さしみていしょく menú de sashimi"),
            ("寿司", "sushi", "—", "すし", 12, "—", "寿司を 食べます", "sushi-OBJ / como",
             "寿 (larga vida) + 司 (encargado): ¡brindis por la larga vida del que te prepara el sushi!", "寿司 すし sushi · 回転寿司 かいてんずし sushi sobre cinta · 寿司屋 すしや sushería"),
            ("弁当", "bento (caja de comida)", "—", "べんとう", 11, "—", "お弁当を 買います", "bento-OBJ / compro",
             "弁 (dividir) + 当 (corresponder): la caja con cada cosa en su compartimento", "弁当 べんとう bento · 駅弁 えきべん bento de estación"),
            ("蕎麦", "soba (fideos de trigo sarraceno)", "—", "そば", 22, "—", "冷たい お蕎麦を ください", "fría / soba-OBJ / por-favor",
             "蕎 (hierba) + 麦 (trigo): la planta con la que se hace el fideo oscuro", "蕎麦 そば soba · 蕎麦屋 そばや restaurante de soba · 小麦 こむぎ trigo"),
            ("辛口", "picante / seco", "—", "からくち", 10, "—", "辛口に して ください", "picante-A / hazlo / por-favor",
             "辛 (picante) + 口 (boca): el que pica en la boca; también el sake o el vino secos", "辛口 からくち picante/seco · 辛い からい picante · 甘口 あまくち dulce/suave"),
            ("持ち帰り", "para llevar", "—", "もちかえり", 19, "—", "持ち帰りで お願いします", "para-llevar-CON / por-favor",
             "持 (llevar en la mano) + 帰 (volver): lo coges y te lo llevas a casa", "持ち帰り もちかえり para llevar · 持つ もつ llevar/tener · 帰る かえる volver"),
            ("店内", "dentro del local", "—", "てんない", 12, "—", "店内で 食べます", "dentro-del-local-EN / como",
             "店 (tienda) + 内 (dentro): para comer dentro; la pregunta típica es 店内ですか", "店内 てんない dentro del local · 案内 あんない guía"),
            ("日替わり", "plato del día", "—", "ひがわり", 16, "—", "日替わりランチを ください", "plato-del-día-almuerzo-OBJ / por-favor",
             "日 (día) + 替 (cambiar): el que cambia cada día", "日替わり ひがわり del día · 両替 りょうがえ cambio"),
        ],
    ),
    (
        "viaje_carteles", "Kanjis de viaje — Carteles y avisos",
        "entender qué se puede y qué no se puede hacer: prohibiciones, peligros y avisos de uso",
        [],
        [
            ("禁止", "prohibido", "—", "きんし", 17, "—", "ここは 撮影禁止です", "aquí-TEMA / fotos-prohibidas-es",
             "禁 (vedar) + 止 (parar): vedado, así que detente", "禁止 きんし prohibido · 駐車禁止 ちゅうしゃきんし prohibido aparcar"),
            ("禁煙", "prohibido fumar", "—", "きんえん", 26, "—", "ここは 禁煙です", "aquí-TEMA / prohibido-fumar-es",
             "禁 (vedar) + 煙 (humo): el humo vedado", "禁煙 きんえん no fumar · 禁煙席 きんえんせき zona de no fumadores"),
            ("喫煙所", "zona de fumadores", "—", "きつえんじょ", 33, "—", "喫煙所は どこですか", "zona-de-fumadores-TEMA / ¿dónde-está?",
             "喫 (consumir) + 煙 (humo) + 所 (lugar): el único sitio donde consumes humo", "喫煙 きつえん fumar · 喫茶店 きっさてん cafetería"),
            ("立入禁止", "prohibido el paso", "—", "たちいりきんし", 24, "—", "ここは 立入禁止です", "aquí-TEMA / prohibido-el-paso-es",
             "立入 (ponerse de pie dentro) + 禁止 (prohibido): ni pongas el pie dentro", "立入禁止 たちいりきんし prohibido el paso · 立つ たつ ponerse de pie"),
            ("撮影禁止", "prohibido fotografiar", "—", "さつえいきんし", 47, "—", "撮影禁止の 美術館です", "fotos-prohibidas-DE / museo-es",
             "撮影 (hacer fotos) + 禁止 (prohibido): cámara guardada", "撮影 さつえい fotografiar · 撮影禁止 さつえいきんし no fotos"),
            ("駐車禁止", "prohibido aparcar", "—", "ちゅうしゃきんし", 39, "—", "ここは 駐車禁止です", "aquí-TEMA / prohibido-aparcar-es",
             "駐車 (aparcar) + 禁止 (prohibido): cartel de calle para el coche", "駐車 ちゅうしゃ aparcar · 駐車場 ちゅうしゃじょう aparcamiento"),
            ("危険", "peligro", "—", "きけん", 17, "—", "危険ですから 入らないで ください", "peligro-porque / no-entres / por-favor",
             "危 (arriesgado) + 険 (escarpado): un risco escarpado, peligro de caer", "危険 きけん peligro · 危ない あぶない peligroso"),
            ("注意", "atención / cuidado", "—", "ちゅうい", 21, "—", "足元に ご注意ください", "a-los-pies / atención-por-favor",
             "注 (verter) + 意 (mente): vierte tu mente en el entorno, ¡fíjate!", "注意 ちゅうい atención · 足元注意 あしもとちゅうい cuidado con el escalón"),
            ("使用中", "en uso / ocupado", "—", "しようちゅう", 17, "—", "ただいま 使用中です", "ahora-mismo / en-uso-es",
             "使 (usar) + 用 (utilidad) + 中 (en curso): se está usando ahora", "使用中 しようちゅう en uso · 使う つかう usar"),
            ("故障中", "averiado", "—", "こしょうちゅう", 27, "—", "この 機械は 故障中です", "esta / máquina-TEMA / averiada-está",
             "故 (causa) + 障 (obstáculo) + 中 (en curso): hay un obstáculo en la máquina, no funciona", "故障 こしょう avería · 故障中 こしょうちゅう averiado"),
            ("工事中", "en obras", "—", "こうじちゅう", 15, "—", "この 道は 工事中です", "este / camino-TEMA / en-obras-está",
             "工 (obra) + 事 (asunto) + 中 (en curso): obras en curso", "工事 こうじ obras · 工事中 こうじちゅう en obras"),
            ("満員", "completo (lleno)", "—", "まんいん", 22, "—", "電車は 満員です", "tren-TEMA / lleno-está",
             "満 (lleno) + 員 (miembro): ni un miembro más cabe", "満員 まんいん lleno · 満席 まんせき sin mesas libres"),
        ],
    ),
    (
        "viaje_banos", "Kanjis de viaje — Baños, puertas y salidas",
        "no equivocarte de puerta ni de baño, y encontrar la salida de emergencia",
        [],
        [
            ("お手洗い", "aseos", "—", "おてあらい", 13, "—", "お手洗いは どこですか", "aseos-TEMA / ¿dónde-está?",
             "お + 手 (mano) + 洗い (lavar): el sitio donde te lavas las manos, forma educada de decir baño", "お手洗い おてあらい aseos · 手洗い てあらい lavarse las manos · 洗う あらう lavar"),
            ("化粧室", "aseo / tocador", "—", "けしょうしつ", 25, "—", "化粧室は 二階です", "aseo-TEMA / primer-piso-es",
             "化粧 (maquillaje) + 室 (sala): la sala donde te arreglas y maquillas; palabra elegante para baño", "化粧室 けしょうしつ tocador · 化粧 けしょう maquillaje · 教室 きょうしつ aula"),
            ("男性", "hombres", "—", "だんせい", 15, "—", "男性用 トイレは こちらです", "para-hombres / baño-TEMA / por-aquí-es",
             "男 (hombre) + 性 (género): lado de los hombres; el cartel azul", "男性 だんせい hombre · 男子 だんし chico"),
            ("女性", "mujeres", "—", "じょせい", 11, "—", "女性用 トイレは あちらです", "para-mujeres / baño-TEMA / por-allí-es",
             "女 (mujer) + 性 (género): lado de las mujeres; el cartel rojo", "女性 じょせい mujer · 女子 じょし chica"),
            ("押", "empujar", "オウ", "お(す)", 8, "手 (てへん)", "ドアを 押して ください", "puerta-OBJ / empuja / por-favor",
             "una mano (扌) con un trazo que se mete en la caja (甲): empujas la hoja de la puerta", "押す おす empujar · 押し入れ おしいれ armario empotrado"),
            ("引", "tirar", "イン", "ひ(く)", 4, "弓 (ゆみ)", "ドアを 引いて ください", "puerta-OBJ / tira / por-favor",
             "un arco (弓) con la cuerda tensada hacia atrás (丨): tiras hacia ti", "引く ひく tirar · 引っ越し ひっこし mudanza · 割引 わりびき descuento"),
            ("開", "abrir", "カイ", "あ(く)・ひら(く)", 12, "門 (もんがまえ)", "ドアが 開きます", "puerta-SUJ / se-abre",
             "las dos hojas de un portón (門) con un cerrojo (幵) que se quita: se abre", "開く あく abrirse · 開店 かいてん abrir la tienda · 開ける あける abrir"),
            ("閉", "cerrar", "ヘイ", "し(まる)・と(じる)", 11, "門 (もんがまえ)", "ドアが 閉まります", "puerta-SUJ / se-cierra",
             "un portón (門) con una tranca (才) cruzada: queda cerrado", "閉まる しまる cerrarse · 閉店 へいてん cerrar la tienda · 閉める しめる cerrar"),
            ("自動", "automático", "—", "じどう", 17, "—", "自動ドアです", "automática-puerta-es",
             "自 (uno mismo) + 動 (moverse): se mueve ella sola; 自動ドア, 自動販売機", "自動 じどう automático · 自動販売機 じどうはんばいき máquina expendedora"),
            ("非常口", "salida de emergencia", "—", "ひじょうぐち", 22, "—", "非常口は あちらです", "salida-de-emergencia-TEMA / por-allí-es",
             "非 (no) + 常 (normal) + 口 (boca): la salida para lo que no es normal", "非常口 ひじょうぐち salida de emergencia · 非常 ひじょう emergencia"),
        ],
    ),
    (
        "viaje_ciudad", "Kanjis de viaje — Ciudad y direcciones",
        "orientarte por la ciudad: servicios, calles, mapas y sitios que quieres visitar",
        [],
        [
            ("駐車場", "aparcamiento", "—", "ちゅうしゃじょう", 34, "—", "駐車場は ありますか", "aparcamiento-TEMA / ¿hay?",
             "駐 (detenerse) + 車 (coche) + 場 (lugar): el lugar donde el coche se detiene", "駐車場 ちゅうしゃじょう aparcamiento · 会場 かいじょう recinto"),
            ("案内所", "oficina de información", "—", "あんないじょ", 22, "—", "案内所で 地図を もらいます", "oficina-de-información-EN / mapa-OBJ / recibo",
             "案 (plan) + 内 (dentro) + 所 (lugar): el sitio donde te guían por dentro de la ciudad", "案内所 あんないじょ información · 案内 あんない guía"),
            ("観光", "turismo", "—", "かんこう", 24, "—", "観光に 来ました", "turismo-A / he-venido",
             "観 (contemplar) + 光 (luz): ir a contemplar la luz, es decir las vistas", "観光 かんこう turismo · 観光地 かんこうち zona turística"),
            ("交番", "puesto de policía", "—", "こうばん", 18, "—", "交番は どこですか", "puesto-de-policía-TEMA / ¿dónde-está?",
             "交 (cruzar) + 番 (turno): la caseta donde se turnan los agentes en el cruce", "交番 こうばん puesto de policía · 交差点 こうさてん cruce"),
            ("病院", "hospital", "—", "びょういん", 20, "—", "病院へ 行きたいです", "hospital-A / quiero-ir",
             "病 (enfermedad) + 院 (institución): el centro de las enfermedades", "病院 びょういん hospital · 病気 びょうき enfermedad"),
            ("薬局", "farmacia", "—", "やっきょく", 23, "—", "薬局は あそこです", "farmacia-TEMA / allí-es",
             "薬 (medicina) + 局 (oficina): la oficina de las medicinas", "薬局 やっきょく farmacia · 薬 くすり medicina"),
            ("郵便局", "oficina de correos", "—", "ゆうびんきょく", 27, "—", "郵便局は どこですか", "correos-TEMA / ¿dónde-está?",
             "郵 (correo) + 便 (servicio) + 局 (oficina): la oficina del servicio de correo", "郵便局 ゆうびんきょく correos · 郵便 ゆうびん correo"),
            ("信号", "semáforo", "—", "しんごう", 14, "—", "信号を 右に 曲がります", "semáforo-OBJ / derecha-A / giro",
             "信 (fe) + 号 (señal): señal en la que se confía para cruzar", "信号 しんごう semáforo · 番号 ばんごう número"),
            ("横断歩道", "paso de cebra", "—", "おうだんほどう", 46, "—", "横断歩道を わたります", "paso-de-cebra-OBJ / cruzo",
             "横断 (atravesar) + 歩道 (acera): la acera que cruza la calzada", "横断 おうだん cruzar · 歩道 ほどう acera · 歩く あるく caminar"),
            ("交差点", "cruce", "—", "こうさてん", 25, "—", "次の 交差点を 左へ", "siguiente / cruce-OBJ / izquierda-A",
             "交 (cruzar) + 差 (diferencia) + 点 (punto): el punto donde dos calles se cruzan", "交差点 こうさてん cruce · 点 てん punto"),
            ("一方通行", "dirección única", "—", "いっぽうつうこう", 21, "—", "この 道は 一方通行です", "esta / calle-TEMA / dirección-única-es",
             "一方 (una dirección) + 通行 (circulación): el tráfico solo va en un sentido", "一方通行 いっぽうつうこう dirección única · 通行止め つうこうどめ cortado al tráfico"),
            ("荷物", "equipaje", "—", "にもつ", 18, "—", "荷物を あずけたいです", "equipaje-OBJ / quiero-dejar",
             "荷 (carga) + 物 (cosa): las cosas que cargas, tu maleta", "荷物 にもつ equipaje · 手荷物 てにもつ equipaje de mano · 荷物預かり所 にもつあずかりじょ consigna"),
            ("温泉", "onsen (aguas termales)", "—", "おんせん", 21, "—", "温泉に 入りたいです", "onsen-A / quiero-entrar",
             "温 (cálido) + 泉 (manantial): el manantial caliente", "温泉 おんせん onsen · 温かい あたたかい cálido"),
            ("神社", "santuario sintoísta", "—", "じんじゃ", 16, "—", "神社へ お参りに 行きます", "santuario-A / visita-A / voy",
             "神 (dios) + 社 (santuario): la casa del dios", "神社 じんじゃ santuario · 会社 かいしゃ empresa"),
            ("寺", "templo budista", "ジ", "てら", 6, "寸 (すん)", "お寺に 行きましょう", "templo-A / vayamos",
             "tierra (土) y una mano que mide (寸): el lugar de la tierra medida y recogida; lo ves en nombres como 清水寺", "お寺 おてら templo · 清水寺 きよみずでら templo Kiyomizu · 時 じ hora"),
            ("公園", "parque", "—", "こうえん", 17, "—", "公園で 休みます", "parque-EN / descanso",
             "公 (público) + 園 (jardín): el jardín de todos", "公園 こうえん parque · 動物園 どうぶつえん zoo"),
            ("地図", "mapa", "—", "ちず", 13, "—", "地図を 見せて ください", "mapa-OBJ / enseña / por-favor",
             "地 (tierra) + 図 (dibujo): el dibujo de la tierra", "地図 ちず mapa · 地下 ちか subterráneo"),
            ("現在地", "usted está aquí", "—", "げんざいち", 23, "—", "現在地は ここです", "usted-está-aquí-TEMA / aquí-es",
             "現在 (ahora) + 地 (lugar): el lugar en el que estás ahora, el punto del mapa", "現在地 げんざいち usted está aquí · 現在 げんざい ahora"),
            ("受付", "recepción", "—", "うけつけ", 13, "—", "受付は 一階です", "recepción-TEMA / planta-1-es",
             "受 (recibir) + 付 (pegar): donde te reciben y te apuntan; en hoteles, hospitales y museos", "受付 うけつけ recepción · 受付時間 horario de recepción"),
            ("階", "planta / piso", "カイ・ガイ", "—", 12, "阝 (こざとへん)", "トイレは 二階です", "baño-TEMA / planta-2-es",
             "una colina (阝) con escalones que suben todos (皆) a la vez: los pisos de un edificio", "一階 いっかい planta baja · 三階 さんがい 3.ª planta (¡がい!) · 地下一階 sótano 1"),
        ],
    ),
]


def _kata_a_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


# la on de 4 y 7 (し, しち) casi nunca se usa al contar: chocan con 死/一
_READING_CARD = {"四": "よん", "七": "なな", "九": "きゅう", "生ビール": "なまビール"}

# kanji que en la card se reconocen por su ON aunque tengan kun: números, y los
# que en la práctica solo viven en compuestos (時 じ, 語 ご, 社 しゃ...). El resto
# muestra su kun, que es como se lee el carácter suelto (山 やま, no さん).
_ON_CARD = set("一二三四五六七八九十千円時分半語社年天本生先学文字")


def _card_reading(jp, on, kun):
    if jp in _READING_CARD:
        return _READING_CARD[jp]
    base = on if (jp in _ON_CARD or kun == "—") else kun
    if base == "—":
        base = on
    return _kata_a_hira(base).split("・")[0].replace("(", "").replace(")", "")


def _item(t):
    """Tupla de datos → ítem del temario (kind vocabulario, tipo kanji)."""
    jp, sig, on, kun, trazos, radical, ejemplo, literal, mnemo, vocab = t
    lect = " · ".join(p for p in (f"on {on}" if on != "—" else "",
                                  f"kun {kun}" if kun != "—" else "") if p)
    return {
        "kind": "vocabulario", "tipo": "kanji", "jp": jp,
        "reading": (kun if kun != "—" else on).split("・")[0].replace("(", "").replace(")", ""),
        "reading_card": _card_reading(jp, on, kun),
        "meaning": f"{sig} (kanji)",
        "ejemplo": ejemplo, "literal": literal,
        "uso": f"{lect} · {trazos} trazos · radical {radical}. {mnemo}. Aparece en: {vocab}",
        # campos crudos por si algún día la cara dibuja una ficha de kanji
        "on": on, "kun": kun, "trazos": trazos, "radical": radical,
        "mnemo": mnemo, "vocab_ejemplo": vocab,
    }


KANJI_N5 = [
    dict(_item(t), categoria=uid, categoria_nombre=nombre)
    for uid, nombre, _funcion, _frases, tuplas in _CATEGORIAS + _CATEGORIAS_VIAJE for t in tuplas
]
_N_N5 = sum(len(c[4]) for c in _CATEGORIAS)


def unidades_kanji(ya_en_temario=frozenset(), prerequisito=None, umbral=0.75):
    """Las unidades temáticas de kanji, encadenadas por prerrequisito.

    `ya_en_temario` son los `jp` que otra unidad ya enseña (一〜千 viven en la
    unidad de números): se filtran para que el SRS no lleve dos fichas del
    mismo carácter. Las unidades que se quedan vacías desaparecen.
    """
    unidades = []
    anterior = prerequisito
    for uid, nombre, funcion, frases, tuplas in _CATEGORIAS:
        items = [_item(t) for t in tuplas if t[0] not in ya_en_temario]
        if not items:
            continue
        unidades.append({
            "id": uid, "nombre": nombre, "funcion": funcion,
            "frases_hechas": frases, "prerequisito": anterior,
            "umbral_prereq": umbral, "items": items,
        })
        anterior = uid
    return unidades


if __name__ == "__main__":
    # 108 kanji sueltos + los 7 días de la semana como palabra (月曜日〜日曜日)
    n5, viaje = KANJI_N5[:_N_N5], KANJI_N5[_N_N5:]
    assert len(n5) == 115, len(n5)
    for k in n5:
        assert 1 <= len(k["jp"]) <= 3 and all("一" <= c <= "鿿" for c in k["jp"]), k["jp"]
        assert k["reading"] and k["ejemplo"] and k["literal"] and k["mnemo"], k["jp"]
        assert 1 <= k["trazos"] <= 20 * len(k["jp"]), k

    us = unidades_kanji()
    assert len(us) == 11 and sum(len(u["items"]) for u in us) == 115
    assert us[0]["prerequisito"] is None

    # viaje: fuera del sensei, jp únicos en todo KANJI_N5, kana permitido
    assert len(viaje) >= 60, len(viaje)
    assert len({k["jp"] for k in KANJI_N5}) == len(KANJI_N5), "jp repetido"
    en_sensei = {i["jp"] for u in us for i in u["items"]}
    for k in viaje:
        assert k["categoria"].startswith("viaje_") and k["jp"] not in en_sensei, k["jp"]
        assert 1 <= len(k["jp"]) <= 6, k["jp"]
        assert k["reading"] and k["reading_card"] and k["ejemplo"] and k["literal"] and k["mnemo"] and k["vocab_ejemplo"], k["jp"]
        assert 1 <= k["trazos"] <= 20 * len(k["jp"]), k
    assert not any(u["id"].startswith("viaje_") for u in us)
    print("OK", len(n5), len(viaje))
