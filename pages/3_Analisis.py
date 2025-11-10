# pages/3_Analisis.py
import streamlit as st
from modules.analytics import analytics_app

st.title("Análisis")

if 'df_ventas' not in st.session_state:
    st.warning("Sube datos en **Archivos**")
    st.stop()

if 'df_resultados' not in st.session_state:
    with st.spinner("Procesando..."):
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(
            st.session_state.df_ventas,
            st.session_state.get('df_stock', pd.DataFrame())
        )

analytics_app()
