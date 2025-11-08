# modules/analytics.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

def analytics_app():
    st.markdown("## Simulación Realista de Inventario")
    st.markdown("*Reorden automático cuando stock ≤ PR (en unidades)*")

    # --- Verificar datos ---
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

    # --- Filtros ---
    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox(
            "Período",
            ["Últimos 3 meses", "Últimos 6 meses", "Todo el año"],
            key="analytics_periodo"
        )
    with col2:
        producto = st.selectbox(
            "Producto",
            ok['producto'].tolist(),
            key="analytics_producto"
        )

    # --- Parámetros del sidebar ---
    lead_time = st.session_state.get('analytics_lead_time', 7)
    stock_seguridad = st.session_state.get('analytics_stock_seguridad', 3)
    frecuencia = st.session_state.get('analytics_frecuencia', 7)

    st.caption(
        f"**Configuración**: Lead Time = {lead_time} días | "
        f"Stock de Seguridad = {stock_seguridad} días | "
        f"Estacionalidad = {frecuencia} días"
    )

    # --- Datos del producto ---
    r = ok[ok['producto'] == producto].iloc[0].to_dict()
    pr = r['punto_reorden']
    cantidad_pedir = r['cantidad_a_ordenar']
    pronostico = r['pronostico_diario_promedio']

    # --- Stock inicial ---
    stock_inicial = 0.0
    if st.session_state.inventario_df is not None:
        row = st.session_state.inventario_df[st.session_state.inventario_df['Producto'] == producto]
        if not row.empty:
            stock_inicial = float(row['Stock Actual'].iloc[0])

    # --- Mostrar métricas ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stock Inicial", f"{stock_inicial:.0f}")
    with col2:
        st.metric("PR (unidades)", f"{pr:.0f}")
    st.info(f"**Pide {cantidad_pedir:.0f} unidades cuando stock ≤ {pr:.0f}**")

    # --- TRAZABILIDAD (GRÁFICA ORIGINAL) ---
    df_ventas = st.session_state.df_ventas_trazabilidad
    df_stock = st.session_state.df_stock_trazabilidad

    # Filtrar por producto
    ventas_prod = df_ventas[df_ventas['producto'] == producto].copy()
    stock_prod = df_stock[df_stock['producto'] == producto].copy()

    # Rango completo
    fecha_min = ventas_prod['fecha'].min()
    fecha_max = ventas_prod['fecha'].max()
    fechas = pd.date_range(fecha_min, fecha_max, freq='D')

    # Simular inventario día a día
    inventario = []
    stock_actual = stock_inicial
    orden_pendiente = None  # (fecha_entrega, cantidad)

    for fecha in fechas:
        fecha_str = fecha.strftime('%Y-%m-%d')

        # 1. Recibir stock si llega
        if orden_pendiente and orden_pendiente[0] == fecha:
            stock_actual += orden_pendiente[1]
            orden_pendiente = None

        # 2. Vender
        venta = ventas_prod[ventas_prod['fecha'] == fecha_str]['cantidad_vendida'].sum()
        stock_actual -= venta

        # 3. Reorden si ≤ PR y no hay orden pendiente
        if stock_actual <= pr and orden_pendiente is None:
            fecha_entrega = fecha + timedelta(days=lead_time)
            orden_pendiente = (fecha_entrega, cantidad_pedir)

        # 4. Recibir stock programado
        recepcion = stock_prod[stock_prod['fecha'] == fecha_str]['cantidad_recibida'].sum()
        stock_actual += recepcion

        inventario.append({
            'fecha': fecha,
            'stock': max(0, stock_actual),
            'venta': venta,
            'recepcion': recepcion,
            'orden': 1 if (orden_pendiente and orden_pendiente[0] == fecha) else 0
        })

    df_sim = pd.DataFrame(inventario)

    # --- GRÁFICA ORIGINAL (exactamente como antes) ---
    fig, ax = plt.subplots(figsize=(12, 6))

    # Línea de stock
    ax.plot(df_sim['fecha'], df_sim['stock'], label='Stock', color='blue', linewidth=2)

    # Ventas (barras negativas)
    ax.bar(df_sim['fecha'], -df_sim['venta'], label='Ventas', color='orange', alpha=0.6, width=0.8)

    # Recepciones (barras positivas)
    recepciones = df_sim[df_sim['recepcion'] > 0]
    ax.bar(recepciones['fecha'], recepciones['recepcion'], label='Recepción', color='green', alpha=0.8, width=0.8)

    # Punto de Reorden
    ax.axhline(y=pr, color='red', linestyle='--', label=f'PR = {pr:.0f}', linewidth=2)

    # Lead Time (sombreado desde orden hasta entrega)
    if orden_pendiente:
        fecha_orden = df_sim[df_sim['stock'] <= pr].iloc[0]['fecha']
        fecha_entrega = fecha_orden + timedelta(days=lead_time)
        ax.axvspan(fecha_orden, fecha_entrega, color='gray', alpha=0.2, label='Lead Time')

    ax.set_title(f"Trazabilidad: {producto}", fontsize=16, fontweight='bold')
    ax.set_ylabel("Unidades")
    ax.set_xlabel("Fecha")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Formato de fechas
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45)

    plt.tight_layout()
    st.pyplot(fig)
