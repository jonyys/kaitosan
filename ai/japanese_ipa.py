import pykakasi

kks = pykakasi.kakasi()

# Mapeo de hiragana a IPA (cada sílaba completa)
HIRAGANA_IPA = {
    "あ": "a", "い": "i", "う": "ɯ", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "kɯ", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gɯ", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "ɕi", "す": "sɯ", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ʑi", "ず": "zɯ", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "tɕi", "つ": "tsɯ", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ʑi", "づ": "zɯ", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nɯ", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "çi", "ふ": "ɸɯ", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bɯ", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pɯ", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mɯ", "め": "me", "も": "mo",
    "や": "ja", "ゆ": "jɯ", "よ": "jo",
    "ら": "ɾa", "り": "ɾi", "る": "ɾɯ", "れ": "ɾe", "ろ": "ɾo",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o",
    "ん": "N",
    "きゃ": "kja", "きゅ": "kjɯ", "きょ": "kjo",
    "ぎゃ": "gja", "ぎゅ": "gjɯ", "ぎょ": "gjo",
    "しゃ": "ɕa", "しゅ": "ɕɯ", "しょ": "ɕo",
    "じゃ": "ʑa", "じゅ": "ʑɯ", "じょ": "ʑo",
    "ちゃ": "tɕa", "ちゅ": "tɕɯ", "ちょ": "tɕo",
    "ぢゃ": "ʑa", "ぢゅ": "ʑɯ", "ぢょ": "ʑo",
    "にゃ": "ɲa", "にゅ": "ɲɯ", "にょ": "ɲo",
    "ひゃ": "ça", "ひゅ": "çɯ", "ひょ": "ço",
    "びゃ": "bja", "びゅ": "bjɯ", "びょ": "bjo",
    "ぴゃ": "pja", "ぴゅ": "pjɯ", "ぴょ": "pjo",
    "みゃ": "mja", "みゅ": "mjɯ", "みょ": "mjo",
    "りゃ": "ɾja", "りゅ": "ɾjɯ", "りょ": "ɾjo",
    "ー": "ː",  # alargamiento (si aparece)
}

VOCALES = 'aiɯeo'


def texto_a_ipa(texto: str) -> str:
    """
    Convierte texto japonés (kanji/kana) a transcripción IPA
    aplicando ensordecimiento vocálico realista.
    """
    resultado = kks.convert(texto)
    moras_ipa = []
    i = 0
    items = resultado  # lista de dicts con 'orig' y 'hira'

    while i < len(items):
        hira = items[i]['hira']

        if hira == 'っ':
            # Geminación: duplicar consonante de la siguiente mora
            if i + 1 < len(items):
                next_hira = items[i+1]['hira']
                next_ipa = HIRAGANA_IPA.get(next_hira, '')
                if next_ipa:
                    # Extraer consonante inicial
                    idx_vocal = next((j for j, ch in enumerate(next_ipa) if ch in VOCALES), None)
                    if idx_vocal is not None and idx_vocal > 0:
                        cons = next_ipa[:idx_vocal]
                        # Duplicar consonante
                        next_ipa = cons + next_ipa
                moras_ipa.append(next_ipa)
                i += 2
                continue
            else:
                i += 1
                continue
        else:
            ipa = HIRAGANA_IPA.get(hira, '')
            if ipa:
                moras_ipa.append(ipa)
            i += 1

    # Aplicar ensordecimiento de vocales altas entre consonantes sordas o final
    moras_ipa = _aplicar_ensordecimiento(moras_ipa)
    return ''.join(moras_ipa)


def _es_consonante_sorda(cons: str) -> bool:
    """Determina si una cadena representa una consonante sorda en IPA."""
    if not cons:
        return False
    sordas_inicio = ('k', 's', 't', 'h', 'p', 'ɕ', 'ç', 'ɸ')
    if cons.startswith(('ts', 'tɕ')):
        return True
    if cons[0] in sordas_inicio:
        return True
    return False


def _aplicar_ensordecimiento(moras):
    """
    Aplica la regla de ensordecimiento de /i/ y /ɯ/
    entre consonantes sordas o al final de frase.
    """
    nuevas = []
    for idx, mora in enumerate(moras):
        if not mora:
            nuevas.append('')
            continue

        # Buscar la última vocal de la mora
        ultima_vocal_idx = -1
        for j, ch in enumerate(mora):
            if ch in VOCALES:
                ultima_vocal_idx = j

        if ultima_vocal_idx == -1:   # sin vocal (ej. N, ː)
            nuevas.append(mora)
            continue

        vocal = mora[ultima_vocal_idx]
        if vocal not in ('i', 'ɯ'):
            nuevas.append(mora)
            continue

        consonante = mora[:ultima_vocal_idx]
        if not _es_consonante_sorda(consonante):
            nuevas.append(mora)
            continue

        # Contexto derecho
        siguiente_mora = moras[idx+1] if idx+1 < len(moras) else None
        if siguiente_mora is None:
            # Final de frase → eliminar vocal (ensordecimiento)
            nuevas.append(consonante)
        else:
            # Extraer consonante inicial de la siguiente mora
            sig_cons = ''
            for ch in siguiente_mora:
                if ch in VOCALES:
                    break
                sig_cons += ch
            if _es_consonante_sorda(sig_cons):
                nuevas.append(consonante)   # eliminar vocal
            else:
                nuevas.append(mora)
    return nuevas