# modules/components.py (Solo se muestra la función modificada y las dependencias relevantes)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List, Union

# ... (Mantener todas las demás funciones: generar_inventario_base, sincronizar_puntos_optimos, inventario_basico_app) ...
# ... (Estas funciones son extensas, solo mostraré la función de gráfico aquí para brevedad) ...

def crear_grafico_trazabilidad_total(
    df_trazabilidad: pd.DataFrame, 
    resultado: Dict, 
    lead_time: int
):
    """
    Crea el gráfico de trazabilidad de Inventario (Histórico y Proyectado) 
    con doble eje para Stock y Demanda, incluyendo la simulación de órdenes.
    """
    nombre = resultado['producto']
    punto_reorden = resultado['punto_reorden']
    cantidad_a_ordenar = resultado['cantidad_a_ordenar']
    pronostico_diario_promedio = resultado['pronostico_diario_promedio']
    
    fig, ax1 = plt.subplots(figsize=(12, 6)) # Eje primario para STOCK
    ax2 = ax1.twinx() # Eje secundario para DEMANDA/VENTAS
    
    # ----------------------------------
    # Eje 1 (Izquierda): STOCK
    # ----------------------------------
    df_hist = df_trazabilidad[df_trazabilidad['Tipo'] == 'Histórico']
    df_proj = df_trazabilidad[df_trazabilidad['Tipo'] == 'Proyectado']
    
    ax1.plot(df_hist['Fecha'], df_hist['Stock'], 
            color='#1f77b4', linewidth=3, 
            label='Stock Real Histórico')
            
    ax1.plot(df_proj['Fecha'], df_proj['Stock'], 
            color='#ff7f0e', linewidth=2, linestyle='--',
            label='Stock Proyectado (Simulación PR)')

    # Líneas de Referencia de Stock
    ax1.axhline(y=punto_reorden, color='red', linestyle='-', 
               linewidth=1.5, alpha=0.8,
               label=f'Punto de Reorden ({punto_reorden:.0f})')
               
    stock_maximo = punto_reorden + cantidad_a_ordenar
    ax1.axhline(y=stock_maximo, color='green', linestyle=':', 
               linewidth=1.5, alpha=0.6,
               label=f'Stock Máximo Teórico ({stock_maximo:.0f})')
    
    ax1.set_ylabel('Stock (Unidades)', color='#1f77b4', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f77b4')

    # ----------------------------------
    # Eje 2 (Derecha): DEMANDA (Ventas + Pronóstico + Órdenes)
    # ----------------------------------
    
    # Ventas Históricas
    ax2.bar(df_hist['Fecha'], df_hist['Ventas'], 
            color='purple', alpha=0.3, width=1, 
            label='Venta Diaria Histórica')
            
    # Pronóstico de Demanda Diaria (línea constante en el futuro)
    pronostico_fechas = df_proj['Fecha']
    pronostico_valores = [pronostico_diario_promedio] * len(df_proj)
    
    if not pronostico_fechas.empty:
        ax2.plot(pronostico_fechas, pronostico_valores, 
                color='purple', linewidth=2, linestyle='-',
                label=f'Pronóstico Diario ({pronostico_diario_promedio:.1f})')
                
    # Mostrar las órdenes de compra simuladas (como scatter points)
    ordenes_simuladas = df_proj[df_proj['Simulacion_Entradas'] > 0].copy()
    
    if not ordenes_simuladas.empty:
        ax2.scatter(ordenes_simuladas['Fecha'], ordenes_simuladas['Simulacion_Entradas'], 
                    color='green', marker='^', s=100, zorder=5, 
                    label=f'Entrega de Orden Simulada ({cantidad_a_ordenar:.0f})')


    ax2.set_ylabel('Demanda Diaria y Órdenes', color='purple', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.set_ylim(bottom=0)
    
    # ----------------------------------
    # Configuración General
    # ----------------------------------
    
    fecha_actual = datetime.now().date()
    ax1.axvline(x=fecha_actual, color='gray', linestyle='-.', alpha=0.5, label='Fecha Actual')
    
    ax1.set_xlabel('Fecha', fontsize=12)
    ax1.set_title(f'📉 {nombre}: Stock, Ventas y Simulación de Órdenes (PR)', 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # Asegurar una densidad razonable de ticks
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df_trazabilidad) // 10))) 
    plt.xticks(rotation=45, ha='right')
    
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Combinar leyendas de ambos ejes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9, framealpha=0.9)
    
    plt.tight_layout()
    
    return fig

# ... (Aquí va el resto de las funciones de modules/components.py sin modificaciones) ...
