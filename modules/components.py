# modules/components.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List

# ============================================
# FUNCIONES DE INTERFAZ Y COMPONENTES (UI)
# ============================================

def generar_inventario_base(df_ventas: pd.DataFrame = None) -> pd.DataFrame:
    """
    Genera un DataFrame base para el inventario, usando productos de ventas si están disponibles.
    """
    productos_de_ventas = []
    if df_ventas is not None:
        productos_de_ventas = sorted(df_ventas['producto'].unique().tolist())
        
    if not productos_de_ventas:
        productos_base = ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)']
        stock_init = 50.0
        pr_init = 10.0
        costo_init = 5.0
        orden_init = 20.0
    else:
        productos_base = productos_de_ventas
        stock_init = 0.0
        pr_init = 0.0
        costo_init = 1.0
        orden_init = 0.0

    data = {
        'Producto': productos_base,
        'Categoría': ['Insumo'] * len(productos_base),
        'Unidad': ['UNI'] * len(productos_base),
        'Stock Actual': [stock_init] * len(productos_base),
        'Punto de Reorden (PR)': [pr_init] * len(productos_base),
        'Cantidad a Ordenar': [orden_init] * len(productos_base),
        'Costo Unitario': [costo_init] * len(productos_base),
    }
    df = pd.DataFrame(data)
    
    # Asignación de unidades basada en el nombre
    df['Unidad'] = np.select(
        [
            df['Producto'].str.contains(r'\(Kg\)', na=False, case=False),
            df['Producto'].str.contains(r'\(L\)', na=False, case=False),
            df['Producto'].str.contains(r'\(Uni\)', na=False, case=False)
        ],
        ['KG', 'L', 'UNI'],
        default='UNI'
    )
    
    # Cálculos iniciales
    df['Faltante?'] = df['Stock Actual'] < df['Punto de Reorden (PR)']
    df['Valor Total'] = df['Stock Actual'] * df['Costo Unitario']
    return df

def sincronizar_puntos_optimos(df_inventario: pd.DataFrame, df_resultados: pd.DataFrame) -> pd.DataFrame:
    """
    Actualiza las columnas 'Punto de Reorden (PR)' y 'Cantidad a Ordenar' 
    en el inventario con los valores calculados.
    """
    # 1. Crear diccionarios de valores {producto: valor}
    pr_map = df_resultados.set_index('producto')['punto_reorden'].to_dict()
    orden_map = df_resultados.set_index('producto')['cantidad_a_ordenar'].to_dict()
    
    # Asegurar que las columnas del inventario sean numéricas
    for col in ['Punto de Reorden (PR)', 'Cantidad a Ordenar']:
        df_inventario[col] = pd.to_numeric(df_inventario[col], errors='coerce').fillna(0)
    
    # 2. Mapear y actualizar PR
    df_inventario['PR Mapeado'] = df_inventario['Producto'].map(pr_map).fillna(0)
    df_inventario['Punto de Reorden (PR)'] = np.where(
        df_inventario['PR Mapeado'] > 0, 
        df_inventario['PR Mapeado'].round(2),
        df_inventario['Punto de Reorden (PR)']
    )
    df_inventario = df_inventario.drop(columns=['PR Mapeado'], errors='ignore')
    
    # 3. Mapear y actualizar Cantidad a Ordenar
    df_inventario['Orden Mapeado'] = df_inventario['Producto'].map(orden_map).fillna(0)
    df_inventario['Cantidad a Ordenar'] = np.where(
        df_inventario['Orden Mapeado'] > 0, 
        df_inventario['Orden Mapeado'].round(2),
        df_inventario['Cantidad a Ordenar']
    )
    df_inventario = df_inventario.drop(columns=['Orden Mapeado'], errors='ignore')
    
    return df_inventario


def inventario_basico_app():
    """
    Componente completo para la interfaz del control de inventario básico.
    """
    
    st.header("🛒 Control de Inventario Básico")
    st.info("💡 Usa esta sección para gestionar el stock físico. **Actualiza 'Stock Actual'** aquí. El **Punto de Reorden (PR)** y la **Cantidad a Ordenar** se actualizan automáticamente con el análisis.")

    # --- Lógica de inicialización y SINCRONIZACIÓN ---
    
    # Inicializar con productos de ventas si existen
    df_ventas_temp = st.session_state.get('df_ventas_trazabilidad')
    if 'inventario_df' not in st.session_state:
        st.session_state['inventario_df'] = generar_inventario_base(df_ventas_temp)
        
    df_inventario_actual = st.session_state['inventario_df'].copy()
    
    # 1. Sincronizar PR y Cantidad a Ordenar si los resultados están disponibles
    if 'df_resultados' in st.session_state:
        df_resultados = st.session_state['df_resultados']
        if not df_resultados.empty:
            df_inventario_actual = sincronizar_puntos_optimos(df_inventario_actual, df_resultados)
            st.session_state['inventario_df'] = df_inventario_actual 

    # 2. Sincronización de productos nuevos de ventas
    if df_ventas_temp is not None:
        productos_de_ventas_actuales = set(df_ventas_temp['producto'].unique().tolist())
        productos_en_inventario = set(df_inventario_actual['Producto'].tolist())
        nuevos_productos = list(productos_de_ventas_actuales - productos_en_inventario)
        
        if nuevos_productos:
            # Crea y concatena nuevos productos (con PR/Stock/Orden en 0)
            data_nuevos = {
                'Producto': nuevos_productos,
                'Categoría': ['Insumo'] * len(nuevos_productos),
                'Unidad': ['UNI'] * len(nuevos_productos),
                'Stock Actual': [0.0] * len(nuevos_productos),
                'Punto de Reorden (PR)': [0.0] * len(nuevos_productos),
                'Cantidad a Ordenar': [0.0] * len(nuevos_productos),
                'Costo Unitario': [1.0] * len(nuevos_productos),
                'Faltante?': [True] * len(nuevos_productos),
                'Valor Total': [0.0] * len(nuevos_productos),
            }
            df_nuevos = pd.DataFrame(data_nuevos)
            df_inventario_actual = pd.concat([df_inventario_actual, df_nuevos], ignore_index=True)
            st.session_state['inventario_df'] = df_inventario_actual
            st.info(f"✨ Se han agregado **{len(nuevos_productos)}** productos nuevos de tu archivo de ventas a esta tabla.")
    
    df_inventario = st.session_state['inventario_df'].copy()

    # --- Edición del DataFrame ---
    st.subheader("1️⃣ Inventario Actual (Edición en Vivo)")
    
    editable_columns = ['Producto', 'Categoría', 'Unidad', 'Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar', 'Costo Unitario']
    column_config = {
        "Producto": st.column_config.TextColumn("Producto", required=True),
        "Stock Actual": st.column_config.NumberColumn("Stock Actual", required=True, format="%.2f"),
        # DESHABILITADO: PR y Cantidad a Ordenar deben venir del cálculo
        "Punto de Reorden (PR)": st.column_config.NumberColumn("Punto de Reorden (PR)", required=True, format="%.2f", disabled=True),
        "Cantidad a Ordenar": st.column_config.NumberColumn("Cantidad a Ordenar", required=True, format="%.2f", disabled=True),
        "Costo Unitario": st.column_config.NumberColumn("Costo Unitario", format="$%.2f"),
        "Faltante?": st.column_config.CheckboxColumn("Faltante?", disabled=True),
        "Valor Total": st.column_config.NumberColumn("Valor Total", disabled=True, format="$%.2f"),
    }
    
    df_editable_subset = df_inventario[editable_columns]
    
    edited_df = st.data_editor(
        df_editable_subset,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_inventario"
    )

    # Re-calcular columnas derivadas (manejo robusto de NaN)
    if not edited_df.empty:
        try:
            df_final = edited_df.copy()
            
            for col in ['Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar', 'Costo Unitario']:
                df_final.loc[:, col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
            
            df_final.loc[:, 'Faltante?'] = df_final['Stock Actual'] < df_final['Punto de Reorden (PR)']
            df_final.loc[:, 'Valor Total'] = df_final['Stock Actual'] * df_final['Costo Unitario']
            
            st.session_state['inventario_df'] = df_final
            
        except Exception as e:
            st.error(f"Error al procesar la tabla editada. Detalle: {e}")
            st.stop()

    df_actual = st.session_state['inventario_df']

    # --- Alertas y Totales ---
    st.subheader("2️⃣ Alertas y Totales")

    items_faltantes = df_actual[df_actual['Faltante?']].sort_values('Punto de Reorden (PR)', ascending=False)
    total_valor = df_actual['Valor Total'].sum()
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("🚨 Ítems con Bajo Stock", f"{len(items_faltantes)}")
    with col_b:
        st.metric("💰 Valor Total del Inventario", f"${total_valor:,.2f}")

    if not items_faltantes.empty:
        st.warning("⚠️ **¡URGENTE!** Los siguientes ítems están por debajo de su Punto de Reorden y deben ser pedidos.")
        # Muestra la Cantidad a Ordenar
        st.dataframe(
            items_faltantes[['Producto', 'Unidad', 'Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 Todo el inventario está en niveles óptimos.")

    # --- Descarga ---
    st.markdown("---")
    st.download_button(
        "⬇️ Descargar Inventario Actual (CSV)",
        df_actual.to_csv(index=False).encode('utf-8'),
        f"inventario_basico_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv",
        use_container_width=True
    )


def crear_grafico_trazabilidad_total(
    df_trazabilidad: pd.DataFrame, 
    resultado: Dict, 
    lead_time: int
):
    """
    Crea el gráfico de trazabilidad de Inventario (Histórico y Proyectado).
    """
    nombre = resultado['producto']
    punto_reorden = resultado['punto_reorden']
    cantidad_a_ordenar = resultado['cantidad_a_ordenar']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    df_hist = df_trazabilidad[df_trazabilidad['Tipo'] == 'Histórico']
    df_proj = df_trazabilidad[df_trazabilidad['Tipo'] == 'Proyectado']
    
    ax.plot(df_hist['Fecha'], df_hist['Stock'], 
            color='#1f77b4', linewidth=3, 
            label='Stock Real Histórico')
            
    ax.plot(df_proj['Fecha'], df_proj['Stock'], 
            color='#ff7f0e', linewidth=2, linestyle='--',
            label='Stock Proyectado (Demanda media)')

    ax.axhline(y=punto_reorden, color='red', linestyle='-', 
               linewidth=1.5, alpha=0.8,
               label=f'Punto de Reorden ({punto_reorden:.0f})')
               
    stock_maximo = punto_reorden + cantidad_a_ordenar
    ax.axhline(y=stock_maximo, color='green', linestyle=':', 
               linewidth=1.5, alpha=0.6,
               label=f'Stock Máximo Teórico ({stock_maximo:.0f})')
               
    fecha_actual = datetime.now().date()
    ax.axvline(x=fecha_actual, color='gray', linestyle='-.', alpha=0.5, label='Fecha Actual')
    
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Stock (Unidades)', fontsize=12)
    ax.set_title(f'📉 Trazabilidad y Proyección de Inventario para {nombre}', 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df_trazabilidad) // 10)))
    plt.xticks(rotation=45, ha='right')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    plt.tight_layout()
    
    return fig


def crear_grafico_comparativo(resultados: List[Dict]):
    """
    Crea el gráfico de volumen total de ventas para la visión general.
    """
    df = pd.DataFrame([r for r in resultados if r.get('error') is None])
    if df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title('No hay datos suficientes para la Visión General.')
        return fig
        
    df_sorted = df.sort_values('volumen_total_vendido', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_sorted['producto'], df_sorted['volumen_total_vendido'], color='skyblue')
    ax.set_title('Volumen Total de Ventas por Producto')
    ax.set_ylabel('Unidades Vendidas')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return fig
