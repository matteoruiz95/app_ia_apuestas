from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv


load_dotenv()
load_dotenv("API_KEYS_AQUI.env")


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
    Login simple Dual:
    - Logo con st.image para evitar HTML/base64 como texto.
    - Usuario, contraseña y botón.
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

    st.markdown(
        """
        <style>
            header,
            footer,
            div[data-testid="stToolbar"],
            [data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }

            .stApp {
                background:
                    radial-gradient(circle at 50% 0%, rgba(121, 42, 244, 0.14), transparent 34%),
                    linear-gradient(180deg, #ffffff 0%, #faf7ff 48%, #ffffff 100%);
            }

            .block-container {
                max-width: 420px !important;
                padding-top: 12vh !important;
                padding-left: 1.2rem !important;
                padding-right: 1.2rem !important;
                padding-bottom: 0 !important;
            }

            div[data-testid="stImage"] {
                display: flex;
                justify-content: center;
                margin-bottom: 34px;
            }

            div[data-testid="stImage"] img {
                max-width: 210px !important;
                height: auto !important;
            }

            div[data-testid="stForm"] {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }

            div[data-testid="stTextInput"] {
                margin-bottom: 8px !important;
            }

            div[data-testid="stTextInput"] label {
                color: #24113f !important;
                font-size: 14px !important;
                font-weight: 700 !important;
            }

            div[data-testid="stTextInput"] input {
                min-height: 46px !important;
                border-radius: 14px !important;
                border: 1px solid rgba(121, 42, 244, 0.28) !important;
                background: #ffffff !important;
                color: #24113f !important;
                box-shadow: 0 10px 28px rgba(121, 42, 244, 0.08) !important;
            }

            div[data-testid="stTextInput"] input:focus {
                border: 1px solid #792af4 !important;
                box-shadow: 0 0 0 3px rgba(121, 42, 244, 0.12) !important;
            }

            div[data-testid="stFormSubmitButton"] button {
                min-height: 46px !important;
                border-radius: 14px !important;
                background: #792af4 !important;
                border: 1px solid #792af4 !important;
                color: #ffffff !important;
                font-weight: 800 !important;
                margin-top: 10px !important;
                box-shadow: 0 14px 34px rgba(121, 42, 244, 0.25) !important;
            }

            div[data-testid="stFormSubmitButton"] button:hover {
                background: #6421d4 !important;
                border-color: #6421d4 !important;
            }

            div[data-testid="stAlert"] {
                border-radius: 14px !important;
                margin-top: 14px !important;
            }

            @media (max-height: 720px) {
                .block-container {
                    padding-top: 7vh !important;
                    max-width: 390px !important;
                }

                div[data-testid="stImage"] {
                    margin-bottom: 22px;
                }

                div[data-testid="stImage"] img {
                    max-width: 170px !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.image("assets/dual_logo_purple.png", width=210)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)

    if submitted:
        if authenticate_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["auth_user"] = username.strip()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    return False
