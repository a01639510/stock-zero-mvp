# modules/trazability.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Union, List

# ============================================
# FUNCIONES DE TRAZABILIDAD
# ============================================

def calcular_trazabilidad_inventario(
    df_ventas: pd.DataFrame, 
    df_entradas: pd.DataFrame, 
    nombre_producto: str, 
    stock_actual_manual: float,
    pronostico_diario_promedio: float,
    lead_time: int
) -> Union[pd.DataFrame, None]:
    """
    Calcula la trazabilidad histórica del stock y la proyecta al futuro. 
    Asegura la robustez de los tipos de datos para prevenir errores de 'fillna'.
    """
    
    # --- 1. PREPARACIÓN DE DATOS DIARIOS Y LIMPIEZA DE TIPOS ---
    
    # Filtrar datos del producto
    ventas_prod = df_ventas[df_ventas['producto'] == nombre_producto][['fecha', 'cantidad_vendida']].copy()
    entradas_prod = df_entradas[df_entradas['producto'] == nombre_producto][['fecha', 'cantidad_recibida']].copy()
    
    if ventas_prod.empty and entradas_prod.empty:
        return None

    # CORRECCIÓN DE TIPO: Asegurar que las columnas de cantidad sean numéricas y manejar NaN al inicio
    ventas_prod['cantidad_vendida'] = pd.to_numeric(ventas_prod['cantidad_vendida'], errors='coerce').fillna(0)
    entradas_prod['cantidad_recibida'] = pd.to_numeric(entradas_prod['cantidad_recibida'], errors='coerce').fillna(0)
    
    # Determinar el rango de fechas para el análisis
    fecha_actual = datetime.now().date()

    min_date_ventas = ventas_prod['fecha'].min().date() if not ventas_prod.empty else fecha_actual
    min_date_entradas = entradas_prod['fecha'].min().date() if not entradas_prod.empty else fecha_actual
    min_date = min(min_date_ventas, min_date_entradas)
    
    # Crear índice diario que cubra el historial y la proyección
    dias_proyeccion = (fecha_actual - min_date).days + lead_time + 10
    fechas = pd.date_range(start=min_date, periods=dias_proyeccion, name='Fecha')
    
    df_diario = pd.DataFrame(index=fechas)
    df_diario['Ventas'] = 0.0
    df_diario['Entradas'] = 0.0
    
    # Resample y mapear datos
    if not ventas_prod.empty:
        # Extraemos la Serie
        ventas_diarias = ventas_prod.set_index('fecha').resample('D').sum()['cantidad_vendida']
        # NUEVA CORRECCIÓN: Forzamos a que sea una Serie de Pandas antes de llamar a fillna
        ventas_diarias = pd.Series(ventas_diarias).fillna(0) 
        df_diario.loc[df_diario.index.intersection(ventas_diarias.index), 'Ventas'] = ventas_diarias
        
    if not entradas_prod.empty:
        # Extraemos la Serie
        entradas_diarias = entradas_prod.set_index('fecha').resample('D').sum()['cantidad_recibida']
        # NUEVA CORRECCIÓN: Forzamos a que sea una Serie de Pandas antes de llamar a fillna
        entradas_diarias = pd.Series(entradas_diarias).fillna(0) 
        df_diario.loc[df_diario.index.intersection(entradas_diarias.index), 'Entradas'] = entradas_diarias

    # --- 2. CÁLCULO DEL INVENTARIO HISTÓRICO (HACIA ATRÁS) ---
    
    df_diario['Stock'] = 0.0
    stock_t = stock_actual_manual
    
    # Asegurar el stock del día de hoy (punto de anclaje)
    try:
        df_diario.loc[fecha_actual.strftime("%Y-%m-%d"), 'Stock'] = stock_actual_manual
    except KeyError:
         pass 
    
    # Iterar hacia atrás desde la fecha actual
    for date_ts in reversed(df_diario.index):
        date = date_ts.date()
        
        if date > fecha_actual:
            continue
        
        df_diario.loc[date_ts, 'Stock'] = stock_t
        
        ventas_t = df_diario.loc[date_ts, 'Ventas']
        entradas_t = df_diario.loc[date_ts, 'Entradas']
        
        # Fórmula inversa: Stock del día anterior = Stock de hoy + Ventas de hoy - Entradas de hoy
        stock_t = stock_t + ventas_t - entradas_t
        stock_t = max(0, stock_t)
            
    # --- 3. PROYECCIÓN DEL INVENTARIO FUTURO (HACIA ADELANTE) ---

    for i, date_ts in enumerate(df_diario.index):
        date = date_ts.date()
        
        if date > fecha_actual:
            
            # Obtener el stock del día anterior
            idx_anterior = df_diario.index[i - 1]
            stock_anterior = df_diario.loc[idx_anterior, 'Stock']
            
            # Stock proyectado = Stock anterior - Consumo promedio diario (pronóstico)
            stock_proyectado = stock_anterior - pronostico_diario_promedio
            
            df_diario.loc[date_ts, 'Stock'] = max(0, stock_proyectado)
            
    # --- 4. MARCAR LA DIVISIÓN ---
    
    # Usar np.where para etiquetar las filas como Histórico o Proyectado
    fechas_indice = np.array([d.date() for d in df_diario.index])
    df_diario['Tipo'] = np.where(fechas_indice <= fecha_actual, 'Histórico', 'Proyectado')
    
    return df_diario.reset_index()
