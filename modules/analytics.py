# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data(ttl=3600, show_spinner="Procesando tu archivo...")
def cargar_datos_excel(_file):
    try:
        df = pd.read_excel(_file)
        # Normalizar columnas
        df.columns = df.columns.str.strip().str.lower()
        # Asegurar tipos
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        if 'ventas' in df.columns:
            df['ventas'] = pd.to_numeric(df['ventas'], errors='coerce')
        if 'stock' in df.columns:
            df['stock'] = pd.to_numeric(df['stock'], errors='coerce')
        return df.dropna(subset=['fecha'])
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame()
