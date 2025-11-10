# pages/3_Analisis.py
import streamlit as st
from modules.analytics import analytics_app

st.title("Análisis")

if 'df_ventas' not in st.session_state:
    st.warning("Sube datos en **Archivos**")
    st.stop()

# === RECALCULAR df_resultados SI NO EXISTE O FALTAN DATOS ===
if 'df_resultados' not in st.session_state or st.session_state.df_resultados is None:
    with st.spinner("Procesando datos..."):
        try:
            from modules.core_analysis import procesar_multiple_productos
            st.session_state.df_resultados = procesar_multiple_productos(
                st.session_state.df_ventas,
                st.session_state.get('df_stock', pd.DataFrame())
            )
        except Exception as e:
            st.error(f"Error procesando: {e}")
            st.stop()

# === EJECUTAR ANÁLISIS ===
analytics_app()
