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
