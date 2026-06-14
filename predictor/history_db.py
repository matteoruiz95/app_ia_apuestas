from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "analisis_historico.sqlite"


def get_db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def _connect() -> sqlite3.Connection:
    path = get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_history_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_run_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                match_key TEXT NOT NULL,
                match_no INTEGER,
                group_name TEXT,
                home TEXT,
                away TEXT,
                date_col TEXT,
                time_col TEXT,
                analysis_status TEXT,
                ai_analyzed_at TEXT,
                prediction TEXT,
                prediction_probability REAL,
                ai_bet_conclusion TEXT,
                favorite_conclusion TEXT,
                summary TEXT,
                row_json TEXT NOT NULL
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_match_no ON analysis_history(match_no)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_saved_at ON analysis_history(saved_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_match_key ON analysis_history(match_key)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_run_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                history_id INTEGER,
                match_no INTEGER,
                match_key TEXT,
                group_name TEXT,
                home TEXT,
                away TEXT,
                actual_home_goals INTEGER NOT NULL,
                actual_away_goals INTEGER NOT NULL,
                actual_total_goals INTEGER NOT NULL,
                actual_result TEXT NOT NULL,
                actual_score TEXT NOT NULL,
                prediction TEXT,
                expected_result TEXT,
                ai_bet_market TEXT,
                ai_bet_selection TEXT,
                ai_bet_vs_favorite TEXT,
                favorite_team TEXT,
                favorite_side TEXT,
                winner_correct INTEGER,
                expected_score_correct INTEGER,
                expected_total_goals_close INTEGER,
                goal_market_correct INTEGER,
                ai_bet_correct INTEGER,
                ai_bet_vs_favorite_correct INTEGER,
                favorite_direct_correct INTEGER,
                favorite_double_chance_correct INTEGER,
                notes TEXT,
                evaluation_json TEXT NOT NULL
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_evaluations_match_no ON analysis_evaluations(match_no)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_evaluations_history_id ON analysis_evaluations(history_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_evaluations_saved_at ON analysis_evaluations(saved_at)"
        )


def _jsonable(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        return value

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]

    try:
        return value.item()
    except Exception:
        pass

    return str(value)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or pd.isna(value):
            return None
        return int(float(value))
    except Exception:
        return None


def _match_key(row: dict[str, Any]) -> str:
    match_no = _safe_int(row.get("match_no"))

    if match_no is not None:
        return f"match_no:{match_no}"

    group = str(row.get("group") or "").strip()
    home = str(row.get("home") or "").strip()
    away = str(row.get("away") or "").strip()
    date_col = str(row.get("date_col") or "").strip()
    time_col = str(row.get("time_col") or "").strip()

    return f"{group}|{home}|{away}|{date_col}|{time_col}".lower()


def _row_to_json(row: dict[str, Any]) -> str:
    payload = {str(k): _jsonable(v) for k, v in row.items()}
    return json.dumps(payload, ensure_ascii=False)


def _from_row_json(row_json: str) -> dict[str, Any]:
    try:
        data = json.loads(row_json or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _clean_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).duplicated()]
    return df


def save_analysis_history(
    df: pd.DataFrame | None,
    selected_match_nos: Iterable[int] | None = None,
    source: str = "streamlit",
) -> int:
    """
    Guarda en SQLite los partidos procesados en la última ejecución.

    Guarda una fila por cada partido seleccionado que tenga ai_attempted=True
    o analysis_status distinto de BASE/RUNNING.
    """
    ensure_history_db()

    df = _clean_dataframe(df)

    if df.empty:
        return 0

    if selected_match_nos:
        selected = {_safe_int(x) for x in selected_match_nos}
        selected.discard(None)
        if "match_no" in df.columns:
            df = df[df["match_no"].apply(_safe_int).isin(selected)].copy()

    if df.empty:
        return 0

    mask = pd.Series([True] * len(df), index=df.index)

    if "ai_attempted" in df.columns:
        attempted = df["ai_attempted"].fillna(False).astype(bool)
        mask = mask & attempted

    if "analysis_status" in df.columns:
        status = df["analysis_status"].fillna("").astype(str).str.upper()
        mask = mask & ~status.isin(["", "BASE", "RUNNING"])

    df = df[mask].copy()

    if df.empty:
        return 0

    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis_run_id = f"{saved_at}_{uuid.uuid4().hex[:8]}"

    rows_to_insert = []

    for _, series in df.iterrows():
        row = series.to_dict()
        row_json = _row_to_json(row)

        rows_to_insert.append(
            (
                analysis_run_id,
                saved_at,
                _match_key(row),
                _safe_int(row.get("match_no")),
                _jsonable(row.get("group")),
                _jsonable(row.get("home")),
                _jsonable(row.get("away")),
                _jsonable(row.get("date_col")),
                _jsonable(row.get("time_col")),
                _jsonable(row.get("analysis_status")),
                _jsonable(row.get("ai_analyzed_at")),
                _jsonable(row.get("prediction")),
                _safe_float(row.get("prediction_probability")),
                _jsonable(row.get("ai_bet_conclusion")),
                _jsonable(row.get("favorite_conclusion")),
                _jsonable(row.get("summary")),
                row_json,
            )
        )

    with _connect() as conn:
        conn.executemany(
            """
            INSERT INTO analysis_history (
                analysis_run_id, saved_at, match_key, match_no, group_name,
                home, away, date_col, time_col, analysis_status, ai_analyzed_at,
                prediction, prediction_probability, ai_bet_conclusion,
                favorite_conclusion, summary, row_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

    return len(rows_to_insert)


def history_existing_match_nos(match_nos: Iterable[int] | None) -> list[int]:
    ensure_history_db()

    if not match_nos:
        return []

    cleaned = sorted({_safe_int(x) for x in match_nos if _safe_int(x) is not None})

    if not cleaned:
        return []

    placeholders = ",".join(["?"] * len(cleaned))

    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT DISTINCT match_no
            FROM analysis_history
            WHERE match_no IN ({placeholders})
            ORDER BY match_no
            """,
            cleaned,
        ).fetchall()

    return [int(row["match_no"]) for row in rows if row["match_no"] is not None]


def read_analysis_history(limit: int | None = 1000) -> pd.DataFrame:
    ensure_history_db()

    sql = """
        SELECT *
        FROM analysis_history
        ORDER BY id DESC
    """

    params: list[Any] = []

    if limit is not None and int(limit) > 0:
        sql += " LIMIT ?"
        params.append(int(limit))

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    records: list[dict[str, Any]] = []

    for row in rows:
        base = dict(row)
        row_json = base.pop("row_json", "{}")
        payload = _from_row_json(row_json)

        record = {}
        record.update(payload)
        record["history_id"] = base.get("id")
        record["history_saved_at"] = base.get("saved_at")
        record["history_analysis_run_id"] = base.get("analysis_run_id")
        record["history_match_key"] = base.get("match_key")

        records.append(record)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def latest_analysis_history() -> pd.DataFrame:
    """
    Devuelve solo el último análisis guardado por match_no.
    """
    history = read_analysis_history(limit=None)

    if history.empty:
        return history

    if "history_id" not in history.columns:
        return history

    history = history.copy()
    history["history_id"] = pd.to_numeric(history["history_id"], errors="coerce")
    history = history.sort_values("history_id", ascending=False)

    if "match_no" in history.columns:
        history["_match_no_int"] = history["match_no"].apply(_safe_int)
        latest = history.drop_duplicates("_match_no_int", keep="first").drop(columns=["_match_no_int"])
        return latest.reset_index(drop=True)

    return history


def merge_latest_history_into_df(df: pd.DataFrame | None) -> pd.DataFrame:
    """
    Carga el último histórico en la tabla actual de la app.
    """
    current = _clean_dataframe(df)
    latest = latest_analysis_history()

    if current.empty or latest.empty or "match_no" not in current.columns or "match_no" not in latest.columns:
        return current

    current = current.copy()

    for _, row in latest.iterrows():
        match_no = _safe_int(row.get("match_no"))
        if match_no is None:
            continue

        idxs = current.index[current["match_no"].apply(_safe_int) == match_no].tolist()
        if not idxs:
            continue

        idx = idxs[0]

        for col, value in row.items():
            if col not in current.columns:
                current[col] = pd.Series([None] * len(current), index=current.index, dtype="object")

            current.at[idx, col] = value

    return current


def clear_analysis_history() -> None:
    ensure_history_db()

    with _connect() as conn:
        conn.execute("DELETE FROM analysis_history")


def history_count() -> int:
    ensure_history_db()

    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM analysis_history").fetchone()

    return int(row["total"] or 0)


# ============================================================
# Evaluación de aciertos contra resultados reales
# ============================================================

def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def _normalize_result(value: Any) -> str:
    text = _safe_text(value).lower()

    if text in ["local", "home", "1", "gana local"]:
        return "local"

    if text in ["visitante", "away", "2", "gana visitante"]:
        return "visitante"

    if text in ["empate", "draw", "x"]:
        return "empate"

    if "local" in text:
        return "local"

    if "visitante" in text:
        return "visitante"

    if "empate" in text:
        return "empate"

    return text


def _bool_to_int(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def _infer_favorite_side(row: dict[str, Any]) -> str:
    favorite_side = _safe_text(row.get("favorite_side")).lower()

    if favorite_side in ["local", "visitante"]:
        return favorite_side

    favorite_team = _safe_text(row.get("favorite_team")).lower()
    home = _safe_text(row.get("home")).lower()
    away = _safe_text(row.get("away")).lower()

    if favorite_team and favorite_team == home:
        return "local"

    if favorite_team and favorite_team == away:
        return "visitante"

    # Fallback por probabilidades
    home_prob = _safe_float(row.get("prob_home_ai")) or _safe_float(row.get("prob_home_final")) or 0
    away_prob = _safe_float(row.get("prob_away_ai")) or _safe_float(row.get("prob_away_final")) or 0

    if home_prob > away_prob:
        return "local"

    if away_prob > home_prob:
        return "visitante"

    return ""


def _actual_result(home_goals: int, away_goals: int) -> str:
    if int(home_goals) > int(away_goals):
        return "local"

    if int(away_goals) > int(home_goals):
        return "visitante"

    return "empate"


def _selection_won(selection: str, market: str, actual_result: str, actual_total_goals: int) -> bool | None:
    selection_l = _safe_text(selection).lower()
    market_l = _safe_text(market).lower()

    if not selection_l or selection_l in ["no apostar", "sin apuesta"]:
        return None

    if "sin apuesta" in market_l:
        return None

    # Resultado final 1X2
    if "gana local" in selection_l or selection_l == "local":
        return actual_result == "local"

    if "gana visitante" in selection_l or selection_l == "visitante":
        return actual_result == "visitante"

    if "empate" == selection_l or selection_l.startswith("empate"):
        return actual_result == "empate"

    # Doble oportunidad
    if "local o empate" in selection_l or "1x" in selection_l:
        return actual_result in ["local", "empate"]

    if "visitante o empate" in selection_l or "x2" in selection_l:
        return actual_result in ["visitante", "empate"]

    if "local o visitante" in selection_l or selection_l == "12":
        return actual_result in ["local", "visitante"]

    # Total goles
    if "más de 0.5" in selection_l or "mas de 0.5" in selection_l:
        return actual_total_goals > 0.5

    if "más de 1.5" in selection_l or "mas de 1.5" in selection_l:
        return actual_total_goals > 1.5

    if "más de 2.5" in selection_l or "mas de 2.5" in selection_l:
        return actual_total_goals > 2.5

    if "más de 3.5" in selection_l or "mas de 3.5" in selection_l:
        return actual_total_goals > 3.5

    return None


def _goal_market_correct(selection: str, market: str, actual_total_goals: int) -> bool | None:
    market_l = _safe_text(market).lower()
    selection_l = _safe_text(selection).lower()

    if "gol" not in market_l and "gol" not in selection_l:
        return None

    return _selection_won(selection, market, "empate", actual_total_goals)


def _ai_bet_vs_favorite_correct(
    ai_bet_vs_favorite: str,
    favorite_side: str,
    ai_bet_market: str,
    ai_bet_selection: str,
    actual_result: str,
    actual_total_goals: int,
) -> bool | None:
    text = _safe_text(ai_bet_vs_favorite).lower()

    if not text:
        return None

    if "no apuesta" in text or "no apostar" in text:
        return None

    if not favorite_side:
        return None

    if "favorito directo" in text:
        return actual_result == favorite_side

    if "gana o empata favorito" in text:
        return actual_result in [favorite_side, "empate"]

    if "prefiere mercado de goles" in text:
        return _selection_won(ai_bet_selection, ai_bet_market, actual_result, actual_total_goals)

    # Si dice que evita favorito directo, lo evaluamos con la apuesta real.
    return _selection_won(ai_bet_selection, ai_bet_market, actual_result, actual_total_goals)


def calculate_evaluation(
    analysis_row: dict[str, Any],
    actual_home_goals: int,
    actual_away_goals: int,
    notes: str = "",
) -> dict[str, Any]:
    """
    Calcula si el análisis fue acertado contra el resultado real.
    """
    actual_home_goals = int(actual_home_goals)
    actual_away_goals = int(actual_away_goals)
    actual_total_goals = actual_home_goals + actual_away_goals
    actual_result = _actual_result(actual_home_goals, actual_away_goals)
    actual_score = f"{actual_home_goals}-{actual_away_goals}"

    prediction = _normalize_result(
        analysis_row.get("prediction") or analysis_row.get("ai_prediction")
    )

    winner_correct = None
    if prediction in ["local", "empate", "visitante"]:
        winner_correct = prediction == actual_result

    expected_result = _safe_text(analysis_row.get("expected_result")).replace(" ", "")
    expected_score_correct = None
    if expected_result:
        expected_score_correct = expected_result == actual_score

    expected_total = _safe_float(analysis_row.get("expected_total_goals_ai"))
    expected_total_goals_close = None
    if expected_total is not None:
        # Criterio tolerante: el total real quedó a máximo 0.75 goles del promedio esperado.
        expected_total_goals_close = abs(float(actual_total_goals) - float(expected_total)) <= 0.75

    ai_bet_market = _safe_text(analysis_row.get("ai_bet_market"))
    ai_bet_selection = _safe_text(analysis_row.get("ai_bet_selection"))
    ai_bet_vs_favorite = _safe_text(analysis_row.get("ai_bet_vs_favorite"))
    favorite_side = _infer_favorite_side(analysis_row)

    ai_bet_correct = _selection_won(
        ai_bet_selection,
        ai_bet_market,
        actual_result,
        actual_total_goals,
    )

    goal_market_correct = _goal_market_correct(
        ai_bet_selection,
        ai_bet_market,
        actual_total_goals,
    )

    ai_bet_vs_favorite_correct = _ai_bet_vs_favorite_correct(
        ai_bet_vs_favorite,
        favorite_side,
        ai_bet_market,
        ai_bet_selection,
        actual_result,
        actual_total_goals,
    )

    favorite_direct_correct = None
    favorite_double_chance_correct = None

    if favorite_side in ["local", "visitante"]:
        favorite_direct_correct = actual_result == favorite_side
        favorite_double_chance_correct = actual_result in [favorite_side, "empate"]

    evaluation = {
        "history_id": _safe_int(analysis_row.get("history_id")),
        "match_no": _safe_int(analysis_row.get("match_no")),
        "match_key": _safe_text(analysis_row.get("history_match_key") or _match_key(analysis_row)),
        "group": _safe_text(analysis_row.get("group")),
        "home": _safe_text(analysis_row.get("home")),
        "away": _safe_text(analysis_row.get("away")),
        "actual_home_goals": actual_home_goals,
        "actual_away_goals": actual_away_goals,
        "actual_total_goals": actual_total_goals,
        "actual_result": actual_result,
        "actual_score": actual_score,
        "prediction": prediction,
        "expected_result": expected_result,
        "ai_bet_market": ai_bet_market,
        "ai_bet_selection": ai_bet_selection,
        "ai_bet_vs_favorite": ai_bet_vs_favorite,
        "favorite_team": _safe_text(analysis_row.get("favorite_team")),
        "favorite_side": favorite_side,
        "winner_correct": winner_correct,
        "expected_score_correct": expected_score_correct,
        "expected_total_goals_close": expected_total_goals_close,
        "goal_market_correct": goal_market_correct,
        "ai_bet_correct": ai_bet_correct,
        "ai_bet_vs_favorite_correct": ai_bet_vs_favorite_correct,
        "favorite_direct_correct": favorite_direct_correct,
        "favorite_double_chance_correct": favorite_double_chance_correct,
        "notes": _safe_text(notes),
    }

    return evaluation


def save_analysis_evaluation(
    analysis_row: dict[str, Any],
    actual_home_goals: int,
    actual_away_goals: int,
    notes: str = "",
) -> int:
    ensure_history_db()

    evaluation = calculate_evaluation(
        analysis_row=analysis_row,
        actual_home_goals=actual_home_goals,
        actual_away_goals=actual_away_goals,
        notes=notes,
    )

    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evaluation_run_id = f"{saved_at}_{uuid.uuid4().hex[:8]}"
    evaluation_json = json.dumps({str(k): _jsonable(v) for k, v in evaluation.items()}, ensure_ascii=False)

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_evaluations (
                evaluation_run_id, saved_at, history_id, match_no, match_key,
                group_name, home, away, actual_home_goals, actual_away_goals,
                actual_total_goals, actual_result, actual_score,
                prediction, expected_result, ai_bet_market, ai_bet_selection,
                ai_bet_vs_favorite, favorite_team, favorite_side,
                winner_correct, expected_score_correct, expected_total_goals_close,
                goal_market_correct, ai_bet_correct, ai_bet_vs_favorite_correct,
                favorite_direct_correct, favorite_double_chance_correct,
                notes, evaluation_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_run_id,
                saved_at,
                evaluation.get("history_id"),
                evaluation.get("match_no"),
                evaluation.get("match_key"),
                evaluation.get("group"),
                evaluation.get("home"),
                evaluation.get("away"),
                evaluation.get("actual_home_goals"),
                evaluation.get("actual_away_goals"),
                evaluation.get("actual_total_goals"),
                evaluation.get("actual_result"),
                evaluation.get("actual_score"),
                evaluation.get("prediction"),
                evaluation.get("expected_result"),
                evaluation.get("ai_bet_market"),
                evaluation.get("ai_bet_selection"),
                evaluation.get("ai_bet_vs_favorite"),
                evaluation.get("favorite_team"),
                evaluation.get("favorite_side"),
                _bool_to_int(evaluation.get("winner_correct")),
                _bool_to_int(evaluation.get("expected_score_correct")),
                _bool_to_int(evaluation.get("expected_total_goals_close")),
                _bool_to_int(evaluation.get("goal_market_correct")),
                _bool_to_int(evaluation.get("ai_bet_correct")),
                _bool_to_int(evaluation.get("ai_bet_vs_favorite_correct")),
                _bool_to_int(evaluation.get("favorite_direct_correct")),
                _bool_to_int(evaluation.get("favorite_double_chance_correct")),
                evaluation.get("notes"),
                evaluation_json,
            ),
        )

        return int(cursor.lastrowid)


def read_analysis_evaluations(limit: int | None = None) -> pd.DataFrame:
    ensure_history_db()

    sql = """
        SELECT *
        FROM analysis_evaluations
        ORDER BY id DESC
    """

    params: list[Any] = []

    if limit is not None and int(limit) > 0:
        sql += " LIMIT ?"
        params.append(int(limit))

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    records: list[dict[str, Any]] = []

    for row in rows:
        base = dict(row)
        evaluation_json = base.pop("evaluation_json", "{}")
        payload = _from_row_json(evaluation_json)
        record = {}
        record.update(payload)
        record["evaluation_id"] = base.get("id")
        record["evaluation_saved_at"] = base.get("saved_at")
        record["evaluation_run_id"] = base.get("evaluation_run_id")

        # Garantizar columnas principales aunque no estén en JSON.
        for key, value in base.items():
            if key not in record:
                record[key] = value

        records.append(record)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def evaluation_count() -> int:
    ensure_history_db()

    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM analysis_evaluations").fetchone()

    return int(row["total"] or 0)


def clear_analysis_evaluations() -> None:
    ensure_history_db()

    with _connect() as conn:
        conn.execute("DELETE FROM analysis_evaluations")
