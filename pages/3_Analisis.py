# pages/3_Analisis.py
import streamlit as st

# === SIDEBAR ===
with st.sidebar:
    st.page_link("stock_zero_mvp.py", label="Home", icon="🏠")
    st.page_link("pages/1_Archivos.py", label="Archivos", icon="📁")
    st.page_link("pages/2_Inventario.py", label="Inventario", icon="📦")
    st.page_link("pages/3_Analisis.py", label="Análisis", icon="📊")
    st.page_link("pages/4_Productos.py", label="Productos", icon="🛒")

st.title("Análisis")

if st.session_state.get('df_ventas') is None:
    st.warning("Sube datos en **Archivos**")
else:
    # CALCULAR RESULTADOS SI NO EXISTEN
    if 'df_resultados' not in st.session_state or st.session_state.df_resultados is None:
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(st.session_state.df_ventas, 7, 3, 7)
    
    from modules.analytics import analytics_app
    analytics_app()
