# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Zero", layout="wide")

# === TÍTULO ===
st.title("Stock Zero")
st.markdown("---")

# === DASHBOARD ===
st.header("Main Dashboard")

# === VERIFICAR DATOS ===
if st.session_state.get('df_ventas') is None:
    st.warning("Sube datos en **Archivos** para ver el dashboard.")
    st.stop()

df_ventas = st.session_state.df_ventas_trazabilidad or st.session_state.df_ventas
df_stock = st.session_state.df_stock

# === GRÁFICO DE VENTAS (ÚLTIMOS 30 DÍAS) ===
st.markdown("### Ventas Diarias (Control Chart)")
ultimos_30 = df_ventas[df_ventas['fecha'] >= df_ventas['fecha'].max() - timedelta(days=30)]
ventas_diarias = ultimos_30.groupby('fecha')['cantidad_vendida'].sum()

media = ventas_diarias.mean()
desv = ventas_diarias.std()
ucl = media + 3*desv
lcl = media - 3*desv

fig = go.Figure()
fig.add_trace(go.Scatter(x=ventas_diarias.index, y=ventas_diarias.values, mode='lines+markers', name='Ventas'))
fig.add_hline(y=media, line_dash="dash", line_color="green", annotation_text="Media")
fig.add_hline(y=ucl, line_dash="dot", line_color="red", annotation_text="UCL")
fig.add_hline(y=lcl, line_dash="dot", line_color="red", annotation_text="LCL")
fig.update_layout(title="Control Chart de Ventas", height=400)
st.plotly_chart(fig, width='stretch')

# === KPIs ===
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Ventas Hoy", ventas_diarias.iloc[-1] if len(ventas_diarias) > 0 else 0)
with col2: st.metric("Stock Total", df_stock['cantidad'].sum() if df_stock is not None else 0)
with col3: st.metric("Productos Críticos", len(df_stock[df_stock['cantidad'] < 10]) if df_stock is not None else 0)
with col4: st.metric("Valor Inventario", f"${(df_stock['cantidad'] * df_stock.get('costo_unitario', 10)).sum():,.0f}" if df_stock is not None else "$0")

st.success("Dashboard activo. Usa el menú lateral.")
