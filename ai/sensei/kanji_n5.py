"""Los 103 kanji del JLPT N5, en formato de ítem del temario.

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
             "un solo trazo, un solo dedo", "一人 ひとり una persona · 一日 ついたち el día 1"),
            ("二", "dos", "ニ", "ふた(つ)", 2, "二 (に)", "二つ あります", "dos / hay",
             "dos trazos, dos palillos", "二人 ふたり dos personas · 二月 にがつ febrero"),
            ("三", "tres", "サン", "み(っつ)", 3, "一 (いち)", "三つ ください", "tres / por-favor",
             "tres trazos; la serie 一二三 se acaba aquí", "三人 さんにん tres personas · 三日 みっか el día 3"),
            ("四", "cuatro", "シ", "よ・よん・よっ(つ)", 5, "囗 (くにがまえ)", "四時に あいましょう", "4h-A / quedemos",
             "una caja con las piernas dentro: deja de contar trazos aquí", "四時 よじ las 4 · 四月 しがつ abril"),
            ("五", "cinco", "ゴ", "いつ(つ)", 4, "二 (に)", "五百円です", "500-yenes-es",
             "una mano abierta estilizada entre dos líneas", "五時 ごじ las 5 · 五日 いつか el día 5"),
            ("六", "seis", "ロク", "むっ(つ)", 4, "八 (はち)", "六時に おきます", "6h-A / me-levanto",
             "un tejadillo con dos patas", "六月 ろくがつ junio · 六つ むっつ seis"),
            ("七", "siete", "シチ", "なな(つ)", 2, "一 (いち)", "今 七時です", "ahora / 7h-es",
             "un 十 torcido: el siete se cae hacia la derecha", "七月 しちがつ julio · 七つ ななつ siete"),
            ("八", "ocho", "ハチ", "やっ(つ)", 2, "八 (はち)", "八百円 でした", "800-yenes / fue",
             "dos trazos que se abren: el número de la suerte", "八月 はちがつ agosto · 八百屋 やおや verdulería"),
            ("九", "nueve", "キュウ・ク", "ここの(つ)", 2, "乙 (おつ)", "九時に ねます", "9h-A / me-acuesto",
             "casi diez, pero le falta un trozo", "九月 くがつ septiembre (¡く, no きゅう!) · 九つ ここのつ nueve"),
            ("十", "diez", "ジュウ・ジッ", "とお", 2, "十 (じゅう)", "十人 います", "10-personas / hay",
             "una cruz perfecta: la decena", "十月 じゅうがつ octubre · 二十歳 はたち 20 años"),
            ("百", "cien", "ヒャク", "—", 6, "白 (しろ)", "三百円です", "300-yenes-es",
             "un 一 encima de 白: 'uno' delante del blanco", "百 ひゃく cien · 三百 さんびゃく 300 (¡suena びゃく!)"),
            ("千", "mil", "セン", "ち", 3, "十 (じゅう)", "千円 ください", "1000-yenes / por-favor",
             "un 十 con flequillo", "千円 せんえん 1000 yenes · 三千 さんぜん 3000 (¡ぜん!)"),
            ("万", "diez mil", "マン・バン", "—", 3, "一 (いち)", "一万円です", "10000-yenes-es",
             "en japonés se cuenta de 万 en 万, no de mil en mil", "一万 いちまん 10.000 · 万年筆 まんねんひつ pluma"),
            ("円", "yen / círculo", "エン", "まる(い)", 4, "冂 (けいがまえ)", "いくらですか。五百円です", "¿cuánto-es? / 500-yenes-es",
             "una moneda vista de canto", "円 えん yen · 百円玉 ひゃくえんだま moneda de 100"),
        ],
    ),
    (
        "kanji_tiempo", "Kanjis N5 — Tiempo y calendario",
        "leer un horario, un calendario y los carteles de apertura de una tienda",
        [
            {"jp": "何曜日ですか", "uso": "'¿qué día de la semana es?'"},
            {"jp": "今日は 何日ですか", "uso": "'¿a qué día del mes estamos?'"},
            {"jp": "時間が ないんです", "uso": "'es que no tengo tiempo'; excusa educada y comodín"},
        ],
        [
            ("日", "día / sol", "ニチ・ジツ", "ひ・か", 4, "日 (ひへん)", "今日は いい 日ですね", "hoy-TEMA / buen / día-es-¿verdad?",
             "un sol con una raya dentro", "日本 にほん Japón · 三日 みっか el día 3 · 日曜日 にちようび domingo"),
            ("月", "mes / luna", "ゲツ・ガツ", "つき", 4, "月 (つきへん)", "月曜日に あいます", "lunes-A / quedamos",
             "una luna en cuarto creciente", "月曜日 げつようび lunes · 一月 いちがつ enero · 今月 こんげつ este mes"),
            ("火", "fuego", "カ", "ひ", 4, "火 (ひ)", "火曜日は やすみです", "martes-TEMA / descanso-es",
             "una hoguera con chispas a los lados", "火曜日 かようび martes · 花火 はなび fuegos artificiales"),
            ("水", "agua", "スイ", "みず", 4, "水 (みず)", "お水を ください", "agua-OBJ / por-favor",
             "un chorro con salpicaduras a los lados", "水 みず agua · 水曜日 すいようび miércoles"),
            ("木", "árbol / madera", "モク・ボク", "き", 4, "木 (きへん)", "木の 下で まっています", "árbol-DE / debajo-EN / estoy-esperando",
             "un tronco con raíces y ramas", "木 き árbol · 木曜日 もくようび jueves"),
            ("金", "oro / dinero", "キン", "かね", 8, "金 (かねへん)", "お金が ありません", "dinero-SUJ / no-hay",
             "un tejado sobre lingotes enterrados", "お金 おかね dinero · 金曜日 きんようび viernes"),
            ("土", "tierra", "ド", "つち", 3, "土 (つちへん)", "土曜日に 行きます", "sábado-A / voy",
             "una cruz plantada en el suelo", "土曜日 どようび sábado · 土 つち tierra"),
            ("曜", "día de la semana", "ヨウ", "—", 18, "日 (ひへん)", "何曜日ですか", "¿qué-día-de-la-semana-es?",
             "el kanji más largo del N5; solo aparece en 〜曜日", "曜日 ようび día de la semana"),
            ("年", "año", "ネン", "とし", 6, "干 (かん)", "来年 日本に 行きます", "año-que-viene / Japón-A / voy",
             "una espiga: un año es una cosecha", "今年 ことし este año · 去年 きょねん el año pasado"),
            ("時", "hora / momento", "ジ", "とき", 10, "日 (ひへん)", "今 何時ですか", "ahora / ¿qué-hora-es?",
             "el sol 日 en un templo: el reloj de sol", "時間 じかん tiempo · 一時 いちじ la 1 · 時々 ときどき a veces"),
            ("分", "minuto / dividir", "フン・ブン", "わ(ける)・わ(かる)", 4, "刀 (かたな)", "十分 まって ください", "10-minutos / espera / por-favor",
             "un cuchillo 刀 partiendo algo: las partes de la hora", "五分 ごふん 5 min · 分かる わかる entender"),
            ("半", "mitad", "ハン", "なか(ば)", 5, "十 (じゅう)", "二時半に あいましょう", "2h-y-media-A / quedemos",
             "algo cortado por el eje", "半分 はんぶん la mitad · 二時半 にじはん las 2:30"),
            ("今", "ahora", "コン", "いま", 4, "人 (ひとやね)", "今 行きます", "ahora / voy",
             "un tejado sobre el instante presente", "今日 きょう hoy · 今年 ことし este año · 今 いま ahora"),
            ("週", "semana", "シュウ", "—", 11, "辵 (しんにょう)", "来週 あいましょう", "semana-que-viene / quedemos",
             "しんにょう es movimiento: la semana que avanza", "今週 こんしゅう esta semana · 週末 しゅうまつ fin de semana"),
            ("間", "intervalo / entre", "カン", "あいだ", 12, "門 (もんがまえ)", "三時間 べんきょうしました", "3-horas / estudié",
             "el sol 日 asomando entre las hojas de una puerta 門", "時間 じかん tiempo · 人間 にんげん ser humano"),
            ("毎", "cada", "マイ", "—", 6, "毋 (なかれ)", "毎日 日本語を べんきょうします", "cada-día / japonés-OBJ / estudio",
             "casi 母, pero con la cabeza tachada: la repetición", "毎日 まいにち todos los días · 毎朝 まいあさ cada mañana"),
            ("午", "mediodía", "ゴ", "—", 4, "十 (じゅう)", "午後 あいましょう", "por-la-tarde / quedemos",
             "un 牛 sin cuerno; solo vive dentro de 午前 y 午後", "午前 ごぜん a.m. · 午後 ごご p.m."),
            ("前", "antes / delante", "ゼン", "まえ", 9, "刀 (りっとう)", "駅の 前で まってます", "estación-DE / delante-EN / estoy-esperando",
             "sirve para el espacio y para el tiempo, igual que 'delante/antes'", "名前 なまえ nombre · 午前 ごぜん a.m. · 前 まえ delante"),
            ("後", "después / detrás", "ゴ・コウ", "あと・うし(ろ)", 9, "彳 (ぎょうにんべん)", "後で 電話します", "después-EN / llamo",
             "el contrario exacto de 前, también en los dos sentidos", "午後 ごご p.m. · 後ろ うしろ detrás · 後で あとで luego"),
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
             "una raya y algo que sobresale por encima", "上 うえ encima · 上手 じょうず hábil"),
            ("下", "abajo / debajo", "カ・ゲ", "した・さ(がる)", 3, "一 (いち)", "いすの 下に ねこが います", "silla-DE / debajo-EN / gato-SUJ / hay",
             "el 上 puesto del revés", "下 した debajo · 下手 へた torpe · 地下鉄 ちかてつ metro"),
            ("中", "dentro / en medio", "チュウ", "なか", 4, "丨 (たてぼう)", "かばんの 中に あります", "bolso-DE / dentro-EN / está",
             "una flecha que atraviesa una caja por el centro", "中 なか dentro · 中国 ちゅうごく China · 一日中 いちにちじゅう todo el día"),
            ("外", "fuera / exterior", "ガイ", "そと", 5, "夕 (ゆうべ)", "外は さむいですよ", "fuera-TEMA / frío-es-¡eh!",
             "夕 (la tarde) + adivinación: lo que queda fuera de casa", "外 そと fuera · 外国 がいこく extranjero · 外国人 がいこくじん extranjero"),
            ("右", "derecha", "ウ・ユウ", "みぎ", 5, "口 (くち)", "つぎの かどを 右に まがって ください", "siguiente / esquina-OBJ / derecha-A / gira / por-favor",
             "una mano sobre una boca: con la derecha se come", "右 みぎ derecha · 右手 みぎて mano derecha"),
            ("左", "izquierda", "サ", "ひだり", 5, "工 (たくみ)", "左の 店です", "izquierda-DE / tienda-es",
             "casi idéntico a 右, pero con 工 debajo: la mano que sujeta la herramienta", "左 ひだり izquierda · 左手 ひだりて mano izquierda"),
            ("東", "este", "トウ", "ひがし", 8, "木 (き)", "東京に すんでいます", "Tokio-EN / vivo",
             "el sol 日 saliendo por detrás de un árbol 木", "東京 とうきょう Tokio · 東 ひがし este"),
            ("西", "oeste", "セイ・サイ", "にし", 6, "西 (にし)", "西の そらが あかいです", "oeste-DE / cielo-SUJ / rojo-es",
             "un pájaro entrando en el nido al atardecer", "西 にし oeste · 関西 かんさい la región de Kansai"),
            ("南", "sur", "ナン", "みなみ", 9, "十 (じゅう)", "南は あたたかいです", "sur-TEMA / cálido-es",
             "un invernadero: por el sur entra el calor", "南 みなみ sur · 南口 みなみぐち salida sur"),
            ("北", "norte", "ホク", "きた", 5, "匕 (さじのひ)", "北は さむいです", "norte-TEMA / frío-es",
             "dos personas de espaldas, dándose calor", "北 きた norte · 北海道 ほっかいどう Hokkaido"),
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
             "dos piernas andando", "人 ひと persona · 日本人 にほんじん japonés · 三人 さんにん tres personas"),
            ("男", "hombre", "ダン", "おとこ", 7, "田 (た)", "男の 人が 二人 います", "hombre-DE / persona-SUJ / dos / hay",
             "田 (campo) + 力 (fuerza): el que trabaja el campo", "男 おとこ hombre · 男の子 おとこのこ niño"),
            ("女", "mujer", "ジョ", "おんな", 3, "女 (おんな)", "女の 人と はなしました", "mujer-DE / persona-CON / hablé",
             "una figura sentada con los brazos cruzados", "女 おんな mujer · 女の子 おんなのこ niña · 彼女 かのじょ ella"),
            ("子", "niño / hijo", "シ", "こ", 3, "子 (こへん)", "子どもが 三人 います", "niños-SUJ / tres / hay",
             "un bebé envuelto con los brazos abiertos", "子ども こども niño · 女子 じょし chica · 息子 むすこ hijo"),
            ("母", "madre (propia)", "ボ", "はは", 5, "毋 (なかれ)", "母は 元気です", "madre-TEMA / bien-está",
             "los dos puntos son los pechos que amamantan", "母 はは mi madre · お母さん おかあさん su madre"),
            ("父", "padre (propio)", "フ", "ちち", 4, "父 (ちち)", "父は 会社に います", "padre-TEMA / empresa-EN / está",
             "una mano sujetando un hacha", "父 ちち mi padre · お父さん おとうさん su padre"),
            ("友", "amigo", "ユウ", "とも", 4, "又 (また)", "友だちと 会います", "amigo-CON / quedo",
             "dos manos que se cruzan", "友だち ともだち amigo · 友人 ゆうじん amistad (formal)"),
            ("先", "antes / previo / punta", "セン", "さき", 6, "儿 (にんにょう)", "お先に しつれいします", "antes-que-usted / me-retiro",
             "un pie que va por delante", "先生 せんせい profesor · 先週 せんしゅう la semana pasada"),
            ("生", "vida / nacer / crudo", "セイ・ショウ", "う(まれる)・い(きる)・なま", 5, "生 (うまれる)", "私は 学生です", "yo-TEMA / estudiante-soy",
             "un brote saliendo de la tierra", "学生 がくせい estudiante · 生ビール なまビール cerveza de barril"),
            ("学", "estudiar / ciencia", "ガク", "まな(ぶ)", 8, "子 (こ)", "日本語を 学んでいます", "japonés-OBJ / estoy-estudiando",
             "un niño 子 bajo el techo de la escuela", "学校 がっこう escuela · 大学 だいがく universidad · 学生 がくせい estudiante"),
            ("校", "escuela", "コウ", "—", 10, "木 (きへん)", "学校に 行きます", "escuela-A / voy",
             "casi siempre va pegado a 学; solo, casi no aparece", "学校 がっこう escuela · 高校 こうこう instituto"),
            ("名", "nombre", "メイ", "な", 6, "口 (くち)", "お名前は", "¿su-nombre-TEMA?",
             "夕 (noche) + 口 (boca): de noche hay que decir tu nombre", "名前 なまえ nombre · 有名 ゆうめい famoso"),
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
             "una boca abierta, cuadrada", "口 くち boca · 入口 いりぐち entrada · 出口 でぐち salida"),
            ("目", "ojo", "モク", "め", 5, "目 (め)", "目が いたいです", "ojo-SUJ / duele",
             "un ojo puesto de pie", "目 め ojo · 一つ目 ひとつめ el primero"),
            ("耳", "oreja / oído", "ジ", "みみ", 6, "耳 (みみへん)", "耳が よく 聞こえません", "oído-SUJ / bien / no-oigo",
             "una oreja de perfil", "耳 みみ oreja"),
            ("手", "mano", "シュ", "て", 4, "手 (てへん)", "手を あらいます", "manos-OBJ / me-lavo",
             "cuatro dedos y la muñeca", "手 て mano · 上手 じょうず hábil · 切手 きって sello"),
            ("足", "pie / pierna / bastar", "ソク", "あし・た(りる)", 7, "足 (あしへん)", "足が つかれました", "piernas-SUJ / se-cansaron",
             "口 (la rodilla) con un pie debajo", "足 あし pie · 足りる たりる ser suficiente"),
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
             "un cruce de caminos visto desde arriba", "行く いく ir · 銀行 ぎんこう banco · 旅行 りょこう viaje"),
            ("来", "venir", "ライ", "く(る)", 7, "木 (き)", "友だちが 来ます", "amigo-SUJ / viene",
             "un árbol con dos personitas acercándose", "来る くる venir · 来年 らいねん el año que viene"),
            ("見", "ver / mirar", "ケン", "み(る)", 7, "見 (みる)", "テレビを 見ます", "tele-OBJ / veo",
             "un ojo 目 con piernas: el ojo que va a mirar", "見る みる ver · 見せる みせる mostrar · 花見 はなみ ver los cerezos"),
            ("聞", "escuchar / preguntar", "ブン・モン", "き(く)", 14, "耳 (みみ)", "音楽を 聞きます", "música-OBJ / escucho",
             "una oreja 耳 pegada a la puerta 門", "聞く きく escuchar · 新聞 しんぶん periódico"),
            ("読", "leer", "ドク", "よ(む)", 14, "言 (ごんべん)", "本を 読みます", "libro-OBJ / leo",
             "言 (palabra) + vender: leer es hacer circular palabras", "読む よむ leer · 読書 どくしょ lectura"),
            ("書", "escribir", "ショ", "か(く)", 10, "曰 (ひらび)", "名前を 書いて ください", "nombre-OBJ / escribe / por-favor",
             "un pincel sobre un papel", "書く かく escribir · 辞書 じしょ diccionario · 図書館 としょかん biblioteca"),
            ("話", "hablar / historia", "ワ", "はな(す)・はなし", 13, "言 (ごんべん)", "日本語を 話します", "japonés-OBJ / hablo",
             "言 (palabra) + 舌 (lengua)", "話す はなす hablar · 電話 でんわ teléfono · お話 おはなし cuento"),
            ("言", "decir", "ゲン・ゴン", "い(う)", 7, "言 (ことば)", "何と 言いましたか", "qué-QUE / ¿dijiste?",
             "una boca 口 con las palabras saliendo en capas", "言う いう decir · 言葉 ことば palabra"),
            ("食", "comer", "ショク", "た(べる)", 9, "食 (しょくへん)", "ごはんを 食べます", "comida-OBJ / como",
             "un tejado sobre un cuenco de arroz", "食べる たべる comer · 食堂 しょくどう comedor · 食事 しょくじ comida"),
            ("飲", "beber", "イン", "の(む)", 12, "食 (しょくへん)", "お茶を 飲みます", "té-OBJ / bebo",
             "食 (comida) + 欠 (boca abierta): tragar", "飲む のむ beber · 飲み物 のみもの bebida"),
            ("買", "comprar", "バイ", "か(う)", 12, "貝 (かい)", "パンを 買います", "pan-OBJ / compro",
             "una red sobre 貝 (concha): las conchas eran el dinero", "買う かう comprar · 買い物 かいもの la compra"),
            ("出", "salir / sacar", "シュツ", "で(る)・だ(す)", 5, "凵 (かんにょう)", "八時に 家を 出ます", "8h-A / casa-OBJ / salgo",
             "dos montañas apiladas: algo que asoma", "出る でる salir · 出口 でぐち salida · 出す だす sacar"),
            ("入", "entrar / meter", "ニュウ", "はい(る)・い(れる)", 2, "入 (いる)", "店に 入ります", "tienda-A / entro",
             "casi igual que 人; en 入 el trazo largo es el de la izquierda", "入る はいる entrar · 入口 いりぐち entrada"),
            ("立", "estar de pie", "リツ", "た(つ)", 5, "立 (たつ)", "ここに 立って ください", "aquí-EN / ponte-de-pie / por-favor",
             "una persona con los pies bien plantados", "立つ たつ ponerse de pie · 立派 りっぱ espléndido"),
            ("休", "descansar", "キュウ", "やす(む)", 6, "人 (にんべん)", "日曜日は 休みます", "domingo-TEMA / descanso",
             "una persona 亻 apoyada en un árbol 木", "休む やすむ descansar · 休み やすみ descanso · 昼休み ひるやすみ pausa"),
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
             "tres picos, el del medio más alto", "山 やま montaña · 富士山 ふじさん el monte Fuji · 火山 かざん volcán"),
            ("川", "río", "セン", "かわ", 3, "巛 (かわ)", "川で およぎました", "río-EN / nadé",
             "tres líneas de corriente", "川 かわ río · 小川 おがわ arroyo"),
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


def _item(t):
    """Tupla de datos → ítem del temario (kind vocabulario, tipo kanji)."""
    jp, sig, on, kun, trazos, radical, ejemplo, literal, mnemo, vocab = t
    lect = " · ".join(p for p in (f"on {on}" if on != "—" else "",
                                  f"kun {kun}" if kun != "—" else "") if p)
    return {
        "kind": "vocabulario", "tipo": "kanji", "jp": jp,
        "reading": (kun if kun != "—" else on).split("・")[0].replace("(", "").replace(")", ""),
        "meaning": f"{sig} (kanji)",
        "ejemplo": ejemplo, "literal": literal,
        "uso": f"{lect} · {trazos} trazos · radical {radical}. {mnemo}. Aparece en: {vocab}",
        # campos crudos por si algún día la cara dibuja una ficha de kanji
        "on": on, "kun": kun, "trazos": trazos, "radical": radical,
        "mnemo": mnemo, "vocab_ejemplo": vocab,
    }


KANJI_N5 = [_item(t) for _, _, _, _, tuplas in _CATEGORIAS for t in tuplas]


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
    assert len(KANJI_N5) == 103, len(KANJI_N5)
    assert len({k["jp"] for k in KANJI_N5}) == 103, "kanji repetido"
    for k in KANJI_N5:
        assert len(k["jp"]) == 1 and "一" <= k["jp"] <= "鿿", k["jp"]
        assert k["reading"] and k["ejemplo"] and k["literal"] and k["mnemo"], k["jp"]
        assert 1 <= k["trazos"] <= 20, k

    us = unidades_kanji()
    assert len(us) == 10 and sum(len(u["items"]) for u in us) == 103
    assert us[0]["prerequisito"] is None
    assert [u["prerequisito"] for u in us[1:]] == [u["id"] for u in us[:-1]], "cadena rota"

    # con las fichas que ya existen filtradas, ningún carácter se duplica
    filtradas = unidades_kanji({"一", "二", "三", "山"}, prerequisito="x")
    assert sum(len(u["items"]) for u in filtradas) == 99
    assert filtradas[0]["prerequisito"] == "x"
    print("ok:", len(KANJI_N5), "kanji N5 en", len(us), "unidades")
