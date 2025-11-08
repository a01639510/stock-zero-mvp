# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PALETA AZUL
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4CC9F0"
COLOR_STOCK_HIST = "#7209B7"
COLOR_STOCK_FUT = "#4CC9F0"
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"

def analytics_app():
    st.title("Simulación Realista de Inventario")
    st.markdown("**Reorden automático cuando stock ≤ PR (en unidades)**")

    # === 1. DATOS ===
    if st.session_state.df_ventas is None:
        st.warning("Sube datos en **Optimización**")
        return

    df_ventas = st.session_state.df_ventas.copy()
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    df_ventas = df_ventas.dropna(subset=['fecha']).sort_values('fecha')
    df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()

    # === 2. FILTRO TEMPORAL ===
    ultimo_dia = df_ventas['fecha'].max()
    opciones_filtro = {
        "Última semana": 7,
        "Último mes": 30,
        "Últimos 3 meses": 90,
        "Todo el historial": 9999
    }
    filtro = st.selectbox("Período", list(opciones_filtro.keys()))
    dias = opciones_filtro[filtro]
    fecha_inicio = ultimo_dia - timedelta(days=min(dias, 9999))
    df_filtrado = df_ventas[df_ventas['fecha'] >= fecha_inicio]

    # === 3. PRODUCTO ===
    productos = df_filtrado['producto'].unique()
    if len(productos) == 0:
        st.error("No hay productos")
        return
    producto = st.selectbox("Producto", sorted(productos))

    # === 4. VENTAS DEL PRODUCTO ===
    ventas_prod = df_filtrado[df_filtrado['producto'] == producto].copy()
    ventas_prod['dia_semana'] = ventas_prod['fecha'].dt.day_name()

    # === 5. ESTACIONALIDAD: VENTA PROMEDIO POR DÍA DE SEMANA (EN UNIDADES) ===
    venta_por_dia = ventas_prod.groupby('dia_semana')['cantidad_vendida'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    # Si pocos datos → estacionalidad realista
    if len(ventas_prod) < 14:
        base = venta_por_dia.mean() or 10
        venta_por_dia = pd.Series({
            'Monday': base * 0.8, 'Tuesday': base * 0.9, 'Wednesday': base * 0.95,
            'Thursday': base * 1.0, 'Friday': base * 1.2, 'Saturday': base * 1.3, 'Sunday': base * 1.1
        })

    venta_promedio_diaria = venta_por_dia.mean()

    # === 6. PR EN CANTIDAD (3 DÍAS DE VENTA PROMEDIO) ===
    PR = venta_promedio_diaria * 3  # ← EN UNIDADES, NO DÍAS
    PR = max(PR, 1)  # Mínimo 1

    # === 7. CANTIDAD A ORDENAR (2x PR o EOQ) ===
    cantidad_orden = max(PR * 2, 50)  # ← Mínimo 50 o 2x PR

    # === 8. SIMULACIÓN COMPLETA (HISTÓRICO + FUTURO) ===
    fechas = list(df_filtrado['fecha'].unique()) + list(pd.date_range(ultimo_dia + timedelta(days=1), periods=7))
    stock_simulado = []
    fechas_simuladas = []
    stock_actual = PR + cantidad_orden  # ← INICIO SEGURO

    for i, fecha in enumerate(fechas):
        if fecha <= ultimo_dia:
            # HISTÓRICO: venta real
            venta = ventas_prod[ventas_prod['fecha'] == fecha]['cantidad_vendida'].sum()
        else:
            # FUTURO: predicción
            venta = venta_por_dia[pd.Timestamp(fecha).day_name()]

        # REORDEN: si stock ≤ PR
        if stock_actual <= PR:
            stock_actual += cantidad_orden

        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})
    df_hist = df_sim[df_sim['fecha'] <= ultimo_dia]
    df_fut = df_sim[df_sim['fecha'] > ultimo_dia]

    # === 9. GRÁFICO ===
    fig = go.Figure()

    # Ventas reales
    ventas_diarias = ventas_prod.groupby('fecha')['cantidad_vendida'].sum()
    fig.add_trace(go.Scatter(
        x=ventas_diarias.index, y=ventas_diarias.values,
        mode='lines+markers', name='Ventas Reales',
        line=dict(color=COLOR_VENTAS, width=3)
    ))

    # Predicción futura
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    prediccion = [venta_por_dia[f.day_name()] for f in futuro]
    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion,
        mode='lines+markers', name='Predicción',
        line=dict(color=COLOR_PREDICCION, width=3),
        fill='tonexty', fillcolor='rgba(76, 201, 240, 0.2)'
    ))

    # Stock histórico
    fig.add_trace(go.Scatter(
        x=df_hist['fecha'], y=df_hist['stock'],
        mode='lines', name='Stock Simulado (Pasado)',
        line=dict(color=COLOR_STOCK_HIST, width=2, dash='dot'),
        yaxis='y2'
    ))

    # Stock futuro
    fig.add_trace(go.Scatter(
        x=df_fut['fecha'], y=df_fut['stock'],
        mode='lines+markers', name='Stock Simulado (Futuro)',
        line=dict(color=COLOR_STOCK_FUT, width=3),
        yaxis='y2'
    ))

    # PR
    fig.add_hline(y=PR, line_dash="dash", line_color=COLOR_PR,
                  annotation_text=f"PR = {PR:.0f} unidades", annotation_position="top left")

    # Órdenes
    ordenes = df_sim[df_sim['stock'].diff() > cantidad_orden * 0.8]
    if not ordenes.empty:
        fig.add_trace(go.Scatter(
            x=ordenes['fecha'], y=ordenes['stock'],
            mode='markers', name='Reorden',
            marker=dict(color=COLOR_ORDEN, size=12, symbol='triangle-up'),
            yaxis='y2'
        ))

    fig.update_layout(
        title=f"{producto}: Stock Sube y Baja con Reorden Automático",
        xaxis_title="Fecha",
        yaxis_title="Ventas",
        yaxis2=dict(title="Stock (unidades)", overlaying="y", side="right"),
        hovermode='x unified',
        template="plotly_white",
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # === 10. KPIs ===
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR (unidades)", f"{PR:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Stock Inicial", f"{PR + cantidad_orden:.0f}")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando stock ≤ **{PR:.0f}**")
