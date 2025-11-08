# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PALETA AZUL PROFESIONAL
COLOR_VENTAS = "#4361EE"      # Azul fuerte
COLOR_PREDICCION = "#4CC9F0"  # Cian
COLOR_STOCK = "#7209B7"       # Violeta-azul
COLOR_PR = "#FF6B6B"          # Rojo suave (solo alertas)
COLOR_ORDEN = "#2ECC71"       # Verde

def analytics_app():
    st.title("Predicción de Ventas + Simulación de Inventario")
    st.markdown("**Historia visual: ¿Cuándo pedirías? ¿Cuánto?**")

    # === 1. CARGAR DATOS DE OPTIMIZACIÓN ===
    if st.session_state.df_ventas is None:
        st.warning("Sube datos en **Optimización de Inventario**")
        return

    df_ventas = st.session_state.df_ventas.copy()
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    df_ventas = df_ventas.dropna(subset=['fecha']).sort_values('fecha')
    df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()

    # === 2. RESULTADOS DE OPTIMIZACIÓN (PR y Cantidad) ===
    if st.session_state.df_resultados is None:
        st.info("Calcula en **Optimización** para ver PR y cantidades")
        return

    resultados = st.session_state.df_resultados
    if 'error' in resultados.columns:
        resultados = resultados[resultados['error'].isnull()]
    if resultados.empty:
        st.error("No hay resultados válidos")
        return

    # === 3. PRODUCTO A ANALIZAR ===
    productos = resultados['producto'].unique()
    producto = st.selectbox("Producto", sorted(productos))

    # === 4. DATOS DEL PRODUCTO ===
    ventas_prod = df_ventas[df_ventas['producto'] == producto].copy()
    res_prod = resultados[resultados['producto'] == producto].iloc[0]
    pr = res_prod['punto_reorden']
    cantidad_orden = res_prod['cantidad_a_ordenar']
    pronostico_diario = res_prod['pronostico_diario_promedio']

    # === 5. PREDICCIÓN 7 DÍAS (SIN HUECO) ===
    ultimo_dia = ventas_prod['fecha'].max()
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)

    # Media móvil 7 días
    ventas_diarias = ventas_prod.groupby('fecha')['cantidad_vendida'].sum()
    prediccion_hist = ventas_diarias.rolling(7, min_periods=1).mean()
    ultima_pred = prediccion_hist.iloc[-1]
    prediccion_futura = pd.Series([ultima_pred] * 7, index=futuro)

    # === 6. SIMULACIÓN DE STOCK (HISTORIA) ===
    stock_inicial = pr + cantidad_orden  # Suponemos que acabas de recibir
    stock_simulado = [stock_inicial]
    fechas_simuladas = [ultimo_dia]

    stock_actual = stock_inicial
    for fecha in futuro:
        venta = prediccion_futura[fecha]
        stock_actual = max(stock_actual - venta, 0)
        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha)

        # ¿Llegamos al PR? → Simulamos reorden
        if stock_actual <= pr and len(stock_simulado) < 15:
            stock_actual += cantidad_orden
            stock_simulado.append(stock_actual)
            fechas_simuladas.append(fecha + timedelta(days=1))  # Llega al día siguiente

    df_sim = pd.DataFrame({
        'fecha': fechas_simuladas,
        'stock': stock_simulado
    })

    # === 7. GRÁFICO: HISTORIA + PREDICCIÓN ===
    fig = go.Figure()

    # Ventas reales
    fig.add_trace(go.Scatter(
        x=ventas_diarias.index, y=ventas_diarias.values,
        mode='lines+markers', name='Ventas Reales',
        line=dict(color=COLOR_VENTAS, width=3)
    ))

    # Predicción histórica
    fig.add_trace(go.Scatter(
        x=prediccion_hist.index, y=prediccion_hist.values,
        mode='lines', name='Tendencia (7 días)',
        line=dict(dash='dot', color=COLOR_PREDICCION, width=2)
    ))

    # Predicción futura
    fig.add_trace(go.Scatter(
        x=futuro, y=prediccion_futura.values,
        mode='lines+markers', name='Predicción 7 días',
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

    # PR
    fig.add_hline(y=pr, line_dash="dash", line_color=COLOR_PR,
                  annotation_text=f"PR: {pr:.0f}", annotation_position="top left")

    # Órdenes simuladas
    ordenes = df_sim[df_sim['stock'].diff() > cantidad_orden * 0.8]
    if not ordenes.empty:
        fig.add_trace(go.Scatter(
            x=ordenes['fecha'], y=ordenes['stock'],
            mode='markers', name='Reorden Simulado',
            marker=dict(color=COLOR_ORDEN, size=12, symbol='triangle-up')
        ))

    # === 8. CONFIGURACIÓN ===
    fig.update_layout(
        title=f"📈 {producto}: Predicción + ¿Cuándo pedirías?",
        xaxis_title="Fecha",
        yaxis_title="Ventas Diarias",
        yaxis2=dict(
            title="Stock Simulado",
            overlaying="y",
            side="right",
            range=[0, max(stock_inicial, pr + cantidad_orden) * 1.3]
        ),
        hovermode='x unified',
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=60, t=80, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # === 9. KPIs + HISTORIA ===
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("PR", f"{pr:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Pronóstico Diario", f"{pronostico_diario:.1f}")
    with col4: st.metric("Stock Inicial Simulado", f"{stock_inicial:.0f}")

    st.markdown("### Historia Visual")
    st.markdown(f"""
    - **Día 0**: Recibes **{cantidad_orden:.0f} unidades** → Stock = **{stock_inicial:.0f}**
    - Ventas diarias: **~{pronostico_diario:.1f}**
    - **Después de {int(pr / pronostico_diario)} días**: Llegas al **PR ({pr:.0f})**
    - **Pides {cantidad_orden:.0f}** → Evitas ruptura
    """)

    st.success("**Recomendación**: Pide **hoy** si tu stock real < PR")
