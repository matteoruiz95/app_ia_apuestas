from __future__ import annotations

import numpy as np
import pandas as pd


def confidence_label(prob: float) -> str:
    try:
        prob = float(prob)
    except Exception:
        return "Sin dato"
    if prob >= 0.80:
        return "Muy alta"
    if prob >= 0.70:
        return "Alta"
    if prob >= 0.60:
        return "Media"
    return "Baja"


def risk_label(prob: float, draw_prob: float, margin: float) -> str:
    try:
        prob = float(prob)
        draw_prob = float(draw_prob)
        margin = float(margin)
    except Exception:
        return "Sin dato"
    if prob >= 0.78 and draw_prob < 0.17 and margin <= 0.12:
        return "Bajo"
    if prob >= 0.65 and draw_prob < 0.24:
        return "Medio"
    return "Alto"


def normalize_probs(home: float, draw: float, away: float) -> tuple[float, float, float]:
    values = np.array([home, draw, away], dtype=float)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    values = np.clip(values, 0.0, None)
    total = float(values.sum())
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    values = values / total
    return float(values[0]), float(values[1]), float(values[2])


def ensure_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Une columnas duplicadas tomando el último valor no vacío."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    if not df.columns.duplicated().any():
        return df.copy()

    result = pd.DataFrame(index=df.index)
    for col in pd.unique(df.columns):
        subset = df.loc[:, df.columns == col]
        if subset.shape[1] == 1:
            result[str(col)] = subset.iloc[:, 0]
        else:
            # La columna más a la derecha suele ser la generada más recientemente por IA.
            result[str(col)] = subset.iloc[:, ::-1].bfill(axis=1).iloc[:, 0]
    return result


def _drop_existing(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Elimina columnas calculadas antes de recalcular, evitando duplicados."""
    df = ensure_unique_columns(df)
    return df.drop(columns=[c for c in columns if c in df.columns], errors="ignore")


def add_market_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_unique_columns(df).copy()

    market_cols = [
        "prob_home_raw", "prob_draw_raw", "prob_away_raw", "overround", "bookmaker_margin",
        "prob_home_market", "prob_draw_market", "prob_away_market", "market_favorite",
        "favorite_odds", "favorite_market_prob", "market_confidence", "market_risk",
    ]
    df = _drop_existing(df, market_cols)

    df["home_odds"] = pd.to_numeric(df["home_odds"], errors="coerce")
    df["draw_odds"] = pd.to_numeric(df["draw_odds"], errors="coerce")
    df["away_odds"] = pd.to_numeric(df["away_odds"], errors="coerce")

    df["prob_home_raw"] = 1 / df["home_odds"]
    df["prob_draw_raw"] = 1 / df["draw_odds"]
    df["prob_away_raw"] = 1 / df["away_odds"]
    df["overround"] = df["prob_home_raw"] + df["prob_draw_raw"] + df["prob_away_raw"]
    df["bookmaker_margin"] = df["overround"] - 1
    df["prob_home_market"] = df["prob_home_raw"] / df["overround"]
    df["prob_draw_market"] = df["prob_draw_raw"] / df["overround"]
    df["prob_away_market"] = df["prob_away_raw"] / df["overround"]

    favorites: list[str] = []
    favorite_probs: list[float] = []
    favorite_odds: list[float] = []

    for _, row in df.iterrows():
        candidates = {
            str(row["home"]): (row["home_odds"], row["prob_home_market"]),
            "Empate": (row["draw_odds"], row["prob_draw_market"]),
            str(row["away"]): (row["away_odds"], row["prob_away_market"]),
        }
        fav = min(candidates, key=lambda k: candidates[k][0])
        favorites.append(fav)
        favorite_odds.append(float(candidates[fav][0]))
        favorite_probs.append(float(candidates[fav][1]))

    df["market_favorite"] = favorites
    df["favorite_odds"] = favorite_odds
    df["favorite_market_prob"] = favorite_probs
    df["market_confidence"] = df["favorite_market_prob"].apply(confidence_label)
    df["market_risk"] = df.apply(
        lambda r: risk_label(r["favorite_market_prob"], r["prob_draw_market"], r["bookmaker_margin"]),
        axis=1,
    )
    return ensure_unique_columns(df)


def final_prediction(row: pd.Series, market_weight: float = 0.70, ai_weight: float = 0.30) -> dict:
    """Combina probabilidad de mercado + probabilidad IA. Si no hay IA, usa mercado."""
    mh, md, ma = float(row["prob_home_market"]), float(row["prob_draw_market"]), float(row["prob_away_market"])
    ah, ad, aa = row.get("prob_home_ai", np.nan), row.get("prob_draw_ai", np.nan), row.get("prob_away_ai", np.nan)

    has_ai = pd.notna(ah) and pd.notna(ad) and pd.notna(aa)
    if not has_ai:
        fh, fd, fa = mh, md, ma
    else:
        ah, ad, aa = normalize_probs(float(ah), float(ad), float(aa))
        total_weight = market_weight + ai_weight
        if total_weight <= 0:
            market_weight, ai_weight, total_weight = 0.70, 0.30, 1.0
        mw = market_weight / total_weight
        aw = ai_weight / total_weight
        fh = mw * mh + aw * ah
        fd = mw * md + aw * ad
        fa = mw * ma + aw * aa
        fh, fd, fa = normalize_probs(fh, fd, fa)

    probs = {str(row["home"]): fh, "Empate": fd, str(row["away"]): fa}
    prediction = max(probs, key=probs.get)
    probability = float(probs[prediction])
    return {
        "prob_home_final": fh,
        "prob_draw_final": fd,
        "prob_away_final": fa,
        "prediction": prediction,
        "prediction_probability": probability,
        "confidence": confidence_label(probability),
        "risk": risk_label(probability, fd, row["bookmaker_margin"]),
    }


def add_final_predictions(df: pd.DataFrame, market_weight: float = 0.70, ai_weight: float = 0.30) -> pd.DataFrame:
    df = ensure_unique_columns(df).copy()
    final_cols = [
        "prob_home_final", "prob_draw_final", "prob_away_final", "prediction",
        "prediction_probability", "confidence", "risk",
    ]
    df = _drop_existing(df, final_cols)
    preds = df.apply(lambda r: final_prediction(r, market_weight, ai_weight), axis=1, result_type="expand")
    out = pd.concat([df, preds], axis=1)
    return ensure_unique_columns(out)


def _bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    """Convierte columnas booleanas mixtas/duplicadas a máscara segura."""
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    series = df[col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return series.fillna(False).map(lambda x: str(x).strip().lower() in {"true", "1", "yes", "si", "sí", "ok"})


def analyzed_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve solo partidos analizados con IA exitosamente."""
    df = ensure_unique_columns(df)
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    if "ai_analyzed" not in df.columns:
        return df.iloc[0:0].copy()
    mask = _bool_series(df, "ai_analyzed")
    return df.loc[mask].copy()


def processed_subset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve partidos procesados por IA, incluyendo OK y ERROR.
    Esto permite ver errores cuando la API/modelo falla.
    """
    df = ensure_unique_columns(df)
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    if "ai_attempted" in df.columns:
        mask = _bool_series(df, "ai_attempted")
        return df.loc[mask].copy()
    if "analysis_status" in df.columns:
        status = df["analysis_status"]
        if isinstance(status, pd.DataFrame):
            status = status.iloc[:, 0]
        mask = status.fillna("").astype(str).str.upper().isin(["OK", "ERROR"])
        return df.loc[mask].copy()
    return analyzed_subset(df)


def display_scope(df: pd.DataFrame, only_analyzed: bool = False) -> pd.DataFrame:
    df = ensure_unique_columns(df)
    if only_analyzed:
        subset = processed_subset(df)
        if not subset.empty:
            return subset
    return df.copy()


def monte_carlo(df: pd.DataFrame, n: int = 10000, seed: int = 42) -> pd.DataFrame:
    df = ensure_unique_columns(df).copy()
    if df.empty:
        return pd.DataFrame()

    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(int(n)):
        wins_favorite = 0
        wins_prediction = 0
        for _, row in df.iterrows():
            outcomes = [str(row["home"]), "Empate", str(row["away"])]
            probs = [float(row["prob_home_final"]), float(row["prob_draw_final"]), float(row["prob_away_final"])]
            probs = normalize_probs(*probs)
            result = rng.choice(outcomes, p=probs)
            if result == row.get("market_favorite"):
                wins_favorite += 1
            if result == row.get("prediction"):
                wins_prediction += 1
        rows.append({"favorites_won": wins_favorite, "predictions_won": wins_prediction})
    return pd.DataFrame(rows)
