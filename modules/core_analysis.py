# modules/core_analysis.py

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union, List
import numpy as np

def calcular_orden_optima_producto(
    df_producto: pd.DataFrame,
    nombre_producto: str,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> Dict[str, Union[float, str]]:
    """Calcula el punto de reorden y la cantidad a ordenar para UN producto."""
    try:
        df = df_producto.copy()
        df = df.set_index('fecha').sort_index()
        df_diario = df.resample('D').sum()
        df_diario['cantidad_vendida'] = df_diario['cantidad_vendida'].fillna(0)
        
        volumen_total_vendido = df_diario['cantidad_vendida'].sum()
        
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'producto': nombre_producto, 'error': 'Datos insuficientes (mínimo de estacionalidad)',
                'punto_reorden': 0.0, 'cantidad_a_ordenar': 0.0, 'pronostico_diario_promedio': 0.0, 
                'volumen_total_vendido': volumen_total_vendido
            }
            
        serie_ventas = df_diario['cantidad_vendida']
        
        # Modelo Holt-Winters
        modelo = ExponentialSmoothing(
            serie_ventas, trend='add', seasonal='add', seasonal_periods=frecuencia_estacional
        )
        
        modelo_ajustado = modelo.fit(optimized=True)
        
        # El pronóstico se calcula para el Lead Time
        pronostico = modelo_ajustado.forecast(steps=lead_time)
        pronostico = pronostico.clip(lower=0)
        
        demanda_lead_time = pronostico.sum()
        pronostico_diario_promedio = pronostico.mean()
        stock_seguridad = pronostico_diario_promedio * stock_seguridad_dias
        
        # Cálculo de PR y Cantidad a Ordenar
        punto_reorden = demanda_lead_time + stock_seguridad
        
        # La cantidad a ordenar puede ser el consumo de medio ciclo
        orden_horizonte_dias = frecuencia_estacional / 2 
        cantidad_a_ordenar = pronostico_diario_promedio * orden_horizonte_dias
        
        return {
            'producto': nombre_producto, 'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'volumen_total_vendido': volumen_total_vendido
        }
        
    except Exception as e:
        return {
            'producto': nombre_producto, 'error': f'Error: {str(e)}',
            'punto_reorden': 0.0, 'cantidad_a_ordenar': 0.0, 'pronostico_diario_promedio': 0.0, 
            'volumen_total_vendido': 0.0
        }


def procesar_multiple_productos(
    df: pd.DataFrame,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> pd.DataFrame:
    """Procesa múltiples productos, realiza la clasificación ABC y devuelve un DataFrame."""
    resultados = []
    productos = df['producto'].unique()
    
    for producto in productos:
        df_producto = df[df['producto'] == producto][['fecha', 'cantidad_vendida']].copy()
        
        resultado = calcular_orden_optima_producto(df_producto, producto, lead_time, stock_seguridad_dias, frecuencia_estacional)
        resultados.append(resultado)
        
    df_resultados = pd.DataFrame(resultados)

    if 'error' not in df_resultados.columns:
        df_resultados['error'] = None
    
    df_resultados['clasificacion_abc'] = 'N/A'

    # Clasificación ABC
    df_abc = df_resultados[df_resultados['error'].isnull() & (df_resultados['volumen_total_vendido'] > 0)].copy()
    
    if not df_abc.empty:
        df_abc = df_abc.sort_values('volumen_total_vendido', ascending=False)
        total_volumen = df_abc['volumen_total_vendido'].sum()
        df_abc['volumen_pct'] = (df_abc['volumen_total_vendido'] / total_volumen) * 100
        df_abc['volumen_acum_pct'] = df_abc['volumen_pct'].cumsum()
        
        df_abc['clasificacion_abc'] = np.select(
            [df_abc['volumen_acum_pct'] <= 80, df_abc['volumen_acum_pct'] <= 95],
            ['A', 'B'],
            default='C'
        )
        
        df_resultados.loc[df_abc.index, 'clasificacion_abc'] = df_abc['clasificacion_abc']
    
    return df_resultados
