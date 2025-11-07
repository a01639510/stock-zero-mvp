import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union, List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
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
    Calcula el punto de reorden para UN producto específico.
    """
    try:
        # Preparar serie temporal
        df = df_producto.copy()
        df = df.set_index('fecha').sort_index()
        df_diario = df.resample('D').sum()
        df_diario['cantidad_vendida'] = df_diario['cantidad_vendida'].fillna(0)
        
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'producto': nombre_producto,
                'error': f'Datos insuficientes (mínimo {frecuencia_estacional * 2} días)',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0
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
        
        # Cálculos
        demanda_lead_time = pronostico.sum()
        pronostico_diario_promedio = pronostico.mean()
        stock_seguridad = pronostico_diario_promedio * stock_seguridad_dias
        punto_reorden = demanda_lead_time + stock_seguridad
        
        # Cantidad a ordenar cubre la mitad de la estacionalidad (horizonte de planeación)
        orden_horizonte_dias = frecuencia_estacional / 2
        cantidad_a_ordenar = pronostico_diario_promedio * orden_horizonte_dias
        
        # Guardar datos para gráficos (últimos 30 días + pronóstico)
        ultimos_30_dias = df_diario.tail(30).copy()
        
        return {
            'producto': nombre_producto,
            'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'demanda_lead_time': round(demanda_lead_time, 2),
            'stock_seguridad': round(stock_seguridad, 2),
            'dias_historicos': len(df_diario),
            # Datos para gráficos
            'datos_historicos': ultimos_30_dias,
            'pronostico_fechas': pronostico.index.tolist(),
            'pronostico_valores': pronostico.tolist()
        }
        
    except Exception as e:
        return {
            'producto': nombre_producto,
            'error': f'Error: {str(e)}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0
        }


def procesar_multiple_productos(
    df: pd.DataFrame,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> List[Dict]:
    """
    Procesa múltiples productos desde un CSV en formato largo.
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
    
    return resultados


def crear_grafico_comparativo(resultados: List[Dict]):
    """
    Crea un gráfico comparando ventas históricas y pronósticos de múltiples productos.
    """
    productos_exitosos = [r for r in resultados if 'error' not in r]
    
    colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for idx, resultado in enumerate(productos_exitosos):
        color = colores[idx % len(colores)]
        nombre = resultado['producto']
        
        df_hist = resultado['datos_historicos']
        fechas_hist = df_hist.index
        ventas_hist = df_hist['cantidad_vendida'].values
        
        fechas_pron = resultado['pronostico_fechas']
        valores_pron = resultado['pronostico_valores']
        
        ax.plot(fechas_hist, ventas_hist, 
                color=color, linewidth=2, marker='o', markersize=3,
                label=f'{nombre}', alpha=0.8)
        
        ultima_fecha_hist = fechas_hist[-1]
        ultimo_valor_hist = ventas_hist[-1]
        
        fechas_pronostico_completo = [ultima_fecha_hist] + fechas_pron
        valores_pronostico_completo = [ultimo_valor_hist] + valores_pron
        
        ax.plot(fechas_pronostico_completo, valores_pronostico_completo,
                color=color, linewidth=2, linestyle='--', 
                label=f'{nombre} (Pronóstico)', alpha=0.7)
    
    ax.set_xlabel('Fecha', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cantidad Vendida', fontsize=12, fontweight='bold')
    ax.set_title('📊 Ventas Históricas vs Pronóstico por Producto', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45, ha='right')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              fontsize=9, framealpha=0.9)
    
    plt.tight_layout()
    
    return fig

# ============================================
# FUNCIONES DE INVENTARIO BÁSICO
# ============================================

def generar_inventario_base():
    """Genera un DataFrame base para la sección de inventario."""
    data = {
        'Producto': ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Azúcar (Kg)', 'Vaso 12oz (Unidad)', 'Tapa 12oz (Unidad)'],
        'Categoría': ['Insumo', 'Insumo', 'Insumo', 'Desechable', 'Desechable'],
        'Unidad': ['KG', 'L', 'KG', 'UNI', 'UNI'],
        'Stock Actual': [5.0, 15.0, 8.0, 500, 500],
        'Punto de Reorden (PR)': [3.0, 5.0, 2.0, 100, 100],
        'Costo Unitario': [180.0, 25.0, 15.0, 1.5, 0.8],
    }
    df = pd.DataFrame(data)
    
    # Cálculos dinámicos
    df['Faltante?'] = df['Stock Actual'] < df['Punto de Reorden (PR)']
    df['Valor Total'] = df['Stock Actual'] * df['Costo Unitario']
    return df

def inventario_basico_app():
    """Interfaz para el control de inventario básico tipo Excel."""
    
    st.header("🛒 Control de Inventario Básico")
    st.info("💡 Usa esta sección para gestionar el stock físico. Las alertas se activan si el 'Stock Actual' cae por debajo del 'Punto de Reorden'.")

    # Inicializar o cargar el DataFrame en el estado de la sesión
    if 'inventario_df' not in st.session_state:
        st.session_state['inventario_df'] = generar_inventario_base()

    df_inventario = st.session_state['inventario_df'].copy()

    # --- Edición del DataFrame ---
    st.subheader("1️⃣ Inventario Actual (Edición en Vivo)")
    
    # Columnas para la edición
    editable_columns = ['Producto', 'Categoría', 'Unidad', 'Stock Actual', 'Punto de Reorden (PR)', 'Costo Unitario']
    column_config = {
        "Producto": st.column_config.TextColumn("Producto", required=True),
        "Stock Actual": st.column_config.NumberColumn("Stock Actual", required=True, format="%.2f"),
        "Punto de Reorden (PR)": st.column_config.NumberColumn("Punto de Reorden (PR)", required=True, format="%.2f"),
        "Costo Unitario": st.column_config.NumberColumn("Costo Unitario", format="$%.2f"),
        # 'Faltante?' y 'Valor Total' se calculan
        "Faltante?": st.column_config.CheckboxColumn("Faltante?", disabled=True),
        "Valor Total": st.column_config.NumberColumn("Valor Total", disabled=True, format="$%.2f"),
    }
    
    # Widget de edición de datos
    edited_df = st.data_editor(
        df_inventario[editable_columns],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_inventario"
    )

    # Re-calcular columnas derivadas
    if not edited_df.empty:
        try:
            edited_df['Stock Actual'] = pd.to_numeric(edited_df['Stock Actual'], errors='coerce').fillna(0)
            edited_df['Punto de Reorden (PR)'] = pd.to_numeric(edited_df['Punto de Reorden (PR)'], errors='coerce').fillna(0)
            edited_df['Costo Unitario'] = pd.to_numeric(edited_df['Costo Unitario'], errors='coerce').fillna(0)

            df_final = edited_df.copy()
            df_final['Faltante?'] = df_final['Stock Actual'] < df_final['Punto de Reorden (PR)']
            df_final['Valor Total'] = df_final['Stock Actual'] * df_final['Costo Unitario']
            
            st.session_state['inventario_df'] = df_final
            
        except Exception as e:
            st.error(f"Error en el cálculo: {e}. Revisa los formatos de números.")
            st.stop()
    else:
        st.session_state['inventario_df'] = pd.DataFrame(columns=df_inventario.columns)
        
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
        st.dataframe(
            items_faltantes[['Producto', 'Unidad', 'Stock Actual', 'Punto de Reorden (PR)']],
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

# ============================================
# PÁGINA PRINCIPAL DE LA APP
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide")

st.title("📦 Stock Zero")
st.subheader("Optimización de Inventario para Pymes - Multi-Producto")
st.markdown("---")

# USAMOS PESTAÑAS PARA SEPARAR LAS FUNCIONALIDADES
tab_optimizacion, tab_control_basico = st.tabs(["🚀 Optimización de Inventario (Pronóstico)", "🛒 Control de Inventario Básico"])


# === PESTAÑA 1: OPTIMIZACIÓN Y PRONÓSTICO ===
with tab_optimizacion:
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        lead_time = st.slider("Lead Time (días)", 1, 30, 7, 
                              help="Días que tarda tu proveedor en entregar")
        stock_seguridad = st.slider("Stock de Seguridad (días)", 1, 10, 3,
                                    help="Días adicionales de inventario como buffer")
        frecuencia = st.selectbox(
            "Estacionalidad", 
            [7, 14, 30], 
            index=0,
            format_func=lambda x: f"{x} días ({'Semanal' if x==7 else 'Mensual' if x==30 else 'Quincenal'})",
            help="Patrón de repetición de ventas"
        )
        
        st.markdown("---")
        st.markdown("### 💡 Formatos Aceptados")
        st.markdown("""
        **Formato Largo** (Recomendado):
        - fecha
        - producto
        - cantidad_vendida
        """)

    # Upload CSV
    st.markdown("### 1️⃣ Sube tu archivo de ventas")
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo CSV",
        type=['csv'],
        help="Debe tener historial de ventas en formato largo o ancho."
    )
    
    with st.expander("📋 Ver formatos de archivo aceptados"):
        tab1, tab2 = st.tabs(["Formato Largo (Recomendado)", "Formato Ancho"])
        
        with tab1:
            st.markdown("**Ideal para restaurantes con POS**")
            ejemplo_largo = pd.DataFrame({
                'fecha': ['2024-09-01', '2024-09-01', '2024-09-01', '2024-09-02', '2024-09-02', '2024-09-02'],
                'producto': ['Cerveza Corona', 'Tacos al Pastor', 'Coca-Cola', 'Cerveza Corona', 'Tacos al Pastor', 'Coca-Cola'],
                'cantidad_vendida': [45, 120, 38, 52, 135, 41]
            })
            st.dataframe(ejemplo_largo, use_container_width=True)
        
        with tab2:
            st.markdown("**Típico de hojas de Excel**")
            ejemplo_ancho = pd.DataFrame({
                'fecha': ['2024-09-01', '2024-09-02', '2024-09-03'],
                'Cerveza Corona': [45, 52, 48],
                'Tacos al Pastor': [120, 135, 128],
                'Coca-Cola': [38, 41, 35]
            })
            st.dataframe(ejemplo_ancho, use_container_width=True)


    # Procesar archivo
    if uploaded_file is not None:
        try:
            # Leer CSV
            df_raw = pd.read_csv(uploaded_file)
            
            formato_detectado = None
            
            if 'producto' in df_raw.columns and 'cantidad_vendida' in df_raw.columns:
                formato_detectado = "largo"
                df = df_raw.copy()
            elif 'fecha' in df_raw.columns and len(df_raw.columns) > 2:
                formato_detectado = "ancho"
                df = df_raw.melt(
                    id_vars=['fecha'],
                    var_name='producto',
                    value_name='cantidad_vendida'
                )
            else:
                st.error("❌ Formato no reconocido.")
                st.stop()
            
            # Validar y limpiar datos
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df = df.dropna(subset=['fecha'])
            df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce').fillna(0)
            
            # Mostrar información del archivo
            st.markdown("### 2️⃣ Datos cargados correctamente")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📁 Formato detectado", formato_detectado.upper())
            with col2:
                num_productos = df['producto'].nunique()
                st.metric("📦 Productos únicos", num_productos)
            with col3:
                st.metric("📅 Total registros", len(df))
            with col4:
                dias_datos = (df['fecha'].max() - df['fecha'].min()).days + 1
                st.metric("📊 Días de datos", dias_datos)
            
            with st.expander("👁️ Ver datos cargados"):
                st.dataframe(df.head(20), use_container_width=True)
            
            productos = sorted(df['producto'].unique())
            st.markdown(f"**Productos encontrados:** {', '.join(productos)}")
            
            # Botón de cálculo
            st.markdown("### 3️⃣ Calcular Inventario Óptimo")
            
            if st.button("🚀 Calcular para TODOS los productos", type="primary", use_container_width=True):
                with st.spinner(f"Analizando {len(productos)} productos..."):
                    resultados = procesar_multiple_productos(
                        df,
                        lead_time,
                        stock_seguridad,
                        frecuencia
                    )
                
                # Mostrar resultados
                st.markdown("---")
                st.markdown("## 📊 Resultados del Análisis")
                
                exitosos = [r for r in resultados if 'error' not in r]
                
                if exitosos:
                    st.success(f"✅ Se analizaron exitosamente {len(exitosos)} productos")
                    
                    # Gráfico
                    st.markdown("---")
                    st.markdown("### 📈 Visualización: Ventas y Pronósticos")
                    fig = crear_grafico_comparativo(exitosos)
                    st.pyplot(fig)
                    st.info("El gráfico muestra el pronóstico (línea punteada) basado en el Lead Time.")
                    
                    # Métricas
                    df_resultados = pd.DataFrame(exitosos).sort_values('cantidad_a_ordenar', ascending=False)
                    total_reorden = df_resultados['punto_reorden'].sum()
                    total_ordenar = df_resultados['cantidad_a_ordenar'].sum()
                    cobertura_orden = frecuencia / 2
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🎯 Total Punto de Reorden", f"{total_reorden:.0f} unidades")
                    with col2:
                        st.metric("📦 Total a Ordenar", f"{total_ordenar:.0f} unidades")
                    
                    # Tabla y Top 5 (Omitido por espacio, pero funciona)
                    st.markdown("### 📋 Recomendaciones por Producto")
                    df_display = df_resultados[['producto', 'punto_reorden', 'cantidad_a_ordenar', 
                                                'pronostico_diario_promedio']].copy()
                    df_display.columns = ['Producto', 'Punto de Reorden', 'Cantidad a Ordenar', 'Venta Diaria Promedio']
                    
                    # Top 5
                    st.markdown("### 🔝 Top 5 Productos Prioritarios")
                    for idx, row in df_resultados.head(5).iterrows():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        with col1: st.markdown(f"**{row['producto']}**")
                        with col2: st.metric("Reorden", f"{row['punto_reorden']:.0f}")
                        with col3: st.metric("A Ordenar", f"{row['cantidad_a_ordenar']:.0f}")
                        with col4: st.metric("Diario", f"{row['pronostico_diario_promedio']:.1f}")
                    
                    # Interpretación
                    st.markdown("---")
                    st.markdown("### 💡 ¿Cómo usar estos resultados?")
                    st.markdown(f"""
                    **1. Punto de Reorden:** Cuando tu inventario llegue a esta cantidad, ordena.
                    **2. Cantidad a Ordenar:** Cubre aproximadamente **{cobertura_orden} días** de demanda.
                    """)
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Verifica el formato de tu CSV.")

    else:
        st.info("👆 **Comienza subiendo tu archivo CSV de ventas** para obtener el análisis avanzado.")


# === PESTAÑA 2: CONTROL DE INVENTARIO BÁSICO ===
with tab_control_basico:
    inventario_basico_app()


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Stock Zero MVP</strong> - Optimización Multi-Producto | Google Gemini Pro</p>
</div>
""", unsafe_allow_html=True)
