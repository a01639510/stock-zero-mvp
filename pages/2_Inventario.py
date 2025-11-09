# pages/2_Inventario.py
import streamlit as st
from modules.sidebar import mostrar_sidebar
from modules.components import inventario_basico_app

mostrar_sidebar()

st.title("Inventario")

if 'df_stock' not in st.session_state:
    st.warning("Sube stock en **Archivos**")
    st.stop()

df_stock = st.session_state.df_stock

# KPIs
col1, col2 = st.columns(2)
valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum()
with col1: st.metric("Valor Total", f"${valor:,.0f}")
with col2: st.metric("Productos", len(df_stock))

# Alertas
bajos = df_stock[df_stock['cantidad_recibida'] < 10]
if not bajos.empty:
    st.error(f"{len(bajos)} productos con stock bajo")
    st.dataframe(bajos[['producto', 'cantidad_recibida']])

inventario_basico_app()
