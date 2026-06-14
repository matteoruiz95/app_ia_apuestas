# Cambios v8.2 - Factor entropía

Esta versión mantiene la base v8.1:
- Goles esperados y factor suerte.
- Promedio de goles en partidos oficiales, excluyendo amistosos.
- No aplica la modificación v9 de Poisson.

Se agregan nuevas columnas:

- `entropy_score`
- `entropy_factor`
- `entropy_explanation`

## Qué significa

`entropy_score` mide qué tan repartidas están las probabilidades entre local, empate y visitante.

Escala:
- 0.00 = muy predecible, un resultado domina.
- 1.00 = máxima incertidumbre, probabilidades muy repartidas.

## Clasificación

- `Bajo`: favorito más claro.
- `Medio`: hay favorito, pero empate o sorpresa tienen peso.
- `Alto`: partido abierto, difícil de predecir.

## Fórmula

Se usa entropía de Shannon normalizada:

H = -sum(p * ln(p)) / ln(3)

Donde p son las probabilidades IA normalizadas de local, empate y visitante.
