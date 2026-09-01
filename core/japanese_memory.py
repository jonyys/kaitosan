import sqlite3
from datetime import datetime
from ai.sensei.srs import sm2


class JapaneseMemory:
    def __init__(self, db_path):
        self.db_path = db_path
        self._inicializar_tablas()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _inicializar_tablas(self):
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS japanese_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    reading TEXT,
                    meaning TEXT,
                    type TEXT,
                    status TEXT DEFAULT 'learning',
                    confidence REAL DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    last_reviewed DATETIME,
                    times_reviewed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_grammar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grammar_point TEXT NOT NULL,
                    description TEXT,
                    mastery REAL DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS japanese_kanji (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kanji TEXT NOT NULL,
                    reading TEXT,
                    meaning TEXT,
                    type TEXT DEFAULT 'kanji',
                    status TEXT DEFAULT 'learning',
                    confidence REAL DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    last_reviewed DATETIME,
                    times_reviewed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reps INTEGER DEFAULT 0,
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 0,
                    next_review TEXT,
                    times_correct INTEGER DEFAULT 0,
                    first_taught_session_id INTEGER
                );

                CREATE TABLE IF NOT EXISTS japanese_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    words_learned INTEGER DEFAULT 0,
                    grammar_practiced TEXT,
                    errors_noted TEXT,
                    summary TEXT
                );

                CREATE TABLE IF NOT EXISTS laura_episodios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    episodio TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS kaito_anecdotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    anecdota TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS kanji_mnemo (
                    kanji TEXT PRIMARY KEY,
                    mnemo TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS can_do_progreso (
                    can_do_id     TEXT PRIMARY KEY,
                    estado        TEXT DEFAULT 'no_intentado',  -- no_intentado | en_progreso | dominado
                    veces_ok      INTEGER DEFAULT 0,
                    ultima_sesion INTEGER,
                    nota          TEXT
                );
            """)
        self._migrar_srs()

    def _migrar_srs(self):
        """Migración idempotente: añade columnas SRS si no existen."""
        vocab_cols = {
            "reps": "INTEGER DEFAULT 0",
            "ease_factor": "REAL DEFAULT 2.5",
            "interval_days": "INTEGER DEFAULT 0",
            "next_review": "TEXT",
            "times_correct": "INTEGER DEFAULT 0",
            "first_taught_session_id": "INTEGER",
        }
        grammar_cols = {
            "reps": "INTEGER DEFAULT 0",
            "ease_factor": "REAL DEFAULT 2.5",
            "interval_days": "INTEGER DEFAULT 0",
            "next_review": "TEXT",
            "times_seen": "INTEGER DEFAULT 0",
            "times_correct": "INTEGER DEFAULT 0",
            # espejo de vocab/kanji: lo que Laura pidió en sesión no se purga
            # (Fase 04) y lo poblará el extractor en la Fase 08.
            "first_taught_session_id": "INTEGER",
        }
        kanji_cols = {
            "reps": "INTEGER DEFAULT 0",
            "ease_factor": "REAL DEFAULT 2.5",
            "interval_days": "INTEGER DEFAULT 0",
            "next_review": "TEXT",
            "times_correct": "INTEGER DEFAULT 0",
            "first_taught_session_id": "INTEGER",
        }
        with self._conectar() as conn:
            self._add_columns_if_missing(conn, "japanese_vocabulary", vocab_cols)
            self._add_columns_if_missing(conn, "japanese_grammar", grammar_cols)
            self._add_columns_if_missing(conn, "japanese_kanji", kanji_cols)
            conn.execute(
                "UPDATE japanese_vocabulary SET next_review = date('now') WHERE next_review IS NULL"
            )
            conn.execute(
                "UPDATE japanese_grammar SET next_review = date('now') WHERE next_review IS NULL"
            )
            conn.execute(
                "UPDATE japanese_kanji SET next_review = date('now') WHERE next_review IS NULL"
            )

    def _add_columns_if_missing(self, conn, table, columns):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for col, definition in columns.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

    # ── Mnemotecnias de kanji personalizadas por Laura ─────────────────────

    def get_mnemos(self) -> dict:
        """{kanji: mnemo} con las reglas que Laura ha reescrito."""
        with self._conectar() as conn:
            return dict(conn.execute("SELECT kanji, mnemo FROM kanji_mnemo"))

    def set_mnemo(self, kanji: str, texto: str):
        """Guarda la mnemotecnia de Laura; texto vacío borra y vuelve a la de serie."""
        texto = (texto or "").strip()
        with self._conectar() as conn:
            if texto:
                conn.execute(
                    "INSERT INTO kanji_mnemo (kanji, mnemo) VALUES (?, ?) "
                    "ON CONFLICT(kanji) DO UPDATE SET mnemo = excluded.mnemo",
                    (kanji, texto),
                )
            else:
                conn.execute("DELETE FROM kanji_mnemo WHERE kanji = ?", (kanji,))

    # ── Métodos SRS nuevos ──────────────────────────────────────────────────

    def add_item(self, kind, jp, reading=None, meaning=None, tipo=None, session_id=None):
        """Inserta un ítem nuevo si no existe; si existe, no duplica.

        kind: "vocabulario" | "gramatica" | "kanji"
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if kind == "vocabulario":
            with self._conectar() as conn:
                existing = conn.execute(
                    "SELECT id FROM japanese_vocabulary WHERE word = ?", (jp,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO japanese_vocabulary
                           (word, reading, meaning, type, status, confidence,
                            reps, ease_factor, interval_days, next_review,
                            times_reviewed, times_correct, first_taught_session_id)
                           VALUES (?, ?, ?, ?, 'learning', 0,
                                   0, 2.5, 0, ?,
                                   0, 0, ?)""",
                        (jp, reading, meaning, tipo, today, session_id),
                    )
        elif kind == "gramatica":
            with self._conectar() as conn:
                existing = conn.execute(
                    "SELECT id FROM japanese_grammar WHERE grammar_point = ?", (jp,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO japanese_grammar
                           (grammar_point, description, mastery,
                            reps, ease_factor, interval_days, next_review,
                            times_seen, times_correct)
                           VALUES (?, ?, 0,
                                   0, 2.5, 0, ?,
                                   0, 0)""",
                        (jp, meaning, today),
                    )
        elif kind == "kanji":
            with self._conectar() as conn:
                existing = conn.execute(
                    "SELECT id FROM japanese_kanji WHERE kanji = ?", (jp,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO japanese_kanji
                           (kanji, reading, meaning, type, status, confidence,
                            reps, ease_factor, interval_days, next_review,
                            times_reviewed, times_correct, first_taught_session_id)
                           VALUES (?, ?, ?, 'kanji', 'learning', 0,
                                   0, 2.5, 0, ?,
                                   0, 0, ?)""",
                        (jp, reading, meaning, today, session_id),
                    )

    def get_due_items(self, limit=5, kind="vocabulario"):
        """Devuelve ítems cuyo next_review <= hoy, ordenados por fecha."""
        today = datetime.now().strftime("%Y-%m-%d")
        if kind == "vocabulario":
            query = """
                SELECT id, word AS jp, reading, meaning, type,
                       reps, ease_factor, interval_days, next_review, status
                FROM japanese_vocabulary
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """
        elif kind == "kanji":
            query = """
                SELECT id, kanji AS jp, reading, meaning, type,
                       reps, ease_factor, interval_days, next_review, status
                FROM japanese_kanji
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """
        else:
            query = """
                SELECT id, grammar_point AS jp, description AS meaning,
                       reps, ease_factor, interval_days, next_review, mastery
                FROM japanese_grammar
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """

        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (today, limit)).fetchall()
            return [dict(r) for r in rows]

    def review(self, item_id, quality, kind="vocabulario"):
        """Aplica SM-2 al ítem y actualiza la BD."""
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().isoformat(sep=" ", timespec="seconds")

        if kind == "vocabulario":
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT reps, ease_factor, interval_days FROM japanese_vocabulary WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if not row:
                    return
                reps, ease, interval = sm2(quality, row[0], row[1], row[2])
                from datetime import timedelta
                next_review = (
                    datetime.now() + timedelta(days=max(interval, 1))
                ).strftime("%Y-%m-%d")

                if interval >= 21:
                    status = "mastered"
                elif interval >= 7:
                    status = "learned"
                else:
                    status = "learning"

                conn.execute(
                    """UPDATE japanese_vocabulary SET
                           reps = ?, ease_factor = ?, interval_days = ?,
                           next_review = ?, status = ?,
                           times_reviewed = times_reviewed + 1,
                           times_correct = times_correct + ?,
                           errors = errors + ?,
                           last_reviewed = ?
                       WHERE id = ?""",
                    (
                        reps, round(ease, 4), interval,
                        next_review, status,
                        1 if quality >= 3 else 0,
                        1 if quality < 3 else 0,
                        now, item_id,
                    ),
                )
        elif kind == "kanji":
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT reps, ease_factor, interval_days FROM japanese_kanji WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if not row:
                    return
                reps, ease, interval = sm2(quality, row[0], row[1], row[2])
                from datetime import timedelta
                next_review = (
                    datetime.now() + timedelta(days=max(interval, 1))
                ).strftime("%Y-%m-%d")

                if interval >= 21:
                    status = "mastered"
                elif interval >= 7:
                    status = "learned"
                else:
                    status = "learning"

                conn.execute(
                    """UPDATE japanese_kanji SET
                           reps = ?, ease_factor = ?, interval_days = ?,
                           next_review = ?, status = ?,
                           times_reviewed = times_reviewed + 1,
                           times_correct = times_correct + ?,
                           errors = errors + ?,
                           last_reviewed = ?
                       WHERE id = ?""",
                    (
                        reps, round(ease, 4), interval,
                        next_review, status,
                        1 if quality >= 3 else 0,
                        1 if quality < 3 else 0,
                        now, item_id,
                    ),
                )
        elif kind == "gramatica":
            with self._conectar() as conn:
                row = conn.execute(
                    "SELECT reps, ease_factor, interval_days FROM japanese_grammar WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if not row:
                    return
                reps, ease, interval = sm2(quality, row[0], row[1], row[2])
                from datetime import timedelta
                next_review = (
                    datetime.now() + timedelta(days=max(interval, 1))
                ).strftime("%Y-%m-%d")

                correct_delta = 1 if quality >= 3 else 0
                conn.execute(
                    """UPDATE japanese_grammar SET
                           reps = ?, ease_factor = ?, interval_days = ?,
                           next_review = ?,
                           mastery = CAST(times_correct + ? AS REAL) / (times_seen + 1) * 100,
                           times_seen = times_seen + 1,
                           times_correct = times_correct + ?,
                           errors = errors + ?,
                           last_used = ?
                       WHERE id = ?""",
                    (
                        reps, round(ease, 4), interval,
                        next_review,
                        correct_delta,
                        correct_delta,
                        1 if quality < 3 else 0,
                        now, item_id,
                    ),
                )

    def vocab_rows(self) -> dict:
        """{word: {reading, meaning, type, status, reps}} de todo el vocabulario en BD."""
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            return {r["word"]: dict(r) for r in conn.execute(
                "SELECT word, reading, meaning, type, status, "
                "COALESCE(reps, 0) AS reps FROM japanese_vocabulary"
            )}

    def gram_rows(self) -> dict:
        """{grammar_point: {description, mastery, reps}} de toda la gramática en BD."""
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            return {r["grammar_point"]: dict(r) for r in conn.execute(
                "SELECT grammar_point, description, COALESCE(mastery, 0) AS mastery, "
                "COALESCE(reps, 0) AS reps FROM japanese_grammar"
            )}

    def purgar_fuera_de_temario(self, jps_vocab, jps_gram):
        """Borra vocabulario y gramática que solo existían por el temario viejo
        N4/N3: filas cuyo texto japonés no está en el temario N5 actual Y que
        nadie pidió en sesión (`first_taught_session_id IS NULL`).

        Idempotente: en la segunda pasada ya no queda nada fuera de temario sin
        pedir, así que no borra nada. Se corre una vez al desplegar.
        Devuelve (borradas_vocab, borradas_gram).
        """
        jps_vocab = set(jps_vocab)
        jps_gram = set(jps_gram)
        with self._conectar() as conn:
            vocab = conn.execute(
                "SELECT id, word FROM japanese_vocabulary "
                "WHERE first_taught_session_id IS NULL"
            ).fetchall()
            sobra_v = [(i,) for i, w in vocab if w not in jps_vocab]
            conn.executemany(
                "DELETE FROM japanese_vocabulary WHERE id = ?", sobra_v
            )

            gram = conn.execute(
                "SELECT id, grammar_point FROM japanese_grammar "
                "WHERE first_taught_session_id IS NULL"
            ).fetchall()
            sobra_g = [(i,) for i, g in gram if g not in jps_gram]
            conn.executemany(
                "DELETE FROM japanese_grammar WHERE id = ?", sobra_g
            )
        return len(sobra_v), len(sobra_g)

    def marcar_completo(self, jp, kind="vocabulario", reading=None, meaning=None, tipo=None):
        """Marca una palabra, kanji o punto de gramática como aprendido del todo:
        fuera de la cola de repaso y del flujo de ítems nuevos de las sesiones.
        Crea la fila si Laura aún no la tenía."""
        if kind == "gramatica":
            with self._conectar() as conn:
                existe = conn.execute(
                    "SELECT 1 FROM japanese_grammar WHERE grammar_point = ?", (jp,)
                ).fetchone()
                if existe:
                    conn.execute(
                        """UPDATE japanese_grammar SET
                               mastery=100, reps=MAX(COALESCE(reps, 0), 8),
                               ease_factor=2.5, interval_days=36500,
                               next_review=date('now', '+36500 days'), errors=0
                           WHERE grammar_point = ?""",
                        (jp,),
                    )
                else:
                    conn.execute(
                        """INSERT INTO japanese_grammar
                               (grammar_point, description, mastery,
                                reps, ease_factor, interval_days, next_review,
                                times_seen, times_correct)
                           VALUES (?, ?, 100,
                                   8, 2.5, 36500, date('now', '+36500 days'), 0, 8)""",
                        (jp, meaning),
                    )
            return

        tabla, col = (("japanese_kanji", "kanji") if kind == "kanji"
                      else ("japanese_vocabulary", "word"))
        with self._conectar() as conn:
            existe = conn.execute(
                f"SELECT 1 FROM {tabla} WHERE {col} = ?", (jp,)
            ).fetchone()
            if existe:
                conn.execute(
                    f"""UPDATE {tabla} SET
                           status='mastered', reps=MAX(COALESCE(reps, 0), 8),
                           ease_factor=2.5, interval_days=36500,
                           next_review=date('now', '+36500 days'), errors=0
                       WHERE {col} = ?""",
                    (jp,),
                )
            else:
                conn.execute(
                    f"""INSERT INTO {tabla}
                           ({col}, reading, meaning, type, status, confidence,
                            reps, ease_factor, interval_days, next_review,
                            times_reviewed, times_correct)
                       VALUES (?, ?, ?, ?, 'mastered', 0,
                               8, 2.5, 36500, date('now', '+36500 days'), 0, 8)""",
                    (jp, reading, meaning, tipo or ("kanji" if kind == "kanji" else "vocabulario")),
                )

    def dominados(self, kind: str = "kanji") -> set:
        """Textos (jp) que se cuentan como aprendidos del todo:
        status 'learned'/'mastered', mastery >= 100 o reps >= 2."""
        if kind == "gramatica":
            with self._conectar() as conn:
                return {r[0] for r in conn.execute(
                    "SELECT grammar_point FROM japanese_grammar "
                    "WHERE COALESCE(mastery, 0) >= 100 OR COALESCE(reps, 0) >= 2"
                )}
        tabla, col = (("japanese_kanji", "kanji") if kind == "kanji"
                      else ("japanese_vocabulary", "word"))
        with self._conectar() as conn:
            return {r[0] for r in conn.execute(
                f"SELECT {col} FROM {tabla} "
                "WHERE status IN ('learned', 'mastered') OR COALESCE(reps, 0) >= 2"
            )}

    # ── Estado de ítem y progreso de can-dos (Fase 07) ─────────────────────

    def estado_item(self, jp: str, kind: str = "vocabulario") -> str:
        """'sabido' | 'en_progreso' | 'nuevo' para un ítem de vocab/gramática.

        Fuente única de la lógica que vivía en `app.py:_temario_unidades()`
        ('aprendida'/'en_curso'/'nueva' desde `status`+`reps`). Renombrada 1:1:
        aprendida→sabido, en_curso→en_progreso, sin fila/nueva→nuevo.
        """
        with self._conectar() as conn:
            if kind == "gramatica":
                row = conn.execute(
                    "SELECT COALESCE(reps, 0), COALESCE(mastery, 0) "
                    "FROM japanese_grammar WHERE grammar_point = ?", (jp,),
                ).fetchone()
                if not row:
                    return "nuevo"
                reps, mastery = row
                return "sabido" if reps >= 2 or mastery >= 100 else "en_progreso"
            row = conn.execute(
                "SELECT COALESCE(reps, 0), status "
                "FROM japanese_vocabulary WHERE word = ?", (jp,),
            ).fetchone()
            if not row:
                return "nuevo"
            reps, status = row
            if reps >= 2 or status in ("learned", "mastered"):
                return "sabido"
            return "en_progreso"

    def set_can_do(self, can_do_id: str, resultado: str, session_id, nota: str = None):
        """Registra el resultado de un can-do en una sesión y recalcula su estado.

        resultado: 'conseguido' | 'parcial' | 'error' | 'no_intentado'
        - 'conseguido' en 2 sesiones distintas (session_id distinto) → 'dominado'
        - un solo 'conseguido' → 'en_progreso', veces_ok = 1
        - 'error' / 'parcial' estando ya 'dominado' → baja a 'en_progreso'
        - 'no_intentado' no cambia el estado.
        `nota` — evidencia textual de la sesión (cita del extractor). Si se pasa
        no vacía, se guarda; si es None se conserva la nota previa.
        Upsert: crea la fila si no existe. Actualiza veces_ok y ultima_sesion.
        """
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT estado, veces_ok, ultima_sesion, nota FROM can_do_progreso "
                "WHERE can_do_id = ?", (can_do_id,),
            ).fetchone()
            estado, veces_ok, ultima, nota_prev = (
                row if row else ("no_intentado", 0, None, None)
            )

            if resultado == "conseguido":
                if session_id != ultima:
                    veces_ok += 1
                estado = "dominado" if veces_ok >= 2 else "en_progreso"
            elif resultado in ("error", "parcial") and estado == "dominado":
                estado = "en_progreso"

            nota_final = nota if nota else nota_prev

            conn.execute(
                """INSERT INTO can_do_progreso
                       (can_do_id, estado, veces_ok, ultima_sesion, nota)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(can_do_id) DO UPDATE SET
                       estado = excluded.estado,
                       veces_ok = excluded.veces_ok,
                       ultima_sesion = excluded.ultima_sesion,
                       nota = excluded.nota""",
                (can_do_id, estado, veces_ok, session_id, nota_final),
            )

    def can_dos_progreso(self) -> dict:
        """{can_do_id: {estado, veces_ok, ultima_sesion, nota}}."""
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            return {r["can_do_id"]: {
                "estado": r["estado"],
                "veces_ok": r["veces_ok"],
                "ultima_sesion": r["ultima_sesion"],
                "nota": r["nota"],
            } for r in conn.execute(
                "SELECT can_do_id, estado, veces_ok, ultima_sesion, nota "
                "FROM can_do_progreso"
            )}

    def fraccion_can_dos(self, unit_id: str) -> float:
        """Fracción de can-dos de la unidad (según CURRICULUM) en 'dominado'.
        0.0 si la unidad no existe o no tiene can-dos."""
        from ai.sensei.curriculum import CURRICULUM

        unidad = next((u for u in CURRICULUM if u.get("id") == unit_id), None)
        can_dos = (unidad or {}).get("can_dos", [])
        if not can_dos:
            return 0.0
        prog = self.can_dos_progreso()
        dominados = sum(
            1 for cd in can_dos
            if prog.get(cd["id"], {}).get("estado") == "dominado"
        )
        return dominados / len(can_dos)

    def boletin(self) -> dict:
        """Contexto de /japones/boletin (solo lectura, Fase 11).

        - can-dos por unidad temática con estado visual (○ no_intentado /
          ◐ en_progreso / ● dominado) y la sesión en que se consiguieron los
          dominados. Las unidades de kanji (sin can-dos) van aparte, como enlace.
        - inventario N5: vocab no-kanji y gramática en estado 'sabido'
          (`estado_item`), sobre el total real del temario (jp distintos en
          CURRICULUM, no el 717/~80 aproximado del plan).
        - puntos débiles activos (los que ya trackea `resumen_perfil`).
        """
        from ai.sensei.curriculum import CURRICULUM

        prog = self.can_dos_progreso()
        simbolo = {"no_intentado": "○", "en_progreso": "◐", "dominado": "●"}

        unidades, kanji_unidades = [], []
        cd_total = cd_dominados = 0
        for u in CURRICULUM:
            cds = u.get("can_dos", [])
            if not cds:
                kanji_unidades.append({"id": u["id"], "nombre": u.get("nombre", "")})
                continue
            filas = []
            for cd in cds:
                p = prog.get(cd["id"], {})
                estado = p.get("estado", "no_intentado")
                cd_total += 1
                if estado == "dominado":
                    cd_dominados += 1
                filas.append({
                    "texto": cd.get("texto", cd["id"]),
                    "estado": estado,
                    "simbolo": simbolo.get(estado, "○"),
                    "ultima_sesion": p.get("ultima_sesion") if estado == "dominado" else None,
                })
            dom = sum(1 for f in filas if f["estado"] == "dominado")
            unidades.append({
                "id": u["id"], "nombre": u.get("nombre", ""),
                "can_dos": filas, "n_dominados": dom, "n_total": len(filas),
                "pct": round(dom * 100 / len(filas)) if filas else 0,
            })

        vocab_jp, gram_jp = set(), set()
        for u in CURRICULUM:
            for e in u.get("items", []):
                jp = str(e.get("jp") or "").strip()
                if not jp:
                    continue
                if e.get("kind") == "gramatica":
                    gram_jp.add(jp)
                elif e.get("kind") == "vocabulario" and e.get("tipo") != "kanji":
                    vocab_jp.add(jp)
        # ponytail: una consulta por ítem (≈800), igual que la página de temario.
        # Página de solo lectura y poco tráfico; el batch (estado_items_bulk) se
        # aparca para la Fase 18 (limpieza), es más que el alcance de la Fase 14.
        vocab_sabido = sum(1 for jp in vocab_jp
                           if self.estado_item(jp, "vocabulario") == "sabido")
        gram_sabido = sum(1 for jp in gram_jp
                          if self.estado_item(jp, "gramatica") == "sabido")

        perfil = self.resumen_perfil()

        def pct(n, d):
            return round(n * 100 / d) if d else 0

        return {
            "unidades": unidades,
            "kanji_unidades": kanji_unidades,
            "candos_total": cd_total,
            "candos_dominados": cd_dominados,
            "candos_pct": pct(cd_dominados, cd_total),
            "vocab_sabido": vocab_sabido,
            "vocab_total": len(vocab_jp),
            "vocab_pct": pct(vocab_sabido, len(vocab_jp)),
            "gram_sabido": gram_sabido,
            "gram_total": len(gram_jp),
            "gram_pct": pct(gram_sabido, len(gram_jp)),
            "weak_points": perfil["weak_points"],
            "weak_grammar": perfil["weak_grammar"],
        }

    def get_practiced_set(self, kind: str = "kanji") -> set:
        """Conjunto de textos (jp) que ya tienen ficha SRS en la BD."""
        if kind == "vocabulario":
            table, col = "japanese_vocabulary", "word"
        elif kind == "kanji":
            table, col = "japanese_kanji", "kanji"
        else:
            table, col = "japanese_grammar", "grammar_point"
        with self._conectar() as conn:
            return {row[0] for row in conn.execute(f"SELECT {col} FROM {table}")}

    def get_item_id(self, jp: str, kind: str = "vocabulario"):
        """Devuelve el id de un ítem por su texto en japonés, o None si no existe."""
        if kind == "vocabulario":
            table, col = "japanese_vocabulary", "word"
        elif kind == "kanji":
            table, col = "japanese_kanji", "kanji"
        else:
            table, col = "japanese_grammar", "grammar_point"
        with self._conectar() as conn:
            row = conn.execute(
                f"SELECT id FROM {table} WHERE {col} = ?", (jp,)
            ).fetchone()
        return row[0] if row else None

    def guardar_resumen_sesion(self, session_id, summary, words_learned=0,
                               grammar_practiced="", errors_noted=""):
        """Actualiza el resumen de una sesión al cerrarla."""
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                """UPDATE japanese_sessions SET
                       ended_at = ?, summary = ?,
                       words_learned = ?, grammar_practiced = ?, errors_noted = ?
                   WHERE id = ?""",
                (now, summary, words_learned, grammar_practiced, errors_noted, session_id),
            )

    def guardar_episodios(self, session_id, episodios: list):
        """Guarda lo que Laura contó de su vida en la sesión (memoria episódica)."""
        episodios = [e.strip() for e in (episodios or []) if e and e.strip()]
        if not episodios:
            return
        with self._conectar() as conn:
            conn.executemany(
                "INSERT INTO laura_episodios (session_id, episodio) VALUES (?, ?)",
                [(session_id, e) for e in episodios],
            )

    def guardar_anecdotas_kaito(self, session_id, anecdotas: list):
        """Guarda lo que Kaito ha afirmado sobre sí mismo, para no contradecirse."""
        anecdotas = [a.strip() for a in (anecdotas or []) if a and a.strip()]
        if not anecdotas:
            return
        with self._conectar() as conn:
            conn.executemany(
                "INSERT INTO kaito_anecdotas (session_id, anecdota) VALUES (?, ?)",
                [(session_id, a) for a in anecdotas],
            )

    def resumen_perfil(self) -> dict:
        """Versión ligera de obtener_perfil_completo para el orquestador."""
        with self._conectar() as conn:
            vocab_counts = conn.execute(
                """SELECT status, COUNT(*) FROM japanese_vocabulary GROUP BY status"""
            ).fetchall()
            due_count = (
                conn.execute(
                    "SELECT COUNT(*) FROM japanese_vocabulary WHERE next_review <= date('now')"
                ).fetchone()[0]
                + conn.execute(
                    "SELECT COUNT(*) FROM japanese_grammar WHERE next_review <= date('now')"
                ).fetchone()[0]
                + conn.execute(
                    "SELECT COUNT(*) FROM japanese_kanji WHERE next_review <= date('now')"
                ).fetchone()[0]
            )
            last_sessions = conn.execute(
                """SELECT summary FROM japanese_sessions
                   WHERE summary IS NOT NULL ORDER BY started_at DESC LIMIT 3"""
            ).fetchall()
            episodios = conn.execute(
                "SELECT episodio FROM laura_episodios ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
            anecdotas_kaito = conn.execute(
                "SELECT anecdota FROM kaito_anecdotas ORDER BY created_at DESC LIMIT 8"
            ).fetchall()
            # Errores que el profesor decidió no comentar en su momento: se
            # arrastran a la sesión siguiente en vez de perderse.
            sin_corregir = conn.execute(
                """SELECT errors_noted FROM japanese_sessions
                   WHERE errors_noted IS NOT NULL AND errors_noted != ''
                   ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
            weak = conn.execute(
                "SELECT word, errors FROM japanese_vocabulary "
                "WHERE times_reviewed >= 3 AND CAST(errors AS REAL) / times_reviewed > 0.4 "
                "ORDER BY CAST(errors AS REAL) / times_reviewed DESC LIMIT 5"
            ).fetchall()
            weak_gram = conn.execute(
                "SELECT grammar_point, errors FROM japanese_grammar "
                "WHERE times_seen >= 3 AND CAST(errors AS REAL) / times_seen > 0.4 "
                "ORDER BY CAST(errors AS REAL) / times_seen DESC LIMIT 5"
            ).fetchall()

        return {
            "vocab_by_status": dict(vocab_counts),
            "due_count": due_count,
            "last_sessions": [s for (s,) in last_sessions],
            # compat: el resumen más reciente solo, para quien aún lee esta clave.
            "last_session_summary": last_sessions[0][0] if last_sessions else None,
            "episodios_laura": [e for (e,) in episodios],
            "anecdotas_kaito": [a for (a,) in anecdotas_kaito],
            "sin_corregir": sin_corregir[0] if sin_corregir else None,
            "weak_points": [{"word": w, "errors": e} for w, e in weak],
            "weak_grammar": [{"punto": g, "errors": e} for g, e in weak_gram],
        }

    # ── Perfil para el agente general ───────────────────────────────────────
    # `obtener_perfil_completo` sigue en uso: lo llama el agente general de
    # brain.py (flujo `consultar_progreso`), que es independiente del modo
    # sensei. El orquestador sensei usa `resumen_perfil()` en su lugar.

    def obtener_perfil_completo(self) -> str:
        """Genera el perfil actual de Laura para el prompt del profesor."""
        with self._conectar() as conn:
            vocab_count = conn.execute(
                "SELECT COUNT(*) FROM japanese_vocabulary WHERE status IN ('learned','mastered')"
            ).fetchone()[0]
            grammar = conn.execute(
                "SELECT grammar_point, mastery FROM japanese_grammar ORDER BY mastery DESC"
            ).fetchall()
            errors = conn.execute(
                "SELECT word, errors FROM japanese_vocabulary "
                "WHERE times_reviewed >= 3 AND CAST(errors AS REAL) / times_reviewed > 0.4 "
                "ORDER BY CAST(errors AS REAL) / times_reviewed DESC LIMIT 5"
            ).fetchall()

        perfil = "=== PERFIL ACTUAL DE LAURA (JAPONÉS) ===\n"
        perfil += f"Palabras dominadas: {vocab_count}\n"
        perfil += "Gramática:\n"
        for g, m in grammar:
            perfil += f"- {g}: {m:.0f}% dominio\n"
        if errors:
            perfil += "Puntos débiles:\n"
            for w, e in errors:
                perfil += f"- {w}: {e} errores\n"
        perfil += "\nInstrucciones:\n"
        perfil += "- No enseñes vocabulario ya dominado.\n"
        perfil += "- Refuerza las estructuras con errores frecuentes.\n"
        return perfil
