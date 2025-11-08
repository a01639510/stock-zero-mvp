# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PALETA AZUL
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4CC9F0"
COLOR_STOCK_HIST = "#7209B7"   # Violeta oscuro (histórico)
COLOR_STOCK_FUT = "#4CC9F0"    # Cian (futuro)
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"

def analytics_app():
    st.title("Simulación Completa de Inventario")
    st.markdown("**Pasado + Futuro: ¿Cuándo habrías pedido?**")

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

    # === 5. ESTACIONALIDAD REAL (PROMEDIO POR DÍA) ===
    ventas_por_dia = ventas_prod.groupby('dia_semana')['cantidad_vendida'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    # Si pocos datos → estacionalidad realista
    if len(ventas_prod) < 14:
        base = ventas_por_dia.mean()
        ventas_por_dia = pd.Series({
            'Monday': base * 0.8, 'Tuesday': base * 0.9, 'Wednesday': base * 0.95,
            'Thursday': base * 1.0, 'Friday': base * 1.2, 'Saturday': base * 1.3, 'Sunday': base * 1.1
        })

    # === 6. PR = 3 DÍAS DE DEMANDA (POR DÍA DE SEMANA) ===
    pr_por_dia = {dia: ventas_por_dia[dia] * 3 for dia in ventas_por_dia.index}
    pr_promedio = sum(pr_por_dia.values()) / 7

    # === 7. CANTIDAD A ORDENAR (EOQ SIMPLE) ===
    demanda_anual = ventas_por_dia.mean() * 365
    cantidad_orden = max(np.sqrt(2 * demanda_anual * 100 / 0.2), pr_promedio * 2)  # Mínimo 2x PR

    # === 8. SIMULACIÓN COMPLETA (HISTÓRICO + FUTURO) ===
    fechas = df_filtrado['fecha'].unique()
    stock_simulado = []
    fechas_simuladas = []
    stock_actual = pr_promedio + cantidad_orden  # Stock inicial

    # HISTÓRICO
    for fecha in fechas:
        dia = pd.Timestamp(fecha).day_name()
        venta = ventas_prod[ventas_prod['fecha'] == fecha]['cantidad_vendida'].sum()
        pr_hoy = pr_por_dia[dia]

        # Reorden si baja del PR
        if stock_actual <= pr_hoy:
            stock_actual += cantidad_orden

        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

    # FUTURO (7 días)
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    for fecha in futuro:
        dia = fecha.day_name()
        venta = ventas_por_dia[dia]  # Predicción
        pr_hoy = pr_por_dia[dia]

        if stock_actual <= pr_hoy:
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
    prediccion_futura = pd.Series([ventas_por_dia[f.day_name()] for f in futuro], index=futuro)
    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion_futura.values,
        mode='lines+markers', name='Predicción',
        line=dict(color=COLOR_PREDICCION, width=3),
        fill='tonexty', fillcolor='rgba(76, 201, 240, 0.2)'
    ))

    # Stock histórico (hue bajo)
    fig.add_trace(go.Scatter(
        x=df_hist['fecha'], y=df_hist['stock'],
        mode='lines', name='Stock Simulado (Histórico)',
        line=dict(color=COLOR_STOCK_HIST, width=2, dash='dot'),
        yaxis='y2'
    ))

    # Stock futuro (hue alto)
    fig.add_trace(go.Scatter(
        x=df_fut['fecha'], y=df_fut['stock'],
        mode='lines+markers', name='Stock Simulado (Futuro)',
        line=dict(color=COLOR_STOCK_FUT, width=3),
        yaxis='y2'
    ))

    # PR promedio
    fig.add_hline(y=pr_promedio, line_dash="dash", line_color=COLOR_PR,
                  annotation_text=f"PR ≈ {pr_promedio:.0f} (3 días)", annotation_position="top left")

    # Órdenes simuladas
    ordenes = df_sim[df_sim['stock'].diff() > cantidad_orden * 0.8]
    if not ordenes.empty:
        fig.add_trace(go.Scatter(
            x=ordenes['fecha'], y=ordenes['stock'],
            mode='markers', name='Reorden Simulado',
            marker=dict(color=COLOR_ORDEN, size=12, symbol='triangle-up'),
            yaxis='y2'
        ))

    fig.update_layout(
        title=f"{producto}: Simulación Completa de Inventario ({filtro})",
        xaxis_title="Fecha",
        yaxis_title="Ventas",
        yaxis2=dict(title="Stock Simulado", overlaying="y", side="right"),
        hovermode='x unified',
        template="plotly_white",
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # === 10. KPIs ===
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR (3 días)", f"{pr_promedio:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Pico (Sábado)", f"{ventas_por_dia['Saturday']:.1f}")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando el stock baje a **~{pr_promedio:.0f}**")
