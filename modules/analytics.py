# modules/analytics.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def mostrar_grafico_tiempo(df):
    """Gráfico principal: Ventas, Stock, Predicción, Proyección"""
    df = df.copy()
    df['prediccion_ventas'] = df['ventas'].rolling(window=7, min_periods=1).mean()
    df['ventas_acumuladas_futuras'] = df['prediccion_ventas'].cumsum().shift(-7).fillna(0)
    df['proyeccion_stock'] = df['stock'] - df['ventas_acumuladas_futuras']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['ventas'], mode='lines+markers', name='Ventas Reales',
                             line=dict(color='#4361EE', width=3)))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['stock'], mode='lines+markers', name='Stock Actual',
                             line=dict(color='#F72585', width=3)))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['prediccion_ventas'], mode='lines', name='Predicción (7 días)',
                             line=dict(dash='dot', color='#4CC9F0', width=2)))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['proyeccion_stock'], mode='lines', name='Proyección Stock',
                             line=dict(dash='dash', color='#7209B7', width=2)))

    fig.update_layout(
        title="Ventas, Stock y Proyecciones",
        xaxis_title="Fecha", yaxis_title="Cantidad",
        hovermode='x unified', template="plotly_white", height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=80, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def mostrar_estacionalidad(df):
    """Detecta patrones semanales"""
    df = df.copy()
    df['dia_semana'] = df['fecha'].dt.day_name()
    ventas_dia = df.groupby('dia_semana')['ventas'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ])
    variacion = ((ventas_dia.max() - ventas_dia.min()) / ventas_dia.mean()) * 100
    dia_pico = ventas_dia.idxmax()

    st.markdown("---")
    st.subheader("Tendencias Temporales Detectadas")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### Patrón Semanal")
        if variacion > 60:
            st.success(f"**Tendencia SEMANAL FUERTE**")
            st.write(f"**Pico**: {dia_pico} (+{ventas_dia[dia_pico]:.0f})")
        elif variacion > 30:
            st.info(f"**Tendencia moderada** ({variacion:.0f}% variación)")
        else:
            st.warning("**Sin patrón claro**")
    with col2:
        fig = px.bar(x=ventas_dia.index, y=ventas_dia.values,
                     labels={'x': 'Día', 'y': 'Ventas Promedio'},
                     color=ventas_dia.values, color_continuous_scale='Blues')
        fig.update_layout(showlegend=False, template="plotly_white", height=300, margin=dict(l=0,r=0,t=0,b=0))
        fig.update_traces(hovertemplate='<b>%{x}</b>: %{y:.0f}')
        st.plotly_chart(fig, use_container_width=True)

def analytics_app():
    """
    Página de Análisis: Usa datos de Optimización o Excel
    """
    st.title("Análisis de Ventas e Inventario")

    # === PRIORIDAD 1: Usar datos ya cargados en Optimización ===
    if st.session_state.df_ventas is not None:
        df_ventas = st.session_state.df_ventas.copy()
        st.success("Datos cargados desde **Optimización de Inventario**")
        
        # Convertir a formato esperado: fecha, ventas, stock
        df = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
        df = df.rename(columns={'cantidad_vendida': 'ventas'})
        
        # Si hay stock, unirlo
        if st.session_state.df_stock is not None:
            df_stock = st.session_state.df_stock.groupby('fecha')['cantidad_recibida'].sum().reset_index()
            df = df.merge(df_stock, on='fecha', how='left').fillna(0)
            df['stock'] = df['cantidad_recibida'].cumsum()
        else:
            df['stock'] = 500  # valor por defecto

        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values('fecha').reset_index(drop=True)

        st.info(f"Mostrando {len(df)} días | Ventas totales: {df['ventas'].sum():.0f}")
        
        mostrar_grafico_tiempo(df)
        mostrar_estacionalidad(df)
        return

    # === PRIORIDAD 2: Subir Excel (solo si no hay datos) ===
    st.markdown("**O sube un Excel con columnas: `fecha`, `ventas`, `stock`**")
    uploaded_file = st.file_uploader("Seleccionar archivo Excel", type=['xlsx', 'xls'], key="analytics_uploader")

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()
        
        required = ['fecha', 'ventas', 'stock']
        if not all(col in df.columns for col in required):
            st.error(f"Faltan columnas: {set(required) - set(df.columns)}")
            return

        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha']).sort_values('fecha').reset_index(drop=True)

        if df.empty:
            st.error("No hay datos válidos.")
            return

        st.success(f"{len(df)} registros cargados")
        mostrar_grafico_tiempo(df)
        mostrar_estacionalidad(df)

    else:
        st.info("Sube un archivo o carga datos en **Optimización de Inventario**")
        st.markdown("""
        ### Ejemplo de Excel:
        | fecha      | ventas | stock |
        |------------|--------|-------|
        | 2025-01-01 | 120    | 500   |
        | 2025-01-02 | 135    | 480   |
        """)
