import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

def calcular_indicadores_ventas(df_ventas: pd.DataFrame) -> Dict:
    """
    Calcula indicadores detallados de ventas
    """
    if df_ventas is None or df_ventas.empty:
        return {}
    
    # Ventas totales y por período
    ventas_por_dia = df_ventas.groupby('fecha')['cantidad_vendida'].sum()
    total_ventas = ventas_por_dia.sum()
    
    # Análisis temporal
    fecha_max = df_ventas['fecha'].max()
    fecha_min = df_ventas['fecha'].min()
    dias_analisis = (fecha_max - fecha_min).days + 1
    
    # Ventas promedio
    ventas_promedio_diarias = total_ventas / dias_analisis
    ventas_promedio_semanales = ventas_promedio_diarias * 7
    ventas_promedio_mensuales = ventas_promedio_diarias * 30
    
    # Tendencia (comparación de períodos)
    fecha_medio = fecha_min + timedelta(days=dias_analisis // 2)
    
    ventas_primera_mitad = df_ventas[df_ventas['fecha'] < fecha_medio]['cantidad_vendida'].sum()
    ventas_segunda_mitad = df_ventas[df_ventas['fecha'] >= fecha_medio]['cantidad_vendida'].sum()
    
    if ventas_primera_mitad > 0:
        tendencia_crecimiento = ((ventas_segunda_mitad - ventas_primera_mitad) / ventas_primera_mitad) * 100
    else:
        tendencia_crecimiento = 0
    
    # Análisis por producto
    ventas_por_producto = df_ventas.groupby('producto')['cantidad_vendida'].sum().sort_values(ascending=False)
    producto_top = ventas_por_producto.index[0] if not ventas_por_producto.empty else None
    
    # Concentración de ventas (Top 20% de productos)
    n_productos = len(ventas_por_producto)
    n_top_20 = max(1, int(n_productos * 0.2))
    ventas_top_20 = ventas_por_producto.head(n_top_20).sum()
    concentracion_ventas = (ventas_top_20 / total_ventas) * 100 if total_ventas > 0 else 0
    
    # Estacionalidad (ventas por día de semana)
    df_ventas['dia_semana'] = df_ventas['fecha'].dt.day_name()
    ventas_por_dia_semana = df_ventas.groupby('dia_semana')['cantidad_vendida'].mean()
    
    # Volatilidad
    volatilidad_ventas = ventas_por_dia.std()
    coeficiente_variacion = (volatilidad_ventas / ventas_promedio_diarias) * 100 if ventas_promedio_diarias > 0 else 0
    
    return {
        'total_ventas': total_ventas,
        'dias_analisis': dias_analisis,
        'ventas_promedio_diarias': ventas_promedio_diarias,
        'ventas_promedio_semanales': ventas_promedio_semanales,
        'ventas_promedio_mensuales': ventas_promedio_mensuales,
        'tendencia_crecimiento': tendencia_crecimiento,
        'producto_top': producto_top,
        'concentracion_ventas': concentracion_ventas,
        'ventas_por_dia_semana': ventas_por_dia_semana.to_dict(),
        'volatilidad_ventas': volatilidad_ventas,
        'coeficiente_variacion': coeficiente_variacion
    }

def calcular_indicadores_inventario(inventario_df: pd.DataFrame, df_resultados: pd.DataFrame) -> Dict:
    """
    Calcula indicadores detallados de inventario
    """
    if inventario_df is None or inventario_df.empty:
        return {}
    
    # Stock total y por producto
    stock_total = inventario_df['Stock Actual'].sum()
    productos_con_stock = (inventario_df['Stock Actual'] > 0).sum()
    productos_totales = len(inventario_df)
    
    # Distribución de stock
    stock_promedio_por_producto = stock_total / productos_totales if productos_totales > 0 else 0
    
    # Productos con stock cero
    productos_sin_stock = (inventario_df['Stock Actual'] == 0).sum()
    porcentaje_sin_stock = (productos_sin_stock / productos_totales) * 100 if productos_totales > 0 else 0
    
    # Análisis de criticidad
    productos_criticos = 0
    productos_advertencia = 0
    productos_optimos = 0
    
    if df_resultados is not None and not df_resultados.empty:
        df_combinado = pd.merge(inventario_df, df_resultados, left_on='Producto', right_on='producto', how='left')
        
        productos_criticos = len(df_combinado[df_combinado['Stock Actual'] <= df_combinado['punto_reorden']])
        productos_advertencia = len(df_combinado[(df_combinado['Stock Actual'] > df_combinado['punto_reorden']) & 
                                                (df_combinado['Stock Actual'] <= df_combinado['punto_reorden'] * 1.5)])
        productos_optimos = productos_totales - productos_criticos - productos_advertencia
    
    # Valor del inventario (asumiendo costos promedio)
    valor_inventario = stock_total * 15  # Valor promedio de $15 por unidad
    costo_almacenaje_mensual = valor_inventario * 0.02  # 2% mensual
    
    # Análisis ABC si hay resultados
    analisis_abc = {}
    if df_resultados is not None and not df_resultados.empty:
        abc_counts = df_resultados['clasificacion_abc'].value_counts()
        analisis_abc = {
            'productos_A': abc_counts.get('A', 0),
            'productos_B': abc_counts.get('B', 0),
            'productos_C': abc_counts.get('C', 0)
        }
    
    return {
        'stock_total': stock_total,
        'productos_con_stock': productos_con_stock,
        'productos_totales': productos_totales,
        'stock_promedio_por_producto': stock_promedio_por_producto,
        'productos_sin_stock': productos_sin_stock,
        'porcentaje_sin_stock': porcentaje_sin_stock,
        'productos_criticos': productos_criticos,
        'productos_advertencia': productos_advertencia,
        'productos_optimos': productos_optimos,
        'valor_inventario': valor_inventario,
        'costo_almacenaje_mensual': costo_almacenaje_mensual,
        'analisis_abc': analisis_abc
    }

def calcular_eficiencia_operacional(ventas_kpis: Dict, inventario_kpis: Dict, df_ventas: pd.DataFrame) -> Dict:
    """
    Calcula indicadores de eficiencia operacional
    """
    if not ventas_kpis or not inventario_kpis:
        return {}
    
    # Rotación de inventario
    stock_total = inventario_kpis['stock_total']
    total_ventas = ventas_kpis['total_ventas']
    
    if stock_total > 0:
        rotacion_inventario = total_ventas / stock_total
        dias_inventario = stock_total / ventas_kpis['ventas_promedio_diarias'] if ventas_kpis['ventas_promedio_diarias'] > 0 else float('inf')
    else:
        rotacion_inventario = 0
        dias_inventario = 0
    
    # Fill Rate (basado en productos sin stock)
    productos_totales = inventario_kpis['productos_totales']
    productos_sin_stock = inventario_kpis['productos_sin_stock']
    
    fill_rate = ((productos_totales - productos_sin_stock) / productos_totales * 100) if productos_totales > 0 else 0
    
    # Nivel de servicio (basado en productos críticos)
    productos_criticos = inventario_kpis['productos_criticos']
    nivel_servicio = ((productos_totales - productos_criticos) / productos_totales * 100) if productos_totales > 0 else 0
    
    # Eficiencia de predicción (basada en volatilidad)
    volatilidad = ventas_kpis['volatilidad_ventas']
    ventas_promedio = ventas_kpis['ventas_promedio_diarias']
    
    if ventas_promedio > 0:
        eficiencia_prediccion = max(0, 100 - ventas_kpis['coeficiente_variacion'])
    else:
        eficiencia_prediccion = 0
    
    # Costos operativos estimados
    valor_inventario = inventario_kpis['valor_inventario']
    costo_almacenaje_anual = valor_inventario * 0.24  # 24% anual
    costo_quiebre_stock = productos_criticos * 500  # $500 por quiebre
    costo_exceso_stock = max(0, (stock_total - total_ventas) * 10)  # $10 por unidad excedente
    
    costo_total_optimizado = costo_almacenaje_anual + costo_quiebre_stock + costo_exceso_stock
    
    return {
        'rotacion_inventario': rotacion_inventario,
        'dias_inventario': dias_inventario if dias_inventario != float('inf') else 0,
        'fill_rate': fill_rate,
        'nivel_servicio': nivel_servicio,
        'eficiencia_prediccion': eficiencia_prediccion,
        'costo_almacenaje_anual': costo_almacenaje_anual,
        'costo_quiebre_stock': costo_quiebre_stock,
        'costo_exceso_stock': costo_exceso_stock,
        'costo_total_optimizado': costo_total_optimizado
    }

def generar_recomendaciones(kpis_ventas: Dict, kpis_inventario: Dict, kpis_eficiencia: Dict) -> List[str]:
    """
    Genera recomendaciones automáticas basadas en los KPIs
    """
    recomendaciones = []
    
    # Recomendaciones de ventas
    if kpis_ventas.get('tendencia_crecimiento', 0) < -10:
        recomendaciones.append("📉 **VENTAS:** Ventas en declive. Considera promociones, revisa precios o analiza competencia.")
    
    if kpis_ventas.get('coeficiente_variacion', 0) > 50:
        recomendaciones.append("📊 **VOLATILIDAD:** Alta variabilidad en ventas. Mejora la precisión de pronósticos con más datos históricos.")
    
    if kpis_ventas.get('concentracion_ventas', 0) > 80:
        recomendaciones.append("⚠️ **CONCENTRACIÓN:** Alta dependencia de pocos productos. Diversifica cartera o enfócate en productos clave.")
    
    # Recomendaciones de inventario
    if kpis_inventario.get('porcentaje_sin_stock', 0) > 10:
        recomendaciones.append("🚨 **STOCK OUT:** Más del 10% de productos sin stock. Revisa puntos de reorden inmediatamente.")
    
    if kpis_inventario.get('productos_criticos', 0) > 0:
        criticos = kpis_inventario['productos_criticos']
        recomendaciones.append(f"🔴 **CRÍTICO:** {criticos} productos necesitan reorden urgente. Genera órdenes de compra hoy.")
    
    if kpis_inventario.get('stock_total', 0) > kpis_ventas.get('total_ventas', 0) * 2:
        recomendaciones.append("📦 **EXCESO:** Stock excesivo detectado. Reduce órdenes o implementa promociones para mover inventario.")
    
    # Recomendaciones de eficiencia
    if kpis_eficiencia.get('rotacion_inventario', 0) < 1:
        recomendaciones.append("🔄 **ROTACIÓN:** Baja rotación de inventario. Revisa perfiles de producto y elimina SKUs no rentables.")
    
    if kpis_eficiencia.get('dias_inventario', 0) > 60:
        recomendaciones.append("⏱️ **DÍAS INVENTARIO:** Inventario obsoleto. Considera liquidación o donación de productos antiguos.")
    
    if kpis_eficiencia.get('fill_rate', 0) < 95:
        recomendaciones.append("📈 **FILL RATE:** Debajo del 95%. Aumenta niveles de safety stock o mejora tiempos de entrega.")
    
    if kpis_eficiencia.get('eficiencia_prediccion', 0) < 70:
        recomendaciones.append("🎯 **PRONÓSTICO:** Baja precisión en predicciones. Implementa modelos más sofisticados o segmenta por temporada.")
    
    # Recomendaciones de costos
    if kpis_eficiencia.get('costo_quiebre_stock', 0) > 1000:
        recomendaciones.append("💰 **COSTOS:** Altos costos por quiebre de stock. Invierte en buffer inventory o mejora procesos.")
    
    if kpis_eficiencia.get('costo_exceso_stock', 0) > 2000:
        recomendaciones.append("💸 **COSTOS:** Altos costos de exceso. Optimiza tamaños de lote y frecuencia de pedidos.")
    
    # Si todo está bien
    if not recomendaciones:
        recomendaciones.append("✅ **EXCELENTE:** Todos los indicadores están en rangos óptimos. Continúa monitoreando y mejora gradualmente.")
    
    return recomendaciones

def calcular_kpi_tendencias(df_ventas: pd.DataFrame, dias_periodo: int = 30) -> Dict:
    """
    Calcula tendencias específicas para el dashboard
    """
    if df_ventas is None or df_ventas.empty:
        return {}
    
    fecha_max = df_ventas['fecha'].max()
    
    # Períodos para comparación
    fecha_inicio_reciente = fecha_max - timedelta(days=dias_periodo)
    fecha_inicio_anterior = fecha_max - timedelta(days=dias_periodo * 2)
    fecha_fin_anterior = fecha_max - timedelta(days=dias_periodo + 1)
    
    # Ventas recientes
    ventas_recientes = df_ventas[df_ventas['fecha'] >= fecha_inicio_reciente]['cantidad_vendida'].sum()
    
    # Ventas período anterior
    ventas_anteriores = df_ventas[
        (df_ventas['fecha'] >= fecha_inicio_anterior) & 
        (df_ventas['fecha'] <= fecha_fin_anterior)
    ]['cantidad_vendida'].sum()
    
    # Cálculo de tendencia
    if ventas_anteriores > 0:
        tendencia_porcentual = ((ventas_recientes - ventas_anteriores) / ventas_anteriores) * 100
        cambio_absoluto = ventas_recientes - ventas_anteriores
    else:
        tendencia_porcentual = 100 if ventas_recientes > 0 else 0
        cambio_absoluto = ventas_recientes
    
    # Tendencia por producto
    productos_recientes = df_ventas[df_ventas['fecha'] >= fecha_inicio_reciente].groupby('producto')['cantidad_vendida'].sum()
    productos_anteriores = df_ventas[
        (df_ventas['fecha'] >= fecha_inicio_anterior) & 
        (df_ventas['fecha'] <= fecha_fin_anterior)
    ].groupby('producto')['cantidad_vendida'].sum()
    
    tendencias_producto = {}
    for producto in productos_recientes.index:
        venta_reciente = productos_recientes.get(producto, 0)
        venta_anterior = productos_anteriores.get(producto, 0)
        
        if venta_anterior > 0:
            tendencia = ((venta_reciente - venta_anterior) / venta_anterior) * 100
        else:
            tendencia = 100 if venta_reciente > 0 else 0
        
        tendencias_producto[producto] = tendencia
    
    return {
        'ventas_recientes': ventas_recientes,
        'ventas_anteriores': ventas_anteriores,
        'tendencia_porcentual': tendencia_porcentual,
        'cambio_absoluto': cambio_absoluto,
        'tendencias_producto': tendencias_producto
    }
