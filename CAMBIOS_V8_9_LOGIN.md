# Cambios v8.9 - Inicio de sesión

Esta versión agrega pantalla de login antes de entrar al predictor.

## Archivos nuevos

- `predictor/auth.py`
- `generar_hash_password.py`

## Usuario local por defecto

Si no configuras nada, la app entra con:

- Usuario: `admin`
- Contraseña: `admin123`

Cámbialo antes de publicar.

## Configuración simple

En `API_KEYS_AQUI.env`:

```env
APP_USERNAME=admin
APP_PASSWORD=tu_contraseña_segura
```

## Configuración recomendada con hash

1. Ejecuta:

```bash
python generar_hash_password.py
```

2. Escribe la contraseña.
3. Copia el hash generado.
4. En `API_KEYS_AQUI.env`:

```env
APP_USERNAME=admin
APP_PASSWORD_HASH=pega_aqui_el_hash_sha256
```

## Multiusuario

```env
APP_USERS_JSON={"mateo":"hash_sha256_1","deiby":"hash_sha256_2"}
```

## Para Vercel

Cuando publiques, configura estas variables en el panel de variables de entorno:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `API_FOOTBALL_KEY`
- `THE_ODDS_API_KEY`
- `APP_USERNAME`
- `APP_PASSWORD_HASH`

Nota importante:
SQLite funciona bien localmente. Para una app multiusuario publicada, el histórico local en SQLite puede no ser ideal si el hosting no conserva archivos entre ejecuciones. Si varias personas la van a usar en producción, lo recomendable después será migrar histórico y evaluaciones a una base externa como Supabase/PostgreSQL.
