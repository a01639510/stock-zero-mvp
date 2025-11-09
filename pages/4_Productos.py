# pages/4_Productos.py
import streamlit as st
from modules.sidebar import mostrar_sidebar

mostrar_sidebar()

st.title("Productos")

if 'df_ventas' not in st.session_state:
    st.info("Sube ventas")
else:
    productos = st.session_state.df_ventas['producto'].unique()
    producto = st.selectbox("Producto", productos)
    df = st.session_state.df_ventas[st.session_state.df_ventas['producto'] == producto]
    st.line_chart(df.groupby('fecha')['cantidad_vendida'].sum())
