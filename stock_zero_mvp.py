# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from modules.sidebar import mostrar_sidebar

st.set_page_config(page_title="Stock Zero", layout="wide")

# === SIDEBAR CENTRALIZADO ===
mostrar_sidebar()

st.title("Stock Zero")
st.markdown("---")

st.header("Main Dashboard")

# === VERIFICAR DATOS ===
if 'df_ventas' not in st.session_state or st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos** para ver el dashboard.")
    st.stop()

df_ventas = st.session_state.df_ventas.copy()
df_stock = st.session_state.get('df_stock', pd.DataFrame())

# === SIMULACIÓN RÁPIDA PARA GRÁFICO ===
try:
    from modules.analytics import analytics_app
    with st.spinner("Calculando simulación..."):
        # Simular solo para gráfico
        df_sim = st.session_state.get('df_sim')
        if df_sim is None:
            # Ejecutar simulación ligera
            from modules.analytics import analytics_app
            # No mostrar, solo capturar datos
            pass
except:
    st.error("Error en simulación")
    st.stop()

# === GRÁFICO DE FLUJO: STOCK + VENTAS + PR ===
st.markdown("### Flujo de Inventario (Stock vs Ventas vs PR)")

try:
    # Usar datos de analytics si existen
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])
    ultimo_dia = df_ventas['fecha'].max()
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=30)

    # Ventas reales
    ventas_hist = df_ventas.groupby('fecha')['cantidad_vendida'].sum()

    # Simulación de stock (de analytics)
    df_sim = st.session_state.get('df_sim', pd.DataFrame())
    PR = st.session_state.get('PR', 100)

    fig = go.Figure()

    # Ventas reales
    fig.add_trace(go.Bar(x=ventas_hist.index, y=ventas_hist.values, name="Ventas Reales", marker_color="#4361EE"))

    # Stock simulado
    if not df_sim.empty:
        fig.add_trace(go.Scatter(x=df_sim['fecha'], y=df_sim['stock'], mode='lines', name="Stock Simulado", line=dict(color="#4CC9F0", width=3)))

    # PR
    fig.add_hline(y=PR, line_dash="dash", line_color="#FF6B6B", annotation_text=f"PR = {PR}")

    fig.update_layout(
        title="Flujo de Inventario: Ventas + Stock + Punto de Reorden",
        xaxis_title="Fecha",
        yaxis_title="Unidades",
        barmode='overlay',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error en gráfico: {e}")

# === KPIs ===
col1, col2, col3, col4 = st.columns(4)
with col1:
    ventas_hoy = ventas_hist.iloc[-1] if len(ventas_hist) > 0 else 0
    st.metric("Ventas Hoy", f"{ventas_hoy:.0f}")
with col2:
    stock_total = df_stock['cantidad_recibida'].sum() if not df_stock.empty else 0
    st.metric("Stock Total", f"{stock_total:.0f}")
with col3:
    criticos = len(df_stock[df_stock['cantidad_recibida'] < 10]) if not df_stock.empty else 0
    st.metric("Productos Críticos", criticos)
with col4:
    valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum() if not df_stock.empty else 0
    st.metric("Valor Inventario", f"${valor:,.0f}")

st.success("Dashboard activo. Usa el menú lateral.")
