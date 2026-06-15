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
        "ai_bet_probability", "market_prob", "ai_prob", "final_prob", "favorite_probability",
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


def _get(row: pd.Series, *names: str, default: Any = "") -> Any:
    for name in names:
        if name in row.index:
            value = row.get(name)
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                return value
    return default


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.replace("%", "").replace(",", ".").strip()
        numeric = float(value)
        if numeric > 1.5:
            numeric = numeric / 100
        return numeric
    except Exception:
        return None


def _pct(value: Any) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return ""
    return f"{numeric * 100:.1f}%"


def _num(value: Any, decimals: int = 2) -> str:
    try:
        if value is None or value == "":
            return ""
        numeric = float(str(value).replace(",", "."))
        return f"{numeric:.{decimals}f}"
    except Exception:
        return ""


def _yes_no(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"true", "1", "sí", "si", "yes", "y", "claro"}:
        return "Sí"
    if text in {"false", "0", "no", "n"}:
        return "No"
    return str(value) if str(value).strip() else ""


def _normalize_level(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "alto" in text or "alta" in text or "high" in text:
        return "Alto"
    if "medio" in text or "media" in text or "medium" in text:
        return "Medio"
    if "bajo" in text or "baja" in text or "low" in text:
        return "Bajo"
    return str(value or "").strip()


def _contains_no_bet(text: Any) -> bool:
    s = str(text or "").lower()
    return any(x in s for x in ["no apostar", "no conviene", "evitar", "descartar"])


def _contains_caution(text: Any) -> bool:
    s = str(text or "").lower()
    return any(x in s for x in ["cautela", "moderad", "riesgo", "esperar", "validar", "revisar"])


def _join_text(*values: Any, max_chars: int = 900) -> str:
    parts: list[str] = []
    for value in values:
        if value is None or value == "":
            continue

        if isinstance(value, str):
            text = value.strip()
            if text.startswith("[") or text.startswith("{"):
                try:
                    parsed = json.loads(text)
                    value = parsed
                except Exception:
                    value = text

        if isinstance(value, (list, tuple, set)):
            for item in value:
                item_text = str(item).strip()
                if item_text:
                    parts.append(item_text)
        elif isinstance(value, dict):
            for k, v in value.items():
                item_text = f"{k}: {v}".strip()
                if item_text:
                    parts.append(item_text)
        else:
            text = str(value).strip()
            if text:
                parts.append(text)

    # quitar duplicados conservando orden
    seen = set()
    clean = []
    for part in parts:
        key = part.lower()
        if key not in seen:
            seen.add(key)
            clean.append(part)

    result = " | ".join(clean)
    if len(result) > max_chars:
        result = result[: max_chars - 3] + "..."
    return result


def _favorite_probability(row: pd.Series) -> Any:
    favorite_probability = _get(row, "favorite_probability", default="")
    if favorite_probability != "":
        return favorite_probability

    side = str(_get(row, "favorite_side", default="")).lower()
    if "home" in side or "local" in side:
        return _get(row, "prob_home_ai", "prob_home", default="")
    if "away" in side or "visitante" in side:
        return _get(row, "prob_away_ai", "prob_away", default="")
    if "draw" in side or "empate" in side:
        return _get(row, "prob_draw_ai", "prob_draw", default="")

    market_favorite = str(_get(row, "market_favorite", default="")).strip()
    home = str(_get(row, "home", default="")).strip()
    away = str(_get(row, "away", default="")).strip()

    if market_favorite and home and market_favorite.lower() == home.lower():
        return _get(row, "prob_home_ai", "prob_home", default="")
    if market_favorite and away and market_favorite.lower() == away.lower():
        return _get(row, "prob_away_ai", "prob_away", default="")

    return _get(row, "prediction_probability", default="")


def _favorite_team(row: pd.Series) -> str:
    value = str(_get(row, "favorite_team", "market_favorite", default="")).strip()
    if value:
        return value

    home = str(_get(row, "home", default="")).strip()
    away = str(_get(row, "away", default="")).strip()
    side = str(_get(row, "favorite_side", default="")).lower()

    if "home" in side or "local" in side:
        return home
    if "away" in side or "visitante" in side:
        return away
    return str(_get(row, "prediction", default="")).strip()


def _decision(row: pd.Series) -> tuple[str, str]:
    """
    Genera una decisión operativa:
    - APOSTAR
    - APOSTAR CON CAUTELA
    - NO APOSTAR

    La decisión usa datos ya calculados por la app:
    favorito claro, probabilidad del favorito, entropía, suerte, riesgo y conclusión IA.
    """
    fav_prob = _to_float(_favorite_probability(row))
    entropy = _to_float(_get(row, "entropy_score", default=""))
    luck = _normalize_level(_get(row, "luck_factor", default=""))
    risk = _normalize_level(_get(row, "risk_level", "risk", default=""))
    clear_fav = _yes_no(_get(row, "clear_favorite", default="")).lower() == "sí"
    ai_conclusion = _get(row, "ai_bet_conclusion", "favorite_bet_recommendation", default="")

    high_luck = luck == "Alto"
    high_risk = risk == "Alto"
    high_entropy = entropy is not None and entropy >= 0.90
    medium_entropy = entropy is not None and 0.78 <= entropy < 0.90

    reasons: list[str] = []

    if _contains_no_bet(ai_conclusion):
        reasons.append("La conclusión IA recomienda no apostar o evitar la jugada.")
        return "NO APOSTAR", " ".join(reasons)

    if fav_prob is not None:
        reasons.append(f"Probabilidad del favorito: {fav_prob * 100:.1f}%.")

    if entropy is not None:
        reasons.append(f"Entropía: {entropy:.2f}.")

    if risk:
        reasons.append(f"Riesgo: {risk}.")

    if luck:
        reasons.append(f"Factor suerte: {luck}.")

    if high_risk or high_luck or high_entropy:
        if high_risk:
            reasons.append("Riesgo alto.")
        if high_luck:
            reasons.append("Factor suerte alto.")
        if high_entropy:
            reasons.append("Partido con alta incertidumbre.")
        return "NO APOSTAR", " ".join(reasons)

    if clear_fav and fav_prob is not None and fav_prob >= 0.70 and not medium_entropy:
        reasons.append("Favorito claro con buena probabilidad y baja incertidumbre.")
        return "APOSTAR", " ".join(reasons)

    if fav_prob is not None and fav_prob >= 0.58:
        reasons.append("Hay señal positiva, pero no suficientemente limpia para entrada fuerte.")
        return "APOSTAR CON CAUTELA", " ".join(reasons)

    if _contains_caution(ai_conclusion):
        reasons.append("La conclusión IA exige cautela o validación adicional.")
        return "APOSTAR CON CAUTELA", " ".join(reasons)

    reasons.append("No hay ventaja suficiente en los datos principales.")
    return "NO APOSTAR", " ".join(reasons)


def _goles_resumen(row: pd.Series) -> str:
    home = _num(_get(row, "expected_goals_home_ai", default=""))
    away = _num(_get(row, "expected_goals_away_ai", default=""))
    total = _num(_get(row, "expected_total_goals_ai", default=""))
    over05 = _pct(_get(row, "prob_over_0_5_goals", default=""))
    over15 = _pct(_get(row, "prob_over_1_5_goals", default=""))
    over25 = _pct(_get(row, "prob_over_2_5_goals", default=""))

    parts = []
    if home or away or total:
        parts.append(f"Goles esperados: local {home or 'N/D'} - visitante {away or 'N/D'} | total {total or 'N/D'}")
    probs = []
    if over05:
        probs.append(f"Over 0.5: {over05}")
    if over15:
        probs.append(f"Over 1.5: {over15}")
    if over25:
        probs.append(f"Over 2.5: {over25}")
    if probs:
        parts.append(" | ".join(probs))

    summary = _get(row, "goal_expectation_summary", default="")
    if summary:
        parts.append(str(summary))

    return " || ".join(parts)


def _factores_equipos(row: pd.Series) -> str:
    return _join_text(
        _get(row, "team_level_matchup", default=""),
        _get(row, "team_level_caution", default=""),
        _get(row, "team_level_betting_comment", default=""),
        _get(row, "key_factors", default=""),
        _get(row, "expert_factors", default=""),
        _get(row, "market_reading", default=""),
        max_chars=1000,
    )


def _alertas_lesiones_contexto(row: pd.Series) -> str:
    alerts = _join_text(
        _get(row, "red_flags", default=""),
        _get(row, "volatility_factors", default=""),
        _get(row, "draw_risk", default=""),
        _get(row, "sources_used", default=""),
        max_chars=900,
    )
    if alerts:
        return alerts
    return "Sin alerta específica en la IA. Revisar lesiones, alineaciones oficiales, rotaciones y noticias antes de apostar."


def _is_prediction_like(df: pd.DataFrame) -> bool:
    cols = set(df.columns)
    return bool({"home", "away"}.issubset(cols) and (
        "favorite_team" in cols
        or "market_favorite" in cols
        or "prob_home_ai" in cols
        or "ai_bet_conclusion" in cols
    ))


def _compact_decision_export(raw_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for _, row in raw_df.iterrows():
        decision, decision_reason = _decision(row)

        home = str(_get(row, "home", default="")).strip()
        away = str(_get(row, "away", default="")).strip()
        partido = f"{home} vs {away}".strip(" vs ")

        rows.append({
            "N°": _get(row, "match_no", default=""),
            "Fecha": _get(row, "date_col", "date", default=""),
            "Hora": _get(row, "time_col", "time", default=""),
            "Grupo": _get(row, "group", "group_name", default=""),
            "Partido": partido,
            "Equipo favorito": _favorite_team(row),
            "Favorito claro": _yes_no(_get(row, "clear_favorite", default="")),
            "Prob. gana favorito": _pct(_favorite_probability(row)),
            "Decisión": decision,
            "Motivo decisión": decision_reason,
            "Recomendación IA": _join_text(
                _get(row, "ai_bet_conclusion", default=""),
                _get(row, "ai_bet_reason", default=""),
                _get(row, "favorite_bet_recommendation", default=""),
                max_chars=850,
            ),
            "Goles / probabilidades": _goles_resumen(row),
            "Entropía": _num(_get(row, "entropy_score", default=""), 2),
            "Lectura entropía": _join_text(
                _get(row, "entropy_factor", default=""),
                _get(row, "entropy_explanation", default=""),
                max_chars=450,
            ),
            "Factor suerte": _normalize_level(_get(row, "luck_factor", default="")),
            "Lectura suerte": _get(row, "luck_explanation", default=""),
            "Riesgo": _normalize_level(_get(row, "risk_level", "risk", default="")),
            "Factores equipos": _factores_equipos(row),
            "Lesiones / alertas / contexto": _alertas_lesiones_contexto(row),
            "Resumen IA": _get(row, "summary", default=""),
            "Estado IA": _get(row, "analysis_status", default=""),
            "Error IA": _get(row, "error_message", default=""),
        })

    out = pd.DataFrame(rows)

    # Orden de prioridad para lectura: primero las apuestas más claras.
    priority = {"APOSTAR": 0, "APOSTAR CON CAUTELA": 1, "NO APOSTAR": 2}
    if not out.empty and "Decisión" in out.columns:
        out["_orden"] = out["Decisión"].map(priority).fillna(9)
        out["_prob_num"] = out["Prob. gana favorito"].astype(str).str.replace("%", "", regex=False)
        out["_prob_num"] = pd.to_numeric(out["_prob_num"], errors="coerce")
        out = out.sort_values(["_orden", "_prob_num"], ascending=[True, False], na_position="last")
        out = out.drop(columns=["_orden", "_prob_num"], errors="ignore")

    return out


def excel_bytes(
    df: pd.DataFrame | None,
    simulations: pd.DataFrame | None = None,
    only_analyzed: bool = True,
) -> bytes:
    """
    Genera un Excel compacto para toma de decisión.

    Para predicciones:
    - No exporta todas las columnas técnicas.
    - Entrega favorito, probabilidad, decisión, goles, entropía, suerte,
      riesgo y factores clave.

    Para históricos/evaluaciones u otros DataFrames:
    - Exporta una hoja simple con las columnas disponibles.
    """
    output = io.BytesIO()

    raw_export_df = _filter_export_df(df, only_analyzed=only_analyzed)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if _is_prediction_like(raw_export_df):
            decision_df = _compact_decision_export(raw_export_df)
            decision_df.to_excel(writer, sheet_name="Decisión", index=False)

            resumen = pd.DataFrame({
                "Métrica": [
                    "Total partidos",
                    "APOSTAR",
                    "APOSTAR CON CAUTELA",
                    "NO APOSTAR",
                ],
                "Valor": [
                    len(decision_df),
                    int((decision_df["Decisión"] == "APOSTAR").sum()) if "Decisión" in decision_df.columns else 0,
                    int((decision_df["Decisión"] == "APOSTAR CON CAUTELA").sum()) if "Decisión" in decision_df.columns else 0,
                    int((decision_df["Decisión"] == "NO APOSTAR").sum()) if "Decisión" in decision_df.columns else 0,
                ],
            })
            resumen.to_excel(writer, sheet_name="Resumen", index=False)

            notes = pd.DataFrame({"Notas": [
                "Este Excel está simplificado para tomar decisión. No exporta todas las columnas técnicas del modelo.",
                "Decisión = APOSTAR / APOSTAR CON CAUTELA / NO APOSTAR, calculada con favorito claro, probabilidad del favorito, entropía, suerte y riesgo.",
                "La columna 'Lesiones / alertas / contexto' depende de lo que la IA y las fuentes disponibles hayan podido evaluar. Debes validar lesiones, alineaciones oficiales, rotaciones y noticias antes del partido.",
                "La probabilidad del favorito no garantiza el resultado. En fútbol siempre existen eventos de alta varianza: roja, penal, lesión, VAR, gol temprano o cambios tácticos.",
                "No apuestes capital + ganancia completa. Usa gestión de banca y límite por partido.",
            ]})
            notes.to_excel(writer, sheet_name="Notas", index=False)

        else:
            export_df = to_display_percent(raw_export_df)
            export_df.to_excel(writer, sheet_name="Datos", index=False)

            notes = pd.DataFrame({"Notas": [
                "Este archivo no tiene estructura de predicciones de partido; se exportaron las columnas disponibles.",
                "Las predicciones son probabilísticas y no garantizan resultados.",
            ]})
            notes.to_excel(writer, sheet_name="Notas", index=False)

        for sheet in writer.book.worksheets:
            sheet.sheet_state = "visible"
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                max_length = 0
                letter = column_cells[0].column_letter
                for cell in column_cells:
                    value = "" if cell.value is None else str(cell.value)
                    max_length = max(max_length, len(value))
                sheet.column_dimensions[letter].width = min(max_length + 2, 70)
        writer.book.active = 0

    output.seek(0)
    return output.getvalue()
