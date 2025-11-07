import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union
import warnings
warnings.filterwarnings('ignore')


def calcular_orden_optima(
    ruta_archivo_csv: str,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> Dict[str, Union[float, str]]:
    """
    Calcula el punto de reorden y la cantidad óptima a ordenar usando Holt-Winters.
    
    Args:
        ruta_archivo_csv: Ruta al archivo CSV con columnas 'fecha' y 'cantidad_vendida'
        lead_time: Días que tarda el proveedor en entregar (default: 7)
        stock_seguridad_dias: Días adicionales de inventario de seguridad (default: 3)
        frecuencia_estacional: Periodicidad de la estacionalidad en días (default: 7 para semanal)
    
    Returns:
        Diccionario con métricas de inventario redondeadas a 2 decimales
    """
    
    try:
        # 1. CARGA Y VALIDACIÓN DE DATOS
        df = pd.read_csv(ruta_archivo_csv)
        
        # Validar que existan las columnas necesarias
        if 'fecha' not in df.columns or 'cantidad_vendida' not in df.columns:
            return {
                'error': 'El CSV debe contener las columnas: fecha, cantidad_vendida',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0
            }
        
        # Convertir fecha a datetime
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
        
        # Asegurar que cantidad_vendida sea numérica
        df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce').fillna(0)
        
        # 2. PREPARACIÓN DE SERIE TEMPORAL CONTINUA
        df = df.set_index('fecha').sort_index()
        
        # Resample diario y rellenar días sin ventas con cero
        df_diario = df.resample('D').sum()
        df_diario['cantidad_vendida'] = df_diario['cantidad_vendida'].fillna(0)
        
        # Validar que haya suficientes datos para el modelo
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'error': f'Se necesitan al menos {frecuencia_estacional * 2} días de datos históricos',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0
            }
        
        # 3. MODELO HOLT-WINTERS ESTACIONAL
        serie_ventas = df_diario['cantidad_vendida']
        
        # Configurar y entrenar el modelo
        modelo = ExponentialSmoothing(
            serie_ventas,
            trend='add',
            seasonal='add',
            seasonal_periods=frecuencia_estacional
        )
        
        modelo_ajustado = modelo.fit(optimized=True)
        
        # Generar pronóstico para los días del lead time
        pronostico = modelo_ajustado.forecast(steps=lead_time)
        
        # Asegurar que no haya valores negativos en el pronóstico
        pronostico = pronostico.clip(lower=0)
        
        # 4. CÁLCULOS DE NEGOCIO
        
        # Demanda durante el Lead Time
        demanda_lead_time = pronostico.sum()
        
        # Pronóstico diario promedio (del lead time)
        pronostico_diario_promedio = pronostico.mean()
        
        # Stock de Seguridad
        stock_seguridad = pronostico_diario_promedio * stock_seguridad_dias
        
        # Punto de Reorden
        punto_reorden = demanda_lead_time + stock_seguridad
        
        # Cantidad a Ordenar (cobertura de 14 días)
        cantidad_a_ordenar = pronostico_diario_promedio * 14
        
        # 5. PREPARAR OUTPUT
        resultado = {
            'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'demanda_lead_time': round(demanda_lead_time, 2),
            'stock_seguridad': round(stock_seguridad, 2),
            'dias_historicos_analizados': len(df_diario),
            'configuracion': {
                'lead_time': lead_time,
                'stock_seguridad_dias': stock_seguridad_dias,
                'frecuencia_estacional': frecuencia_estacional
            }
        }
        
        return resultado
        
    except FileNotFoundError:
        return {
            'error': f'Archivo no encontrado: {ruta_archivo_csv}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0
        }
    
    except Exception as e:
        return {
            'error': f'Error en el cálculo: {str(e)}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0
        }


# ============================================
# EJEMPLO DE USO CON DATOS SIMULADOS
# ============================================

def generar_datos_simulados_csv(nombre_archivo: str = 'ventas_simuladas.csv'):
    """
    Genera un CSV de ejemplo con estacionalidad semanal (fines de semana más altos)
    """
    import datetime
    
    # Generar 60 días de datos
    fecha_inicio = datetime.date(2024, 9, 1)
    fechas = [fecha_inicio + datetime.timedelta(days=i) for i in range(60)]
    
    # Simular ventas con patrón semanal (más ventas en viernes-sábado-domingo)
    np.random.seed(42)
    ventas = []
    
    for fecha in fechas:
        dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
        
        # Base de ventas
        venta_base = 50
        
        # Multiplicador por día de la semana
        if dia_semana in [4, 5, 6]:  # Viernes, Sábado, Domingo
            multiplicador = np.random.uniform(1.5, 2.0)
        else:
            multiplicador = np.random.uniform(0.8, 1.2)
        
        # Añadir ruido aleatorio
        venta = int(venta_base * multiplicador + np.random.normal(0, 10))
        venta = max(0, venta)  # No puede ser negativa
        
        ventas.append(venta)
    
    # Crear DataFrame
    df = pd.DataFrame({
        'fecha': fechas,
        'cantidad_vendida': ventas
    })
    
    # Simular días sin ventas (data sucia real de Pymes)
    indices_faltantes = np.random.choice(df.index, size=5, replace=False)
    df.loc[indices_faltantes, 'cantidad_vendida'] = np.nan
    
    # Guardar CSV
    df.to_csv(nombre_archivo, index=False)
    print(f"✓ Archivo '{nombre_archivo}' generado con {len(df)} días de datos")
    print(f"  - Incluye estacionalidad semanal (fines de semana altos)")
    print(f"  - Incluye {len(indices_faltantes)} días con datos faltantes")
    
    return nombre_archivo


# EJECUTAR EJEMPLO
if __name__ == "__main__":
    print("=" * 60)
    print("STOCK ZERO - MVP Backend")
    print("Cálculo de Inventario Óptimo para Pymes")
    print("=" * 60)
    print()
    
    # 1. Generar datos simulados
    archivo_csv = generar_datos_simulados_csv()
    print()
    
    # 2. Ejecutar cálculo
    print("Ejecutando cálculo de inventario óptimo...")
    resultado = calcular_orden_optima(
        ruta_archivo_csv=archivo_csv,
        lead_time=7,
        stock_seguridad_dias=3,
        frecuencia_estacional=7
    )
    
    print()
    print("=" * 60)
    print("RESULTADOS DEL ANÁLISIS")
    print("=" * 60)
    
    if 'error' in resultado:
        print(f"❌ ERROR: {resultado['error']}")
    else:
        print(f"📊 Días históricos analizados: {resultado['dias_historicos_analizados']}")
        print()
        print("MÉTRICAS CLAVE:")
        print(f"  • Pronóstico Diario Promedio: {resultado['pronostico_diario_promedio']} unidades")
        print(f"  • Demanda durante Lead Time: {resultado['demanda_lead_time']} unidades")
        print(f"  • Stock de Seguridad: {resultado['stock_seguridad']} unidades")
        print()
        print("RECOMENDACIONES DE COMPRA:")
        print(f"  🎯 PUNTO DE REORDEN: {resultado['punto_reorden']} unidades")
        print(f"  📦 CANTIDAD A ORDENAR: {resultado['cantidad_a_ordenar']} unidades")
        print()
        print("CONFIGURACIÓN UTILIZADA:")
        print(f"  - Lead Time: {resultado['configuracion']['lead_time']} días")
        print(f"  - Stock de Seguridad: {resultado['configuracion']['stock_seguridad_dias']} días")
        print(f"  - Frecuencia Estacional: {resultado['configuracion']['frecuencia_estacional']} días")
    
    print("=" * 60)