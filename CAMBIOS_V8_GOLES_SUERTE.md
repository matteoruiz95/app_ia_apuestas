# Cambios v8 - Goles esperados y factor suerte

Esta versión agrega nuevos campos al análisis IA:

- `expected_result`: marcador esperado del partido, ejemplo 2-0.
- `expected_goals_home_ai`: promedio de goles esperado del local.
- `expected_goals_away_ai`: promedio de goles esperado del visitante.
- `expected_total_goals_ai`: promedio total de goles del partido.
- `goal_expectation_summary`: explicación corta del promedio de goles.
- `luck_factor`: Bajo, Medio o Alto.
- `luck_explanation`: explicación del factor suerte/varianza.
- `volatility_factors`: eventos que pueden alterar el partido, como VAR, penal, roja, balón parado, rebote.
- `expert_factors`: factores expertos adicionales como xG, balón parado, disciplina, contexto de grupo y duelo táctico.

También se mantiene el fallback para completar campos si la IA omite alguno.
