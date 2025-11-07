import streamlit as st
import pandas as pd
from datetime import datetime
import warnings

# --- IMPORTACIONES DE MÓDULOS ---
# Asegúrate de que estos archivos estén en la carpeta 'modules'
from modules.core_analysis import procesar_multiple_productos
from modules.trazability import calcular_trazabilidad_inventario
from modules.components import (
    inventario_basico_app, 
    crear_grafico_comparativo, 
    crear_grafico_trazabilidad_total, 
    generar_inventario_base
)

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN E INICIO DE LA APLICACIÓN
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide")

st.title("📦 Stock Zero")
st.subheader("Optimización de Inventario para Pymes - Multi-Producto")
st.markdown("---")

# Inicializar DataFrames de sesión si no existen
if 'df_ventas_trazabilidad' not in st.session_state:
    st.session_state['df_ventas_trazabilidad'] = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_vendida'])
if 'df_stock_trazabilidad' not in st.session_state:
    st.session_state['df_stock_trazabilidad'] = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida']) 
if 'inventario_df' not in st.session_state:
    st.session_state['inventario_df'] = generar_inventario_base(None, use_example_data=True)


# USAMOS PESTAÑAS PARA SEPARAR LAS FUNCIONALIDADES
tab_optimizacion, tab_control_basico = st.tabs(["🚀 Optimización de Inventario (Pronóstico)", "🛒 Control de Inventario Básico"])

# ============================================
# PESTAÑA 1: OPTIMIZACIÓN Y PRONÓSTICO
# ============================================
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
        **Ventas:** `fecha`, `producto`, `cantidad_vendida`
        **Stock:** `fecha`, `producto`, `cantidad_recibida`
        """)

    # --- Carga de Archivos ---
    st.markdown("### 1️⃣ Sube tus archivos (Ventas y Stock)")
    
    col_ventas, col_stock = st.columns(2)
    
    uploaded_file_ventas = col_ventas.file_uploader(
        "Archivo CSV de **Ventas Históricas** (Requerido)",
        type=['csv'],
        key="upload_ventas"
    )
    
    uploaded_file_stock = col_stock.file_uploader(
        "Archivo CSV de **Entradas de Stock** (Opcional para Trazabilidad)",
        type=['csv'],
        key="upload_stock"
    )

    # Procesar archivo de VENTAS
    df_ventas = None
    if uploaded_file_ventas is not None:
        try:
            df_raw_ventas = pd.read_csv(uploaded_file_ventas)
            
            # Detección de formato y pre-procesamiento de VENTAS
            if 'producto' not in df_raw_ventas.columns and len(df_raw_ventas.columns) > 2:
                df_ventas = df_raw_ventas.melt(id_vars=['fecha'], var_name='producto', value_name='cantidad_vendida')
                formato_detectado = "ancho"
            elif 'producto' in df_raw_ventas.columns and 'cantidad_vendida' in df_raw_ventas.columns:
                df_ventas = df_raw_ventas.copy()
                formato_detectado = "largo"
            else:
                st.error("❌ Formato de VENTAS no reconocido. Columnas requeridas: `fecha` y (`producto`, `cantidad_vendida`) o `fecha` y columnas de producto.")
                st.stop()
            
            # Limpieza robusta de datos de ventas
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce').normalize()
            df_ventas = df_ventas.dropna(subset=['fecha'])
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)
            
            # Procesar archivo de STOCK
            df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida']) 
            if uploaded_file_stock is not None:
                try:
                    df_raw_stock = pd.read_csv(uploaded_file_stock)
                    if 'fecha' in df_raw_stock.columns and 'producto' in df_raw_stock.columns and 'cantidad_recibida' in df_raw_stock.columns:
                        df_stock = df_raw_stock.copy()
                        df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce').normalize()
                        df_stock = df_stock.dropna(subset=['fecha'])
                        df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
                        st.success("✅ Historial de Entradas de Stock cargado.")
                    else:
                        st.warning("⚠️ El archivo de STOCK no contiene las columnas esperadas: `fecha`, `producto`, `cantidad_recibida`.")
                        df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])

                except Exception as e:
                    st.error(f"Error al procesar el archivo de STOCK: {str(e)}")
                    df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])

            # --- Guardar DataFrames en session_state ---
            st.session_state['df_ventas_trazabilidad'] = df_ventas
            st.session_state['df_stock_trazabilidad'] = df_stock
            
            # Reinicio de Inventario si se detectan datos nuevos
            example_products = set(['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)'])
            if 'inventario_df' in st.session_state:
                current_products = set(st.session_state['inventario_df']['Producto'].tolist())
                if example_products.issubset(current_products):
                    st.session_state['inventario_df'] = generar_inventario_base(df_ventas, use_example_data=False)
            else:
                 st.session_state['inventario_df'] = generar_inventario_base(df_ventas)
                
            st.markdown("### 2️⃣ Datos cargados correctamente")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📁 Formato Ventas", formato_detectado.upper())
            with col2: st.metric("📦 Productos únicos", df_ventas['producto'].nunique())
            with col3: st.metric("📅 Total registros Ventas", len(df_ventas))
            with col4: st.metric("📊 Días de datos Ventas", (df_ventas['fecha'].max() - df_ventas['fecha'].min()).days + 1)
            
            productos = sorted(df_ventas['producto'].unique())
            st.markdown(f"**Productos encontrados:** {', '.join(productos)}")
            
            st.markdown("### 3️⃣ Calcular Inventario Óptimo")
            
            # El botón llama a la función modular de cálculo
            if st.button("🚀 Calcular para TODOS los productos", type="primary", use_container_width=True):
                with st.spinner(f"Analizando {len(productos)} productos..."):
                    df_resultados = procesar_multiple_productos(
                        df_ventas,
                        lead_time,
                        stock_seguridad,
                        frecuencia
                    )
                
                st.session_state['df_resultados'] = df_resultados
                st.rerun()

            # --- SECCIÓN DE RESULTADOS ---
            if 'df_resultados' in st.session_state:
                df_resultados = st.session_state['df_resultados']
                df_exitosos = df_resultados[df_resultados['error'].isnull()].sort_values('cantidad_a_ordenar', ascending=False)
                
                st.markdown("---")
                st.markdown("## 📊 Resultados del Análisis")
                
                if not df_exitosos.empty:
                    st.success(f"✅ Se analizaron exitosamente {len(df_exitosos)} productos.")
                    
                    # Métricas resumidas
                    total_reorden = df_exitosos['punto_reorden'].sum()
                    total_ordenar = df_exitosos['cantidad_a_ordenar'].sum()
                    col1, col2 = st.columns(2)
                    with col1: st.metric("🎯 Total Punto de Reorden", f"{total_reorden:.0f} unidades")
                    with col2: st.metric("📦 Total a Ordenar", f"{total_ordenar:.0f} unidades")
                    
                    # TABLA ABC y Recomendaciones
                    st.markdown("### 📋 Recomendaciones y Clasificación ABC")
                    df_display = df_exitosos[['producto', 'clasificacion_abc', 'punto_reorden', 'cantidad_a_ordenar']].copy()
                    df_display.columns = ['Producto', 'ABC', 'Punto de Reorden', 'Cantidad a Ordenar']
                    df_display['Punto de Reorden'] = df_display['Punto de Reorden'].apply(lambda x: f"{x:.0f}")
                    df_display['Cantidad a Ordenar'] = df_display['Cantidad a Ordenar'].apply(lambda x: f"{x:.0f}")
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Gráfico de Trazabilidad
                    st.markdown("---")
                    st.markdown("### 📈 Trazabilidad de Inventario (Simulación de PR)")
                    
                    producto_seleccionado_inv = st.selectbox(
                        "Selecciona un producto para ver la simulación de stock y órdenes:",
                        options=df_exitosos['producto'].tolist(),
                        key="selector_inventario_proyectado" 
                    )
                    
                    if producto_seleccionado_inv:
                        resultado_prod = df_exitosos[df_exitosos['producto'] == producto_seleccionado_inv].iloc[0].to_dict()
                        
                        # Obtener Stock Actual
                        df_inv_basico = st.session_state.get('inventario_df', pd.DataFrame())
                        stock_actual = 0.0
                        mensaje_stock = "⚠️ **Stock Inicial/Actual no cargado.** Usando Stock = 0. ¡Actualiza el Stock Actual en la pestaña de Control de Inventario Básico!"
                        
                        if not df_inv_basico.empty and 'Producto' in df_inv_basico.columns:
                            stock_row = df_inv_basico[df_inv_basico['Producto'] == producto_seleccionado_inv]
                            if not stock_row.empty:
                                try:
                                    stock_actual = float(stock_row['Stock Actual'].iloc[0])
                                    mensaje_stock = f"Stock Inicial/Actual: **{stock_actual:.2f}** (tomado de Control de Inventario Básico)."
                                except:
                                    stock_actual = 0.0
                        
                        st.warning(mensaje_stock)

                        # LLAMADA AL MÓDULO TRAZABILITY
                        try:
                            df_trazabilidad = calcular_trazabilidad_inventario(
                                st.session_state['df_ventas_trazabilidad'],
                                st.session_state['df_stock_trazabilidad'],
                                producto_seleccionado_inv,
                                stock_actual,
                                resultado_prod['punto_reorden'],
                                resultado_prod['cantidad_a_ordenar'],
                                resultado_prod['pronostico_diario_promedio'],
                                lead_time
                            )

                            if df_trazabilidad is not None and not df_trazabilidad.empty:
                                # LLAMADA AL MÓDULO COMPONENTS (Gráfico)
                                fig_trazabilidad = crear_grafico_trazabilidad_total(
                                    df_trazabilidad,
                                    resultado_prod,
                                    lead_time
                                )
                                st.pyplot(fig_trazabilidad)
                            else:
                                st.error(f"❌ La función de trazabilidad no devolvió datos válidos para {producto_seleccionado_inv}.")
                        
                        except Exception as e:
                            st.error(f"❌ Error crítico al generar la trazabilidad. Detalle: {e}")

                    # Gráfico Comparativo
                    st.markdown("---")
                    st.markdown("### 📊 Tendencias de Ventas (Visión General)")
                    fig_comparativo = crear_grafico_comparativo(df_exitosos.to_dict('records'))
                    st.pyplot(fig_comparativo)
            
                else:
                    st.info("No se pudo calcular la optimización para ningún producto. Revisa la cantidad de datos históricos.")

            else:
                 st.info("👆 Haz clic en 'Calcular para TODOS los productos' para ver los resultados del análisis.")


        except Exception as e:
            st.error(f"Error al procesar el archivo de ventas o al calcular. Asegúrate de que las columnas `fecha` y `cantidad_vendida` sean correctas. Detalle: {e}")
            st.stop()
    elif 'df_ventas_trazabilidad' not in st.session_state or st.session_state['df_ventas_trazabilidad'].empty:
        st.info("Sube tus archivos de Ventas e Historial de Stock para comenzar el análisis.")

# ============================================
# PESTAÑA 2: CONTROL DE INVENTARIO BÁSICO
# ============================================
with tab_control_basico:
    # La función debe estar definida en modules/components.py
    inventario_basico_app()
