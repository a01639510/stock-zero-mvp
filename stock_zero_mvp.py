# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

# === VERIFICAR LOGIN ===
if "user" not in st.session_state:
    st.warning("Por favor, inicia sesión en la página de Login.")
    st.stop()

# === CONEXIÓN A SUPABASE ===
supabase_url = st.secrets["connections"]["supabase"]["url"]
supabase_key = st.secrets["connections"]["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

# === CARGAR DATOS DEL USUARIO ===
@st.cache_data(ttl=60)
def cargar_datos():
    ventas = supabase.table("ventas").select("*").eq("user_id", st.session_state.user_id).execute()
    stock = supabase.table("stock").select("*").eq("user_id", st.session_state.user_id).execute()
    return pd.DataFrame(ventas.data), pd.DataFrame(stock.data)

df_ventas, df_stock = cargar_datos()
st.session_state.df_ventas = df_ventas
st.session_state.df_stock = df_stock

# === SIDEBAR ===
with st.sidebar:
    st.image("https://via.placeholder.com/100", caption="Stock Zero")
    st.markdown("### Navegación")
    st.markdown("- [Home](stock_zero_mvp.py)")
    st.markdown("- [Login](pages/0_Login.py)")
    st.markdown("- [Archivos](pages/1_Archivos.py)")
    st.markdown("- [Inventario](pages/2_Inventario.py)")
    st.markdown("- [Análisis](pages/3_Analisis.py)")
    st.markdown("- [Productos](pages/4_Productos.py)")

# === TU DASHBOARD ===
st.title("Stock Zero")
st.header("Dashboard")

# ... tu código de gráficos y KPIs
