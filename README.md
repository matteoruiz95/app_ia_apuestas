# Mundial 2026 — Predictor IA fase de grupos

App web en Python/Streamlit para analizar partidos del Mundial 2026 con:

- cuotas base 1X2;
- probabilidad implícita ajustada sin margen de la casa;
- análisis IA con OpenAI y búsqueda web;
- contexto opcional de API-Football;
- cuotas opcionales de The Odds API;
- gráficos interactivos;
- simulación Monte Carlo;
- descarga de resultados en Excel.

> Importante: esto no garantiza resultados. Es un sistema probabilístico de apoyo al análisis.

---

## 1. Requisitos

Instala Python 3.11 o superior.

Luego abre la terminal dentro de esta carpeta y ejecuta:

```bash
python -m pip install -r requirements.txt
```

En Windows también puedes ejecutar:

```bash
run.bat
```

En Mac/Linux:

```bash
chmod +x run.sh
./run.sh
```

---

## 2. Crear las API Keys

### A. OpenAI

1. Entra a https://platform.openai.com/
2. Crea una cuenta o inicia sesión.
3. Ve a **API keys**.
4. Crea una nueva key.
5. Copia la key.
6. Agrega saldo/billing para poder ejecutar el modelo.

La app usa la Responses API de OpenAI y opcionalmente `web_search_preview` para buscar información actualizada.

Modelo recomendado para cuidar presupuesto:

```env
OPENAI_MODEL=gpt-5-mini
```

Modelo más fuerte, si tu cuenta lo tiene habilitado:

```env
OPENAI_MODEL=gpt-5.5
```

### B. API-Football

1. Entra a https://www.api-football.com/
2. Crea cuenta.
3. Elige plan. Para tu presupuesto, el plan Pro de 1 mes suele ser suficiente.
4. Copia tu API key.

La app usa API-Football como contexto adicional. Si no la configuras, la app sigue funcionando con cuotas + OpenAI.

### C. The Odds API

1. Entra a https://the-odds-api.com/
2. Crea cuenta.
3. Usa el plan gratis para una primera ejecución.
4. Copia tu API key.

La app intenta consultar cuotas actuales. Si no encuentra el partido, mantiene las cuotas base cargadas.

---

## 3. Configurar variables de entorno

Copia el archivo:

```bash
.env.example
```

y renómbralo como:

```bash
.env
```

Completa tus claves:

```env
OPENAI_API_KEY=tu_api_key_de_openai
OPENAI_MODEL=gpt-5-mini
API_FOOTBALL_KEY=tu_api_key_de_api_football
THE_ODDS_API_KEY=tu_api_key_de_the_odds_api
THE_ODDS_SPORT_KEY=soccer_fifa_world_cup
```

También puedes pegar las claves directamente en la barra lateral de la app.

---

## 4. Ejecutar la app

Desde la carpeta del proyecto:

```bash
python -m streamlit run app.py
```

Streamlit abrirá algo similar a:

```text
http://localhost:8501
```

---

## 5. Cómo usarla

1. Abre la app.
2. En la barra lateral pega tu `OPENAI_API_KEY`.
3. Activa o desactiva búsqueda web.
4. Selecciona el número de partidos a analizar con IA.
   - Para prueba: 3 a 5 partidos.
   - Para cuidar presupuesto: 12 a 20 partidos.
   - Para fase de grupos completa: 72 partidos.
5. Haz clic en **Ejecutar IA**.
6. Revisa los gráficos.
7. Ejecuta **Monte Carlo** si quieres simular escenarios.
8. Descarga el Excel con **Descargar Excel**.

---

## 6. Criterios de análisis

La app combina:

### A. Mercado / cuotas

Convierte cuotas decimales a probabilidad:

```text
probabilidad bruta = 1 / cuota
```

Luego quita el margen de la casa:

```text
probabilidad ajustada = probabilidad bruta / suma de probabilidades brutas
```

### B. IA con búsqueda web

La IA busca y analiza:

- ranking FIFA/ELO reciente;
- forma reciente;
- jugadores clave;
- lesiones o sanciones;
- historial relevante;
- fortaleza ofensiva/defensiva;
- contexto del grupo;
- riesgo de empate o sorpresa.

### C. Fórmula final

Por defecto:

```text
70% mercado + 30% IA
```

Puedes cambiar los pesos desde la barra lateral.

---

## 7. Control de presupuesto

Para no pasarte de $200.000 COP:

- usa `gpt-5-mini`;
- primero prueba con 3 partidos;
- luego sube a 12 o 20;
- ejecuta los 72 solo cuando ya esté todo configurado;
- desactiva búsqueda web si quieres bajar costo;
- usa The Odds API gratis;
- usa API-Football solo si de verdad vas a ejecutar la corrida completa.

---

## 8. Estructura del proyecto

```text
worldcup_ai_predictor_app/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .env.example
├─ run.bat
├─ run.sh
├─ .streamlit/
│  └─ config.toml
└─ predictor/
   ├─ data.py
   ├─ odds_math.py
   ├─ api_clients.py
   ├─ ai_runner.py
   ├─ export.py
   └─ __init__.py
```

---

## 9. Notas importantes

- Si no tienes API keys, la app funciona en modo base con cuotas precargadas.
- Si OpenAI devuelve error de modelo, cambia el modelo a `gpt-4.1-mini` o al modelo que tengas disponible.
- Las cuotas base deben actualizarse antes de una ejecución real.
- No uses esto como garantía de apuesta.


## Mejoras v4

Esta versión corrige los errores por columnas duplicadas y agrega selección manual de partidos.

### Nuevas funciones

- Seleccionar manualmente qué partidos analizar con IA.
- Analizar automáticamente los top favoritos por cuota.
- Analizar todos los 72 partidos si se requiere.
- Dashboard enfocado en partidos analizados.
- Excel por defecto con **solo partidos analizados con IA**.
- Corrección de errores:
  - `At least one sheet must be visible`
  - `cannot import name to_display_percent`
  - `arg must be a list, tuple, 1-d array, or Series`
  - `cannot convert the series to int`

### Uso recomendado con presupuesto bajo

1. Modelo: `gpt-5-mini`.
2. Modo: `Selección manual`.
3. Selecciona 3 a 5 partidos.
4. Ejecuta IA.
5. Descarga Excel.
6. Si todo funciona, sube a 12, 20 y luego 72 partidos.

### Exportación Excel

La opción **Excel solo partidos analizados** viene activada por defecto. Esto significa que el archivo descargado no incluirá partidos que solo tengan análisis base por cuota.


## Configuración rápida de API keys

Esta versión incluye un archivo visible llamado:

```text
API_KEYS_AQUI.env
```

Abre ese archivo y pega tus claves. La app lo lee automáticamente junto con `.env`.

No pegues claves directamente dentro del código.
