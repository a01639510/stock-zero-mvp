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
    st.markdown("**Predicción realista por día de semana + PR dinámico**")

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
        "Últimos 3 meses": 90,
        "Todo el historial": (ultimo_dia - df_ventas['fecha'].min()).days + 1
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
    pronostico_base = res_prod['pronostico_diario_promedio']  # ← VALOR REAL

    if ventas_prod.empty:
        st.error("No hay ventas en este período")
        return

    # === 5. ESTACIONALIDAD ROBUSTA ===
    ventas_prod['dia_semana'] = ventas_prod['fecha'].dt.day_name()
    ventas_dia = ventas_prod.groupby('dia_semana')['cantidad_vendida'].agg(['mean', 'count']).reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]).fillna(0)

    variacion_cv = (ventas_dia['mean'].std() / ventas_dia['mean'].mean()) * 100 if ventas_dia['mean'].mean() > 0 else 0
    st.caption(f"**Variación estacional (CV): {variacion_cv:.1f}%** → {'FUERTE' if variacion_cv > 30 else 'MODERADA' if variacion_cv > 15 else 'DÉBIL'}")

    # === 6. FACTORES ESTACIONALES (SIN DOBLE NORMALIZACIÓN) ===
    if ventas_dia['count'].sum() < 14 or variacion_cv < 10:
        # FACTORES REALISTAS (0.8 a 1.3)
        factores = {
            'Monday': 0.8, 'Tuesday': 0.9, 'Wednesday': 0.95,
            'Thursday': 1.0, 'Friday': 1.2, 'Saturday': 1.3, 'Sunday': 1.1
        }
        st.info("Datos insuficientes → Aplicando **estacionalidad realista (+30% sábado)**")
    else:
        # FACTORES REALES (basado en datos)
        promedio_real = ventas_dia['mean'].mean()
        factores = (ventas_dia['mean'] / promedio_real).to_dict()  # ← 0.7–1.5

    # === 7. PREDICCIÓN = pronostico_base × factor (NO NORMALIZAR) ===
    prediccion_futura = pd.Series([
        pronostico_base * factores[fecha.day_name()] for fecha in pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
    ], index=pd.date_range(ultimo_dia + timedelta(days=1), periods=7))

    # === 8. PR DINÁMICO (AJUSTADO) ===
    pr_base = res_prod['punto_reorden']
    pr_dinamico = {dia: pr_base * factores[dia] for dia in factores}

    # === 9. SIMULACIÓN DE STOCK ===
    stock_inicial = pr_base + cantidad_orden
    stock_simulado = [stock_inicial]
    fechas_simuladas = [ultimo_dia]
    stock_actual = stock_inicial

    for fecha in prediccion_futura.index:
        venta = prediccion_futura[fecha]
        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

        pr_hoy = pr_dinamico[fecha.day_name()]
        if stock_actual <= pr_hoy and len(stock_simulado) < 20:
            stock_actual += cantidad_orden
            stock_simulado.append(stock_actual)
            fechas_simuladas.append(fecha + timedelta(hours=1))

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})

    # === 10. GRÁFICO ===
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
        x=prediccion_futura.index, y=prediccion_futura.values,
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

    # PR dinámico
    pr_serie = [pr_dinamico[fecha.day_name()] for fecha in prediccion_futura.index]
    fig.add_trace(go.Scatter(
        x=prediccion_futura.index, y=pr_serie,
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
        st.subheader("Predicción por Día")
        valores = [pronostico_base * factores[dia] for dia in factores]
        fig_bar = go.Figure(go.Bar(
            x=list(factores.keys()), y=valores,
            marker_color=COLOR_PREDICCION,
            text=[f"{v:.1f}" for v in valores], textposition='outside'
        ))
        fig_bar.update_layout(showlegend=False, height=300, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("PR por Día")
        pr_vals = [pr_dinamico[dia] for dia in factores]
        st.dataframe(
            pd.DataFrame({'Día': factores.keys(), 'PR': pr_vals}).style.format({'PR': '{:.0f}'}),
            hide_index=True
        )

    # === 12. KPIs ===
    st.markdown("### Acción")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR Base", f"{pr_base:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Pico (Sábado)", f"{pronostico_base * factores['Saturday']:.1f}")

    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando el stock baje al PR del día")
