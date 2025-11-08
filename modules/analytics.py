# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

# === PALETA AZUL ===
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4361EE"
COLOR_STOCK_HIST = "#7209B7"
COLOR_STOCK_FUT = "#4CC9F0"
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"

def analytics_app():
    st.title("Simulación Completa de Inventario")
    st.markdown("**Pasado + Futuro: ¿Cuándo habrías pedido?**")

    # === 1. DATOS ===
    if st.session_state.df_ventas is None:
        st.warning("Sube datos de ventas en **Optimización de Inventario**.")
        return

    if st.session_state.df_resultados is None:
        st.info("Primero calcula en **Optimización de Inventario**.")
        return

    df_resultados = st.session_state.df_resultados
    ok = df_resultados[df_resultados['error'].isnull()]
    if ok.empty:
        st.error("No hay resultados válidos.")
        return

    # === 2. FILTROS ===
    col1, col2 = st.columns(2)
    with col1:
        filtro = st.selectbox(
            "Período",
            ["Últimos 3 meses", "Últimos 6 meses", "Todo el año"],
            key="analytics_filtro"
        )
    with col2:
        producto = st.selectbox(
            "Producto",
            ok['producto'].tolist(),
            key="analytics_producto"
        )

    # === 3. PARÁMETROS ===
    lead_time = st.session_state.get('analytics_lead_time', 7)
    stock_seguridad_dias = st.session_state.get('analytics_stock_seguridad', 3)

    # === 4. FILTRAR DATOS ===
    df_ventas = st.session_state.df_ventas_trazabilidad
    ultimo_dia = df_ventas['fecha'].max()

    if filtro == "Últimos 3 meses":
        fecha_inicio = ultimo_dia - timedelta(days=90)
    elif filtro == "Últimos 6 meses":
        fecha_inicio = ultimo_dia - timedelta(days=180)
    else:
        fecha_inicio = df_ventas['fecha'].min()

    df_filtrado = df_ventas[df_ventas['fecha'] >= fecha_inicio].copy()
    ventas_prod = df_filtrado[df_filtrado['producto'] == producto].copy()
    ventas_prod['dia_semana'] = ventas_prod['fecha'].dt.day_name()

    # === 5. ESTACIONALIDAD ===
    venta_por_dia = ventas_prod.groupby('dia_semana')['cantidad_vendida'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    if len(ventas_prod) < 14:
        base = venta_por_dia.mean() or 10
        venta_por_dia = pd.Series({
            'Monday': base * 0.8, 'Tuesday': base * 0.9, 'Wednesday': base * 0.95,
            'Thursday': base * 1.0, 'Friday': base * 1.2, 'Saturday': base * 1.3, 'Sunday': base * 1.1
        })

    # === 6. TENDENCIA PONDERADA (EWMA) ===
    ventas_diarias = ventas_prod.groupby('fecha')['cantidad_vendida'].sum().sort_index()
    
    if len(ventas_diarias) < 7:
        demanda_base = ventas_diarias.mean()
    else:
        demanda_ponderada = ventas_diarias.ewm(alpha=0.3, adjust=False).mean()
        demanda_base = demanda_ponderada.iloc[-1]

    demanda_diaria = demanda_base

    # === 7. PR ===
    demanda_lead_time = demanda_diaria * lead_time
    stock_seguridad = demanda_diaria * stock_seguridad_dias
    PR = demanda_lead_time + stock_seguridad
    PR = max(PR, 1)

    # === 8. CANTIDAD A ORDENAR ===
    cantidad_orden = max(PR * 2, 50)

    # === 9. SIMULACIÓN ===
    fechas = list(df_filtrado['fecha'].unique()) + list(pd.date_range(ultimo_dia + timedelta(days=1), periods=7))
    stock_simulado = []
    fechas_simuladas = []
    stock_actual = PR + cantidad_orden

    for fecha in fechas:
        if fecha <= ultimo_dia:
            venta = ventas_prod[ventas_prod['fecha'] == fecha]['cantidad_vendida'].sum()
        else:
            venta = venta_por_dia[pd.Timestamp(fecha).day_name()]

        if stock_actual <= PR:
            stock_actual += cantidad_orden

        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})

    # === 10. GRÁFICA ===
    fig = go.Figure()

    # Ventas históricas
    df_hist = df_sim[df_sim['fecha'] <= ultimo_dia]
    ventas_hist = ventas_prod.groupby('fecha')['cantidad_vendida'].sum().reindex(df_hist['fecha']).fillna(0)

    fig.add_trace(go.Scatter(
        x=ventas_hist.index, y=ventas_hist.values,
        mode='lines', name='Ventas Reales',
        line=dict(color=COLOR_VENTAS, width=3),
        yaxis='y'
    ))

    # Predicción
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    prediccion = [venta_por_dia[f.day_name()] for f in futuro]

    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion,
        mode='lines+markers', name='Predicción',
        line=dict(color=COLOR_PREDICCION, width=3, dash='dot'),
        marker=dict(size=6),
        yaxis='y'
    ))

    # Stock histórico
    fig.add_trace(go.Scatter(
        x=df_hist['fecha'], y=df_hist['stock'],
        mode='lines', name='Stock (Pasado)',
        line=dict(color=COLOR_STOCK_HIST, width=2, dash='dot'),
        yaxis='y2'
    ))

    # Stock futuro
    df_fut = df_sim[df_sim['fecha'] > ultimo_dia]
    fig.add_trace(go.Scatter(
        x=df_fut['fecha'], y=df_fut['stock'],
        mode='lines+markers', name='Stock (Futuro)',
        line=dict(color=COLOR_STOCK_FUT, width=3),
        marker=dict(size=6),
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
            marker=dict(color=COLOR_ORDEN, size=14, symbol='triangle-up'),
            yaxis='y2'
        ))

    # Layout
    fig.update_layout(
        title=f"{producto}: Stock Sube y Baja con Reorden Automático",
        xaxis_title="Fecha",
        yaxis=dict(title="Ventas (unidades)", side="left"),
        yaxis2=dict(title="Stock (unidades)", overlaying="y", side="right"),
        hovermode='x unified',
        template="plotly_white",
        height=620,
        legend=dict(x=0, y=1.1, orientation="h")
    )

    # === MOSTRAR GRÁFICA (CORREGIDO) ===
    st.plotly_chart(fig, width='stretch')  # ← NUEVA API

    # === KPIs ===
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR (unidades)", f"{PR:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Stock Inicial", f"{PR + cantidad_orden:.0f}")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando stock ≤ **{PR:.0f}**")
