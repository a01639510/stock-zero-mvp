# pages/3_Analisis.py
import streamlit as st
from modules.sidebar import mostrar_sidebar

mostrar_sidebar()

st.title("Análisis")

if 'df_ventas' not in st.session_state:
    st.warning("Sube datos en **Archivos**")
else:
    if 'df_resultados' not in st.session_state:
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(st.session_state.df_ventas, st.session_state.df_stock)
    
    from modules.analytics import analytics_app
    analytics_app()
