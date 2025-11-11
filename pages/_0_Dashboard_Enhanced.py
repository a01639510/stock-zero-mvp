

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
from modules.core_analysis import procesar_multiple_productos
from modules.analytics import analytics_app
from modules.dashboard_analytics import (
    calcular_indicadores_ventas,
    calcular_indicadores_inventario,
    calcular_eficiencia_operacional,
    generar_recomendaciones,
    calcular_kpi_tendencias
)

warnings.filterwarnings('ignore')

# Color palette
COLOR_VENTAS = "#4361EE"
COLOR_PREDICCION = "#4361EE"
COLOR_STOCK_HIST = "#7209B7"
COLOR_STOCK_FUT = "#4CC9F0"
COLOR_PR = "#FF6B6B"
COLOR_ORDEN = "#2ECC71"
COLOR_ABC_A = "#FF6B6B"
COLOR_ABC_B = "#FFA500"
COLOR_ABC_C = "#4CC9F0"

def crear_kpi_cards_enhanced(kpis):
    """
    Crea tarjetas de KPIs mejoradas para el dashboard
    """
    # Primera fila - KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Ventas con tendencia
        delta_color = "normal" if kpis['ventas']['tendencia_ventas'] >= 0 else "inverse"
        st.metric(
            label="📊 Ventas Totales",
            value=f"{kpis['ventas']['total_ventas']:,.0f}",
            delta=f"{kpis['ventas']['tendencia_ventas']:+.1f}% vs 30d",
            delta_color=delta_color
        )
        
    with col2:
        # Stock con alerta de críticos
        delta_color = "inverse" if kpis['inventario']['productos_criticos'] > 0 else "normal"
        st.metric(
            label="📦 Stock Actual",
            value=f"{kpis['inventario']['stock_total']:,.0f}",
            delta=f"{kpis['inventario']['productos_criticos']} críticos",
            delta_color=delta_color
        )
        
    with col3:
        # Rotación con indicador
        delta_color = "normal" if kpis['rotacion']['rotacion_inventario'] > 1 else "inverse"
        st.metric(
            label="🔄 Rotación Inventario",
            value=f"{kpis['rotacion']['rotacion_inventario']:.2f}x",
            delta=f"{kpis['rotacion']['dias_inventario']:.0f} días",
            delta_color=delta_color
        )
        
    with col4:
        # Fill Rate con estado
        delta_color = "normal" if kpis['eficiencia']['fill_rate'] >= 95 else "inverse"
        st.metric(
            label="✅ Fill Rate",
            value=f"{kpis['eficiencia']['fill_rate']:.1f}%",
            delta=f"${kpis['eficiencia']['costo_almacenaje_anual']:,.0f}/año",
            delta_color="inverse"
        )
    
    # Segunda fila - KPIs secundarios
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            label="🎯 Eficiencia Predicción",
            value=f"{kpis['eficiencia']['eficiencia_prediccion']:.1f}%",
            delta="Volatilidad" if kpis['ventas']['volatilidad'] > 50 else "Estable",
            delta_color="inverse" if kpis['ventas']['volatilidad'] > 50 else "normal"
        )
        
    with col6:
        st.metric(
            label="📈 Productos Optimizados",
            value=f"{kpis['optimizacion']['productos_optimizados']}",
            delta=f"ABC: {len(kpis['optimizacion']['clasificacion_abc'])} cats",
            delta_color="normal"
        )
        
    with col7:
        st.metric(
            label="🏆 Producto Top",
            value=str(kpis['ventas']['producto_mas_vendido'])[:20],
            delta=f"Concentración: {kpis['ventas']['concentracion_ventas']:.1f}%",
            delta_color="inverse" if kpis['ventas']['concentracion_ventas'] > 80 else "normal"
        )
        
    with col8:
        st.metric(
            label="💰 Valor Inventario",
            value=f"${kpis['inventario']['valor_inventario']:,.0f}",
            delta=f"Promedio: ${kpis['inventario']['valor_inventario']/kpis['inventario']['productos_totales']:.0f}" if kpis['inventario']['productos_totales'] > 0 else "N/A",
            delta_color="normal"
        )

def crear_grafico_ventas_tendencia_enhanced(df_ventas):
    """
    Crea gráfico de tendencia de ventas mejorado
    """
    if df_ventas is None or df_ventas.empty:
        return None
    
    # Agrupar ventas por día
    ventas_diarias = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
    
    # Calcular media móvil de 7 días y 30 días
    ventas_diarias['media_movil_7d'] = ventas_diarias['cantidad_vendida'].rolling(window=7, min_periods=1).mean()
    ventas_diarias['media_movil_30d'] = ventas_diarias['cantidad_vendida'].rolling(window=30, min_periods=1).mean()
    
    fig = go.Figure()
    
    # Ventas diarias
    fig.add_trace(go.Scatter(
        x=ventas_diarias['fecha'],
        y=ventas_diarias['cantidad_vendida'],
        mode='lines+markers',
        name='Ventas Diarias',
        line=dict(color=COLOR_VENTAS, width=1),
        opacity=0.6,
        hovertemplate='Fecha: %{x}<br>Ventas: %{y}<extra></extra>'
    ))
    
    # Media móvil 7 días
    fig.add_trace(go.Scatter(
        x=ventas_diarias['fecha'],
        y=ventas_diarias['media_movil_7d'],
        mode='lines',
        name='Tendencia (7d)',
        line=dict(color=COLOR_PREDICCION, width=3),
        hovertemplate='Fecha: %{x}<br>Promedio 7d: %{y:.1f}<extra></extra>'
    ))
    
    # Media móvil 30 días
    fig.add_trace(go.Scatter(
        x=ventas_diarias['fecha'],
        y=ventas_diarias['media_movil_30d'],
        mode='lines',
        name='Tendencia (30d)',
        line=dict(color=COLOR_STOCK_FUT, width=2, dash='dash'),
        hovertemplate='Fecha: %{x}<br>Promedio 30d: %{y:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="📈 Tendencia de Ventas Diarias con Medias Móviles",
        xaxis_title="Fecha",
        yaxis_title="Unidades Vendidas",
        template="plotly_white",
        height=450,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def crear_grafico_composicion_stock(inventario_df, df_resultados):
    """
    Crea gráfico de composición de stock por estado
    """
    if inventario_df is None or inventario_df.empty:
        return None
    
    if df_resultados is None or df_resultados.empty:
        # Sin datos de optimización
        estados = {'Sin optimización': len(inventario_df)}
        colors = ['gray']
    else:
        # Combinar datos para determinar estados
        df_combinado = pd.merge(inventario_df, df_resultados, left_on='Producto', right_on='producto', how='left')
        
        estados = {}
        for _, row in df_combinado.iterrows():
            if pd.isna(row['punto_reorden']):
                estado = 'Sin optimización'
            elif row['Stock Actual'] <= row['punto_reorden']:
                estado = '🔴 Crítico'
            elif row['Stock Actual'] <= row['punto_reorden'] * 1.5:
                estado = '🟡 Advertencia'
            else:
                estado = '🟢 Óptimo'
            
            estados[estado] = estados.get(estado, 0) + 1
        
        colors = {
            '🔴 Crítico': COLOR_PR,
            '🟡 Advertencia': COLOR_ABC_B,
            '🟢 Óptimo': COLOR_ORDEN,
            'Sin optimización': 'gray'
        }
    
    fig = go.Figure(data=[go.Pie(
        labels=list(estados.keys()),
        values=list(estados.values()),
        hole=0.4,
        marker_colors=[colors.get(k, 'gray') for k in estados.keys()],
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="📊 Composición del Stock por Estado",
        template="plotly_white",
        height=400,
        showlegend=True
    )
    
    return fig

def crear_tablero_control_eficiencia(kpis):
    """
    Crea un tablero de control visual de eficiencia
    """
    col1, col2 = st.columns(2)
    
    with col1:
        # Gauge de Fill Rate
        fig_fill_rate = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = kpis['eficiencia']['fill_rate'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Fill Rate (%)"},
            delta = {'reference': 95},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': COLOR_ORDEN},
                'steps': [
                    {'range': [0, 80], 'color': COLOR_PR},
                    {'range': [80, 95], 'color': COLOR_ABC_B},
                    {'range': [95, 100], 'color': COLOR_ORDEN}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_fill_rate.update_layout(height=300, template="plotly_white")
        st.plotly_chart(fig_fill_rate, use_container_width=True)
    
    with col2:
        # Gauge de Eficiencia de Predicción
        fig_eficiencia = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = kpis['eficiencia']['eficiencia_prediccion'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Eficiencia de Predicción (%)"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': COLOR_VENTAS},
                'steps': [
                    {'range': [0, 60], 'color': COLOR_PR},
                    {'range': [60, 80], 'color': COLOR_ABC_B},
                    {'range': [80, 100], 'color': COLOR_VENTAS}
                ],
                'threshold': {
                    'line': {'color': "orange", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig_eficiencia.update_layout(height=300, template="plotly_white")
        st.plotly_chart(fig_eficiencia, use_container_width=True)

def crear_tabla_estados_producto_enhanced(inventario_df, df_resultados):
    """
    Crea tabla mejorada con estado actual de todos los productos
    """
    if inventario_df is None or inventario_df.empty:
        return pd.DataFrame()
    
    df_trabajo = inventario_df.copy()
    
    if df_resultados is None or df_resultados.empty:
        df_trabajo['Estado'] = 'Sin optimización'
        df_trabajo['ABC'] = 'N/A'
        df_trabajo['Punto Reorden'] = 0
        df_trabajo['Cantidad a Ordenar'] = 0
        df_trabajo['Días de Inventario'] = 0
    else:
        # Combinar datos
        df_trabajo = pd.merge(df_trabajo, df_resultados, left_on='Producto', right_on='producto', how='left')
        
        # Determinar estado
        def determinar_estado(row):
            if pd.isna(row['punto_reorden']):
                return '🔴 Sin optimización'
            elif row['Stock Actual'] <= row['punto_reorden']:
                return '🔴 Crítico'
            elif row['Stock Actual'] <= row['punto_reorden'] * 1.5:
                return '🟡 Advertencia'
            else:
                return '🟢 Óptimo'
        
        # Calcular días de inventario estimados
        def calcular_dias_inventario(row):
            if pd.isna(row['pronostico_diario_promedio']) or row['pronostico_diario_promedio'] == 0:
                return 0
            return row['Stock Actual'] / row['pronostico_diario_promedio']
        
        df_trabajo['Estado'] = df_trabajo.apply(determinar_estado, axis=1)
        df_trabajo['ABC'] = df_trabajo['clasificacion_abc'].fillna('N/A')
        df_trabajo['Punto Reorden'] = df_trabajo['punto_reorden'].fillna(0).round(0)
        df_trabajo['Cantidad a Ordenar'] = df_trabajo['cantidad_a_ordenar'].fillna(0).round(0)
        df_trabajo['Días de Inventario'] = df_trabajo.apply(calcular_dias_inventario, axis=1).round(1)
    
    # Ordenar por urgencia
    orden_estados = {'🔴 Crítico': 0, '🔴 Sin optimización': 1, '🟡 Advertencia': 2, '🟢 Óptimo': 3}
    df_trabajo['Prioridad'] = df_trabajo['Estado'].map(orden_estados).fillna(4)
    df_trabajo = df_trabajo.sort_values('Prioridad').drop('Prioridad', axis=1)
    
    return df_trabajo[[
        'Producto', 'Stock Actual', 'Estado', 'ABC', 'Punto Reorden', 
        'Cantidad a Ordenar', 'Días de Inventario'
    ]]

def dashboard_enhanced_app():
    """
    Aplicación principal del dashboard mejorado
    """
    st.title("📊 Dashboard Inteligente de Inventario y Ventas")
    st.markdown("Vista integral con KPIs críticos y recomendaciones automáticas para optimización")
    
    # Verificar datos necesarios
    if 'df_ventas_trazabilidad' not in st.session_state or st.session_state['df_ventas_trazabilidad'].empty:
        st.warning("⚠️ No hay datos de ventas cargados. Por favor, carga tus datos en **Optimización de Inventario**.")
        return
    
    if 'inventario_df' not in st.session_state:
        st.warning("⚠️ No hay datos de inventario cargados. Por favor, configura tu inventario en **Control de Inventario Básico**.")
        return
    
    # Obtener datos
    df_ventas = st.session_state['df_ventas_trazabilidad']
    df_stock = st.session_state.get('df_stock_trazabilidad', pd.DataFrame())
    df_resultados = st.session_state.get('df_resultados', pd.DataFrame())
    inventario_df = st.session_state['inventario_df']
    
    # Filtros mejorados
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periodo_filtro = st.selectbox(
            "📅 Período de análisis",
            ["Últimos 7 días", "Últimos 15 días", "Últimos 30 días", "Últimos 60 días", "Últimos 90 días", "Todos los datos"],
            key="dashboard_periodo"
        )
    
    with col2:
        if df_resultados is not None and not df_resultados.empty:
            categorias_abc = ['Todas'] + sorted(df_resultados['clasificacion_abc'].unique())
            abc_filtro = st.selectbox("🏷️ Filtrar por categoría ABC", categorias_abc, key="dashboard_abc")
        else:
            abc_filtro = 'Todas'
    
    with col3:
        nivel_detalle = st.selectbox(
            "🔍 Nivel de detalle",
            ["Resumen Ejecutivo", "Análisis Completo", "Detallado"],
            key="dashboard_detalle"
        )
    
    # Aplicar filtros
    df_ventas_filtrado = df_ventas.copy()
    if periodo_filtro != "Todos los datos":
        dias_map = {
            "Últimos 7 días": 7, "Últimos 15 días": 15, "Últimos 30 días": 30,
            "Últimos 60 días": 60, "Últimos 90 días": 90
        }
        dias = dias_map[periodo_filtro]
        fecha_limite = df_ventas['fecha'].max() - timedelta(days=dias)
        df_ventas_filtrado = df_ventas[df_ventas['fecha'] >= fecha_limite]
    
    # Filtrar por ABC si es necesario
    if abc_filtro != 'Todas' and df_resultados is not None and not df_resultados.empty:
        productos_abc = df_resultados[df_resultados['clasificacion_abc'] == abc_filtro]['producto'].tolist()
        df_ventas_filtrado = df_ventas_filtrado[df_ventas_filtrado['producto'].isin(productos_abc)]
    
    # Calcular KPIs con spinner mejorado
    with st.spinner("🔄 Analizando datos y calculando KPIs inteligentes..."):
        kpis_ventas = calcular_indicadores_ventas(df_ventas_filtrado)
        kpis_inventario = calcular_indicadores_inventario(inventario_df, df_resultados)
        kpis_eficiencia = calcular_eficiencia_operacional(kpis_ventas, kpis_inventario, df_ventas_filtrado)
        tendencias = calcular_kpi_tendencias(df_ventas_filtrado, 30)
        recomendaciones = generar_recomendaciones(kpis_ventas, kpis_inventario, kpis_eficiencia)
        
        # Formatear KPIs para compatibilidad
        kpis = {
            'ventas': {
                'total_ventas': kpis_ventas.get('total_ventas', 0),
                'tendencia_ventas': tendencias.get('tendencia_porcentual', 0),
                'producto_mas_vendido': kpis_ventas.get('producto_top', 'N/A'),
                'concentracion_ventas': kpis_ventas.get('concentracion_ventas', 0),
                'volatilidad': kpis_ventas.get('coeficiente_variacion', 0)
            },
            'inventario': kpis_inventario,
            'rotacion': kpis_eficiencia,
            'eficiencia': kpis_eficiencia,
            'optimizacion': {
                'productos_optimizados': len(df_resultados[df_resultados['error'].isnull()]) if df_resultados is not None and not df_resultados.empty else 0,
                'clasificacion_abc': kpis_inventario.get('analisis_abc', {})
            }
        }
    
    # Mostrar KPIs principales
    st.markdown("## 🎯 KPIs Principales")
    crear_kpi_cards_enhanced(kpis)
    
    if nivel_detalle in ["Análisis Completo", "Detallado"]:
        # Tablero de control de eficiencia
        st.markdown("---")
        st.markdown("## 📊 Tablero de Control de Eficiencia")
        crear_tablero_control_eficiencia(kpis)
    
    # Sección de gráficos
    st.markdown("---")
    st.markdown("## 📈 Análisis Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_ventas = crear_grafico_ventas_tendencia_enhanced(df_ventas_filtrado)
        if fig_ventas:
            st.plotly_chart(fig_ventas, use_container_width=True)
    
    with col2:
        fig_composicion = crear_grafico_composicion_stock(inventario_df, df_resultados)
        if fig_composicion:
            st.plotly_chart(fig_composicion, use_container_width=True)
    
    if nivel_detalle in ["Análisis Completo", "Detallado"]:
        # Análisis adicional
        st.markdown("---")
        st.markdown("## 🔍 Análisis Detallado")
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Top productos
            if not df_ventas_filtrado.empty:
                ventas_por_producto = df_ventas_filtrado.groupby('producto')['cantidad_vendida'].sum().sort_values(ascending=False).head(10)
                
                fig_top = go.Figure(data=[go.Bar(
                    x=ventas_por_producto.values,
                    y=ventas_por_producto.index,
                    orientation='h',
                    marker_color=COLOR_VENTAS
                )])
                
                fig_top.update_layout(
                    title="🏆 Top 10 Productos Más Vendidos",
                    xaxis_title="Unidades Vendidas",
                    yaxis_title="Producto",
                    template="plotly_white",
                    height=400
                )
                
                st.plotly_chart(fig_top, use_container_width=True)
        
        with col4:
            # Métricas de eficiencia
            st.markdown("### ⚡ Indicadores Clave")
            
            metricas = {
                "Rotación Inventario": f"{kpis_eficiencia.get('rotacion_inventario', 0):.2f}x",
                "Días Inventario": f"{kpis_eficiencia.get('dias_inventario', 0):.0f} días",
                "Nivel Servicio": f"{kpis_eficiencia.get('nivel_servicio', 0):.1f}%",
                "Eficiencia Predicción": f"{kpis_eficiencia.get('eficiencia_prediccion', 0):.1f}%"
            }
            
            for metrica, valor in metricas.items():
                col_met, col_val = st.columns([3, 2])
                with col_met:
                    st.write(f"**{metrica}:**")
                with col_val:
                    st.write(valor)
    
    # Tabla de estados mejorada
    st.markdown("---")
    st.markdown("## 📋 Estado Actual del Inventario")
    
    tabla_estados = crear_tabla_estados_producto_enhanced(inventario_df, df_resultados)
    if not tabla_estados.empty:
        # Resaltar productos críticos
        def highlight_critical_rows(val):
            color = 'background-color: #FFE6E6' if '🔴' in str(val) else ''
            return color
        
        styled_df = tabla_estados.style.applymap(highlight_critical_rows, subset=['Estado'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Estadísticas rápidas
        criticos = len(tabla_estados[tabla_estados['Estado'].str.contains('🔴', na=False)])
        advertencias = len(tabla_estados[tabla_estados['Estado'].str.contains('🟡', na=False)])
        optimos = len(tabla_estados[tabla_estados['Estado'].str.contains('🟢', na=False)])
        
        st.info(f"📊 Resumen: {criticos} críticos | {advertencias} advertencias | {optimos} óptimos")
    
    # Recomendaciones inteligentes
    st.markdown("---")
    st.markdown("## 🤖 Recomendaciones Inteligentes")
    
    if recomendaciones:
        # Agrupar recomendaciones por tipo
        urgentes = [r for r in recomendaciones if '🔴' in r or '🚨' in r]
        importantes = [r for r in recomendaciones if '⚠️' in r or '📉' in r]
        sugerencias = [r for r in recomendaciones if '📊' in r or '💡' in r or '✅' in r]
        
        if urgentes:
            st.error("### 🚨 Acciones Urgentes")
            for rec in urgentes:
                st.error(rec)
        
        if importantes:
            st.warning("### ⚠️ Mejoras Importantes")
            for rec in importantes:
                st.warning(rec)
        
        if sugerencias:
            st.info("### 💡 Sugerencias de Optimización")
            for rec in sugerencias:
                st.info(rec)
    else:
        st.success("✅ **EXCELENTE:** Todos los indicadores están en rangos óptimos. Continúa monitoreando y mejora gradualmente.")
    
    # Botones de acción
    st.markdown("---")
    st.markdown("## 🚀 Acciones Rápidas")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        if st.button("🔄 Actualizar Dashboard", use_container_width=True):
            st.rerun()
    
    with col_b:
        if st.button("📊 Análisis Completo", use_container_width=True):
            st.session_state.current_page = "Optimización de Inventario"
            st.rerun()
    
    with col_c:
        if st.button("📦 Gestionar Inventario", use_container_width=True):
            st.session_state.current_page = "Control de Inventario Básico"
            st.rerun()
    
    with col_d:
        if st.button("📥 Exportar Reporte", use_container_width=True):
            st.success("📊 Reporte exportado exitosamente (funcionalidad en desarrollo)")

# Ejecutar la aplicación
if __name__ == "__main__":
    dashboard_enhanced_app()
