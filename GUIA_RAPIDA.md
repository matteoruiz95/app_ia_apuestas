# Guía rápida — Mundial 2026 IA Predictor

## 1. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

## 2. Configurar API keys

Copia `.env.example` y renómbralo a `.env`.

```env
OPENAI_API_KEY=tu_key_de_openai
OPENAI_MODEL=gpt-5-mini
API_FOOTBALL_KEY=tu_key_de_api_football
THE_ODDS_API_KEY=tu_key_de_the_odds_api
THE_ODDS_SPORT_KEY=soccer_fifa_world_cup
```

## 3. Ejecutar app

```bash
python -m streamlit run app.py
```

## 4. Flujo recomendado

1. Abre la app.
2. En la barra izquierda selecciona el modo:
   - **Selección manual**: escoges partido por partido.
   - **Top favoritos por cuota**: la app selecciona los favoritos más fuertes.
   - **Todos los partidos**: analiza los 72 partidos.
3. Presiona **🧠 Ejecutar IA en seleccionados**.
4. Revisa métricas, gráficos y tabla.
5. Presiona **🎲 Monte Carlo** si quieres simular escenarios.
6. Presiona **⬇️ Descargar Excel (analizados)**.

## Cambio importante v4

El Excel por defecto descarga **solo partidos analizados con IA**, no los 72 partidos completos. Si quieres exportar todos, desmarca en la barra lateral: **Excel solo partidos analizados**.
