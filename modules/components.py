# modules/components.py
import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List  # ← IMPORTS CORRECTOS

# ============================================
# 1. GENERAR INVENTARIO BASE
# ============================================
def generar_inventario_base(df_ventas=None, use_example_data=False):
    """
    Genera inventario base a partir de ventas o ejemplo
    """
    if use_example_data or df_ventas is None:
        return pd.DataFrame({
            'Producto': ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)'],
            'Stock Actual': [50, 100, 200],
            'Unidad': ['kg', 'litros', 'unidades'],
            'Punto de Reorden (PR)': [0, 0, 0],
            'Cantidad a Ordenar': [0, 0, 0],
            'Costo Unitario': [50, 30, 25]
        })
    else:
        productos = df_ventas['producto'].unique()
        inventario = []
        for prod in productos:
            ventas_total = df_ventas[df_ventas['producto'] == prod]['cantidad_vendida'].sum()
            stock_inicial = max(ventas_total * 2, 50)  # Mínimo 50
            stock_actual = max(stock_inicial - ventas_total, 0)
            inventario.append({
                'Producto': prod,
                'Stock Actual': stock_actual,
                'Unidad': 'unidades',
                'Punto de Reorden (PR)': 0,
                'Cantidad a Ordenar': 0,
                'Costo Unitario': 50  # Valor por defecto
            })
        return pd.DataFrame(inventario)

# ============================================
# 2. SINCRONIZAR PUNTOS ÓPTIMOS
# ============================================
def sincronizar_puntos_optimos(df_inventario: pd.DataFrame, df_resultados: pd.DataFrame) -> pd.DataFrame:
    """Actualiza PR y Cantidad a Ordenar desde resultados."""
    if df_resultados is None or df_resultados.empty:
        return df_inventario

    pr_map = df_resultados.set_index('producto')['punto_reorden'].to_dict()
    orden_map = df_resultados.set_index('producto')['cantidad_a_ordenar'].to_dict()

    # Asegurar columnas
    for col in ['Punto de Reorden (PR)', 'Cantidad a Ordenar']:
        if col not in df_inventario.columns:
            df_inventario[col] = 0
        df_inventario[col] = pd.to_numeric(df_inventario[col], errors='coerce').fillna(0)

    df_inventario['PR Mapeado'] = df_inventario['Producto'].map(pr_map).fillna(0)
    df_inventario['Punto de Reorden (PR)'] = np.where(
        df_inventario['PR Mapeado'] > 0,
        df_inventario['PR Mapeado'].round(2),
        df_inventario['Punto de Reorden (PR)']
    )
    df_inventario = df_inventario.drop(columns=['PR Mapeado'], errors='ignore')

    df_inventario['Orden Mapeado'] = df_inventario['Producto'].map(orden_map).fillna(0)
    df_inventario['Cantidad a Ordenar'] = np.where(
        df_inventario['Orden Mapeado'] > 0,
        df_inventario['Orden Mapeado'].round(2),
        df_inventario['Cantidad a Ordenar']
    )
    df_inventario = df_inventario.drop(columns=['Orden Mapeado'], errors='ignore')

    # Evitar valores muy bajos
    df_inventario['Punto de Reorden (PR)'] = np.where(
        df_inventario['Punto de Reorden (PR)'] < 0.01, 0.0, df_inventario['Punto de Reorden (PR)']
    )
    df_inventario['Cantidad a Ordenar'] = np.where(
        df_inventario['Cantidad a Ordenar'] < 0.01, 0.0, df_inventario['Cantidad a Ordenar']
    )
    return df_inventario

# ============================================
# 3. CONTROL DE INVENTARIO BÁSICO
# ============================================
def inventario_basico_app():
    """Interfaz completa de control de inventario."""
    st.header("Control de Inventario Básico")

    df_inventario = st.session_state.get('inventario_df')
    if df_inventario is None or df_inventario.empty:
        st.warning("El inventario base está vacío. Sube datos en la pestaña de Optimización.")
        return

    # Sincronizar si hay resultados
    if 'df_resultados' in st.session_state and st.session_state['df_resultados'] is not None:
        df_resultados = st.session_state['df_resultados']
        if not df_resultados.empty and 'error' in df_resultados.columns:
            df_resultados = df_resultados[df_resultados['error'].isnull()]
        if not df_resultados.empty:
            df_inventario = sincronizar_puntos_optimos(df_inventario, df_resultados)
            st.session_state['inventario_df'] = df_inventario
            st.success("Puntos de reorden y cantidades sincronizados desde Optimización")
        else:
            st.info("Calcula en Optimización para sincronizar PR y cantidades.")
    else:
        st.info("Calcula en Optimización para sincronizar PR y cantidades.")

    st.subheader("1️⃣ Inventario Actual (Edición en Vivo)")
    edited_df = st.data_editor(
        df_inventario,
        use_container_width=True,
        key="data_editor_inventario",
        column_config={
            "Stock Actual": st.column_config.NumberColumn(format="%.2f"),
            "Punto de Reorden (PR)": st.column_config.NumberColumn(format="%.2f"),
            "Cantidad a Ordenar": st.column_config.NumberColumn(format="%.2f"),
            "Costo Unitario": st.column_config.NumberColumn(format="$%.2f")
        }
    )

    if not edited_df.empty:
        df_final = edited_df.copy()
        for col in ['Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar', 'Costo Unitario']:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

        df_final['Faltante?'] = df_final['Stock Actual'] < df_final['Punto de Reorden (PR)']
        df_final['Valor Total'] = df_final['Stock Actual'] * df_final['Costo Unitario']
        st.session_state['inventario_df'] = df_final

    df_actual = st.session_state['inventario_df']
    st.subheader("2️⃣ Alertas y Totales")
    items_faltantes = df_actual[df_actual['Faltante?']]
    total_valor = df_actual['Valor Total'].sum()

    col_a, col_b = st.columns(2)
    with col_a: st.metric("Ítems con Bajo Stock", f"{len(items_faltantes)}")
    with col_b: st.metric("Valor Total del Inventario", f"${total_valor:,.2f}")

    if not items_faltantes.empty:
        st.warning("**¡URGENTE!** Ítems por debajo de PR.")
        st.dataframe(
            items_faltantes[['Producto', 'Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar']],
            use_container_width=True, hide_index=True
        )
    else:
        st.success("Todo el inventario está en niveles óptimos.")

    st.markdown("---")

# ============================================
# 4. GRÁFICO TRAZABILIDAD TOTAL
# ============================================
def crear_grafico_trazabilidad_total(
    df_trazabilidad: pd.DataFrame,
    resultado: Dict,
    lead_time: int
):
    """Gráfico de trazabilidad con doble eje."""
    nombre = resultado['producto']
    punto_reorden = resultado['punto_reorden']
    cantidad_a_ordenar = resultado['cantidad_a_ordenar']
    pronostico_diario_promedio = resultado['pronostico_diario_promedio']

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    df_hist = df_trazabilidad[df_trazabilidad['Tipo'] == 'Histórico']
    df_proj = df_trazabilidad[df_trazabilidad['Tipo'] == 'Proyectado']

    # Eje 1: Stock
    ax1.plot(df_hist['Fecha'], df_hist['Stock'], color='#1f77b4', linewidth=3, label='Stock Real Histórico')
    ax1.plot(df_proj['Fecha'], df_proj['Stock'], color='#ff7f0e', linewidth=2, linestyle='--', label='Stock Proyectado')
    ax1.axhline(y=punto_reorden, color='red', linestyle='-', linewidth=1.5, alpha=0.8, label=f'PR ({punto_reorden:.0f})')
    stock_maximo = punto_reorden + cantidad_a_ordenar
    ax1.axhline(y=stock_maximo, color='green', linestyle=':', linewidth=1.5, alpha=0.6, label=f'Stock Máximo ({stock_maximo:.0f})')
    ax1.set_ylabel('Stock (Unidades)', color='#1f77b4', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f77b4')

    # Eje 2: Demanda
    ax2.bar(df_hist['Fecha'], df_hist['Ventas'], color='purple', alpha=0.3, width=1, label='Venta Diaria')
    pronostico_fechas = df_proj['Fecha']
    pronostico_valores = [pronostico_diario_promedio] * len(df_proj)
    if not pronostico_fechas.empty:
        ax2.plot(pronostico_fechas, pronostico_valores, color='purple', linewidth=2, label=f'Pronóstico ({pronostico_diario_promedio:.1f})')

    ordenes_simuladas = df_proj[df_proj['Simulacion_Entradas'] > 0]
    if not ordenes_simuladas.empty:
        ax2.scatter(ordenes_simuladas['Fecha'], ordenes_simuladas['Simulacion_Entradas'],
                    color='green', marker='^', s=100, zorder=5, label=f'Entrega ({cantidad_a_ordenar:.0f})')

    ax2.set_ylabel('Demanda y Órdenes', color='purple', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.set_ylim(bottom=0)

    # Configuración
    fecha_actual = datetime.now().date()
    ax1.axvline(x=fecha_actual, color='gray', linestyle='-.', alpha=0.5, label='Hoy')

    ax1.set_xlabel('Fecha')
    ax1.set_title(f'{nombre}: Stock, Ventas y Simulación de Órdenes', fontweight='bold')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df_trazabilidad) // 10)))
    plt.xticks(rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, linestyle='--')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9, framealpha=0.9)
    plt.tight_layout()

    return fig

# ============================================
# 5. GRÁFICO COMPARATIVO
# ============================================
def crear_grafico_comparativo(resultados: List[Dict]):
    """Gráfico de volumen total de ventas."""
    df = pd.DataFrame([r for r in resultados if r.get('error') is None])
    if df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title('No hay datos para comparar.')
        return fig

    df_sorted = df.sort_values('volumen_total_vendido', ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df_sorted['producto'], df_sorted['volumen_total_vendido'], color='skyblue')
    ax.set_title('Volumen Total de Ventas por Producto', fontweight='bold')
    ax.set_ylabel('Unidades Vendidas')
    ax.tick_params(axis='x', rotation=45)

    # Etiquetas en barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    return fig
