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

        # === COMPARACIÓN ECONÓMICA: RESTAURANTE ===
    st.markdown("---")
    st.markdown("### Restaurante: Costos Reales vs Nuestro Sistema")
    st.info("**Tradicional**: Pedir cada 7 días (fijo). **Nuestro**: PR + Lead Time + Tendencia.")
        # === GRÁFICA DE BARRAS: VENTAS vs STOCK (SEMANAL) ===
    st.markdown("---")
    st.markdown("### 📊 Ventas vs Stock Promedio (por Semana)")

    # === 1. SIMULACIÓN DE 12 SEMANAS (para tener datos) ===
    semanas = 12
    fechas_sim = pd.date_range(ultimo_dia - timedelta(days=7*semanas), periods=7*semanas, freq='D')
    ventas_semanales = []
    stock_nuestro_semanales = []
    stock_trad_semanales = []

    # Sistema Tradicional: pedir 300 cada 7 días
    stock_trad = 0
    fecha_ultimo_pedido = None

    for i in range(0, len(fechas_sim), 7):
        semana = fechas_sim[i:i+7]
        
        # VENTAS REALES (o estimadas)
        venta_semana = sum(venta_por_dia[pd.Timestamp(d).day_name()] for d in semana)
        ventas_semanales.append(venta_semana)

        # NUESTRO SISTEMA: promedio de stock en la semana
        stock_nuestro_semana = df_sim[df_sim['fecha'].isin(semana)]['stock'].mean() if not df_sim.empty else PR + cantidad_orden
        stock_nuestro_semanales.append(stock_nuestro_semana)

        # TRADICIONAL: pedir 300 cada 7 días
        if fecha_ultimo_pedido is None or (semana[0] - fecha_ultimo_pedido).days >= 7:
            stock_trad = 300
            fecha_ultimo_pedido = semana[0]
        stock_trad = max(stock_trad - venta_semana, 0)
        stock_trad_semanales.append(stock_trad + (300 if (semana[-1] - fecha_ultimo_pedido).days >= 7 else 0))

    # === 2. DATAFRAME SEMANAL ===
    df_semanal = pd.DataFrame({
        'Semana': [f"S{i+1}" for i in range(semanas)],
        'Ventas': [round(v, 1) for v in ventas_semanales],
        'Nuestro Stock': [round(s, 1) for s in stock_nuestro_semanales],
        'Tradicional Stock': [round(s, 1) for s in stock_trad_semanales]
    })

    # === GRÁFICA DE BARRAS: VENTAS vs STOCK (SEMANAL) ===
    st.markdown("---")
    st.markdown("### Ventas vs Stock Promedio (por Semana)")

    semanas = 12
    fechas_sim = pd.date_range(ultimo_dia - timedelta(days=7*semanas), periods=7*semanas, freq='D')
    ventas_semanales = []
    stock_nuestro_semanales = []
    stock_trad_semanales = []

    # === SISTEMA TRADICIONAL: REORDEN FIJO CADA 7 DÍAS ===
    stock_trad = 0
    proximo_pedido = fechas_sim[0]  # Primer día de la simulación

    for i in range(0, len(fechas_sim), 7):
        semana = fechas_sim[i:i+7]
        venta_semana = sum(venta_por_dia[pd.Timestamp(d).day_name()] for d in semana)
        ventas_semanales.append(venta_semana)

        # --- NUESTRO SISTEMA ---
        stock_nuestro_semana = df_sim[df_sim['fecha'].isin(semana)]['stock'].mean() if not df_sim.empty else PR + cantidad_orden
        stock_nuestro_semanales.append(stock_nuestro_semana)

        # --- TRADICIONAL: REORDEN FIJO ---
        # ¿Llega pedido esta semana?
        if semana[0] >= proximo_pedido:
            stock_trad += 300  # Llega el pedido
            proximo_pedido = semana[0] + timedelta(days=7)  # Próximo en 7 días

        # Se consume la venta
        stock_trad = max(stock_trad - venta_semana, 0)

        # Guardar stock promedio de la semana (después de consumo)
        stock_trad_semanales.append(stock_trad)

    # === DATAFRAME ===
    df_semanal = pd.DataFrame({
        'Semana': [f"S{i+1}" for i in range(semanas)],
        'Ventas': [round(v, 1) for v in ventas_semanales],
        'Nuestro Stock': [round(s, 1) for s in stock_nuestro_semanales],
        'Tradicional Stock': [round(s, 1) for s in stock_trad_semanales]
    })

    # === GRÁFICA ===
    fig_barras = go.Figure(data=[
        go.Bar(name='Ventas', x=df_semanal['Semana'], y=df_semanal['Ventas'], marker_color='#4361EE'),
        go.Bar(name='Nuestro Stock', x=df_semanal['Semana'], y=df_semanal['Nuestro Stock'], marker_color='#4CC9F0'),
        go.Bar(name='Tradicional Stock', x=df_semanal['Semana'], y=df_semanal['Tradicional Stock'], marker_color='#FF6B6B')
    ])

    fig_barras.update_layout(
        barmode='group',
        title="Ventas vs Stock Promedio por Semana (Reorden Fijo Cada 7 Días)",
        xaxis_title="Semana",
        yaxis_title="Unidades",
        template="plotly_white",
        height=500,
        legend=dict(x=0.7, y=1.1, orientation="h")
    )
    st.plotly_chart(fig_barras, width='stretch')

    # === RESUMEN ===
    exceso_promedio = df_semanal['Tradicional Stock'].mean() - df_semanal['Nuestro Stock'].mean()
    st.info(f"**Stock promedio tradicional**: {df_semanal['Tradicional Stock'].mean():.1f} unidades\n\n"
            f"**Stock promedio nuestro**: {df_semanal['Nuestro Stock'].mean():.1f} unidades\n\n"
            f"**Exceso evitado**: {exceso_promedio:.1f} unidades/semana")
    # === COSTOS DE RESTAURANTE ===
    costo_pedido = 25          # $25 por entrega (repartidor)
    costo_holding_diario = 0.015  # 1.5% del valor del producto por día
    costo_stockout = 200       # $200 por unidad perdida (cliente se va)
    periodo_dias = 365

    # === VALOR DEL PRODUCTO (estimado) ===
    # Asumimos que cada unidad cuesta $10 (ej. carne, queso, etc.)
    valor_unidad = 10

    # === SISTEMA TRADICIONAL (pedir cada 7 días) ===
    frecuencia_trad = 7
    cantidad_trad = int(demanda_diaria * frecuencia_trad * 1.5)  # 50% extra por seguridad
    pedidos_trad = periodo_dias // frecuencia_trad
    stock_prom_trad = cantidad_trad / 2
    merma_trad = stock_prom_trad * 0.1  # 10% se echa a perder
    quiebres_trad = max(0, (demanda_diaria * periodo_dias) - (cantidad_trad * pedidos_trad)) * 0.15  # 15% quiebres

    costos_trad = {
        'pedidos': pedidos_trad * costo_pedido,
        'holding': stock_prom_trad * costo_holding_diario * valor_unidad * periodo_dias,
        'merma': merma_trad * valor_unidad,
        'stockout': quiebres_trad * costo_stockout
    }
    costos_trad['total'] = sum(costos_trad.values())

    # === NUESTRO SISTEMA (PR + Lead Time) ===
    pedidos_nuestro = len(eventos_entrega)
    stock_prom_nuestro = df_sim['stock'].mean()
    merma_nuestro = stock_prom_nuestro * 0.03  # Solo 3% merma
    quiebres_nuestro = max(0, PR - stock_prom_nuestro) * 0.02  # Solo 2% quiebres

    costos_nuestro = {
        'pedidos': pedidos_nuestro * costo_pedido,
        'holding': stock_prom_nuestro * costo_holding_diario * valor_unidad * periodo_dias,
        'merma': merma_nuestro * valor_unidad,
        'stockout': quiebres_nuestro * costo_stockout
    }
    costos_nuestro['total'] = sum(costos_nuestro.values())

    # === TABLA COMPARATIVA ===
    comparacion = pd.DataFrame({
        'Costo': ['Pedidos ($)', 'Almacenaje ($)', 'Merma ($)', 'Quiebres ($)', 'TOTAL ANUAL ($)'],
        'Tradicional': [
            f"${costos_trad['pedidos']:.0f}",
            f"${costos_trad['holding']:.0f}",
            f"${costos_trad['merma']:.0f}",
            f"${costos_trad['stockout']:.0f}",
            f"${costos_trad['total']:.0f}"
        ],
        'Nuestro': [
            f"${costos_nuestro['pedidos']:.0f}",
            f"${costos_nuestro['holding']:.0f}",
            f"${costos_nuestro['merma']:.0f}",
            f"${costos_nuestro['stockout']:.0f}",
            f"${costos_nuestro['total']:.0f}"
        ],
        'Ahorro': [
            f"${costos_trad['pedidos'] - costos_nuestro['pedidos']:.0f}",
            f"${costos_trad['holding'] - costos_nuestro['holding']:.0f}",
            f"${costos_trad['merma'] - costos_nuestro['merma']:.0f}",
            f"${costos_trad['stockout'] - costos_nuestro['stockout']:.0f}",
            f"${costos_trad['total'] - costos_nuestro['total']:.0f}"
        ]
    })

    st.dataframe(comparacion, use_container_width=True, hide_index=True)

    # === GRÁFICO DE COSTOS ===
    fig_costos = go.Figure(data=[
        go.Bar(name='Tradicional', x=comparacion['Costo'][:-1], y=[
            costos_trad['pedidos'], costos_trad['holding'], costos_trad['merma'], costos_trad['stockout']
        ]),
        go.Bar(name='Nuestro', x=comparacion['Costo'][:-1], y=[
            costos_nuestro['pedidos'], costos_nuestro['holding'], costos_nuestro['merma'], costos_nuestro['stockout']
        ])
    ])
    fig_costos.update_layout(
        barmode='group',
        title="Comparación de Costos Anuales ($)",
        xaxis_title="Tipo de Costo",
        yaxis_title="Costo ($)",
        template="plotly_white"
    )
    st.plotly_chart(fig_costos, width='stretch')

    # === AHORRO FINAL ===
    ahorro_total = costos_trad['total'] - costos_nuestro['total']
    ahorro_porcentaje = (ahorro_total / costos_trad['total']) * 100 if costos_trad['total'] > 0 else 0

    st.success(f"**Ahorro anual: ${ahorro_total:,.0f} ({ahorro_porcentaje:.1f}%)**")
    st.balloons()
