# modules/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def analytics_app():
    st.title("Análisis Avanzado de Ventas e Inventario")

    # === PRIORIDAD 1: Usar datos de Optimización ===
        # === PRIORIDAD 1: Usar datos de Optimización ===
    if st.session_state.df_ventas is None:
        st.warning("Sube datos en **Optimización de Inventario** o usa Excel abajo.")
    else:
        df_ventas = st.session_state.df_ventas.copy()
        
        # --- LIMPIEZA DE FECHAS (CRÍTICO) ---
        df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
        if df_ventas['fecha'].isna().all():
            st.error("Todas las fechas son inválidas. Revisa el formato (YYYY-MM-DD).")
            st.stop()
        df_ventas = df_ventas.dropna(subset=['fecha']).copy()
        df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()

        # === 1. Preparar datos agregados ===
        ventas_diarias = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
        ventas_diarias = ventas_diarias.rename(columns={'cantidad_vendida': 'ventas'})
        
        # Stock: acumulado de entradas
        if st.session_state.df_stock is not None:
            stock_diario = st.session_state.df_stock.copy()
            stock_diario['fecha'] = pd.to_datetime(stock_diario['fecha'], errors='coerce')
            stock_diario = stock_diario.dropna(subset=['fecha']).copy()
            stock_acum = stock_diario.groupby('fecha')['cantidad_recibida'].sum().cumsum().reset_index()
            stock_acum = stock_acum.rename(columns={'cantidad_recibida': 'stock_entradas'})
        else:
            stock_acum = pd.DataFrame({'fecha': ventas_diarias['fecha'], 'stock_entradas': 500})

        # Unir
        df = ventas_diarias.merge(stock_acum, on='fecha', how='left').fillna(method='ffill').fillna(0)
        df['stock_real'] = df['stock_entradas'].cumsum() - df['ventas'].cumsum()
        df = df[df['stock_real'] >= 0]  # Evitar negativos irreales
        
        # === 1. Preparar datos agregados ===
        ventas_diarias = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
        ventas_diarias = ventas_diarias.rename(columns={'cantidad_vendida': 'ventas'})
        
        # Stock: acumulado de entradas
        if st.session_state.df_stock is not None:
            stock_diario = st.session_state.df_stock.copy()
            stock_diario['fecha'] = pd.to_datetime(stock_diario['fecha'])
            stock_acum = stock_diario.groupby('fecha')['cantidad_recibida'].sum().cumsum().reset_index()
            stock_acum = stock_acum.rename(columns={'cantidad_recibida': 'stock_entradas'})
        else:
            stock_acum = pd.DataFrame({'fecha': ventas_diarias['fecha'], 'stock_entradas': 500})

        # Unir
        df = ventas_diarias.merge(stock_acum, on='fecha', how='left').fillna(method='ffill').fillna(0)
        df['stock_real'] = df['stock_entradas'].cumsum() - df['ventas'].cumsum()
        df = df[df['stock_real'] >= 0]  # Evitar negativos irreales

        # === 2. Predicción 7 días adelante ===
        ultimo_dia = df['fecha'].max()
        futuro = pd.date_range(ultimo_dia + timedelta(days=1), periods=7)
        
        # Media móvil 7 días
        prediccion_historica = df['ventas'].rolling(window=7, min_periods=1).mean()
        ultima_prediccion = prediccion_historica.iloc[-1]
        prediccion_futura = pd.Series([ultima_prediccion] * 7, index=futuro)

        # === 3. Proyección de stock óptima ===
        stock_optimo = []
        stock_actual = df['stock_real'].iloc[-1]
        for v in prediccion_futura:
            stock_actual -= v
            stock_optimo.append(max(stock_actual, 0))
        proyeccion_optima = pd.Series(stock_optimo, index=futuro)

        # === 4. Comparación: Gasto Real vs Óptimo ===
        costo_unitario_prom = 50  # Ajusta según tu negocio
        gasto_real = (df['ventas'].sum() * costo_unitario_prom)
        ventas_optimas = df['ventas'].sum() + prediccion_futura.sum()
        gasto_optimo = ventas_optimas * costo_unitario_prom
        ahorro_dinero = gasto_optimo - gasto_real
        ahorro_inventario = proyeccion_optima.iloc[-1] - df['stock_real'].iloc[-1]

        # === 5. Mostrar KPIs ===
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Ventas Totales", f"{df['ventas'].sum():.0f}")
        with col2: st.metric("Stock Final", f"{df['stock_real'].iloc[-1]:.0f}")
        with col3: st.metric("Ahorro Potencial (7 días)", f"${ahorro_dinero:,.0f}")
        with col4: st.metric("Inventario Ahorrado", f"{ahorro_inventario:.0f}")

        # === 6. Gráfico principal ===
        fig = go.Figure()

        # Histórico
        fig.add_trace(go.Scatter(x=df['fecha'], y=df['ventas'], mode='lines+markers', name='Ventas Reales',
                                 line=dict(color='#4361EE', width=3)))
        fig.add_trace(go.Scatter(x=df['fecha'], y=df['stock_real'], mode='lines+markers', name='Stock Real',
                                 line=dict(color='#F72585', width=3)))

        # Predicción
        fig.add_trace(go.Scatter(x=df['fecha'], y=prediccion_historica, mode='lines', name='Tendencia',
                                 line=dict(dash='dot', color='#4CC9F0')))
        fig.add_trace(go.Scatter(x=futuro, y=prediccion_futura, mode='lines', name='Predicción 7 días',
                                 line=dict(dash='dot', color='#4CC9F0', width=3)))

        # Proyección stock
        fig.add_trace(go.Scatter(x=futuro, y=proyeccion_optima, mode='lines', name='Stock Óptimo',
                                 line=dict(dash='dash', color='#7209B7', width=3)))

        fig.update_layout(
            title="Ventas, Stock, Predicción y Proyección Óptima",
            xaxis_title="Fecha", yaxis_title="Unidades",
            hovermode='x unified', template="plotly_white", height=550,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # === 7. Estacionalidad mejorada ===
        df['dia_semana'] = df['fecha'].dt.day_name()
        ventas_dia = df.groupby('dia_semana')['ventas'].agg(['mean', 'std']).reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        variacion_cv = (ventas_dia['std'] / ventas_dia['mean']).mean() * 100
        dia_pico = ventas_dia['mean'].idxmax()

        st.markdown("---")
        st.subheader("Tendencias Semanales (CV = Coeficiente de Variación)")

        col1, col2 = st.columns(2)
        with col1:
            if variacion_cv > 40:
                st.success(f"**PATRON SEMANAL FUERTE** (CV: {variacion_cv:.0f}%)")
                st.write(f"**Pico**: {dia_pico} → {ventas_dia.loc[dia_pico, 'mean']:.0f}/día")
            elif variacion_cv > 20:
                st.info(f"**Patrón moderado** (CV: {variacion_cv:.0f}%)")
            else:
                st.warning("**Estable** – Sin picos claros")

        with col2:
            fig_bar = px.bar(x=ventas_dia.index, y=ventas_dia['mean'],
                             error_y=ventas_dia['std'],
                             labels={'x': 'Día', 'y': 'Ventas Promedio'},
                             color=ventas_dia['mean'], color_continuous_scale='Viridis')
            fig_bar.update_layout(showlegend=False, template="plotly_white", height=320)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.info("**CV bajo = ventas estables | CV alto = picos predecibles**")

    # === SUBIR EXCEL (opcional) ===
    st.markdown("---")
    with st.expander("O subir Excel manual (fecha, ventas, stock)", expanded=False):
        uploaded = st.file_uploader("Excel", type=['xlsx'], key="manual_excel")
        if uploaded:
            df = pd.read_excel(uploaded)
            df.columns = df.columns.str.lower().str.strip()
            if {'fecha', 'ventas', 'stock'}.issubset(df.columns):
                df['fecha'] = pd.to_datetime(df['fecha'])
                df = df.sort_values('fecha')
                mostrar_grafico_tiempo(df)
                mostrar_estacionalidad(df)
            else:
                st.error("Faltan columnas: fecha, ventas, stock")
