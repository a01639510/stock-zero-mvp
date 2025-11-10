# pages/1_Archivos.py
import streamlit as st
import pandas as pd

st.title("Archivos")

col1, col2 = st.columns(2)
with col1:
    uploaded_ventas = st.file_uploader("Ventas CSV", type="csv", key="ventas")
with col2:
    uploaded_stock = st.file_uploader("Stock CSV", type="csv", key="stock")

if uploaded_ventas:
    df = pd.read_csv(uploaded_ventas)
    st.session_state.df_ventas = df
    st.session_state.df_ventas_trazabilidad = df.copy()
    st.success("Ventas cargadas")
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.rerun()

if uploaded_stock:
    df = pd.read_csv(uploaded_stock)
    st.session_state.df_stock = df
    st.success("Stock cargado")
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.rerun()

# === EDITAR ===
if 'df_ventas' in st.session_state:
    st.markdown("### Editar Ventas")
    edited = st.data_editor(st.session_state.df_ventas, num_rows="dynamic")
    if st.button("Guardar Ventas"):
        st.session_state.df_ventas = edited
        st.session_state.df_ventas_trazabilidad = edited
        if 'df_resultados' in st.session_state:
            del st.session_state.df_resultados
        st.rerun()

if 'df_stock' in st.session_state:
    st.markdown("### Editar Stock")
    edited = st.data_editor(st.session_state.df_stock, num_rows="dynamic")
    if st.button("Guardar Stock"):
        st.session_state.df_stock = edited
        if 'df_resultados' in st.session_state:
            del st.session_state.df_resultados
        st.rerun()
