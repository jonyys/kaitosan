"""Espina dorsal del temario de japonés y selector del próximo ítem nuevo."""

from ai.sensei.kanji_n5 import unidades_kanji

CURRICULUM = [
    # ── Unidad 0: Saludos y expresiones básicas (sin puerta) ─────────────────
    {
        "id": "saludos_basicos",
        "nombre": "Saludos y expresiones básicas",
        "funcion": "saludar y despedirte a cualquier hora, dar las gracias, disculparte y decir que no has entendido",
        "frases_hechas": [
            {"jp": "おつかれさま", "uso": "a alguien que acaba algo: un curro, un examen, una mudanza"},
            {"jp": "よろしくお願いします", "uso": "al conocer a alguien y al pedir algo: 'cuento contigo'"},
            {"jp": "なるほど", "uso": "cuando algo te encaja: 'ah, ya veo'"},
            {"jp": "ちょっと…", "uso": "para decir que no sin decir no"},
        ],
        "prerequisito": None,
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "はい", "reading": "はい", "meaning": "sí", "tipo": "expresión",
             "ejemplo": "はい、そうです", "literal": "sí / así-es",
             "uso": "confirmar; también es el '¿sí?' de coger el teléfono o de responder cuando te llaman"},
            {"kind": "vocabulario", "jp": "いいえ", "reading": "いいえ", "meaning": "no", "tipo": "expresión",
             "ejemplo": "いいえ、ちがいます", "literal": "no / es-diferente",
             "uso": "negar con claridad; en el día a día se suaviza con ううん o con ちょっと…, porque un いいえ seco suena cortante"},
            {"kind": "vocabulario", "jp": "ありがとう", "reading": "ありがとう", "meaning": "gracias", "tipo": "expresión",
             "ejemplo": "ありがとう ございます", "literal": "gracias / (forma cortés)",
             "uso": "con amigos ありがとう a secas; con desconocidos o gente mayor, siempre con ございます"},
            {"kind": "vocabulario", "jp": "すみません", "reading": "すみません", "meaning": "disculpe / perdón", "tipo": "expresión",
             "ejemplo": "すみません、みずを ください", "literal": "perdón / agua-OBJ / por-favor",
             "uso": "vale para tres cosas: pedir perdón, llamar al camarero y dar las gracias por una molestia"},
            {"kind": "vocabulario", "jp": "こんにちは", "reading": "こんにちは", "meaning": "hola (durante el día)", "tipo": "expresión",
             "ejemplo": "こんにちは、げんきですか", "literal": "hola / ¿estás-bien?",
             "uso": "solo de día, de media mañana al atardecer; no se usa con la gente de tu propia casa"},
            {"kind": "vocabulario", "jp": "おはようございます", "reading": "おはようございます", "meaning": "buenos días", "tipo": "expresión",
             "ejemplo": "せんせい、おはようございます", "literal": "profesor / buenos-días",
             "uso": "hasta media mañana; entre amigos se corta a おはよう"},
            {"kind": "vocabulario", "jp": "こんばんは", "reading": "こんばんは", "meaning": "buenas noches (saludo)", "tipo": "expresión",
             "ejemplo": "こんばんは、おそいですね", "literal": "buenas-noches / es-tarde-¿verdad?",
             "uso": "al encontrarte con alguien ya de noche; no sirve como despedida"},
            {"kind": "vocabulario", "jp": "さようなら", "reading": "さようなら", "meaning": "adiós", "tipo": "expresión",
             "ejemplo": "さようなら、また らいしゅう", "literal": "adiós / otra-vez / la-semana-que-viene",
             "uso": "despedida con peso de 'no nos vemos en un tiempo'; para el día a día se dice じゃあね o また あした"},
            {"kind": "vocabulario", "jp": "おやすみなさい", "reading": "おやすみなさい", "meaning": "buenas noches (al dormir)", "tipo": "expresión",
             "ejemplo": "おやすみなさい、また あした", "literal": "buenas-noches / otra-vez / mañana",
             "uso": "solo cuando alguien se va a dormir, no al despedirte por la calle de noche"},
            {"kind": "vocabulario", "jp": "わかりました", "reading": "わかりました", "meaning": "entendido / comprendido", "tipo": "expresión",
             "ejemplo": "はい、わかりました", "literal": "sí / he-entendido",
             "uso": "va en pasado: 'ya lo he captado'. Responder わかります suena raro"},
            {"kind": "vocabulario", "jp": "わかりません", "reading": "わかりません", "meaning": "no entiendo", "tipo": "expresión",
             "ejemplo": "すみません、わかりません", "literal": "perdón / no-entiendo",
             "uso": "en presente negativo; para 'no te he entendido ahora mismo' nunca se usa わかりませんでした"},
            {"kind": "vocabulario", "jp": "もう一度", "reading": "もういちど", "meaning": "una vez más / repetir", "tipo": "expresión",
             "ejemplo": "もういちど おねがいします", "literal": "una-vez-más / por-favor",
             "uso": "la frase de supervivencia en clase; casi siempre con おねがいします detrás"},
            {"kind": "vocabulario", "jp": "ゆっくり", "reading": "ゆっくり", "meaning": "despacio / lentamente", "tipo": "adverbio",
             "ejemplo": "ゆっくり はなして ください", "literal": "despacio / habla / por-favor",
             "uso": "es adverbio: va delante del verbo, nunca detrás"},
        ],
    },

    # ── Unidad 1: Partículas básicas ─────────────────────────────────────────
    {
        "id": "particulas_basicas",
        "nombre": "Partículas básicas は・が・を・に",
        "funcion": "montar frases tuyas: decir de qué hablas, qué haces, dónde y con quién",
        "frases_hechas": [
            {"jp": "そうですね", "uso": "para ganar tiempo antes de responder, como el 'pues…' español"},
            {"jp": "えっと…", "uso": "el 'ehh…' japonés mientras piensas"},
            {"jp": "それで？", "uso": "'¿y entonces?', para que el otro siga contando"},
            {"jp": "やっぱり", "uso": "'lo sabía' / 'al final sí', cuando se confirma lo que esperabas"},
        ],
        "prerequisito": "saludos_basicos",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "は", "meaning": "partícula de tema (wa): marca el tema de la oración",
             "ejemplo": "わたしは ラウラです", "literal": "yo-TEMA / Laura-soy",
             "uso": "se escribe は pero se pronuncia 'wa'. Marca de qué se habla, no quién hace la acción"},
            {"kind": "gramatica", "jp": "が", "meaning": "partícula de sujeto: enfatiza quién realiza la acción",
             "ejemplo": "ねこが います", "literal": "gato-SUJ / hay",
             "uso": "presenta algo nuevo o responde a '¿quién?' o '¿qué?'. Con すき y じょうず marca lo que gusta: にほんごが すきです"},
            {"kind": "gramatica", "jp": "を", "meaning": "partícula de objeto directo (wo): marca el complemento directo",
             "ejemplo": "ごはんを たべます", "literal": "comida-OBJ / como",
             "uso": "se escribe を y se pronuncia 'o'. Solo aparece delante de verbos que llevan objeto"},
            {"kind": "gramatica", "jp": "に", "meaning": "partícula de dirección / destino / tiempo / receptor",
             "ejemplo": "７じに うちに かえります", "literal": "7h-EN / casa-A / vuelvo",
             "uso": "hora concreta y destino. Los tiempos relativos (きょう, あした, まいにち) NO llevan に"},
            {"kind": "gramatica", "jp": "で", "meaning": "partícula de lugar de acción o medio / herramienta",
             "ejemplo": "レストランで たべます", "literal": "restaurante-EN / como",
             "uso": "で es el sitio donde ocurre la acción; に es el sitio adonde vas o donde algo está quieto"},
            {"kind": "gramatica", "jp": "の", "meaning": "partícula posesiva: A の B → 'B de A'",
             "ejemplo": "ラウラの ねこ", "literal": "Laura-DE / gato",
             "uso": "orden inverso al español: el poseedor va delante. También encadena: にほんごの せんせいの くるま"},
            {"kind": "gramatica", "jp": "も", "meaning": "partícula inclusiva: 'también' / 'tampoco'",
             "ejemplo": "わたしも いきます", "literal": "yo-TAMBIÉN / voy",
             "uso": "sustituye a は y a が, no se suma a ellas: nunca わたしはも"},
            {"kind": "gramatica", "jp": "と", "meaning": "partícula 'y' (sustantivos) / 'con' (compañía)",
             "ejemplo": "ともだちと はなします", "literal": "amigo-CON / hablo",
             "uso": "'y' solo entre sustantivos y en lista cerrada. Para unir dos frases no sirve: eso es la forma-て"},
            {"kind": "gramatica", "jp": "か", "meaning": "partícula interrogativa: convierte la oración en pregunta",
             "ejemplo": "コーヒーを のみますか", "literal": "café-OBJ / ¿bebes?",
             "uso": "va al final del todo. Con か no hace falta ni signo de interrogación ni subir el tono"},
            {"kind": "gramatica", "jp": "ね", "meaning": "partícula final: busca confirmación ('¿verdad?', '¿no?')",
             "ejemplo": "おいしいですね", "literal": "está-rico-¿verdad?",
             "uso": "busca complicidad: das por hecho que el otro opina lo mismo que tú"},
            {"kind": "gramatica", "jp": "よ", "meaning": "partícula final: afirma algo que el oyente no sabe",
             "ejemplo": "あの みせは やすいですよ", "literal": "esa / tienda-TEMA / barata-es-¡eh!",
             "uso": "informa de algo nuevo para el otro. Abusar de よ suena insistente o sabelotodo"},
        ],
    },

    # ── Unidad 2: Cópula です y forma ます ────────────────────────────────────
    {
        "id": "desu_masu",
        "nombre": "Cópula です y forma ～ます",
        "funcion": "presentarte, decir qué eres y qué haces cada día, y preguntarle lo mismo a alguien",
        "frases_hechas": [
            {"jp": "はじめまして", "uso": "solo la primerísima vez que ves a alguien, nunca después"},
            {"jp": "どうぞよろしく", "uso": "cierra la presentación, justo después de tu nombre"},
            {"jp": "こちらこそ", "uso": "'lo mismo digo', al devolver un gracias o un cumplido"},
            {"jp": "おひさしぶりです", "uso": "a alguien que llevas tiempo sin ver"},
        ],
        "prerequisito": "particulas_basicas",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "です", "meaning": "cópula formal: 'es / son' (afirmativo presente)",
             "ejemplo": "わたしは がくせいです", "literal": "yo-TEMA / estudiante-soy",
             "uso": "no es un verbo 'ser' de verdad: con adjetivos-い no se conjuga (おいしかったです, nunca おいしいでした)"},
            {"kind": "gramatica", "jp": "ではありません", "meaning": "cópula formal negativa: 'no es / no son'",
             "ejemplo": "がくせいでは ありません", "literal": "estudiante-EN-CUANTO-A / no-hay",
             "uso": "muy formal, de documento o discurso. Hablando se dice じゃありません o じゃないです"},
            {"kind": "gramatica", "jp": "でした", "meaning": "cópula formal pasada: 'era / fueron'",
             "ejemplo": "きのうは やすみでした", "literal": "ayer-TEMA / descanso-fue",
             "uso": "solo con sustantivos y adjetivos-な; con adjetivos-い se usa 〜かった"},
            {"kind": "gramatica", "jp": "〜ます", "meaning": "terminación verbal formal presente / futuro afirmativo",
             "ejemplo": "まいあさ コーヒーを のみます", "literal": "cada-mañana / café-OBJ / bebo",
             "uso": "presente y futuro a la vez: 'bebo' y 'beberé'. Lo decide el contexto, no el verbo"},
            {"kind": "gramatica", "jp": "〜ません", "meaning": "terminación verbal formal presente negativa",
             "ejemplo": "にくは たべません", "literal": "carne-TEMA / no-como",
             "uso": "sirve tanto para 'ahora no como' como para 'no como carne nunca'"},
            {"kind": "gramatica", "jp": "〜ました", "meaning": "terminación verbal formal pasada afirmativa",
             "ejemplo": "ゆうべ えいがを みました", "literal": "anoche / película-OBJ / vi",
             "uso": "pasado formal; también para lo que se acaba de terminar hace un momento"},
            {"kind": "gramatica", "jp": "〜ませんでした", "meaning": "terminación verbal formal pasada negativa",
             "ejemplo": "ゆうべ ねませんでした", "literal": "anoche / no-dormí",
             "uso": "dos piezas pegadas: negativo + pasado. Es larga, por eso en informal se abrevia a 〜なかった"},
            {"kind": "gramatica", "jp": "〜ますか", "meaning": "pregunta formal sobre acción: '¿hace X?'",
             "ejemplo": "あした きますか", "literal": "mañana / ¿vienes?",
             "uso": "pregunta directa. Para invitar de forma suave se usa 〜ませんか ('¿no te vienes?')"},
        ],
    },

    # ── Unidad 3: Verbos esenciales N5 ───────────────────────────────────────
    {
        "id": "verbos_n5",
        "nombre": "Verbos esenciales N5",
        "funcion": "contar tu día entero: a qué hora te levantas, qué comes, adónde vas y qué haces",
        "frases_hechas": [
            {"jp": "いってきます", "uso": "al salir de casa; literalmente 'voy y vuelvo'"},
            {"jp": "いってらっしゃい", "uso": "lo que contesta quien se queda"},
            {"jp": "ただいま", "uso": "al volver a casa, aunque no haya nadie"},
            {"jp": "おかえり", "uso": "lo que contesta quien estaba en casa"},
        ],
        "prerequisito": "desu_masu",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "食べる", "reading": "たべる", "meaning": "comer", "tipo": "verbo",
             "ejemplo": "パンを たべます", "literal": "pan-OBJ / como",
             "uso": "grupo 2: quitas る y pones ます. Comer con la boca; tomarse una medicina es のむ, no たべる"},
            {"kind": "vocabulario", "jp": "飲む", "reading": "のむ", "meaning": "beber", "tipo": "verbo",
             "ejemplo": "みずを のみます", "literal": "agua-OBJ / bebo",
             "uso": "en japonés se 'beben' también la sopa, las pastillas y hasta el tabaco (たばこを のむ)"},
            {"kind": "vocabulario", "jp": "行く", "reading": "いく", "meaning": "ir", "tipo": "verbo",
             "ejemplo": "がっこうに いきます", "literal": "escuela-A / voy",
             "uso": "alejarte de donde estás. Su forma-て es la única irregular del grupo 1: いって"},
            {"kind": "vocabulario", "jp": "来る", "reading": "くる", "meaning": "venir", "tipo": "verbo",
             "ejemplo": "ともだちが きます", "literal": "amigo-SUJ / viene",
             "uso": "acercarse a donde estás tú. Si eres tú quien va a casa del otro, en japonés es いく"},
            {"kind": "vocabulario", "jp": "する", "reading": "する", "meaning": "hacer", "tipo": "verbo",
             "ejemplo": "べんきょうを します", "literal": "estudio-OBJ / hago",
             "uso": "convierte sustantivos en verbos: そうじする, でんわする, りょこうする. Es el comodín del idioma"},
            {"kind": "vocabulario", "jp": "見る", "reading": "みる", "meaning": "ver / mirar", "tipo": "verbo",
             "ejemplo": "テレビを みます", "literal": "tele-OBJ / veo",
             "uso": "mirar con intención. Lo que se ve sin querer, lo que está a la vista, es みえる"},
            {"kind": "vocabulario", "jp": "聞く", "reading": "きく", "meaning": "escuchar / preguntar", "tipo": "verbo",
             "ejemplo": "おんがくを ききます", "literal": "música-OBJ / escucho",
             "uso": "dos sentidos: escuchar algo, y preguntar a alguien (せんせいに ききます = 'le pregunto al profe')"},
            {"kind": "vocabulario", "jp": "話す", "reading": "はなす", "meaning": "hablar", "tipo": "verbo",
             "ejemplo": "にほんごを はなします", "literal": "japonés-OBJ / hablo",
             "uso": "hablar un idioma o contar algo. Charlar CON alguien lleva と: ともだちと はなす"},
            {"kind": "vocabulario", "jp": "書く", "reading": "かく", "meaning": "escribir", "tipo": "verbo",
             "ejemplo": "なまえを かきます", "literal": "nombre-OBJ / escribo",
             "uso": "grupo 1 en く: かいて, かきます. Dibujar es el mismo かく pero se escribe 描く"},
            {"kind": "vocabulario", "jp": "読む", "reading": "よむ", "meaning": "leer", "tipo": "verbo",
             "ejemplo": "ほんを よみます", "literal": "libro-OBJ / leo",
             "uso": "grupo 1 en む: よんで. También 'leer' el ambiente de una sala: くうきを よむ"},
            {"kind": "vocabulario", "jp": "買う", "reading": "かう", "meaning": "comprar", "tipo": "verbo",
             "ejemplo": "スーパーで くつを かいます", "literal": "súper-EN / zapatos-OBJ / compro",
             "uso": "grupo 1 en う: かって, かいます. El sitio donde compras lleva で"},
            {"kind": "vocabulario", "jp": "帰る", "reading": "かえる", "meaning": "regresar / volver a casa", "tipo": "verbo",
             "ejemplo": "うちに かえります", "literal": "casa-A / vuelvo",
             "uso": "volver al sitio al que perteneces (casa, país). Acaba en る pero es grupo 1: かえって"},
            {"kind": "vocabulario", "jp": "起きる", "reading": "おきる", "meaning": "levantarse / despertarse", "tipo": "verbo",
             "ejemplo": "６じに おきます", "literal": "6h-EN / me-levanto",
             "uso": "levantarse de dormir; también 'ocurrir' algo (じこが おきる = 'pasa un accidente')"},
            {"kind": "vocabulario", "jp": "寝る", "reading": "ねる", "meaning": "dormir / acostarse", "tipo": "verbo",
             "ejemplo": "１１じに ねます", "literal": "11h-EN / me-acuesto",
             "uso": "irse a la cama. Estar durmiendo ahora mismo es ねています"},
            {"kind": "vocabulario", "jp": "分かる", "reading": "わかる", "meaning": "entender / comprender", "tipo": "verbo",
             "ejemplo": "いみが わかります", "literal": "significado-SUJ / entiendo",
             "uso": "lleva が, no を: lo entendido es el sujeto. Es 'me queda claro', no 'lo comprendo a base de esfuerzo'"},
            {"kind": "vocabulario", "jp": "ある", "reading": "ある", "meaning": "haber / existir (objetos inanimados)", "tipo": "verbo",
             "ejemplo": "つくえの うえに ほんが あります", "literal": "mesa-DE / encima-EN / libro-SUJ / hay",
             "uso": "cosas y plantas; también planes y citas: あした しけんが あります"},
            {"kind": "vocabulario", "jp": "いる", "reading": "いる", "meaning": "estar / existir (personas y animales)", "tipo": "verbo",
             "ejemplo": "へやに ねこが います", "literal": "habitación-EN / gato-SUJ / hay",
             "uso": "lo que se mueve por sí solo. Un coche es ある aunque esté en marcha; la persona que va dentro, いる"},
            {"kind": "vocabulario", "jp": "思う", "reading": "おもう", "meaning": "pensar / creer", "tipo": "verbo",
             "ejemplo": "いいと おもいます", "literal": "bueno-QUE / pienso",
             "uso": "la opinión va delante marcada con と. Es la forma educada de opinar: sin おもいます suena a verdad absoluta"},
            {"kind": "vocabulario", "jp": "待つ", "reading": "まつ", "meaning": "esperar", "tipo": "verbo",
             "ejemplo": "ちょっと まって ください", "literal": "un-momento / espera / por-favor",
             "uso": "grupo 1 en つ: まって, まちます. Esa frase se oye cien veces al día"},
            {"kind": "vocabulario", "jp": "持つ", "reading": "もつ", "meaning": "tener / sostener / llevar", "tipo": "verbo",
             "ejemplo": "かばんを もちます", "literal": "bolso-OBJ / llevo",
             "uso": "sostener en la mano. 'Tener' en el sentido de poseer se dice もっています"},
        ],
    },

    # ── Unidad 4: Adjetivos N5 ───────────────────────────────────────────────
    {
        "id": "adjetivos_n5",
        "nombre": "Adjetivos N5 (い y な)",
        "funcion": "describir cosas y personas, y decir con claridad qué te gusta y qué no",
        "frases_hechas": [
            {"jp": "すごい", "uso": "vale para todo: admiración, sorpresa o susto"},
            {"jp": "かわいい", "uso": "no es solo 'mono': se dice de casi cualquier cosa que gusta"},
            {"jp": "びみょう", "uso": "'regulero', ni bien ni mal; muy útil para no mojarte"},
            {"jp": "大丈夫です", "uso": "también sirve para rechazar algo con educación: 'no, gracias'"},
        ],
        "prerequisito": "verbos_n5",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "大きい", "reading": "おおきい", "meaning": "grande (adj-い)", "tipo": "adjetivo",
             "ejemplo": "おおきい いえですね", "literal": "grande / casa-es-¿verdad?",
             "uso": "adj-い: va pegado delante del sustantivo, sin nada en medio"},
            {"kind": "vocabulario", "jp": "小さい", "reading": "ちいさい", "meaning": "pequeño (adj-い)", "tipo": "adjetivo",
             "ejemplo": "ちいさい こえで はなします", "literal": "pequeña / voz-CON / hablo",
             "uso": "también 'bajito' de volumen y 'de poca edad'"},
            {"kind": "vocabulario", "jp": "新しい", "reading": "あたらしい", "meaning": "nuevo (adj-い)", "tipo": "adjetivo",
             "ejemplo": "あたらしい ケータイを かいました", "literal": "nuevo / móvil-OBJ / compré",
             "uso": "nuevo de recién hecho o recién comprado. Algo usado que es nuevo para ti no es あたらしい"},
            {"kind": "vocabulario", "jp": "古い", "reading": "ふるい", "meaning": "viejo / antiguo (adj-い)", "tipo": "adjetivo",
             "ejemplo": "この ビルは ふるいです", "literal": "este / edificio-TEMA / viejo-es",
             "uso": "solo cosas. Una persona mayor nunca es ふるい: es としうえ o おとしより"},
            {"kind": "vocabulario", "jp": "おいしい", "reading": "おいしい", "meaning": "delicioso / rico (adj-い)", "tipo": "adjetivo",
             "ejemplo": "この ラーメン、おいしい！", "literal": "este / ramen / ¡rico!",
             "uso": "en la mesa se dice sin です y funciona como cumplido a quien ha cocinado"},
            {"kind": "vocabulario", "jp": "たのしい", "reading": "たのしい", "meaning": "divertido / agradable (adj-い)", "tipo": "adjetivo",
             "ejemplo": "パーティーは たのしかったです", "literal": "fiesta-TEMA / divertida-fue",
             "uso": "divertido porque tú lo pasas bien. Algo gracioso que da risa es おもしろい"},
            {"kind": "vocabulario", "jp": "むずかしい", "reading": "むずかしい", "meaning": "difícil (adj-い)", "tipo": "adjetivo",
             "ejemplo": "かんじは むずかしいです", "literal": "kanji-TEMA / difícil-es",
             "uso": "difícil de hacer o de entender; su contrario natural es かんたん o やさしい"},
            {"kind": "vocabulario", "jp": "やさしい", "reading": "やさしい", "meaning": "fácil / amable (adj-い)", "tipo": "adjetivo",
             "ejemplo": "せんせいは やさしいです", "literal": "profesor-TEMA / amable-es",
             "uso": "dos sentidos según de qué hables: fácil (un ejercicio) o amable (una persona)"},
            {"kind": "vocabulario", "jp": "たかい", "reading": "たかい", "meaning": "caro / alto (adj-い)", "tipo": "adjetivo",
             "ejemplo": "この とけいは たかいです", "literal": "este / reloj-TEMA / caro-es",
             "uso": "caro y alto son la misma palabra: たかい ビル es un edificio alto"},
            {"kind": "vocabulario", "jp": "やすい", "reading": "やすい", "meaning": "barato (adj-い)", "tipo": "adjetivo",
             "ejemplo": "スーパーは やすいですね", "literal": "súper-TEMA / barato-es-¿verdad?",
             "uso": "barato de precio, sin juicio. 'Barato' de mala calidad es やすっぽい"},
            {"kind": "vocabulario", "jp": "きれい", "reading": "きれい", "meaning": "bonito / limpio (adj-な)", "tipo": "adjetivo",
             "ejemplo": "きれいな へやですね", "literal": "bonita / habitación-es-¿verdad?",
             "uso": "adj-な: necesita な delante del sustantivo. Acaba en い pero NO es adjetivo-い"},
            {"kind": "vocabulario", "jp": "すき", "reading": "すき", "meaning": "que gusta / favorito (adj-な)", "tipo": "adjetivo",
             "ejemplo": "にほんごが すきです", "literal": "japonés-SUJ / gusta-es",
             "uso": "lo que gusta lleva が. No es un verbo: se construye como un adjetivo"},
            {"kind": "vocabulario", "jp": "きらい", "reading": "きらい", "meaning": "que no gusta / odiar (adj-な)", "tipo": "adjetivo",
             "ejemplo": "なっとうが きらいです", "literal": "natto-SUJ / no-gusta-es",
             "uso": "suena fuerte. Para suavizar se dice あまり すきじゃない ('no me gusta mucho')"},
            {"kind": "vocabulario", "jp": "じょうず", "reading": "じょうず", "meaning": "hábil / bueno en algo (adj-な)", "tipo": "adjetivo",
             "ejemplo": "りょうりが じょうずですね", "literal": "cocina-SUJ / hábil-es-¿verdad?",
             "uso": "se usa para elogiar a otro, nunca de uno mismo. De uno mismo se dice とくい"},
            {"kind": "vocabulario", "jp": "へた", "reading": "へた", "meaning": "torpe / malo en algo (adj-な)", "tipo": "adjetivo",
             "ejemplo": "うたが へたです", "literal": "canto-SUJ / torpe-es",
             "uso": "de uno mismo sin problema; dicho de otra persona es de mala educación"},
        ],
    },

    # ── Unidad 4b: Conjugación de adjetivos い y な ──────────────────────────
    {
        "id": "conjugacion_adj",
        "nombre": "Conjugación de adjetivos い y な",
        "funcion": "contar cómo fue algo y cómo no fue: si la comida estaba rica, si el día se hizo duro",
        "frases_hechas": [
            {"jp": "よかった", "uso": "'menos mal', alivio por algo que salió bien"},
            {"jp": "どうだった？", "uso": "'¿qué tal estuvo?', la pregunta con la que empieza cualquier charla"},
            {"jp": "まあまあ", "uso": "'ni fu ni fa', la respuesta honesta y educada"},
            {"jp": "さいこう！", "uso": "'lo mejor', cuando algo te ha encantado de verdad"},
        ],
        "prerequisito": "adjetivos_n5",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜かった", "meaning": "pasado de adj-い: おいしかった, たのしかった, たかかった",
             "ejemplo": "えいがは おもしろかったです", "literal": "película-TEMA / interesante-fue",
             "uso": "quitas い y pones かった. El です va detrás, nunca おもしろいでした"},
            {"kind": "gramatica", "jp": "〜くない", "meaning": "negativo de adj-い: おいしくない, むずかしくない",
             "ejemplo": "この もんだいは むずかしくないです", "literal": "este / problema-TEMA / no-difícil-es",
             "uso": "quitas い y pones くない. いい es irregular: よくない, nunca いくない"},
            {"kind": "gramatica", "jp": "〜くなかった", "meaning": "negativo pasado de adj-い: おいしくなかった",
             "ejemplo": "レストランは たかくなかったです", "literal": "restaurante-TEMA / no-fue-caro",
             "uso": "negativo y pasado encadenados: 〜く + なかった"},
            {"kind": "gramatica", "jp": "〜じゃない", "meaning": "negativo informal de adj-な / sustantivo: きれいじゃない, 学生じゃない",
             "ejemplo": "へやは きれいじゃないです", "literal": "habitación-TEMA / no-bonita-es",
             "uso": "para adj-な y sustantivos. じゃない es la versión hablada de ではない"},
            {"kind": "gramatica", "jp": "〜だった", "meaning": "pasado de adj-な / sustantivo: きれいだった, 学生だった",
             "ejemplo": "がくせいだった とき、よく あそびました", "literal": "estudiante-era / cuando / mucho / jugué",
             "uso": "pasado informal de です; en formal se dice でした"},
            {"kind": "gramatica", "jp": "〜じゃなかった", "meaning": "negativo pasado de adj-な / sustantivo: きれいじゃなかった",
             "ejemplo": "へやは しずかじゃなかったです", "literal": "habitación-TEMA / no-fue-tranquila",
             "uso": "adj-な y sustantivos en negativo pasado; la versión formal es ではありませんでした"},
        ],
    },

    # ── Unidad 4c: Grupos verbales y conjugación base ────────────────────────
    {
        "id": "grupos_verbales",
        "nombre": "Grupos verbales: る動詞, う動詞, irregulares",
        "funcion": "conjugar tú sola cualquier verbo nuevo que oigas, sin tener que preguntar la forma",
        "frases_hechas": [
            {"jp": "なんて言うんですか", "uso": "'¿cómo se dice?', tu salvavidas cuando falta una palabra"},
            {"jp": "どういう意味ですか", "uso": "'¿qué significa?', cuando la oyes pero no la entiendes"},
            {"jp": "ゆっくりお願いします", "uso": "'más despacio, por favor'; funciona con cualquier japonés"},
            {"jp": "わかった！", "uso": "'¡lo pillé!', informal, cuando por fin te sale la conjugación"},
        ],
        "prerequisito": "conjugacion_adj",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "る動詞", "meaning": "grupo 2 (ichidan): terminan en え/い + る. Raíz = quita る: 食べ-, 見-, 起き-, 寝-. Ej: 食べる→食べます→食べて→食べた→食べない",
             "ejemplo": "たべる → たべます → たべて → たべた", "literal": "comer / como / comiendo / comí",
             "uso": "si la sílaba antes de る es え o い, casi siempre es grupo 2. Trampas: かえる, はいる y はしる acaban en る y son grupo 1"},
            {"kind": "gramatica", "jp": "う動詞", "meaning": "grupo 1 (godan): terminan en consonante+u. La columna del hiragana cambia según la forma: 書く→書いて, 飲む→飲んで, 話す→話して, 待つ→待って",
             "ejemplo": "のむ → のみます → のんで → のんだ", "literal": "beber / bebo / bebiendo / bebí",
             "uso": "la forma-て depende de la última sílaba: く→いて, ぐ→いで, む・ぬ・ぶ→んで, る・う・つ→って, す→して"},
            {"kind": "gramatica", "jp": "する活用", "meaning": "irregular する: します・して・した・しない・しなかった (verbo comodín para cualquier sustantivo verbal)",
             "ejemplo": "べんきょうする → べんきょうします → べんきょうして", "literal": "estudiar / estudio / estudiando",
             "uso": "cualquier sustantivo de acción + する se conjuga igual: そうじ, りょこう, でんわ, うんてん"},
            {"kind": "gramatica", "jp": "くる活用", "meaning": "irregular くる: きます・きて・きた・こない・こなかった",
             "ejemplo": "くる → きます → きて → こない", "literal": "venir / vengo / viniendo / no-vengo",
             "uso": "cambia la raíz entera (く→き→こ). No hay regla: se aprende de memoria"},
            {"kind": "gramatica", "jp": "行くのて形", "meaning": "excepción: 行く→行って (no *行いて): única irregularidad de う動詞 en て形",
             "ejemplo": "がっこうに いって、それから かえります", "literal": "escuela-A / voy-y / después / vuelvo",
             "uso": "la única excepción de la forma-て en grupo 1. Se aprende sola porque sale todos los días"},
        ],
    },

    # ── Unidad 5: Forma て ────────────────────────────────────────────────────
    {
        "id": "te_forma",
        "nombre": "Forma て",
        "funcion": "encadenar acciones, pedir cosas con educación y pedir permiso",
        "frases_hechas": [
            {"jp": "ちょっと待って", "uso": "'espera un momento', informal; con ください es más educado"},
            {"jp": "がんばって", "uso": "'ánimo'; literalmente 'esfuérzate', se dice antes de algo difícil"},
            {"jp": "教えてください", "uso": "'dime' / 'enséñame'; se usa muchísimo más que en español"},
            {"jp": "助かりました", "uso": "'me has salvado', para agradecer una ayuda de verdad"},
        ],
        "prerequisito": "grupos_verbales",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜て", "meaning": "forma-て: conecta acciones secuenciales ('y luego')",
             "ejemplo": "おきて、ごはんを たべて、でかけます", "literal": "me-levanto-y / comida-OBJ / como-y / salgo",
             "uso": "encadena acciones en orden. El tiempo verbal lo marca solo el último verbo de la frase"},
            {"kind": "gramatica", "jp": "〜ている", "meaning": "〜て + いる: acción en progreso o estado resultante",
             "ejemplo": "いま ごはんを たべています", "literal": "ahora / comida-OBJ / estoy-comiendo",
             "uso": "para lo que pasa ahora mismo, y también para estados: けっこんしています es 'estoy casado', no 'me estoy casando'. Al hablar se come la い: たべてます"},
            {"kind": "gramatica", "jp": "〜てください", "meaning": "〜て + ください: petición formal 'por favor haz X'",
             "ejemplo": "ちょっと まって ください", "literal": "un-momento / espera / por-favor",
             "uso": "cortés pero directa, casi una instrucción. Para pedir un favor de verdad: 〜てくださいませんか"},
            {"kind": "gramatica", "jp": "〜てもいいですか", "meaning": "pedir permiso: '¿puedo hacer X?'",
             "ejemplo": "ここに すわっても いいですか", "literal": "aquí-EN / aunque-me-siente / ¿está-bien?",
             "uso": "la forma normal de pedir permiso. La respuesta corta que vas a oír es どうぞ"},
            {"kind": "gramatica", "jp": "〜てはいけません", "meaning": "prohibición: 'no se debe hacer X'",
             "ejemplo": "ここで たばこを すっては いけません", "literal": "aquí-EN / tabaco-OBJ / si-fumas / no-vale",
             "uso": "prohibición de norma o de autoridad. Entre amigos se dice 〜ちゃだめ"},
            {"kind": "gramatica", "jp": "〜てから", "meaning": "secuencia: 'después de hacer X'",
             "ejemplo": "ごはんを たべてから、でかけます", "literal": "comida-OBJ / después-de-comer / salgo",
             "uso": "deja claro que la primera acción termina antes de empezar la segunda; más explícito que 〜て a secas"},
        ],
    },

    # ── Unidad 6: Katakana — préstamos frecuentes ─────────────────────────────
    {
        "id": "katakana_comun",
        "nombre": "Katakana — préstamos frecuentes",
        "funcion": "pedir en una cafetería o una tienda y hablar de las cosas de fuera que están en el día a día",
        "frases_hechas": [
            {"jp": "これ、ください", "uso": "señalando la carta o el escaparate; resuelve casi cualquier compra"},
            {"jp": "お願いします", "uso": "cierra cualquier pedido; es el 'por favor' que lo remata"},
            {"jp": "テイクアウトで", "uso": "'para llevar', en cualquier cafetería"},
            {"jp": "いくらですか", "uso": "'¿cuánto es?'"},
        ],
        "prerequisito": "te_forma",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "コーヒー", "reading": "こーひー", "meaning": "café (bebida)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "テレビ", "reading": "てれび", "meaning": "televisión", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "パン", "reading": "ぱん", "meaning": "pan", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "バス", "reading": "ばす", "meaning": "autobús", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "タクシー", "reading": "たくしー", "meaning": "taxi", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "レストラン", "reading": "れすとらん", "meaning": "restaurante", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "ホテル", "reading": "ほてる", "meaning": "hotel", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "スーパー", "reading": "すーぱー", "meaning": "supermercado", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "アイスクリーム", "reading": "あいすくりーむ", "meaning": "helado", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "ケータイ", "reading": "けーたい", "meaning": "teléfono móvil", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "カメラ", "reading": "かめら", "meaning": "cámara (fotográfica)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "インターネット", "reading": "いんたーねっと", "meaning": "internet", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 7: Personas y familia N5 ──────────────────────────────────────
    {
        "id": "familia_personas",
        "nombre": "Personas y familia N5",
        "funcion": "hablar de tu familia y de tus amigos, y preguntar por los de otra persona",
        "frases_hechas": [
            {"jp": "〜さん", "uso": "se pone a todo el mundo menos a uno mismo; olvidarlo suena brusco"},
            {"jp": "うちの…", "uso": "'el mío de casa', al hablar de tu propia familia"},
            {"jp": "お名前は", "uso": "'¿y tú, cómo te llamas?', sin necesidad de más frase"},
            {"jp": "ご家族は", "uso": "'¿y tu familia?'; el ご delante es respeto por lo del otro"},
        ],
        "prerequisito": "katakana_comun",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "人", "reading": "ひと", "meaning": "persona", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "友達", "reading": "ともだち", "meaning": "amigo/a", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "先生", "reading": "せんせい", "meaning": "profesor/a / maestro/a", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "学生", "reading": "がくせい", "meaning": "estudiante", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "お父さん", "reading": "おとうさん", "meaning": "padre (de otra persona)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "お母さん", "reading": "おかあさん", "meaning": "madre (de otra persona)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "兄", "reading": "あに", "meaning": "hermano mayor (propio)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "姉", "reading": "あね", "meaning": "hermana mayor (propia)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "弟", "reading": "おとうと", "meaning": "hermano menor (propio)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "妹", "reading": "いもうと", "meaning": "hermana menor (propia)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "子供", "reading": "こども", "meaning": "niño/a / hijo/a", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 8: Tiempo y lugar N5 ───────────────────────────────────────────
    {
        "id": "tiempo_lugar",
        "nombre": "Tiempo y lugar N5",
        "funcion": "quedar con alguien: decir cuándo y dónde, y preguntar por un sitio",
        "frases_hechas": [
            {"jp": "何時ですか", "uso": "'¿qué hora es?' y también '¿a qué hora?'"},
            {"jp": "ここはどこですか", "uso": "'¿dónde estoy?', cuando te pierdes"},
            {"jp": "また今度", "uso": "'otro día'; posterga sin cerrar la puerta, y a veces significa que no"},
            {"jp": "ちょっと遠いですね", "uso": "'queda un poco lejos'; forma suave de decir que no te apetece"},
        ],
        "prerequisito": "familia_personas",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "今", "reading": "いま", "meaning": "ahora", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "今日", "reading": "きょう", "meaning": "hoy", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "明日", "reading": "あした", "meaning": "mañana", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "昨日", "reading": "きのう", "meaning": "ayer", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "毎日", "reading": "まいにち", "meaning": "todos los días", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "時間", "reading": "じかん", "meaning": "tiempo / hora", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "駅", "reading": "えき", "meaning": "estación de tren", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "学校", "reading": "がっこう", "meaning": "escuela / colegio", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "家", "reading": "うち", "meaning": "casa / hogar", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "店", "reading": "みせ", "meaning": "tienda / establecimiento", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "公園", "reading": "こうえん", "meaning": "parque", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "病院", "reading": "びょういん", "meaning": "hospital", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 9: Comida y bebida ─────────────────────────────────────────────
    {
        "id": "comida_bebida",
        "nombre": "Comida y bebida",
        "funcion": "pedir en un restaurante, decir qué te gusta y qué no, y preguntar el precio",
        "frases_hechas": [
            {"jp": "いただきます", "uso": "antes de comer, siempre, aunque comas sola"},
            {"jp": "ごちそうさまでした", "uso": "al terminar de comer, y al despedirte de quien te invitó"},
            {"jp": "おいしそう", "uso": "al ver la comida, antes de probarla"},
            {"jp": "おかわり", "uso": "'repito', para pedir otra ración o rellenar el vaso"},
        ],
        "prerequisito": "tiempo_lugar",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "ご飯", "reading": "ごはん", "meaning": "arroz cocido / comida", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "水", "reading": "みず", "meaning": "agua", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "お茶", "reading": "おちゃ", "meaning": "té (japonés)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "肉", "reading": "にく", "meaning": "carne", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "魚", "reading": "さかな", "meaning": "pescado / pez", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "野菜", "reading": "やさい", "meaning": "verduras", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "果物", "reading": "くだもの", "meaning": "fruta", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "寿司", "reading": "すし", "meaning": "sushi", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "ラーメン", "reading": "らーめん", "meaning": "ramen (sopa de fideos)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "牛乳", "reading": "ぎゅうにゅう", "meaning": "leche", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "卵", "reading": "たまご", "meaning": "huevo", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "りんご", "reading": "りんご", "meaning": "manzana", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 10: Números ────────────────────────────────────────────────────
    {
        "id": "numeros",
        "nombre": "Números 1-10 y centenas",
        "funcion": "decir cantidades y precios, y entender lo que te dicen en una caja",
        "frases_hechas": [
            {"jp": "いくつですか", "uso": "'¿cuántos?'; también '¿cuántos años tienes?' con お delante"},
            {"jp": "ひとつください", "uso": "'uno, por favor'; el contador ひとつ vale para casi todo"},
            {"jp": "ちょうどです", "uso": "'justo', al pagar con el importe exacto"},
            {"jp": "半分こ", "uso": "'a medias', repartir algo entre dos; muy coloquial"},
        ],
        "prerequisito": "comida_bebida",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "一", "reading": "いち", "meaning": "uno (1)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "二", "reading": "に", "meaning": "dos (2)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "三", "reading": "さん", "meaning": "tres (3)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "四", "reading": "し / よん", "meaning": "cuatro (4)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "五", "reading": "ご", "meaning": "cinco (5)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "六", "reading": "ろく", "meaning": "seis (6)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "七", "reading": "しち / なな", "meaning": "siete (7)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "八", "reading": "はち", "meaning": "ocho (8)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "九", "reading": "きゅう / く", "meaning": "nueve (9)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "十", "reading": "じゅう", "meaning": "diez (10)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "百", "reading": "ひゃく", "meaning": "cien (100)", "tipo": "número"},
            {"kind": "vocabulario", "jp": "千", "reading": "せん", "meaning": "mil (1000)", "tipo": "número"},
        ],
    },

    # ── Unidad 11: Formas negativa y condicional ──────────────────────────────
    {
        "id": "negacion_condicional",
        "nombre": "Negación と〜ない y condicional と〜たら",
        "funcion": "decir lo que no haces y lo que te apetece hacer, y proponer planes con condición",
        "frases_hechas": [
            {"jp": "行きたい！", "uso": "'¡quiero ir!'; el 〜たい se dice solo de uno mismo"},
            {"jp": "べつに", "uso": "'nada en especial' / 'me da igual'; según el tono suena a desgana"},
            {"jp": "じゃあ、そうしよう", "uso": "'venga, hagamos eso', para cerrar un plan"},
            {"jp": "やめとく", "uso": "'paso', decidir no hacer algo sin dar explicaciones"},
        ],
        "prerequisito": "numeros",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜ない", "meaning": "forma negativa casual del verbo (presente)"},
            {"kind": "gramatica", "jp": "〜なかった", "meaning": "forma negativa casual del verbo (pasado)"},
            {"kind": "gramatica", "jp": "〜たい", "meaning": "expresar deseo: 'quiero hacer X'"},
            {"kind": "gramatica", "jp": "〜たいです", "meaning": "expresar deseo (formal): 'quisiera hacer X'"},
            {"kind": "gramatica", "jp": "〜たら", "meaning": "condicional: 'si / cuando ocurre X'"},
            {"kind": "gramatica", "jp": "〜と思う", "meaning": "expresar opinión: 'creo que / pienso que'"},
            {"kind": "gramatica", "jp": "〜から", "meaning": "causal: 'porque X' / 'así que Y'"},
        ],
    },

    # ── Unidad 11b: Forma plain y registro casual ────────────────────────────
    {
        "id": "forma_casual",
        "nombre": "Forma plain y registro casual",
        "funcion": "hablar como con un amigo, sin です ni ます, que es como se habla de verdad fuera del aula",
        "frases_hechas": [
            {"jp": "うん / ううん", "uso": "sí y no informales; solo con gente de confianza, nunca con un jefe"},
            {"jp": "マジで", "uso": "'¿en serio?'; entre amigos, jamás en el trabajo"},
            {"jp": "だよね", "uso": "'ya ves' / 'exacto'; muestra que estáis de acuerdo"},
            {"jp": "めっちゃ", "uso": "'un montón'; nació en Kansai y ya se oye en todas partes"},
        ],
        "prerequisito": "negacion_condicional",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜た", "meaning": "pasado plain form (casual): 食べた, 行った, した, きた — equivale a 〜ました en registro informal"},
            {"kind": "gramatica", "jp": "〜だ", "meaning": "cópula casual / plain form: 学生だ, きれいだ — equivale a です en registro informal"},
            {"kind": "gramatica", "jp": "〜んだ", "meaning": "forma explicativa 'es que…': どうしたの？→ 疲れたんだ. Añade contexto o justificación"},
            {"kind": "gramatica", "jp": "〜けど", "meaning": "adversativo suave 'pero / aunque': おいしかったけど、高かった. También abre contexto sin terminar la idea"},
            {"kind": "gramatica", "jp": "〜し", "meaning": "enumerar razones con tono acumulativo: やさしいし、おもしろいし… ('es amable, además es interesante…')"},
        ],
    },

    # ── Unidad 12: Viaje y transporte ─────────────────────────────────────────
    {
        "id": "viaje_transporte",
        "nombre": "Viaje y transporte",
        "funcion": "moverte por Japón: comprar un billete, preguntar por una línea y pedir direcciones",
        "frases_hechas": [
            {"jp": "駅はどこですか", "uso": "'¿dónde está la estación?'; cámbiale el sustantivo y sirve para todo"},
            {"jp": "次は", "uso": "'¿la siguiente cuál es?', dentro del tren"},
            {"jp": "乗り換えですか", "uso": "'¿hay que hacer transbordo?'"},
            {"jp": "気をつけて", "uso": "'ve con cuidado', al despedir a alguien que se va de viaje"},
        ],
        "prerequisito": "forma_casual",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "電車", "reading": "でんしゃ", "meaning": "tren", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "飛行機", "reading": "ひこうき", "meaning": "avión", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "車", "reading": "くるま", "meaning": "coche / automóvil", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "地下鉄", "reading": "ちかてつ", "meaning": "metro / subte", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "空港", "reading": "くうこう", "meaning": "aeropuerto", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "切符", "reading": "きっぷ", "meaning": "billete / ticket", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "地図", "reading": "ちず", "meaning": "mapa", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "右", "reading": "みぎ", "meaning": "derecha", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "左", "reading": "ひだり", "meaning": "izquierda", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "まっすぐ", "reading": "まっすぐ", "meaning": "recto / todo recto", "tipo": "adverbio"},
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # N5 — Completar Genki I (unidades 13-15)
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Unidad 13: Demostrativos こそあど ─────────────────────────────────────
    {
        "id": "demostrativos",
        "nombre": "Demostrativos こそあど y pronombres de lugar",
        "funcion": "señalar y elegir: esto, eso, aquello, y preguntar dónde está lo que buscas",
        "frases_hechas": [
            {"jp": "これ何ですか", "uso": "'¿qué es esto?'; la frase que más vas a usar en una tienda"},
            {"jp": "あそこです", "uso": "'está allí', señalando algo lejos de los dos"},
            {"jp": "どっちでもいい", "uso": "'cualquiera me vale'"},
            {"jp": "こちらへどうぞ", "uso": "'por aquí, pase'; lo oirás en cualquier restaurante"},
        ],
        "prerequisito": "viaje_transporte",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "これ", "reading": "これ", "meaning": "esto (objeto cercano al hablante)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "それ", "reading": "それ", "meaning": "eso (objeto cercano al oyente)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "あれ", "reading": "あれ", "meaning": "aquello (objeto lejos de ambos)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "どれ", "reading": "どれ", "meaning": "cuál (de tres o más)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "ここ", "reading": "ここ", "meaning": "aquí (lugar del hablante)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "そこ", "reading": "そこ", "meaning": "ahí (lugar del oyente)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "あそこ", "reading": "あそこ", "meaning": "allá (lugar lejos de ambos)", "tipo": "pronombre"},
            {"kind": "vocabulario", "jp": "どこ", "reading": "どこ", "meaning": "dónde", "tipo": "pronombre"},
            {"kind": "gramatica", "jp": "この〜", "meaning": "este/esta + sustantivo (この本 = este libro)"},
            {"kind": "gramatica", "jp": "その〜", "meaning": "ese/esa + sustantivo (その本 = ese libro)"},
            {"kind": "gramatica", "jp": "あの〜", "meaning": "aquel/aquella + sustantivo (あの本 = aquel libro)"},
            {"kind": "gramatica", "jp": "どの〜", "meaning": "qué/cuál + sustantivo (¿どの本? = ¿qué libro?)"},
        ],
    },

    # ── Unidad 14: Cuerpo y salud N5 ─────────────────────────────────────────
    {
        "id": "cuerpo_salud",
        "nombre": "Cuerpo y salud N5",
        "funcion": "decir que algo te duele y contar cómo te encuentras, en casa o en una farmacia",
        "frases_hechas": [
            {"jp": "大丈夫", "uso": "'¿estás bien?' preguntando, y 'estoy bien' respondiendo"},
            {"jp": "お大事に", "uso": "'cuídate', a alguien enfermo; se dice al despedirse"},
            {"jp": "疲れた〜", "uso": "'qué cansancio'; se suelta en voz alta sin dirigirlo a nadie"},
            {"jp": "ちょっと調子が悪い", "uso": "'no me encuentro muy bien', sin dar detalles"},
        ],
        "prerequisito": "demostrativos",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "頭", "reading": "あたま", "meaning": "cabeza", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "目", "reading": "め", "meaning": "ojo/s", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "耳", "reading": "みみ", "meaning": "oreja / oído", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "口", "reading": "くち", "meaning": "boca", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "手", "reading": "て", "meaning": "mano", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "足", "reading": "あし", "meaning": "pie / pierna", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "体", "reading": "からだ", "meaning": "cuerpo", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "痛い", "reading": "いたい", "meaning": "doloroso / me duele (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "薬", "reading": "くすり", "meaning": "medicina / medicamento", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "元気", "reading": "げんき", "meaning": "con energía / estar bien (adj-な)", "tipo": "adjetivo"},
            {"kind": "gramatica", "jp": "〜が痛い", "meaning": "me duele X: あたまが痛い = me duele la cabeza"},
            {"kind": "gramatica", "jp": "〜んです", "meaning": "forma explicativa: da contexto o explicación ('es que...')"},
        ],
    },

    # ── Unidad 15: Comparaciones y deseos N5 ──────────────────────────────────
    {
        "id": "comparaciones_deseos",
        "nombre": "Comparaciones y deseos N5",
        "funcion": "comparar dos cosas, decir cuál prefieres y suavizar una opinión para no imponerla",
        "frases_hechas": [
            {"jp": "どっちがいい", "uso": "'¿cuál prefieres?', entre dos opciones"},
            {"jp": "一番好き", "uso": "'el que más me gusta', de todos"},
            {"jp": "〜のほうがいいかも", "uso": "'quizá mejor…', para sugerir sin imponer"},
            {"jp": "そうかもね", "uso": "'puede ser'; sirve para no llevar la contraria de frente"},
        ],
        "prerequisito": "cuerpo_salud",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜より", "meaning": "comparativo: 'más que X' (AはBよりおおきい = A es más grande que B)"},
            {"kind": "gramatica", "jp": "〜のほうが", "meaning": "preferencia: 'X es mejor' (BよりAのほうが〜 = A es más ~ que B)"},
            {"kind": "gramatica", "jp": "〜ほしい", "meaning": "querer una cosa: 'ほしい' (solo objetos; para acciones usar 〜たい)"},
            {"kind": "gramatica", "jp": "〜すぎる", "meaning": "exceso: 'demasiado X' (たべすぎる = comer demasiado)"},
            {"kind": "gramatica", "jp": "〜でしょう", "meaning": "conjetura formal: 'probablemente...' / '¿no es así?'"},
            {"kind": "gramatica", "jp": "〜かもしれません", "meaning": "posibilidad: 'quizás / puede que...'"},
            {"kind": "gramatica", "jp": "〜でも", "meaning": "adversativo: 'pero / sin embargo' (conector entre oraciones)"},
            {"kind": "vocabulario", "jp": "もっと", "reading": "もっと", "meaning": "más (grado o cantidad): 'más despacio', 'más grande'", "tipo": "adverbio"},
            {"kind": "vocabulario", "jp": "一番", "reading": "いちばん", "meaning": "el más / lo mejor (superlativo): 'el más rápido'", "tipo": "adverbio"},
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # N4 — Genki II (unidades 16-24)
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Unidad 16: Forma potencial N4 ────────────────────────────────────────
    {
        "id": "forma_potencial",
        "nombre": "Forma potencial N4: poder hacer X",
        "funcion": "decir lo que puedes y lo que no puedes hacer, y pedir ayuda cuando algo se te escapa",
        "frases_hechas": [
            {"jp": "できる", "uso": "'¿puedes?' preguntando, 'puedo' respondiendo"},
            {"jp": "ちょっと無理かも", "uso": "'lo veo difícil'; es el 'no' amable de todos los días"},
            {"jp": "手伝ってくれる", "uso": "'¿me echas una mano?'"},
            {"jp": "やってみる", "uso": "'lo intento'; literalmente 'lo hago a ver qué pasa'"},
        ],
        "prerequisito": "comparaciones_deseos",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜られる", "meaning": "potencial de verbos る: 'poder hacer X' (たべられる = puedo comer)"},
            {"kind": "gramatica", "jp": "〜える", "meaning": "potencial de verbos う: 'poder hacer X' (かける = puedo escribir)"},
            {"kind": "vocabulario", "jp": "できる", "reading": "できる", "meaning": "poder / ser capaz de / estar listo", "tipo": "verbo"},
            {"kind": "gramatica", "jp": "〜ことができる", "meaning": "potencial formal: 'ser capaz de hacer X' (〜こと = nominalización)"},
            {"kind": "gramatica", "jp": "〜ようになる", "meaning": "cambio de habilidad: 'llegar a poder / ponerse a hacer X'"},
            {"kind": "gramatica", "jp": "〜ようにする", "meaning": "esfuerzo o hábito: 'procurar hacer X habitualmente'"},
            {"kind": "vocabulario", "jp": "無理", "reading": "むり", "meaning": "imposible / sin sentido / forzado (adj-な / sustantivo)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "必要", "reading": "ひつよう", "meaning": "necesario (adj-な): 〜が必要です", "tipo": "adjetivo"},
        ],
    },

    # ── Unidad 17: Volitiva, intención y propósito N4 ────────────────────────
    {
        "id": "volitiva_proposito",
        "nombre": "Volitiva, intención y propósito N4",
        "funcion": "proponer planes, decir tus intenciones y explicar para qué haces algo",
        "frases_hechas": [
            {"jp": "行こう！", "uso": "'¡vamos!'; volitiva informal, entre amigos"},
            {"jp": "〜しようか", "uso": "'¿hacemos…?', proponer dejando la decisión al otro"},
            {"jp": "そろそろ…", "uso": "'va siendo hora de…'; el aviso suave de que toca irse"},
            {"jp": "また誘って", "uso": "'avísame la próxima', al rechazar un plan sin cerrar la puerta"},
        ],
        "prerequisito": "forma_potencial",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜ましょう", "meaning": "sugerencia formal: 'hagamos X / vamos a X'"},
            {"kind": "gramatica", "jp": "〜よう", "meaning": "volitiva casual: 'vamos a X' / expresar intención propia"},
            {"kind": "gramatica", "jp": "〜つもり", "meaning": "intención / plan: 'tengo pensado hacer X'"},
            {"kind": "gramatica", "jp": "〜ために", "meaning": "propósito: 'para hacer X / con el fin de X'"},
            {"kind": "gramatica", "jp": "〜まで", "meaning": "límite: 'hasta X' (tiempo, lugar o condición)"},
            {"kind": "gramatica", "jp": "〜ながら", "meaning": "simultaneidad: 'haciendo X al mismo tiempo que Y'"},
            {"kind": "vocabulario", "jp": "予定", "reading": "よてい", "meaning": "plan / programa / horario previsto", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "目的", "reading": "もくてき", "meaning": "objetivo / propósito", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 18: Condicionales N4 ───────────────────────────────────────────
    {
        "id": "condicionales_n4",
        "nombre": "Condicionales N4: 〜ば・〜と・〜なら・〜ても",
        "funcion": "hablar de hipótesis y condiciones: si pasa esto, entonces aquello",
        "frases_hechas": [
            {"jp": "もしよかったら", "uso": "'si te apetece'; abre una invitación sin presionar"},
            {"jp": "だったら…", "uso": "'en ese caso…', para reaccionar a lo que acaban de decirte"},
            {"jp": "それなら大丈夫", "uso": "'así sí, sin problema'"},
            {"jp": "〜すればよかった", "uso": "'ojalá hubiera…'; arrepentimiento por lo que no hiciste"},
        ],
        "prerequisito": "volitiva_proposito",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜ば", "meaning": "condicional hipotético: 'si hago X' (たべれば = si como)"},
            {"kind": "gramatica", "jp": "〜と (condicional)", "meaning": "consecuencia natural: 'si haces X, siempre ocurre Y'"},
            {"kind": "gramatica", "jp": "〜なら", "meaning": "condicional contextual: 'si es el caso de X, entonces Y'"},
            {"kind": "gramatica", "jp": "〜ても", "meaning": "concesiva: 'aunque / incluso si X, Y'"},
            {"kind": "gramatica", "jp": "〜なくても", "meaning": "concesiva negativa: 'aunque no hagas X, Y'"},
            {"kind": "gramatica", "jp": "〜のに (contraste)", "meaning": "contraste de expectativa: 'aunque X, Y (resultado inesperado)'"},
            {"kind": "gramatica", "jp": "〜ので", "meaning": "causal suave y formal: 'porque X' (más neutro que 〜から)"},
        ],
    },

    # ── Unidad 19: Experiencia y aspecto N4 ──────────────────────────────────
    {
        "id": "experiencia_aspecto",
        "nombre": "Experiencia y cambio aspectual N4",
        "funcion": "contar experiencias que has tenido y cambios que notas: lo que ya hiciste y lo que se te fue de las manos",
        "frases_hechas": [
            {"jp": "〜たことある", "uso": "'¿has probado alguna vez…?'; abre mil conversaciones"},
            {"jp": "やっちゃった", "uso": "'la he liado'; el 〜てしまう informal, con resignación"},
            {"jp": "忘れてた！", "uso": "'¡se me había olvidado!'"},
            {"jp": "慣れてきた", "uso": "'ya me voy acostumbrando'; el 〜てくる del cambio gradual"},
        ],
        "prerequisito": "condicionales_n4",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜たことがある", "meaning": "experiencia pasada: 'he hecho X alguna vez'"},
            {"kind": "gramatica", "jp": "〜たことがない", "meaning": "falta de experiencia: 'nunca he hecho X'"},
            {"kind": "gramatica", "jp": "〜ていく", "meaning": "cambio progresivo (alejándose): 'ir haciéndose X / seguirá ocurriendo'"},
            {"kind": "gramatica", "jp": "〜てくる", "meaning": "cambio que se acerca (hacia ahora): 'ha venido ocurriendo / empieza a X'"},
            {"kind": "gramatica", "jp": "〜てしまう", "meaning": "completitud o lamento: 'acabar de hacer X / lamentablemente X'"},
            {"kind": "gramatica", "jp": "〜てある", "meaning": "estado resultado de acción intencional: 'X está hecho (a propósito)'"},
            {"kind": "gramatica", "jp": "〜ておく", "meaning": "preparación anticipada: 'hacer X de antemano para cuando sea necesario'"},
        ],
    },

    # ── Unidad 20: Verbos transitivos e intransitivos N4 ─────────────────────
    {
        "id": "transitivos_intransitivos",
        "nombre": "Verbos transitivos e intransitivos N4",
        "funcion": "distinguir lo que tú haces de lo que pasa solo: abrir una puerta o que la puerta se abra",
        "frases_hechas": [
            {"jp": "開いてる", "uso": "'¿está abierto?'; describe el estado, no quién lo abrió"},
            {"jp": "壊れちゃった", "uso": "'se ha roto'; en japonés no se culpa a nadie, la cosa se rompe sola"},
            {"jp": "始まるよ", "uso": "'que empieza', avisando de que va a comenzar algo"},
            {"jp": "閉めておいて", "uso": "'déjalo cerrado, porfa'; dejar algo hecho para después"},
        ],
        "prerequisito": "experiencia_aspecto",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "開く", "reading": "あく", "meaning": "abrirse (intransitivo: la puerta se abre sola)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "開ける", "reading": "あける", "meaning": "abrir algo (transitivo: yo abro la puerta)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "閉まる", "reading": "しまる", "meaning": "cerrarse (intransitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "閉める", "reading": "しめる", "meaning": "cerrar algo (transitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "始まる", "reading": "はじまる", "meaning": "comenzar / empezar (intransitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "始める", "reading": "はじめる", "meaning": "empezar algo (transitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "終わる", "reading": "おわる", "meaning": "terminar / acabar (intransitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "壊れる", "reading": "こわれる", "meaning": "romperse / averiarse (intransitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "壊す", "reading": "こわす", "meaning": "romper algo (transitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "見つかる", "reading": "みつかる", "meaning": "ser encontrado / aparecer (intransitivo)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "見つける", "reading": "みつける", "meaning": "encontrar algo (transitivo)", "tipo": "verbo"},
        ],
    },

    # ── Unidad 21: Vocabulario N4 — Vida cotidiana y sociedad ────────────────
    {
        "id": "vocabulario_n4_vida",
        "nombre": "Vocabulario N4 — Vida cotidiana y sociedad",
        "funcion": "manejarte en el trabajo y en la vida adulta: quedar, llamar, avisar y resolver problemas",
        "frases_hechas": [
            {"jp": "おつかれさまです", "uso": "el saludo del trabajo a cualquier hora: hola, adiós y gracias a la vez"},
            {"jp": "ちょっといいですか", "uso": "'¿tienes un momento?', antes de interrumpir a alguien"},
            {"jp": "確認します", "uso": "'lo compruebo'; la respuesta segura cuando no sabes algo"},
            {"jp": "お先に失礼します", "uso": "'me voy antes que vosotros', al salir de la oficina"},
        ],
        "prerequisito": "transitivos_intransitivos",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "仕事", "reading": "しごと", "meaning": "trabajo / empleo", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "会社", "reading": "かいしゃ", "meaning": "empresa / compañía", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "会議", "reading": "かいぎ", "meaning": "reunión / junta", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "電話", "reading": "でんわ", "meaning": "teléfono / llamada telefónica", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "連絡", "reading": "れんらく", "meaning": "contacto / comunicación", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "問題", "reading": "もんだい", "meaning": "problema / cuestión", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "答え", "reading": "こたえ", "meaning": "respuesta", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "練習", "reading": "れんしゅう", "meaning": "práctica / ejercicio", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "大切", "reading": "たいせつ", "meaning": "importante / valioso (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "便利", "reading": "べんり", "meaning": "conveniente / práctico (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "特別", "reading": "とくべつ", "meaning": "especial / en particular (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "色々", "reading": "いろいろ", "meaning": "varios / diverso / de todo tipo", "tipo": "adjetivo"},
        ],
    },

    # ── Unidad 22: Apariencia y suposición N4 ────────────────────────────────
    {
        "id": "apariencia_suposicion",
        "nombre": "Apariencia y suposición N4: 〜そう・〜らしい・〜ようだ",
        "funcion": "decir cómo parece algo y de qué te has enterado, sin afirmarlo del todo",
        "frases_hechas": [
            {"jp": "〜みたい", "uso": "'parece que…'; la versión hablada de 〜ようだ"},
            {"jp": "らしいよ", "uso": "'según dicen'; marcas que la información no es tuya"},
            {"jp": "たぶんね", "uso": "'probablemente'; deja la puerta abierta a equivocarte"},
            {"jp": "どうやら…", "uso": "'por lo visto…', cuando lo deduces de lo que ves"},
        ],
        "prerequisito": "vocabulario_n4_vida",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜そう", "meaning": "apariencia directa: 'parece que va a X / tiene aspecto de X'"},
            {"kind": "gramatica", "jp": "〜らしい", "meaning": "suposición por evidencia indirecta: 'parece que / se dice que X'"},
            {"kind": "gramatica", "jp": "〜ようだ", "meaning": "deducción por evidencia directa: 'parece que / da la impresión de X'"},
            {"kind": "gramatica", "jp": "〜はずだ", "meaning": "expectativa razonada: 'debería ser X / se supone que X'"},
            {"kind": "gramatica", "jp": "〜わけだ", "meaning": "conclusión lógica: 'eso explica que / por eso X / lógicamente X'"},
            {"kind": "gramatica", "jp": "〜と言われている", "meaning": "referencia general: 'se dice que X / es conocido que X'"},
            {"kind": "vocabulario", "jp": "様子", "reading": "ようす", "meaning": "apariencia / aspecto / situación", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "場合", "reading": "ばあい", "meaning": "caso / situación / circunstancia", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 23: Causativo, pasivo y dar/recibir N4 ─────────────────────────
    {
        "id": "causativo_pasivo",
        "nombre": "Causativo, pasivo y dar/recibir N4",
        "funcion": "hablar de favores: quién hace qué por quién, y pedir permiso para hacerlo tú",
        "frases_hechas": [
            {"jp": "〜てくれてありがとう", "uso": "'gracias por hacerlo'; agradece la acción, no la cosa"},
            {"jp": "〜させてください", "uso": "'déjame hacerlo'; ofrecerte a hacer algo con educación"},
            {"jp": "おごるよ", "uso": "'invito yo'"},
            {"jp": "遠慮しないで", "uso": "'no te cortes'; lo que se dice al que dice que no por educación"},
        ],
        "prerequisito": "apariencia_suposicion",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜させる", "meaning": "causativo: 'hacer que alguien haga X / dejar hacer X'"},
            {"kind": "gramatica", "jp": "〜させてください", "meaning": "petición de permiso: 'permítame hacer X / déjeme hacer X'"},
            {"kind": "gramatica", "jp": "〜られる (pasivo)", "meaning": "pasivo: 'ser hecho X por alguien' (たべられる = ser comido)"},
            {"kind": "gramatica", "jp": "〜に〜られる", "meaning": "pasivo con agente explícito: 'me hacen X a mí / me lo hicieron'"},
            {"kind": "gramatica", "jp": "〜てもらう", "meaning": "recibir un favor: 'X me hace el favor de...'"},
            {"kind": "gramatica", "jp": "〜てあげる", "meaning": "dar un favor: 'hacerle X a alguien (favor que yo doy)'"},
            {"kind": "gramatica", "jp": "〜てくれる", "meaning": "recibir favor (alguien lo hace por mí/nosotros): 'X me hace X'"},
            {"kind": "vocabulario", "jp": "許す", "reading": "ゆるす", "meaning": "perdonar / permitir", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "命令", "reading": "めいれい", "meaning": "orden / mandato", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 24: Honoríficos básicos N4 (敬語 intro) ───────────────────────
    {
        "id": "keigo_intro",
        "nombre": "Honoríficos básicos N4: prefijos お・ご y formas respetuosas",
        "funcion": "hablar con respeto a un desconocido, a un jefe o en una tienda sin sonar raro",
        "frases_hechas": [
            {"jp": "いらっしゃいませ", "uso": "lo que te dicen al entrar en cualquier tienda; no se responde"},
            {"jp": "少々お待ちください", "uso": "'un momento, por favor', de quien atiende"},
            {"jp": "かしこまりました", "uso": "'entendido'; solo lo dice quien sirve al cliente"},
            {"jp": "失礼します", "uso": "al entrar y al salir de una sala, y al colgar el teléfono"},
        ],
        "prerequisito": "causativo_pasivo",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "お〜 / ご〜", "meaning": "prefijos honoríficos: お + 和語 / ご + 漢語 (お名前、ご家族)"},
            {"kind": "gramatica", "jp": "〜でございます", "meaning": "cópula muy formal: equivale a 〜です pero más deferente"},
            {"kind": "gramatica", "jp": "いらっしゃる", "meaning": "verbo honorífico de 'estar / ir / venir': forma respetuosa"},
            {"kind": "gramatica", "jp": "おっしゃる", "meaning": "decir (honorífico): forma respetuosa de 言う"},
            {"kind": "gramatica", "jp": "なさる", "meaning": "hacer (honorífico): forma respetuosa de する"},
            {"kind": "gramatica", "jp": "くださる", "meaning": "dar honorífico hacia abajo: forma respetuosa de くれる"},
            {"kind": "gramatica", "jp": "〜ていただく", "meaning": "recibir favor con humildad: 'le pido que haga X / me hace X (agradecimiento)'"},
            {"kind": "vocabulario", "jp": "失礼", "reading": "しつれい", "meaning": "descortesía / perdone la molestia", "tipo": "sustantivo"},
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # N3 — Tobira / Shin Kanzen Master N3 (unidades 25-30)
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Unidad 25: Keigo avanzado N3 — 尊敬語 y 謙譲語 ───────────────────────
    {
        "id": "keigo_avanzado",
        "nombre": "Keigo avanzado N3: 尊敬語 y 謙譲語",
        "funcion": "moverte en situaciones formales de verdad: presentarte en una empresa, atender y ser atendida",
        "frases_hechas": [
            {"jp": "お世話になっております", "uso": "apertura estándar de cualquier llamada o correo de trabajo"},
            {"jp": "恐れ入りますが", "uso": "'disculpe la molestia, pero…', antes de pedir algo incómodo"},
            {"jp": "ご確認ください", "uso": "'compruébelo, por favor'"},
            {"jp": "お疲れさまでした", "uso": "cierre formal de la jornada, con el お y el でした"},
        ],
        "prerequisito": "keigo_intro",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "ご覧になる", "meaning": "尊敬語 de 見る: 'verlo/mirarlo (usted)' — forma muy respetuosa"},
            {"kind": "gramatica", "jp": "召し上がる", "meaning": "尊敬語 de 食べる・飲む: 'comer / beber (usted)'"},
            {"kind": "gramatica", "jp": "いただく", "meaning": "謙譲語 de もらう・食べる・飲む: 'recibir / comer (yo, humilde)'"},
            {"kind": "gramatica", "jp": "申す", "meaning": "謙譲語 de 言う: 'decir (yo, humilde)'"},
            {"kind": "gramatica", "jp": "参る", "meaning": "謙譲語 de 行く・来る: 'ir / venir (yo, humilde)'"},
            {"kind": "gramatica", "jp": "おる", "meaning": "謙譲語 de いる: 'estar (yo, humilde)'"},
            {"kind": "gramatica", "jp": "存じる", "meaning": "謙譲語 de 知る・思う: 'saber / creer (yo, humilde)'"},
            {"kind": "vocabulario", "jp": "敬語", "reading": "けいご", "meaning": "lenguaje de cortesía / sistema de honoríficos", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "丁寧", "reading": "ていねい", "meaning": "cortés / cuidadoso / formal (adj-な)", "tipo": "adjetivo"},
        ],
    },

    # ── Unidad 26: Causativo-pasivo y compuestos verbales N3 ─────────────────
    {
        "id": "causativo_pasivo_n3",
        "nombre": "Causativo-pasivo y verbos compuestos N3",
        "funcion": "contar lo que te han hecho hacer y lo que no paras de hacer, con matiz de obligación o queja",
        "frases_hechas": [
            {"jp": "残業させられた", "uso": "'me hicieron quedarme a currar'; queja clásica de oficina"},
            {"jp": "〜てばかり", "uso": "'no para de…'; siempre con tono de reproche"},
            {"jp": "しかたない", "uso": "'qué le vamos a hacer'; muy japonés, resignación sin drama"},
            {"jp": "まあ、いいか", "uso": "'bueno, da igual', para soltar el tema"},
        ],
        "prerequisito": "keigo_avanzado",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜させられる", "meaning": "causativo-pasivo: 'me hacen hacer X a la fuerza / me obligan a X'"},
            {"kind": "gramatica", "jp": "〜させてもらう", "meaning": "permiso causativo (yo solicito): 'me permiten hacer X'"},
            {"kind": "gramatica", "jp": "〜ずに", "meaning": "sin hacer X: 'sin comer / sin dormir' (forma más formal que 〜ないで)"},
            {"kind": "gramatica", "jp": "〜てばかりいる", "meaning": "reproche de hábito: 'estar siempre haciendo X / no hacer nada más'"},
            {"kind": "gramatica", "jp": "〜きる", "meaning": "completitud total: 'hacer X por completo / hasta el final'"},
            {"kind": "gramatica", "jp": "〜だす", "meaning": "comienzo repentino: 'ponerse a X de repente'"},
            {"kind": "gramatica", "jp": "〜続ける", "meaning": "continuación: 'seguir haciendo X / continuar X'"},
            {"kind": "vocabulario", "jp": "強制", "reading": "きょうせい", "meaning": "obligación / coacción", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 27: Expresiones de matiz N3 — 〜わけ・〜はず・〜べき ──────────
    {
        "id": "matiz_n3_a",
        "nombre": "Matiz N3: 〜わけ・〜はず・〜べき・〜もの",
        "funcion": "opinar con matiz: lo que debería ser, lo que es imposible y lo que se da por hecho",
        "frases_hechas": [
            {"jp": "そんなわけない", "uso": "'ni de broma'; niega algo tajantemente"},
            {"jp": "〜べきだと思う", "uso": "'creo que habría que…'; suaviza el べき, que solo suena duro"},
            {"jp": "当たり前じゃん", "uso": "'pues claro'; informal, casi con reproche cariñoso"},
            {"jp": "そういうものだ", "uso": "'las cosas son así'; tono reflexivo, de conclusión"},
        ],
        "prerequisito": "causativo_pasivo_n3",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜わけがない", "meaning": "imposibilidad lógica: 'no hay manera de que X / es imposible que X'"},
            {"kind": "gramatica", "jp": "〜わけにはいかない", "meaning": "restricción moral/social: 'no puedo permitirme hacer X / no está bien que X'"},
            {"kind": "gramatica", "jp": "〜はずがない", "meaning": "descarte razonado: 'no puede ser que X / no debería ser X'"},
            {"kind": "gramatica", "jp": "〜べきだ", "meaning": "obligación / deber moral: 'debería hacer X / lo correcto es X'"},
            {"kind": "gramatica", "jp": "〜べきではない", "meaning": "prohibición moral: 'no debería hacer X'"},
            {"kind": "gramatica", "jp": "〜ものだ", "meaning": "generalización / norma natural: 'así son las cosas / es natural que X'"},
            {"kind": "gramatica", "jp": "〜ものではない", "meaning": "reproche de norma: 'no se debe hacer X / no está bien X'"},
            {"kind": "vocabulario", "jp": "当然", "reading": "とうぜん", "meaning": "natural / obvio / como es debido (adj-な / adv)", "tipo": "adjetivo"},
        ],
    },

    # ── Unidad 28: Causa y contraste formal N3 ────────────────────────────────
    {
        "id": "causa_contraste_n3",
        "nombre": "Causa y contraste formal N3: 〜ため・〜ものの・〜によって",
        "funcion": "explicar causas y contrastes en registro formal: informes, noticias y discusiones",
        "frases_hechas": [
            {"jp": "というのは…", "uso": "'lo que pasa es que…', antes de dar la explicación"},
            {"jp": "それに対して", "uso": "'frente a eso'; para contraponer dos datos"},
            {"jp": "にもかかわらず", "uso": "'pese a todo'; escrito y formal, no en la charla del bar"},
            {"jp": "結果として", "uso": "'como resultado', al cerrar un razonamiento"},
        ],
        "prerequisito": "matiz_n3_a",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜ため(に)", "meaning": "causa o propósito formal: 'debido a X / por causa de X' (o 'para X' con verbo)"},
            {"kind": "gramatica", "jp": "〜ものの", "meaning": "concesión formal: 'aunque X, sin embargo Y' (más formal que 〜けど)"},
            {"kind": "gramatica", "jp": "〜くせに", "meaning": "reproche: 'a pesar de X, Y (con tono de crítica)'"},
            {"kind": "gramatica", "jp": "〜にもかかわらず", "meaning": "a pesar de (formal): 'a pesar de X, Y'"},
            {"kind": "gramatica", "jp": "〜に対して", "meaning": "contraste o relación: 'frente a X / hacia X / en contraste con X'"},
            {"kind": "gramatica", "jp": "〜によって", "meaning": "agente o medio formal: 'mediante X / por X / dependiendo de X'"},
            {"kind": "gramatica", "jp": "〜において", "meaning": "localización formal (escrito): 'en el ámbito de X / en X'"},
            {"kind": "vocabulario", "jp": "原因", "reading": "げんいん", "meaning": "causa / motivo (de un problema)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "結果", "reading": "けっか", "meaning": "resultado / consecuencia", "tipo": "sustantivo"},
        ],
    },

    # ── Unidad 29: Conjunciones y decisiones N3 ───────────────────────────────
    {
        "id": "conjunciones_n3",
        "nombre": "Conjunciones y decisiones N3",
        "funcion": "encadenar razones y contar decisiones: por qué haces algo y en qué has quedado",
        "frases_hechas": [
            {"jp": "というか…", "uso": "'o más bien…', para corregirte a media frase"},
            {"jp": "ってことは", "uso": "'¿eso significa que…?', al sacar una conclusión"},
            {"jp": "ことにした", "uso": "'he decidido que…'; la decisión es tuya"},
            {"jp": "一方で", "uso": "'por otro lado'; ordena las dos caras de un asunto"},
        ],
        "prerequisito": "causa_contraste_n3",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜一方で", "meaning": "contraste: 'por un lado X, por otro Y / mientras que X, Y'"},
            {"kind": "gramatica", "jp": "〜上に", "meaning": "adición con agravante: 'además de X (que ya es mucho), también Y'"},
            {"kind": "gramatica", "jp": "〜というのは", "meaning": "explicación de definición: 'lo que se llama X significa...'"},
            {"kind": "gramatica", "jp": "〜かどうか", "meaning": "duda indirecta: 'si X o no X / no sé si X'"},
            {"kind": "gramatica", "jp": "〜ということ", "meaning": "nominalización/cita: 'el hecho de que X / lo de X'"},
            {"kind": "gramatica", "jp": "〜ことにする", "meaning": "decisión personal: 'decidir hacer X / voy a hacer X (decisión propia)'"},
            {"kind": "gramatica", "jp": "〜ことになる", "meaning": "resultado o decisión externa: 'resulta que X / se ha decidido que X'"},
        ],
    },

    # ── Unidad 30: Vocabulario N3 — Abstracto, emocional y formal ────────────
    {
        "id": "vocabulario_n3",
        "nombre": "Vocabulario N3 — Abstracto, emocional y formal",
        "funcion": "hablar de lo que sientes y de lo que piensas: opiniones, experiencias y situaciones abstractas",
        "frases_hechas": [
            {"jp": "気にしないで", "uso": "'no le des importancia', a quien se disculpa o se agobia"},
            {"jp": "自信ない", "uso": "'no me veo capaz'; se dice mucho más que en español"},
            {"jp": "なんとなく", "uso": "'sin razón concreta', 'porque sí'; respuesta comodín"},
            {"jp": "気持ちわかる", "uso": "'te entiendo'; literalmente 'entiendo tu sentimiento'"},
        ],
        "prerequisito": "conjunciones_n3",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "気持ち", "reading": "きもち", "meaning": "sentimiento / emoción / cómo te sientes", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "意見", "reading": "いけん", "meaning": "opinión", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "経験", "reading": "けいけん", "meaning": "experiencia", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "関係", "reading": "かんけい", "meaning": "relación / conexión", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "影響", "reading": "えいきょう", "meaning": "influencia / impacto", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "状況", "reading": "じょうきょう", "meaning": "situación / estado de las cosas", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "判断", "reading": "はんだん", "meaning": "juicio / decisión / valoración", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "努力", "reading": "どりょく", "meaning": "esfuerzo", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "成功", "reading": "せいこう", "meaning": "éxito", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "失敗", "reading": "しっぱい", "meaning": "fracaso / error", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "不安", "reading": "ふあん", "meaning": "ansiedad / inquietud (adj-な / sustantivo)", "tipo": "sustantivo"},
            {"kind": "vocabulario", "jp": "自信", "reading": "じしん", "meaning": "confianza en uno mismo / seguridad", "tipo": "sustantivo"},
        ],
    },
]


# Los 103 kanji N5 entran como bloque de cierre del N5, justo antes del N4: para
# entonces Laura ya sabe decir de viva voz casi todo lo que los kanji escriben.
# Los caracteres que otra unidad ya enseña (一〜千, 人, 目, 手…) se filtran, para
# que el SRS no lleve dos fichas del mismo carácter.
_YA_EN_TEMARIO = {item["jp"] for unit in CURRICULUM for item in unit["items"]}
_UNIDADES_KANJI = unidades_kanji(_YA_EN_TEMARIO, prerequisito="comparaciones_deseos")
_CORTE = next(i for i, u in enumerate(CURRICULUM) if u["id"] == "forma_potencial")
CURRICULUM[_CORTE]["prerequisito"] = _UNIDADES_KANJI[-1]["id"]
CURRICULUM[_CORTE:_CORTE] = _UNIDADES_KANJI

UMBRAL_PREREQ_DEFECTO = 0.75

# Índice jp → ítem del temario, para enriquecer el FOCO (ejemplo / literal / uso)
# también en los ítems de repaso, que vienen de la BD y no traen esos campos.
ITEM_POR_JP = {item["jp"]: item for unit in CURRICULUM for item in unit["items"]}


def _snapshot_reps(jap_memory):
    """Un solo viaje a la BD: {(kind, jp): reps} de todo lo que Laura ya tiene.

    El recorrido del temario preguntaba ítem a ítem (~360 conexiones por turno);
    con la foto en memoria son dos consultas y una conexión.
    """
    with jap_memory._conectar() as conn:
        snap = {("vocabulario", w): r or 0
                for w, r in conn.execute("SELECT word, reps FROM japanese_vocabulary")}
        snap.update({("gramatica", g): r or 0
                     for g, r in conn.execute("SELECT grammar_point, reps FROM japanese_grammar")})
    return snap


def _clave(item):
    return ("vocabulario" if item["kind"] == "vocabulario" else "gramatica", item["jp"])


def _fraccion_aprendida(unit_id, reps):
    """Fracción de ítems de una unidad que el alumno tiene aprendidos (reps >= 2)."""
    unit = next((u for u in CURRICULUM if u["id"] == unit_id), None)
    if not unit or not unit["items"]:
        return 0.0
    aprendidas = sum(1 for item in unit["items"] if reps.get(_clave(item), 0) >= 2)
    return aprendidas / len(unit["items"])


def _gate_met(unit, reps):
    prereq = unit.get("prerequisito")
    if not prereq:
        return True
    return _fraccion_aprendida(prereq, reps) >= unit.get("umbral_prereq", UMBRAL_PREREQ_DEFECTO)


def unidad_actual(jap_memory):
    """La unidad que Laura tiene abierta: la primera con la puerta cumplida que
    aún no está aprendida del todo. Si las tiene todas, la última abierta."""
    reps = _snapshot_reps(jap_memory)
    abierta = None
    for unit in CURRICULUM:
        if not _gate_met(unit, reps):
            break
        abierta = unit
        if _fraccion_aprendida(unit["id"], reps) < 1.0:
            return unit
    return abierta


def siguiente_items_nuevos(jap_memory, n=1):
    """Devuelve hasta n ítems del currículo que Laura aún no tiene y cuyas
    puertas de prerequisito estén cumplidas.

    Retorna lista de dicts {kind, jp, reading?, meaning, tipo?, unidad}.
    """
    reps = _snapshot_reps(jap_memory)
    result = []
    seen = set()  # ítems elegidos en esta llamada pero aún no en BD
    for unit in CURRICULUM:
        if not _gate_met(unit, reps):
            continue
        for item in unit["items"]:
            if item["jp"] in seen or _clave(item) in reps:
                continue
            result.append({**item, "unidad": unit["nombre"]})
            seen.add(item["jp"])
            if len(result) >= n:
                return result
    return result


def siguiente_item_nuevo(jap_memory):
    """Compatibilidad: devuelve un único ítem nuevo o None."""
    items = siguiente_items_nuevos(jap_memory, 1)
    return items[0] if items else None
