def sm2(quality: int, reps: int, ease: float, interval: int) -> tuple:
    """Devuelve (reps, ease, interval_days) según SM-2.

    quality: 0-5 (calidad del recuerdo).
    Mapeo desde extracción: bien→5, duda→3, mal→1.
    """
    if quality < 3:
        reps = 0
        interval = 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = round(interval * ease)

    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease < 1.3:
        ease = 1.3

    return reps, ease, interval
