# modules/core_analysis.py

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union, List
from datetime import datetime
import warnings

# Ocultar advertencias de statsmodels
warnings.filterwarnings('ignore') 

# ============================================
# FUNCIONES DE ANÁLISIS (CORE DE LA APP)
# ============================================

def calcular_orden_optima_producto(
    df_producto: pd.DataFrame,
    nombre_producto: str,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> Dict[str, Union[float, str]]:
    """
    Calcula el punto de reorden para UN producto específico usando Holt-Winters.
    """
    try:
        # Preparar serie temporal
        df = df_producto.copy()
        df = df.set_index('fecha').sort_index()
        df_diario = df.resample('D').sum()
        df_diario['cantidad_vendida'] = df_diario['cantidad_vendida'].fillna(0)
        
        # Volumen Total Vendido (Necesario para ABC)
        volumen_total_vendido = df_diario['cantidad_vendida'].sum()
        
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'producto': nombre_producto,
                'error': f'Datos insuficientes (mínimo {frecuencia_estacional * 2} días)',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0,
                'volumen_total_vendido': volumen_total_vendido
            }
            
        # Modelo Holt-Winters
        serie_ventas = df_diario['cantidad_vendida']
        
        modelo = ExponentialSmoothing(
            serie_ventas,
            trend='add',
            seasonal='add',
            seasonal_periods=frecuencia_estacional
        )
        
        modelo_ajustado = modelo.fit(optimized=True)
        pronostico = modelo_ajustado.forecast(steps=lead_time)
        pronostico = pronostico.clip(lower=0)
        
        # Cálculos de Punto de Reorden (PR)
        demanda_lead_time = pronostico.sum()
        pronostico_diario_promedio = pronostico.mean()
        stock_seguridad = pronostico_diario_promedio * stock_seguridad_dias
        punto_reorden = demanda_lead_time + stock_seguridad
        
        # Cantidad a ordenar (cubre un horizonte de planeación, ej. media estacionalidad)
        orden_horizonte_dias = frecuencia_estacional / 2
        cantidad_a_ordenar = pronostico_diario_promedio * orden_horizonte_dias
        
        return {
            'producto': nombre_producto,
            'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'demanda_lead_time': round(demanda_lead_time, 2),
            'stock_seguridad': round(stock_seguridad, 2),
            'dias_historicos': len(df_diario),
            'volumen_total_vendido': volumen_total_vendido,
            # Datos para gráficos (para uso en la capa de componentes si es necesario)
            'datos_historicos': df_diario.tail(30).copy(),
            'pronostico_fechas': pronostico.index.tolist(),
            'pronostico_valores': pronostico.tolist()
        }
        
    except Exception as e:
        return {
            'producto': nombre_producto,
            'error': f'Error: {str(e)}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0,
            'volumen_total_vendido': 0.0
        }


def procesar_multiple_productos(
    df: pd.DataFrame,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> pd.DataFrame:
    """
    Procesa múltiples productos, realiza la clasificación ABC y devuelve un DataFrame.
    """
    resultados = []
    productos = df['producto'].unique()
    
    for producto in productos:
        df_producto = df[df['producto'] == producto][['fecha', 'cantidad_vendida']].copy()
        
        resultado = calcular_orden_optima_producto(
            df_producto,
            producto,
            lead_time,
            stock_seguridad_dias,
            frecuencia_estacional
        )
        resultados.append(resultado)
        
    # --- Clasificación ABC ---
    df_resultados = pd.DataFrame(resultados)

    if 'error' not in df_resultados.columns:
        df_resultados['error'] = None
    
    df_resultados['clasificacion_abc'] = 'N/A'

    # Filtrar solo productos con resultados exitosos y ventas > 0 para ABC
    df_abc = df_resultados[df_resultados['error'].isnull() & (df_resultados['volumen_total_vendido'] > 0)].copy()
    
    if not df_abc.empty:
        df_abc = df_abc.sort_values('volumen_total_vendido', ascending=False)
        total_volumen = df_abc['volumen_total_vendido'].sum()
        df_abc['volumen_pct'] = (df_abc['volumen_total_vendido'] / total_volumen) * 100
        df_abc['volumen_acum_pct'] = df_abc['volumen_pct'].cumsum()
        
        df_abc['clasificacion_abc'] = np.select(
            [
                df_abc['volumen_acum_pct'] <= 80, 
                df_abc['volumen_acum_pct'] <= 95    
            ],
            [
                'A',
                'B'
            ],
            default='C'
        )
        
        # Mapear las clasificaciones de vuelta al DataFrame completo de resultados
        df_resultados.loc[df_abc.index, 'clasificacion_abc'] = df_abc['clasificacion_abc']
    
    return df_resultados
