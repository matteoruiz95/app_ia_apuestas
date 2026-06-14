# Cambios v8.8 - Evaluación de resultados reales

Esta versión agrega una pantalla para evaluar si la IA acertó cuando ya se conoce el marcador real.

## Nueva pestaña

`Evaluación resultados`

Permite:

- Seleccionar un análisis histórico.
- Registrar marcador real.
- Guardar evaluación en SQLite.
- Ver métricas y gráficos de acierto.
- Descargar evaluaciones a Excel.

## Nueva tabla SQLite

Se crea automáticamente:

`analysis_evaluations`

Dentro de la misma base local:

`data/analisis_historico.sqlite`

## Qué calcula

Al guardar el resultado real, la app calcula:

- `winner_correct`: si acertó ganador/empate.
- `expected_score_correct`: si acertó marcador exacto.
- `expected_total_goals_close`: si el total de goles real quedó cerca del promedio esperado.
- `goal_market_correct`: si acertó mercado de goles cuando recomendó over 0.5 / 1.5 / 2.5.
- `ai_bet_correct`: si la apuesta sugerida por IA fue correcta.
- `ai_bet_vs_favorite_correct`: si fue verdad lo que decía la columna IA vs favorito.
- `favorite_direct_correct`: si el favorito ganó.
- `favorite_double_chance_correct`: si el favorito ganó o empató.

## Gráficos

La pestaña muestra:

- Tasa de acierto por métrica.
- Distribución de mercados recomendados.
- Distribución de resultados reales.
- Acierto por mercado de apuesta IA.
