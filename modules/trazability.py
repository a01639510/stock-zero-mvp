# modules/trazability.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Union

def calcular_trazabilidad_inventario(
    df_ventas: pd.DataFrame, 
    df_entradas: pd.DataFrame, 
    nombre_producto: str, 
    stock_actual_manual: float,
    punto_reorden: float,
    cantidad_a_ordenar: float,
    pronostico_diario_promedio: float,
    lead_time: int
) -> Union[pd.DataFrame, None]:
    """
    Calcula la trazabilidad histórica del stock y la proyecta al futuro,
    simulando órdenes de compra al tocar el PR.
    """
    
    # --- 1. PREPARACIÓN DE DATOS DIARIOS ---
    
    ventas_prod = df_ventas[df_ventas['producto'] == nombre_producto][['fecha', 'cantidad_vendida']].copy()
    entradas_prod = df_entradas[df_entradas['producto'] == nombre_producto][['fecha', 'cantidad_recibida']].copy()
    
    if ventas_prod.empty and entradas_prod.empty:
        return None

    # Limpieza de tipos (Robusta)
    ventas_prod['cantidad_vendida'] = pd.to_numeric(ventas_prod['cantidad_vendida'], errors='coerce').fillna(0)
    entradas_prod['cantidad_recibida'] = pd.to_numeric(entradas_prod['cantidad_recibida'], errors='coerce').fillna(0)
    
    # Rango de fechas: Desde el inicio de los datos hasta hoy + 60 días
    
    # CORRECCIÓN CLAVE: Usamos .now().date() para obtener un objeto de fecha nativa
    # y luego lo convertimos a datetime con tiempo 00:00:00. 
    fecha_actual = datetime.now().date()
    fecha_actual_dt = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day)
    
    # Obtener las fechas mínimas ya normalizadas (a 00:00:00) del DataFrame principal
    min_date_ventas = ventas_prod['fecha'].min() if not ventas_prod.empty and not pd.isna(ventas_prod['fecha'].min()) else fecha_actual_dt
    min_date_entradas = entradas_prod['fecha'].min() if not entradas_prod.empty and not pd.isna(entradas_prod['fecha'].min()) else fecha_actual_dt

    # Aseguramos que solo comparamos objetos datetime.datetime o pd.Timestamp (que se comportan similarmente aquí)
    min_date = min(min_date_ventas, min_date_entradas)
    
    dias_proyeccion = 60
    fechas = pd.date_range(start=min_date, end=fecha_actual_dt + timedelta(days=dias_proyeccion), name='Fecha')
    
    df_diario = pd.DataFrame(index=fechas)
    df_diario['Ventas'] = 0.0
    df_diario['Entradas'] = 0.0
    
    # Mapear ventas y entradas históricas
    if not ventas_prod.empty:
        # Aseguramos que la columna 'fecha' sea el índice y luego la re-muestreamos
        ventas_diarias = ventas_prod.set_index('fecha').resample('D').sum()['cantidad_vendida']
        ventas_diarias = pd.Series(ventas_diarias).fillna(0)
        df_diario.loc[df_diario.index.intersection(ventas_diarias.index), 'Ventas'] = ventas_diarias
        
    if not entradas_prod.empty:
        entradas_diarias = entradas_prod.set_index('fecha').resample('D').sum()['cantidad_recibida']
        entradas_diarias = pd.Series(entradas_diarias).fillna(0)
        df_diario.loc[df_diario.index.intersection(entradas_diarias.index), 'Entradas'] = entradas_diarias

    # --- 2. CÁLCULO DE INVENTARIO (Simulación de PR) ---
    
    df_diario['Stock'] = 0.0
    df_diario['Simulacion_Entradas'] = 0.0
    
    df_diario['Tipo'] = np.where(df_diario.index.date <= fecha_actual_dt.date(), 'Histórico', 'Proyectado')
    
    stock_t = stock_actual_manual
    
    # Iterar día a día
    for i, date_ts in enumerate(df_diario.index):
        if i == 0:
            df_diario.loc[date_ts, 'Stock'] = stock_t
            continue
            
        idx_anterior = df_diario.index[i - 1]
        
        # 1. Stock del inicio del día = Stock del día anterior
        stock_t = df_diario.loc[idx_anterior, 'Stock']
        
        # 2. Determinar la Demanda y Entradas
        is_historico = df_diario.loc[date_ts, 'Tipo'] == 'Histórico'
        
        demanda_t = df_diario.loc[date_ts, 'Ventas'] if is_historico else pronostico_diario_promedio
        entradas_reales_t = df_diario.loc[date_ts, 'Entradas'] if is_historico else 0
        
        simulacion_entrada_t = 0.0
        
        # 3. Simular Orden de Compra (Solo en la proyección)
        if not is_historico:
            # Comprobamos el PR ANTES de consumir la demanda del día
            if stock_t <= punto_reorden:
                fecha_llegada = date_ts + timedelta(days=lead_time)
                
                # Agregamos la orden de compra en la fecha de llegada
                if fecha_llegada in df_diario.index:
                    df_diario.loc[fecha_llegada, 'Simulacion_Entradas'] += cantidad_a_ordenar
                    
            # Si hoy llegó una orden simulada, la agregamos al stock
            simulacion_entrada_t = df_diario.loc[date_ts, 'Simulacion_Entradas']

        # 4. Cálculo del Stock Final del Día
        stock_final = stock_t - demanda_t + entradas_reales_t + simulacion_entrada_t
        stock_final = max(0, stock_final)
        
        # 5. Guardar Stock para el día actual
        df_diario.loc[date_ts, 'Stock'] = stock_final
        
    return df_diario.reset_index()
