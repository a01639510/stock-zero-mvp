
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from supabase import create_client
# stock_zero_mvp.py
st.cache_data.clear()
st.cache_resource.clear()
# === CONFIGURACIÓN ===
st.set_page_config(page_title="Stock Zero", layout="wide")

# === VERIFICAR LOGIN ===
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor, inicia sesión en la página de **Login**.")
    st.stop()

# === CONEXIÓN A SUPABASE ===
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

# === CARGAR DATOS DEL USUARIO ===
@st.cache_data(ttl=60)
def load_user_data():
    try:
        ventas = supabase.table("ventas").select("*").eq("user_id", st.session_state.user_id).execute()
        stock = supabase.table("stock").select("*").eq("user_id", st.session_state.user_id).execute()
        return pd.DataFrame(ventas.data), pd.DataFrame(stock.data)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_ventas, df_stock = load_user_data()
st.session_state.df_ventas = df_ventas
st.session_state.df_stock = df_stock

# === SIDEBAR ===
with st.sidebar:
    st.image("https://via.placeholder.com/100", caption="Stock Zero", width=100)
    st.markdown("### Navegación")
    st.markdown("- [Home](stock_zero_mvp.py)")
    st.markdown("- [Login](pages/0_Login.py)")
    st.markdown("- [Archivos](pages/1_Archivos.py)")
    st.markdown("- [Inventario](pages/2_Inventario.py)")
    st.markdown("- [Análisis](pages/3_Analisis.py)")
    st.markdown("- [Productos](pages/4_Productos.py)")
    
    st.markdown("---")
    st.markdown("### Configuración")
    st.session_state.lead_time = st.slider("Lead Time (días)", 1, 30, 7)
    st.session_state.stock_seguridad = st.slider("Stock Seguridad (días)", 0, 10, 3)
    st.session_state.min_pedido = st.number_input("Mínimo por pedido", 1, 1000, 50)

    if st.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

# === TÍTULO ===
st.title("Stock Zero")
st.markdown("---")

# === DASHBOARD ===
st.header("Main Dashboard")

if df_ventas.empty:
    st.info("Sube datos en **Archivos** para ver el dashboard.")
else:
    # === GRÁFICO DE FLUJO ===
    st.markdown("### Flujo de Inventario")
    try:
        df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
        ventas_hist = df_ventas.groupby('fecha')['cantidad_vendida'].sum()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=ventas_hist.index, y=ventas_hist.values, name="Ventas", marker_color="#4361EE"))
        
        if not df_stock.empty:
            stock_total = df_stock['cantidad_recibida'].sum()
            fig.add_hline(y=stock_total, line_dash="dash", line_color="#4CC9F0", annotation_text="Stock Actual")

        PR = st.session_state.get('PR', 100)
        fig.add_hline(y=PR, line_dash="dot", line_color="#FF6B6B", annotation_text=f"PR = {PR}")

        fig.update_layout(title="Ventas + Stock + Punto de Reorden", height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error en gráfico: {e}")

    # === KPIs ===
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hoy = ventas_hist.iloc[-1] if len(ventas_hist) > 0 else 0
        st.metric("Ventas Hoy", f"{hoy:.0f}")
    with col2:
        total = df_stock['cantidad_recibida'].sum() if not df_stock.empty else 0
        st.metric("Stock Total", f"{total:.0f}")
    with col3:
        criticos = len(df_stock[df_stock['cantidad_recibida'] < 10]) if not df_stock.empty else 0
        st.metric("Productos Críticos", criticos)
    with col4:
        valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum() if not df_stock.empty else 0
        st.metric("Valor Inventario", f"${valor:,.0f}")

st.success("Dashboard activo.")
