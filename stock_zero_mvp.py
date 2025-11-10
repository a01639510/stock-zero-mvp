# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from modules.analytics import analytics_app  # Importamos aquí

st.set_page_config(page_title="Stock Zero", layout="wide")


st.title("Stock Zero")
st.markdown("---")

st.header("Main Dashboard")

# === VERIFICAR DATOS ===
if 'df_ventas' not in st.session_state or st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos** para ver el dashboard.")
    st.stop()

df_ventas = st.session_state.df_ventas.copy()
df_stock = st.session_state.get('df_stock', pd.DataFrame())

# === CALCULAR RESULTADOS SI NO EXISTEN ===
if 'df_resultados' not in st.session_state:
    try:
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(
            st.session_state.df_ventas, 
            st.session_state.get('df_stock', pd.DataFrame())
        )
    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        st.stop()

# === GRÁFICO DE FLUJO (SIN UCL/LCL) ===
st.markdown("### Flujo de Inventario (Stock vs Ventas vs PR)")
# Al inicio del gráfico en stock_zero_mvp.py
if 'df_resultados' not in st.session_state:
    with st.spinner("Calculando análisis..."):
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(
            st.session_state.df_ventas,
            st.session_state.get('df_stock', pd.DataFrame())
        )
try:
    # Ejecutar analytics_app() para obtener df_sim y PR
    with st.container():
        analytics_app()  # Esto genera df_sim y PR en session_state

    df_sim = st.session_state.get('df_sim')
    PR = st.session_state.get('PR', 100)

    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    ventas_hist = df_ventas.groupby('fecha')['cantidad_vendida'].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=ventas_hist.index, y=ventas_hist.values, name="Ventas", marker_color="#4361EE"))
    
    if df_sim is not None and not df_sim.empty:
        fig.add_trace(go.Scatter(x=df_sim['fecha'], y=df_sim['stock'], mode='lines', name="Stock", line=dict(color="#4CC9F0", width=3)))
    
    fig.add_hline(y=PR, line_dash="dash", line_color="#FF6B6B", annotation_text=f"PR = {PR}")

    fig.update_layout(title="Flujo: Ventas + Stock + Punto de Reorden", height=500)
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
