# Cambios v8.11 - Login simple sin scroll

Esta versión simplifica la pantalla de inicio/login.

## Cambios

- Se eliminó el bloque final de recomendaciones/configuración.
- Se eliminó el expander de ayuda de usuarios.
- La pantalla de login queda más compacta.
- Se ajustó el layout para que todo quepa en una sola pantalla.
- Se mantiene branding Dual blanco/morado.
- Se mantiene logo de Dual.
- Se oculta la barra lateral antes del login para evitar scroll y distracciones.

## Credenciales

Sigue funcionando igual:

```env
APP_USERNAME=admin
APP_PASSWORD_HASH=hash_sha256
```

O multiusuario:

```env
APP_USERS_JSON={"mateo":"hash_sha256_1","deiby":"hash_sha256_2"}
```
