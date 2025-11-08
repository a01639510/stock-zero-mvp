# modules/analytics.py
import streamlit as st
import pandas as pd
from datetime import timedelta

def analytics_app():
    st.markdown("## Simulación Realista de Inventario")
    st.markdown("*Reorden automático cuando stock ≤ PR*")

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

    # === FILTROS ===
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

    # === PARÁMETROS DEL SIDEBAR (persistentes) ===
    lead_time = st.session_state.get('analytics_lead_time', 7)
    stock_seguridad = st.session_state.get('analytics_stock_seguridad', 3)
    frecuencia = st.session_state.get('analytics_frecuencia', 7)

    st.caption(
        f"**Configuración**: Lead Time = {lead_time} días | "
        f"Stock de Seguridad = {stock_seguridad} días | "
        f"Estacionalidad = {frecuencia} días"
    )

    # === DATOS DEL PRODUCTO ===
    r = ok[ok['producto'] == producto].iloc[0].to_dict()
    pr = r['punto_reorden']
    cantidad = r['cantidad_a_ordenar']
    pronostico = r['pronostico_diario_promedio']

    # === STOCK INICIAL ===
    stock_inicial = 0.0
    if st.session_state.inventario_df is not None:
        row = st.session_state.inventario_df[st.session_state.inventario_df['Producto'] == producto]
        if not row.empty:
            stock_inicial = float(row['Stock Actual'].iloc[0])

    st.metric("Stock Inicial", f"{stock_inicial:.0f}")
    st.info(f"**Pide {cantidad:.0f} unidades cuando stock ≤ {pr:.0f}**")

    # === SIMULACIÓN ===
    from modules.trazability import calcular_trazabilidad_inventario
    from modules.components import crear_grafico_trazabilidad_total

    traz = calcular_trazabilidad_inventario(
        st.session_state.df_ventas_trazabilidad,
        st.session_state.df_stock_trazabilidad,
        producto,
        stock_inicial,
        pr,
        cantidad,
        pronostico,
        lead_time
    )

    if traz is not None and not traz.empty:
        fig = crear_grafico_trazabilidad_total(traz, r, lead_time)
        st.pyplot(fig)
    else:
        st.error("No se pudo simular. Verifica datos de stock.")
