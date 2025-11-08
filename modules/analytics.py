# modules/analytics.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

@st.cache_data(ttl=3600, show_spinner="Procesando tu archivo Excel...")
def cargar_datos_excel(_file):
    """
    Carga y limpia el Excel subido por el usuario.
    """
    try:
        df = pd.read_excel(_file)
        df.columns = df.columns.str.strip().str.lower()

        # Validar columnas mínimas
        required = ['fecha', 'ventas', 'stock']
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"Columnas faltantes en el Excel: {missing}")
            st.info("Asegúrate de tener: `fecha`, `ventas`, `stock`")
            return pd.DataFrame()

        # Convertir tipos
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['ventas'] = pd.to_numeric(df['ventas'], errors='coerce')
        df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

        # Eliminar filas con fecha inválida
        df = df.dropna(subset=['fecha'])

        if df.empty:
            st.error("No hay datos válidos después de limpiar.")
            return pd.DataFrame()

        return df.sort_values('fecha').reset_index(drop=True)

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame()


def mostrar_grafico_tiempo(df):
    """
    Gráfico principal: Ventas, Stock, Predicción, Proyección
    """
    df = df.copy()
    df['prediccion_ventas'] = df['ventas'].rolling(window=7, min_periods=1).mean()
    
    # Proyección de stock: stock actual - ventas acumuladas futuras (predicción)
    df['ventas_acumuladas_futuras'] = df['prediccion_ventas'].cumsum().shift(-7).fillna(0)
    df['proyeccion_stock'] = df['stock'] - df['ventas_acumuladas_futuras']

    fig = go.Figure()

    # Ventas reales
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ventas'],
        mode='lines+markers',
        name='Ventas Reales',
        line=dict(color='#4361EE', width=3),
        hovertemplate='<b>Ventas</b>: %{y}<br><b>Fecha</b>: %{x}<extra></extra>'
    ))

    # Stock actual
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['stock'],
        mode='lines+markers',
        name='Stock Actual',
        line=dict(color='#F72585', width=3),
        hovertemplate='<b>Stock</b>: %{y}<br><b>Fecha</b>: %{x}<extra></extra>'
    ))

    # Predicción (media móvil)
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['prediccion_ventas'],
        mode='lines',
        name='Predicción (7 días)',
        line=dict(dash='dot', color='#4CC9F0', width=2),
        hovertemplate='<b>Predicción</b>: %{y:.1f}<extra></extra>'
    ))

    # Proyección de stock
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['proyeccion_stock'],
        mode='lines',
        name='Proyección Stock',
        line=dict(dash='dash', color='#7209B7', width=2),
        hovertemplate='<b>Proyección</b>: %{y:.0f}<extra></extra>'
    ))

    fig.update_layout(
        title="📈 Ventas, Stock y Proyecciones",
        xaxis_title="Fecha",
        yaxis_title="Cantidad",
        hovermode='x unified',
        template="plotly_white",
        height=520,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=80, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


def mostrar_estacionalidad(df):
    """
    Detecta patrones semanales y muestra resumen + gráfico
    """
    df = df.copy()
    df['dia_semana'] = df['fecha'].dt.day_name()
    df['dia_num'] = df['fecha'].dt.weekday  # 0=Lunes

    # Ventas promedio por día
    ventas_dia = df.groupby('dia_semana')['ventas'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ])

    variacion = ((ventas_dia.max() - ventas_dia.min()) / ventas_dia.mean()) * 100
    dia_pico = ventas_dia.idxmax()
    dia_bajo = ventas_dia.idxmin()

    st.markdown("---")
    st.subheader("🔄 Tendencias Temporales Detectadas")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📊 Patrón Semanal")
        if variacion > 60:
            st.success(f"**Tendencia SEMANAL FUERTE**")
            st.write(f"**Pico**: {dia_pico} (+{ventas_dia[dia_pico]:.0f})")
            st.write(f"**Valle**: {dia_bajo}")
        elif variacion > 30:
            st.info(f"**Tendencia semanal moderada** ({variacion:.0f}% variación)")
        else:
            st.warning("**Sin patrón claro** – Ventas estables")

    with col2:
        fig = px.bar(
            x=ventas_dia.index,
            y=ventas_dia.values,
            labels={'x': 'Día', 'y': 'Ventas Promedio'},
            color=ventas_dia.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            showlegend=False,
            template="plotly_white",
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        fig.update_traces(hovertemplate='<b>%{x}</b>: %{y:.0f}')
        st.plotly_chart(fig, use_container_width=True)


def analytics_app():
    """
    Página principal de Análisis
    """
    st.title("📊 Análisis de Ventas e Inventario")
    st.markdown("Sube tu Excel con columnas: **fecha**, **ventas**, **stock**")

    uploaded_file = st.file_uploader(
        "Seleccionar archivo Excel",
        type=['xlsx', 'xls'],
        key="file_uploader_analytics"
    )

    if uploaded_file is not None:
        # Forzar recarga con nombre + tamaño
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if 'last_file_key' not in st.session_state or st.session_state['last_file_key'] != file_key:
            st.session_state['last_file_key'] = file_key
            if 'df_analytics' in st.session_state:
                del st.session_state['df_analytics']

        df = cargar_datos_excel(uploaded_file)

        if not df.empty:
            st.session_state['df_analytics'] = df
            st.success(f"✅ **{len(df)} registros cargados** – Última fecha: {df['fecha'].max().strftime('%Y-%m-%d')}")
            
            mostrar_grafico_tiempo(df)
            mostrar_estacionalidad(df)

        else:
            st.error("No se pudieron cargar los datos. Revisa el formato.")
    else:
        if 'df_analytics' in st.session_state:
            df = st.session_state['df_analytics']
            st.info("Usando datos anteriores. Sube un nuevo archivo para actualizar.")
            mostrar_grafico_tiempo(df)
            mostrar_estacionalidad(df)
        else:
            st.info("Esperando archivo Excel...")
            st.markdown("""
            ### Ejemplo de formato:
            | fecha      | ventas | stock |
            |------------|--------|-------|
            | 2025-01-01 | 120    | 500   |
            | 2025-01-02 | 135    | 480   |
            """)
