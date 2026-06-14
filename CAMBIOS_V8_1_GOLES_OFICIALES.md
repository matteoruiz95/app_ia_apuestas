# Cambios v8.1 - Promedio de goles oficiales no amistosos

Esta versión NO aplica el cambio de Poisson del v9.

Se mantiene la lógica de la versión v8 y se agregan columnas calculadas con API-Football para partidos oficiales, excluyendo amistosos/friendlies:

- `home_official_matches_sample`
- `home_avg_goals_for_official`
- `home_avg_goals_against_official`
- `home_avg_total_goals_official`
- `home_official_competitions_sample`
- `away_official_matches_sample`
- `away_avg_goals_for_official`
- `away_avg_goals_against_official`
- `away_avg_total_goals_official`
- `away_official_competitions_sample`

La muestra objetivo es de los últimos 10 partidos oficiales disponibles por selección.
La app excluye ligas/torneos que contengan palabras como:
- Friendly
- Friendlies
- Amistoso
- Amistosos

Estos datos se agregan al contexto que recibe la IA y también salen en la tabla y en el Excel.

Importante:
- Para obtener estas columnas necesitas configurar `API_FOOTBALL_KEY`.
- Si API-Football no está configurado, las columnas quedan vacías.
- La app usa caché por equipo para no consultar la misma selección muchas veces durante la misma ejecución.
