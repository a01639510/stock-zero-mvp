# pages/
import streamlit as st
import pandas as pd

st.title("Productos")

if st.session_state.df_ventas is None:
    st.info("Sube ventas para ver productos")
else:
    productos = st.session_state.df_ventas['producto'].unique()
    producto = st.selectbox("Seleccionar Producto", productos)
    
    df_prod = st.session_state.df_ventas[st.session_state.df_ventas['producto'] == producto]
    st.metric("Ventas Totales", df_prod['cantidad_vendida'].sum())
    st.line_chart(df_prod.groupby('fecha')['cantidad_vendida'].sum())
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="Stock Zero")
    st.page_link("stock_zero_mvp.py", label="Home")
    st.page_link("pages/1_Archivos.py", label="Archivos")
    st.page_link("pages/2_Inventario.py", label="Inventario")
    st.page_link("pages/3_Analisis.py", label="Análisis")
    st.page_link("pages/4_Productos.py", label="Productos")
