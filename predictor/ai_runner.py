from __future__ import annotations

import time
from datetime import datetime
from typing import Callable, Iterable

import numpy as np
import pandas as pd

from .api_clients import ApiFootballClient, OpenAIAnalyzer, TheOddsApiClient
from .odds_math import add_final_predictions, ensure_unique_columns, normalize_probs


AI_RESULT_COLUMNS = [
    "prob_home_ai", "prob_draw_ai", "prob_away_ai", "ai_prediction", "ai_confidence",
    "risk_level", "summary", "market_reading", "team_context", "draw_risk",
    "expected_result", "expected_goals_home_ai", "expected_goals_away_ai",
    "expected_total_goals_ai", "goal_expectation_summary",
    "luck_factor", "luck_explanation",
    "entropy_score", "entropy_factor", "entropy_explanation",
    "home_team_level", "away_team_level", "home_team_level_comment", "away_team_level_comment",
    "team_level_matchup", "team_level_gap", "team_level_caution", "team_level_betting_comment",
    "clear_favorite", "favorite_side", "favorite_team", "favorite_probability",
    "favorite_margin_to_second", "favorite_strength", "favorite_conclusion",
    "favorite_double_chance_selection", "favorite_bet_recommendation", "ai_bet_vs_favorite",
    "ai_bet_market", "ai_bet_selection", "ai_bet_probability",
    "ai_bet_confidence", "ai_bet_conclusion", "ai_bet_reason",
    "prob_over_0_5_goals", "prob_over_1_5_goals", "prob_over_2_5_goals",
    "prob_double_chance_home_draw", "prob_double_chance_away_draw",
    "prob_double_chance_home_away",
    "ai_fallback_used", "ai_fallback_reason", "openai_first_error",
    "volatility_factors", "expert_factors",
    "home_official_matches_sample", "home_avg_goals_for_official",
    "home_avg_goals_against_official", "home_avg_total_goals_official",
    "home_official_competitions_sample",
    "away_official_matches_sample", "away_avg_goals_for_official",
    "away_avg_goals_against_official", "away_avg_total_goals_official",
    "away_official_competitions_sample",
    "key_factors", "red_flags", "sources_used",
    "ai_analyzed", "ai_attempted", "ai_analyzed_at", "analysis_status", "error_message",
]

AI_VALUE_COLUMNS = [
    "prob_home_ai", "prob_draw_ai", "prob_away_ai", "ai_prediction", "ai_confidence",
    "risk_level", "summary", "market_reading", "team_context", "draw_risk",
    "expected_result", "expected_goals_home_ai", "expected_goals_away_ai",
    "expected_total_goals_ai", "goal_expectation_summary",
    "luck_factor", "luck_explanation",
    "entropy_score", "entropy_factor", "entropy_explanation",
    "home_team_level", "away_team_level", "home_team_level_comment", "away_team_level_comment",
    "team_level_matchup", "team_level_gap", "team_level_caution", "team_level_betting_comment",
    "clear_favorite", "favorite_side", "favorite_team", "favorite_probability",
    "favorite_margin_to_second", "favorite_strength", "favorite_conclusion",
    "favorite_double_chance_selection", "favorite_bet_recommendation", "ai_bet_vs_favorite",
    "ai_bet_market", "ai_bet_selection", "ai_bet_probability",
    "ai_bet_confidence", "ai_bet_conclusion", "ai_bet_reason",
    "prob_over_0_5_goals", "prob_over_1_5_goals", "prob_over_2_5_goals",
    "prob_double_chance_home_draw", "prob_double_chance_away_draw",
    "prob_double_chance_home_away",
    "ai_fallback_used", "ai_fallback_reason", "openai_first_error",
    "volatility_factors", "expert_factors",
    "home_official_matches_sample", "home_avg_goals_for_official",
    "home_avg_goals_against_official", "home_avg_total_goals_official",
    "home_official_competitions_sample",
    "away_official_matches_sample", "away_avg_goals_for_official",
    "away_avg_goals_against_official", "away_avg_total_goals_official",
    "away_official_competitions_sample",
    "key_factors", "red_flags", "sources_used", "error_message",
]


def _selected_indexes(
    df: pd.DataFrame,
    selected_match_nos: Iterable[int] | None = None,
    max_matches: int = 12,
) -> list[int]:
    """Obtiene los índices que se analizarán con IA."""
    if selected_match_nos:
        selected_set = {int(x) for x in selected_match_nos}
        return df.index[df["match_no"].astype(int).isin(selected_set)].tolist()

    # Compatibilidad: si no se envía selección manual, usar los favoritos más fuertes.
    return df.sort_values("favorite_market_prob", ascending=False).index.tolist()[: int(max_matches)]


def _safe_float(value, default=np.nan):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _normalize_ai_result(result: dict) -> dict:
    """Limpia y normaliza la respuesta de IA antes de escribirla en el DataFrame."""
    result = dict(result or {})
    ph = _safe_float(result.get("prob_home_ai"))
    pd_ = _safe_float(result.get("prob_draw_ai"))
    pa = _safe_float(result.get("prob_away_ai"))

    if not np.isnan(ph) and not np.isnan(pd_) and not np.isnan(pa):
        ph, pd_, pa = normalize_probs(ph, pd_, pa)
        result["prob_home_ai"] = ph
        result["prob_draw_ai"] = pd_
        result["prob_away_ai"] = pa

    result.setdefault("summary", "Análisis IA ejecutado.")
    result.setdefault("key_factors", [])
    result.setdefault("red_flags", [])
    result.setdefault("sources_used", [])
    return result


def run_ai_analysis(
    df: pd.DataFrame,
    max_matches: int = 12,
    selected_match_nos: Iterable[int] | None = None,
    market_weight: float = 0.70,
    ai_weight: float = 0.30,
    openai_key: str | None = None,
    openai_model: str = "gpt-5-mini",
    enable_web_search: bool = True,
    api_football_key: str | None = None,
    odds_api_key: str | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> pd.DataFrame:
    """
    Ejecuta IA sobre los partidos seleccionados.

    Mejora v4:
    - Permite seleccionar partidos manualmente.
    - No duplica columnas al recalcular.
    - Marca ai_analyzed=True solo en los partidos ejecutados.
    - Conserva el resto de partidos como base, pero el Excel puede exportar solo analizados.
    """
    df = ensure_unique_columns(df).copy()

    # Garantizar columnas de estado sin duplicarlas.
    for col in AI_RESULT_COLUMNS:
        if col not in df.columns:
            if col in ["ai_analyzed", "ai_attempted"]:
                df[col] = False
            else:
                df[col] = pd.Series([None] * len(df), index=df.index, dtype="object")

    selected = _selected_indexes(df, selected_match_nos=selected_match_nos, max_matches=max_matches)
    if not selected:
        return add_final_predictions(df, market_weight=market_weight, ai_weight=ai_weight)

    analyzer = OpenAIAnalyzer(api_key=openai_key, model=openai_model, enable_web_search=enable_web_search)
    football = ApiFootballClient(api_key=api_football_key)
    odds = TheOddsApiClient(api_key=odds_api_key)

    total = len(selected)
    for count, idx in enumerate(selected, start=1):
        # Limpiar valores IA previos para que una nueva ejecución fallida no use resultados antiguos.
        for col in AI_VALUE_COLUMNS:
            if col in df.columns:
                df.at[idx, col] = None
        df.at[idx, "ai_analyzed"] = False
        df.at[idx, "ai_attempted"] = True
        df.at[idx, "ai_analyzed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx, "analysis_status"] = "RUNNING"

        row = df.loc[idx].to_dict()
        label = f"{row['home']} vs {row['away']}"
        if progress_callback:
            progress_callback(count, total, label)

        try:
            api_context = ""
            if football.enabled:
                h2h_context = football.head_to_head_context(row["home"], row["away"])
                official_context, official_stats = football.official_match_goals_context(
                    row["home"],
                    row["away"],
                    sample_size=10,
                )

                for key, value in official_stats.items():
                    if key not in df.columns:
                        df[key] = pd.Series([None] * len(df), index=df.index, dtype="object")
                    df.at[idx, key] = value
                    row[key] = value

                api_context = f"{h2h_context}\n{official_context}"
            else:
                api_context = "API-Football no configurado. No se calcularon promedios oficiales no amistosos."

            odds_context = odds.match_odds_snapshot(row["home"], row["away"]) if odds.enabled else ""
            result = analyzer.analyze_match(row, api_context=api_context, odds_context=odds_context)
            result = _normalize_ai_result(result)

            for key in AI_RESULT_COLUMNS:
                if key in result:
                    df.at[idx, key] = result[key]

            # Si el modelo devolvió otros campos, guardarlos también sin duplicar columnas.
            for key, value in result.items():
                if key not in df.columns:
                    df[key] = pd.Series([None] * len(df), index=df.index, dtype="object")
                df.at[idx, key] = value

            df.at[idx, "ai_analyzed"] = True
            df.at[idx, "ai_attempted"] = True
            df.at[idx, "ai_analyzed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[idx, "analysis_status"] = "OK"
            df.at[idx, "error_message"] = None
            time.sleep(0.2)

        except Exception as exc:
            msg = str(exc)
            df.at[idx, "summary"] = f"Error IA: {msg}"
            df.at[idx, "error_message"] = msg
            df.at[idx, "ai_confidence"] = "No ejecutado"
            df.at[idx, "risk_level"] = "No ejecutado"
            df.at[idx, "analysis_status"] = "ERROR"
            df.at[idx, "ai_analyzed"] = False
            df.at[idx, "ai_attempted"] = True

    df = add_final_predictions(df, market_weight=market_weight, ai_weight=ai_weight)
    return ensure_unique_columns(df)
