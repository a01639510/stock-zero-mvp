# pages/0_Login.py
import streamlit as st
from streamlit_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Login - Stock Zero")

st.title("Login - Stock Zero")

# === CONEXIÓN ===
conn = st.connection("supabase", type=SupabaseConnection)

# === FORM DE LOGIN ===
with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.form_submit_button("Login"):
            try:
                # Login con Supabase
                response = conn.auth.sign_in_with_password({"email": email, "password": password})
                if response.user:
                    st.session_state.user = response.user
                    st.session_state.user_id = response.user.id
                    st.success("¡Login exitoso! Redirigiendo...")
                    st.rerun()
                else:
                    st.error("Email o password incorrecto")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.form_submit_button("Sign Up"):
            try:
                # Registro
                response = conn.auth.sign_up({"email": email, "password": password})
                if response.user:
                    st.success("¡Usuario creado! Verifica tu email.")
                else:
                    st.error("Error al crear usuario")
            except Exception as e:
                st.error(f"Error: {e}")

# === SI YA ESTÁ LOGUEADO ===
if "user" in st.session_state:
    st.success(f"Bienvenido, {st.session_state.user.email}!")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.df_ventas = None
        st.session_state.df_stock = None
        st.session_state.df_resultados = None
        st.rerun()
