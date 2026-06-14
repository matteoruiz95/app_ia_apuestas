# Dónde pegar las API keys

Abre el archivo:

```text
API_KEYS_AQUI.env
```

Pega tus claves en estas líneas:

```env
OPENAI_API_KEY=PEGA_AQUI_TU_API_KEY_DE_OPENAI
OPENAI_MODEL=gpt-5-mini
API_FOOTBALL_KEY=PEGA_AQUI_TU_API_KEY_DE_API_FOOTBALL
THE_ODDS_API_KEY=PEGA_AQUI_TU_API_KEY_DE_THE_ODDS_API
THE_ODDS_SPORT_KEY=soccer_fifa_world_cup
```

Ejemplo de formato correcto:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxx
OPENAI_MODEL=gpt-5-mini
API_FOOTBALL_KEY=xxxxxxxx
THE_ODDS_API_KEY=xxxxxxxx
THE_ODDS_SPORT_KEY=soccer_fifa_world_cup
```

Después guarda el archivo y ejecuta:

```bash
python -m streamlit run app.py
```

## Recomendación

No pegues API keys dentro de `app.py`. El archivo `API_KEYS_AQUI.env` es el lugar correcto.

## Nota de seguridad

Si ya compartiste una key en un chat o correo, elimínala en el dashboard del proveedor y crea una nueva.
