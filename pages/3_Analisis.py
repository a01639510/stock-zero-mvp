# pages
import streamlit as st
from modules.analytics import analytics_app

st.title("Análisis")

if st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos**")
else:
    analytics_app()
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="Stock Zero")
    st.page_link("stock_zero_mvp.py", label="Home")
    st.page_link("pages/1_Archivos.py", label="Archivos")
    st.page_link("pages/2_Inventario.py", label="Inventario")
    st.page_link("pages/3_Analisis.py", label="Análisis")
    st.page_link("pages/4_Productos.py", label="Productos")
