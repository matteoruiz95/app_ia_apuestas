# Cambios v8.3 - Fallback robusto para respuesta vacía de IA

Esta versión corrige el error:

`Error IA: La IA devolvió respuesta vacía o incompleta incluso en fallback. Datos: {}`

Ahora el flujo tiene tres niveles:

1. Primer intento con Structured Outputs.
2. Segundo intento con prompt JSON simple.
3. Fallback determinístico basado en probabilidades de mercado ajustadas.

Si OpenAI devuelve `{}` o una respuesta vacía, la app ya no se detiene.
En su lugar, crea un análisis base usando las cuotas y deja trazabilidad con:

- `ai_fallback_used`
- `ai_fallback_reason`
- `openai_first_error`

También conserva:
- Factor entropía.
- Goles esperados.
- Factor suerte.
- Promedio de goles oficiales no amistosos.

Recomendación:
- Prueba 1 partido primero.
- Si ves `ai_fallback_used = True`, significa que OpenAI no devolvió texto útil y la app usó mercado como respaldo.
