from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv


load_dotenv()
load_dotenv("API_KEYS_AQUI.env")

APP_ROOT = Path(__file__).resolve().parents[1]
DUAL_LOGO_PURPLE = APP_ROOT / "assets" / "dual_logo_purple.png"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return _sha256(password)


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _default_users() -> dict[str, str]:
    """
    Formato esperado:
    APP_USERS_JSON={"mateo":"<sha256>","admin":"<sha256>"}

    Alternativa simple:
    APP_USERNAME=admin
    APP_PASSWORD=1234

    Recomendado para producción:
    APP_PASSWORD_HASH=<sha256>
    """
    users_json = os.getenv("APP_USERS_JSON", "").strip()

    if users_json:
        parsed = _safe_json_loads(users_json)

        if isinstance(parsed, dict):
            return {
                str(username).strip(): str(password_hash).strip()
                for username, password_hash in parsed.items()
                if str(username).strip() and str(password_hash).strip()
            }

    username = os.getenv("APP_USERNAME", "admin").strip()
    password_hash = os.getenv("APP_PASSWORD_HASH", "").strip()
    password_plain = os.getenv("APP_PASSWORD", "").strip()

    if password_hash:
        return {username: password_hash}

    if password_plain:
        return {username: hash_password(password_plain)}

    # Usuario local de desarrollo. Cámbialo antes de publicar.
    return {"admin": hash_password("admin123")}


def authenticate_user(username: str, password: str) -> bool:
    username = str(username or "").strip()
    password = str(password or "")

    if not username or not password:
        return False

    users = _default_users()
    stored_hash = users.get(username)

    if not stored_hash:
        return False

    entered_hash = hash_password(password)

    return hmac.compare_digest(entered_hash, stored_hash)


def logout() -> None:
    st.session_state["authenticated"] = False
    st.session_state["auth_user"] = ""
    st.rerun()


def require_login() -> bool:
    """
    Renderiza pantalla de login y retorna True si el usuario ya inició sesión.

    Uso:
        if not require_login():
            return
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = ""

    if st.session_state.get("authenticated"):
        with st.sidebar:
            st.markdown("---")
            st.caption(f"Sesión iniciada: {st.session_state.get('auth_user', '')}")
            if st.button("Cerrar sesión", use_container_width=True):
                logout()

        return True

    left, center, right = st.columns([1, 1.4, 1])
    with center:
        if DUAL_LOGO_PURPLE.exists():
            st.image(str(DUAL_LOGO_PURPLE), use_container_width=True)

    st.markdown(
        """
        <div class="dual-login-wrap">
            <h2>Acceso privado</h2>
            <p>
                Ingresa tus credenciales para acceder al predictor, histórico y evaluación de análisis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)

    if submitted:
        if authenticate_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["auth_user"] = username.strip()
            st.success("Inicio de sesión correcto.")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    with st.expander("Ayuda para configurar usuarios", expanded=False):
        st.code(
            """
# Opción simple en API_KEYS_AQUI.env
APP_USERNAME=admin
APP_PASSWORD=tu_contraseña_segura

# Opción recomendada
APP_USERNAME=admin
APP_PASSWORD_HASH=sha256_de_tu_contraseña

# Opción multiusuario
APP_USERS_JSON={"mateo":"hash_sha256_1","deiby":"hash_sha256_2"}
            """.strip(),
            language="env",
        )

    return False
