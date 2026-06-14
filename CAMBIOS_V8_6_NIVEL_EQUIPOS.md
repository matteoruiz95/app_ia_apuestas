# Cambios v8.6 - Clasificación competitiva de equipos

Esta versión agrega clasificación de selecciones por nivel competitivo:

- `Elite`
- `Medio`
- `Bajo`

Importante: `Bajo` no significa que el equipo sea malo. En esta app significa menor experiencia mundialista reciente, menor profundidad de plantilla, menor peso internacional relativo o menor roce ante selecciones top.

## Nuevas columnas

- `home_team_level`
- `away_team_level`
- `home_team_level_comment`
- `away_team_level_comment`
- `team_level_matchup`
- `team_level_gap`
- `team_level_caution`
- `team_level_betting_comment`

## Cómo lo usa la app

La clasificación entra como contexto para la IA y también como cálculo determinístico dentro de la app.

Se combina con:

- Probabilidades IA
- Entropía
- Factor suerte
- Riesgo
- Goles esperados
- Promedio de goles oficiales no amistosos
- Favorito claro
- Conclusión de apuesta

## Lectura práctica

- Elite vs Bajo: puede haber favorito claro, pero se revisa rotación, varianza, roja, penal o baja intensidad.
- Elite vs Medio: favorito probable, pero se valida con entropía y doble oportunidad.
- Medio vs Medio: partido peligroso; cuidado con ganador directo.
- Medio vs Bajo: puede haber favorito, pero no asumir goleada sin respaldo de goles y cuotas.
- Bajo vs Bajo: alta cautela; preferir goles, doble oportunidad o no apostar.
