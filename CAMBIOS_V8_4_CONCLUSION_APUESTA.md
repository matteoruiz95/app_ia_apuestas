# Cambios v8.4 - Conclusión de apuesta IA

Esta versión agrega una conclusión tipo casa de apuestas.

Nuevas columnas:

- `ai_bet_market`
- `ai_bet_selection`
- `ai_bet_probability`
- `ai_bet_confidence`
- `ai_bet_conclusion`
- `ai_bet_reason`

También agrega probabilidades de mercados comunes:

- `prob_over_0_5_goals`
- `prob_over_1_5_goals`
- `prob_over_2_5_goals`
- `prob_double_chance_home_draw`
- `prob_double_chance_away_draw`
- `prob_double_chance_home_away`

## Mercados evaluados

- Resultado final 1X2:
  - Gana local
  - Empate
  - Gana visitante

- Doble oportunidad:
  - Local o empate 1X
  - Visitante o empate X2
  - Local o visitante 12

- Total de goles:
  - Más de 0.5 goles
  - Más de 1.5 goles
  - Más de 2.5 goles

## Cómo decide

La app compara:

- Probabilidades IA del partido.
- Goles esperados.
- Factor entropía.
- Nivel de riesgo.
- Factor suerte.

Si no hay una opción suficientemente fuerte, devuelve:

`No apostar`

Nota: esta columna es una lectura probabilística y no garantiza resultados.
