# Cambios v8.12.1 - Fix _asset_base64

Corrige el error:

`NameError: name '_asset_base64' is not defined`

Se reemplazó `predictor/auth.py` completo, incluyendo la función `_asset_base64` y el login con header Dual.
