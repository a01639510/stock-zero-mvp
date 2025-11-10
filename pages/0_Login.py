# pages/0_Login.py
import streamlit as st
from supabase import create_client, Client
import os

st.set_page_config(page_title="Login - Stock Zero")

# === CARGAR CREDENCIALES DESDE SECRETS ===
supabase_url = st.secrets["connections"]["supabase"]["url"]
supabase_key = st.secrets["connections"]["supabase"]["key"]

# === CONEXIÓN A SUPABASE ===
@st.cache_resource
def get_supabase() -> Client:
    return create_client(supabase_url, supabase_key)

supabase: Client = get_supabase()

st.title("Stock Zero - Login")

# === LOGIN / SIGNUP ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("Login")
    with st.form("login"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.form_submit_button("Iniciar Sesión"):
            try:
                data, _ = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = data.user
                st.session_state.user_id = data.user.id
                st.success("¡Login exitoso!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.subheader("Registro")
    with st.form("signup"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.form_submit_button("Crear Cuenta"):
            try:
                user = supabase.auth.sign_up({"email": email, "password": password})
                st.success("¡Cuenta creada! Revisa tu email para confirmar.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# === LOGOUT ===
if "user" in st.session_state:
    st.sidebar.success(f"Usuario: {st.session_state.user.email}")
    if st.sidebar.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
