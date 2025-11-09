# modules/
import streamlit as st

def mostrar_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/100", caption="Stock Zero", width=100)
        st.markdown("### Navegación")
        st.markdown("- [Home](stock_zero_mvp.py)")
        st.markdown("- [Archivos](pages/1_Archivos.py)")
        st.markdown("- [Inventario](pages/2_Inventario.py)")
        st.markdown("- [Análisis](pages/3_Analisis.py)")
        st.markdown("- [Productos](pages/4_Productos.py)")
