"""Espina dorsal del temario de japonés y selector del próximo ítem nuevo."""

from ai.sensei.kanji_n5 import unidades_kanji

CURRICULUM = [
  {
    'id': 'saludos_basicos',
    'nombre': 'Saludos y expresiones básicas',
    'funcion': 'saludar y despedirte a cualquier hora, dar las gracias, disculparte y decir que no has entendido',
    'frases_hechas': [
      {'jp': 'おつかれさま', 'uso': 'a alguien que acaba algo: un curro, un examen, una mudanza'},
      {'jp': 'よろしくお願いします', 'uso': "al conocer a alguien y al pedir algo: 'cuento contigo'"},
      {'jp': 'なるほど', 'uso': "cuando algo te encaja: 'ah, ya veo'"},
      {'jp': 'ちょっと…', 'uso': 'para decir que no sin decir no'}
    ],
    'prerequisito': None,
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'ああ',
        'reading': 'ああ',
        'meaning': '¡ah! / ¡oh!',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Ah' de caer en algo; alargado (「ああ…」) marca duda, fastidio o resignación."
      },
      {
        'kind': 'vocabulario',
        'jp': 'いいえ',
        'reading': 'いいえ',
        'meaning': 'no',
        'tipo': 'expresión',
        'ejemplo': 'いいえ、ちがいます',
        'literal': 'no / es-diferente',
        'uso': 'negar con claridad; en el día a día se suaviza con ううん o con ちょっと…, porque un いいえ seco suena cortante'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ええ',
        'reading': 'ええ',
        'meaning': 'sí',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Sí' en tono algo más formal o de escucha atenta que 「うん」; menos tajante que 「はい」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'お～',
        'reading': 'お～',
        'meaning': 'prefijo honorífico お- (お茶, お金…)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': 'Prefijo de cortesía; obligatorio en algunas palabras (「お茶」「お金」「お風呂」) y opcional en otras. Abusar de él suena remilgado, sobre todo en un hombre.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'さあ',
        'reading': 'さあ',
        'meaning': 'vamos, bueno…',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Para animar ('venga, vamos') o para expresar que no se sabe: 「さあ…」 encogiéndose de hombros."
      },
      {
        'kind': 'vocabulario',
        'jp': 'そう; そうです',
        'reading': 'そう / そうです',
        'meaning': 'así es, sí; parece que',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "「そうです」 confirma lo dicho por el otro ('así es'). Tras una frase entera, 「～そうです」 es 'dicen que ~'. 「そう？」 = '¿ah, sí?'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'どうぞ',
        'reading': 'どうぞ',
        'meaning': 'por favor, adelante',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Se dice al ceder algo: el turno, el paso, un asiento, una taza de té. Responde a una petición: 'adelante', 'sírvase'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'どうも',
        'reading': 'どうも',
        'meaning': 'gracias; de algún modo',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Comodín: 'gracias' (「どうもありがとう」 acortado), 'hola', 'perdona' o 'no sé por qué' (「どうも調子が悪い」). Solo, es un agradecimiento rápido e informal."
      },
      {
        'kind': 'vocabulario',
        'jp': 'はい',
        'reading': 'はい',
        'meaning': 'sí',
        'tipo': 'expresión',
        'ejemplo': 'はい、そうです',
        'literal': 'sí / así-es',
        'uso': "confirmar; también es el '¿sí?' de coger el teléfono o de responder cuando te llaman"
      },
      {
        'kind': 'vocabulario',
        'jp': 'もしもし',
        'reading': 'もしもし',
        'meaning': '¿diga? (al descolgar el teléfono)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': 'Casi solo al teléfono, al descolgar o si se corta la voz. En persona, para llamar a un desconocido, mejor 「すみません」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '大丈夫',
        'reading': 'だいじょうぶ',
        'meaning': 'está bien, no pasa nada',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Sirve para 'estoy bien' y también para rechazar con suavidad: ante 「コーヒーいかがですか」, 「大丈夫です」 significa 'no, gracias'."
      },
      {
        'kind': 'vocabulario',
        'jp': '皆さん',
        'reading': 'みなさん',
        'meaning': 'todos ustedes',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "Para dirigirse con respeto a un grupo ('todos ustedes'). Entre amigos se dice 「みんな」."
      },
      {
        'kind': 'vocabulario',
        'jp': '結構',
        'reading': 'けっこう',
        'meaning': 'estupendo; suficiente',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Dos caras: 'estupendo, de acuerdo' al aprobar algo y 'no, gracias' al rechazar un ofrecimiento; el tono lo desambigua. Como adverbio, 'bastante'."
      },
      {
        'kind': 'vocabulario',
        'jp': '～さん',
        'reading': '～さん',
        'meaning': 'señor/a ~ (detrás de un nombre)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': 'Detrás del apellido o el nombre; nunca sobre uno mismo. Con cercanía o niños, 「くん」/「ちゃん」; en contexto muy formal, 「さま」.'
      }
    ]
  },
  {
    'id': 'desu_masu',
    'nombre': 'Cópula です y forma ～ます',
    'funcion': 'presentarte, decir qué eres y qué haces cada día, y preguntarle lo mismo a alguien',
    'frases_hechas': [
      {'jp': 'はじめまして', 'uso': 'solo la primerísima vez que ves a alguien, nunca después'},
      {'jp': 'どうぞよろしく', 'uso': 'cierra la presentación, justo después de tu nombre'},
      {'jp': 'こちらこそ', 'uso': "'lo mismo digo', al devolver un gracias o un cumplido"},
      {'jp': 'おひさしぶりです', 'uso': 'a alguien que llevas tiempo sin ver'}
    ],
    'prerequisito': 'saludos_basicos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': 'です',
        'meaning': "cópula formal: 'es / son' (afirmativo presente)",
        'ejemplo': 'わたしは がくせいです',
        'literal': 'yo-TEMA / estudiante-soy',
        'uso': "no es un verbo 'ser' de verdad: con adjetivos-い no se conjuga (おいしかったです, nunca おいしいでした)"
      },
      {
        'kind': 'gramatica',
        'jp': 'ではありません',
        'meaning': "cópula formal negativa: 'no es / no son'",
        'ejemplo': 'がくせいでは ありません',
        'literal': 'estudiante-EN-CUANTO-A / no-hay',
        'uso': 'muy formal, de documento o discurso. Hablando se dice じゃありません o じゃないです'
      },
      {
        'kind': 'gramatica',
        'jp': 'じゃありません',
        'meaning': "cópula negativa hablada: 'no es / no son' (contracción de ではありません)",
        'ejemplo': 'わたしは がくせいじゃありません',
        'literal': 'yo-TEMA / estudiante-no-soy',
        'uso': 'La forma normal de negar al hablar; 「ではありません」 suena de discurso o de examen. Aún más coloquial: 「じゃないです」.'
      },
      {
        'kind': 'gramatica',
        'jp': 'でした',
        'meaning': "cópula formal pasada: 'era / fueron'",
        'ejemplo': 'きのうは やすみでした',
        'literal': 'ayer-TEMA / descanso-fue',
        'uso': 'solo con sustantivos y adjetivos-な; con adjetivos-い se usa 〜かった'
      },
      {
        'kind': 'gramatica',
        'jp': 'ではありませんでした',
        'meaning': "cópula formal negativa en pasado: 'no era / no fue'",
        'ejemplo': 'きのうは 休みではありませんでした',
        'literal': 'ayer-TEMA / descanso-no-fue',
        'uso': 'Muy formal y bastante larga; en conversación se dice 「じゃなかったです」 o 「じゃありませんでした」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ます',
        'meaning': 'terminación verbal formal presente / futuro afirmativo',
        'ejemplo': 'まいあさ コーヒーを のみます',
        'literal': 'cada-mañana / café-OBJ / bebo',
        'uso': "presente y futuro a la vez: 'bebo' y 'beberé'. Lo decide el contexto, no el verbo"
      },
      {
        'kind': 'gramatica',
        'jp': '〜ません',
        'meaning': 'terminación verbal formal presente negativa',
        'ejemplo': 'にくは たべません',
        'literal': 'carne-TEMA / no-como',
        'uso': "sirve tanto para 'ahora no como' como para 'no como carne nunca'"
      },
      {
        'kind': 'gramatica',
        'jp': '〜ました',
        'meaning': 'terminación verbal formal pasada afirmativa',
        'ejemplo': 'ゆうべ えいがを みました',
        'literal': 'anoche / película-OBJ / vi',
        'uso': 'pasado formal; también para lo que se acaba de terminar hace un momento'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ませんでした',
        'meaning': 'terminación verbal formal pasada negativa',
        'ejemplo': 'ゆうべ ねませんでした',
        'literal': 'anoche / no-dormí',
        'uso': 'dos piezas pegadas: negativo + pasado. Es larga, por eso en informal se abrevia a 〜なかった'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ましょう',
        'meaning': "propuesta en primera persona del plural: 'hagamos ~ / vamos a ~'",
        'ejemplo': 'いっしょに ひるごはんを 食べましょう',
        'literal': 'juntos / almuerzo-OBJ / comamos',
        'uso': 'Propones algo dando por hecho que el otro acepta; si no lo tienes claro, usa 「〜ましょうか」 o 「〜ませんか」, que dejan salida.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ましょうか',
        'meaning': "ofrecimiento ('¿te ayudo con ~?') o propuesta tanteando ('¿hacemos ~?')",
        'ejemplo': 'にもつを 持ちましょうか',
        'literal': 'equipaje-OBJ / ¿lo-llevo-yo?',
        'uso': 'Con 「か」 suena menos impositivo que 「〜ましょう」: dejas la decisión en el otro. Es la fórmula típica para ofrecer ayuda.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'あなた',
        'reading': 'あなた',
        'meaning': 'tú / usted',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "Entre desconocidos o hacia un superior suena distante o brusco; se usa el nombre + 「さん」 o el cargo. Entre parejas, dicho por la mujer al marido, equivale a 'cariño'."
      },
      {
        'kind': 'vocabulario',
        'jp': '名前',
        'reading': 'なまえ',
        'meaning': 'nombre',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '私',
        'reading': 'わたし / わたくし',
        'meaning': 'yo (わたくし es la forma más formal)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'El pronombre se omite casi siempre; solo se dice para contrastar. 「わたくし」 es muy formal (trabajo, discursos); 「わたし」 sirve para todo; 「あたし」 lo usan mujeres en tono informal.'
      },
      {
        'kind': 'vocabulario',
        'jp': '自分',
        'reading': 'じぶん',
        'meaning': 'uno mismo',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "Vale para 'yo mismo' y para 'uno mismo' en general según el contexto. En habla masculina informal y en Kansai, 「自分」 puede llegar a significar 'tú'."
      }
    ]
  },
  {
    'id': 'demostrativos',
    'nombre': 'Demostrativos こそあど y pronombres de lugar',
    'funcion': 'señalar y elegir: esto, eso, aquello, y preguntar dónde está lo que buscas',
    'frases_hechas': [
      {'jp': 'これ何ですか', 'uso': "'¿qué es esto?'; la frase que más vas a usar en una tienda"},
      {'jp': 'あそこです', 'uso': "'está allí', señalando algo lejos de los dos"},
      {'jp': 'どっちでもいい', 'uso': "'cualquiera me vale'"},
      {'jp': 'こちらへどうぞ', 'uso': "'por aquí, pase'; lo oirás en cualquier restaurante"}
    ],
    'prerequisito': 'desu_masu',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '疑問詞+か',
        'meaning': 'interrogativo + か -> indefinido afirmativo: algo, alguien, en algún sitio, alguna vez',
        'ejemplo': 'かばんの なかに 何か ありますか',
        'literal': 'bolso-DE / dentro-EN / algo / ¿hay?',
        'uso': "Con 「だれか」, 「どこか」, 「いつか」, 「なにか」 la pregunta se vuelve un indefinido ('alguien', 'algún sitio'). La partícula 「は」/「が」/「を」 suele caerse al hablar."
      },
      {
        'kind': 'gramatica',
        'jp': '疑問詞+も',
        'meaning': 'interrogativo + も + verbo en negativo -> nada, nadie, en ningún sitio',
        'ejemplo': 'きょうは どこも 行きません',
        'literal': 'hoy-TEMA / a-ningún-sitio / no-voy',
        'uso': "Pide verbo en negativo: 「だれもいません」 ('no hay nadie'). En afirmativo el sentido cambia a 'todos/cualquiera', pero para N5 quédate con el negativo."
      },
      {
        'kind': 'vocabulario',
        'jp': 'あそこ',
        'reading': 'あそこ',
        'meaning': 'allá (lugar lejos de ambos)',
        'tipo': 'pronombre',
        'ejemplo': 'あそこは どこですか',
        'literal': 'allá-TEMA / ¿dónde-es?',
        'uso': 'lugar lejano. Visible en la distancia'
      },
      {
        'kind': 'vocabulario',
        'jp': 'あちら',
        'reading': 'あちら',
        'meaning': 'por allí / aquella persona (cortés)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "'Allí' o 'aquella persona' en cortés. Versión llana: 「あっち」, que no se usa delante de un superior o un cliente."
      },
      {
        'kind': 'vocabulario',
        'jp': 'あっち',
        'reading': 'あっち',
        'meaning': 'por allí (informal)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'Forma llana de 「あちら」; entre iguales. Señalar así a una persona resulta grosero.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'あの',
        'reading': 'あの',
        'meaning': 'aquel / aquella; oye… (para llamar la atención)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "Además de 'aquel', alargado (「あのう…」) es la muletilla para pedir la palabra o abordar a alguien con tacto: 'oye…', 'perdona…'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'あれ',
        'reading': 'あれ',
        'meaning': 'aquello (objeto lejos de ambos)',
        'tipo': 'pronombre',
        'ejemplo': 'あれは 何ですか',
        'literal': 'aquello-TEMA / ¿qué-es?',
        'uso': 'demostrativo. Lejos de ambos o visible en la distancia'
      },
      {
        'kind': 'vocabulario',
        'jp': 'いくら',
        'reading': 'いくら',
        'meaning': 'cuánto / a cuánto asciende',
        'tipo': 'pronombre',
        'ejemplo': 'それは いくらですか',
        'literal': 'eso-TEMA / ¿cuánto-cuesta?',
        'uso': 'pregunta de precio. Muy común en tiendas, supermercados y mercadillos'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ここ',
        'reading': 'ここ',
        'meaning': 'aquí (lugar del hablante)',
        'tipo': 'pronombre',
        'ejemplo': 'ここに 座ってください',
        'literal': 'aquí-EN / siéntate / por-favor',
        'uso': 'lugar cercano al que habla. Dentro del mismo espacio'
      },
      {
        'kind': 'vocabulario',
        'jp': 'こちら',
        'reading': 'こちら',
        'meaning': 'esta persona / por aquí (cortés)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "Para presentar a alguien: 「こちらは田中さんです」. También es un 'yo/nosotros' cortés al teléfono o en una tienda."
      },
      {
        'kind': 'vocabulario',
        'jp': 'こっち',
        'reading': 'こっち',
        'meaning': 'por aquí (informal)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'Forma llana de 「こちら」; natural entre amigos, cortante con un superior.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'この',
        'reading': 'この',
        'meaning': 'este/esta (delante de nombre)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'これ',
        'reading': 'これ',
        'meaning': 'esto (objeto cercano al hablante)',
        'tipo': 'pronombre',
        'ejemplo': 'これは 何ですか',
        'literal': 'esto-TEMA / ¿qué-es?',
        'uso': 'demostrativo. Cerca del que habla'
      },
      {
        'kind': 'vocabulario',
        'jp': 'こんな',
        'reading': 'こんな',
        'meaning': 'así, de este tipo',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'そこ',
        'reading': 'そこ',
        'meaning': 'ahí (lugar del oyente)',
        'tipo': 'pronombre',
        'ejemplo': 'そこで 待ってください',
        'literal': 'ahí-EN / espera / por-favor',
        'uso': 'lugar cercano al oyente. Donde está la otra persona'
      },
      {
        'kind': 'vocabulario',
        'jp': 'そちら',
        'reading': 'そちら',
        'meaning': 'por ahí (cortés)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "'Ahí, tu lado' en tono cortés; también alude a tu interlocutor o a su empresa. Versión llana: 「そっち」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'そっち',
        'reading': 'そっち',
        'meaning': 'por ahí (informal)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'Forma llana de 「そちら」; entre iguales. Con un cliente o un jefe, 「そちら」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'その',
        'reading': 'その',
        'meaning': 'ese/esa (delante de nombre)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'それ',
        'reading': 'それ',
        'meaning': 'eso (objeto cercano al oyente)',
        'tipo': 'pronombre',
        'ejemplo': 'それは いくらですか',
        'literal': 'eso-TEMA / ¿cuánto-cuesta?',
        'uso': 'demostrativo. Cerca del oyente o ya mencionado'
      },
      {
        'kind': 'vocabulario',
        'jp': 'どう',
        'reading': 'どう',
        'meaning': 'cómo',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'どうして',
        'reading': 'どうして',
        'meaning': 'por qué',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': "'Por qué' neutro en conversación; también puede ser '¿cómo?' (「どうして分かったの」). Casual: 「なんで」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'どこ',
        'reading': 'どこ',
        'meaning': 'dónde',
        'tipo': 'pronombre',
        'ejemplo': 'どこに いますか',
        'literal': '¿dónde-EN / estás?',
        'uso': 'pregunta de ubicación. La pregunta más importante cuando se pierde'
      },
      {
        'kind': 'vocabulario',
        'jp': 'どちら',
        'reading': 'どちら',
        'meaning': 'cuál de los dos / ¿por dónde? (formal)',
        'tipo': 'pronombre',
        'ejemplo': 'どちらが いいですか',
        'literal': '¿cuál-entre-los-dos-SUJ / está-bien?',
        'uso': 'versión más formal de どっち. Muy útil en tiendas o con desconocidos'
      },
      {
        'kind': 'vocabulario',
        'jp': 'どっち',
        'reading': 'どっち',
        'meaning': 'cuál de los dos',
        'tipo': 'pronombre',
        'ejemplo': 'どっちが いいですか',
        'literal': '¿cuál-de-los-dos-SUJ / está-bien?',
        'uso': 'interrogativo de elección entre dos. Se oye más que どちら si hablas con amigos'
      },
      {
        'kind': 'vocabulario',
        'jp': 'どなた',
        'reading': 'どなた',
        'meaning': 'quién (cortés)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'どの',
        'reading': 'どの',
        'meaning': 'cuál (delante de nombre)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'どれ',
        'reading': 'どれ',
        'meaning': 'cuál (de tres o más)',
        'tipo': 'pronombre',
        'ejemplo': 'どれが ほしいですか',
        'literal': '¿cuál-SUJ / quieres?',
        'uso': 'pregunta entre muchas opciones. Con dos opciones usa どっち'
      },
      {
        'kind': 'vocabulario',
        'jp': 'どんな',
        'reading': 'どんな',
        'meaning': 'qué tipo de',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'なぜ',
        'reading': 'なぜ',
        'meaning': 'por qué (igual que どうして)',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'Más propio de texto escrito o pregunta formal; al hablar es más normal 「どうして」, y en tono casual 「なんで」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '何',
        'reading': 'なん / なに',
        'meaning': 'qué',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': 'Se lee 「なん」 antes de 「です」, 「た」, 「の」 y los contadores (「何時」「何人」); 「なに」 en el resto (「何を」「何が」).'
      },
      {
        'kind': 'vocabulario',
        'jp': '何～',
        'reading': 'なん～',
        'meaning': 'qué tipo de ~ / cuántos ~',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '誰',
        'reading': 'だれ',
        'meaning': 'quién',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '誰か',
        'reading': 'だれか',
        'meaning': 'alguien',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'particulas_basicas',
    'nombre': 'Partículas básicas は・が・を・に',
    'funcion': 'montar frases tuyas: decir de qué hablas, qué haces, dónde y con quién',
    'frases_hechas': [
      {'jp': 'そうですね', 'uso': "para ganar tiempo antes de responder, como el 'pues…' español"},
      {'jp': 'えっと…', 'uso': "el 'ehh…' japonés mientras piensas"},
      {'jp': 'それで？', 'uso': "'¿y entonces?', para que el otro siga contando"},
      {'jp': 'やっぱり', 'uso': "'lo sabía' / 'al final sí', cuando se confirma lo que esperabas"}
    ],
    'prerequisito': 'demostrativos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': 'は',
        'meaning': 'partícula de tema (wa): marca el tema de la oración',
        'ejemplo': 'わたしは ラウラです',
        'literal': 'yo-TEMA / Laura-soy',
        'uso': "se escribe は pero se pronuncia 'wa'. Marca de qué se habla, no quién hace la acción"
      },
      {
        'kind': 'gramatica',
        'jp': 'が',
        'meaning': 'partícula de sujeto: enfatiza quién realiza la acción',
        'ejemplo': 'ねこが います',
        'literal': 'gato-SUJ / hay',
        'uso': "presenta algo nuevo o responde a '¿quién?' o '¿qué?'. Con すき y じょうず marca lo que gusta: にほんごが すきです"
      },
      {
        'kind': 'gramatica',
        'jp': 'を',
        'meaning': 'partícula de objeto directo (wo): marca el complemento directo',
        'ejemplo': 'ごはんを たべます',
        'literal': 'comida-OBJ / como',
        'uso': "se escribe を y se pronuncia 'o'. Solo aparece delante de verbos que llevan objeto"
      },
      {
        'kind': 'gramatica',
        'jp': 'に',
        'meaning': 'partícula de dirección / destino / tiempo / receptor',
        'ejemplo': '７じに うちに かえります',
        'literal': '7h-EN / casa-A / vuelvo',
        'uso': 'hora concreta y destino. Los tiempos relativos (きょう, あした, まいにち) NO llevan に'
      },
      {
        'kind': 'gramatica',
        'jp': 'で',
        'meaning': 'partícula de lugar de acción o medio / herramienta',
        'ejemplo': 'レストランで たべます',
        'literal': 'restaurante-EN / como',
        'uso': 'で es el sitio donde ocurre la acción; に es el sitio adonde vas o donde algo está quieto'
      },
      {
        'kind': 'gramatica',
        'jp': 'と',
        'meaning': "partícula 'y' (sustantivos) / 'con' (compañía)",
        'ejemplo': 'ともだちと はなします',
        'literal': 'amigo-CON / hablo',
        'uso': "'y' solo entre sustantivos y en lista cerrada. Para unir dos frases no sirve: eso es la forma-て"
      },
      {
        'kind': 'gramatica',
        'jp': 'も',
        'meaning': "partícula inclusiva: 'también' / 'tampoco'",
        'ejemplo': 'わたしも いきます',
        'literal': 'yo-TAMBIÉN / voy',
        'uso': 'sustituye a は y a が, no se suma a ellas: nunca わたしはも'
      },
      {
        'kind': 'gramatica',
        'jp': 'の',
        'meaning': "partícula posesiva: A の B → 'B de A'",
        'ejemplo': 'ラウラの ねこ',
        'literal': 'Laura-DE / gato',
        'uso': 'orden inverso al español: el poseedor va delante. También encadena: にほんごの せんせいの くるま'
      },
      {
        'kind': 'gramatica',
        'jp': 'から',
        'meaning': "partícula: 'desde ~ / a partir de ~' (punto de inicio en lugar o tiempo)",
        'ejemplo': '九時から しごとです',
        'literal': 'nueve-horas-DESDE / trabajo-es',
        'uso': "Marca de dónde o de cuándo arranca algo; se empareja con 「まで」 para el otro extremo. Detrás de una frase entera, 「から」 significa 'porque'."
      },
      {
        'kind': 'gramatica',
        'jp': 'まで',
        'meaning': "partícula: 'hasta ~' (límite de lugar, tiempo o cantidad)",
        'ejemplo': 'えきまで あるきます',
        'literal': 'estación-HASTA / voy-andando',
        'uso': "El tope de un recorrido o de un plazo; va con 「から」. No lo confundas con 「までに」, que es 'antes de (una fecha límite)'."
      },
      {
        'kind': 'gramatica',
        'jp': 'や',
        'meaning': "partícula 'y' para listas abiertas: 'A や B (entre otras cosas)'",
        'ejemplo': 'つくえの うえに ノートや ペンが あります',
        'literal': 'mesa-DE / encima-EN / cuaderno-Y / boli-SUJ / hay',
        'uso': 'Citas solo algunos ejemplos, no la lista entera; 「と」 en cambio da la lista cerrada. Suele rematarse con 「など」.'
      },
      {
        'kind': 'gramatica',
        'jp': 'へ',
        'meaning': "partícula de dirección: 'hacia ~ / a ~' (se pronuncia 'e')",
        'ejemplo': 'らいしゅう 京都へ 行きます',
        'literal': 'semana-que-viene / Kioto-HACIA / voy',
        'uso': "Casi intercambiable con 「に」 para destinos; 「へ」 pone el acento en el trayecto y 「に」 en el punto de llegada. Se escribe 「へ」 pero se pronuncia 'e'."
      },
      {
        'kind': 'gramatica',
        'jp': 'か',
        'meaning': 'partícula interrogativa: convierte la oración en pregunta',
        'ejemplo': 'コーヒーを のみますか',
        'literal': 'café-OBJ / ¿bebes?',
        'uso': 'va al final del todo. Con か no hace falta ni signo de interrogación ni subir el tono'
      },
      {
        'kind': 'gramatica',
        'jp': 'ね',
        'meaning': "partícula final: busca confirmación ('¿verdad?', '¿no?')",
        'ejemplo': 'おいしいですね',
        'literal': 'está-rico-¿verdad?',
        'uso': 'busca complicidad: das por hecho que el otro opina lo mismo que tú'
      },
      {
        'kind': 'gramatica',
        'jp': 'よ',
        'meaning': 'partícula final: afirma algo que el oyente no sabe',
        'ejemplo': 'あの みせは やすいですよ',
        'literal': 'esa / tienda-TEMA / barata-es-¡eh!',
        'uso': 'informa de algo nuevo para el otro. Abusar de よ suena insistente o sabelotodo'
      },
      {
        'kind': 'gramatica',
        'jp': 'という',
        'meaning': "'llamado ~ / que se llama ~': introduce un nombre o una cita",
        'ejemplo': '「こんにちは」という ことばを つかいます',
        'literal': "'hola'-LLAMADO / palabra-OBJ / uso",
        'uso': 'Para presentar algo por su nombre cuando el oyente no lo conoce, o para citar lo dicho. En charla informal se oye 「っていう」.'
      }
    ]
  },
  {
    'id': 'katakana_comun',
    'nombre': 'Katakana — préstamos frecuentes',
    'funcion': 'pedir en una cafetería o una tienda y hablar de las cosas de fuera que están en el día a día',
    'frases_hechas': [
      {'jp': 'これ、ください', 'uso': 'señalando la carta o el escaparate; resuelve casi cualquier compra'},
      {'jp': 'お願いします', 'uso': "cierra cualquier pedido; es el 'por favor' que lo remata"},
      {'jp': 'テイクアウトで', 'uso': "'para llevar', en cualquier cafetería"},
      {'jp': 'いくらですか', 'uso': "'¿cuánto es?'"}
    ],
    'prerequisito': 'particulas_basicas',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'カメラ',
        'reading': 'カメラ',
        'meaning': 'cámara (fotográfica)',
        'tipo': 'sustantivo',
        'ejemplo': 'あたらしい カメラで しゃしんを とりました',
        'literal': 'nueva / cámara-EN / foto-OBJ / hice',
        'uso': 'de fotos. La de vídeo es ビデオカメラ. Hacer fotos es しゃしんを とる'
      },
      {
        'kind': 'vocabulario',
        'jp': 'コーヒー',
        'reading': 'コーヒー',
        'meaning': 'café (bebida)',
        'tipo': 'sustantivo',
        'ejemplo': '毎朝 コーヒーを のみます',
        'literal': 'cada-mañana / café-OBJ / bebo',
        'uso': 'la bebida más común en las cafeterías. El café solo es ブラック, con leche es ミルク'
      },
      {
        'kind': 'vocabulario',
        'jp': 'タクシー',
        'reading': 'タクシー',
        'meaning': 'taxi',
        'tipo': 'sustantivo',
        'ejemplo': '駅の そばに タクシーが あります',
        'literal': 'estación-DE / cerca-EN / taxi-SUJ / hay',
        'uso': 'muy caro en Japón. Solo se coge de parada u hotel, nunca en la calle'
      },
      {
        'kind': 'vocabulario',
        'jp': 'テレビ',
        'reading': 'テレビ',
        'meaning': 'televisión',
        'tipo': 'sustantivo',
        'ejemplo': 'ばん テレビを みます',
        'literal': 'noche-TEMA / tele-OBJ / veo',
        'uso': 'para mirar tele se usa みる. En casos muy coloquiales, つける (encender)'
      },
      {
        'kind': 'vocabulario',
        'jp': 'バス',
        'reading': 'バス',
        'meaning': 'autobús',
        'tipo': 'sustantivo',
        'ejemplo': 'バスで 学校に いきます',
        'literal': 'autobús-EN / escuela-A / voy',
        'uso': 'el transporte urbano. バス停 es la parada. A veces va lleno'
      },
      {
        'kind': 'vocabulario',
        'jp': 'パン',
        'reading': 'パン',
        'meaning': 'pan',
        'tipo': 'sustantivo',
        'ejemplo': 'あさごはんに パンを たべます',
        'literal': 'desayuno-EN / pan-OBJ / como',
        'uso': 'el pan de panadería, de todas formas. El de molde también es パン'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ホテル',
        'reading': 'ホテル',
        'meaning': 'hotel',
        'tipo': 'sustantivo',
        'ejemplo': 'りょこうで ホテルに とまります',
        'literal': 'viaje-EN / hotel-EN / me-hospedo',
        'uso': 'alojamiento occidental. El tradicional es 旅館 (りょかん)'
      },
      {
        'kind': 'vocabulario',
        'jp': 'レストラン',
        'reading': 'レストラン',
        'meaning': 'restaurante',
        'tipo': 'sustantivo',
        'ejemplo': 'しゅうまつに レストランに いきました',
        'literal': 'fin-de-semana-EN / restaurante-A / fui',
        'uso': 'restaurante occidental. El de comida japonesa es 日本料理屋'
      },
      {
        'kind': 'vocabulario',
        'jp': '写真',
        'reading': 'しゃしん',
        'meaning': 'foto',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '撮る',
        'reading': 'とる',
        'meaning': 'hacer (una foto)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Es el 「とる」 de hacer fotos y grabar vídeo (「写真をとる」). Para 'coger algo' es 「取る」, que se pronuncia igual."
      },
      {
        'kind': 'vocabulario',
        'jp': '買い物',
        'reading': 'かいもの',
        'meaning': 'compras',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'numeros',
    'nombre': 'Números 1-10 y centenas',
    'funcion': 'decir cantidades y precios, y entender lo que te dicen en una caja',
    'frases_hechas': [
      {'jp': 'いくつですか', 'uso': "'¿cuántos?'; también '¿cuántos años tienes?' con お delante"},
      {'jp': 'ひとつください', 'uso': "'uno, por favor'; el contador ひとつ vale para casi todo"},
      {'jp': 'ちょうどです', 'uso': "'justo', al pagar con el importe exacto"},
      {'jp': '半分こ', 'uso': "'a medias', repartir algo entre dos; muy coloquial"}
    ],
    'prerequisito': 'katakana_comun',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'いくつ',
        'reading': 'いくつ',
        'meaning': 'cuántos / cuántos años',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'お金',
        'reading': 'おかね',
        'meaning': 'dinero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'キロ; キログラム',
        'reading': 'キロ / キログラム',
        'meaning': 'kilo(gramo)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'グラム',
        'reading': 'グラム',
        'meaning': 'gramo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ゼロ',
        'reading': 'ゼロ',
        'meaning': 'cero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'メートル',
        'reading': 'メートル',
        'meaning': 'metro (medida)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '一',
        'reading': 'いち',
        'meaning': 'uno (1)',
        'tipo': 'número',
        'ejemplo': '一つ ください',
        'literal': 'uno-contador / por-favor',
        'uso': 'número base. Para contar objetos sin especificar: ひとつ (informal)'
      },
      {
        'kind': 'vocabulario',
        'jp': '一つ',
        'reading': 'ひとつ',
        'meaning': 'uno, una cosa',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': "La serie 「ひとつ・ふたつ…とお」 cuenta hasta diez cosas cualesquiera cuando no sabes o no hace falta el contador exacto. 「一つ」 al pedir algo lo suaviza: 'uno, por favor'."
      },
      {
        'kind': 'vocabulario',
        'jp': '七',
        'reading': 'しち / なな',
        'meaning': 'siete (7)',
        'tipo': 'número',
        'ejemplo': '七月 ですね',
        'literal': 'julio-TEMA-¿verdad?',
        'uso': 'しち (formal), なな (coloquial). 700 se lee ななひゃく'
      },
      {
        'kind': 'vocabulario',
        'jp': '七つ',
        'reading': 'ななつ',
        'meaning': 'siete (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '万',
        'reading': 'まん',
        'meaning': 'diez mil (10.000)',
        'tipo': 'número',
        'ejemplo': '一万円 です',
        'literal': '10000-yen / es',
        'uso': 'la unidad de 10.000. Es la base del sistema sinojaponés para cantidades grandes; 3万 = 30000'
      },
      {
        'kind': 'vocabulario',
        'jp': '三',
        'reading': 'さん',
        'meaning': 'tres (3)',
        'tipo': 'número',
        'ejemplo': '三つください',
        'literal': 'tres-contador / por-favor',
        'uso': 'número base. Contador general: みっつ'
      },
      {
        'kind': 'vocabulario',
        'jp': '三つ',
        'reading': 'みっつ',
        'meaning': 'tres (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '九',
        'reading': 'きゅう / く',
        'meaning': 'nueve (9)',
        'tipo': 'número',
        'ejemplo': '九時 です',
        'literal': '9h / es',
        'uso': 'きゅう (formal), く (coloquial). 900 se lee きゅうひゃく'
      },
      {
        'kind': 'vocabulario',
        'jp': '九つ',
        'reading': 'ここのつ',
        'meaning': 'nueve (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '二',
        'reading': 'に',
        'meaning': 'dos (2)',
        'tipo': 'número',
        'ejemplo': '二人 います',
        'literal': 'dos-personas / hay',
        'uso': 'número base. Con contador de personas: ふたり'
      },
      {
        'kind': 'vocabulario',
        'jp': '二つ',
        'reading': 'ふたつ',
        'meaning': 'dos (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '五',
        'reading': 'ご',
        'meaning': 'cinco (5)',
        'tipo': 'número',
        'ejemplo': '五百円 です',
        'literal': '500-yen / es',
        'uso': 'número base. En composición con cientos, 500 se lee ごひゃく'
      },
      {
        'kind': 'vocabulario',
        'jp': '五つ',
        'reading': 'いつつ',
        'meaning': 'cinco (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '八',
        'reading': 'はち',
        'meaning': 'ocho (8)',
        'tipo': 'número',
        'ejemplo': '八百円 です',
        'literal': '800-yen / es',
        'uso': 'número base. 800 se lee はっぴゃく, con la alteración fonética 8 + 百'
      },
      {
        'kind': 'vocabulario',
        'jp': '八つ',
        'reading': 'やっつ',
        'meaning': 'ocho (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '六',
        'reading': 'ろく',
        'meaning': 'seis (6)',
        'tipo': 'número',
        'ejemplo': '六時 に',
        'literal': '6h-EN',
        'uso': 'número base. En cientos, 600 se lee ろっぴゃく'
      },
      {
        'kind': 'vocabulario',
        'jp': '六つ',
        'reading': 'むっつ',
        'meaning': 'seis (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '十',
        'reading': 'じゅう',
        'meaning': 'diez (10)',
        'tipo': 'número',
        'ejemplo': '十個 買いました',
        'literal': '10-piezas / compré',
        'uso': 'base para contar decenas. 11 = 十一 (じゅういち), 20 = 二十 (にじゅう)'
      },
      {
        'kind': 'vocabulario',
        'jp': '千',
        'reading': 'せん',
        'meaning': 'mil (1000)',
        'tipo': 'número',
        'ejemplo': '千円 で いいですか',
        'literal': '1000-yen / ¿está-bien?',
        'uso': 'miles. 2000 = 二千 (にせん), 3000 = 三千 (さんぜん), 8000 = 八千 (はっせん)'
      },
      {
        'kind': 'vocabulario',
        'jp': '半分',
        'reading': 'はんぶん',
        'meaning': 'mitad',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '四',
        'reading': 'し / よん',
        'meaning': 'cuatro (4)',
        'tipo': 'número',
        'ejemplo': '四時に 来ます',
        'literal': '4h-EN / vengo',
        'uso': 'dos formas: し (formal), よん (coloquial). Con personas: よにん'
      },
      {
        'kind': 'vocabulario',
        'jp': '四つ',
        'reading': 'よっつ',
        'meaning': 'cuatro (cosas)',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '安い',
        'reading': 'やすい',
        'meaning': 'barato',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '番号',
        'reading': 'ばんごう',
        'meaning': 'número',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '百',
        'reading': 'ひゃく',
        'meaning': 'cien (100)',
        'tipo': 'número',
        'ejemplo': '百円 です',
        'literal': '100-yen / es',
        'uso': 'centenas. 200 = 二百 (にひゃく), 300 = 三百 (さんびゃく), 600 = 六百 (ろっぴゃく)'
      },
      {
        'kind': 'vocabulario',
        'jp': '財布',
        'reading': 'さいふ',
        'meaning': 'cartera, monedero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '零',
        'reading': 'れい',
        'meaning': 'cero',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '～円',
        'reading': '～えん',
        'meaning': 'yenes',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'El yen no tiene decimales; 「四円」 se lee 「よえん」. Al hablar de precios el número entero va pegado: 「せんえん」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～歳',
        'reading': '～さい',
        'meaning': '~ años (edad)',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': '1, 8 y a menudo 10 y 20 se contraen: 「いっさい」「はっさい」「じゅっさい」. Los 20 años tienen forma propia: 「はたち」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～番',
        'reading': '～ばん',
        'meaning': 'número ~ / el mejor en ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Número X' de una serie o el turno. 「一番」 además significa 'el primero' o 'el más ~' (「一番高い」)."
      }
    ]
  },
  {
    'id': 'contadores_n5',
    'nombre': 'Contadores N5: series de medida',
    'funcion': 'contar objetos reales, personas, animales, tiempo y reacciones sin perderte en la serie correcta',
    'frases_hechas': [
      {'jp': '一人です', 'uso': "'soy uno/a solas'; la forma más frecuente para decir 'yo solo'"},
      {'jp': '本を三冊買った', 'uso': "'compré tres libros'; la serie 本 se usa para cosas alargadas"},
      {'jp': '二匹の猫', 'uso': "'dos gatos'; la serie 匹 para animales"},
      {'jp': '三回', 'uso': "'tres veces'; la serie 回 sirve para frecuencia y repeticiones"}
    ],
    'prerequisito': 'numeros',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': '一人',
        'reading': 'ひとり',
        'meaning': 'una persona, solo/a',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': "Irregular: 「ひとり」. Además de 'una persona', 'solo, sin compañía' (「一人で行く」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '二人',
        'reading': 'ふたり',
        'meaning': 'dos personas',
        'tipo': 'número',
        'ejemplo': '',
        'literal': '',
        'uso': 'Irregular: 「ふたり」. De tres en adelante ya es 「さんにん」…'
      },
      {
        'kind': 'vocabulario',
        'jp': '～か月',
        'reading': '～かげつ',
        'meaning': 'contador de meses',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Cuenta duración en meses ('durante X meses'). No lo confundas con 「～月」 (「がつ」), que nombra el mes del año."
      },
      {
        'kind': 'vocabulario',
        'jp': '～人',
        'reading': '～じん / ～にん',
        'meaning': 'contador de personas / gentilicio (según lectura)',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': '1 y 2 personas son irregulares: 「ひとり」「ふたり」; de 3 en adelante, 「～にん」. Con un país forma el gentilicio: 「～じん」 (「日本人」).'
      },
      {
        'kind': 'vocabulario',
        'jp': '～個',
        'reading': '～こ',
        'meaning': 'contador de objetos pequeños',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Cosas pequeñas y compactas sin forma propia (fruta, piezas). 1, 6, 8, 10 se contraen: 「いっこ」「ろっこ」「はっこ」「じゅっこ」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～冊',
        'reading': '～さつ',
        'meaning': 'contador de libros',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Libros, cuadernos y revistas. 1, 8, 10: 「いっさつ」「はっさつ」「じゅっさつ」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～匹',
        'reading': '～ひき',
        'meaning': 'contador de animales pequeños',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Animales pequeños. La consonante cambia: 「いっぴき」「にひき」「さんびき」「ろっぴき」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～台',
        'reading': '～だい',
        'meaning': 'contador de vehículos y máquinas',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Coches, bicicletas, máquinas y aparatos (ordenador, nevera, televisión).'
      },
      {
        'kind': 'vocabulario',
        'jp': '～回',
        'reading': '～かい',
        'meaning': 'contador de veces',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Número de veces que se repite algo. Muy próximo a 「～度」, pero 「～回」 subraya la repetición.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～度',
        'reading': '～ど',
        'meaning': 'contador de veces / grados',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Veces' insistiendo en la ocasión concreta (「今度」 'esta vez'); también 'grados' de temperatura o de ángulo."
      },
      {
        'kind': 'vocabulario',
        'jp': '～本',
        'reading': '～ほん',
        'meaning': 'contador de objetos alargados',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Objetos largos y finos (botellas, paraguas, bolis, árboles) y también llamadas, trenes y películas. Suena 「いっぽん」「さんぼん」「ろっぽん」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～杯',
        'reading': '～はい',
        'meaning': 'contador de vasos y tazas',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Vasos, tazas y cuencos con su contenido. Suena 「いっぱい」「さんばい」「ろっぱい」. 「いっぱい」 aparte significa 'lleno'."
      },
      {
        'kind': 'vocabulario',
        'jp': '～枚',
        'reading': '～まい',
        'meaning': 'contador de objetos planos',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Cosas planas y finas: hojas, sellos, camisetas, platos, entradas.'
      }
    ]
  },
  {
    'id': 'hora_fecha_n5',
    'nombre': 'Hora, fecha y calendario N5',
    'funcion': 'decir la hora, recordar fechas, pedir una cita y hablar del día y la semana sin perderte',
    'frases_hechas': [
      {'jp': '何時ですか', 'uso': "'¿qué hora es?' como apertura de conversación"},
      {'jp': '三時半です', 'uso': "'son las tres y media'; la hora exacta es lo más práctico"},
      {'jp': '今日は月曜日です', 'uso': "'hoy es lunes'; sirve para mover la semana"},
      {'jp': '十一月です', 'uso': "'es noviembre'; el mes con la lectura más rara del año"}
    ],
    'prerequisito': 'contadores_n5',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'いつ',
        'reading': 'いつ',
        'meaning': 'cuándo',
        'tipo': 'pronombre',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'おととし',
        'reading': 'おととし',
        'meaning': 'hace dos años (el año antepasado)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'さ来年',
        'reading': 'さらいねん',
        'meaning': 'dentro de dos años (el año que viene del que viene)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'カレンダー',
        'reading': 'カレンダー',
        'meaning': 'calendario',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '一日',
        'reading': 'いちにち / ついたち',
        'meaning': 'un día (duración) / día uno del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「いちにち」 = 'un día (de duración)'; 「ついたち」 = 'el día 1 del mes'."
      },
      {
        'kind': 'vocabulario',
        'jp': '一昨日',
        'reading': 'おととい',
        'meaning': 'anteayer',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '一月',
        'reading': 'いちがつ',
        'meaning': 'enero',
        'tipo': 'sustantivo',
        'ejemplo': '一月に うまれました',
        'literal': 'enero-EN / nací',
        'uso': 'mes de enero; 1月 es muy común en cumpleaños y vacaciones'
      },
      {
        'kind': 'vocabulario',
        'jp': '七日',
        'reading': 'なのか',
        'meaning': 'siete días / día 7 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '三日',
        'reading': 'みっか',
        'meaning': 'tres días / día 3 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '九日',
        'reading': 'ここのか',
        'meaning': 'nueve días / día 9 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '二十日',
        'reading': 'はつか',
        'meaning': 'veinte días / día 20 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '二十歳',
        'reading': 'はたち',
        'meaning': 'veinte años (edad)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Los 20 años, con lectura propia 「はたち」; marca la mayoría de edad en Japón.'
      },
      {
        'kind': 'vocabulario',
        'jp': '二日',
        'reading': 'ふつか',
        'meaning': 'dos días / día 2 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '五日',
        'reading': 'いつか',
        'meaning': 'cinco días / día 5 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '今年',
        'reading': 'ことし',
        'meaning': 'este año',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '今日',
        'reading': 'きょう',
        'meaning': 'hoy',
        'tipo': 'sustantivo',
        'ejemplo': '今日も いい天気です',
        'literal': 'hoy-TAMBién / buen-tiempo-es',
        'uso': 'prácticamente siempre viene con は u に en frases de rutina'
      },
      {
        'kind': 'vocabulario',
        'jp': '今晩',
        'reading': 'こんばん',
        'meaning': 'esta noche',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '今月',
        'reading': 'こんげつ',
        'meaning': 'este mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '今朝',
        'reading': 'けさ',
        'meaning': 'esta mañana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '今週',
        'reading': 'こんしゅう',
        'meaning': 'esta semana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '休み',
        'reading': 'やすみ',
        'meaning': 'descanso, día libre; ausencia',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Descanso, vacaciones, día libre' y también 'falta de asistencia' (「学校が休み」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '先月',
        'reading': 'せんげつ',
        'meaning': 'el mes pasado',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '先週',
        'reading': 'せんしゅう',
        'meaning': 'la semana pasada',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '八日',
        'reading': 'ようか',
        'meaning': 'ocho días / día 8 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '六日',
        'reading': 'むいか',
        'meaning': 'seis días / día 6 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '十日',
        'reading': 'とおか',
        'meaning': 'diez días / día 10 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '午前',
        'reading': 'ごぜん',
        'meaning': 'mañana / antes del mediodía',
        'tipo': 'sustantivo',
        'ejemplo': '午前九時です',
        'literal': 'mañana-9h-es',
        'uso': 'muy útil para horarios formales; se usa en trenes, entradas y citas'
      },
      {
        'kind': 'vocabulario',
        'jp': '午後',
        'reading': 'ごご',
        'meaning': 'tarde / después del mediodía',
        'tipo': 'sustantivo',
        'ejemplo': '午後三時です',
        'literal': 'tarde-3h-es',
        'uso': 'también en horarios formales. Es el sistema más claro para hablar de la tarde'
      },
      {
        'kind': 'vocabulario',
        'jp': '半',
        'reading': 'はん',
        'meaning': 'media hora / mitad',
        'tipo': 'sustantivo',
        'ejemplo': '三時半です',
        'literal': '3h-media-es',
        'uso': 'añadido a la hora: 3時半 = tres y media. 30分 = media hora, también muy útil'
      },
      {
        'kind': 'vocabulario',
        'jp': '去年',
        'reading': 'きょねん',
        'meaning': 'el año pasado',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '四日',
        'reading': 'よっか',
        'meaning': 'cuatro días / día 4 del mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '土曜日',
        'reading': 'どようび',
        'meaning': 'sábado',
        'tipo': 'sustantivo',
        'ejemplo': '土曜日に うみへ 行きます',
        'literal': 'sábado-EN / mar-A / voy',
        'uso': 'si alguien te dice 土曜日, ya sabes que es fin de semana'
      },
      {
        'kind': 'vocabulario',
        'jp': '夕方',
        'reading': 'ゆうがた',
        'meaning': 'atardecer',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '夜',
        'reading': 'よる',
        'meaning': 'noche',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '年',
        'reading': 'とし',
        'meaning': 'año, edad',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Año' y también 'edad': 「年を取る」 'hacerse mayor', 「年上」 'mayor que uno'."
      },
      {
        'kind': 'vocabulario',
        'jp': '日曜日',
        'reading': 'にちようび',
        'meaning': 'domingo',
        'tipo': 'sustantivo',
        'ejemplo': '日曜日は 休みです',
        'literal': 'domingo-TEMA / descanso-es',
        'uso': 'equivale al día de descanso más claro'
      },
      {
        'kind': 'vocabulario',
        'jp': '早い',
        'reading': 'はやい',
        'meaning': 'temprano',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Temprano' en el tiempo (「朝が早い」). 'Rápido' de velocidad se escribe 「速い」, con la misma lectura 「はやい」."
      },
      {
        'kind': 'vocabulario',
        'jp': '明後日',
        'reading': 'あさって',
        'meaning': 'pasado mañana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '明日',
        'reading': 'あした',
        'meaning': 'mañana',
        'tipo': 'sustantivo',
        'ejemplo': '明日 いきます',
        'literal': 'mañana / voy',
        'uso': 'el día que viene. Muy útil para citas, trabajo y escuela'
      },
      {
        'kind': 'vocabulario',
        'jp': '昨夜',
        'reading': 'ゆうべ',
        'meaning': 'anoche',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '昨日',
        'reading': 'きのう',
        'meaning': 'ayer',
        'tipo': 'sustantivo',
        'ejemplo': '昨日 しっていますか',
        'literal': 'ayer / ¿lo sabías?',
        'uso': 'frecuente para contar acciones pasadas'
      },
      {
        'kind': 'vocabulario',
        'jp': '昼',
        'reading': 'ひる',
        'meaning': 'mediodía, de día',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Vale para 'mediodía', 'de día' (frente a 「夜」) y 'almuerzo' (「昼を食べる」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '晩',
        'reading': 'ばん',
        'meaning': 'noche (tarde-noche)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Noche' de la tarde-noche, sobre todo en compuestos: 「今晩」「毎晩」「晩ごはん」. Para la noche en general, 「夜」."
      },
      {
        'kind': 'vocabulario',
        'jp': '月曜日',
        'reading': 'げつようび',
        'meaning': 'lunes',
        'tipo': 'sustantivo',
        'ejemplo': '月曜日に 会います',
        'literal': 'lunes-EN / nos vemos',
        'uso': "el día de la semana. Los días se forman como 'día + 曜日'"
      },
      {
        'kind': 'vocabulario',
        'jp': '朝',
        'reading': 'あさ',
        'meaning': 'mañana (parte del día)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '木曜日',
        'reading': 'もくようび',
        'meaning': 'jueves',
        'tipo': 'sustantivo',
        'ejemplo': '木曜日は たくさん べんきょうします',
        'literal': 'jueves-TEMA / mucho / estudio',
        'uso': 'día medio de la semana, muy útil para rutinas'
      },
      {
        'kind': 'vocabulario',
        'jp': '来年',
        'reading': 'らいねん',
        'meaning': 'el año que viene',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '来月',
        'reading': 'らいげつ',
        'meaning': 'el mes que viene',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '来週',
        'reading': 'らいしゅう',
        'meaning': 'la semana que viene',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎年',
        'reading': 'まいねん / まいとし',
        'meaning': 'cada año',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎晩',
        'reading': 'まいばん',
        'meaning': 'cada noche',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎月',
        'reading': 'まいげつ / まいつき',
        'meaning': 'cada mes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎朝',
        'reading': 'まいあさ',
        'meaning': 'cada mañana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎週',
        'reading': 'まいしゅう',
        'meaning': 'cada semana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '水曜日',
        'reading': 'すいようび',
        'meaning': 'miércoles',
        'tipo': 'sustantivo',
        'ejemplo': '水曜日に テストがあります',
        'literal': 'miércoles-EN / examen-hay',
        'uso': 'suele aparecer en horarios y planificación'
      },
      {
        'kind': 'vocabulario',
        'jp': '火曜日',
        'reading': 'かようび',
        'meaning': 'martes',
        'tipo': 'sustantivo',
        'ejemplo': '火曜日は 休みです',
        'literal': 'martes-TEMA / descanso-es',
        'uso': 'se usa con は para el día libre/ahí'
      },
      {
        'kind': 'vocabulario',
        'jp': '誕生日',
        'reading': 'たんじょうび',
        'meaning': 'cumpleaños',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '遅い',
        'reading': 'おそい',
        'meaning': 'lento; tarde',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Vale para 'lento' (poca velocidad) y para 'tarde' (「もう遅い」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '金曜日',
        'reading': 'きんようび',
        'meaning': 'viernes',
        'tipo': 'sustantivo',
        'ejemplo': '金曜日は たのしいです',
        'literal': 'viernes-TEMA / divertido-es',
        'uso': 'días de la semana con su lectura especial'
      },
      {
        'kind': 'vocabulario',
        'jp': '～ころ; ～ごろ',
        'reading': '～ころ / ～ごろ',
        'meaning': 'hacia, sobre (una hora aproximada)',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Momento aproximado en el tiempo: 「三時ごろ」 'hacia las tres', 「子供のころ」 'de niño'. Para cantidades aproximadas se usa 「くらい・ぐらい」."
      },
      {
        'kind': 'vocabulario',
        'jp': '～中',
        'reading': '～じゅう / ～ちゅう',
        'meaning': 'durante ~ / mientras ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Se lee 「じゅう」 para 'todo el / durante todo' (「一日中」 'todo el día'); 「ちゅう」 para 'en pleno' (「勉強中」 'estudiando ahora')."
      },
      {
        'kind': 'vocabulario',
        'jp': '～分',
        'reading': '～ふん',
        'meaning': '~ minutos',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Minutos. La consonante cambia: 「いっぷん」「さんぷん」「よんふん」「ろっぷん」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～年',
        'reading': '～ねん',
        'meaning': '~ años',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '～日',
        'reading': '～にち',
        'meaning': 'día ~ del mes / durante ~ días',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Del 1 al 10 y el 14, 20 y 24 tienen lectura especial (「ついたち」「ふつか」「はつか」…). Vale para el día del mes y para 'durante X días'."
      },
      {
        'kind': 'vocabulario',
        'jp': '～時',
        'reading': '～じ / ～とき',
        'meaning': 'las ~ (hora) / cuando ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "「じ」 marca la hora en punto (「三時」); 「とき」 es 'cuando ~' (「子供のとき」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '～時間',
        'reading': '～じかん',
        'meaning': '~ horas',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Durante X horas' (duración). El punto de la hora es 「～時」, sin 「間」."
      },
      {
        'kind': 'vocabulario',
        'jp': '～月',
        'reading': '～がつ',
        'meaning': 'mes de ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Nombra el mes: 「一月」 = 'enero'. Para preguntar cuántos meses dura algo se usa 「何か月」."
      },
      {
        'kind': 'vocabulario',
        'jp': '～週間',
        'reading': '～しゅうかん',
        'meaning': '~ semanas',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'verbos_n5',
    'nombre': 'Verbos del día a día N5',
    'funcion': 'contar tu rutina diaria: levantarte, comer, estudiar, hablar, entender y describir lo que pasa',
    'frases_hechas': [
      {'jp': 'いってきます', 'uso': "al salir de casa; literalmente 'voy y vuelvo'"},
      {'jp': 'いってらっしゃい', 'uso': 'lo que contesta quien se queda'},
      {'jp': 'ただいま', 'uso': 'al volver a casa, aunque no haya nadie'},
      {'jp': 'おかえり', 'uso': 'lo que contesta quien estaba en casa'}
    ],
    'prerequisito': 'hora_fecha_n5',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'かける',
        'reading': 'かける',
        'meaning': 'llamar (por teléfono); sentarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Verbo comodín: 「電話をかける」 (llamar), 「いすにかける」 (sentarse), 「めがねをかける」 (ponerse gafas), 「時間をかける」 (dedicar tiempo).'
      },
      {
        'kind': 'vocabulario',
        'jp': 'する',
        'reading': 'する',
        'meaning': 'hacer',
        'tipo': 'verbo',
        'ejemplo': 'べんきょうを します',
        'literal': 'estudio-OBJ / hago',
        'uso': 'convierte sustantivos en verbos: そうじする, でんわする, りょこうする. Es el comodín del idioma'
      },
      {
        'kind': 'vocabulario',
        'jp': 'なる',
        'reading': 'なる',
        'meaning': 'convertirse, llegar a ser',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Volverse, llegar a ser'. Con adjetivo-い va 「くなる」; con adjetivo-な y sustantivos, 「になる」. También en fórmulas de cortesía (「お世話になる」)."
      },
      {
        'kind': 'vocabulario',
        'jp': 'やる',
        'reading': 'やる',
        'meaning': 'hacer; dar (a mascotas, plantas o personas cercanas)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Hacer', versión llana y algo brusca de 「する」, entre amigos. También 'dar' a alguien de menos rango, a plantas o animales (「花に水をやる」), donde a un igual se diría 「あげる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '上げる',
        'reading': 'あげる',
        'meaning': 'levantar, subir; dar (a alguien)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Levantar, subir' (「手を上げる」). Se solapa en sonido con 「あげる」 'dar'. Su pareja intransitiva es 「上がる」 'subir (por sí solo)'."
      },
      {
        'kind': 'vocabulario',
        'jp': '並ぶ',
        'reading': 'ならぶ',
        'meaning': 'hacer cola, alinearse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Intransitivo: 'ponerse en fila, hacer cola' (「店の前に並ぶ」). Colocar cosas en fila es 「並べる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '並べる',
        'reading': 'ならべる',
        'meaning': 'poner en fila, colocar en orden',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Transitivo: 'colocar en fila u ordenar' (「皿を並べる」). Que las cosas 'estén en fila' es 「並ぶ」."
      },
      {
        'kind': 'vocabulario',
        'jp': '作る',
        'reading': 'つくる',
        'meaning': 'hacer, crear',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '働く',
        'reading': 'はたらく',
        'meaning': 'trabajar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Trabajar' como actividad; el lugar lleva 「で」: 「工場で働く」. Para decir en qué empresa estás empleado, 「～に勤める」."
      },
      {
        'kind': 'vocabulario',
        'jp': '入れる',
        'reading': 'いれる',
        'meaning': 'meter, poner dentro',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Transitivo: 'meter, poner dentro' (「かばんに入れる」); también 「電気を入れる」 (encender), 「コーヒーを入れる」 (preparar). Que algo 'entre' es 「入る」."
      },
      {
        'kind': 'vocabulario',
        'jp': '出かける',
        'reading': 'でかける',
        'meaning': 'salir (de casa)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '出す',
        'reading': 'だす',
        'meaning': 'sacar (algo); entregar (una tarea)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Sacar' (「かばんから出す」), pero también 「手紙を出す」 (echar al correo), 「宿題を出す」 (entregar), 「お金を出す」 (poner el dinero)."
      },
      {
        'kind': 'vocabulario',
        'jp': '分かる',
        'reading': 'わかる',
        'meaning': 'entender / comprender',
        'tipo': 'verbo',
        'ejemplo': 'いみが わかります',
        'literal': 'significado-SUJ / entiendo',
        'uso': "lleva が, no を: lo entendido es el sujeto. Es 'me queda claro', no 'lo comprendo a base de esfuerzo'"
      },
      {
        'kind': 'vocabulario',
        'jp': '切る',
        'reading': 'きる',
        'meaning': 'cortar; colgar (el teléfono)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cortar', y además 「電話を切る」 (colgar), 「スイッチを切る」 (apagar). Se pronuncia igual que 「着る」 'ponerse ropa'."
      },
      {
        'kind': 'vocabulario',
        'jp': '勉強',
        'reading': 'べんきょう (する)',
        'meaning': 'estudiar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '勤める',
        'reading': 'つとめる',
        'meaning': 'trabajar (para una empresa)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Trabajar para' una empresa; el sitio lleva 「に」: 「銀行に勤める」. 「働く」 se centra en la acción de currar y lleva 「で」."
      },
      {
        'kind': 'vocabulario',
        'jp': '取る',
        'reading': 'とる',
        'meaning': 'coger, tomar (una clase, una nota)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Coger, quitar', pero también 'apuntarse a' una clase, 'tomar' notas y 「年を取る」 'cumplir años'."
      },
      {
        'kind': 'vocabulario',
        'jp': '呼ぶ',
        'reading': 'よぶ',
        'meaning': 'llamar (por su nombre); invitar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Llamar' por el nombre o para que alguien venga (「名前を呼ぶ」); también 'invitar' (「パーティーに呼ぶ」). Llamar por teléfono es 「電話をかける」."
      },
      {
        'kind': 'vocabulario',
        'jp': '困る',
        'reading': 'こまる',
        'meaning': 'tener problemas, estar en apuros',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'No saber qué hacer, estar en un apuro'. Muy usado como 「困っている」 y con condición: 「来られると困る」 'me viene mal que vengas'."
      },
      {
        'kind': 'vocabulario',
        'jp': '在る',
        'reading': 'ある',
        'meaning': 'haber, existir (cosas)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Existencia de cosas y hechos (「時間がある」 'tener tiempo'); para personas y animales se usa 「いる」. Casi siempre se escribe en kana, 「ある」."
      },
      {
        'kind': 'vocabulario',
        'jp': '寝る',
        'reading': 'ねる',
        'meaning': 'dormir / acostarse',
        'tipo': 'verbo',
        'ejemplo': '１１じに ねます',
        'literal': '11h-EN / me-acuesto',
        'uso': 'irse a la cama. Estar durmiendo ahora mismo es ねています'
      },
      {
        'kind': 'vocabulario',
        'jp': '居る',
        'reading': 'いる',
        'meaning': 'estar, haber (seres vivos)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Existencia de personas y animales (「猫がいる」); para cosas se usa 「ある」. Se escribe casi siempre en kana, 「いる」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '帰る',
        'reading': 'かえる',
        'meaning': 'regresar / volver a casa',
        'tipo': 'verbo',
        'ejemplo': 'うちに かえります',
        'literal': 'casa-A / vuelvo',
        'uso': 'volver al sitio al que perteneces (casa, país). Acaba en る pero es grupo 1: かえって'
      },
      {
        'kind': 'vocabulario',
        'jp': '引く',
        'reading': 'ひく',
        'meaning': 'tirar; restar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Tirar de' algo (「ドアを引く」), y además 「風邪を引く」 (coger un resfriado), 「辞書を引く」 (buscar en el diccionario), restar. Suena como 「弾く」 'tocar (piano, guitarra)'."
      },
      {
        'kind': 'vocabulario',
        'jp': '待つ',
        'reading': 'まつ',
        'meaning': 'esperar',
        'tipo': 'verbo',
        'ejemplo': 'ちょっと まって ください',
        'literal': 'un-momento / espera / por-favor',
        'uso': 'grupo 1 en つ: まって, まちます. Esa frase se oye cien veces al día'
      },
      {
        'kind': 'vocabulario',
        'jp': '押す',
        'reading': 'おす',
        'meaning': 'empujar, apretar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Empujar' y 'pulsar' (「ボタンを押す」). En las puertas japonesas, 「押す」 = empujar, 「引く」 = tirar."
      },
      {
        'kind': 'vocabulario',
        'jp': '持つ',
        'reading': 'もつ',
        'meaning': 'tener / sostener / llevar',
        'tipo': 'verbo',
        'ejemplo': 'かばんを もちます',
        'literal': 'bolso-OBJ / llevo',
        'uso': "sostener en la mano. 'Tener' en el sentido de poseer se dice もっています"
      },
      {
        'kind': 'vocabulario',
        'jp': '散歩',
        'reading': 'さんぽ (する)',
        'meaning': 'pasear',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '書く',
        'reading': 'かく',
        'meaning': 'escribir',
        'tipo': 'verbo',
        'ejemplo': 'なまえを かきます',
        'literal': 'nombre-OBJ / escribo',
        'uso': 'grupo 1 en く: かいて, かきます. Dibujar es el mismo かく pero se escribe 描く'
      },
      {
        'kind': 'vocabulario',
        'jp': '有る',
        'reading': 'ある',
        'meaning': 'haber, tener',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Haber, tener' cosas y hechos (「お金がある」). Para seres vivos, 「いる」. Se escribe casi siempre en kana, 「ある」."
      },
      {
        'kind': 'vocabulario',
        'jp': '来る',
        'reading': 'くる',
        'meaning': 'venir',
        'tipo': 'verbo',
        'ejemplo': 'ともだちが きます',
        'literal': 'amigo-SUJ / viene',
        'uso': 'acercarse a donde estás tú. Si eres tú quien va a casa del otro, en japonés es いく'
      },
      {
        'kind': 'vocabulario',
        'jp': '渡す',
        'reading': 'わたす',
        'meaning': 'entregar, pasar (algo a alguien)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Transitivo: 'entregar algo en mano' (「書類を渡す」). Cruzar (una calle, un puente) es 「渡る」."
      },
      {
        'kind': 'vocabulario',
        'jp': '無くす',
        'reading': 'なくす',
        'meaning': 'perder (algo)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Perder' algo por descuido (「かぎを無くす」). Que algo 'desaparezca' solo es 「無くなる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '聞く',
        'reading': 'きく',
        'meaning': 'escuchar / preguntar',
        'tipo': 'verbo',
        'ejemplo': 'おんがくを ききます',
        'literal': 'música-OBJ / escucho',
        'uso': "dos sentidos: escuchar algo, y preguntar a alguien (せんせいに ききます = 'le pregunto al profe')"
      },
      {
        'kind': 'vocabulario',
        'jp': '行く',
        'reading': 'いく',
        'meaning': 'ir',
        'tipo': 'verbo',
        'ejemplo': 'がっこうに いきます',
        'literal': 'escuela-A / voy',
        'uso': 'alejarte de donde estás. Su forma-て es la única irregular del grupo 1: いって'
      },
      {
        'kind': 'vocabulario',
        'jp': '見せる',
        'reading': 'みせる',
        'meaning': 'mostrar, enseñar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mostrar' algo a alguien a propósito (「写真を見せる」). Que algo 'se vea' o 'poder ver' es 「見える」."
      },
      {
        'kind': 'vocabulario',
        'jp': '見る',
        'reading': 'みる',
        'meaning': 'ver / mirar',
        'tipo': 'verbo',
        'ejemplo': 'テレビを みます',
        'literal': 'tele-OBJ / veo',
        'uso': 'mirar con intención. Lo que se ve sin querer, lo que está a la vista, es みえる'
      },
      {
        'kind': 'vocabulario',
        'jp': '言う',
        'reading': 'いう',
        'meaning': 'decir',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Se pronuncia 「ゆう」. En 「～という」 sirve para citar o para presentar un nombre (「田中という人」).'
      },
      {
        'kind': 'vocabulario',
        'jp': '話',
        'reading': 'はなし',
        'meaning': 'conversación, historia',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '話す',
        'reading': 'はなす',
        'meaning': 'hablar',
        'tipo': 'verbo',
        'ejemplo': 'にほんごを はなします',
        'literal': 'japonés-OBJ / hablo',
        'uso': 'hablar un idioma o contar algo. Charlar CON alguien lleva と: ともだちと はなす'
      },
      {
        'kind': 'vocabulario',
        'jp': '読む',
        'reading': 'よむ',
        'meaning': 'leer',
        'tipo': 'verbo',
        'ejemplo': 'ほんを よみます',
        'literal': 'libro-OBJ / leo',
        'uso': "grupo 1 en む: よんで. También 'leer' el ambiente de una sala: くうきを よむ"
      },
      {
        'kind': 'vocabulario',
        'jp': '買う',
        'reading': 'かう',
        'meaning': 'comprar',
        'tipo': 'verbo',
        'ejemplo': 'スーパーで くつを かいます',
        'literal': 'súper-EN / zapatos-OBJ / compro',
        'uso': 'grupo 1 en う: かって, かいます. El sitio donde compras lleva で'
      },
      {
        'kind': 'vocabulario',
        'jp': '起きる',
        'reading': 'おきる',
        'meaning': 'levantarse / despertarse',
        'tipo': 'verbo',
        'ejemplo': '６じに おきます',
        'literal': '6h-EN / me-levanto',
        'uso': "levantarse de dormir; también 'ocurrir' algo (じこが おきる = 'pasa un accidente')"
      },
      {
        'kind': 'vocabulario',
        'jp': '食べる',
        'reading': 'たべる',
        'meaning': 'comer',
        'tipo': 'verbo',
        'ejemplo': 'パンを たべます',
        'literal': 'pan-OBJ / como',
        'uso': 'grupo 2: quitas る y pones ます. Comer con la boca; tomarse una medicina es のむ, no たべる'
      },
      {
        'kind': 'vocabulario',
        'jp': '飲む',
        'reading': 'のむ',
        'meaning': 'beber',
        'tipo': 'verbo',
        'ejemplo': 'みずを のみます',
        'literal': 'agua-OBJ / bebo',
        'uso': "en japonés se 'beben' también la sopa, las pastillas y hasta el tabaco (たばこを のむ)"
      }
    ]
  },
  {
    'id': 'verbos_movimiento_objeto_n5',
    'nombre': 'Verbos de movimiento y objeto N5',
    'funcion': 'moverte por la ciudad, usar cosas y describir acciones con objetos, trayecto y salida',
    'frases_hechas': [
      {
        'jp': 'ちょっと待って',
        'uso': 'cuando necesitas retener a alguien o hacer una pausa antes de salir'
      },
      {'jp': 'どこに行く？', 'uso': 'la pregunta básica para moverse entre sitios'},
      {'jp': 'それを使ってください', 'uso': 'pidiendo usar algo concreto'},
      {'jp': 'ここで待ってて', 'uso': 'dejar a alguien esperando en una zona concreta'}
    ],
    'prerequisito': 'verbos_n5',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'かぶる',
        'reading': 'かぶる',
        'meaning': 'ponerse en la cabeza / cubrirse',
        'tipo': 'verbo',
        'ejemplo': 'ぼうしを かぶります',
        'literal': 'gorra-OBJ / me-pongo',
        'uso': 'sombreros, gorras, etc. El verbo va con la cabeza o la prenda'
      },
      {
        'kind': 'vocabulario',
        'jp': 'はく',
        'reading': 'はく',
        'meaning': 'poner(se) / llevar (pantalones, zapatos)',
        'tipo': 'verbo',
        'ejemplo': 'くつを はきます',
        'literal': 'zapatos-OBJ / me-pongo',
        'uso': 'vestido y calzado por encima de pies o piernas. No todos los verbos se usan igual'
      },
      {
        'kind': 'vocabulario',
        'jp': '乗る',
        'reading': 'のる',
        'meaning': 'subir / montarse',
        'tipo': 'verbo',
        'ejemplo': 'バスに のります',
        'literal': 'autobús-A / me-subo',
        'uso': 'montarse en un transporte o en un elevador. Con caballos también se usa のる'
      },
      {
        'kind': 'vocabulario',
        'jp': '休む',
        'reading': 'やすむ',
        'meaning': 'descansar / tomar descanso',
        'tipo': 'verbo',
        'ejemplo': '今日は 休みます',
        'literal': 'hoy / descanso',
        'uso': "descansar, no necesariamente dormir. En el trabajo significa 'tomarse un día libre'"
      },
      {
        'kind': 'vocabulario',
        'jp': '使う',
        'reading': 'つかう',
        'meaning': 'usar',
        'tipo': 'verbo',
        'ejemplo': 'コンピューターを つかいます',
        'literal': 'ordenador-OBJ / uso',
        'uso': 'usar una herramienta o un servicio; el objeto que usa lleva を'
      },
      {
        'kind': 'vocabulario',
        'jp': '入る',
        'reading': 'はいる',
        'meaning': 'entrar / entrar en',
        'tipo': 'verbo',
        'ejemplo': '部屋に はいります',
        'literal': 'habitación-A / entro',
        'uso': 'entrar a un sitio. Como verbo útil para lugares y horarios: ８じに はいる'
      },
      {
        'kind': 'vocabulario',
        'jp': '出る',
        'reading': 'でる',
        'meaning': 'salir / irse / aparecer',
        'tipo': 'verbo',
        'ejemplo': '学校を でます',
        'literal': 'escuela-OBJ / salgo',
        'uso': "salir de un sitio. También 'aparecer' o 'surgir' en un contexto"
      },
      {
        'kind': 'vocabulario',
        'jp': '座る',
        'reading': 'すわる',
        'meaning': 'sentarse',
        'tipo': 'verbo',
        'ejemplo': 'ここに すわってください',
        'literal': 'aquí-EN / siéntate / por-favor',
        'uso': 'sentarse en una silla o en el suelo. El verbo se usa para tolerar una situación: すわるは difícil'
      },
      {
        'kind': 'vocabulario',
        'jp': '忘れる',
        'reading': 'わすれる',
        'meaning': 'olvidar',
        'tipo': 'verbo',
        'ejemplo': 'かばんを わすれました',
        'literal': 'bolso-OBJ / olvidé',
        'uso': "olvidar algo; el objeto directo lleva を. También se usa para 'dejar de acordarse'"
      },
      {
        'kind': 'vocabulario',
        'jp': '教える',
        'reading': 'おしえる',
        'meaning': 'enseñar / decir',
        'tipo': 'verbo',
        'ejemplo': '先生が じゅんばんを おしえます',
        'literal': 'profesor-SUJ / orden-OBJ / enseña',
        'uso': 'enseñar a alguien o explicar cómo se hace. El objeto directo es lo que enseñan'
      },
      {
        'kind': 'vocabulario',
        'jp': '泳ぐ',
        'reading': 'およぐ',
        'meaning': 'nadar',
        'tipo': 'verbo',
        'ejemplo': 'プールで およぎます',
        'literal': 'piscina-EN / nado',
        'uso': 'nadar. Se usa con で por el sitio en el que ocurre la acción'
      },
      {
        'kind': 'vocabulario',
        'jp': '着る',
        'reading': 'きる',
        'meaning': 'ponerse / llevar puesto (ropa de torso)',
        'tipo': 'verbo',
        'ejemplo': 'シャツを きます',
        'literal': 'camisa-OBJ / me-pongo',
        'uso': 'ropa superior o prendas que se ponen sobre el cuerpo; el verbo cambia según la prenda'
      },
      {
        'kind': 'vocabulario',
        'jp': '知る',
        'reading': 'しる',
        'meaning': 'saber / conocer',
        'tipo': 'verbo',
        'ejemplo': 'その 人を しっています',
        'literal': 'esa / persona-OBJ / conozco',
        'uso': "saber o conocer algo. No confundir con わかる: 知る es más 'conocer' / 'tener noticia'"
      },
      {
        'kind': 'vocabulario',
        'jp': '立つ',
        'reading': 'たつ',
        'meaning': 'levantarse / ponerse de pie',
        'tipo': 'verbo',
        'ejemplo': 'みんな 立ちました',
        'literal': 'todos / se-levantaron',
        'uso': "ponerse de pie; también 'estar en pie' o 'tener lugar' en un contexto"
      },
      {
        'kind': 'vocabulario',
        'jp': '走る',
        'reading': 'はしる',
        'meaning': 'correr',
        'tipo': 'verbo',
        'ejemplo': '駅まで 走ります',
        'literal': 'estación-hasta / corro',
        'uso': 'correr a pie. Es un verbo importante para expresar rapidez o prisa'
      },
      {
        'kind': 'vocabulario',
        'jp': '遊ぶ',
        'reading': 'あそぶ',
        'meaning': 'jugar / divertirse',
        'tipo': 'verbo',
        'ejemplo': 'ともだちと あそびます',
        'literal': 'amigos-CON / me-divierto',
        'uso': "jugar o pasarlo bien. No se usa para 'jugar a la consola' cuando se dice する"
      },
      {
        'kind': 'vocabulario',
        'jp': '閉める',
        'reading': 'しめる',
        'meaning': 'cerrar / cerrar con llave',
        'tipo': 'verbo',
        'ejemplo': 'ドアを しめます',
        'literal': 'puerta-OBJ / cierro',
        'uso': 'cerrar un objeto o una puerta. Se usa mucho en la casa y al salir'
      },
      {
        'kind': 'vocabulario',
        'jp': '開ける',
        'reading': 'あける',
        'meaning': 'abrir',
        'tipo': 'verbo',
        'ejemplo': 'まどを あけます',
        'literal': 'ventana-OBJ / abro',
        'uso': 'abrir; muy útil para puertas, ventanas y paquetes'
      },
      {
        'kind': 'vocabulario',
        'jp': '降りる',
        'reading': 'おりる',
        'meaning': 'bajar / apearse',
        'tipo': 'verbo',
        'ejemplo': '駅で おりました',
        'literal': 'estación-EN / bajé',
        'uso': "bajar del transporte o del tren. También se usa para 'bajar de un vehículo'"
      }
    ]
  },
  {
    'id': 'adjetivos_n5',
    'nombre': 'Adjetivos N5 (い y な)',
    'funcion': 'describir cosas y personas, y decir con claridad qué te gusta y qué no',
    'frases_hechas': [
      {'jp': 'すごい', 'uso': 'vale para todo: admiración, sorpresa o susto'},
      {'jp': 'かわいい', 'uso': "no es solo 'mono': se dice de casi cualquier cosa que gusta"},
      {'jp': 'びみょう', 'uso': "'regulero', ni bien ni mal; muy útil para no mojarte"},
      {'jp': '大丈夫です', 'uso': "también sirve para rechazar algo con educación: 'no, gracias'"}
    ],
    'prerequisito': 'verbos_movimiento_objeto_n5',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'いい; よい',
        'reading': 'いい / よい',
        'meaning': 'bueno, bien',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': '「いい」 solo vale en presente afirmativo; para lo demás cambia a 「よい」: 「よくない」「よかった」「よくて」. 「よい」 suena algo más formal.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'うるさい',
        'reading': 'うるさい',
        'meaning': 'ruidoso, molesto',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Ruidoso, molesto'; también 'quisquilloso' con algo (「味にうるさい」). 「うるさい！」 a secas es un '¡cállate!'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'つまらない',
        'reading': 'つまらない',
        'meaning': 'aburrido; insignificante',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Aburrido, insignificante'. En 「つまらないものですが」 es la fórmula humilde al entregar un regalo."
      },
      {
        'kind': 'vocabulario',
        'jp': 'にぎやか',
        'reading': 'にぎやか',
        'meaning': 'animado, bullicioso (な)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'りっぱ',
        'reading': 'りっぱ',
        'meaning': 'espléndido, magnífico (な)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '丈夫',
        'reading': 'じょうぶ',
        'meaning': 'fuerte, resistente, duradero (な)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '上手',
        'reading': 'じょうず',
        'meaning': 'hábil, bueno haciendo algo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'No se usa para uno mismo (suena a fanfarronada); ahí se dice 「できる」. De otra persona es un elogio: 「日本語が上手ですね」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '下手',
        'reading': 'へた',
        'meaning': 'torpe, malo haciendo algo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Sí se puede decir de uno mismo, como modestia. Soltárselo a otro a la cara es grosero.'
      },
      {
        'kind': 'vocabulario',
        'jp': '丸い; 円い',
        'reading': 'まるい',
        'meaning': 'redondo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '低い',
        'reading': 'ひくい',
        'meaning': 'bajo (de altura)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '危ない',
        'reading': 'あぶない',
        'meaning': 'peligroso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Peligroso'; gritado, 「あぶない！」 es '¡cuidado!'."
      },
      {
        'kind': 'vocabulario',
        'jp': '厚い',
        'reading': 'あつい',
        'meaning': 'grueso; cálido (de corazón)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Grueso' (「厚い本」). Se pronuncia como 「暑い」 'caluroso' y 「熱い」 'caliente'."
      },
      {
        'kind': 'vocabulario',
        'jp': '古い',
        'reading': 'ふるい',
        'meaning': 'viejo / antiguo (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'この ビルは ふるいです',
        'literal': 'este / edificio-TEMA / viejo-es',
        'uso': 'solo cosas. Una persona mayor nunca es ふるい: es としうえ o おとしより'
      },
      {
        'kind': 'vocabulario',
        'jp': '可愛い',
        'reading': 'かわいい',
        'meaning': 'mono, adorable',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '大きい',
        'reading': 'おおきい',
        'meaning': 'grande (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'おおきい いえですね',
        'literal': 'grande / casa-es-¿verdad?',
        'uso': 'adj-い: va pegado delante del sustantivo, sin nada en medio'
      },
      {
        'kind': 'vocabulario',
        'jp': '大きな',
        'reading': 'おおきな',
        'meaning': 'grande',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Solo delante de un nombre (「大きな家」); no se predica: para eso, 「大きい」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '大変',
        'reading': 'たいへん',
        'meaning': 'muy; duro, difícil',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Como adverbio, 'muy' (「大変うれしい」, formal); como adjetivo-な, 'duro, penoso' (「大変な仕事」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '小さい',
        'reading': 'ちいさい',
        'meaning': 'pequeño (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'ちいさい こえで はなします',
        'literal': 'pequeña / voz-CON / hablo',
        'uso': "también 'bajito' de volumen y 'de poca edad'"
      },
      {
        'kind': 'vocabulario',
        'jp': '小さな',
        'reading': 'ちいさな',
        'meaning': 'pequeño',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Solo delante de un nombre (「小さな声」); para predicar, 「小さい」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '忙しい',
        'reading': 'いそがしい',
        'meaning': 'ocupado',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '悪い',
        'reading': 'わるい',
        'meaning': 'malo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '新しい',
        'reading': 'あたらしい',
        'meaning': 'nuevo (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'あたらしい ケータイを かいました',
        'literal': 'nuevo / móvil-OBJ / compré',
        'uso': 'nuevo de recién hecho o recién comprado. Algo usado que es nuevo para ti no es あたらしい'
      },
      {
        'kind': 'vocabulario',
        'jp': '明るい',
        'reading': 'あかるい',
        'meaning': 'alegre, luminoso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Luminoso' y también 'alegre, abierto' de carácter (「明るい人」). Opuesto: 「暗い」."
      },
      {
        'kind': 'vocabulario',
        'jp': '易しい',
        'reading': 'やさしい',
        'meaning': 'fácil, sencillo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Fácil'. Se pronuncia igual que 「優しい」 'amable'; el contexto los distingue."
      },
      {
        'kind': 'vocabulario',
        'jp': '暗い',
        'reading': 'くらい',
        'meaning': 'oscuro',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '有名',
        'reading': 'ゆうめい',
        'meaning': 'famoso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '楽しい',
        'reading': 'たのしい',
        'meaning': 'divertido',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '汚い',
        'reading': 'きたない',
        'meaning': 'sucio',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '短い',
        'reading': 'みじかい',
        'meaning': 'corto',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '綺麗',
        'reading': 'きれい',
        'meaning': 'bonito, limpio',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '軽い',
        'reading': 'かるい',
        'meaning': 'ligero, leve',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '重い',
        'reading': 'おもい',
        'meaning': 'pesado',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '長い',
        'reading': 'ながい',
        'meaning': 'largo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '難しい',
        'reading': 'むずかしい',
        'meaning': 'difícil',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '静か',
        'reading': 'しずか',
        'meaning': 'tranquilo, silencioso (な)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '面白い',
        'reading': 'おもしろい',
        'meaning': 'interesante, divertido',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '高い',
        'reading': 'たかい',
        'meaning': 'alto; caro',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'conjugacion_adj',
    'nombre': 'Conjugación de adjetivos い y な',
    'funcion': 'contar cómo fue algo y cómo no fue: si la comida estaba rica, si el día se hizo duro',
    'frases_hechas': [
      {'jp': 'よかった', 'uso': "'menos mal', alivio por algo que salió bien"},
      {'jp': 'どうだった？', 'uso': "'¿qué tal estuvo?', la pregunta con la que empieza cualquier charla"},
      {'jp': 'まあまあ', 'uso': "'ni fu ni fa', la respuesta honesta y educada"},
      {'jp': 'さいこう！', 'uso': "'lo mejor', cuando algo te ha encantado de verdad"}
    ],
    'prerequisito': 'adjetivos_n5',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜やすいです',
        'meaning': "'fácil de ~': verbo en raíz-ます + やすい",
        'ejemplo': 'この ペンは 書きやすいです',
        'literal': 'este / boli-TEMA / fácil-de-escribir-es',
        'uso': 'Se forma sobre la raíz de 「ます」 (「かきます」 -> 「かき」+「やすい」) y se conjuga como adjetivo-い. Opuesto: 「にくい」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜にくいです',
        'meaning': "'difícil de ~ / cuesta ~': verbo en raíz-ます + にくい",
        'ejemplo': 'この くすりは 飲みにくいです',
        'literal': 'esta / medicina-TEMA / difícil-de-tragar-es',
        'uso': "No es que no se pueda, es que resulta incómodo o costoso; para 'no puedo' va el potencial. Se conjuga como adjetivo-い: 「にくかった」."
      },
      {
        'kind': 'gramatica',
        'jp': '〜くなります',
        'meaning': "cambio de estado con adjetivo-い: 'volverse ~ / ponerse ~'",
        'ejemplo': 'はるに なると あたたかくなります',
        'literal': 'primavera-A / al-llegar / se-vuelve-cálido',
        'uso': 'El adjetivo-い pierde 「い」, toma 「く」 y se le añade 「なる」. El cambio ocurre solo; si alguien lo provoca, es 「くします」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜になります',
        'meaning': "cambio de estado con adjetivo-な o sustantivo: 'llegar a ser ~ / convertirse en ~'",
        'ejemplo': 'らいねん 二十歳に なります',
        'literal': 'año-que-viene / veinte-años-A / me-hago',
        'uso': 'Para adjetivo-な y sustantivos: 「に」 + 「なる」. Para adjetivo-い es 「くなります」. Muy usado con edad, hora y profesión.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜くします',
        'meaning': "provocar un cambio con adjetivo-い: 'hacer que algo quede ~'",
        'ejemplo': 'へやを あかるくします',
        'literal': 'habitación-OBJ / la-pongo-luminosa',
        'uso': 'El adjetivo-い pierde 「い」, toma 「く」 y se le añade 「する」: alguien cambia algo a propósito, frente a 「くなります」, que pasa solo.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜にします',
        'meaning': "provocar un cambio, o elegir: 'dejar algo ~ / decidirse por ~'",
        'ejemplo': 'わたしは コーヒーに します',
        'literal': 'yo-TEMA / café-A / me-decido',
        'uso': 'Dos usos: cambiar algo aposta (「しずかにしてください」) y elegir al pedir (「わたしはこれにします」). Con adjetivo-な y sustantivos.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜くて',
        'meaning': 'forma-て del adjetivo-い: enlaza cualidades o da un motivo',
        'ejemplo': 'この へやは ひろくて あかるいです',
        'literal': 'esta / habitación-TEMA / ancha-y / luminosa-es',
        'uso': 'El adjetivo-い pasa a 「くて」 para encadenar dos cualidades o dar una causa (「あたまがいたくてねました」). Nunca 「いで」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜で（な形容詞）',
        'meaning': 'forma-て del adjetivo-な y del sustantivo: enlaza o da un motivo',
        'ejemplo': 'この まちは しずかで きれいです',
        'literal': 'esta / ciudad-TEMA / tranquila-y / bonita-es',
        'uso': 'El adjetivo-な y los sustantivos pierden 「だ」 y toman 「で」 (「げんきでしんせつなひと」). Es el equivalente de 「くて」 para el otro tipo de adjetivo.'
      }
    ]
  },
  {
    'id': 'familia_personas',
    'nombre': 'Personas y familia N5',
    'funcion': 'hablar de tu familia y de tus amigos, y preguntar por los de otra persona',
    'frases_hechas': [
      {'jp': '〜さん', 'uso': 'se pone a todo el mundo menos a uno mismo; olvidarlo suena brusco'},
      {'jp': 'うちの…', 'uso': "'el mío de casa', al hablar de tu propia familia"},
      {'jp': 'お名前は', 'uso': "'¿y tú, cómo te llamas?', sin necesidad de más frase"},
      {'jp': 'ご家族は', 'uso': "'¿y tu familia?'; el ご delante es respeto por lo del otro"}
    ],
    'prerequisito': 'conjugacion_adj',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'おじいさん',
        'reading': 'おじいさん',
        'meaning': 'abuelo / anciano',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Abuelo' o señor mayor. Cuidado con la vocal: 「おじさん」 (corta) es 'tío / señor'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'おばあさん',
        'reading': 'おばあさん',
        'meaning': 'abuela / anciana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Abuela' o señora mayor. 「おばさん」 (corta) es 'tía / señora'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'お兄さん',
        'reading': 'おにいさん',
        'meaning': 'hermano mayor (de otra persona, cortés)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'El hermano mayor de otra persona, o para dirigirte al tuyo. Del propio, hacia fuera, 「兄」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お姉さん',
        'reading': 'おねえさん',
        'meaning': 'hermana mayor (de otra persona, cortés)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La hermana mayor de otro, o para llamar a la tuya. De la propia, hacia fuera, 「姉」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お母さん',
        'reading': 'おかあさん',
        'meaning': 'madre (de otra persona)',
        'tipo': 'sustantivo',
        'ejemplo': 'お母さんに 電話しました',
        'literal': 'madre-A / llamé',
        'uso': 'forma respetuosa. El de uno mismo es 母 (はは)'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お父さん',
        'reading': 'おとうさん',
        'meaning': 'padre (de otra persona)',
        'tipo': 'sustantivo',
        'ejemplo': 'お父さんは 何をしていますか',
        'literal': 'padre-TEMA / ¿qué-hace?',
        'uso': 'forma respetuosa. El de uno mismo es 父 (ちち)'
      },
      {
        'kind': 'vocabulario',
        'jp': 'みんな',
        'reading': 'みんな',
        'meaning': 'todos, todo el mundo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Informal para 'todos'; ante un grupo al que tratas de usted, 「皆さん」."
      },
      {
        'kind': 'vocabulario',
        'jp': '両親',
        'reading': 'りょうしん',
        'meaning': 'padres (ambos)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mis padres'. Los de otra persona, con respeto, 「ご両親」."
      },
      {
        'kind': 'vocabulario',
        'jp': '人',
        'reading': 'ひと',
        'meaning': 'persona',
        'tipo': 'sustantivo',
        'ejemplo': '日本人は どのくらい いますか',
        'literal': 'japoneses-SUJ / ¿cuántos-aprox / hay?',
        'uso': 'persona cualquiera. Para contar personas lleva contador ～人'
      },
      {
        'kind': 'vocabulario',
        'jp': '伯母さん; 叔母さん',
        'reading': 'おばさん',
        'meaning': 'tía',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Tía'; 「伯母」 si es mayor que tu padre o madre, 「叔母」 si es menor, pero se lee igual. No alargues la vocal: 「おばあさん」 es 'abuela'."
      },
      {
        'kind': 'vocabulario',
        'jp': '伯父; 叔父さん',
        'reading': 'おじさん',
        'meaning': 'tío',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Tío'; 「伯父」 mayor que tu padre o madre, 「叔父」 menor. 「おじいさん」, con vocal larga, es 'abuelo'."
      },
      {
        'kind': 'vocabulario',
        'jp': '兄',
        'reading': 'あに',
        'meaning': 'hermano mayor (propio)',
        'tipo': 'sustantivo',
        'ejemplo': '兄は 会社員です',
        'literal': 'hermano-TEMA / empleado-es',
        'uso': 'tu hermano mayor. El de otro es お兄さん'
      },
      {
        'kind': 'vocabulario',
        'jp': '兄弟',
        'reading': 'きょうだい',
        'meaning': 'hermanos (hermano y hermana)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Hermanos' en general, e incluye a las hermanas. 「ご兄弟」 para los de otro."
      },
      {
        'kind': 'vocabulario',
        'jp': '先生',
        'reading': 'せんせい',
        'meaning': 'profesor/a / maestro/a',
        'tipo': 'sustantivo',
        'ejemplo': '先生は 何時に 来ますか',
        'literal': 'profesor-TEMA / ¿a-qué-hora / viene?',
        'uso': 'maestro, profesor o doctor. Dirigirse con 先生 es respetuoso'
      },
      {
        'kind': 'vocabulario',
        'jp': '友達',
        'reading': 'ともだち',
        'meaning': 'amigo/a',
        'tipo': 'sustantivo',
        'ejemplo': '友達と 遊びました',
        'literal': 'amigo-CON / jugué',
        'uso': 'amigo informal. Amigo de verdad es 親友 (しんゆう)'
      },
      {
        'kind': 'vocabulario',
        'jp': '大人',
        'reading': 'おとな',
        'meaning': 'adulto',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Adulto'; 「大人になる」 'hacerse mayor'. 「大人しい」 es otra palabra: 'tranquilo, dócil'."
      },
      {
        'kind': 'vocabulario',
        'jp': '奥さん',
        'reading': 'おくさん',
        'meaning': 'esposa de otra persona (cortés)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La mujer de otro. A la propia esposa, hacia fuera, se la llama 「妻」 o 「家内」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '女',
        'reading': 'おんな',
        'meaning': 'mujer',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'A secas puede sonar brusco al referirse a alguien; en trato normal, 「女の人」 o 「女性」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '女の子',
        'reading': 'おんなのこ',
        'meaning': 'niña',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '妹',
        'reading': 'いもうと',
        'meaning': 'hermana menor (propia)',
        'tipo': 'sustantivo',
        'ejemplo': '妹は 中学生です',
        'literal': 'hermana-menor-TEMA / estudiante-de-ESO-es',
        'uso': 'tu hermana menor. La de otro es 妹さん'
      },
      {
        'kind': 'vocabulario',
        'jp': '姉',
        'reading': 'あね',
        'meaning': 'hermana mayor (propia)',
        'tipo': 'sustantivo',
        'ejemplo': '姉と 話しました',
        'literal': 'hermana-CON / hablé',
        'uso': 'tu hermana mayor. La de otro es お姉さん'
      },
      {
        'kind': 'vocabulario',
        'jp': '子供',
        'reading': 'こども',
        'meaning': 'niño/a / hijo/a',
        'tipo': 'sustantivo',
        'ejemplo': '子供が いますか',
        'literal': 'niño-SUJ / ¿tienes?',
        'uso': 'niño o hijo. Cuando crecen se dice 大人 (おとな)'
      },
      {
        'kind': 'vocabulario',
        'jp': '学生',
        'reading': 'がくせい',
        'meaning': 'estudiante',
        'tipo': 'sustantivo',
        'ejemplo': '彼は 大学の 学生です',
        'literal': 'él-TEMA / universidad-DE / estudiante-es',
        'uso': 'estudiante de instituto o universidad'
      },
      {
        'kind': 'vocabulario',
        'jp': '家庭',
        'reading': 'かてい',
        'meaning': 'hogar, familia',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '家族',
        'reading': 'かぞく',
        'meaning': 'familia',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mi familia'. La de otra persona, 「ご家族」."
      },
      {
        'kind': 'vocabulario',
        'jp': '弟',
        'reading': 'おとうと',
        'meaning': 'hermano menor (propio)',
        'tipo': 'sustantivo',
        'ejemplo': '弟に 手伝ってもらいました',
        'literal': 'hermano-menor-A / me-ayudó',
        'uso': 'tu hermano menor. El de otro es 弟さん'
      },
      {
        'kind': 'vocabulario',
        'jp': '母',
        'reading': 'はは',
        'meaning': 'madre (mía)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mi madre', al hablar de ella con otros. A la tuya en persona la llamas 「お母さん」; la de otra persona también es 「お母さん」."
      },
      {
        'kind': 'vocabulario',
        'jp': '父',
        'reading': 'ちち',
        'meaning': 'padre (mío)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mi padre', al hablar de él con otros. En persona le dices 「お父さん」; al padre de otro, 「お父さん」."
      },
      {
        'kind': 'vocabulario',
        'jp': '生まれる',
        'reading': 'うまれる',
        'meaning': 'nacer',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Nacer'; el lugar lleva 「で」 y a menudo va en pasado: 「東京で生まれました」."
      },
      {
        'kind': 'vocabulario',
        'jp': '男',
        'reading': 'おとこ',
        'meaning': 'hombre',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'A secas resulta seco para referirse a alguien; mejor 「男の人」 o 「男性」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '男の子',
        'reading': 'おとこのこ',
        'meaning': 'niño',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '結婚',
        'reading': 'けっこん (する)',
        'meaning': 'casarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '若い',
        'reading': 'わかい',
        'meaning': 'joven',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '～たち',
        'reading': '～たち',
        'meaning': 'sufijo de plural (私たち = nosotros)',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Plural solo para personas y seres vivos (「子供たち」), nunca para objetos. Con 「私」 forma 'nosotros'."
      }
    ]
  },
  {
    'id': 'tiempo_lugar',
    'nombre': 'Tiempo y lugar N5',
    'funcion': 'quedar con alguien: decir cuándo y dónde, y preguntar por un sitio',
    'frases_hechas': [
      {'jp': '何時ですか', 'uso': "'¿qué hora es?' y también '¿a qué hora?'"},
      {'jp': 'ここはどこですか', 'uso': "'¿dónde estoy?', cuando te pierdes"},
      {'jp': 'また今度', 'uso': "'otro día'; posterga sin cerrar la puerta, y a veces significa que no"},
      {'jp': 'ちょっと遠いですね', 'uso': "'queda un poco lejos'; forma suave de decir que no te apetece"}
    ],
    'prerequisito': 'familia_personas',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'かかる',
        'reading': 'かかる',
        'meaning': 'tardar, costar (tiempo o dinero)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Pareja intransitiva de 「かける」: 「時間がかかる」「お金がかかる」, 「かぎがかかる」 (estar cerrado con llave), 「電話がかかってくる」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'そば',
        'reading': 'そば',
        'meaning': 'cerca, al lado; (también: soba, fideos)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cerca de', a poca distancia (「駅のそば」); más vago que 「隣」 o 「横」. Se pronuncia como 「そば」 los fideos."
      },
      {
        'kind': 'vocabulario',
        'jp': '一緒',
        'reading': 'いっしょ',
        'meaning': 'junto, a la vez',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Casi siempre 「一緒に」 'juntos, a la vez': 「一緒に行く」."
      },
      {
        'kind': 'vocabulario',
        'jp': '上',
        'reading': 'うえ',
        'meaning': 'encima / arriba',
        'tipo': 'sustantivo',
        'ejemplo': '本が 机の 上に あります',
        'literal': 'libro-SUJ / mesa-DE / encima-EN / hay',
        'uso': 'posición. Va con の o に según la frase: 机の上, 机の上にある'
      },
      {
        'kind': 'vocabulario',
        'jp': '下',
        'reading': 'した',
        'meaning': 'debajo / abajo',
        'tipo': 'sustantivo',
        'ejemplo': '猫が ベッドの 下に います',
        'literal': 'gato-SUJ / cama-DE / debajo-EN / está',
        'uso': 'posición vertical opuesta a 上. Muy útil para dar indicaciones'
      },
      {
        'kind': 'vocabulario',
        'jp': '中',
        'reading': 'なか',
        'meaning': 'dentro / en medio',
        'tipo': 'sustantivo',
        'ejemplo': '教室の 中に います',
        'literal': 'aula-DE / dentro-EN / estoy',
        'uso': "alude a un espacio interior. 〜の中 = 'dentro de'"
      },
      {
        'kind': 'vocabulario',
        'jp': '今',
        'reading': 'いま',
        'meaning': 'ahora',
        'tipo': 'sustantivo',
        'ejemplo': '今 何時ですか',
        'literal': 'ahora / ¿qué-hora-es?',
        'uso': 'ahora mismo. Para referirse al presente en general se usa 現在 (げんざい)'
      },
      {
        'kind': 'vocabulario',
        'jp': '会う',
        'reading': 'あう',
        'meaning': 'quedar, verse con alguien',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La persona con quien te ves lleva 「に」, no 「を」: 「友達に会う」. 「と会う」 sugiere una cita acordada entre ambos.'
      },
      {
        'kind': 'vocabulario',
        'jp': '先',
        'reading': 'さき',
        'meaning': 'futuro; antes, primero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Palabra muy elástica: 'la punta', 'más adelante', 'antes / primero' (「お先に」), 'hace un rato' (「先ほど」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '公園',
        'reading': 'こうえん',
        'meaning': 'parque',
        'tipo': 'sustantivo',
        'ejemplo': '公園で あそびました',
        'literal': 'parque-EN / jugué',
        'uso': 'parque público. Lleva で para la acción que ocurre allí'
      },
      {
        'kind': 'vocabulario',
        'jp': '初め; 始め',
        'reading': 'はじめ',
        'meaning': 'principio, comienzo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Sustantivo: 'el comienzo' (「月の初め」). 'Por primera vez' es 「初めて」, con 「て」."
      },
      {
        'kind': 'vocabulario',
        'jp': '初めて',
        'reading': 'はじめて',
        'meaning': 'por primera vez',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "Adverbio: 'por primera vez' (「初めて会う」). El sustantivo 'el principio' es 「初め」."
      },
      {
        'kind': 'vocabulario',
        'jp': '前',
        'reading': 'まえ',
        'meaning': 'delante / frente',
        'tipo': 'sustantivo',
        'ejemplo': '駅の 前に います',
        'literal': 'estación-DE / delante-EN / estoy',
        'uso': "delante de una cosa o de una persona. También 'antes' en el tiempo: まえに"
      },
      {
        'kind': 'vocabulario',
        'jp': '向こう',
        'reading': 'むこう',
        'meaning': 'allá / al otro lado / frente',
        'tipo': 'sustantivo',
        'ejemplo': '向こう側に あります',
        'literal': 'allá / lado-EN / está',
        'uso': 'dirigido a un sitio visible más lejos o al lado opuesto. Muy útil para dar direcciones'
      },
      {
        'kind': 'vocabulario',
        'jp': '外',
        'reading': 'そと',
        'meaning': 'fuera / exterior',
        'tipo': 'sustantivo',
        'ejemplo': '外で たってください',
        'literal': 'fuera-EN / ponte-de-pie / por-favor',
        'uso': "fuera del espacio. También 'exterior' o 'afuera de la casa'"
      },
      {
        'kind': 'vocabulario',
        'jp': '学校',
        'reading': 'がっこう',
        'meaning': 'escuela / colegio',
        'tipo': 'sustantivo',
        'ejemplo': '学校は どこですか',
        'literal': 'escuela-TEMA / ¿dónde-está?',
        'uso': 'institución educativa. Instituto es 高校 (こうこう), universidad es 大学 (だいがく)'
      },
      {
        'kind': 'vocabulario',
        'jp': '家',
        'reading': 'うち',
        'meaning': 'casa / hogar',
        'tipo': 'sustantivo',
        'ejemplo': '家に 帰りました',
        'literal': 'casa-A / volví',
        'uso': 'tu casa. Es coloquial. Formal es 家 (いえ). Mi casa se dice うちの家'
      },
      {
        'kind': 'vocabulario',
        'jp': '店',
        'reading': 'みせ',
        'meaning': 'tienda / establecimiento',
        'tipo': 'sustantivo',
        'ejemplo': 'この 店は 新しいです',
        'literal': 'esta / tienda-TEMA / nueva-es',
        'uso': 'comercio pequeño. Tienda de ropa es ふく屋 (ふくや)'
      },
      {
        'kind': 'vocabulario',
        'jp': '後',
        'reading': 'あと',
        'meaning': 'después, más tarde; el resto; desde entonces',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '後ろ',
        'reading': 'うしろ',
        'meaning': 'detrás / atrás',
        'tipo': 'sustantivo',
        'ejemplo': '後ろを 見てください',
        'literal': 'atrás-OBJ / mira / por-favor',
        'uso': "posición detrás de algo. En tiempo, うしろ significa 'después' o 'al final'"
      },
      {
        'kind': 'vocabulario',
        'jp': '所',
        'reading': 'ところ',
        'meaning': 'lugar',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Sitio, lugar'. Tras un verbo marca el momento: 「今、着いたところです」 'acabo de llegar'."
      },
      {
        'kind': 'vocabulario',
        'jp': '時間',
        'reading': 'じかん',
        'meaning': 'tiempo / hora',
        'tipo': 'sustantivo',
        'ejemplo': '時間が ありません',
        'literal': 'tiempo-SUJ / no-hay',
        'uso': 'tiempo disponible o cantidad de horas. Para la hora concreta usa 時 (じ)'
      },
      {
        'kind': 'vocabulario',
        'jp': '暇',
        'reading': 'ひま',
        'meaning': 'tiempo libre',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '横',
        'reading': 'よこ',
        'meaning': 'al lado; anchura',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Al costado de' algo, sin más (「駅の横」). No implica ser del mismo tipo, a diferencia de 「隣」."
      },
      {
        'kind': 'vocabulario',
        'jp': '次',
        'reading': 'つぎ',
        'meaning': 'siguiente',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '毎日',
        'reading': 'まいにち',
        'meaning': 'todos los días',
        'tipo': 'sustantivo',
        'ejemplo': '毎日 学校に 行きます',
        'literal': 'todos-los-días / escuela-A / voy',
        'uso': 'cada día. Tampoco lleva に. Otros: 毎週 (まいしゅう = cada semana), 毎月 (まいつき)'
      },
      {
        'kind': 'vocabulario',
        'jp': '病院',
        'reading': 'びょういん',
        'meaning': 'hospital',
        'tipo': 'sustantivo',
        'ejemplo': '病院に 行きました',
        'literal': 'hospital-A / fui',
        'uso': 'hospital o clínica. El doctor es 医者 (いしゃ), el enfermero es 看護師 (かんごし)'
      },
      {
        'kind': 'vocabulario',
        'jp': '終る',
        'reading': 'おわる',
        'meaning': 'terminar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '辺',
        'reading': 'へん',
        'meaning': 'zona, alrededores',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Por la zona de', impreciso: 「この辺」 'por aquí'."
      },
      {
        'kind': 'vocabulario',
        'jp': '近い',
        'reading': 'ちかい',
        'meaning': 'cerca',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '近く',
        'reading': 'ちかく',
        'meaning': 'cerca / vecindario',
        'tipo': 'sustantivo',
        'ejemplo': '駅の 近くに 住んでいます',
        'literal': 'estación-DE / cerca-EN / vivo',
        'uso': 'lugar cercano. Se usa como sustantivo o adverbio: 近くに, 近くまで'
      },
      {
        'kind': 'vocabulario',
        'jp': '遠い',
        'reading': 'とおい',
        'meaning': 'lejos',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '隣',
        'reading': 'となり',
        'meaning': 'al lado de',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Al lado' entre cosas del mismo tipo y en contacto: la casa de al lado, la persona sentada al lado (「隣の人」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '駅',
        'reading': 'えき',
        'meaning': 'estación de tren',
        'tipo': 'sustantivo',
        'ejemplo': '駅はどこですか',
        'literal': 'estación-TEMA / ¿dónde-está?',
        'uso': 'estación de ferrocarril. Lleva に para el destino (駅に行く)'
      },
      {
        'kind': 'vocabulario',
        'jp': '～側',
        'reading': '～がわ',
        'meaning': 'lado de ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '～前',
        'reading': '～まえ',
        'meaning': 'delante de ~ / antes de ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Delante de' en el espacio (「駅の前」) y 'antes de / hace' en el tiempo (「三日前」). No es 「名前」 'nombre'."
      }
    ]
  },
  {
    'id': 'comida_bebida',
    'nombre': 'Comida y bebida',
    'funcion': 'pedir en un restaurante, decir qué te gusta y qué no, y preguntar el precio',
    'frases_hechas': [
      {'jp': 'いただきます', 'uso': 'antes de comer, siempre, aunque comas sola'},
      {'jp': 'ごちそうさまでした', 'uso': 'al terminar de comer, y al despedirte de quien te invitó'},
      {'jp': 'おいしそう', 'uso': 'al ver la comida, antes de probarla'},
      {'jp': 'おかわり', 'uso': "'repito', para pedir otra ración o rellenar el vaso"}
    ],
    'prerequisito': 'tiempo_lugar',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'いかが',
        'reading': 'いかが',
        'meaning': '¿cómo? (cortés, para ofrecer algo)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': 'Versión cortés de 「どう」; se usa sobre todo para ofrecer: 「コーヒーはいかがですか」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お弁当',
        'reading': 'おべんとう',
        'meaning': 'fiambrera, almuerzo para llevar',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'お茶',
        'reading': 'おちゃ',
        'meaning': 'té (japonés)',
        'tipo': 'sustantivo',
        'ejemplo': 'お茶を どうぞ',
        'literal': 'té-OBJ / adelante',
        'uso': 'té verde, no el té negro. Té negro es 紅茶 (こうちゃ)'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お菓子',
        'reading': 'おかし',
        'meaning': 'dulces, chuches',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'お酒',
        'reading': 'おさけ',
        'meaning': 'sake, alcohol',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「さけ」 puede ser el sake de arroz en concreto o el alcohol en general. Casi siempre con 「お」: 「お酒を飲む」 = 'beber alcohol'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'まずい',
        'reading': 'まずい',
        'meaning': 'malo de sabor, soso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Malo de sabor'. También, coloquial, 'mala cosa, complicado' (「それはまずい」)."
      },
      {
        'kind': 'vocabulario',
        'jp': 'カレー',
        'reading': 'カレー',
        'meaning': 'curry',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'バター',
        'reading': 'バター',
        'meaning': 'mantequilla',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '卵',
        'reading': 'たまご',
        'meaning': 'huevo',
        'tipo': 'sustantivo',
        'ejemplo': '卵を 買ってください',
        'literal': 'huevo-OBJ / compra-por-favor',
        'uso': 'huevo de gallina. En japonés no se especifica si es singular o plural'
      },
      {
        'kind': 'vocabulario',
        'jp': '塩',
        'reading': 'しお',
        'meaning': 'sal',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '夕飯',
        'reading': 'ゆうはん',
        'meaning': 'cena',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '御飯',
        'reading': 'ごはん',
        'meaning': 'arroz cocido, comida',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「ごはん」 es tanto 'arroz cocido' como 'comida / comer' en general: 「ごはんを食べる」. Formal: 「食事」."
      },
      {
        'kind': 'vocabulario',
        'jp': '料理',
        'reading': 'りょうり',
        'meaning': 'cocina, plato (comida)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '昼御飯',
        'reading': 'ひるごはん',
        'meaning': 'almuerzo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '晩御飯',
        'reading': 'ばんごはん',
        'meaning': 'cena',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '朝御飯',
        'reading': 'あさごはん',
        'meaning': 'desayuno',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '果物',
        'reading': 'くだもの',
        'meaning': 'fruta',
        'tipo': 'sustantivo',
        'ejemplo': '果物を 買いました',
        'literal': 'fruta-OBJ / compré',
        'uso': 'frutas en general. Fruta singular: りんご (manzana), みかん (mandarina)'
      },
      {
        'kind': 'vocabulario',
        'jp': '水',
        'reading': 'みず',
        'meaning': 'agua',
        'tipo': 'sustantivo',
        'ejemplo': '水を ください',
        'literal': 'agua-OBJ / por-favor',
        'uso': 'agua fría. Agua caliente para beber es お湯 (おゆ)'
      },
      {
        'kind': 'vocabulario',
        'jp': '温い',
        'reading': 'ぬるい',
        'meaning': 'tibio',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '熱い',
        'reading': 'あつい',
        'meaning': 'caliente',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Caliente' al tacto (objetos, comida, bebida). Para el tiempo caluroso es 「暑い」; para algo grueso, 「厚い」: los tres se dicen 「あつい」."
      },
      {
        'kind': 'vocabulario',
        'jp': '牛乳',
        'reading': 'ぎゅうにゅう',
        'meaning': 'leche',
        'tipo': 'sustantivo',
        'ejemplo': '朝 牛乳を のみます',
        'literal': 'mañana / leche-OBJ / bebo',
        'uso': 'leche de vaca. En Japón se bebe fría o templada, no hervida'
      },
      {
        'kind': 'vocabulario',
        'jp': '牛肉',
        'reading': 'ぎゅうにく',
        'meaning': 'carne de vaca',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '甘い',
        'reading': 'あまい',
        'meaning': 'dulce',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Dulce'; también 'blando, indulgente' o 'ingenuo' (「考えが甘い」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '砂糖',
        'reading': 'さとう',
        'meaning': 'azúcar',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '箸',
        'reading': 'はし',
        'meaning': 'palillos',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Palillos'. Se pronuncia como 「橋」 'puente' y 「端」 'borde', con acento distinto; el contexto los separa."
      },
      {
        'kind': 'vocabulario',
        'jp': '紅茶',
        'reading': 'こうちゃ',
        'meaning': 'té negro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Literalmente 'té rojo', es el té negro occidental. El té verde japonés es 「お茶」 o 「緑茶」."
      },
      {
        'kind': 'vocabulario',
        'jp': '美味しい',
        'reading': 'おいしい',
        'meaning': 'delicioso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '肉',
        'reading': 'にく',
        'meaning': 'carne',
        'tipo': 'sustantivo',
        'ejemplo': '肉は 好きですか',
        'literal': 'carne-TEMA / ¿te-gusta?',
        'uso': 'carne cualquiera. Vaca es 牛肉 (ぎゅうにく), cerdo es 豚肉 (ぶたにく)'
      },
      {
        'kind': 'vocabulario',
        'jp': '茶碗',
        'reading': 'ちゃわん',
        'meaning': 'cuenco de arroz',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Pese al 「茶」, es el cuenco del arroz, no una taza de té. La taza de té es 「湯のみ」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '薄い',
        'reading': 'うすい',
        'meaning': 'fino, flojo (de sabor)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Fino' (「薄い紙」) y 'flojo' de sabor o color (「味が薄い」). Opuestos: 「厚い」 (grosor) y 「濃い」 (intensidad)."
      },
      {
        'kind': 'vocabulario',
        'jp': '豚肉',
        'reading': 'ぶたにく',
        'meaning': 'carne de cerdo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '辛い',
        'reading': 'からい',
        'meaning': 'picante; salado',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Con lectura 「からい」 es 'picante' (a veces 'salado'). El mismo kanji leído 「つらい」 significa 'duro, penoso'."
      },
      {
        'kind': 'vocabulario',
        'jp': '醤油',
        'reading': 'しょうゆ',
        'meaning': 'salsa de soja',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '野菜',
        'reading': 'やさい',
        'meaning': 'verduras',
        'tipo': 'sustantivo',
        'ejemplo': '野菜が 好きですか',
        'literal': 'verduras-SUJ / ¿te-gustan?',
        'uso': 'grupo de verduras. Verdura singular se especifica: トマト, ニンジン'
      },
      {
        'kind': 'vocabulario',
        'jp': '食べ物',
        'reading': 'たべもの',
        'meaning': 'comida',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '食堂',
        'reading': 'しょくどう',
        'meaning': 'comedor, cafetería',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '飲み物',
        'reading': 'のみもの',
        'meaning': 'bebida',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '飴',
        'reading': 'あめ',
        'meaning': 'caramelo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '魚',
        'reading': 'さかな',
        'meaning': 'pescado / pez',
        'tipo': 'sustantivo',
        'ejemplo': '魚を たべます',
        'literal': 'pescado-OBJ / como',
        'uso': 'pez o pescado como comida. Sushi es すし'
      },
      {
        'kind': 'vocabulario',
        'jp': '鶏肉',
        'reading': 'とりにく',
        'meaning': 'carne de pollo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'colores_ropa',
    'nombre': 'Colores y ropa',
    'funcion': 'decir de qué color es algo y hablar de la ropa que llevas o que te quieres comprar',
    'frases_hechas': [
      {'jp': '何色ですか', 'uso': "'¿de qué color es?'; 何色 se lee なにいろ"},
      {'jp': '着てみてもいいですか', 'uso': "'¿me lo puedo probar?', en una tienda"},
      {'jp': '似合いますね', 'uso': "'te queda bien'; se dice de quien la lleva, no de la prenda"},
      {'jp': 'ちょっと大きいです', 'uso': "'me queda un poco grande'; cambia el adjetivo y sirve para todo"}
    ],
    'prerequisito': 'comida_bebida',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'コート',
        'reading': 'コート',
        'meaning': 'abrigo; pista (de tenis)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Abrigo' y también 'pista' de tenis: dos préstamos que suenan igual."
      },
      {
        'kind': 'vocabulario',
        'jp': 'シャツ',
        'reading': 'しゃつ',
        'meaning': 'camisa / camiseta',
        'tipo': 'sustantivo',
        'ejemplo': 'しろい シャツを きます',
        'literal': 'blanca / camisa-OBJ / me-pongo',
        'uso': 'para las prendas de la parte de arriba, el verbo es きる'
      },
      {
        'kind': 'vocabulario',
        'jp': 'スカート',
        'reading': 'スカート',
        'meaning': 'falda',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ズボン',
        'reading': 'ずぼん',
        'meaning': 'pantalón',
        'tipo': 'sustantivo',
        'ejemplo': 'くろい ズボンを はきます',
        'literal': 'negro / pantalón-OBJ / me-pongo',
        'uso': "del francés 'jupon'. Para el pantalón y lo que se sube por las piernas, el verbo es はく, no きる"
      },
      {
        'kind': 'vocabulario',
        'jp': 'セーター',
        'reading': 'セーター',
        'meaning': 'jersey',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ネクタイ',
        'reading': 'ネクタイ',
        'meaning': 'corbata',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ハンカチ',
        'reading': 'ハンカチ',
        'meaning': 'pañuelo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ボタン',
        'reading': 'ボタン',
        'meaning': 'botón (de ropa o aparato)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ポケット',
        'reading': 'ポケット',
        'meaning': 'bolsillo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ワイシャツ',
        'reading': 'ワイシャツ',
        'meaning': 'camisa de vestir',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '上着',
        'reading': 'うわぎ',
        'meaning': 'chaqueta, abrigo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '帽子',
        'reading': 'ぼうし',
        'meaning': 'sombrero / gorra',
        'tipo': 'sustantivo',
        'ejemplo': 'ぼうしを かぶって ください',
        'literal': 'gorra-OBJ / ponte / por-favor',
        'uso': 'lo que va en la cabeza usa un tercer verbo: かぶる'
      },
      {
        'kind': 'vocabulario',
        'jp': '服',
        'reading': 'ふく',
        'meaning': 'ropa',
        'tipo': 'sustantivo',
        'ejemplo': 'あたらしい ふくを かいました',
        'literal': 'nueva / ropa-OBJ / compré',
        'uso': "genérico para 'ropa'. 洋服 (ようふく) es la ropa de estilo occidental, casi todo lo que se lleva hoy"
      },
      {
        'kind': 'vocabulario',
        'jp': '洋服',
        'reading': 'ようふく',
        'meaning': 'ropa occidental',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Ropa de estilo occidental, por oposición al kimono (「和服」). En el día a día es simplemente 'ropa'."
      },
      {
        'kind': 'vocabulario',
        'jp': '白',
        'reading': 'しろ',
        'meaning': 'blanco',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '白い',
        'reading': 'しろい',
        'meaning': 'blanco (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'しろい シャツを きます',
        'literal': 'blanca / camisa-OBJ / me-pongo',
        'uso': 'adj-い. Sustantivo: しろ'
      },
      {
        'kind': 'vocabulario',
        'jp': '眼鏡',
        'reading': 'めがね',
        'meaning': 'gafas',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '緑',
        'reading': 'みどり',
        'meaning': 'verde',
        'tipo': 'sustantivo',
        'ejemplo': 'みどりの ぼうしを かぶります',
        'literal': 'verde-DE / gorra-OBJ / me-pongo',
        'uso': 'sustantivo; se usa con の. No tiene forma en 〜い de uso común'
      },
      {
        'kind': 'vocabulario',
        'jp': '締める',
        'reading': 'しめる',
        'meaning': 'atar, apretar (un cinturón, una corbata)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Apretar, atar' lo que rodea el cuerpo: 「ネクタイを締める」「シートベルトを締める」."
      },
      {
        'kind': 'vocabulario',
        'jp': '背広',
        'reading': 'せびろ',
        'meaning': 'traje (de hombre)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Traje' de hombre; palabra algo anticuada, hoy se dice más 「スーツ」."
      },
      {
        'kind': 'vocabulario',
        'jp': '脱ぐ',
        'reading': 'ぬぐ',
        'meaning': 'quitarse (ropa)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Quitarse' ropa, zapatos o sombrero. Ponerse ropa de tronco es 「着る」; de piernas o pies, 「はく」."
      },
      {
        'kind': 'vocabulario',
        'jp': '色',
        'reading': 'いろ',
        'meaning': 'color',
        'tipo': 'sustantivo',
        'ejemplo': 'すきな いろは なんですか',
        'literal': 'favorito / color-TEMA / ¿qué-es?',
        'uso': "cada color tiene forma de sustantivo y, muchos, forma en 〜い. 何色 (なにいろ) es '¿qué color?'"
      },
      {
        'kind': 'vocabulario',
        'jp': '茶色',
        'reading': 'ちゃいろ',
        'meaning': 'marrón',
        'tipo': 'sustantivo',
        'ejemplo': 'ちゃいろの コートです',
        'literal': 'marrón-DE / abrigo-es',
        'uso': "literalmente 'color del té'. Como adjetivo casi siempre con の: ちゃいろの…"
      },
      {
        'kind': 'vocabulario',
        'jp': '赤',
        'reading': 'あか',
        'meaning': 'rojo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '赤い',
        'reading': 'あかい',
        'meaning': 'rojo (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'あかい りんごを かいました',
        'literal': 'roja / manzana-OBJ / compré',
        'uso': "adj-い. El sustantivo 'el rojo' es あか, sin い"
      },
      {
        'kind': 'vocabulario',
        'jp': '青',
        'reading': 'あお',
        'meaning': 'azul',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Cubre el azul y, por tradición, parte del verde: 「青信号」 es el semáforo en verde y 「青りんご」 la manzana verde.'
      },
      {
        'kind': 'vocabulario',
        'jp': '青い',
        'reading': 'あおい',
        'meaning': 'azul (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'そらが あおいです',
        'literal': 'cielo-SUJ / azul-es',
        'uso': 'あおい cubre el azul y, en cosas como el semáforo o la fruta verde, también el verde'
      },
      {
        'kind': 'vocabulario',
        'jp': '靴',
        'reading': 'くつ',
        'meaning': 'zapatos',
        'tipo': 'sustantivo',
        'ejemplo': 'げんかんで くつを ぬぎます',
        'literal': 'recibidor-EN / zapatos-OBJ / me-quito',
        'uso': 'se ponen con はく y se quitan con ぬぐ. En una casa japonesa se quitan siempre en el げんかん'
      },
      {
        'kind': 'vocabulario',
        'jp': '靴下',
        'reading': 'くつした',
        'meaning': 'calcetines',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '黄色',
        'reading': 'きいろ',
        'meaning': 'amarillo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '黄色い',
        'reading': 'きいろい',
        'meaning': 'amarillo (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'きいろい はなが すきです',
        'literal': 'amarillas / flores-SUJ / gustan',
        'uso': 'lleva 色 dentro. Sustantivo: きいろ'
      },
      {
        'kind': 'vocabulario',
        'jp': '黒',
        'reading': 'くろ',
        'meaning': 'negro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '黒い',
        'reading': 'くろい',
        'meaning': 'negro (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'くろい かばんを もって います',
        'literal': 'negro / bolso-OBJ / llevo',
        'uso': 'adj-い. Sustantivo: くろ. El café solo es ブラック'
      }
    ]
  },
  {
    'id': 'clima_estaciones',
    'nombre': 'Clima y estaciones',
    'funcion': 'hablar del tiempo que hace y de la época del año, que es como arranca media conversación en Japón',
    'frases_hechas': [
      {'jp': 'いい天気ですね', 'uso': "'qué buen tiempo hace'; el comentario con el que se rompe el hielo"},
      {'jp': '暑いですね', 'uso': "'qué calor'; en invierno, 寒いですね"},
      {'jp': '雨が降りそうです', 'uso': "'parece que va a llover', mirando el cielo"},
      {'jp': 'だんだん寒くなりますね', 'uso': "'va refrescando'; だんだん + 〜くなる para un cambio gradual"}
    ],
    'prerequisito': 'colores_ropa',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': '傘',
        'reading': 'かさ',
        'meaning': 'paraguas',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '冬',
        'reading': 'ふゆ',
        'meaning': 'invierno',
        'tipo': 'sustantivo',
        'ejemplo': 'ふゆは ゆきが おおいです',
        'literal': 'invierno-TEMA / nieve-SUJ / abundante-es',
        'uso': 'ふゆやすみ son las vacaciones de invierno, en torno al año nuevo'
      },
      {
        'kind': 'vocabulario',
        'jp': '冷たい',
        'reading': 'つめたい',
        'meaning': 'frío (cosas, personas)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Frío' al tacto (agua, manos) y 'frío' de trato (「冷たい人」). Para el tiempo frío se usa 「寒い」."
      },
      {
        'kind': 'vocabulario',
        'jp': '吹く',
        'reading': 'ふく',
        'meaning': 'soplar (el viento)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Soplar' el viento (「風が吹く」) y 'tocar' un instrumento de viento (「笛を吹く」). Suena como 「拭く」 'limpiar frotando'."
      },
      {
        'kind': 'vocabulario',
        'jp': '咲く',
        'reading': 'さく',
        'meaning': 'florecer',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '夏',
        'reading': 'なつ',
        'meaning': 'verano',
        'tipo': 'sustantivo',
        'ejemplo': 'なつやすみに うみへ いきます',
        'literal': 'vacaciones-de-verano-EN / mar-A / voy',
        'uso': 'なつやすみ son las vacaciones de verano, largas para los estudiantes'
      },
      {
        'kind': 'vocabulario',
        'jp': '夏休み',
        'reading': 'なつやすみ',
        'meaning': 'vacaciones de verano',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '天気',
        'reading': 'てんき',
        'meaning': 'tiempo (meteorológico)',
        'tipo': 'sustantivo',
        'ejemplo': 'きょうは いい てんきです',
        'literal': 'hoy-TEMA / buen / tiempo-es',
        'uso': "'buen tiempo' es いい てんき; 'mal tiempo', わるい てんき. お天気 con お suena más suave"
      },
      {
        'kind': 'vocabulario',
        'jp': '寒い',
        'reading': 'さむい',
        'meaning': 'frío (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'そとは さむいですよ',
        'literal': 'fuera-TEMA / frío-es-¡eh!',
        'uso': 'del tiempo y del ambiente. Una bebida o un objeto frío es つめたい'
      },
      {
        'kind': 'vocabulario',
        'jp': '差す',
        'reading': 'さす',
        'meaning': 'abrir (un paraguas), extender (la mano)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "El paraguas 'se lleva' con 「差す」 (「かさを差す」), no con 「開く」. También 「日が差す」 'entrar el sol'."
      },
      {
        'kind': 'vocabulario',
        'jp': '春',
        'reading': 'はる',
        'meaning': 'primavera',
        'tipo': 'sustantivo',
        'ejemplo': 'はるに さくらを みます',
        'literal': 'primavera-EN / cerezos-OBJ / vemos',
        'uso': 'la estación como punto en el tiempo lleva に'
      },
      {
        'kind': 'vocabulario',
        'jp': '晴れ',
        'reading': 'はれ',
        'meaning': 'despejado / buen tiempo',
        'tipo': 'sustantivo',
        'ejemplo': 'あしたは はれです',
        'literal': 'mañana-TEMA / despejado-es',
        'uso': 'en el parte del tiempo va como sustantivo. El verbo es はれる: あした はれます'
      },
      {
        'kind': 'vocabulario',
        'jp': '晴れる',
        'reading': 'はれる',
        'meaning': 'hacer sol, despejarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '暑い',
        'reading': 'あつい',
        'meaning': 'caluroso (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'なつは とても あついです',
        'literal': 'verano-TEMA / muy / caluroso-es',
        'uso': 'solo del tiempo y del ambiente. Un objeto caliente al tacto es あつい escrito 熱い'
      },
      {
        'kind': 'vocabulario',
        'jp': '暖かい',
        'reading': 'あたたかい',
        'meaning': 'templado / cálido (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'はるは あたたかいです',
        'literal': 'primavera-TEMA / templada-es',
        'uso': 'del tiempo. Para comida o bebida caliente y agradable se escribe 温かい, misma lectura'
      },
      {
        'kind': 'vocabulario',
        'jp': '曇り',
        'reading': 'くもり',
        'meaning': 'nublado',
        'tipo': 'sustantivo',
        'ejemplo': 'きょうは くもりです',
        'literal': 'hoy-TEMA / nublado-es',
        'uso': "verbo くもる. 'Nublado con claros' es はれ ときどき くもり"
      },
      {
        'kind': 'vocabulario',
        'jp': '曇る',
        'reading': 'くもる',
        'meaning': 'nublarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '木',
        'reading': 'き',
        'meaning': 'árbol, madera',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '池',
        'reading': 'いけ',
        'meaning': 'estanque',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '海',
        'reading': 'うみ',
        'meaning': 'mar',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '涼しい',
        'reading': 'すずしい',
        'meaning': 'fresco / agradable (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'あきは すずしくて きもちいいです',
        'literal': 'otoño-TEMA / fresco-y / agradable-es',
        'uso': 'fresco en el buen sentido, ni frío ni calor. El fresco desagradable ya es さむい'
      },
      {
        'kind': 'vocabulario',
        'jp': '秋',
        'reading': 'あき',
        'meaning': 'otoño',
        'tipo': 'sustantivo',
        'ejemplo': 'あきは たべものが おいしいです',
        'literal': 'otoño-TEMA / comida-SUJ / rica-es',
        'uso': 'se le llama el otoño del apetito, del deporte y de la lectura'
      },
      {
        'kind': 'vocabulario',
        'jp': '空',
        'reading': 'そら',
        'meaning': 'cielo',
        'tipo': 'sustantivo',
        'ejemplo': 'そらが あおいです',
        'literal': 'cielo-SUJ / azul-es',
        'uso': "el cielo físico. El 'cielo' religioso es てん"
      },
      {
        'kind': 'vocabulario',
        'jp': '花',
        'reading': 'はな',
        'meaning': 'flor',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Flor'. Se pronuncia como 「鼻」 'nariz', con acento distinto."
      },
      {
        'kind': 'vocabulario',
        'jp': '降る',
        'reading': 'ふる',
        'meaning': 'caer (lluvia, nieve)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Caer lluvia o nieve; lo que cae lleva 「が」: 「雨が降る」. Bajarse de un tren o coche es 「降りる」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '雨',
        'reading': 'あめ',
        'meaning': 'lluvia',
        'tipo': 'sustantivo',
        'ejemplo': 'あめが ふって います',
        'literal': 'lluvia-SUJ / está-cayendo',
        'uso': "llover es あめが ふる, nunca *あめする. 'Bajo la lluvia' es あめの なか"
      },
      {
        'kind': 'vocabulario',
        'jp': '雪',
        'reading': 'ゆき',
        'meaning': 'nieve',
        'tipo': 'sustantivo',
        'ejemplo': 'ふゆは ゆきが ふります',
        'literal': 'invierno-TEMA / nieve-SUJ / cae',
        'uso': 'también con ふる, igual que la lluvia'
      },
      {
        'kind': 'vocabulario',
        'jp': '風',
        'reading': 'かぜ',
        'meaning': 'viento',
        'tipo': 'sustantivo',
        'ejemplo': 'きょうは かぜが つよいです',
        'literal': 'hoy-TEMA / viento-SUJ / fuerte-es',
        'uso': "'hace viento' es かぜが つよい. El mismo かぜ, escrito 風邪, es el resfriado: かぜを ひく"
      }
    ]
  },
  {
    'id': 'casa_objetos',
    'nombre': 'La casa y sus objetos',
    'funcion': 'hablar de tu casa y de lo que hay en cada habitación, y decir dónde está cada cosa',
    'frases_hechas': [
      {'jp': 'お邪魔します', 'uso': "'con permiso', al entrar en casa de alguien"},
      {'jp': 'どうぞ上がってください', 'uso': "'pasa'; se sube (上がる) el escalón del recibidor"},
      {'jp': '電気を消して', 'uso': "'apaga la luz'; 電気 es la electricidad y también la luz"},
      {'jp': '鍵かけた？', 'uso': "'¿has cerrado con llave?', antes de salir"}
    ],
    'prerequisito': 'clima_estaciones',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'うち',
        'reading': 'うち',
        'meaning': 'casa / mi casa',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mi casa' y, por extensión, 'nosotros, los de dentro': mi familia, mi empresa (「うちの会社」), frente a los de fuera (「そと」)."
      },
      {
        'kind': 'vocabulario',
        'jp': 'お手洗い',
        'reading': 'おてあらい',
        'meaning': 'servicio / aseo',
        'tipo': 'sustantivo',
        'ejemplo': 'おてあらいは どこですか',
        'literal': 'aseo-TEMA / ¿dónde-está?',
        'uso': 'la forma educada de pedirlo fuera de casa. トイレ es más directo y también normal'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お皿',
        'reading': 'おさら',
        'meaning': 'plato',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'お風呂',
        'reading': 'おふろ',
        'meaning': 'baño (bañera)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "La bañera y el baño de agua caliente, no el váter (eso es 「トイレ」). 「お風呂に入る」 = 'bañarse'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'かばん',
        'reading': 'かばん',
        'meaning': 'bolso, maletín',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'つける',
        'reading': 'つける',
        'meaning': 'encender (una luz); coger',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Encender' (「電気をつける」), frente a 「消す」. También 「気をつける」 (tener cuidado), 「名前をつける」 (poner nombre). Que algo 'se encienda' solo es 「つく」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'アパート',
        'reading': 'アパート',
        'meaning': 'apartamento',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'エレベーター',
        'reading': 'エレベーター',
        'meaning': 'ascensor',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'カップ',
        'reading': 'カップ',
        'meaning': 'taza, copa',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'コップ',
        'reading': 'コップ',
        'meaning': 'vaso',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'シャワー',
        'reading': 'シャワー',
        'meaning': 'ducha',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ストーブ',
        'reading': 'ストーブ',
        'meaning': 'estufa, calefactor',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'スプーン',
        'reading': 'スプーン',
        'meaning': 'cuchara',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'テーブル',
        'reading': 'テーブル',
        'meaning': 'mesa',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'トイレ',
        'reading': 'トイレ',
        'meaning': 'baño, aseo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ドア',
        'reading': 'どあ',
        'meaning': 'puerta',
        'tipo': 'sustantivo',
        'ejemplo': 'ドアを しめて ください',
        'literal': 'puerta-OBJ / cierra / por-favor',
        'uso': 'la puerta de estilo occidental, con bisagras. La corredera tradicional es と'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ナイフ',
        'reading': 'ナイフ',
        'meaning': 'cuchillo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'フォーク',
        'reading': 'フォーク',
        'meaning': 'tenedor',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ベッド',
        'reading': 'べっど',
        'meaning': 'cama',
        'tipo': 'sustantivo',
        'ejemplo': 'ベッドで ねます',
        'literal': 'cama-EN / duermo',
        'uso': 'la cama occidental. El futón que se tiende en el suelo es ふとん'
      },
      {
        'kind': 'vocabulario',
        'jp': 'マッチ',
        'reading': 'マッチ',
        'meaning': 'cerilla',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ラジオ',
        'reading': 'ラジオ',
        'meaning': 'radio',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ラジオカセ',
        'reading': 'ラジオカセ',
        'meaning': 'radiocasete',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '住む',
        'reading': 'すむ',
        'meaning': 'vivir, residir',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '入口',
        'reading': 'いりぐち',
        'meaning': 'entrada',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '冷蔵庫',
        'reading': 'れいぞうこ',
        'meaning': 'nevera / frigorífico',
        'tipo': 'sustantivo',
        'ejemplo': 'ぎゅうにゅうは れいぞうこに あります',
        'literal': 'leche-TEMA / nevera-EN / está',
        'uso': 'palabra larga pero muy frecuente; conviene memorizarla entera'
      },
      {
        'kind': 'vocabulario',
        'jp': '出口',
        'reading': 'でぐち',
        'meaning': 'salida',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '台所',
        'reading': 'だいどころ',
        'meaning': 'cocina (estancia)',
        'tipo': 'sustantivo',
        'ejemplo': 'ははが だいどころに います',
        'literal': 'madre-SUJ / cocina-EN / está',
        'uso': 'la cocina como sala de la casa. Cocinar es りょうりを する; el office moderno, キッチン'
      },
      {
        'kind': 'vocabulario',
        'jp': '広い',
        'reading': 'ひろい',
        'meaning': 'espacioso, amplio',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '庭',
        'reading': 'にわ',
        'meaning': 'jardín',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '廊下',
        'reading': 'ろうか',
        'meaning': 'pasillo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '戸',
        'reading': 'と',
        'meaning': 'puerta (estilo japonés)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Puerta corredera de estilo japonés. La de bisagra occidental es 「ドア」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '掃除',
        'reading': 'そうじ (する)',
        'meaning': 'limpiar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '掛ける',
        'reading': 'かける',
        'meaning': 'colgar; ponerse (gafas)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Mismo 「かける」 en kanji: colgar algo de un gancho, echar (una manta, salsa), sentarse, ponerse las gafas.'
      },
      {
        'kind': 'vocabulario',
        'jp': '時計',
        'reading': 'とけい',
        'meaning': 'reloj',
        'tipo': 'sustantivo',
        'ejemplo': 'へやに とけいが あります',
        'literal': 'habitación-EN / reloj-SUJ / hay',
        'uso': 'de pared y de pulsera es el mismo とけい; el de muñeca puede precisarse como うでどけい'
      },
      {
        'kind': 'vocabulario',
        'jp': '本棚',
        'reading': 'ほんだな',
        'meaning': 'estantería / librería (mueble)',
        'tipo': 'sustantivo',
        'ejemplo': 'ほんだなに ほんを ならべます',
        'literal': 'estantería-EN / libros-OBJ / coloco',
        'uso': 'たな solo es cualquier estante; con 本 delante, el de los libros'
      },
      {
        'kind': 'vocabulario',
        'jp': '机',
        'reading': 'つくえ',
        'meaning': 'mesa / escritorio',
        'tipo': 'sustantivo',
        'ejemplo': 'つくえの うえに ほんが あります',
        'literal': 'escritorio-DE / encima-EN / libro-SUJ / hay',
        'uso': 'la mesa de estudio o de trabajo. La de comedor es テーブル'
      },
      {
        'kind': 'vocabulario',
        'jp': '椅子',
        'reading': 'いす',
        'meaning': 'silla',
        'tipo': 'sustantivo',
        'ejemplo': 'いすに すわって ください',
        'literal': 'silla-EN / siéntate / por-favor',
        'uso': 'sentarse en una silla lleva に, no を'
      },
      {
        'kind': 'vocabulario',
        'jp': '洗う',
        'reading': 'あらう',
        'meaning': 'lavar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '洗濯',
        'reading': 'せんたく',
        'meaning': 'colada, lavado de ropa',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '消える',
        'reading': 'きえる',
        'meaning': 'apagarse, desaparecer',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Intransitivo: 'apagarse, borrarse, desaparecer' (「電気が消える」). Apagar o borrar algo es 「消す」."
      },
      {
        'kind': 'vocabulario',
        'jp': '消す',
        'reading': 'けす',
        'meaning': 'borrar; apagar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Transitivo: 'apagar' (luz, tele, fuego) y 'borrar' (「字を消す」). Que algo 'se apague' solo es 「消える」."
      },
      {
        'kind': 'vocabulario',
        'jp': '灰皿',
        'reading': 'はいざら',
        'meaning': 'cenicero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cenicero'. 「灰」 es 'ceniza' y 「皿」 'plato'."
      },
      {
        'kind': 'vocabulario',
        'jp': '物',
        'reading': 'もの',
        'meaning': 'cosa (objeto concreto)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cosa' concreta que se puede tocar. Para algo abstracto (un hecho, un asunto) se usa 「こと」."
      },
      {
        'kind': 'vocabulario',
        'jp': '狭い',
        'reading': 'せまい',
        'meaning': 'estrecho, pequeño (espacio)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '玄関',
        'reading': 'げんかん',
        'meaning': 'entrada (de una casa)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'El recibidor a la entrada de la casa, donde te descalzas antes de subir el escalón al interior.'
      },
      {
        'kind': 'vocabulario',
        'jp': '石鹸',
        'reading': 'せっけん',
        'meaning': 'jabón',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '窓',
        'reading': 'まど',
        'meaning': 'ventana',
        'tipo': 'sustantivo',
        'ejemplo': 'まどを あけても いいですか',
        'literal': 'ventana-OBJ / aunque-abra / ¿está-bien?',
        'uso': 'abrir y cerrar con あける／しめる'
      },
      {
        'kind': 'vocabulario',
        'jp': '箱',
        'reading': 'はこ',
        'meaning': 'caja',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '紙',
        'reading': 'かみ',
        'meaning': 'papel',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '置く',
        'reading': 'おく',
        'meaning': 'poner, colocar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Poner, dejar' algo en un sitio (「かばんを置く」). En 「～ておく」 es 'dejar algo hecho de antemano'."
      },
      {
        'kind': 'vocabulario',
        'jp': '花瓶',
        'reading': 'かびん',
        'meaning': 'jarrón',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '部屋',
        'reading': 'へや',
        'meaning': 'habitación / cuarto',
        'tipo': 'sustantivo',
        'ejemplo': 'わたしの へやは ひろいです',
        'literal': 'yo-DE / habitación-TEMA / amplia-es',
        'uso': "cualquier estancia. 'Mi cuarto' es わたしの へや"
      },
      {
        'kind': 'vocabulario',
        'jp': '鍵',
        'reading': 'かぎ',
        'meaning': 'llave',
        'tipo': 'sustantivo',
        'ejemplo': 'かぎを かけましたか',
        'literal': 'llave-OBJ / ¿echaste?',
        'uso': 'cerrar con llave es かぎを かける; abrir, かぎを あける. También es la cerradura'
      },
      {
        'kind': 'vocabulario',
        'jp': '門',
        'reading': 'もん',
        'meaning': 'puerta, portón',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '階段',
        'reading': 'かいだん',
        'meaning': 'escaleras',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '電気',
        'reading': 'でんき',
        'meaning': 'luz / electricidad',
        'tipo': 'sustantivo',
        'ejemplo': 'でんきを つけて ください',
        'literal': 'luz-OBJ / enciende / por-favor',
        'uso': 'encender y apagar: でんきを つける／けす. La factura de la luz es でんきだい'
      },
      {
        'kind': 'vocabulario',
        'jp': '～階',
        'reading': '～かい',
        'meaning': 'contador de pisos de un edificio',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Pisos de un edificio. El 3 suele sonar 「さんがい」. 「何階」 '¿qué planta?' se confunde de oído con 「何回」 '¿cuántas veces?'."
      }
    ]
  },
  {
    'id': 'te_forma',
    'nombre': 'Forma て',
    'funcion': 'encadenar acciones, pedir cosas con educación y pedir permiso',
    'frases_hechas': [
      {'jp': 'ちょっと待って', 'uso': "'espera un momento', informal; con ください es más educado"},
      {'jp': 'がんばって', 'uso': "'ánimo'; literalmente 'esfuérzate', se dice antes de algo difícil"},
      {'jp': '教えてください', 'uso': "'dime' / 'enséñame'; se usa muchísimo más que en español"},
      {'jp': '助かりました', 'uso': "'me has salvado', para agradecer una ayuda de verdad"}
    ],
    'prerequisito': 'casa_objetos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜て（て形）',
        'meaning': "forma-て: conecta acciones secuenciales ('y luego')",
        'ejemplo': 'おきて、ごはんを たべて、でかけます',
        'literal': 'me-levanto-y / comida-OBJ / como-y / salgo',
        'uso': 'encadena acciones en orden. El tiempo verbal lo marca solo el último verbo de la frase'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てください',
        'meaning': "〜て + ください: petición formal 'por favor haz X'",
        'ejemplo': 'ちょっと まって ください',
        'literal': 'un-momento / espera / por-favor',
        'uso': 'cortés pero directa, casi una instrucción. Para pedir un favor de verdad: 〜てくださいませんか'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てもいいです',
        'meaning': "pedir permiso: '¿puedo hacer X?'",
        'ejemplo': 'ここに すわっても いいですか',
        'literal': 'aquí-EN / aunque-me-siente / ¿está-bien?',
        'uso': 'la forma normal de pedir permiso. La respuesta corta que vas a oír es どうぞ'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てはいけません',
        'meaning': "prohibición: 'no se debe hacer X'",
        'ejemplo': 'ここで たばこを すっては いけません',
        'literal': 'aquí-EN / tabaco-OBJ / fumar-TE / no-se-puede',
        'uso': "prohibición de norma o de autoridad. La idea es 'si haces X, no está bien'. En habla casual se dice 〜ちゃだめ o 〜ちゃいけない"
      },
      {
        'kind': 'gramatica',
        'jp': '〜ています',
        'meaning': '〜て + いる: acción en progreso o estado resultante',
        'ejemplo': 'いま ごはんを たべています',
        'literal': 'ahora / comida-OBJ / estoy-comiendo',
        'uso': "para lo que pasa ahora mismo, y también para estados: けっこんしています es 'estoy casado', no 'me estoy casando'. Al hablar se come la い: たべてます"
      },
      {
        'kind': 'gramatica',
        'jp': '〜てから',
        'meaning': "secuencia: 'después de hacer X'",
        'ejemplo': 'ごはんを たべてから、でかけます',
        'literal': 'comida-OBJ / después-de-comer / salgo',
        'uso': 'deja claro que la primera acción termina antes de empezar la segunda; más explícito que 〜て a secas'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てみます',
        'meaning': "'probar a ~ / hacer ~ a ver qué tal': forma-て + みる",
        'ejemplo': 'この ケーキを 食べてみます',
        'literal': 'este / pastel-OBJ / pruebo-a-comer',
        'uso': "Haces algo por primera vez a ver qué tal, sin saber si saldrá bien. 「てみてください」 es 'inténtalo'."
      },
      {
        'kind': 'gramatica',
        'jp': '〜ておきます',
        'meaning': "'dejar ~ hecho de antemano': forma-て + おく",
        'ejemplo': 'りょこうの まえに きっぷを 買っておきます',
        'literal': 'viaje-DE / antes / billete-OBJ / lo-dejo-comprado',
        'uso': 'Preparar algo con vistas a más tarde, o dejarlo tal cual porque va a servir. Al hablar se contrae en 「とく」 (「かっとく」).'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てしまいます',
        'meaning': "'terminar ~ del todo', o '~ sin querer / para mi disgusto': forma-て + しまう",
        'ejemplo': 'しゅくだいを ぜんぶ やってしまいました',
        'literal': 'deberes-OBJ / todos / los-terminé',
        'uso': "Dos matices según el contexto: acción rematada ('me lo acabé') o algo que lamentas (「さいふをなくしてしまいました」). Contracción hablada: 「ちゃう」."
      },
      {
        'kind': 'gramatica',
        'jp': '〜てあげます',
        'meaning': 'hacer algo por otro como favor: forma-て + あげる',
        'ejemplo': 'ともだちに 日本語を 教えてあげます',
        'literal': 'amigo-A / japonés-OBJ / se-lo-enseño',
        'uso': 'El favor va del hablante hacia fuera. Dicho a la cara puede sonar a que te las das de generoso; mejor entre iguales o de arriba abajo.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てくれます',
        'meaning': 'alguien hace algo por mí (o por los míos): forma-て + くれる',
        'ejemplo': 'ちちが かさを 貸してくれました',
        'literal': 'padre-SUJ / paraguas-OBJ / me-lo-prestó',
        'uso': 'El favor entra hacia el hablante o los suyos; quien lo hace lleva 「が」. Sirve para agradecer: 「てつだってくれてありがとう」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜てもらいます',
        'meaning': 'conseguir que alguien haga algo por mí: forma-て + もらう',
        'ejemplo': 'せんせいに 日本語を 教えてもらいました',
        'literal': 'profesor-A / japonés-OBJ / me-lo-enseñó',
        'uso': 'Yo recibo el favor y normalmente lo he pedido; la persona que lo hace lleva 「に」. 「くれる」, en cambio, no implica que lo pidieras.'
      },
      {
        'kind': 'gramatica',
        'jp': 'あげます',
        'meaning': 'dar algo (del hablante o su grupo hacia fuera, o entre iguales)',
        'ejemplo': 'ラウラさんに 花を あげます',
        'literal': 'Laura-san-A / flores-OBJ / doy',
        'uso': 'El que da soy yo o alguien de mi lado; nunca para algo que me dan a mí (eso es 「くれる」). Con un superior se sube a 「さしあげます」.'
      },
      {
        'kind': 'gramatica',
        'jp': 'もらいます',
        'meaning': 'recibir algo de alguien',
        'ejemplo': 'ともだちに プレゼントを もらいました',
        'literal': 'amigo-DE / regalo-OBJ / recibí',
        'uso': 'El que recibe es el sujeto (yo, casi siempre); la fuente lleva 「に」 o 「から」. Educado hacia arriba: 「いただきます」.'
      },
      {
        'kind': 'gramatica',
        'jp': 'くれます',
        'meaning': 'alguien me da algo a mí (o a alguien de mi grupo)',
        'ejemplo': 'あねが 本を くれました',
        'literal': 'hermana-mayor-SUJ / libro-OBJ / me-dio',
        'uso': 'Solo cuando quien recibe soy yo o los míos; el que da lleva 「が」. Si es un superior: 「くださいます」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '下さい',
        'reading': 'ください',
        'meaning': 'por favor, deme (detrás de una forma-て)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'permiso_obligacion',
    'nombre': 'Permiso, obligación y no obligación',
    'funcion': 'pedir permiso, dar normas y decir qué está prohibido o qué no hace falta hacer',
    'frases_hechas': [
      {'jp': 'ここで写真を撮ってもいいですか', 'uso': "'¿puedo sacar fotos aquí?'"},
      {'jp': '学校でスマホを使ってはいけません', 'uso': "'en la escuela no se puede usar el móvil'"},
      {'jp': '今日は休んでもいいです', 'uso': "'hoy puedes descansar'"},
      {'jp': '早く帰らなければなりません', 'uso': "'hay que volver pronto'"}
    ],
    'prerequisito': 'te_forma',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜ないでください',
        'meaning': "petición negativa: 'por favor, no hagas X'",
        'ejemplo': 'ここで しゃべらないでください',
        'literal': 'aquí-EN / no-hables / por-favor',
        'uso': "sirve para pedir que otra persona no haga algo. Es más amable y formal que un directo 'no'"
      },
      {
        'kind': 'gramatica',
        'jp': '〜なくてもいいです',
        'meaning': 'no hace falta / no es necesario hacer X',
        'ejemplo': '今日は べんきょうしなくても いいです',
        'literal': 'hoy-TEMA / estudiar-no-hacer-aunque / bien-es',
        'uso': "equivale a 'no hace falta', 'puedes no hacerlo'. Es la versión relajada de la obligación"
      },
      {
        'kind': 'gramatica',
        'jp': '〜なければなりません',
        'meaning': "obligación: 'hay que hacer X / debes hacer X'",
        'ejemplo': 'きょうは しゅくだいを しなければなりません',
        'literal': 'hoy-TEMA / tarea-OBJ / tengo-que-hacer',
        'uso': "obligación fuerte, normativa o diaria. Es la forma literal: 'si no lo haces, no vale'"
      },
      {
        'kind': 'gramatica',
        'jp': '〜なくてはいけません',
        'meaning': "obligación: 'hay que ~ / tengo que ~' (variante de なければなりません)",
        'ejemplo': 'くすりを 飲まなくてはいけません',
        'literal': 'medicina-OBJ / si-no-la-tomo / no-vale',
        'uso': 'Misma idea que 「なければなりません」, un poco más de conversación. Contracción muy usada: 「なくちゃ」 (「のまなくちゃ」).'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ないほうがいいです',
        'meaning': "consejo en negativo: 'mejor no ~'",
        'ejemplo': 'たばこは 吸わないほうがいいです',
        'literal': 'tabaco-TEMA / no-fumar / mejor-es',
        'uso': 'Recomendación de no hacer algo, más suave que una prohibición. El afirmativo lleva verbo en pasado (「たほうがいい」), pero el negativo va en presente.'
      }
    ]
  },
  {
    'id': 'negacion_condicional',
    'nombre': 'Negación と〜ない y condicional と〜たら',
    'funcion': 'decir lo que no haces y lo que te apetece hacer, y proponer planes con condición',
    'frases_hechas': [
      {'jp': '行きたい！', 'uso': "'¡quiero ir!'; el 〜たい se dice solo de uno mismo"},
      {'jp': 'べつに', 'uso': "'nada en especial' / 'me da igual'; según el tono suena a desgana"},
      {'jp': 'じゃあ、そうしよう', 'uso': "'venga, hagamos eso', para cerrar un plan"},
      {'jp': 'やめとく', 'uso': "'paso', decidir no hacer algo sin dar explicaciones"}
    ],
    'prerequisito': 'permiso_obligacion',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜たいです',
        'meaning': "expresar deseo (formal): 'quisiera hacer X'",
        'ejemplo': '何を したいですか',
        'literal': '¿qué-OBJ / quieres-hacer?',
        'uso': 'versión formal de 〜たい. Pregunta típica de entrevista'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たくないです',
        'meaning': "deseo en negativo: 'no quiero ~'",
        'ejemplo': 'きょうは 出かけたくないです',
        'literal': 'hoy-TEMA / no-quiero-salir',
        'uso': 'Es 「たい」 negado como adjetivo-い (「たい」 -> 「たくない」). Solo para lo que quiere el hablante; para otra persona, 「たがる」. También 「たくありません」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たがっています',
        'meaning': "deseo de un tercero visible desde fuera: 'se le nota que quiere ~'",
        'ejemplo': 'いもうとが 犬を かいたがっています',
        'literal': 'hermana-menor-SUJ / perro-OBJ / anda-queriendo-tener',
        'uso': 'No se usa 「たい」 para lo que siente otro; con 「たがる」 describes lo que se le ve o se le oye querer. El objeto suele ir con 「を」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たことがあります',
        'meaning': "experiencia: 'he ~ alguna vez'",
        'ejemplo': '日本へ 行ったことがあります',
        'literal': 'Japón-A / hay-vez-de-haber-ido',
        'uso': 'Verbo en pasado llano + 「ことがある」: habla de si algo pasó alguna vez en la vida, no de cuándo. Para algo de ayer no vale.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たり〜たりします',
        'meaning': "enumerar algunas acciones de ejemplo: 'hacer cosas como ~ y ~'",
        'ejemplo': '日曜日は 本を 読んだり おんがくを 聞いたりします',
        'literal': 'domingo-TEMA / libro-OBJ / leo-y / música-OBJ / escucho-y-tal',
        'uso': 'Das una muestra de acciones, no la lista completa ni el orden; se cierra con 「する」 conjugado según el tiempo. Verbo en pasado llano + 「り」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たあとで',
        'meaning': "secuencia: 'después de ~'",
        'ejemplo': 'ごはんを 食べたあとで さんぽします',
        'literal': 'comida-OBJ / después-de-comer / paseo',
        'uso': 'Verbo en pasado llano + 「あとで」; la primera acción está del todo terminada. Con sustantivo: 「のあとで」 (「じゅぎょうのあとで」).'
      },
      {
        'kind': 'gramatica',
        'jp': '〜たほうがいいです',
        'meaning': "consejo: 'mejor ~ / deberías ~'",
        'ejemplo': 'はやく ねたほうがいいです',
        'literal': 'pronto / dormir / mejor-es',
        'uso': 'Consejo bastante directo, casi advertencia; el verbo va en pasado llano aunque el consejo sea para ahora. Negativo: 「ないほうがいい」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜まえに',
        'meaning': "secuencia: 'antes de ~'",
        'ejemplo': 'ねるまえに はを みがきます',
        'literal': 'antes-de-dormir / dientes-OBJ / cepillo',
        'uso': 'El verbo va en presente llano aunque la acción sea pasada. Con sustantivo: 「のまえに」 (「しょくじのまえに」); con tiempo: 「三日まえに」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ながら',
        'meaning': "dos acciones a la vez hechas por la misma persona: 'mientras ~'",
        'ejemplo': 'おんがくを 聞きながら べんきょうします',
        'literal': 'música-OBJ / escuchando / estudio',
        'uso': "Raíz de 「ます」 + 「ながら」; la acción principal es la segunda ('estudio escuchando música'). Los dos verbos tienen que hacerlos la misma persona."
      },
      {
        'kind': 'gramatica',
        'jp': '〜ことができます',
        'meaning': 'poder / saber hacer algo: verbo en presente llano + ことができる',
        'ejemplo': 'ラウラさんは ピアノを ひくことができます',
        'literal': 'Laura-san-TEMA / piano-OBJ / puede-tocar',
        'uso': 'Más formal y algo más rígido que la forma potencial (「ひける」); típico de carteles y textos. Negativo para lo prohibido o imposible: 「ことができません」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ことがあります',
        'meaning': "'a veces pasa que ~ / hay veces que ~' (frecuencia baja)",
        'ejemplo': 'あさ ごはんを 食べないことがあります',
        'literal': 'mañana / comida-OBJ / hay-veces-de-no-comer',
        'uso': 'Verbo en presente llano + 「ことがある」: ocurre de vez en cuando. Con verbo en pasado (「たことがある」) cambia a experiencia de toda la vida.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜と思います',
        'meaning': "expresar opinión: 'creo que / pienso que'",
        'ejemplo': 'いいと 思います',
        'literal': 'bueno-QUE / pienso',
        'uso': 'opinión educada. La opinión va marcada con と antes'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ば',
        'meaning': "condicional hipotético: 'si ~'",
        'ejemplo': 'じかんが あれば 行きます',
        'literal': 'tiempo-SUJ / si-hay / voy',
        'uso': "Pone el foco en la condición ('con que se dé esto, basta'); el resultado suele ser algo deseado. Formación: 「う」 -> 「えば」, adjetivo-い -> 「ければ」."
      },
      {
        'kind': 'gramatica',
        'jp': '〜たら',
        'meaning': "condicional: 'si / cuando ocurre X'",
        'ejemplo': '雨が ふったら、家に います',
        'literal': 'lluvia-SUJ / si-llueve / en-casa / estoy',
        'uso': 'condición hipotética. Si + verbo pasado forma la condición'
      },
      {
        'kind': 'gramatica',
        'jp': 'と（条件）',
        'meaning': "consecuencia automática: 'si ~, (siempre) pasa ~'",
        'ejemplo': 'この ボタンを おすと でんきが つきます',
        'literal': 'este / botón-OBJ / al-pulsar / luz-SUJ / se-enciende',
        'uso': 'Verbo en presente llano + 「と」: para leyes naturales, mecanismos e instrucciones. El resultado no puede ser una orden ni una petición.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜なら',
        'meaning': "condición sobre un tema que el otro acaba de sacar: 'si es (lo de) ~, entonces ~'",
        'ejemplo': '京都へ 行くなら バスが べんりです',
        'literal': 'Kioto-A / si-vas / autobús-SUJ / práctico-es',
        'uso': 'Recoges un tema que el otro acaba de sacar y das tu consejo o reacción. Con sustantivo va directo: 「日本語なら田中さんです」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜から（理由）',
        'meaning': "causal: 'porque X' / 'así que Y'",
        'ejemplo': '忙しいから、行けません',
        'literal': 'ocupado-porque / no-puedo-ir',
        'uso': "causal. Más fuerte que 〜ので. 'Así que' cuando cierra un razonamiento"
      },
      {
        'kind': 'gramatica',
        'jp': '〜ので',
        'meaning': "causa presentada con suavidad: 'como ~ / dado que ~'",
        'ejemplo': 'あたまが いたいので 帰ります',
        'literal': 'cabeza-SUJ / como-duele / me-voy',
        'uso': 'Razón expuesta como un hecho, más blanda y educada que 「から」; buena para excusas y peticiones. Tras adjetivo-な o sustantivo: 「なので」.'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ない',
        'reading': 'ない',
        'meaning': 'no hay, no tiene',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      }
    ]
  },
  {
    'id': 'adverbios_cantidad',
    'nombre': 'Adverbios de cantidad y frecuencia',
    'funcion': 'dar intensidad, preguntar cantidad y hablar de cómo de a menudo o cuánto te apetece algo',
    'frases_hechas': [
      {'jp': 'とてもいいです', 'uso': "'es muy bueno'; la intensidad más clara y universal"},
      {'jp': 'あまり好きじゃない', 'uso': "'no me gusta mucho'; suaviza un rechazo"},
      {'jp': 'まだです', 'uso': "'todavía no'; muy común en la vida diaria"},
      {'jp': 'もう終わりました', 'uso': "'ya está'; se oye a cada paso"}
    ],
    'prerequisito': 'negacion_condicional',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'いつも',
        'reading': 'いつも',
        'meaning': 'siempre, normalmente',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "'Siempre, normalmente'. Con verbo en negativo: 'no siempre'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'すぐに',
        'reading': 'すぐに',
        'meaning': 'enseguida, inmediatamente',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ちょっと',
        'reading': 'ちょっと',
        'meaning': 'un poco / un momento',
        'tipo': 'adverbio',
        'ejemplo': 'ちょっと まってください',
        'literal': 'un-poco / espera / por-favor',
        'uso': "modera una petición o un comentario; también como 'de momento'"
      },
      {
        'kind': 'vocabulario',
        'jp': 'とても',
        'reading': 'とても',
        'meaning': 'muy / muchísimo',
        'tipo': 'adverbio',
        'ejemplo': 'とても たのしいです',
        'literal': 'muy / divertido-es',
        'uso': 'grado fuerte. Es un adverbio neutral y muy frecuente'
      },
      {
        'kind': 'vocabulario',
        'jp': 'まだ',
        'reading': 'まだ',
        'meaning': 'todavía / aún / no ... todavía',
        'tipo': 'adverbio',
        'ejemplo': 'まだ かえっていません',
        'literal': 'todavía / no-ha-vuelto',
        'uso': 'si el estado sigue siendo así. A menudo marca espera o no finalización'
      },
      {
        'kind': 'vocabulario',
        'jp': 'もう',
        'reading': 'もう',
        'meaning': 'ya / otra vez / más',
        'tipo': 'adverbio',
        'ejemplo': 'もう ねました',
        'literal': 'ya / dormí',
        'uso': 'se usa para afirmar que algo ya ha pasado o que ya no falta más'
      },
      {
        'kind': 'vocabulario',
        'jp': 'ゆっくりと',
        'reading': 'ゆっくりと',
        'meaning': 'despacio, con calma',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "'Despacio'; también 'con calma, sin prisa': 「ゆっくりしてください」 'ponte cómodo, tómate tu tiempo'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'よく',
        'reading': 'よく',
        'meaning': 'a menudo, bien (hábilmente)',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "Dos sentidos según el contexto: 'a menudo' (「よく来る」) y 'bien, con habilidad' (「よくできた」). También admiración: 「よく分かったね」."
      },
      {
        'kind': 'vocabulario',
        'jp': '丁度',
        'reading': 'ちょうど',
        'meaning': 'justo, exacto',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '余り',
        'reading': 'あまり',
        'meaning': 'no mucho, apenas (con negativo); sobra',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "Con verbo en negativo, 'no mucho, apenas' (「あまり食べない」). Sin negación, como sustantivo, 'lo que sobra'; 「あまりに」 = 'demasiado'."
      },
      {
        'kind': 'vocabulario',
        'jp': '全部',
        'reading': 'ぜんぶ',
        'meaning': 'todo, entero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '多い',
        'reading': 'おおい',
        'meaning': 'mucho, numeroso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'No se pone con soltura delante del nombre: se dice 「人が多い」 o 「多くの人」, no 「多い人」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '多分',
        'reading': 'たぶん',
        'meaning': 'quizás, probablemente',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "'Probablemente'; suele acompañarse de 「～でしょう」 o 「～と思う」."
      },
      {
        'kind': 'vocabulario',
        'jp': '大勢',
        'reading': 'おおぜい',
        'meaning': 'mucha gente',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mucha gente'; solo para personas (「大勢の人」), nunca para cosas."
      },
      {
        'kind': 'vocabulario',
        'jp': '少し',
        'reading': 'すこし',
        'meaning': 'un poco / poco',
        'tipo': 'adverbio',
        'ejemplo': 'すこし 休みましょう',
        'literal': 'un-poco / descansenos',
        'uso': 'cantidad pequeña y poco marcada; muy útil para suavizar una petición'
      },
      {
        'kind': 'vocabulario',
        'jp': '少ない',
        'reading': 'すくない',
        'meaning': 'poco, escaso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '時々',
        'reading': 'ときどき',
        'meaning': 'a veces',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '段々',
        'reading': 'だんだん',
        'meaning': 'poco a poco, gradualmente',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '沢山',
        'reading': 'たくさん',
        'meaning': 'mucho, muchos',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "'Mucho', para cosas y también personas. Si son solo personas, se puede usar 「大勢」."
      },
      {
        'kind': 'vocabulario',
        'jp': '～くらい; ぐらい',
        'reading': '～くらい / ぐらい',
        'meaning': 'aproximadamente',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': 'Cantidad o grado aproximados (「千円ぐらい」). Tras 「これ・それ」 se dice 「くらい」. Para una hora aproximada se usa 「ごろ」, no 「くらい」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～すぎ',
        'reading': '～すぎ',
        'meaning': 'pasado de ~ / demasiado ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pasadas las ~' con horas (「六時すぎ」). Tras la raíz de un verbo o de un adjetivo significa 'demasiado' (「食べすぎ」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '～ずつ',
        'reading': '～ずつ',
        'meaning': 'de ~ en ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Reparto en partes iguales: 'de ~ en ~' (「一つずつ」), 'poco a poco' (「少しずつ」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '～だけ',
        'reading': '～だけ',
        'meaning': 'solo ~, solamente',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Solo ~', sin idea negativa. 「しか」 + verbo en negativo da un sentido parecido pero con matiz de 'no más que'."
      },
      {
        'kind': 'vocabulario',
        'jp': '～など',
        'reading': '～など',
        'meaning': 'etcétera',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'~ etcétera'; suele cerrar una enumeración abierta hecha con 「や」 (「本やノートなど」). Según el tono puede sonar humilde o despectivo."
      }
    ]
  },
  {
    'id': 'forma_casual',
    'nombre': 'Forma plain y registro casual',
    'funcion': 'hablar como con un amigo, sin です ni ます, que es como se habla de verdad fuera del aula',
    'frases_hechas': [
      {
        'jp': 'うん / ううん',
        'uso': 'sí y no informales; solo con gente de confianza, nunca con un jefe'
      },
      {'jp': 'マジで', 'uso': "'¿en serio?'; entre amigos, jamás en el trabajo"},
      {'jp': 'だよね', 'uso': "'ya ves' / 'exacto'; muestra que estáis de acuerdo"},
      {'jp': 'めっちゃ', 'uso': "'un montón'; nació en Kansai y ya se oye en todas partes"}
    ],
    'prerequisito': 'adverbios_cantidad',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'じゃ; じゃあ',
        'reading': 'じゃ / じゃあ',
        'meaning': 'bueno, pues (casual de では)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "Contracción hablada de 「では」: 'bueno, pues…'. Sirve para cerrar o cambiar de tema (「じゃあ、また」)."
      }
    ]
  },
  {
    'id': 'viaje_transporte',
    'nombre': 'Viaje y transporte',
    'funcion': 'moverte por Japón: comprar un billete, preguntar por una línea y pedir direcciones',
    'frases_hechas': [
      {
        'jp': '駅はどこですか',
        'uso': "'¿dónde está la estación?'; cámbiale el sustantivo y sirve para todo"
      },
      {'jp': '次は', 'uso': "'¿la siguiente cuál es?', dentro del tren"},
      {'jp': '乗り換えですか', 'uso': "'¿hay que hacer transbordo?'"},
      {'jp': '気をつけて', 'uso': "'ve con cuidado', al despedir a alguien que se va de viaje"}
    ],
    'prerequisito': 'forma_casual',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'おまわりさん',
        'reading': 'おまわりさん',
        'meaning': 'policía (trato cercano, coloquial)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Forma cercana y cotidiana de 'policía', sobre todo el de barrio. En contexto formal, 「警察官」 o 「警官」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'まっすぐ',
        'reading': 'まっすぐ',
        'meaning': 'recto / todo recto',
        'tipo': 'adverbio',
        'ejemplo': 'ここからまっすぐです',
        'literal': 'desde-aquí / todo-recto',
        'uso': 'dirección. La instrucción más simple para no perderse'
      },
      {
        'kind': 'vocabulario',
        'jp': 'キロ; キロメートル',
        'reading': 'キロ / キロメートル',
        'meaning': 'kilómetro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'デパート',
        'reading': 'デパート',
        'meaning': 'grandes almacenes',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ポスト',
        'reading': 'ポスト',
        'meaning': 'buzón; puesto, posición',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Buzón' de correos (rojo, en la calle) y también 'puesto, cargo'."
      },
      {
        'kind': 'vocabulario',
        'jp': '交差点',
        'reading': 'こうさてん',
        'meaning': 'cruce, intersección',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '交番',
        'reading': 'こうばん',
        'meaning': 'caseta de policía',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Garita de policía de barrio, muy presente en las ciudades japonesas; se va allí a preguntar direcciones o a entregar algo perdido.'
      },
      {
        'kind': 'vocabulario',
        'jp': '八百屋',
        'reading': 'やおや',
        'meaning': 'verdulería, frutería',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '切手',
        'reading': 'きって',
        'meaning': 'sello de correos',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '切符',
        'reading': 'きっぷ',
        'meaning': 'billete / ticket',
        'tipo': 'sustantivo',
        'ejemplo': '切符を 買いました',
        'literal': 'billete-OBJ / compré',
        'uso': 'billete de tren, autobús o avión'
      },
      {
        'kind': 'vocabulario',
        'jp': '北',
        'reading': 'きた',
        'meaning': 'norte',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '南',
        'reading': 'みなみ',
        'meaning': 'sur',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '右',
        'reading': 'みぎ',
        'meaning': 'derecha',
        'tipo': 'sustantivo',
        'ejemplo': '右に 曲がってください',
        'literal': 'derecha-A / gira / por-favor',
        'uso': 'dirección. Izquierda es 左 (ひだり)'
      },
      {
        'kind': 'vocabulario',
        'jp': '喫茶店',
        'reading': 'きっさてん',
        'meaning': 'cafetería',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '図書館',
        'reading': 'としょかん',
        'meaning': 'biblioteca',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '地下鉄',
        'reading': 'ちかてつ',
        'meaning': 'metro / subte',
        'tipo': 'sustantivo',
        'ejemplo': '地下鉄で 行った方が 早いです',
        'literal': 'metro-EN / ir-es / más-rápido',
        'uso': 'metro urbano. Rápido en ciudades grandes'
      },
      {
        'kind': 'vocabulario',
        'jp': '地図',
        'reading': 'ちず',
        'meaning': 'mapa',
        'tipo': 'sustantivo',
        'ejemplo': '地図を 見ています',
        'literal': 'mapa-OBJ / estoy-mirando',
        'uso': 'mapa. En móvil es 地図アプリ (ちずあぷり)'
      },
      {
        'kind': 'vocabulario',
        'jp': '大使館',
        'reading': 'たいしかん',
        'meaning': 'embajada',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '封筒',
        'reading': 'ふうとう',
        'meaning': 'sobre (de carta)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '山',
        'reading': 'やま',
        'meaning': 'montaña',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Montaña'; también 'montón' (「仕事が山ほどある」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '川; 河',
        'reading': 'かわ',
        'meaning': 'río',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '左',
        'reading': 'ひだり',
        'meaning': 'izquierda',
        'tipo': 'sustantivo',
        'ejemplo': '左から 来た',
        'literal': 'izquierda-desde / vino',
        'uso': 'dirección. Viene con la partícula から o に según contexto'
      },
      {
        'kind': 'vocabulario',
        'jp': '建物',
        'reading': 'たてもの',
        'meaning': 'edificio',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '手紙',
        'reading': 'てがみ',
        'meaning': 'carta',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '旅行',
        'reading': 'りょこう',
        'meaning': 'viaje',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '映画館',
        'reading': 'えいがかん',
        'meaning': 'cine',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '曲る',
        'reading': 'まがる',
        'meaning': 'girar, doblar (una dirección)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Girar' en una esquina: 「次の角を右に曲がる」. También 'estar torcido'."
      },
      {
        'kind': 'vocabulario',
        'jp': '村',
        'reading': 'むら',
        'meaning': 'pueblo, aldea',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '東',
        'reading': 'ひがし',
        'meaning': 'este (dirección)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '橋',
        'reading': 'はし',
        'meaning': 'puente',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Puente'. Se pronuncia como 「箸」 'palillos' y 「端」 'borde'; los separa el acento y el contexto."
      },
      {
        'kind': 'vocabulario',
        'jp': '止まる',
        'reading': 'とまる',
        'meaning': 'detenerse, pararse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Intransitivo: 'pararse, detenerse' (「電車が止まる」). Parar algo es 「止める」."
      },
      {
        'kind': 'vocabulario',
        'jp': '歩く',
        'reading': 'あるく',
        'meaning': 'caminar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '渡る',
        'reading': 'わたる',
        'meaning': 'cruzar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Intransitivo: 'cruzar' (「道を渡る」, con 「を」 de recorrido). Dar algo en mano es 「渡す」."
      },
      {
        'kind': 'vocabulario',
        'jp': '町',
        'reading': 'まち',
        'meaning': 'ciudad, barrio',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '登る',
        'reading': 'のぼる',
        'meaning': 'subir, escalar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Subir con esfuerzo, sobre todo montañas (「山に登る」); también escaleras o una cuesta.'
      },
      {
        'kind': 'vocabulario',
        'jp': '着く',
        'reading': 'つく',
        'meaning': 'llegar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Llegar' a un sitio; el destino lleva 「に」: 「駅に着く」. Suena como 「着る」 'ponerse ropa' y 「付く」."
      },
      {
        'kind': 'vocabulario',
        'jp': '自動車',
        'reading': 'じどうしゃ',
        'meaning': 'automóvil',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '自転車',
        'reading': 'じてんしゃ',
        'meaning': 'bicicleta',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '荷物',
        'reading': 'にもつ',
        'meaning': 'equipaje',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '葉書',
        'reading': 'はがき',
        'meaning': 'postal',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '西',
        'reading': 'にし',
        'meaning': 'oeste',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '角',
        'reading': 'かど',
        'meaning': 'esquina',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La esquina vista desde fuera, de una calle o un edificio (「角を曲がる」). El rincón interior de una sala es 「隅」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '警官',
        'reading': 'けいかん',
        'meaning': 'policía (agente)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '車',
        'reading': 'くるま',
        'meaning': 'coche / automóvil',
        'tipo': 'sustantivo',
        'ejemplo': '車を 運転します',
        'literal': 'coche-OBJ / conduzco',
        'uso': 'cualquier automóvil. Conducir es 運転する'
      },
      {
        'kind': 'vocabulario',
        'jp': '速い',
        'reading': 'はやい',
        'meaning': 'rápido',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Rápido' de velocidad (「足が速い」). 'Temprano' en el tiempo se escribe 「早い」."
      },
      {
        'kind': 'vocabulario',
        'jp': '道',
        'reading': 'みち',
        'meaning': 'camino, calle',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '郵便局',
        'reading': 'ゆうびんきょく',
        'meaning': 'oficina de correos',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '銀行',
        'reading': 'ぎんこう',
        'meaning': 'banco',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '電車',
        'reading': 'でんしゃ',
        'meaning': 'tren',
        'tipo': 'sustantivo',
        'ejemplo': '電車で 学校に いきます',
        'literal': 'tren-EN / escuela-A / voy',
        'uso': 'tren urbano o de cercanías. Tren de larga distancia es 列車 (れっしゃ)'
      },
      {
        'kind': 'vocabulario',
        'jp': '飛行機',
        'reading': 'ひこうき',
        'meaning': 'avión',
        'tipo': 'sustantivo',
        'ejemplo': '飛行機は 好きじゃないです',
        'literal': 'avión-TEMA / no-me-gusta',
        'uso': 'avión. Subir a un avión es 飛行機に 乗る'
      },
      {
        'kind': 'vocabulario',
        'jp': '～屋',
        'reading': '～や',
        'meaning': 'tienda de ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Tienda de ~' y, por extensión, quien la lleva (「パン屋さん」 el panadero). Nada que ver con 「部屋」 'habitación'."
      }
    ]
  },
  {
    'id': 'cuerpo_salud',
    'nombre': 'Cuerpo y salud N5',
    'funcion': 'decir que algo te duele y contar cómo te encuentras, en casa o en una farmacia',
    'frases_hechas': [
      {'jp': '大丈夫', 'uso': "'¿estás bien?' preguntando, y 'estoy bien' respondiendo"},
      {'jp': 'お大事に', 'uso': "'cuídate', a alguien enfermo; se dice al despedirse"},
      {'jp': '疲れた〜', 'uso': "'qué cansancio'; se suelta en voz alta sin dirigirlo a nadie"},
      {'jp': 'ちょっと調子が悪い', 'uso': "'no me encuentro muy bien', sin dar detalles"}
    ],
    'prerequisito': 'viaje_transporte',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜んです',
        'meaning': "forma explicativa: da contexto o explicación ('es que...')",
        'ejemplo': 'ちょっと 風邪なんです',
        'literal': 'un-poco / es-que-me-resfriado',
        'uso': 'explica o justifica. Más suave que solo 風邪です'
      },
      {
        'kind': 'vocabulario',
        'jp': 'お腹',
        'reading': 'おなか',
        'meaning': 'barriga, estómago',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "En expresiones de hambre y saciedad: 「おなかがすいた」 'tengo hambre', 「おなかがいっぱい」 'estoy lleno'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'たばこ',
        'reading': 'たばこ',
        'meaning': 'tabaco, cigarrillos',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「たばこを吸う」 'fumar' (no 「飲む」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '体',
        'reading': 'からだ',
        'meaning': 'cuerpo',
        'tipo': 'sustantivo',
        'ejemplo': '体が 疲れています',
        'literal': 'cuerpo-SUJ / estoy-cansado',
        'uso': 'cuerpo entero. Cuidar el cuerpo es 体を 大事にする'
      },
      {
        'kind': 'vocabulario',
        'jp': '元気',
        'reading': 'げんき',
        'meaning': 'con energía / estar bien (adj-な)',
        'tipo': 'adjetivo',
        'ejemplo': '元気ですか',
        'literal': '¿estás-bien?',
        'uso': 'salud. Falta de energía es 元気がない'
      },
      {
        'kind': 'vocabulario',
        'jp': '医者',
        'reading': 'いしゃ',
        'meaning': 'médico',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Al referirte a él con respeto, 「お医者さん」. 「医者に行く」 = 'ir al médico'."
      },
      {
        'kind': 'vocabulario',
        'jp': '口',
        'reading': 'くち',
        'meaning': 'boca',
        'tipo': 'sustantivo',
        'ejemplo': '口が 痛いです',
        'literal': 'boca-SUJ / duele',
        'uso': 'boca. Hablar es 口を 聞く (de verdad) o はなす (lo normal)'
      },
      {
        'kind': 'vocabulario',
        'jp': '吸う',
        'reading': 'すう',
        'meaning': 'aspirar, fumar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '声',
        'reading': 'こえ',
        'meaning': 'voz',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La voz de una persona o un animal (「大きな声」). El sonido de las cosas es 「音」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '太い',
        'reading': 'ふとい',
        'meaning': 'gordo, grueso',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Grueso' para cosas (「太い線」). De una persona gorda se dice 「太っている」, no 「太い」."
      },
      {
        'kind': 'vocabulario',
        'jp': '弱い',
        'reading': 'よわい',
        'meaning': 'débil',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '強い',
        'reading': 'つよい',
        'meaning': 'fuerte',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '手',
        'reading': 'て',
        'meaning': 'mano',
        'tipo': 'sustantivo',
        'ejemplo': '手が 冷たいです',
        'literal': 'mano-SUJ / fría-es',
        'uso': 'mano. Mano derecha es 右手 (みぎて)'
      },
      {
        'kind': 'vocabulario',
        'jp': '歯',
        'reading': 'は',
        'meaning': 'diente',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Diente'. 「歯を磨く」 'cepillarse los dientes'. Se pronuncia como 「葉」 'hoja'."
      },
      {
        'kind': 'vocabulario',
        'jp': '死ぬ',
        'reading': 'しぬ',
        'meaning': 'morir',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Es directo y algo brusco; para personas, por respeto se dice 「亡くなる」 o 「亡くなりました」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '浴びる',
        'reading': 'あびる',
        'meaning': 'ducharse, bañarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Ducharse': 「シャワーを浴びる」. Meterse en la bañera es 「お風呂に入る」."
      },
      {
        'kind': 'vocabulario',
        'jp': '疲れる',
        'reading': 'つかれる',
        'meaning': 'cansarse',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Se usa en pasado para el estado de ahora: 「疲れた」 = 'estoy cansado'."
      },
      {
        'kind': 'vocabulario',
        'jp': '病気',
        'reading': 'びょうき',
        'meaning': 'enfermedad',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '痛い',
        'reading': 'いたい',
        'meaning': 'doloroso / me duele (adj-い)',
        'tipo': 'adjetivo',
        'ejemplo': 'すごく 痛いです',
        'literal': 'mucho / duele',
        'uso': 'adjetivo-い. Duele va en la frase como sujeto + 痛い'
      },
      {
        'kind': 'vocabulario',
        'jp': '目',
        'reading': 'め',
        'meaning': 'ojo/s',
        'tipo': 'sustantivo',
        'ejemplo': '目が 疲れています',
        'literal': 'ojo-SUJ / estoy-cansado',
        'uso': 'ojo, puede ir singular o plural. Llorar es 泣く (なく)'
      },
      {
        'kind': 'vocabulario',
        'jp': '磨く',
        'reading': 'みがく',
        'meaning': 'cepillar (los dientes), pulir',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cepillarse' los dientes (「歯を磨く」) y 'sacar brillo' a zapatos o metal."
      },
      {
        'kind': 'vocabulario',
        'jp': '細い',
        'reading': 'ほそい',
        'meaning': 'fino, delgado',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Fino, estrecho' (「細い道」). 'Detallado, menudo' es otra palabra: 「細かい」."
      },
      {
        'kind': 'vocabulario',
        'jp': '耳',
        'reading': 'みみ',
        'meaning': 'oreja / oído',
        'tipo': 'sustantivo',
        'ejemplo': '耳が 痛いです',
        'literal': 'oído-SUJ / duele',
        'uso': 'oído o parte externa. Limpiar oídos es 耳を 掃除する'
      },
      {
        'kind': 'vocabulario',
        'jp': '背',
        'reading': 'せい',
        'meaning': 'estatura',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Estatura': 「背が高い/低い」. También 'espalda' en 「背中」."
      },
      {
        'kind': 'vocabulario',
        'jp': '薬',
        'reading': 'くすり',
        'meaning': 'medicina / medicamento',
        'tipo': 'sustantivo',
        'ejemplo': '薬を 飲みました',
        'literal': 'medicina-OBJ / tomé',
        'uso': 'medicina. Tomar medicina es 薬を 飲む (no たべる)'
      },
      {
        'kind': 'vocabulario',
        'jp': '足; 脚',
        'reading': 'あし',
        'meaning': 'pie, pierna',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '頭',
        'reading': 'あたま',
        'meaning': 'cabeza',
        'tipo': 'sustantivo',
        'ejemplo': '頭が 痛いです',
        'literal': 'cabeza-SUJ / duele',
        'uso': 'cabeza o parte del cuerpo que duele. Peinarse es 髪を とく'
      },
      {
        'kind': 'vocabulario',
        'jp': '顔',
        'reading': 'かお',
        'meaning': 'cara',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '風邪',
        'reading': 'かぜ',
        'meaning': 'resfriado, gripe',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Resfriado'. Se pronuncia igual que 「風」 'viento'. Se 'coge' con 「引く」: 「風邪を引く」."
      },
      {
        'kind': 'vocabulario',
        'jp': '鼻',
        'reading': 'はな',
        'meaning': 'nariz',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Nariz'. Se pronuncia igual que 「花」 'flor'; se distinguen por el acento y el contexto."
      }
    ]
  },
  {
    'id': 'comparaciones_deseos',
    'nombre': 'Comparaciones y deseos N5',
    'funcion': 'comparar dos cosas, decir cuál prefieres y suavizar una opinión para no imponerla',
    'frases_hechas': [
      {'jp': 'どっちがいい', 'uso': "'¿cuál prefieres?', entre dos opciones"},
      {'jp': '一番好き', 'uso': "'el que más me gusta', de todos"},
      {'jp': '〜のほうがいいかも', 'uso': "'quizá mejor…', para sugerir sin imponer"},
      {'jp': 'そうかもね', 'uso': "'puede ser'; sirve para no llevar la contraria de frente"}
    ],
    'prerequisito': 'cuerpo_salud',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'gramatica',
        'jp': '〜つもりです',
        'meaning': "intención decidida: 'tengo pensado ~ / pienso ~'",
        'ejemplo': 'なつやすみに 国へ 帰るつもりです',
        'literal': 'vacaciones-verano-EN / país-A / pienso-volver',
        'uso': "Plan firme y personal, pero no una promesa. 「行かないつもりです」 ('no pienso ir') no es lo mismo que 「行くつもりはありません」 ('ni me lo planteo')."
      },
      {
        'kind': 'gramatica',
        'jp': '〜でしょう',
        'meaning': "conjetura formal: 'probablemente...' / '¿no es así?'",
        'ejemplo': '明日は 雨でしょう',
        'literal': 'mañana-TEMA / lluvia-será-probablemente',
        'uso': 'suposición educada. Más formal que 〜と思います'
      },
      {
        'kind': 'gramatica',
        'jp': '〜かもしれません',
        'meaning': "posibilidad: 'quizás / puede que...'",
        'ejemplo': 'もしかして 遅れるかもしれません',
        'literal': 'puede-ser / retraso-puede-pasar',
        'uso': 'incertidumbre. Menos seguro que でしょう'
      },
      {
        'kind': 'gramatica',
        'jp': '〜そうです',
        'meaning': "impresión por lo que se ve: 'parece que ~ / tiene pinta de ~'",
        'ejemplo': 'この ケーキは おいしそうです',
        'literal': 'este / pastel-TEMA / tiene-pinta-de-rico',
        'uso': "Juicio inmediato por lo que se ve; raíz de adjetivo o verbo + 「そう」 (「いい」 -> 「よさそう」). Distinto del 「そうです」 de 'dicen que', que va tras forma llana completa."
      },
      {
        'kind': 'gramatica',
        'jp': '〜すぎます',
        'meaning': "exceso: 'demasiado X' (たべすぎる = comer demasiado)",
        'ejemplo': '甘すぎます',
        'literal': 'demasiado-dulce-es',
        'uso': 'demasiado. Verbo + すぎる = hacer demasiado de eso'
      },
      {
        'kind': 'gramatica',
        'jp': '〜より',
        'meaning': "comparativo: 'más que X' (AはBよりおおきい = A es más grande que B)",
        'ejemplo': '彼は 私より 背が 高いです',
        'literal': 'él-TEMA / yo-que / altura-SUJ / alto-es',
        'uso': 'comparación de dos. B lleva より, A es lo que se compara'
      },
      {
        'kind': 'gramatica',
        'jp': '〜のほうが',
        'meaning': "preferencia: 'X es mejor' (BよりAのほうが〜 = A es más ~ que B)",
        'ejemplo': '紅茶より、コーヒーのほうが 好きです',
        'literal': 'té-que / café-de-parte-TEMA / gusta',
        'uso': 'marca preferencia clara. A es lo preferido'
      },
      {
        'kind': 'gramatica',
        'jp': '〜ほど〜ない',
        'meaning': "comparación en negativo: 'no tan ~ como ~'",
        'ejemplo': 'きょうは きのうほど さむくないです',
        'literal': 'hoy-TEMA / como-ayer / no-hace-frío',
        'uso': "El término de comparación lleva 「ほど」 y el adjetivo va en negativo; equivale a 'A es menos ~ que B', dicho desde A."
      },
      {
        'kind': 'gramatica',
        'jp': '〜が好きです',
        'meaning': "gusto: 'me gusta ~' (lo que gusta va con が, no を)",
        'ejemplo': 'わたしは くだものが 好きです',
        'literal': 'yo-TEMA / fruta-SUJ / gusta',
        'uso': '「好き」 es adjetivo-な, no un verbo, por eso lo que gusta lleva 「が」. Mucho: 「大好きです」. Negar con tacto: 「あまり好きじゃないです」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜が嫌いです',
        'meaning': "disgusto: 'no me gusta ~ / detesto ~'",
        'ejemplo': 'おとうとは やさいが 嫌いです',
        'literal': 'hermano-menor-TEMA / verdura-SUJ / no-gusta',
        'uso': "「嫌い」 es adjetivo-な y suena fuerte, casi 'odio'; para rebajarlo, 「あまり好きじゃないです」. Muy fuerte: 「大嫌いです」."
      },
      {
        'kind': 'gramatica',
        'jp': '〜がほしいです',
        'meaning': "querer una cosa: 'ほしい' (solo objetos; para acciones usar 〜たい)",
        'ejemplo': '新しい 靴が ほしいです',
        'literal': 'nuevo / zapatos-SUJ / quiero',
        'uso': 'deseo de objeto. El objeto es el sujeto (con が), no el objeto directo'
      },
      {
        'kind': 'gramatica',
        'jp': '〜が上手です',
        'meaning': "habilidad: 'se te da bien ~'",
        'ejemplo': 'ラウラさんは りょうりが 上手です',
        'literal': 'Laura-san-TEMA / cocina-SUJ / hábil-es',
        'uso': 'Se dice de otras personas; de uno mismo suena a fanfarronada, mejor 「ができます」. Elogio típico: 「日本語が上手ですね」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜が下手です',
        'meaning': "torpeza: 'se te da mal ~'",
        'ejemplo': 'わたしは うたが 下手です',
        'literal': 'yo-TEMA / canción-SUJ / torpe-soy',
        'uso': 'De uno mismo sí se usa, como modestia; soltárselo a otro a la cara es grosero. Más suave: 「あまり上手じゃないです」.'
      },
      {
        'kind': 'gramatica',
        'jp': '〜がわかります',
        'meaning': "comprensión: 'entiendo ~ / se me da ~' (con が)",
        'ejemplo': 'ラウラさんは 英語がわかります',
        'literal': 'Laura-san-TEMA / inglés-SUJ / entiende',
        'uso': "「わかる」 no lleva 「を」: lo que se entiende va con 「が」. No es 「知る」 ('saber, conocer'): 「わかる」 es captar o comprender."
      },
      {
        'kind': 'vocabulario',
        'jp': 'もっと',
        'reading': 'もっと',
        'meaning': "más (grado o cantidad): 'más despacio', 'más grande'",
        'tipo': 'adverbio',
        'ejemplo': 'もっと ゆっくり してください',
        'literal': 'más / despacio / haz',
        'uso': 'más de algo. Con adjetivo: もっと + adj'
      },
      {
        'kind': 'vocabulario',
        'jp': '一番',
        'reading': 'いちばん',
        'meaning': "el más / lo mejor (superlativo): 'el más rápido'",
        'tipo': 'adverbio',
        'ejemplo': 'これが 一番 好きです',
        'literal': 'esto-SUJ / el-más / gusta',
        'uso': 'superlativo. Entre todos. 一番 + adj-い'
      },
      {
        'kind': 'vocabulario',
        'jp': '同じ',
        'reading': 'おなじ',
        'meaning': 'igual, mismo',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Delante de un nombre va directo, sin 「な」: 「同じ本」. Para predicar sí lleva 「だ/です」: 「これと同じです」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '大好き',
        'reading': 'だいすき',
        'meaning': 'me encanta, me gusta mucho',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Me encanta'; lo que gusta lleva 「が」: 「犬が大好きです」. Negativo fuerte: 「大嫌い」."
      },
      {
        'kind': 'vocabulario',
        'jp': '好き',
        'reading': 'すき',
        'meaning': 'gustar, que gusta',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '嫌',
        'reading': 'いや',
        'meaning': 'desagradable, que no gusta',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「いや」 es un rechazo visceral y del momento: 'eso no quiero', 'eso me da rabia'. Más suave: 「あまり好きじゃない」."
      },
      {
        'kind': 'vocabulario',
        'jp': '嫌い',
        'reading': 'きらい',
        'meaning': 'no gustar, odiar',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': '「きらい」 es aversión a algo en general (「野菜が嫌い」); lo que no gusta lleva 「が」. Suena fuerte; para rebajarlo, 「あまり好きじゃない」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '欲しい',
        'reading': 'ほしい',
        'meaning': 'querer (algo)',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Querer una cosa'; lo deseado lleva 「が」: 「車が欲しい」. Solo para uno mismo; de un tercero, 「欲しがっている」."
      },
      {
        'kind': 'vocabulario',
        'jp': '違う',
        'reading': 'ちがう',
        'meaning': 'ser diferente, estar equivocado',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "Es verbo, no adjetivo: 「答えが違う」. Como respuesta, 「違います」 corrige al otro ('no es así'), más directo que 「いいえ」."
      }
    ]
  },
  {
    'id': 'vocabulario_n5_extra',
    'nombre': 'Vocabulario N5 — Cajón de sastre',
    'funcion': 'manejar el vocabulario N5 que no cae en una unidad temática concreta: escuela, medios, animales, países y palabras de andamiaje para preguntar por otras palabras',
    'frases_hechas': [
      {'jp': 'それはどういう意味ですか', 'uso': 'para preguntar qué significa una palabra que no conoces'},
      {'jp': '日本語で何と言いますか', 'uso': 'para preguntar cómo se dice algo en japonés'},
      {'jp': 'もう一回言ってください', 'uso': 'para pedir que repitan algo que no has captado'},
      {'jp': 'ゆっくりお願いします', 'uso': 'para pedir que hablen más despacio'}
    ],
    'prerequisito': 'comparaciones_deseos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'しかし',
        'reading': 'しかし',
        'meaning': 'sin embargo, pero',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Sin embargo', al inicio de frase; de registro escrito o formal. Hablando se usa 「でも」, y en tono casual 「けど」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'そうして; そして',
        'reading': 'そうして / そして',
        'meaning': 'y entonces, así',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'それから',
        'reading': 'それから',
        'meaning': 'y después, luego',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Después de eso, y luego'; encadena acciones o añade algo a una lista. También 'desde entonces'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'それでは',
        'reading': 'それでは',
        'meaning': 'bueno, entonces… (para despedirse o cambiar de tema)',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Bueno, pues nada': para despedirse o pasar a otra cosa, algo más formal que 「じゃあ」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'たて',
        'reading': 'たて',
        'meaning': 'longitud, altura (vertical)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "La dimensión vertical o de fondo; se opone a 「横」 (horizontal). 「たてに書く」 'escribir en vertical'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'では',
        'reading': 'では',
        'meaning': 'entonces, bueno',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Entonces, bueno'; para abrir o cerrar algo. Al hablar suele acortarse a 「じゃ」/「じゃあ」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'でも',
        'reading': 'でも',
        'meaning': 'pero, sin embargo',
        'tipo': 'expresión',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pero', al empezar una frase, en conversación. Tras un sustantivo, 「～でも」 es 'o algo así': 「コーヒーでも飲みませんか」."
      },
      {
        'kind': 'vocabulario',
        'jp': 'また',
        'reading': 'また',
        'meaning': 'de nuevo; además',
        'tipo': 'adverbio',
        'ejemplo': '',
        'literal': '',
        'uso': "'Otra vez' (「また会いましょう」) y 'además'. 「また今度」 = 'otro día será'."
      },
      {
        'kind': 'vocabulario',
        'jp': 'ギター',
        'reading': 'ギター',
        'meaning': 'guitarra',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'クラス',
        'reading': 'クラス',
        'meaning': 'clase (de escuela)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'コピーする',
        'reading': 'コピーする',
        'meaning': 'copiar, hacer una copia',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'スポーツ',
        'reading': 'スポーツ',
        'meaning': 'deporte',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'テスト',
        'reading': 'テスト',
        'meaning': 'examen, prueba',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'テープ',
        'reading': 'テープ',
        'meaning': 'cinta (de audio)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'テープレコーダー',
        'reading': 'テープレコーダー',
        'meaning': 'grabadora de cintas',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ニュース',
        'reading': 'ニュース',
        'meaning': 'noticias',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ノート',
        'reading': 'ノート',
        'meaning': 'cuaderno',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'パーティー',
        'reading': 'パーティー',
        'meaning': 'fiesta',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'フィルム',
        'reading': 'フィルム',
        'meaning': 'carrete de fotos',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'プール',
        'reading': 'プール',
        'meaning': 'piscina',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ペット',
        'reading': 'ペット',
        'meaning': 'mascota',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ペン',
        'reading': 'ペン',
        'meaning': 'bolígrafo',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ページ',
        'reading': 'ページ',
        'meaning': 'página',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'ボールペン',
        'reading': 'ボールペン',
        'meaning': 'bolígrafo (de bola)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': 'レコード',
        'reading': 'レコード',
        'meaning': 'disco (de vinilo)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '万年筆',
        'reading': 'まんねんひつ',
        'meaning': 'pluma estilográfica',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '作文',
        'reading': 'さくぶん',
        'meaning': 'redacción, composición',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '借りる',
        'reading': 'かりる',
        'meaning': 'pedir prestado, deber',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pedir prestado' y quedártelo un tiempo (「本を借りる」). Quien deja la cosa es 「貸す」."
      },
      {
        'kind': 'vocabulario',
        'jp': '動物',
        'reading': 'どうぶつ',
        'meaning': 'animal',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '国',
        'reading': 'くに',
        'meaning': 'país',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '売る',
        'reading': 'うる',
        'meaning': 'vender',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '外国',
        'reading': 'がいこく',
        'meaning': 'país extranjero, extranjero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '外国人',
        'reading': 'がいこくじん',
        'meaning': 'extranjero (persona)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '大学',
        'reading': 'だいがく',
        'meaning': 'universidad',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '字引',
        'reading': 'じびき',
        'meaning': 'diccionario',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Diccionario', palabra algo anticuada; hoy se dice 「辞書」."
      },
      {
        'kind': 'vocabulario',
        'jp': '宿題',
        'reading': 'しゅくだい',
        'meaning': 'deberes (tarea escolar)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '平仮名',
        'reading': 'ひらがな',
        'meaning': 'hiragana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '弾く',
        'reading': 'ひく',
        'meaning': 'tocar (un instrumento de cuerda o piano)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Tocar un instrumento de cuerda o de teclado (「ギターを弾く」). Los de viento van con 「吹く」. Se pronuncia como 「引く」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '意味',
        'reading': 'いみ',
        'meaning': 'significado',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '授業',
        'reading': 'じゅぎょう',
        'meaning': 'clase (de escuela)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '教室',
        'reading': 'きょうしつ',
        'meaning': 'aula',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '文章',
        'reading': 'ぶんしょう',
        'meaning': 'frase, texto',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '新聞',
        'reading': 'しんぶん',
        'meaning': 'periódico',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '方',
        'reading': 'かた',
        'meaning': 'persona (honorífico); manera de hacer',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "Con lectura 「かた」, 'persona' en cortés (「あの方」); tras la raíz de un verbo, 'manera de ~' (「作り方」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '映画',
        'reading': 'えいが',
        'meaning': 'película',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '本',
        'reading': 'ほん',
        'meaning': 'libro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '本当',
        'reading': 'ほんとう',
        'meaning': 'de verdad, cierto',
        'tipo': 'adjetivo',
        'ejemplo': '',
        'literal': '',
        'uso': "「本当に」 = 'de verdad, muy'; 「本当？」 (subiendo el tono) = '¿en serio?'."
      },
      {
        'kind': 'vocabulario',
        'jp': '歌',
        'reading': 'うた',
        'meaning': 'canción',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '歌う',
        'reading': 'うたう',
        'meaning': 'cantar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Cantar' una canción (「歌を歌う」). Lo que canta un pájaro es 「鳴く」."
      },
      {
        'kind': 'vocabulario',
        'jp': '漢字',
        'reading': 'かんじ',
        'meaning': 'kanji',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '片仮名',
        'reading': 'かたかな',
        'meaning': 'katakana',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '犬',
        'reading': 'いぬ',
        'meaning': 'perro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '猫',
        'reading': 'ねこ',
        'meaning': 'gato',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '生徒',
        'reading': 'せいと',
        'meaning': 'alumno, estudiante',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': 'Alumno de primaria a bachillerato. El universitario es 「学生」; quien estudia en otro país, 「留学生」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '留学生',
        'reading': 'りゅうがくせい',
        'meaning': 'estudiante extranjero',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '答える',
        'reading': 'こたえる',
        'meaning': 'responder',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'La pregunta o la persona a la que respondes lleva 「に」: 「質問に答える」.'
      },
      {
        'kind': 'vocabulario',
        'jp': '絵',
        'reading': 'え',
        'meaning': 'dibujo, cuadro',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '習う',
        'reading': 'ならう',
        'meaning': 'aprender',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Aprender' de un profesor, en clases (「ピアノを習う」). 'Memorizar' es 「覚える」; estudiar por tu cuenta, 「勉強する」."
      },
      {
        'kind': 'vocabulario',
        'jp': '英語',
        'reading': 'えいご',
        'meaning': 'inglés (idioma)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '要る',
        'reading': 'いる',
        'meaning': 'necesitar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Hacer falta'; lo necesario lleva 「が」: 「お金がいる」. Suena como 「居る」 'estar', pero es verbo-u (「いります」「いらない」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '覚える',
        'reading': 'おぼえる',
        'meaning': 'aprender de memoria, recordar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Aprender de memoria' y 'retener'. 「覚えている」 = 'me acuerdo' (estado); 'traer a la memoria' es 「思い出す」. Opuesto: 「忘れる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '言葉',
        'reading': 'ことば',
        'meaning': 'palabra, idioma',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '貸す',
        'reading': 'かす',
        'meaning': 'prestar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Prestar' algo a alguien (「お金を貸す」). Recibir algo prestado es 「借りる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '貼る',
        'reading': 'はる',
        'meaning': 'pegar (papel), adherir',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pegar' algo plano con adhesivo (「切手を貼る」「ポスターを貼る」)."
      },
      {
        'kind': 'vocabulario',
        'jp': '質問',
        'reading': 'しつもん',
        'meaning': 'pregunta',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '辞書',
        'reading': 'じしょ',
        'meaning': 'diccionario',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '返す',
        'reading': 'かえす',
        'meaning': 'devolver',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Devolver' lo que te prestaron (「本を返す」); pareja de 「借りる」."
      },
      {
        'kind': 'vocabulario',
        'jp': '鉛筆',
        'reading': 'えんぴつ',
        'meaning': 'lápiz',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '雑誌',
        'reading': 'ざっし',
        'meaning': 'revista',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '音楽',
        'reading': 'おんがく',
        'meaning': 'música',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '頼む',
        'reading': 'たのむ',
        'meaning': 'pedir (un favor)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pedir un favor' (「友達に頼む」) y 'pedir' en un bar o restaurante (「コーヒーを頼む」). 「頼むよ」 = 'cuento contigo'."
      },
      {
        'kind': 'vocabulario',
        'jp': '飛ぶ',
        'reading': 'とぶ',
        'meaning': 'volar, saltar',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': ''
      },
      {
        'kind': 'vocabulario',
        'jp': '鳥',
        'reading': 'とり',
        'meaning': 'pájaro (también: pollo, como comida)',
        'tipo': 'sustantivo',
        'ejemplo': '',
        'literal': '',
        'uso': "'Pájaro'. Para la carne se dice 「とり肉」, aunque en cocina 「とり」 a secas también vale por 'pollo'."
      },
      {
        'kind': 'vocabulario',
        'jp': '鳴く',
        'reading': 'なく',
        'meaning': 'cantar/hacer ruido (un animal)',
        'tipo': 'verbo',
        'ejemplo': '',
        'literal': '',
        'uso': 'El sonido de un animal (「犬が鳴く」). Cuando llora una persona es 「泣く」, que se pronuncia igual.'
      },
      {
        'kind': 'vocabulario',
        'jp': '～がる',
        'reading': '～がる',
        'meaning': "sufijo que muestra señales de sentir algo (寒がる = 'parece tener frío')",
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "Se pega a adjetivos de emoción para hablar de lo que siente OTRA persona a la vista: 「寒がる」 'tener pinta de frío', 「ほしがる」 'querer algo (un tercero)'."
      },
      {
        'kind': 'vocabulario',
        'jp': '～語',
        'reading': '～ご',
        'meaning': 'idioma ~',
        'tipo': 'contador',
        'ejemplo': '',
        'literal': '',
        'uso': "'Idioma ~': 「日本語」「フランス語」. Para 'la asignatura de lengua' se usa 「国語」."
      }
    ]
  },
  {
    'id': 'forma_potencial',
    'nombre': 'Forma potencial: poder hacer X',
    'funcion': 'decir lo que puedes y lo que no puedes hacer, y pedir ayuda cuando algo se te escapa',
    'frases_hechas': [
      {'jp': 'できる', 'uso': "'¿puedes?' preguntando, 'puedo' respondiendo"},
      {'jp': 'ちょっと無理かも', 'uso': "'lo veo difícil'; es el 'no' amable de todos los días"},
      {'jp': '手伝ってくれる', 'uso': "'¿me echas una mano?'"},
      {'jp': 'やってみる', 'uso': "'lo intento'; literalmente 'lo hago a ver qué pasa'"}
    ],
    'prerequisito': 'comparaciones_deseos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': 'できる',
        'reading': 'できる',
        'meaning': 'poder / ser capaz de / estar listo',
        'tipo': 'verbo',
        'uso': "'Poder hacer' algo (「日本語ができる」), 'estar terminado o listo' (「ごはんができた」) y 'surgir' (「友達ができた」)."
      }
    ]
  },
  {
    'id': 'transitivos_intransitivos',
    'nombre': 'Verbos transitivos e intransitivos',
    'funcion': 'distinguir lo que tú haces de lo que pasa solo: abrir una puerta o que la puerta se abra',
    'frases_hechas': [
      {'jp': '開いてる', 'uso': "'¿está abierto?'; describe el estado, no quién lo abrió"},
      {'jp': '壊れちゃった', 'uso': "'se ha roto'; en japonés no se culpa a nadie, la cosa se rompe sola"},
      {'jp': '始まるよ', 'uso': "'que empieza', avisando de que va a comenzar algo"},
      {'jp': '閉めておいて', 'uso': "'déjalo cerrado, porfa'; dejar algo hecho para después"}
    ],
    'prerequisito': 'forma_potencial',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': '始まる',
        'reading': 'はじまる',
        'meaning': 'comenzar / empezar (intransitivo)',
        'tipo': 'verbo',
        'uso': "Intransitivo: 'empezar' (「授業が始まる」). Empezar algo uno mismo es 「始める」."
      },
      {
        'kind': 'vocabulario',
        'jp': '閉まる',
        'reading': 'しまる',
        'meaning': 'cerrarse (intransitivo)',
        'tipo': 'verbo',
        'uso': "Intransitivo: 'cerrarse' (「店が閉まる」). Cerrar algo es 「閉める」."
      },
      {
        'kind': 'vocabulario',
        'jp': '開く',
        'reading': 'あく',
        'meaning': 'abrirse (intransitivo: la puerta se abre sola)',
        'tipo': 'verbo',
        'uso': "Intransitivo: 'abrirse' (「ドアが開く」, sola). Abrir algo es 「開ける」."
      }
    ]
  },
  {
    'id': 'vocabulario_vida',
    'nombre': 'Vocabulario N5 — Vida cotidiana y sociedad',
    'funcion': 'manejarte en el trabajo y en la vida adulta: quedar, llamar, avisar y resolver problemas',
    'frases_hechas': [
      {
        'jp': 'おつかれさまです',
        'uso': 'el saludo del trabajo a cualquier hora: hola, adiós y gracias a la vez'
      },
      {'jp': 'ちょっといいですか', 'uso': "'¿tienes un momento?', antes de interrumpir a alguien"},
      {'jp': '確認します', 'uso': "'lo compruebo'; la respuesta segura cuando no sabes algo"},
      {'jp': 'お先に失礼します', 'uso': "'me voy antes que vosotros', al salir de la oficina"}
    ],
    'prerequisito': 'transitivos_intransitivos',
    'umbral_prereq': 0.75,
    'items': [
      {
        'kind': 'vocabulario',
        'jp': '仕事',
        'reading': 'しごと',
        'meaning': 'trabajo / empleo',
        'tipo': 'sustantivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '会社',
        'reading': 'かいしゃ',
        'meaning': 'empresa / compañía',
        'tipo': 'sustantivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '便利',
        'reading': 'べんり',
        'meaning': 'conveniente / práctico (adj-な)',
        'tipo': 'adjetivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '問題',
        'reading': 'もんだい',
        'meaning': 'problema / cuestión',
        'tipo': 'sustantivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '大切',
        'reading': 'たいせつ',
        'meaning': 'importante / valioso (adj-な)',
        'tipo': 'adjetivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '練習',
        'reading': 'れんしゅう',
        'meaning': 'práctica / ejercicio',
        'tipo': 'sustantivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '色々',
        'reading': 'いろいろ',
        'meaning': 'varios / diverso / de todo tipo',
        'tipo': 'adjetivo'
      },
      {
        'kind': 'vocabulario',
        'jp': '電話',
        'reading': 'でんわ',
        'meaning': 'teléfono / llamada telefónica',
        'tipo': 'sustantivo'
      }
    ]
  },
]


# Los 108 kanji N5 entran como bloque de cierre del N5, justo antes del N4: para
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
