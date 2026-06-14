# Cambios v8.7 - Histórico local SQLite

Esta versión agrega una base de datos local al proyecto para conservar los análisis realizados.

## Base de datos local

Se crea automáticamente en:

`data/analisis_historico.sqlite`

No requiere instalación adicional porque usa SQLite, incluido con Python.

## Qué guarda

Cada vez que ejecutas IA sobre partidos seleccionados, la app guarda una copia completa de cada análisis en histórico, incluyendo:

- Partido
- Fecha
- Predicción
- Probabilidades
- Entropía
- Factor suerte
- Nivel de equipos
- Favorito claro
- Conclusión de apuesta
- Errores si los hubo
- JSON completo del análisis

## Nueva pestaña

Se agregó una pestaña:

`Histórico de análisis`

Desde ahí puedes:

- Ver el último análisis por partido.
- Ver todos los análisis guardados.
- Filtrar por grupo, estado y equipo.
- Descargar histórico en Excel.
- Cargar los últimos análisis al dashboard.
- Borrar el histórico local con confirmación.

## Validación antes de volver a analizar

Si seleccionas un partido que ya tiene análisis guardado, la app te avisa en la barra lateral.

Para volver a analizarlo y gastar tokens de nuevo, debes activar:

`Volver a analizar partidos que ya existen en histórico`

Si no lo activas, la app no ejecuta la IA sobre esos partidos y te pide confirmación.
