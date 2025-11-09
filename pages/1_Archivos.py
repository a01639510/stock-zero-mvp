
import streamlit as st
import pandas as pd

st.title("Archivos")

# === CARGAR ARCHIVOS ===
st.markdown("### Cargar Datos")
col1, col2 = st.columns(2)
with col1:
    uploaded_ventas = st.file_uploader("Ventas (CSV)", type="csv", key="upload_ventas")
with col2:
    uploaded_stock = st.file_uploader("Stock Actual (CSV)", type="csv", key="upload_stock")

if uploaded_ventas:
    df_ventas = pd.read_csv(uploaded_ventas)
    st.session_state.df_ventas = df_ventas
    st.success(f"Ventas: {len(df_ventas)} filas")
    st.dataframe(df_ventas.head())

if uploaded_stock:
    df_stock = pd.read_csv(uploaded_stock)
    st.session_state.df_stock = df_stock
    st.success(f"Stock: {len(df_stock)} filas")
    st.dataframe(df_stock.head())

# === EDITAR ARCHIVOS ===
st.markdown("### Editar Datos")
if st.session_state.get('df_ventas') is not None:
    st.markdown("#### Ventas")
    edited_ventas = st.data_editor(st.session_state.df_ventas, num_rows="dynamic")
    if st.button("Guardar Ventas"):
        st.session_state.df_ventas = edited_ventas
        st.success("Ventas guardadas en sesión")

if st.session_state.get('df_stock') is not None:
    st.markdown("#### Stock")
    edited_stock = st.data_editor(st.session_state.df_stock, num_rows="dynamic")
    if st.button("Guardar Stock"):
        st.session_state.df_stock = edited_stock
        st.success("Stock guardado en sesión")
