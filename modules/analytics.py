# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PALETA AZUL PROFESIONAL
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4CC9F0"
COLOR_STOCK = "#7209B7"
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"

def analytics_app():
    st.title("Predicción Estacional + Simulación de Inventario")
    st.markdown("**Predicción variante por día de semana + PR dinámico**")

    # === 1. VALIDAR DATOS ===
    if st.session_state.df_ventas is None or st.session_state.df_resultados is None:
        st.warning("Sube datos y calcula en **Optimización**")
        return

    df_ventas = st.session_state.df_ventas.copy()
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    df_ventas = df_ventas.dropna(subset=['fecha']).sort_values('fecha')
    df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()

    resultados = st.session_state.df_resultados
    if 'error' in resultados.columns:
        resultados = resultados[resultados['error'].isnull()]
    if resultados.empty:
        st.error("No hay resultados válidos")
        return

    # === 2. FILTRO TEMPORAL ===
    ultimo_dia = df_ventas['fecha'].max()
    opciones_filtro = {
        "Última semana": 7,
        "Último mes": 30,
        "Últimos 3 meses": 90
    }
    filtro = st.selectbox("Período", list(opciones_filtro.keys()))
    dias = opciones_filtro[filtro]
    fecha_inicio = ultimo_dia - timedelta(days=dias)
    df_filtrado = df_ventas[df_ventas['fecha'] >= fecha_inicio]

    # === 3. PRODUCTO ===
    productos = resultados['producto'].unique()
    producto = st.selectbox("Producto", sorted(productos), key="producto_analytics")

    # === 4. DATOS DEL PRODUCTO ===
    ventas_prod = df_filtrado[df_filtrado['producto'] == producto].copy()
    res_prod = resultados[resultados['producto'] == producto].iloc[0]
    cantidad_orden = res_prod['cantidad_a_ordenar']

    # === 5. ESTACIONALIDAD: VENTAS POR DÍA DE SEMANA ===
    ventas_prod['dia_semana'] = ventas_prod['fecha'].dt.day_name()
    estacional = ventas_prod.groupby('dia_semana')['cantidad_vendida'].mean().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    # Normalizar: promedio base
    promedio_diario = estacional.mean()
    factores = (estacional / promedio_diario).to_dict()

    # === 6. PR DINÁMICO POR DÍA ===
    pr_base = res_prod['punto_reorden']
    pr_dinamico = {dia: pr_base * factores[dia] for dia in factores}
    pr_promedio = sum(pr_dinamico.values()) / 7

    # === 7. PREDICCIÓN 7 DÍAS CON ESTACIONALIDAD ===
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    prediccion_futura = pd.Series([
        promedio_diario * factores[futuro[i].day_name()] for i in range(7)
    ], index=futuro)

    # === 8. SIMULACIÓN DE STOCK CON REORDEN DINÁMICO ===
    stock_inicial = pr_promedio + cantidad_orden
    stock_simulado = [stock_inicial]
    fechas_simuladas = [ultimo_dia]
    pr_actual = pr_promedio

    stock_actual = stock_inicial
    for i, fecha in enumerate(futuro):
        venta = prediccion_futura[fecha]
        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

        # PR dinámico por día
        dia = fecha.day_name()
        pr_hoy = pr_dinamico[dia]

        # ¿Reorden?
        if stock_actual <= pr_hoy and len(stock_simulado) < 20:
            stock_actual += cantidad_orden
            stock_simulado.append(stock_actual)
            fechas_simuladas.append(fecha + timedelta(hours=1))  # Llegada inmediata (simulación)

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})

    # === 9. GRÁFICO ===
    fig = go.Figure()

    # Ventas reales (filtradas)
    ventas_diarias = ventas_prod.groupby('fecha')['cantidad_vendida'].sum()
    fig.add_trace(go.Scatter(
        x=ventas_diarias.index, y=ventas_diarias.values,
        mode='lines+markers', name='Ventas Reales',
        line=dict(color=COLOR_VENTAS, width=3)
    ))

    # Predicción futura
    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion_futura.values,
        mode='lines+markers', name='Predicción Estacional',
        line=dict(color=COLOR_PREDICCION, width=3),
        fill='tonexty', fillcolor='rgba(76, 201, 240, 0.2)'
    ))

    # Stock simulado
    fig.add_trace(go.Scatter(
        x=df_sim['fecha'], y=df_sim['stock'],
        mode='lines+markers', name='Stock Simulado',
        line=dict(color=COLOR_STOCK, width=3),
        yaxis='y2'
    ))

    # PR dinámico (línea variable)
    pr_serie = [pr_dinamico[fecha.day_name()] for fecha in futuro]
    fig.add_trace(go.Scatter(
        x=futuro, y=pr_serie,
        mode='lines', name='PR Dinámico',
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

    # === 10. LAYOUT ===
    fig.update_layout(
        title=f"{producto}: Predicción Estacional + PR Dinámico ({filtro})",
        xaxis_title="Fecha",
        yaxis_title="Ventas Diarias",
        yaxis2=dict(title="Stock / PR", overlaying="y", side="right"),
        hovermode='x unified',
        template="plotly_white",
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # === 11. ESTACIONALIDAD ===
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Estacionalidad Semanal")
        fig_bar = go.Figure(go.Bar(
            x=estacional.index, y=estacional.values,
            marker_color=COLOR_PREDICCION,
            text=estacional.values.round(1), textposition='outside'
        ))
        fig_bar.update_layout(showlegend=False, height=300, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("PR Dinámico")
        df_pr = pd.DataFrame(list(pr_dinamico.items()), columns=['Día', 'PR'])
        st.dataframe(df_pr.style.format({'PR': '{:.0f}'}), hide_index=True)

    # === 12. KPIs ===
    st.markdown("### Recomendación")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR Promedio", f"{pr_promedio:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Variación Máxima", f"{estacional.max() / estacional.min():.1f}x")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando el stock baje al PR del día")
