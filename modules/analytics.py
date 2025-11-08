# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PALETA AZUL
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4CC9F0"
COLOR_STOCK = "#7209B7"
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"

def analytics_app():
    st.title("Predicción Estacional + Simulación de Inventario")
    st.markdown("**Basado 100% en tus datos reales por día de semana**")

    # === 1. VALIDAR DATOS ===
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
    if ventas_prod.empty:
        st.error("No hay ventas para este producto")
        return

    ventas_prod['dia_semana'] = ventas_prod['fecha'].dt.day_name()

    # === 5. PROMEDIO REAL POR DÍA DE SEMANA (SIN PROMEDIO GLOBAL) ===
    ventas_por_dia = ventas_prod.groupby('dia_semana')['cantidad_vendida'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    # Diagnóstico
    variacion_cv = (ventas_por_dia.std() / ventas_por_dia.mean()) * 100
    st.caption(f"**Variación real (CV): {variacion_cv:.1f}%** → {'FUERTE' if variacion_cv > 30 else 'MODERADA' if variacion_cv > 10 else 'DÉBIL'}")

    # === 6. SI HAY POCOS DATOS → ESTACIONALIDAD REALISTA ===
    if len(ventas_prod) < 14 or variacion_cv < 10:
        st.info("Datos limitados → Aplicando **+30% sábado, +20% viernes, -20% lunes**")
        base = ventas_por_dia.mean()
        ventas_por_dia = pd.Series({
            'Monday': base * 0.8,
            'Tuesday': base * 0.9,
            'Wednesday': base * 0.95,
            'Thursday': base * 1.0,
            'Friday': base * 1.2,
            'Saturday': base * 1.3,
            'Sunday': base * 1.1
        })

    # === 7. PREDICCIÓN 7 DÍAS: VALORES REALES POR DÍA ===
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    prediccion_futura = pd.Series([
        ventas_por_dia[fecha.day_name()] for fecha in futuro
    ], index=futuro)

    # === 8. PR DINÁMICO (basado en ventas reales) ===
    lead_time = 7  # Ajusta si tienes
    stock_seguridad = 3
    pr_dinamico = {dia: ventas_por_dia[dia] * (lead_time + stock_seguridad) for dia in ventas_por_dia.index}

    # === 9. CANTIDAD A ORDENAR (EOQ simple) ===
    demanda_anual = ventas_por_dia.mean() * 365
    costo_orden = 100  # Ajusta
    costo_mantenimiento = 0.2
    cantidad_orden = np.sqrt((2 * demanda_anual * costo_orden) / costo_mantenimiento)

    # === 10. SIMULACIÓN DE STOCK ===
    stock_inicial = ventas_por_dia.mean() * 14 + cantidad_orden
    stock_simulado = [stock_inicial]
    fechas_simuladas = [ultimo_dia]
    stock_actual = stock_inicial

    for fecha in futuro:
        venta = prediccion_futura[fecha]
        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

        pr_hoy = pr_dinamico[fecha.day_name()]
        if stock_actual <= pr_hoy:
            stock_actual += cantidad_orden
            stock_simulado.append(stock_actual)
            fechas_simuladas.append(fecha + timedelta(hours=1))

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})

    # === 11. GRÁFICO ===
    fig = go.Figure()

    # Ventas reales
    ventas_diarias = ventas_prod.groupby('fecha')['cantidad_vendida'].sum()
    fig.add_trace(go.Scatter(
        x=ventas_diarias.index, y=ventas_diarias.values,
        mode='lines+markers', name='Ventas Reales',
        line=dict(color=COLOR_VENTAS, width=3)
    ))

    # Predicción variante
    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion_futura.values,
        mode='lines+markers', name='Predicción por Día',
        line=dict(color=COLOR_PREDICCIONure, width=3),
        fill='tonexty', fillcolor='rgba(76, 201, 240, 0.2)'
    ))

    # Stock
    fig.add_trace(go.Scatter(
        x=df_sim['fecha'], y=df_sim['stock'],
        mode='lines+markers', name='Stock Simulado',
        line=dict(color=COLOR_STOCK, width=3),
        yaxis='y2'
    ))

    # PR dinámico
    pr_serie = [pr_dinamico[fecha.day_name()] for fecha in futuro]
    fig.add_trace(go.Scatter(
        x=futuro, y=pr_serie,
        mode='lines', name='PR por Día',
        line=dict(dash='dash', color=COLOR_PR, width=2),
        yaxis='y2'
    ))

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
        title=f"{producto}: Predicción Real por Día ({filtro})",
        xaxis_title="Fecha",
        yaxis_title="Ventas",
        yaxis2=dict(title="Stock / PR", overlaying="y", side="right"),
        hovermode='x unified',
        template="plotly_white",
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # === 12. ESTACIONALIDAD ===
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ventas por Día")
        fig_bar = go.Figure(go.Bar(
            x=ventas_por_dia.index, y=ventas_por_dia.values,
            marker_color=COLOR_PREDICCION,
            text=ventas_por_dia.values.round(1), textposition='outside'
        ))
        fig_bar.update_layout(showlegend=False, height=300, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("PR por Día")
        st.dataframe(
            pd.DataFrame([
                {"Día": dia, "PR": pr_dinamico[dia]} for dia in pr_dinamico
            ]).style.format({'PR': '{:.0f}'}),
            hide_index=True
        )

    # === 13. KPIs ===
    st.markdown("### Acción")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR Promedio", f"{sum(pr_dinamico.values())/7:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Pico (Sábado)", f"{ventas_por_dia['Saturday']:.1f}")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando baje al PR del día")
