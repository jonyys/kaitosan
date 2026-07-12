from ai.japanese_ipa import texto_a_ipa


def comparar_pronunciacion(objetivo: str, hablado: str) -> dict:
    """
    Compara la pronunciación de Laura con la frase objetivo.
    Devuelve precisión (0-100) y feedback.
    """
    # Convertir ambas a IPA
    ipa_objetivo = texto_a_ipa(objetivo)
    ipa_hablado = texto_a_ipa(hablado)

    if not ipa_objetivo or not ipa_hablado:
        return {"precision": 0, "feedback": "No se pudo analizar la pronunciación."}

    # Normalizar: eliminar diacríticos de ensordecimiento para comparación más indulgente
    def normalizar(ipa: str) -> str:
        # Eliminar marcas de ensordecimiento vocálico (◌̥) y otros diacríticos menores
        ipa = ipa.replace("\u0325", "")  # ensordecimiento
        ipa = ipa.replace("\u032F", "")  # no silábico
        ipa = ipa.replace("\u0303", "")  # nasalización (para N)
        return ipa

    ipa_obj_norm = normalizar(ipa_objetivo)
    ipa_hab_norm = normalizar(ipa_hablado)

    # Calcular distancia de Levenshtein
    distancia = _levenshtein(ipa_obj_norm, ipa_hab_norm)
    max_len = max(len(ipa_obj_norm), len(ipa_hab_norm))
    
    if max_len == 0:
        return {"precision": 100, "feedback": "Sin datos para comparar."}

    precision = round((1 - distancia / max_len) * 100, 1)
    precision = max(0, min(100, precision))

    # Generar feedback
    if precision >= 95:
        feedback = "¡Pronunciación perfecta!"
    elif precision >= 85:
        feedback = "Muy bien, casi perfecto."
    elif precision >= 70:
        feedback = "Bastante bien, pero puedes mejorar algún sonido."
    elif precision >= 50:
        feedback = "Se entiende, pero practica un poco más la pronunciación."
    else:
        feedback = "Inténtalo de nuevo, prestando atención a cada sílaba."

    # Detectar diferencias específicas
    diferencias = []
    for i, (a, b) in enumerate(zip(ipa_obj_norm, ipa_hab_norm)):
        if a != b:
            diferencias.append(f"posición {i+1}: esperado '{a}' vs dicho '{b}'")
    
    if diferencias and precision < 95:
        feedback += " Detalles: " + "; ".join(diferencias[:3])

    return {
        "precision": precision,
        "feedback": feedback,
        "ipa_objetivo": ipa_objetivo,
        "ipa_hablado": ipa_hablado
    }


def _levenshtein(s1: str, s2: str) -> int:
    """Distancia de Levenshtein entre dos strings"""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]