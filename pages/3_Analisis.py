# pages
import streamlit as st
from modules.analytics import analytics_app

st.title("Análisis")

if st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos**")
else:
    analytics_app()
