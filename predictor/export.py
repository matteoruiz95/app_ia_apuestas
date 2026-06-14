from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from .odds_math import processed_subset, ensure_unique_columns


def _safe_cell(value: Any) -> Any:
    """Convierte listas/dicts a texto para evitar errores al exportar a Excel."""
    if isinstance(value, (list, dict, tuple, set)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return value



def _map_dataframe(df: pd.DataFrame, func) -> pd.DataFrame:
    """Aplica una función celda a celda compatible con versiones nuevas y antiguas de pandas."""
    if hasattr(df, "map"):
        return df.map(func)
    return df.applymap(func)


def _safe_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    """Garantiza que siempre haya un DataFrame exportable."""
    if df is None:
        return pd.DataFrame({"Mensaje": ["No hay datos para exportar todavía."]})
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame({"Mensaje": [f"Objeto no exportable: {type(df).__name__}"]})
    df = ensure_unique_columns(df)
    if df.empty and len(df.columns) == 0:
        return pd.DataFrame({"Mensaje": ["No hay datos para exportar todavía."]})
    return _map_dataframe(df.copy(), _safe_cell)


def _percent_columns(columns) -> list[str]:
    keys = [
        "prob_", "bookmaker_margin", "favorite_market_prob", "prediction_probability",
        "ai_bet_probability", "market_prob", "ai_prob", "final_prob",
    ]
    out = []
    for c in columns:
        c_str = str(c)
        c_low = c_str.lower()
        if any(k in c_low for k in keys):
            out.append(c_str)
    return out


def to_display_percent(df: pd.DataFrame | None) -> pd.DataFrame:
    """Convierte probabilidades 0-1 a porcentajes visibles. Tolera columnas duplicadas."""
    df = _safe_dataframe(df)
    for c in _percent_columns(df.columns):
        if c in df.columns:
            try:
                series = df[c]
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                numeric = pd.to_numeric(series, errors="coerce")
                max_val = numeric.max(skipna=True)
                if pd.notna(max_val) and max_val <= 1.5 and c != "overround":
                    df[c] = (numeric * 100).round(2)
                else:
                    df[c] = numeric.round(4 if c == "overround" else 2)
            except Exception:
                df[c] = df[c].astype(str)
    return df


def _filter_export_df(df: pd.DataFrame | None, only_analyzed: bool = True) -> pd.DataFrame:
    df = _safe_dataframe(df)
    if not only_analyzed:
        return df

    processed = processed_subset(df)
    if processed is not None and isinstance(processed, pd.DataFrame) and not processed.empty:
        return processed

    return pd.DataFrame({
        "Mensaje": [
            "No hay partidos procesados con IA para exportar. Ejecuta IA sobre uno o más partidos y vuelve a descargar."
        ]
    })


def excel_bytes(
    df: pd.DataFrame | None,
    simulations: pd.DataFrame | None = None,
    only_analyzed: bool = True,
) -> bytes:
    """
    Genera un Excel robusto.

    Por defecto exporta SOLO los partidos analizados con IA.
    Si aún no hay partidos analizados, crea un Excel con mensaje claro.
    """
    output = io.BytesIO()

    raw_export_df = _filter_export_df(df, only_analyzed=only_analyzed)
    export_df = to_display_percent(raw_export_df)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Predicciones", index=False)

        ranking_cols = [
            "match_no", "date_col", "time_col", "group", "home", "away",
            "market_favorite", "prediction", "prediction_probability",
            "confidence", "risk", "favorite_odds", "favorite_market_prob",
            "home_official_matches_sample", "home_avg_goals_for_official",
            "home_avg_goals_against_official", "home_avg_total_goals_official",
            "away_official_matches_sample", "away_avg_goals_for_official",
            "away_avg_goals_against_official", "away_avg_total_goals_official",
            "ai_analyzed", "ai_attempted", "ai_analyzed_at", "analysis_status", "error_message",
            "summary", "expected_result", "expected_goals_home_ai", "expected_goals_away_ai",
            "expected_total_goals_ai", "goal_expectation_summary",
            "luck_factor", "luck_explanation",
            "entropy_score", "entropy_factor", "entropy_explanation",
            "home_team_level", "away_team_level", "team_level_matchup", "team_level_gap",
            "team_level_caution", "team_level_betting_comment",
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
            "market_reading", "team_context", "draw_risk",
            "key_factors", "red_flags", "sources_used",
        ]
        available = [c for c in ranking_cols if c in raw_export_df.columns]
        if available:
            ranking = _map_dataframe(raw_export_df[available].copy(), _safe_cell)
            if "prediction_probability" in ranking.columns:
                ranking["prediction_probability"] = pd.to_numeric(ranking["prediction_probability"], errors="coerce")
                ranking = ranking.sort_values("prediction_probability", ascending=False, na_position="last")
            ranking = to_display_percent(ranking)
        else:
            ranking = pd.DataFrame({"Mensaje": ["No hay columnas suficientes para construir el ranking."]})
        ranking.to_excel(writer, sheet_name="Ranking", index=False)

        if isinstance(simulations, pd.DataFrame) and not simulations.empty:
            _map_dataframe(simulations.copy(), _safe_cell).describe().to_excel(writer, sheet_name="Monte Carlo")
        else:
            pd.DataFrame({"Mensaje": ["Aún no has ejecutado la simulación Monte Carlo."]}).to_excel(
                writer,
                sheet_name="Monte Carlo",
                index=False,
            )

        notes = pd.DataFrame({"Notas": [
            "Este Excel exporta solo partidos procesados con IA cuando la opción está activa; incluye OK y ERROR para diagnóstico.",
            "Las predicciones son probabilísticas, no garantizan resultados.",
            "La app combina cuotas ajustadas y análisis IA cuando la API de OpenAI está configurada.",
            "Actualiza cuotas, lesiones, nóminas oficiales y noticias antes de tomar decisiones reales.",
            "Si una corrida IA falla para un partido, la app conserva el análisis base y registra el error en summary/status.",
        ]})
        notes.to_excel(writer, sheet_name="Notas", index=False)

        for sheet in writer.book.worksheets:
            sheet.sheet_state = "visible"
            for column_cells in sheet.columns:
                max_length = 0
                letter = column_cells[0].column_letter
                for cell in column_cells:
                    value = "" if cell.value is None else str(cell.value)
                    max_length = max(max_length, len(value))
                sheet.column_dimensions[letter].width = min(max_length + 2, 60)
        writer.book.active = 0

    output.seek(0)
    return output.getvalue()
