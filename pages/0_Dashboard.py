```python
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

def calcular_kpis_completos(df_ventas, df_stock, df_resultados, inventario_df):
    """
    Calcula KPIs completos para el dashboard de inventario y ventas
    """
    kpis = {}
    
    if df_ventas is None or df_ventas.empty:
        return kpis
    
    # 1. KPIs de Ventas
    total_ventas = df_ventas['cantidad_vendida'].sum()
    dias_con_ventas = df_ventas['fecha'].nunique()
    ventas_promedio_diarias = total_ventas / dias_con_ventas if dias_con_ventas > 0 else 0
    
    # Ventas por producto
    ventas_por_producto = df_ventas.groupby('producto')['cantidad_vendida'].sum().sort_values(ascending=False)
    producto_mas_vendido = ventas_por_producto.index[0] if not ventas_por_producto.empty else "N/A"
    
    # Tendencia de ventas (últimos 30 días vs anteriores 30 días)
    fecha_max = df_ventas['fecha'].max()
    fecha_30_dias_atras = fecha_max - timedelta(days=30)
    fecha_60_dias_atras = fecha_max - timedelta(days=60)
    
    ventas_recientes = df_ventas[df_ventas['fecha'] >= fecha_30_dias_atras]['cantidad_vendida'].sum()
   ventas_anteriores = df_ventas[(df_ventas['fecha'] >= fecha_60_dias_atras) & (df_ventas['fecha'] < fecha_30_dias_atras)]['cantidad_vendida'].sum()
    
    tendencia_ventas = ((ventas_recientes - ventas_anteriores) / ventas_anteriores * 100) if ventas_anteriores > 0 else 0
    
    # 2. KPIs de Inventario
    if inventario_df is not None and not inventario_df.empty:
        stock_total_actual = inventario_df['Stock Actual'].sum()
        productos_con_stock = (inventario_df['Stock Actual'] > 0).sum()
        productos_totales = len(inventario_df)
        
        # Valor total del inventario (asumiendo valor promedio de $10 por unidad)
        valor_inventario = stock_total_actual * 10
        
        # Stock crítico (productos con stock bajo punto de reorden)
        if df_resultados is not None and not df_resultados.empty:
            df_criticos = pd.merge(inventario_df, df_resultados, left_on='Producto', right_on='producto', how='left')
            stock_critico = df_criticos[df_criticos['Stock Actual'] <= df_criticos['punto_reorden']]
            productos_criticos = len(stock_criticos)
        else:
            productos_criticos = 0
    else:
        stock_total_actual = 0
        productos_con_stock = 0
        productos_totales = 0
        valor_inventario = 0
        productos_criticos = 0
    
    # 3. KPIs de Rotación
    if stock_total_actual > 0:
        rotacion_inventario = total_ventas / stock_total_actual
        dias_inventario = (stock_total_actual / ventas_promedio_diarias) if ventas_promedio_diarias > 0 else float('inf')
    else:
        rotacion_inventario = 0
        dias_inventario = float('inf')
    
    # 4. KPIs de Optimización
    if df_resultados is not None and not df_resultados.empty:
        productos_optimizados = len(df_resultados[df_resultados['error'].isnull()])
        total_punto_reorden = df_resultados['punto_reorden'].sum()
        total_a_ordenar = df_resultados['cantidad_a_ordenar'].sum()
        
        # Clasificación ABC
        clasificacion_abc = df_resultados['clasificacion_abc'].value_counts().to_dict()
    else:
        productos_optimizados = 0
        total_punto_reorden = 0
        total_a_ordenar = 0
        clasificacion_abc = {}
    
    # 5. KPIs de Eficiencia
    fill_rate = min((total_ventas / (total_ventas + productos_criticos)) * 100, 100) if (total_ventas + productos_criticos) > 0 else 100
    
    # Costos estimados
    costo_almacenaje_diario = 0.015  # 1.5% del valor por día
    costo_almacenaje_anual = valor_inventario * costo_almacenaje_diario * 365
    
    # Guardar todos los KPIs
    kpis = {
        'ventas': {
            'total_ventas': total_ventas,
            'ventas_promedio_diarias': ventas_promedio_diarias,
            'producto_mas_vendido': producto_mas_vendido,
            'tendencia_ventas': tendencia_ventas
        },
        'inventario': {
            'stock_total_actual': stock_total_actual,
            'productos_con_stock': productos_con_stock,
            'productos_totales': productos_totales,
            'valor_inventario': valor_inventario,
            'productos_criticos': productos_criticos
        },
        'rotacion': {
            'rotacion_inventario': rotacion_inventario,
            'dias_inventario': dias_inventario if dias_inventario != float('inf') else 0
        },
        'optimizacion': {
            'productos_optimizados': productos_optimizados,
            'total_punto_reorden': total_punto_reorden,
            'total_a_ordenar': total_a_ordenar,
            'clasificacion_abc': clasificacion_abc
        },
        'eficiencia': {
            'fill_rate': fill_rate,
            'costo_almacenaje_anual': costo_almacenaje_anual
        }
    }
    
    return kpis

def crear_kpi_cards(kpis):
    """
    Crea tarjetas de KPIs para el dashboard
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Ventas Totales",
            value=f"{kpis['ventas']['total_ventas']:,.0f}",
            delta=f"{kpis['ventas']['tendencia_ventas']:+.1f}% vs período anterior",
            delta_color="normal" if kpis['ventas']['tendencia_ventas'] >= 0 else "inverse"
        )
        
    with col2:
        st.metric(
            label="📦 Stock Actual",
            value=f"{kpis['inventario']['stock_total_actual']:,.0f}",
            delta=f"{kpis['inventario']['productos_criticos']} críticos",
            delta_color="inverse" if kpis['inventario']['productos_criticos'] > 0 else "normal"
        )
        
    with col3:
        st.metric(
            label="🔄 Rotación Inventario",
            value=f"{kpis['rotacion']['rotacion_inventario']:.2f}x",
            delta=f"{kpis['rotacion']['dias_inventario']:.0f} días",
            delta_color="normal" if kpis['rotacion']['dias_inventario'] < 30 else "inverse"
        )
        
    with col4:
        st.metric(
            label="✅ Fill Rate",
            value=f"{kpis['eficiencia']['fill_rate']:.1f}%",
            delta=f"${kpis['eficiencia']['costo_almacenaje_anual']:,.0f}/año",
            delta_color="inverse"
        )

def crear_grafico_ventas_tendencia(df_ventas):
    """
    Crea gráfico de tendencia de ventas
    """
    if df_ventas is None or df_ventas.empty:
        return None
    
    # Agrupar ventas por día
    ventas_diarias = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
    
    # Calcular media móvil de 7 días
    ventas_diarias['media_movil_7d'] = ventas_diarias['cantidad_vendida'].rolling(window=7, min_periods=1).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ventas_diarias['fecha'],
        y=ventas_diarias['cantidad_vendida'],
        mode='lines+markers',
        name='Ventas Diarias',
        line=dict(color=COLOR_VENTAS, width=1),
        opacity=0.7
    ))
    
    fig.add_trace(go.Scatter(
        x=ventas_diarias['fecha'],
        y=ventas_diarias['media_movil_7d'],
        mode='lines',
        name='Media Móvil (7d)',
        line=dict(color=COLOR_PREDICCION, width=3)
    ))
    
    fig.update_layout(
        title="📈 Tendencia de Ventas Diarias",
        xaxis_title="Fecha",
        yaxis_title="Unidades Vendidas",
        template="plotly_white",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def crear_grafico_abc_pie(df_resultados):
    """
    Crea gráfico de pastel de clasificación ABC
    """
    if df_resultados is None or df_resultados.empty:
        return None
    
    abc_counts = df_resultados['clasificacion_abc'].value_counts()
    
    colors = {
        'A': COLOR_ABC_A,
        'B': COLOR_ABC_B,
        'C': COLOR_ABC_C
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=abc_counts.index,
        values=abc_counts.values,
        hole=0.3,
        marker_colors=[colors.get(cat, "#GRAY") for cat in abc_counts.index]
    )])
    
    fig.update_layout(
        title="🏷️ Clasificación ABC de Productos",
        template="plotly_white",
        height=400,
        showlegend=True
    )
    
    return fig

def crear_grafico_top_productos(df_ventas):
    """
    Crea gráfico de top productos
    """
    if df_ventas is None or df_ventas.empty:
        return None
    
    ventas_por_producto = df_ventas.groupby('producto')['cantidad_vendida'].sum().sort_values(ascending=False).head(10)
    
    fig = go.Figure(data=[go.Bar(
        x=ventas_por_producto.values,
        y=ventas_por_producto.index,
        orientation='h',
        marker_color=COLOR_VENTAS
    )])
    
    fig.update_layout(
        title="🏆 Top 10 Productos Más Vendidos",
        xaxis_title="Unidades Vendidas",
        yaxis_title="Producto",
        template="plotly_white",
        height=400
    )
    
    return fig

def crear_tabla_estados_producto(inventario_df, df_resultados):
    """
    Crea tabla con estado actual de todos los productos
    """
    if inventario_df is None or inventario_df.empty:
        return pd.DataFrame()
    
    if df_resultados is None or df_resultados.empty:
        inventario_df['Estado'] = 'Sin optimización'
        inventario_df['Punto Reorden'] = 0
        inventario_df['Cantidad a Ordenar'] = 0
        return inventario_df[['Producto', 'Stock Actual', 'Estado']]
    
    # Combinar datos
    df_combinado = pd.merge(inventario_df, df_resultados, left_on='Producto', right_on='producto', how='left')
    
    # Determinar estado
    def determinar_estado(row):
        if pd.isna(row['punto_reorden']):
            return 'Sin optimización'
        elif row['Stock Actual'] <= row['punto_reorden']:
            return '🔴 Crítico'
        elif row['Stock Actual'] <= row['punto_reorden'] * 1.5:
            return '🟡 Advertencia'
        else:
            return '🟢 Óptimo'
    
    df_combinado['Estado'] = df_combinado.apply(determinar_estado, axis=1)
    df_combinado['Punto Reorden'] = df_combinado['punto_reorden'].fillna(0).round(0)
    df_combinado['Cantidad a Ordenar'] = df_combinado['cantidad_a_ordenar'].fillna(0).round(0)
    
    return df_combinado[['Producto', 'Stock Actual', 'Estado', 'ABC', 'Punto Reorden', 'Cantidad a Ordenar']].sort_values('Estado')

def dashboard_app():
    """
    Aplicación principal del dashboard
    """
    st.title("📊 Dashboard de Inventario y Ventas")
    st.markdown("Vista integral de KPIs críticos para optimización de inventario y ventas")
    
    # Verificar datos necesarios
    if 'df_ventas_trazabilidad' not in st.session_state or st.session_state['df_ventas_trazabilidad'].empty:
        st.warning("⚠️ No hay datos de ventas cargados. Por favor, carga tus datos en **Optimización de Inventario**.")
        return
    
    if 'inventario_df' not in st.session_state:
        st.warning("⚠️ No hay datos de inventario cargados. Por favor, configura tu inventario en **Control de Inventario Básico**.")
        return
    
    # Obtener datos
    df_ventas = st.session_state['df_ventas_trazability'] if 'df_ventas_trazability' in st.session_state else st.session_state['df_ventas_trazabilidad']
    df_stock = st.session_state.get('df_stock_trazabilidad', pd.DataFrame())
    df_resultados = st.session_state.get('df_resultados', pd.DataFrame())
    inventario_df = st.session_state['inventario_df']
    
    # Filtros
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        periodo_filtro = st.selectbox(
            "📅 Período de análisis",
            ["Últimos 30 días", "Últimos 60 días", "Últimos 90 días", "Todos los datos"],
            key="dashboard_periodo"
        )
    
    with col2:
        if df_resultados is not None and not df_resultados.empty:
            categorias_abc = ['Todas'] + list(df_resultados['clasificacion_abc'].unique())
            abc_filtro = st.selectbox("🏷️ Filtrar por categoría ABC", categorias_abc, key="dashboard_abc")
    
    # Aplicar filtros
    df_ventas_filtrado = df_ventas.copy()
    if periodo_filtro != "Todos los datos":
        dias = {"Últimos 30 días": 30, "Últimos 60 días": 60, "Últimos 90 días": 90}
        fecha_limite = df_ventas['fecha'].max() - timedelta(days=dias[periodo_filtro])
        df_ventas_filtrado = df_ventas[df_ventas['fecha'] >= fecha_limite]
    
    # Calcular KPIs
    with st.spinner("Calculando KPIs..."):
        kpis = calcular_kpis_completos(df_ventas_filtrado, df_stock, df_resultados, inventario_df)
    
    # Mostrar KPIs principales
    st.markdown("## 🎯 KPIs Principales")
    crear_kpi_cards(kpis)
    
    # Sección de gráficos
    st.markdown("---")
    st.markdown("## 📈 Análisis Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_ventas = crear_grafico_ventas_tendencia(df_ventas_filtrado)
        if fig_ventas:
            st.plotly_chart(fig_ventas, use_container_width=True)
    
    with col2:
        if df_resultados is not None and not df_resultados.empty:
            fig_abc = crear_grafico_abc_pie(df_resultados)
            if fig_abc:
                st.plotly_chart(fig_abc, use_container_width=True)
        else:
            st.info("Carga datos de ventas y ejecuta optimización para ver clasificación ABC")
    
    # Tercera fila de gráficos
    col3, col4 = st.columns(2)
    
    with col3:
        fig_top = crear_grafico_top_productos(df_ventas_filtrado)
        if fig_top:
            st.plotly_chart(fig_top, use_container_width=True)
    
    with col4:
        # Indicadores de eficiencia
        st.markdown("### ⚡ Indicadores de Eficiencia")
        
        metricas_eficiencia = {
            "Productos Optimizados": f"{kpis['optimizacion']['productos_optimizados']}",
            "Fill Rate": f"{kpis['eficiencia']['fill_rate']:.1f}%",
            "Rotación Inventario": f"{kpis['rotacion']['rotacion_inventario']:.2f}x",
            "Días Inventario": f"{kpis['rotacion']['dias_inventario']:.0f}"
        }
        
        for metrica, valor in metricas_eficiencia.items():
            st.metric(metrica, valor)
    
    # Tabla de estados
    st.markdown("---")
    st.markdown("## 📋 Estado Actual del Inventario")
    
    tabla_estados = crear_tabla_estados_producto(inventario_df, df_resultados)
    if not tabla_estados.empty:
        st.dataframe(tabla_estados, use_container_width=True, hide_index=True)
    
    # Recomendaciones
    st.markdown("---")
    st.markdown("## 💡 Recomendaciones Automáticas")
    
    recomendaciones = []
    
    if kpis['inventario']['productos_criticos'] > 0:
        recomendaciones.append(f"🔴 **URGENTE:** {kpis['inventario']['productos_criticos']} productos necesitan reorden inmediato")
    
    if kpis['rotacion']['dias_inventario'] > 60:
        recomendaciones.append("⚠️ **ALERTA:** Inventario con rotación lenta. Considera promociones o reducción de stock")
    
    if kpis['eficiencia']['fill_rate'] < 95:
        recomendaciones.append("📈 **MEJORA:** Fill rate debajo del 95%. Revisa niveles de stock safety")
    
    if kpis['ventas']['tendencia_ventas'] < -10:
        recomendaciones.append("📉 **ANÁLISIS:** Ventas en descenso. Revisa demanda y ajusta pronósticos")
    
    if not recomendaciones:
        recomendaciones.append("✅ **EXCELENTE:** Todos los KPIs están en rangos óptimos")
    
    for rec in recomendaciones:
        st.info(rec)
    
    # Botones de acción
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("🔄 Actualizar Dashboard", use_container_width=True):
            st.rerun()
    
    with col_b:
        if st.button("📊 Ver Análisis Detallado", use_container_width=True):
            st.session_state.current_page = "Optimización de Inventario"
            st.rerun()
    
    with col_c:
        if st.button("📦 Gestionar Inventario", use_container_width=True):
            st.session_state.current_page = "Control de Inventario Básico"
            st.rerun()

# Ejecutar la aplicación
if __name__ == "__main__":
    dashboard_app()
```