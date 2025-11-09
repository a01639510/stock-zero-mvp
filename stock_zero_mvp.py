# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Zero", layout="wide")

# === SIDEBAR SIMPLE (SOLO EN HOME) ===
with st.sidebar:
    st.image("https://via.placeholder.com/100", caption="Stock Zero")
    st.markdown("### Navegación")
    st.markdown("[Home](.)")
    st.markdown("[Archivos](pages/1_Archivos.py)")
    st.markdown("[Inventario](pages/2_Inventario.py)")
    st.markdown("[Análisis](pages/3_Analisis.py)")
    st.markdown("[Productos](pages/4_Productos.py)")

st.title("Stock Zero")
st.markdown("---")

st.header("Main Dashboard")

# === VERIFICAR DATOS (CON CHEQUEOS SEGUROS) ===
if 'df_ventas' not in st.session_state or st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos** para ver el dashboard.")
    st.stop()

df_ventas = st.session_state.df_ventas
df_stock = st.session_state.get('df_stock', pd.DataFrame())

# === GRÁFICO DE VENTAS ===
st.markdown("### Ventas Diarias (Control Chart)")
try:
    ultimos_30 = df_ventas[df_ventas['fecha'] >= df_ventas['fecha'].max() - timedelta(days=30)]
    ventas_diarias = ultimos_30.groupby('fecha')['cantidad_vendida'].sum()

    if len(ventas_diarias) == 0:
        st.info("No hay ventas en los últimos 30 días.")
    else:
        media = ventas_diarias.mean()
        desv = ventas_diarias.std()
        ucl = media + 3*desv
        lcl = max(media - 3*desv, 0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ventas_diarias.index, y=ventas_diarias.values, mode='lines+markers', name='Ventas'))
        fig.add_hline(y=media, line_dash="dash", line_color="green", annotation_text="Media")
        fig.add_hline(y=ucl, line_dash="dot", line_color="red", annotation_text="UCL")
        fig.add_hline(y=lcl, line_dash="dot", line_color="red", annotation_text="LCL")
        fig.update_layout(title="Control Chart de Ventas", height=400)
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error en gráfico: {e}")

# === KPIs (CON CHEQUEOS SEGUROS) ===
col1, col2, col3, col4 = st.columns(4)
with col1:
    hoy = ventas_diarias.iloc[-1] if 'ventas_diarias' in locals() and len(ventas_diarias) > 0 else 0
    st.metric("Ventas Hoy", f"{hoy:.0f}")
with col2:
    total = df_stock['cantidad_recibida'].sum() if not df_stock.empty else 0
    st.metric("Stock Total", f"{total:.0f}")
with col3:
    criticos = len(df_stock[df_stock['cantidad_recibida'] < 10]) if not df_stock.empty else 0
    st.metric("Productos Críticos", criticos)
with col4:
    costo = df_stock.get('costo_unitario', 10)
    valor = (df_stock['cantidad_recibida'] * costo).sum() if not df_stock.empty else 0
    st.metric("Valor Inventario", f"${valor:,.0f}")

st.success("Dashboard activo. Usa el menú lateral.")
