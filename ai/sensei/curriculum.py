"""Espina dorsal del temario de japonés y selector del próximo ítem nuevo."""

CURRICULUM = [
    # ── Unidad 0: Saludos y expresiones básicas (sin puerta) ─────────────────
    {
        "id": "saludos_basicos",
        "nombre": "Saludos y expresiones básicas",
        "prerequisito": None,
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "はい", "reading": "はい", "meaning": "sí", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "いいえ", "reading": "いいえ", "meaning": "no", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "ありがとう", "reading": "ありがとう", "meaning": "gracias", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "すみません", "reading": "すみません", "meaning": "disculpe / perdón", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "こんにちは", "reading": "こんにちは", "meaning": "hola (durante el día)", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "おはようございます", "reading": "おはようございます", "meaning": "buenos días", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "こんばんは", "reading": "こんばんは", "meaning": "buenas noches (saludo)", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "さようなら", "reading": "さようなら", "meaning": "adiós", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "おやすみなさい", "reading": "おやすみなさい", "meaning": "buenas noches (al dormir)", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "わかりました", "reading": "わかりました", "meaning": "entendido / comprendido", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "わかりません", "reading": "わかりません", "meaning": "no entiendo", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "もう一度", "reading": "もういちど", "meaning": "una vez más / repetir", "tipo": "expresión"},
            {"kind": "vocabulario", "jp": "ゆっくり", "reading": "ゆっくり", "meaning": "despacio / lentamente", "tipo": "adverbio"},
        ],
    },

    # ── Unidad 1: Partículas básicas ─────────────────────────────────────────
    {
        "id": "particulas_basicas",
        "nombre": "Partículas básicas は・が・を・に",
        "prerequisito": "saludos_basicos",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "は", "meaning": "partícula de tema (wa): marca el tema de la oración"},
            {"kind": "gramatica", "jp": "が", "meaning": "partícula de sujeto: enfatiza quién realiza la acción"},
            {"kind": "gramatica", "jp": "を", "meaning": "partícula de objeto directo (wo): marca el complemento directo"},
            {"kind": "gramatica", "jp": "に", "meaning": "partícula de dirección / destino / tiempo / receptor"},
            {"kind": "gramatica", "jp": "で", "meaning": "partícula de lugar de acción o medio / herramienta"},
            {"kind": "gramatica", "jp": "の", "meaning": "partícula posesiva: A の B → 'B de A'"},
            {"kind": "gramatica", "jp": "も", "meaning": "partícula inclusiva: 'también' / 'tampoco'"},
            {"kind": "gramatica", "jp": "と", "meaning": "partícula 'y' (sustantivos) / 'con' (compañía)"},
            {"kind": "gramatica", "jp": "か", "meaning": "partícula interrogativa: convierte la oración en pregunta"},
            {"kind": "gramatica", "jp": "ね", "meaning": "partícula final: busca confirmación ('¿verdad?', '¿no?')"},
            {"kind": "gramatica", "jp": "よ", "meaning": "partícula final: afirma algo que el oyente no sabe"},
        ],
    },

    # ── Unidad 2: Cópula です y forma ます ────────────────────────────────────
    {
        "id": "desu_masu",
        "nombre": "Cópula です y forma ～ます",
        "prerequisito": "particulas_basicas",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "です", "meaning": "cópula formal: 'es / son' (afirmativo presente)"},
            {"kind": "gramatica", "jp": "ではありません", "meaning": "cópula formal negativa: 'no es / no son'"},
            {"kind": "gramatica", "jp": "でした", "meaning": "cópula formal pasada: 'era / fueron'"},
            {"kind": "gramatica", "jp": "〜ます", "meaning": "terminación verbal formal presente / futuro afirmativo"},
            {"kind": "gramatica", "jp": "〜ません", "meaning": "terminación verbal formal presente negativa"},
            {"kind": "gramatica", "jp": "〜ました", "meaning": "terminación verbal formal pasada afirmativa"},
            {"kind": "gramatica", "jp": "〜ませんでした", "meaning": "terminación verbal formal pasada negativa"},
            {"kind": "gramatica", "jp": "〜ますか", "meaning": "pregunta formal sobre acción: '¿hace X?'"},
        ],
    },

    # ── Unidad 3: Verbos esenciales N5 ───────────────────────────────────────
    {
        "id": "verbos_n5",
        "nombre": "Verbos esenciales N5",
        "prerequisito": "desu_masu",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "食べる", "reading": "たべる", "meaning": "comer", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "飲む", "reading": "のむ", "meaning": "beber", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "行く", "reading": "いく", "meaning": "ir", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "来る", "reading": "くる", "meaning": "venir", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "する", "reading": "する", "meaning": "hacer", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "見る", "reading": "みる", "meaning": "ver / mirar", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "聞く", "reading": "きく", "meaning": "escuchar / preguntar", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "話す", "reading": "はなす", "meaning": "hablar", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "書く", "reading": "かく", "meaning": "escribir", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "読む", "reading": "よむ", "meaning": "leer", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "買う", "reading": "かう", "meaning": "comprar", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "帰る", "reading": "かえる", "meaning": "regresar / volver a casa", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "起きる", "reading": "おきる", "meaning": "levantarse / despertarse", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "寝る", "reading": "ねる", "meaning": "dormir / acostarse", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "分かる", "reading": "わかる", "meaning": "entender / comprender", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "ある", "reading": "ある", "meaning": "haber / existir (objetos inanimados)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "いる", "reading": "いる", "meaning": "estar / existir (personas y animales)", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "思う", "reading": "おもう", "meaning": "pensar / creer", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "待つ", "reading": "まつ", "meaning": "esperar", "tipo": "verbo"},
            {"kind": "vocabulario", "jp": "持つ", "reading": "もつ", "meaning": "tener / sostener / llevar", "tipo": "verbo"},
        ],
    },

    # ── Unidad 4: Adjetivos N5 ───────────────────────────────────────────────
    {
        "id": "adjetivos_n5",
        "nombre": "Adjetivos N5 (い y な)",
        "prerequisito": "verbos_n5",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "vocabulario", "jp": "大きい", "reading": "おおきい", "meaning": "grande (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "小さい", "reading": "ちいさい", "meaning": "pequeño (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "新しい", "reading": "あたらしい", "meaning": "nuevo (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "古い", "reading": "ふるい", "meaning": "viejo / antiguo (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "おいしい", "reading": "おいしい", "meaning": "delicioso / rico (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "たのしい", "reading": "たのしい", "meaning": "divertido / agradable (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "むずかしい", "reading": "むずかしい", "meaning": "difícil (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "やさしい", "reading": "やさしい", "meaning": "fácil / amable (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "たかい", "reading": "たかい", "meaning": "caro / alto (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "やすい", "reading": "やすい", "meaning": "barato (adj-い)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "きれい", "reading": "きれい", "meaning": "bonito / limpio (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "すき", "reading": "すき", "meaning": "que gusta / favorito (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "きらい", "reading": "きらい", "meaning": "que no gusta / odiar (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "じょうず", "reading": "じょうず", "meaning": "hábil / bueno en algo (adj-な)", "tipo": "adjetivo"},
            {"kind": "vocabulario", "jp": "へた", "reading": "へた", "meaning": "torpe / malo en algo (adj-な)", "tipo": "adjetivo"},
        ],
    },

    # ── Unidad 4b: Conjugación de adjetivos い y な ──────────────────────────
    {
        "id": "conjugacion_adj",
        "nombre": "Conjugación de adjetivos い y な",
        "prerequisito": "adjetivos_n5",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜かった", "meaning": "pasado de adj-い: おいしかった, たのしかった, たかかった"},
            {"kind": "gramatica", "jp": "〜くない", "meaning": "negativo de adj-い: おいしくない, むずかしくない"},
            {"kind": "gramatica", "jp": "〜くなかった", "meaning": "negativo pasado de adj-い: おいしくなかった"},
            {"kind": "gramatica", "jp": "〜じゃない", "meaning": "negativo informal de adj-な / sustantivo: きれいじゃない, 学生じゃない"},
            {"kind": "gramatica", "jp": "〜だった", "meaning": "pasado de adj-な / sustantivo: きれいだった, 学生だった"},
            {"kind": "gramatica", "jp": "〜じゃなかった", "meaning": "negativo pasado de adj-な / sustantivo: きれいじゃなかった"},
        ],
    },

    # ── Unidad 4c: Grupos verbales y conjugación base ────────────────────────
    {
        "id": "grupos_verbales",
        "nombre": "Grupos verbales: る動詞, う動詞, irregulares",
        "prerequisito": "conjugacion_adj",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "る動詞", "meaning": "grupo 2 (ichidan): terminan en え/い + る. Raíz = quita る: 食べ-, 見-, 起き-, 寝-. Ej: 食べる→食べます→食べて→食べた→食べない"},
            {"kind": "gramatica", "jp": "う動詞", "meaning": "grupo 1 (godan): terminan en consonante+u. La columna del hiragana cambia según la forma: 書く→書いて, 飲む→飲んで, 話す→話して, 待つ→待って"},
            {"kind": "gramatica", "jp": "する活用", "meaning": "irregular する: します・して・した・しない・しなかった (verbo comodín para cualquier sustantivo verbal)"},
            {"kind": "gramatica", "jp": "くる活用", "meaning": "irregular くる: きます・きて・きた・こない・こなかった"},
            {"kind": "gramatica", "jp": "行くのて形", "meaning": "excepción: 行く→行って (no *行いて): única irregularidad de う動詞 en て形"},
        ],
    },

    # ── Unidad 5: Forma て ────────────────────────────────────────────────────
    {
        "id": "te_forma",
        "nombre": "Forma て",
        "prerequisito": "grupos_verbales",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜て", "meaning": "forma-て: conecta acciones secuenciales ('y luego')"},
            {"kind": "gramatica", "jp": "〜ている", "meaning": "〜て + いる: acción en progreso o estado resultante"},
            {"kind": "gramatica", "jp": "〜てください", "meaning": "〜て + ください: petición formal 'por favor haz X'"},
            {"kind": "gramatica", "jp": "〜てもいいですか", "meaning": "pedir permiso: '¿puedo hacer X?'"},
            {"kind": "gramatica", "jp": "〜てはいけません", "meaning": "prohibición: 'no se debe hacer X'"},
            {"kind": "gramatica", "jp": "〜てから", "meaning": "secuencia: 'después de hacer X'"},
        ],
    },

    # ── Unidad 6: Katakana — préstamos frecuentes ─────────────────────────────
    {
        "id": "katakana_comun",
        "nombre": "Katakana — préstamos frecuentes",
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
        "prerequisito": "causa_contraste_n3",
        "umbral_prereq": 0.75,
        "items": [
            {"kind": "gramatica", "jp": "〜し", "meaning": "enumeración de razones: 'además de X, también Y / tanto X como Y'"},
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


UMBRAL_PREREQ_DEFECTO = 0.75


def _fraccion_aprendida(jap_memory, unit_id):
    """Fracción de ítems de una unidad que el alumno tiene aprendidos (reps >= 2)."""
    unit = next((u for u in CURRICULUM if u["id"] == unit_id), None)
    if not unit or not unit["items"]:
        return 0.0
    aprendidas = 0
    with jap_memory._conectar() as conn:
        for item in unit["items"]:
            if item["kind"] == "vocabulario":
                row = conn.execute(
                    "SELECT reps FROM japanese_vocabulary WHERE word = ?", (item["jp"],)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT reps FROM japanese_grammar WHERE grammar_point = ?", (item["jp"],)
                ).fetchone()
            if row and (row[0] or 0) >= 2:
                aprendidas += 1
    return aprendidas / len(unit["items"])


def _gate_met(jap_memory, unit):
    prereq = unit.get("prerequisito")
    if not prereq:
        return True
    return _fraccion_aprendida(jap_memory, prereq) >= unit.get("umbral_prereq", UMBRAL_PREREQ_DEFECTO)


def _already_taught(jap_memory, item):
    """Devuelve True si el ítem ya está registrado en la BD de Laura."""
    with jap_memory._conectar() as conn:
        if item["kind"] == "vocabulario":
            row = conn.execute(
                "SELECT id FROM japanese_vocabulary WHERE word = ?",
                (item["jp"],),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM japanese_grammar WHERE grammar_point = ?",
                (item["jp"],),
            ).fetchone()
    return row is not None


def siguiente_items_nuevos(jap_memory, n=1):
    """Devuelve hasta n ítems del currículo que Laura aún no tiene y cuyas
    puertas de prerequisito estén cumplidas.

    Retorna lista de dicts {kind, jp, reading?, meaning, tipo?, unidad}.
    """
    result = []
    seen = set()  # ítems elegidos en esta llamada pero aún no en BD
    for unit in CURRICULUM:
        if not _gate_met(jap_memory, unit):
            continue
        for item in unit["items"]:
            if item["jp"] in seen:
                continue
            if not _already_taught(jap_memory, item):
                result.append({**item, "unidad": unit["nombre"]})
                seen.add(item["jp"])
                if len(result) >= n:
                    return result
    return result


def siguiente_item_nuevo(jap_memory):
    """Compatibilidad: devuelve un único ítem nuevo o None."""
    items = siguiente_items_nuevos(jap_memory, 1)
    return items[0] if items else None
