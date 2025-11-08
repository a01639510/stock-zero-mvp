# modules/components.py
# modules/components.py
import pandas as pd
import streamlit as st

def generar_inventario_base(df_ventas=None, use_example_data=False):
    """
    Genera inventario base a partir de ventas o ejemplo
    """
    if use_example_data or df_ventas is None:
        return pd.DataFrame({
            'Producto': ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)'],
            'Stock Actual': [50, 100, 200],
            'Unidad': ['kg', 'litros', 'unidades']
        })
    else:
        # USAR DATOS REALES
        productos = df_ventas['producto'].unique()
        inventario = []
        for prod in productos:
            ventas_total = df_ventas[df_ventas['producto'] == prod]['cantidad_vendida'].sum()
            # Stock inicial estimado: 2x ventas promedio diarias
            stock_inicial = ventas_total * 2
            stock_actual = max(stock_inicial - ventas_total, 0)
            inventario.append({
                'Producto': prod,
                'Stock Actual': stock_actual,
                'Unidad': 'unidades'
            })
        return pd.DataFrame(inventario)
def sincronizar_puntos_optimos(df_inventario: pd.DataFrame, df_resultados: pd.DataFrame) -> pd.DataFrame:
    """Actualiza las columnas 'Punto de Reorden (PR)' y 'Cantidad a Ordenar'."""
    if df_resultados is None or df_resultados.empty:
        return df_inventario  # No sincronizar si no hay resultados
    
    pr_map = df_resultados.set_index('producto')['punto_reorden'].to_dict()
    orden_map = df_resultados.set_index('producto')['cantidad_a_ordenar'].to_dict()
    
    for col in ['Punto de Reorden (PR)', 'Cantidad a Ordenar']:
        df_inventario[col] = pd.to_numeric(df_inventario[col], errors='coerce').fillna(0)
    
    df_inventario['PR Mapeado'] = df_inventario['Producto'].map(pr_map).fillna(0)
    df_inventario['Punto de Reorden (PR)'] = np.where(
        df_inventario['PR Mapeado'] > 0, df_inventario['PR Mapeado'].round(2), df_inventario['Punto de Reorden (PR)']
    )
    df_inventario = df_inventario.drop(columns=['PR Mapeado'], errors='ignore')
    
    df_inventario['Orden Mapeado'] = df_inventario['Producto'].map(orden_map).fillna(0)
    df_inventario['Cantidad a Ordenar'] = np.where(
        df_inventario['Orden Mapeado'] > 0, df_inventario['Orden Mapeado'].round(2), df_inventario['Cantidad a Ordenar']
    )
    df_inventario = df_inventario.drop(columns=['Orden Mapeado'], errors='ignore')
    
    df_inventario['Punto de Reorden (PR)'] = np.where(
        df_inventario['Punto de Reorden (PR)'] < 0.01, 0.0, df_inventario['Punto de Reorden (PR)']
    )
    df_inventario['Cantidad a Ordenar'] = np.where(
        df_inventario['Cantidad a Ordenar'] < 0.01, 0.0, df_inventario['Cantidad a Ordenar']
    )

    return df_inventario

# ============================================
# FUNCIONES DE INTERFAZ Y GRÁFICOS
# ============================================

def inventario_basico_app():
    """Componente completo para la interfaz del control de inventario básico."""
    st.header("🛒 Control de Inventario Básico")
    
    df_inventario = st.session_state.get('inventario_df')

    if df_inventario is None or df_inventario.empty:
        st.warning("El inventario base está vacío. Sube datos en la pestaña de Optimización.")
        return 

    # Sincronización de datos (SIEMPRE VERIFICAR)
    if 'df_resultados' in st.session_state and st.session_state['df_resultados'] is not None and not st.session_state['df_resultados'].empty:
        df_inventario = sincronizar_puntos_optimos(df_inventario, st.session_state['df_resultados'])
        st.session_state['inventario_df'] = df_inventario
    else:
        st.info("💡 Calcula los resultados en Optimización para sincronizar PR y cantidades.")

    st.subheader("1️⃣ Inventario Actual (Edición en Vivo)")
    
    edited_df = st.data_editor(
        df_inventario, use_container_width=True, key="data_editor_inventario"
    )
    
    if not edited_df.empty:
        try:
            df_final = edited_df.copy()
            for col in ['Stock Actual', 'Punto de Reorden (PR)', 'Cantidad a Ordenar', 'Costo Unitario']:
                df_final.loc[:, col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
            
            df_final.loc[:, 'Faltante?'] = df_final['Stock Actual'] < df_final['Punto de Reorden (PR)']
            df_final.loc[:, 'Valor Total'] = df_final['Stock Actual'] * df_final['Costo Unitario']
            
            st.session_state['inventario_df'] = df_final
            
        except Exception:
            pass
    
    df_actual = st.session_state['inventario_df']

    st.subheader("2️⃣ Alertas y Totales")

    items_faltantes = df_actual[df_actual['Faltante?']]
    total_valor = df_actual['Valor Total'].sum()
    
    col_a, col_b = st.columns(2)
    with col_a: st.metric("🚨 Ítems con Bajo Stock", f"{len(items_faltantes)}")
    with col_b: st.metric("💰 Valor Total del Inventario", f"${total_valor:,.2f}")

    if not items_faltantes.empty:
        st.warning("⚠️ **¡URGENTE!** Ítems por debajo de PR.")
        st.dataframe(
            items_faltantes[['Producto', 'Stock Actual', 'Punto de Reorden (PR)']],
            use_container_width=True, hide_index=True
        )
    else: st.success("🎉 Todo el inventario está en niveles óptimos.")

    st.markdown("---")


def crear_grafico_trazabilidad_total(
    df_trazabilidad: pd.DataFrame, 
    resultado: Dict, 
    lead_time: int
):
    """Crea el gráfico de trazabilidad de Inventario con doble eje para Stock y Demanda."""
    nombre = resultado['producto']
    punto_reorden = resultado['punto_reorden']
    cantidad_a_ordenar = resultado['cantidad_a_ordenar']
    pronostico_diario_promedio = resultado['pronostico_diario_promedio']
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    df_hist = df_trazabilidad[df_trazabilidad['Tipo'] == 'Histórico']
    df_proj = df_trazabilidad[df_trazabilidad['Tipo'] == 'Proyectado']
    
    # Eje 1 (Izquierda): STOCK
    ax1.plot(df_hist['Fecha'], df_hist['Stock'], color='#1f77b4', linewidth=3, label='Stock Real Histórico')
    ax1.plot(df_proj['Fecha'], df_proj['Stock'], color='#ff7f0e', linewidth=2, linestyle='--', label='Stock Proyectado (Simulación PR)')

    ax1.axhline(y=punto_reorden, color='red', linestyle='-', linewidth=1.5, alpha=0.8,
               label=f'Punto de Reorden ({punto_reorden:.0f})')
               
    stock_maximo = punto_reorden + cantidad_a_ordenar
    ax1.axhline(y=stock_maximo, color='green', linestyle=':', linewidth=1.5, alpha=0.6,
               label=f'Stock Máximo Teórico ({stock_maximo:.0f})')
    
    ax1.set_ylabel('Stock (Unidades)', color='#1f77b4', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f77b4')

    # Eje 2 (Derecha): DEMANDA (Ventas + Pronóstico + Órdenes)
    ax2.bar(df_hist['Fecha'], df_hist['Ventas'], color='purple', alpha=0.3, width=1, label='Venta Diaria Histórica')
            
    pronostico_fechas = df_proj['Fecha']
    pronostico_valores = [pronostico_diario_promedio] * len(df_proj)
    
    if not pronostico_fechas.empty:
        ax2.plot(pronostico_fechas, pronostico_valores, color='purple', linewidth=2, linestyle='-',
                label=f'Pronóstico Diario ({pronostico_diario_promedio:.1f})')
                
    # Mostrar las órdenes de compra simuladas
    ordenes_simuladas = df_proj[df_proj['Simulacion_Entradas'] > 0].copy()
    
    if not ordenes_simuladas.empty:
        ax2.scatter(ordenes_simuladas['Fecha'], ordenes_simuladas['Simulacion_Entradas'], 
                    color='green', marker='^', s=100, zorder=5, 
                    label=f'Entrega de Orden Simulada ({cantidad_a_ordenar:.0f})')


    ax2.set_ylabel('Demanda Diaria y Órdenes', color='purple', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.set_ylim(bottom=0)
    
    # Configuración General
    fecha_actual = datetime.now().date()
    ax1.axvline(x=fecha_actual, color='gray', linestyle='-.', alpha=0.5, label='Fecha Actual')
    
    ax1.set_xlabel('Fecha', fontsize=12)
    ax1.set_title(f'📉 {nombre}: Stock, Ventas y Simulación de Órdenes (PR)', 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df_trazabilidad) // 10))) 
    plt.xticks(rotation=45, ha='right')
    
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9, framealpha=0.9)
    
    plt.tight_layout()
    
    return fig

def crear_grafico_comparativo(resultados: List[Dict]):
    """Crea el gráfico de volumen total de ventas para la visión general."""
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
