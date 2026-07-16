"""Espina dorsal del temario de japonés y selector del próximo ítem nuevo."""

# Secuencia: hiragana → katakana → partículas → です/ます → verbos N5
#            → て-forma → vocabulario N5 → temas cotidianos

CURRICULUM = [
    # ── Unidad 0: Saludos y expresiones básicas (sin puerta) ─────────────────
    {
        "id": "saludos_basicos",
        "nombre": "Saludos y expresiones básicas",
        "skill_requerida": None,
        "umbral": 0,
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

    # ── Unidad 1: Partículas básicas (requiere hiragana ≥ 40) ────────────────
    {
        "id": "particulas_basicas",
        "nombre": "Partículas básicas は・が・を・に",
        "skill_requerida": "hiragana",
        "umbral": 40,
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

    # ── Unidad 2: Cópula です y forma ます (requiere hiragana ≥ 50) ───────────
    {
        "id": "desu_masu",
        "nombre": "Cópula です y forma ～ます",
        "skill_requerida": "hiragana",
        "umbral": 50,
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

    # ── Unidad 3: Verbos esenciales N5 (requiere particulas ≥ 40) ───────────
    {
        "id": "verbos_n5",
        "nombre": "Verbos esenciales N5",
        "skill_requerida": "particulas",
        "umbral": 40,
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

    # ── Unidad 4: Adjetivos N5 (requiere desu_masu ≥ 50 → proxy: hiragana ≥ 60) ─
    {
        "id": "adjetivos_n5",
        "nombre": "Adjetivos N5 (い y な)",
        "skill_requerida": "hiragana",
        "umbral": 60,
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

    # ── Unidad 5: Forma て (requiere particulas ≥ 60) ─────────────────────────
    {
        "id": "te_forma",
        "nombre": "Forma て",
        "skill_requerida": "particulas",
        "umbral": 60,
        "items": [
            {"kind": "gramatica", "jp": "〜て", "meaning": "forma-て: conecta acciones secuenciales ('y luego')"},
            {"kind": "gramatica", "jp": "〜ている", "meaning": "〜て + いる: acción en progreso o estado resultante"},
            {"kind": "gramatica", "jp": "〜てください", "meaning": "〜て + ください: petición formal 'por favor haz X'"},
            {"kind": "gramatica", "jp": "〜てもいいですか", "meaning": "pedir permiso: '¿puedo hacer X?'"},
            {"kind": "gramatica", "jp": "〜てはいけません", "meaning": "prohibición: 'no se debe hacer X'"},
            {"kind": "gramatica", "jp": "〜てから", "meaning": "secuencia: 'después de hacer X'"},
        ],
    },

    # ── Unidad 6: Katakana — préstamos frecuentes (requiere katakana ≥ 30) ───
    {
        "id": "katakana_comun",
        "nombre": "Katakana — préstamos frecuentes",
        "skill_requerida": "katakana",
        "umbral": 30,
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

    # ── Unidad 7: Personas y familia N5 (requiere particulas ≥ 50) ───────────
    {
        "id": "familia_personas",
        "nombre": "Personas y familia N5",
        "skill_requerida": "particulas",
        "umbral": 50,
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

    # ── Unidad 8: Tiempo y lugar N5 (requiere particulas ≥ 50) ──────────────
    {
        "id": "tiempo_lugar",
        "nombre": "Tiempo y lugar N5",
        "skill_requerida": "particulas",
        "umbral": 50,
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

    # ── Unidad 9: Comida y bebida (requiere verbos N5 → proxy: particulas ≥ 60) ─
    {
        "id": "comida_bebida",
        "nombre": "Comida y bebida",
        "skill_requerida": "particulas",
        "umbral": 60,
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

    # ── Unidad 10: Números (requiere hiragana ≥ 50) ──────────────────────────
    {
        "id": "numeros",
        "nombre": "Números 1-10 y centenas",
        "skill_requerida": "hiragana",
        "umbral": 50,
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

    # ── Unidad 11: Formas negativa y condicional (requiere gramatica ≥ 50) ───
    {
        "id": "negacion_condicional",
        "nombre": "Negación と〜ない y condicional と〜たら",
        "skill_requerida": "gramatica",
        "umbral": 50,
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

    # ── Unidad 12: Temas cotidianos — viaje y transporte (requiere katakana ≥ 50) ─
    {
        "id": "viaje_transporte",
        "nombre": "Viaje y transporte",
        "skill_requerida": "katakana",
        "umbral": 50,
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
]


def _gate_met(jap_memory, unit):
    """Devuelve True si la puerta de competencia de la unidad está cumplida."""
    if unit["skill_requerida"] is None:
        return True
    with jap_memory._conectar() as conn:
        row = conn.execute(
            "SELECT percentage FROM japanese_skills WHERE skill = ?",
            (unit["skill_requerida"],),
        ).fetchone()
    return (row[0] if row else 0) >= unit["umbral"]


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


def siguiente_item_nuevo(jap_memory):
    """Devuelve el primer ítem del currículo que Laura aún no tiene y cuya
    puerta de competencia esté cumplida.

    Retorna dict con {kind, jp, reading?, meaning, tipo?, unidad} o None si
    todas las unidades accesibles están completas.
    """
    for unit in CURRICULUM:
        if not _gate_met(jap_memory, unit):
            continue
        for item in unit["items"]:
            if not _already_taught(jap_memory, item):
                return {**item, "unidad": unit["nombre"]}
    return None
