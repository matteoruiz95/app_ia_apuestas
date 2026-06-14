from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from predictor.ai_runner import run_ai_analysis
from predictor.data import load_matches
from predictor.export import excel_bytes, to_display_percent
from predictor.auth import require_login
from predictor.history_db import (
    calculate_evaluation,
    clear_analysis_evaluations,
    clear_analysis_history,
    ensure_history_db,
    evaluation_count,
    history_count,
    history_existing_match_nos,
    latest_analysis_history,
    merge_latest_history_into_df,
    read_analysis_evaluations,
    read_analysis_history,
    save_analysis_evaluation,
    save_analysis_history,
)
from predictor.odds_math import (
    add_final_predictions,
    add_market_probabilities,
    analyzed_subset,
    processed_subset,
    display_scope,
    ensure_unique_columns,
    monte_carlo,
)

# Carga variables desde .env y desde API_KEYS_AQUI.env.
# El segundo archivo es más fácil de ver/editar en Windows.
load_dotenv()
load_dotenv("API_KEYS_AQUI.env", override=True)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
DUAL_LOGO_PURPLE = ASSETS_DIR / "dual_logo_purple.png"
DUAL_LOGO_WHITE = ASSETS_DIR / "dual_logo_white.png"

st.set_page_config(
    page_title="Dual | Mundial 2026 IA Predictor",
    page_icon="🟣",
    layout="wide",
)

st.markdown(
    """
<style>
    :root {
        --dual-purple: #792AF4;
        --dual-purple-dark: #2B235F;
        --dual-purple-soft: #F4EEFF;
        --dual-gray: #D8DAD9;
        --dual-text: #171328;
        --dual-muted: #625A78;
        --dual-white: #FFFFFF;
    }

    .stApp {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBF8FF 48%, #FFFFFF 100%);
        color: var(--dual-text);
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBF8FF 50%, #FFFFFF 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F4EEFF 100%);
        border-right: 1px solid rgba(121, 42, 244, 0.16);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: var(--dual-text) !important;
    }

    .block-container {
        padding-top: 1.35rem;
        padding-bottom: 3rem;
    }

    .dual-hero {
        background: linear-gradient(135deg, #792AF4 0%, #6C21E8 52%, #2B235F 100%);
        border-radius: 26px;
        padding: 28px 30px;
        margin-bottom: 22px;
        color: white;
        box-shadow: 0 22px 55px rgba(121, 42, 244, 0.22);
        border: 1px solid rgba(255,255,255,0.18);
    }

    .dual-hero h1 {
        color: white !important;
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.1rem);
        letter-spacing: -0.04em;
        line-height: 1.05;
    }

    .dual-hero p {
        color: rgba(255,255,255,0.88) !important;
        margin-top: 12px;
        font-size: 1.02rem;
        max-width: 980px;
    }

    .dual-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: .85rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: white;
    }

    .dual-card {
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(121, 42, 244, 0.14);
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 14px 36px rgba(43, 35, 95, 0.08);
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid rgba(121,42,244,.18);
        padding: 16px;
        border-radius: 18px;
        box-shadow: 0 14px 30px rgba(43, 35, 95, 0.07);
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--dual-muted) !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--dual-purple-dark) !important;
        font-weight: 800;
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #792AF4 0%, #5E18D7 100%) !important;
        color: #FFFFFF !important;
        border: 0 !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        box-shadow: 0 12px 24px rgba(121,42,244,.22);
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 32px rgba(121,42,244,.28);
    }

    input, textarea, div[data-baseweb="select"] > div {
        border-radius: 14px !important;
        border-color: rgba(121, 42, 244, 0.22) !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--dual-purple) !important;
        font-weight: 800;
    }

    [data-testid="stTabs"] button[aria-selected="true"]::after {
        background-color: var(--dual-purple) !important;
    }

    h1, h2, h3 {
        color: var(--dual-purple-dark) !important;
        letter-spacing: -0.025em;
    }

    .small-note { color: var(--dual-muted); font-size: 0.9rem; }

    .dual-login-wrap {
        max-width: 560px;
        margin: 32px auto 16px auto;
        padding: 30px;
        border-radius: 26px;
        background: #FFFFFF;
        border: 1px solid rgba(121,42,244,.16);
        box-shadow: 0 22px 55px rgba(43, 35, 95, 0.10);
        text-align: center;
    }

    .dual-login-wrap h2 {
        color: var(--dual-purple-dark) !important;
        margin-bottom: 8px;
    }

    .dual-login-wrap p {
        color: var(--dual-muted) !important;
        margin-top: 0;
    }
</style>
""",
    unsafe_allow_html=True,
)



def pct_metric(value: float | int | None) -> str:
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):.1%}"
    except Exception:
        return "N/A"


def bool_label(value) -> str:
    try:
        if value is None or pd.isna(value):
            return "No aplica"
    except Exception:
        pass

    if value in [1, True, "1", "True", "true", "Sí", "Si"]:
        return "Sí"

    if value in [0, False, "0", "False", "false", "No"]:
        return "No"

    return str(value)


def normalize_dataframe_for_ui(df: pd.DataFrame | None) -> pd.DataFrame:
    """Evita errores de Streamlit cuando existen columnas duplicadas."""
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    if df.empty:
        return df.copy()
    return ensure_unique_columns(df)


def create_base_dataframe(market_weight: float = 0.70, ai_weight: float = 0.30) -> pd.DataFrame:
    base = load_matches()
    base = add_market_probabilities(base)
    base = add_final_predictions(base, market_weight=market_weight, ai_weight=ai_weight)
    base["ai_analyzed"] = False
    base["ai_attempted"] = False
    base["analysis_status"] = "BASE"
    base["ai_analyzed_at"] = pd.NA
    base["error_message"] = pd.NA
    return normalize_dataframe_for_ui(base)


def init_state() -> None:
    ensure_history_db()
    if "df" not in st.session_state:
        st.session_state.df = create_base_dataframe()
    if "simulations" not in st.session_state:
        st.session_state.simulations = pd.DataFrame()


def match_label(row: pd.Series) -> str:
    return f"{int(row['match_no']):02d} | Grupo {row['group']} | {row['home']} vs {row['away']} | {row['date_col']} {row['time_col']}"


def selected_subset(df: pd.DataFrame, selected_match_nos: list[int]) -> pd.DataFrame:
    df = normalize_dataframe_for_ui(df)
    if not selected_match_nos or df.empty:
        return df.iloc[0:0].copy()
    return df[df["match_no"].astype(int).isin([int(x) for x in selected_match_nos])].copy()


def get_analysis_scope(df: pd.DataFrame, selected_match_nos: list[int] | None = None) -> pd.DataFrame:
    """
    Para métricas/simulación: prioriza partidos analizados con IA.
    Si aún no hay analizados, usa la selección actual.
    Si tampoco hay selección, usa todo.
    """
    df = normalize_dataframe_for_ui(df)
    processed = processed_subset(df)
    if not processed.empty:
        return processed
    if selected_match_nos:
        selected = selected_subset(df, selected_match_nos)
        if not selected.empty:
            return selected
    return df


def render_header() -> None:
    logo_col, text_col = st.columns([1.1, 5.2], vertical_alignment="center")

    with logo_col:
        if DUAL_LOGO_PURPLE.exists():
            st.image(str(DUAL_LOGO_PURPLE), width=190)
        else:
            st.markdown("### Dual")

    with text_col:
        st.markdown(
            """
            <div class="dual-hero">
                <div class="dual-chip">Dual Developments · Mundial 2026 IA Predictor</div>
                <h1>Predictor IA de fase de grupos</h1>
                <p>
                    Plataforma privada para analizar partidos con cuotas, IA, histórico local,
                    evaluación de resultados y criterios de riesgo. Diseño adaptado a la línea visual
                    de Dual: blanco, morado y enfoque tecnológico.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )



def render_sidebar() -> dict:
    if DUAL_LOGO_PURPLE.exists():
        st.sidebar.image(str(DUAL_LOGO_PURPLE), use_container_width=True)
    st.sidebar.markdown("---")
    st.sidebar.header("Configuración")

    st.sidebar.subheader("API Keys")
    st.sidebar.caption("Puedes pegarlas aquí o en el archivo visible API_KEYS_AQUI.env que viene en la carpeta.")
    openai_key = st.sidebar.text_input("OPENAI_API_KEY", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    api_football_key = st.sidebar.text_input("API_FOOTBALL_KEY", value=os.getenv("API_FOOTBALL_KEY", ""), type="password")
    odds_key = st.sidebar.text_input("THE_ODDS_API_KEY", value=os.getenv("THE_ODDS_API_KEY", ""), type="password")

    st.sidebar.subheader("IA")
    model = st.sidebar.selectbox(
        "Modelo OpenAI",
        options=["gpt-5-mini", "gpt-5", "gpt-5.5", "gpt-4.1-mini", "gpt-4.1"],
        index=0,
        help="Para cuidar presupuesto, usa gpt-5-mini. Para análisis más fuerte, usa gpt-5 o gpt-5.5 si tu cuenta lo permite.",
    )
    enable_web_search = st.sidebar.checkbox("Usar búsqueda web de OpenAI", value=True)

    st.sidebar.subheader("Selección de partidos para IA")
    df = normalize_dataframe_for_ui(st.session_state.get("df"))
    all_match_nos = df["match_no"].astype(int).tolist() if not df.empty and "match_no" in df.columns else []

    selection_mode = st.sidebar.radio(
        "Modo de selección",
        options=["Selección manual", "Top favoritos por cuota", "Todos los partidos"],
        index=0,
        help="La IA solo se ejecutará sobre los partidos seleccionados. El Excel descargará solo los analizados.",
    )

    max_matches = 12
    selected_match_nos: list[int] = []

    if selection_mode == "Todos los partidos":
        selected_match_nos = all_match_nos
        st.sidebar.info(f"Se analizarán {len(selected_match_nos)} partidos.")
    elif selection_mode == "Top favoritos por cuota":
        max_matches = st.sidebar.slider(
            "Cantidad de partidos top",
            min_value=1,
            max_value=max(1, len(all_match_nos)),
            value=min(12, max(1, len(all_match_nos))),
            help="Selecciona automáticamente los favoritos con mayor probabilidad de mercado.",
        )
        if "favorite_market_prob" in df.columns:
            selected_match_nos = (
                df.sort_values("favorite_market_prob", ascending=False)
                .head(int(max_matches))["match_no"]
                .astype(int)
                .tolist()
            )
        else:
            selected_match_nos = all_match_nos[: int(max_matches)]
        st.sidebar.info(f"Se analizarán {len(selected_match_nos)} partidos top.")
    else:
        groups = sorted(df["group"].dropna().unique().tolist()) if not df.empty and "group" in df.columns else []
        selected_groups = st.sidebar.multiselect(
            "Filtrar por grupo",
            options=groups,
            default=groups,
        )
        filtered = df[df["group"].isin(selected_groups)].copy() if selected_groups else df.copy()
        option_map = {match_label(row): int(row["match_no"]) for _, row in filtered.iterrows()}
        default_options = list(option_map.keys())[: min(5, len(option_map))]
        selected_labels = st.sidebar.multiselect(
            "Partidos a analizar",
            options=list(option_map.keys()),
            default=default_options,
            help="Puedes seleccionar uno, varios o todos los partidos visibles.",
        )
        selected_match_nos = [option_map[label] for label in selected_labels]
        st.sidebar.info(f"Seleccionados para IA: {len(selected_match_nos)}")

    st.sidebar.subheader("Pesos del modelo")
    market_weight = st.sidebar.slider("Peso cuotas / mercado", 0.0, 1.0, 0.70, 0.05)
    ai_weight = st.sidebar.slider("Peso IA", 0.0, 1.0, 0.30, 0.05)

    st.sidebar.subheader("Vista y exportación")
    show_only_analyzed = st.sidebar.checkbox(
        "Mostrar solo analizados cuando existan",
        value=True,
        help="Después de ejecutar IA, el dashboard se enfoca en los partidos analizados.",
    )
    export_only_analyzed = st.sidebar.checkbox(
        "Excel solo partidos procesados por IA",
        value=True,
        help="Recomendado: descarga únicamente los partidos que ya pasaron por IA. Si algún partido falla, también se exporta con el error para diagnosticar.",
    )

    st.sidebar.subheader("Simulación")
    simulations = st.sidebar.number_input("Número de simulaciones", min_value=1000, max_value=100000, value=10000, step=1000)

    st.sidebar.markdown(
        "<p class='small-note'>Tip presupuesto: prueba 3 a 5 partidos, luego sube a 12 y finalmente a 72.</p>",
        unsafe_allow_html=True,
    )

    existing_selected_match_nos = history_existing_match_nos(selected_match_nos)
    reanalyze_existing = False

    st.sidebar.subheader("Histórico local")
    st.sidebar.caption("La app guarda los análisis en una base SQLite local dentro de la carpeta data.")

    if existing_selected_match_nos:
        st.sidebar.warning(
            f"{len(existing_selected_match_nos)} partido(s) seleccionado(s) ya tienen análisis guardado en histórico."
        )
        reanalyze_existing = st.sidebar.checkbox(
            "Volver a analizar partidos que ya existen en histórico",
            value=False,
            help="Actívalo solo si quieres gastar tokens nuevamente y guardar una nueva versión del análisis.",
        )
    else:
        st.sidebar.success("Los partidos seleccionados no tienen histórico previo.")

    return {
        "openai_key": openai_key,
        "api_football_key": api_football_key,
        "odds_key": odds_key,
        "model": model,
        "enable_web_search": enable_web_search,
        "max_matches": int(max_matches),
        "selected_match_nos": selected_match_nos,
        "existing_selected_match_nos": existing_selected_match_nos,
        "reanalyze_existing": bool(reanalyze_existing),
        "selection_mode": selection_mode,
        "market_weight": float(market_weight),
        "ai_weight": float(ai_weight),
        "show_only_analyzed": bool(show_only_analyzed),
        "export_only_analyzed": bool(export_only_analyzed),
        "simulations": int(simulations),
    }


def render_actions(config: dict) -> None:
    col1, col2, col3, col4 = st.columns([1.2, 1.5, 1.3, 1.5])

    with col1:
        if st.button("🔄 Recalcular base", use_container_width=True):
            st.session_state.df = create_base_dataframe(config["market_weight"], config["ai_weight"])
            st.session_state.simulations = pd.DataFrame()
            st.toast("Análisis base recalculado")

    with col2:
        if st.button("🧠 Ejecutar IA en seleccionados", type="primary", use_container_width=True):
            if not config["openai_key"]:
                st.error("Agrega tu OPENAI_API_KEY en la barra lateral o en el archivo .env")
            elif not config["selected_match_nos"]:
                st.error("Selecciona al menos un partido para analizar con IA.")
            elif config.get("existing_selected_match_nos") and not config.get("reanalyze_existing", False):
                st.warning(
                    "Uno o más partidos seleccionados ya tienen análisis guardado en el histórico local."
                )
                st.info(
                    "Para volver a analizarlos y gastar tokens nuevamente, activa en la barra lateral: "
                    "'Volver a analizar partidos que ya existen en histórico'."
                )
                st.write("Partidos ya guardados:", config.get("existing_selected_match_nos"))
            else:
                progress = st.progress(0)
                status = st.empty()

                def cb(i: int, total: int, label: str):
                    progress.progress(i / total)
                    status.info(f"Analizando {i}/{total}: {label}")

                ai_df = run_ai_analysis(
                    normalize_dataframe_for_ui(st.session_state.df),
                    max_matches=config["max_matches"],
                    selected_match_nos=config["selected_match_nos"],
                    market_weight=config["market_weight"],
                    ai_weight=config["ai_weight"],
                    openai_key=config["openai_key"],
                    openai_model=config["model"],
                    enable_web_search=config["enable_web_search"],
                    api_football_key=config["api_football_key"],
                    odds_api_key=config["odds_key"],
                    progress_callback=cb,
                )
                st.session_state.df = normalize_dataframe_for_ui(ai_df)
                saved_count = save_analysis_history(
                    st.session_state.df,
                    selected_match_nos=config["selected_match_nos"],
                    source="streamlit",
                )
                st.session_state.simulations = pd.DataFrame()
                status.success(f"Análisis IA terminado. {saved_count} registro(s) guardado(s) en histórico local.")
                st.toast("Predicciones actualizadas y guardadas")

    with col3:
        if st.button("🎲 Monte Carlo", use_container_width=True):
            scope = get_analysis_scope(st.session_state.df, config.get("selected_match_nos", []))
            st.session_state.simulations = monte_carlo(scope, n=config["simulations"])
            st.toast("Simulación terminada")

    with col4:
        try:
            df_xlsx = excel_bytes(
                st.session_state.get("df"),
                st.session_state.get("simulations"),
                only_analyzed=config.get("export_only_analyzed", True),
            )
            suffix = "analizados" if config.get("export_only_analyzed", True) else "todos"
            st.download_button(
                f"⬇️ Descargar Excel ({suffix})",
                data=df_xlsx,
                file_name=f"predicciones_mundial_ia_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"No se pudo generar el Excel: {exc}")


def render_selection_preview(df: pd.DataFrame, selected_match_nos: list[int]) -> None:
    st.subheader("Partidos seleccionados para IA")
    selected = selected_subset(df, selected_match_nos)
    if selected.empty:
        st.info("No hay partidos seleccionados. Selecciona partidos en la barra lateral.")
        return

    display = selected[["match_no", "date_col", "time_col", "group", "home", "away", "favorite_odds", "market_favorite", "favorite_market_prob"]].copy()
    display = to_display_percent(display)
    st.dataframe(display, use_container_width=True, height=220)


def render_metrics(df: pd.DataFrame) -> None:
    df = normalize_dataframe_for_ui(df)
    total = len(df)

    if df.empty:
        high = 0
        low_risk = 0
        avg_prob = 0.0
    else:
        high = int(df.get("confidence", pd.Series(dtype=str)).fillna("").isin(["Alta", "Muy alta"]).sum())
        low_risk = int((df.get("risk", pd.Series(dtype=str)).fillna("") == "Bajo").sum())
        avg_prob = pd.to_numeric(df.get("prediction_probability", pd.Series(dtype=float)), errors="coerce").mean()
        if pd.isna(avg_prob):
            avg_prob = 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Partidos en vista", total)
    c2.metric("Alta / Muy alta confianza", high)
    c3.metric("Riesgo bajo", low_risk)
    c4.metric("Prob. promedio predicción", f"{float(avg_prob):.1%}")


def render_charts(df: pd.DataFrame) -> None:
    df = normalize_dataframe_for_ui(df)
    if df.empty or "prediction_probability" not in df.columns:
        st.info("No hay datos suficientes para generar gráficos.")
        return

    top = df.copy()
    top["prediction_probability"] = pd.to_numeric(top["prediction_probability"], errors="coerce")
    top = top.sort_values("prediction_probability", ascending=False).head(20).copy()
    top["partido"] = top["home"].astype(str) + " vs " + top["away"].astype(str)
    top["probabilidad_%"] = top["prediction_probability"] * 100

    col1, col2 = st.columns([1.4, 1])

    with col1:
        fig = px.bar(
            top.sort_values("probabilidad_%"),
            x="probabilidad_%",
            y="partido",
            orientation="h",
            hover_data=[c for c in ["prediction", "confidence", "risk", "favorite_odds", "ai_analyzed"] if c in top.columns],
            title="Top predicciones más probables",
            labels={"probabilidad_%": "Probabilidad final (%)", "partido": "Partido"},
        )
        fig.update_layout(height=620, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        risk_counts = df.get("risk", pd.Series(dtype=str)).fillna("Sin dato").value_counts().reset_index()
        risk_counts.columns = ["riesgo", "partidos"]
        fig2 = px.pie(risk_counts, names="riesgo", values="partidos", title="Distribución por riesgo")
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)

        conf_counts = df.get("confidence", pd.Series(dtype=str)).fillna("Sin dato").value_counts().reset_index()
        conf_counts.columns = ["confianza", "partidos"]
        fig3 = px.pie(conf_counts, names="confianza", values="partidos", title="Distribución por confianza")
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, use_container_width=True)

    scatter = df.copy()
    scatter["partido"] = scatter["home"].astype(str) + " vs " + scatter["away"].astype(str)
    scatter["prediction_probability"] = pd.to_numeric(scatter["prediction_probability"], errors="coerce")
    scatter["probabilidad_%"] = scatter["prediction_probability"] * 100
    fig4 = px.scatter(
        scatter,
        x="favorite_odds",
        y="probabilidad_%",
        size="probabilidad_%",
        color="risk" if "risk" in scatter.columns else None,
        hover_name="partido",
        hover_data=[c for c in ["prediction", "market_favorite", "confidence", "ai_analyzed"] if c in scatter.columns],
        title="Relación cuota favorita vs probabilidad final",
        labels={"favorite_odds": "Cuota favorita", "probabilidad_%": "Probabilidad final (%)"},
    )
    st.plotly_chart(fig4, use_container_width=True)


def render_table(df: pd.DataFrame) -> None:
    st.subheader("Tabla de predicciones")
    df = normalize_dataframe_for_ui(df)
    if df.empty:
        st.info("No hay partidos para mostrar.")
        return

    display = to_display_percent(df)
    cols = [
        "match_no", "date_col", "time_col", "group", "home", "away",
        "home_odds", "draw_odds", "away_odds",
        "market_favorite", "favorite_market_prob",
        "ai_analyzed", "ai_attempted", "analysis_status", "ai_analyzed_at", "error_message",
        "prediction", "prediction_probability", "confidence", "risk",
        "prob_home_final", "prob_draw_final", "prob_away_final",
        "prob_home_ai", "prob_draw_ai", "prob_away_ai",
        "entropy_score", "entropy_factor", "entropy_explanation",
        "home_team_level", "away_team_level", "team_level_matchup",
        "team_level_caution", "team_level_betting_comment",
        "clear_favorite", "favorite_team", "favorite_probability", "favorite_strength",
        "favorite_conclusion", "favorite_double_chance_selection",
        "favorite_bet_recommendation", "ai_bet_vs_favorite",
        "ai_bet_market", "ai_bet_selection", "ai_bet_probability",
        "ai_bet_confidence", "ai_bet_conclusion", "ai_bet_reason",
        "prob_over_0_5_goals", "prob_over_1_5_goals", "prob_over_2_5_goals",
        "prob_double_chance_home_draw", "prob_double_chance_away_draw",
        "prob_double_chance_home_away",
        "ai_fallback_used", "ai_fallback_reason",
        "home_official_matches_sample", "home_avg_goals_for_official",
        "home_avg_goals_against_official", "home_avg_total_goals_official",
        "away_official_matches_sample", "away_avg_goals_for_official",
        "away_avg_goals_against_official", "away_avg_total_goals_official",
        "summary", "key_factors", "red_flags", "sources_used",
    ]
    available = [c for c in cols if c in display.columns]
    sort_col = "prediction_probability" if "prediction_probability" in display.columns else available[0]
    st.dataframe(display[available].sort_values(sort_col, ascending=False), use_container_width=True, height=500)


def render_simulation(sim: pd.DataFrame) -> None:
    if sim is None or not isinstance(sim, pd.DataFrame) or sim.empty:
        return
    st.subheader("Simulación Monte Carlo")
    c1, c2, c3 = st.columns(3)
    c1.metric("Promedio predicciones acertadas simuladas", f"{sim['predictions_won'].mean():.2f}")
    c2.metric("Percentil 10", int(sim["predictions_won"].quantile(0.10)))
    c3.metric("Percentil 90", int(sim["predictions_won"].quantile(0.90)))

    fig = px.histogram(sim, x="predictions_won", nbins=25, title="Distribución de predicciones ganadoras por simulación")
    st.plotly_chart(fig, use_container_width=True)



def render_history_tab() -> None:
    st.subheader("Histórico local de análisis")

    total = history_count()
    st.caption(
        "Los análisis se guardan en una base SQLite local: data/analisis_historico.sqlite"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Registros históricos", total)

    history_df = read_analysis_history(limit=None)
    latest_df = latest_analysis_history()

    c2.metric("Partidos únicos con histórico", len(latest_df) if isinstance(latest_df, pd.DataFrame) else 0)

    if isinstance(history_df, pd.DataFrame) and not history_df.empty and "analysis_status" in history_df.columns:
        ok_count = int((history_df["analysis_status"].fillna("").astype(str).str.upper() == "OK").sum())
    else:
        ok_count = 0

    c3.metric("Análisis OK guardados", ok_count)

    if history_df.empty:
        st.info("Todavía no hay análisis guardados. Ejecuta IA en uno o más partidos para crear histórico.")
        return

    with st.expander("Acciones del histórico", expanded=False):
        col_a, col_b, col_c = st.columns([1.3, 1.3, 1.4])

        with col_a:
            if st.button("📥 Cargar últimos análisis al dashboard", use_container_width=True):
                st.session_state.df = normalize_dataframe_for_ui(
                    merge_latest_history_into_df(st.session_state.get("df"))
                )
                st.success("Se cargó el último análisis histórico de cada partido en el dashboard.")

        with col_b:
            history_xlsx = excel_bytes(history_df, simulations=None, only_analyzed=False)
            st.download_button(
                "⬇️ Descargar histórico Excel",
                data=history_xlsx,
                file_name=f"historico_analisis_mundial_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_c:
            confirm_clear = st.checkbox("Confirmar borrado del histórico")
            if st.button("🗑️ Borrar histórico local", use_container_width=True, disabled=not confirm_clear):
                clear_analysis_history()
                st.success("Histórico local borrado.")
                st.rerun()

    view_mode = st.radio(
        "Vista",
        options=["Último análisis por partido", "Todos los análisis guardados"],
        horizontal=True,
        index=0,
    )

    df_hist = latest_df if view_mode == "Último análisis por partido" else history_df
    df_hist = normalize_dataframe_for_ui(df_hist)

    if df_hist.empty:
        st.info("No hay datos para mostrar.")
        return

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        groups = sorted(df_hist["group"].dropna().astype(str).unique().tolist()) if "group" in df_hist.columns else []
        selected_groups = st.multiselect("Filtrar grupo", options=groups, default=groups)

    with col2:
        statuses = sorted(df_hist["analysis_status"].dropna().astype(str).unique().tolist()) if "analysis_status" in df_hist.columns else []
        selected_statuses = st.multiselect("Filtrar estado", options=statuses, default=statuses)

    with col3:
        search_text = st.text_input("Buscar equipo", value="")

    filtered = df_hist.copy()

    if selected_groups and "group" in filtered.columns:
        filtered = filtered[filtered["group"].astype(str).isin(selected_groups)]

    if selected_statuses and "analysis_status" in filtered.columns:
        filtered = filtered[filtered["analysis_status"].astype(str).isin(selected_statuses)]

    if search_text.strip() and {"home", "away"}.issubset(filtered.columns):
        term = search_text.strip().lower()
        filtered = filtered[
            filtered["home"].astype(str).str.lower().str.contains(term, na=False)
            | filtered["away"].astype(str).str.lower().str.contains(term, na=False)
        ]

    display = to_display_percent(filtered)

    cols = [
        "history_id", "history_saved_at", "match_no", "date_col", "time_col", "group", "home", "away",
        "analysis_status", "ai_analyzed_at",
        "prediction", "prediction_probability", "confidence", "risk",
        "ai_bet_market", "ai_bet_selection", "ai_bet_probability",
        "ai_bet_confidence", "ai_bet_conclusion",
        "clear_favorite", "favorite_team", "favorite_probability", "favorite_strength",
        "favorite_conclusion", "favorite_bet_recommendation", "ai_bet_vs_favorite",
        "entropy_score", "entropy_factor",
        "home_team_level", "away_team_level", "team_level_matchup",
        "team_level_caution", "team_level_betting_comment",
        "expected_result", "expected_total_goals_ai",
        "luck_factor", "summary", "error_message",
    ]

    available = [c for c in cols if c in display.columns]

    if available:
        st.dataframe(display[available], use_container_width=True, height=520)
    else:
        st.dataframe(display, use_container_width=True, height=520)



def render_evaluation_charts(evaluations: pd.DataFrame) -> None:
    evaluations = normalize_dataframe_for_ui(evaluations)

    if evaluations.empty:
        st.info("Todavía no hay evaluaciones guardadas para graficar.")
        return

    metric_columns = {
        "winner_correct": "Acierto ganador",
        "ai_bet_correct": "Acierto apuesta IA",
        "goal_market_correct": "Acierto mercado de goles",
        "ai_bet_vs_favorite_correct": "Acierto IA vs favorito",
        "favorite_direct_correct": "Acierto favorito directo",
        "favorite_double_chance_correct": "Acierto favorito gana/empata",
        "expected_score_correct": "Acierto marcador exacto",
        "expected_total_goals_close": "Total goles cercano",
    }

    summary_rows = []

    for col, label in metric_columns.items():
        if col not in evaluations.columns:
            continue

        values = pd.to_numeric(evaluations[col], errors="coerce").dropna()

        if values.empty:
            continue

        summary_rows.append(
            {
                "Métrica": label,
                "Evaluaciones": int(len(values)),
                "Aciertos": int((values == 1).sum()),
                "Tasa": float((values == 1).mean()),
            }
        )

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        summary_df["Tasa_%"] = summary_df["Tasa"] * 100

        fig = px.bar(
            summary_df.sort_values("Tasa_%"),
            x="Tasa_%",
            y="Métrica",
            orientation="h",
            text="Tasa_%",
            hover_data=["Evaluaciones", "Aciertos"],
            title="Tasa de acierto por tipo de evaluación",
            labels={"Tasa_%": "Tasa de acierto (%)"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=520, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        if "ai_bet_market" in evaluations.columns:
            market_counts = evaluations["ai_bet_market"].fillna("Sin dato").astype(str).value_counts().reset_index()
            market_counts.columns = ["Mercado", "Cantidad"]
            fig2 = px.pie(
                market_counts,
                names="Mercado",
                values="Cantidad",
                title="Distribución de mercados recomendados por IA",
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        if "actual_result" in evaluations.columns:
            result_counts = evaluations["actual_result"].fillna("Sin dato").astype(str).value_counts().reset_index()
            result_counts.columns = ["Resultado real", "Cantidad"]
            fig3 = px.pie(
                result_counts,
                names="Resultado real",
                values="Cantidad",
                title="Distribución de resultados reales evaluados",
            )
            st.plotly_chart(fig3, use_container_width=True)

    if {"ai_bet_market", "ai_bet_correct"}.issubset(evaluations.columns):
        grouped = evaluations.copy()
        grouped["ai_bet_correct_num"] = pd.to_numeric(grouped["ai_bet_correct"], errors="coerce")
        grouped = grouped.dropna(subset=["ai_bet_correct_num"])

        if not grouped.empty:
            by_market = (
                grouped.groupby("ai_bet_market", dropna=False)
                .agg(
                    evaluaciones=("ai_bet_correct_num", "count"),
                    tasa_acierto=("ai_bet_correct_num", "mean"),
                )
                .reset_index()
            )
            by_market["tasa_%"] = by_market["tasa_acierto"] * 100

            fig4 = px.bar(
                by_market.sort_values("tasa_%"),
                x="tasa_%",
                y="ai_bet_market",
                orientation="h",
                hover_data=["evaluaciones"],
                title="Acierto de apuesta IA por mercado",
                labels={"tasa_%": "Tasa de acierto (%)", "ai_bet_market": "Mercado"},
            )
            fig4.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig4, use_container_width=True)


def render_evaluation_tab() -> None:
    st.subheader("Evaluación de resultados reales")

    st.caption(
        "Aquí registras el marcador real y la app calcula si la IA acertó ganador, mercado de goles, apuesta sugerida y lectura frente al favorito."
    )

    history_df = latest_analysis_history()

    if history_df.empty:
        st.info("Primero debes tener análisis guardados en el histórico para poder evaluarlos.")
        return

    evaluations = read_analysis_evaluations(limit=None)

    c1, c2, c3, c4 = st.columns(4)

    total_evals = evaluation_count()
    c1.metric("Evaluaciones guardadas", total_evals)

    if not evaluations.empty and "winner_correct" in evaluations.columns:
        winner_rate = pd.to_numeric(evaluations["winner_correct"], errors="coerce").dropna().mean()
    else:
        winner_rate = None
    c2.metric("Acierto ganador", pct_metric(winner_rate))

    if not evaluations.empty and "ai_bet_correct" in evaluations.columns:
        bet_rate = pd.to_numeric(evaluations["ai_bet_correct"], errors="coerce").dropna().mean()
    else:
        bet_rate = None
    c3.metric("Acierto apuesta IA", pct_metric(bet_rate))

    if not evaluations.empty and "ai_bet_vs_favorite_correct" in evaluations.columns:
        fav_rate = pd.to_numeric(evaluations["ai_bet_vs_favorite_correct"], errors="coerce").dropna().mean()
    else:
        fav_rate = None
    c4.metric("Acierto IA vs favorito", pct_metric(fav_rate))

    st.divider()

    st.markdown("### Registrar resultado real")

    history_df = normalize_dataframe_for_ui(history_df)

    def eval_option_label(row: pd.Series) -> str:
        history_id = row.get("history_id", "")
        match_no = row.get("match_no", "")
        group = row.get("group", "")
        home = row.get("home", "")
        away = row.get("away", "")
        saved_at = row.get("history_saved_at", "")
        return f"Hist {history_id} | Partido {match_no} | Grupo {group} | {home} vs {away} | {saved_at}"

    option_map = {
        eval_option_label(row): row.to_dict()
        for _, row in history_df.iterrows()
    }

    selected_label = st.selectbox(
        "Selecciona análisis histórico a evaluar",
        options=list(option_map.keys()),
    )

    selected_row = option_map[selected_label]

    preview_cols = [
        "match_no", "group", "home", "away", "prediction", "prediction_probability",
        "expected_result", "expected_total_goals_ai",
        "ai_bet_market", "ai_bet_selection", "ai_bet_probability",
        "ai_bet_vs_favorite", "favorite_team", "favorite_conclusion",
        "entropy_factor", "risk", "luck_factor",
    ]

    preview = pd.DataFrame([{k: selected_row.get(k) for k in preview_cols if k in selected_row}])
    st.dataframe(to_display_percent(preview), use_container_width=True, height=120)

    col_a, col_b, col_c = st.columns([1, 1, 2])

    with col_a:
        actual_home_goals = st.number_input(
            f"Goles reales {selected_row.get('home', 'Local')}",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
        )

    with col_b:
        actual_away_goals = st.number_input(
            f"Goles reales {selected_row.get('away', 'Visitante')}",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
        )

    with col_c:
        notes = st.text_area(
            "Notas de evaluación",
            value="",
            placeholder="Ej: acertó ganador, falló over 1.5 por gol anulado, etc.",
            height=98,
        )

    evaluation_preview = calculate_evaluation(
        analysis_row=selected_row,
        actual_home_goals=int(actual_home_goals),
        actual_away_goals=int(actual_away_goals),
        notes=notes,
    )

    st.markdown("### Vista previa de evaluación")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Resultado real", evaluation_preview["actual_score"])
    p2.metric("Ganador real", evaluation_preview["actual_result"])
    p3.metric("Acertó ganador", bool_label(evaluation_preview["winner_correct"]))
    p4.metric("Acertó apuesta IA", bool_label(evaluation_preview["ai_bet_correct"]))

    p5, p6, p7, p8 = st.columns(4)
    p5.metric("Acertó mercado goles", bool_label(evaluation_preview["goal_market_correct"]))
    p6.metric("IA vs favorito verdad", bool_label(evaluation_preview["ai_bet_vs_favorite_correct"]))
    p7.metric("Favorito directo ganó", bool_label(evaluation_preview["favorite_direct_correct"]))
    p8.metric("Favorito gana/empata", bool_label(evaluation_preview["favorite_double_chance_correct"]))

    detail_cols = [
        "actual_score", "actual_result", "prediction", "winner_correct",
        "expected_result", "expected_score_correct", "expected_total_goals_close",
        "ai_bet_market", "ai_bet_selection", "ai_bet_correct",
        "goal_market_correct", "ai_bet_vs_favorite", "ai_bet_vs_favorite_correct",
        "favorite_team", "favorite_side", "favorite_direct_correct",
        "favorite_double_chance_correct",
    ]

    st.dataframe(
        pd.DataFrame([{k: evaluation_preview.get(k) for k in detail_cols}]),
        use_container_width=True,
        height=120,
    )

    if st.button("💾 Guardar evaluación en base local", type="primary", use_container_width=True):
        evaluation_id = save_analysis_evaluation(
            analysis_row=selected_row,
            actual_home_goals=int(actual_home_goals),
            actual_away_goals=int(actual_away_goals),
            notes=notes,
        )
        st.success(f"Evaluación guardada con ID {evaluation_id}.")
        st.rerun()

    st.divider()

    st.markdown("### Gráficos con evaluaciones almacenadas")

    evaluations = read_analysis_evaluations(limit=None)

    if evaluations.empty:
        st.info("Aún no hay evaluaciones guardadas.")
        return

    render_evaluation_charts(evaluations)

    st.divider()

    st.markdown("### Tabla de evaluaciones guardadas")

    eval_display = evaluations.copy()

    # Convertir 1/0 a Sí/No para lectura.
    bool_cols = [
        "winner_correct", "expected_score_correct", "expected_total_goals_close",
        "goal_market_correct", "ai_bet_correct", "ai_bet_vs_favorite_correct",
        "favorite_direct_correct", "favorite_double_chance_correct",
    ]

    for col in bool_cols:
        if col in eval_display.columns:
            eval_display[col] = eval_display[col].apply(bool_label)

    eval_cols = [
        "evaluation_id", "evaluation_saved_at", "history_id", "match_no", "group",
        "home", "away", "actual_score", "actual_result",
        "prediction", "winner_correct",
        "expected_result", "expected_score_correct", "expected_total_goals_close",
        "ai_bet_market", "ai_bet_selection", "ai_bet_correct",
        "goal_market_correct", "ai_bet_vs_favorite", "ai_bet_vs_favorite_correct",
        "favorite_team", "favorite_side", "favorite_direct_correct",
        "favorite_double_chance_correct", "notes",
    ]

    available_eval_cols = [c for c in eval_cols if c in eval_display.columns]
    st.dataframe(eval_display[available_eval_cols], use_container_width=True, height=520)

    with st.expander("Acciones de evaluaciones", expanded=False):
        col_x, col_y = st.columns(2)

        with col_x:
            eval_xlsx = excel_bytes(evaluations, simulations=None, only_analyzed=False)
            st.download_button(
                "⬇️ Descargar evaluaciones Excel",
                data=eval_xlsx,
                file_name=f"evaluaciones_analisis_mundial_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_y:
            confirm_clear_eval = st.checkbox("Confirmar borrado de evaluaciones")
            if st.button("🗑️ Borrar evaluaciones", use_container_width=True, disabled=not confirm_clear_eval):
                clear_analysis_evaluations()
                st.success("Evaluaciones borradas.")
                st.rerun()


def main() -> None:
    init_state()
    render_header()

    if not require_login():
        return

    config = render_sidebar()

    tab_dashboard, tab_history, tab_evaluation = st.tabs(["📊 Dashboard", "🗄️ Histórico de análisis", "✅ Evaluación resultados"])

    with tab_dashboard:
        render_actions(config)

        raw_df = normalize_dataframe_for_ui(st.session_state.df)
        st.session_state.df = raw_df

        analyzed_count = len(analyzed_subset(raw_df))
        processed = processed_subset(raw_df)
        processed_count = len(processed)
        error_count = 0
        if not processed.empty and "analysis_status" in processed.columns:
            error_count = int((processed["analysis_status"].fillna("").astype(str).str.upper() == "ERROR").sum())

        if processed_count > 0 and config.get("show_only_analyzed", True):
            df = display_scope(raw_df, only_analyzed=True)
            if analyzed_count > 0 and error_count == 0:
                st.success(f"Mostrando {len(df)} partidos procesados con IA: {analyzed_count} OK.")
            elif analyzed_count > 0 and error_count > 0:
                st.warning(f"Mostrando {len(df)} partidos procesados con IA: {analyzed_count} OK y {error_count} con error. Revisa error_message.")
            else:
                st.error(f"Se intentó ejecutar IA en {processed_count} partidos, pero todos fallaron. Revisa analysis_status y error_message en la tabla.")
        else:
            df = raw_df
            if processed_count == 0:
                st.info("Aún no hay partidos procesados con IA. Selecciona partidos en la barra lateral y presiona 'Ejecutar IA en seleccionados'.")
            else:
                st.info(f"Hay {processed_count} partidos procesados con IA, pero estás viendo todos los partidos.")

        with st.expander("Ver partidos seleccionados para la próxima ejecución IA", expanded=False):
            render_selection_preview(raw_df, config.get("selected_match_nos", []))

        render_metrics(df)
        st.divider()
        render_charts(df)
        st.divider()
        render_table(df)
        render_simulation(st.session_state.simulations)

        st.warning(
            "Las predicciones son probabilísticas. No uses esto como garantía de apuesta ni arriesgues dinero que no puedas perder."
        )

    with tab_history:
        render_history_tab()

    with tab_evaluation:
        render_evaluation_tab()


if __name__ == "__main__":
    main()
