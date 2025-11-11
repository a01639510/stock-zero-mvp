# stock_zero_mvp.py
import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = st.secrets.get("supabase", {}).get("url") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Faltan SUPABASE_URL o SUPABASE_KEY. Crea .env o configura secrets.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicializar sesión
if "user" not in st.session_state:
    st.session_state.user = None
if "show_login" not in st.session_state:
    st.session_state.show_login = True

# Login / Signup
@st.experimental_dialog("Acceso", width="small")
def auth_dialog():
    tab1, tab2 = st.tabs(["Login", "Registro"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Contraseña", type="password", key="login_pwd")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                st.session_state.user = res.user
                st.session_state.show_login = False
                st.rerun()
            except:
                st.error("Error de credenciales")

    with tab2:
        name = st.text_input("Empresa", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        pwd = st.text_input("Contraseña (6+)", type="password", key="reg_pwd")
        if st.button("Crear"):
            if len(pwd) < 6:
                st.error("Mínimo 6 caracteres")
            else:
                try:
                    res = supabase.auth.sign_up({"email": email, "password": pwd})
                    supabase.table("clients").insert({
                        "id": res.user.id,
                        "name": name,
                        "plan": "free"
                    }).execute()
                    st.success("Cuenta creada. Verifica email.")
                except Exception as e:
                    st.error("Error al crear cuenta")

if st.session_state.show_login:
    auth_dialog()
    st.stop()

# Sidebar: Logout
with st.sidebar:
    st.write(f"**{st.session_state.user.email}**")
    if st.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.show_login = True
        st.rerun()

# App
st.title("StockZero - MVP Local")
st.write("¡Login exitoso! Sube tus datos.")

# Subir ventas
uploaded = st.file_uploader("Sube ventas (CSV)", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    df['user_id'] = st.session_state.user.id
    data = df.to_dict('records')
    supabase.table("ventas").insert(data).execute()
    st.success("Datos guardados en Supabase")
    st.dataframe(df)
