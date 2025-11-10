# pages/1_Archivos.py
import streamlit as st
import pandas as pd
from modules.sidebar import mostrar_sidebar

st.title("Archivos")

col1, col2 = st.columns(2)
with col1:
    uploaded_ventas = st.file_uploader("Ventas CSV", type="csv")
with col2:
    uploaded_stock = st.file_uploader("Stock CSV", type="csv")

if uploaded_ventas:
    df = pd.read_csv(uploaded_ventas)
    st.session_state.df_ventas = df
    st.session_state.df_ventas_trazabilidad = df.copy()
    st.success("Ventas cargadas")

if uploaded_stock:
    df = pd.read_csv(uploaded_stock)
    st.session_state.df_stock = df
    st.success("Stock cargado")
