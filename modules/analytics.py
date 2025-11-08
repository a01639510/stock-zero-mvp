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

    # === 9. SIMULACIÓN CON ENTREGA REALISTA ===
    fechas = list(df_filtrado['fecha'].unique()) + list(pd.date_range(ultimo_dia + timedelta(days=1), periods=30))
    stock_simulado = []
    fechas_simuladas = []
    pedidos_pendientes = []  # [(fecha_entrega, cantidad)]
    eventos_entrega = []     # (fecha_entrega, cantidad)

    stock_actual = PR + cantidad_orden

    for fecha in fechas:
        fecha_dt = pd.Timestamp(fecha)

        # 1. RECIBIR PEDIDOS
        entregas_hoy = sum(cant for ent, cant in pedidos_pendientes if ent == fecha_dt)
        if entregas_hoy > 0:
            stock_actual += entregas_hoy
            pedidos_pendientes = [(e, c) for e, c in pedidos_pendientes if e != fecha_dt]
            eventos_entrega.append((fecha_dt, entregas_hoy))

        # 2. VENTA
        if fecha_dt <= ultimo_dia:
            venta = ventas_prod[ventas_prod['fecha'] == fecha_dt]['cantidad_vendida'].sum()
        else:
            venta = venta_por_dia[fecha_dt.day_name()]

        stock_actual = max(stock_actual - venta, 0)

        # 3. REORDEN
        if stock_actual <= PR and not any(1 for _ in pedidos_pendientes):
            fecha_entrega = fecha_dt + timedelta(days=lead_time)
            pedidos_pendientes.append((fecha_entrega, cantidad_orden))

        stock_simulado.append(stock_actual)
        fechas_simuladas.append(fecha_dt)

    df_sim = pd.DataFrame({'fecha': fechas_simuladas, 'stock': stock_simulado})

    # === 10. GRÁFICA CON SOMBREADO ===
    fig = go.Figure()

    # Ventas históricas
    df_hist = df_sim[df_sim['fecha'] <= ultimo_dia]
    ventas_hist = ventas_prod.groupby('fecha')['cantidad_vendida'].sum().reindex(df_hist['fecha']).fillna(0)
    fig.add_trace(go.Scatter(x=ventas_hist.index, y=ventas_hist.values, mode='lines', name='Ventas Reales',
                             line=dict(color=COLOR_VENTAS, width=3), yaxis='y'))

    # Predicción
    futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=30)
    prediccion = [venta_por_dia[f.day_name()] for f in futuro]
    fig.add_trace(go.Scatter(x=futuro, y=prediccion, mode='lines+markers', name='Predicción',
                             line=dict(color=COLOR_PREDICCION, width=3, dash='dot'), marker=dict(size=6), yaxis='y'))

    # Stock
    fig.add_trace(go.Scatter(x=df_sim['fecha'], y=df_sim['stock'], mode='lines', name='Stock Simulado',
                             line=dict(color=COLOR_STOCK_FUT, width=3), yaxis='y2'))

    # PR
    fig.add_hline(y=PR, line_dash="dash", line_color=COLOR_PR,
                  annotation_text=f"PR = {PR:.0f} unidades", annotation_position="top left")

    # Sombreado Lead Time
    for entrega_fecha, cantidad in eventos_entrega:
        orden_fecha = entrega_fecha - timedelta(days=lead_time)
        if orden_fecha in df_sim['fecha'].values:
            fig.add_vrect(x0=orden_fecha, x1=entrega_fecha, fillcolor="gray", opacity=0.2, layer="below", line_width=0,
                          annotation_text=f"LT: {lead_time} días" if eventos_entrega.index((entrega_fecha, cantidad)) == 0 else "",
                          annotation_position="top left")

    # Reorden y Entrega
    fechas_orden = [e[0] - timedelta(days=lead_time) for e in eventos_entrega if (e[0] - timedelta(days=lead_time)) in df_sim['fecha'].values]
    if fechas_orden:
        stock_orden = df_sim[df_sim['fecha'].isin(fechas_orden)]['stock']
        fig.add_trace(go.Scatter(x=fechas_orden, y=stock_orden, mode='markers', name='Reorden',
                                 marker=dict(color=COLOR_ORDEN, size=14, symbol='triangle-up'), yaxis='y2'))

    fechas_entrega = [e[0] for e in eventos_entrega]
    if fechas_entrega:
        stock_entrega = df_sim[df_sim['fecha'].isin(fechas_entrega)]['stock']
        fig.add_trace(go.Scatter(x=fechas_entrega, y=stock_entrega, mode='markers', name='Entrega',
                                 marker=dict(color="#2ECC71", size=12, symbol='triangle-down'), yaxis='y2'))

    fig.update_layout(
        title=f"{producto}: Simulación Real con Lead Time = {lead_time} días",
        xaxis_title="Fecha", yaxis=dict(title="Ventas", side="left"),
        yaxis2=dict(title="Stock", overlaying="y", side="right"),
        hovermode='x unified', template="plotly_white", height=620,
        legend=dict(x=0, y=1.1, orientation="h")
    )
    st.plotly_chart(fig, width='stretch')

    # === KPIs ===
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("PR (unidades)", f"{PR:.0f}")
    with col2: st.metric("Cantidad a Pedir", f"{cantidad_orden:.0f}")
    with col3: st.metric("Stock Inicial", f"{PR + cantidad_orden:.0f}")
    st.success(f"**Pide {cantidad_orden:.0f} unidades** cuando stock ≤ **{PR:.0f}**")

    # === COMPARACIÓN ECONÓMICA ===
    st.markdown("---")
    st.markdown("### Comparación Económica: Tradicional vs Nuestro Sistema")
    st.info("**Tradicional**: Reorden fijo cada 30 días (300 unidades). **Nuestro**: PR dinámico + Lead Time.")

    periodo_dias = 365
    costo_pedido = 50
    costo_holding_anual = 0.1
    costo_stockout = 100

    # Sistema Tradicional
    reorden_trad = 30
    cantidad_trad = 300
    pedidos_trad = periodo_dias // reorden_trad
    stock_prom_trad = cantidad_trad / 2
    quiebres_trad = max(0, (demanda_diaria * periodo_dias) - (cantidad_trad * pedidos_trad)) * 0.1

    costos_trad = {
        'pedidos': pedidos_trad * costo_pedido,
        'holding': stock_prom_trad * costo_holding_anual * cantidad_trad,
        'stockout': quiebres_trad * costo_stockout
    }
    costos_trad['total'] = sum(v for k, v in costos_trad.items() if k != 'total')

    # Nuestro Sistema
    pedidos_nuestro = len(eventos_entrega)
    stock_prom_nuestro = df_sim['stock'].mean()
    quiebres_nuestro = max(0, PR - stock_prom_nuestro) * 0.05

    costos_nuestro = {
        'pedidos': pedidos_nuestro * costo_pedido,
        'holding': stock_prom_nuestro * costo_holding_anual,
        'stockout': quiebres_nuestro * costo_stockout
    }
    costos_nuestro['total'] = sum(v for k, v in costos_nuestro.items() if k != 'total')

    # Tabla
    comparacion = pd.DataFrame({
        'Métrica': ['Pedidos', 'Costo Pedidos ($)', 'Costo Holding ($)', 'Costo Stockout ($)', 'Costo Total ($)'],
        'Tradicional': [pedidos_trad, f"${costos_trad['pedidos']:.0f}", f"${costos_trad['holding']:.0f}", f"${costos_trad['stockout']:.0f}", f"${costos_trad['total']:.0f}"],
        'Nuestro': [pedidos_nuestro, f"${costos_nuestro['pedidos']:.0f}", f"${costos_nuestro['holding']:.0f}", f"${costos_nuestro['stockout']:.0f}", f"${costos_nuestro['total']:.0f}"],
        'Ahorro (%)': [
            f"{(pedidos_trad - pedidos_nuestro)/pedidos_trad*100:.1f}%" if pedidos_trad > 0 else "N/A",
            f"{(costos_trad['pedidos'] - costos_nuestro['pedidos'])/costos_trad['pedidos']*100:.1f}%" if costos_trad['pedidos'] > 0 else "N/A",
            f"{(costos_trad['holding'] - costos_nuestro['holding'])/costos_trad['holding']*100:.1f}%" if costos_trad['holding'] > 0 else "N/A",
            f"{(costos_trad['stockout'] - costos_nuestro['stockout'])/costos_trad['stockout']*100:.1f}%" if costos_trad['stockout'] > 0 else "100%",
            f"{(costos_trad['total'] - costos_nuestro['total'])/costos_trad['total']*100:.1f}%"
        ]
    })
    st.dataframe(comparacion, use_container_width=True, hide_index=True)

    # Gráfico de costos
    fig_costos = go.Figure(data=[
        go.Bar(name='Tradicional', x=['Pedidos', 'Holding', 'Stockout'], y=[costos_trad['pedidos'], costos_trad['holding'], costos_trad['stockout']]),
        go.Bar(name='Nuestro', x=['Pedidos', 'Holding', 'Stockout'], y=[costos_nuestro['pedidos'], costos_nuestro['holding'], costos_nuestro['stockout']])
    ])
    fig_costos.update_layout(barmode='group', title="Comparación de Costos ($)", xaxis_title="Tipo", yaxis_title="$")
    st.plotly_chart(fig_costos, width='stretch')

    ahorro = (costos_trad['total'] - costos_nuestro['total']) / costos_trad['total'] * 100
    st.success(f"**Ahorro total anual: {ahorro:.1f}%** → **${costos_trad['total'] - costos_nuestro['total']:.0f}**")
