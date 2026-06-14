# Cambios v8.5 - Favorito claro y apuesta al favorito

Esta versión mantiene la base v8.4 y agrega columnas para explicar explícitamente:

- Si hay favorito claro.
- Cuál es el favorito.
- Qué probabilidad tiene.
- Qué margen tiene frente al segundo escenario.
- Si la IA apuesta al favorito directo.
- Si la IA prefiere cubrir con gana/empata favorito.
- Si aun existiendo favorito claro, prefiere goles o no apostar.

Nuevas columnas:

- `clear_favorite`
- `favorite_side`
- `favorite_team`
- `favorite_probability`
- `favorite_margin_to_second`
- `favorite_strength`
- `favorite_conclusion`
- `favorite_double_chance_selection`
- `favorite_bet_recommendation`
- `ai_bet_vs_favorite`

Regla práctica de favorito claro:

- Debe ser local o visitante.
- Probabilidad IA >= 58%.
- Margen frente al segundo escenario >= 12 puntos.
- Entropía menor a 0.90.

Ejemplos de conclusión:

- `Favorito claro: Alemania... Apuesta al favorito directo: Alemania gana.`
- `Favorito claro: Alemania... Apuesta gana o empata favorito: Alemania gana o empata.`
- `Hay favorito claro, pero la IA prefiere mercado de goles.`
- `No hay favorito claro; la IA evita tomar favorito directo.`
