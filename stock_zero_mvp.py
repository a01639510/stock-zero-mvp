import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings

# --- IMPORTACIONES DE MÓDULOS ---
from modules.core_analysis import procesar_multiple_productos
from modules.trazability import calcular_trazabilidad_inventario
from modules.components import (
    inventario_basico_app, 
    crear_grafico_comparativo, 
    crear_grafico_trazabilidad_total, 
    generar_inventario_base
)

try:
    from modules.recipes import recetas_app
    RECIPES_AVAILABLE = True
except ImportError:
    RECIPES_AVAILABLE = False
    def recetas_app():
        st.error("⚠️ El módulo de recetas no está disponible. Crea el archivo `modules/recipes.py`")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN E INICIO DE LA APLICACIÓN
# ============================================

st.set_page_config(
    page_title="Stock Zero", 
    page_icon="📦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNCIONES AUXILIARES PARA EJEMPLOS
# ============================================

def generar_ejemplo_ventas():
    """Genera un DataFrame de ejemplo para ventas."""
    fechas = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    datos = []
    productos = ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)']
    
    for fecha in fechas:
        for producto in productos:
            cantidad = int(10 + (hash(str(fecha) + producto) % 20))
            datos.append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'producto': producto,
                'cantidad_vendida': cantidad
            })
    
    return pd.DataFrame(datos)

def generar_ejemplo_stock():
    """Genera un DataFrame de ejemplo para entradas de stock."""
    datos = [
        {'fecha': '2024-01-05', 'producto': 'Café en Grano (Kg)', 'cantidad_recibida': 50},
        {'fecha': '2024-01-12', 'producto': 'Leche Entera (Litros)', 'cantidad_recibida': 100},
        {'fecha': '2024-01-18', 'producto': 'Pan Hamburguesa (Uni)', 'cantidad_recibida': 200},
        {'fecha': '2024-01-25', 'producto': 'Café en Grano (Kg)', 'cantidad_recibida': 50},
    ]
    return pd.DataFrame(datos)

def generar_ejemplo_ventas_ancho():
    """Genera un DataFrame de ejemplo en formato ancho para ventas."""
    fechas = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    datos = []
    
    for fecha in fechas:
        fila = {'fecha': fecha.strftime('%Y-%m-%d')}
        fila['Café en Grano (Kg)'] = int(10 + (hash(str(fecha) + 'cafe') % 15))
        fila['Leche Entera (Litros)'] = int(15 + (hash(str(fecha) + 'leche') % 20))
        fila['Pan Hamburguesa (Uni)'] = int(20 + (hash(str(fecha) + 'pan') % 25))
        datos.append(fila)
    
    return pd.DataFrame(datos)

# ============================================
# SIDEBAR CON NAVEGACIÓN Y TÍTULO SIEMPRE VISIBLE
# ============================================

with st.sidebar:
    st.title("📦 Stock Zero")
    st.markdown("### Sistema de Gestión de Inventario")
    st.markdown("---")
    
    # Navegación
    st.markdown("### 🧭 Navegación")
    
    opciones_menu = [
        "🚀 Optimización de Inventario",
        "🛒 Control de Inventario Básico"
    ]
    
    if RECIPES_AVAILABLE:
        opciones_menu.append("👨‍🍳 Recetas y Productos")
    
    pagina = st.radio(
        "Selecciona una sección:",
        opciones_menu,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Configuración (solo visible en página de Optimización)
    if pagina == "🚀 Optimización de Inventario":
        st.markdown("### ⚙️ Configuración del Análisis")
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
    else:
        # Valores por defecto cuando no estamos en Optimización
        lead_time = 7
        stock_seguridad = 3
        frecuencia = 7
    
    st.markdown("---")
    
    # Información del sistema
    st.markdown("### ℹ️ Información")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
    st.caption("🌐 Usuario: Demo")

# ============================================
# INICIALIZAR SESSION STATE
# ============================================

if 'df_ventas_trazabilidad' not in st.session_state:
    st.session_state['df_ventas_trazabilidad'] = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_vendida'])
if 'df_stock_trazabilidad' not in st.session_state:
    st.session_state['df_stock_trazabilidad'] = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida']) 
if 'inventario_df' not in st.session_state:
    st.session_state['inventario_df'] = generar_inventario_base(None, use_example_data=True)

# ============================================
# CONTENIDO PRINCIPAL SEGÚN PÁGINA SELECCIONADA
# ============================================

if pagina == "🚀 Optimización de Inventario":
    st.header("🚀 Optimización de Inventario (Pronóstico)")
    st.markdown("Analiza tus datos históricos de ventas para calcular puntos de reorden óptimos.")
    st.markdown("---")
    
    # --- Sección de Ejemplos y Formatos (CORREGIDA) ---
    with st.expander("📘 Guía de Formatos y Ejemplos de Archivos", expanded=False):
        st.markdown("### 📊 Formatos Aceptados")
        
        col_guia1, col_guia2 = st.columns(2)
        
        with col_guia1:
            st.markdown("#### 📈 Archivo de Ventas (Requerido)")
            
            # Formato Largo
            st.markdown("**Formato 1: Largo (Recomendado)**")
            ejemplo_ventas_largo = generar_ejemplo_ventas().head(5)
            st.dataframe(
                ejemplo_ventas_largo,
                use_container_width=True,
                hide_index=True
            )
            st.caption("↓ Descarga el archivo completo de ejemplo")
            csv_ventas = generar_ejemplo_ventas().to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo (Formato Largo)",
                data=csv_ventas,
                file_name="ejemplo_ventas_largo.csv",
                mime="text/csv",
                key="download_ventas_largo"
            )
            
            st.markdown("---")
            
            # Formato Ancho
            st.markdown("**Formato 2: Ancho**")
            ejemplo_ventas_ancho = generar_ejemplo_ventas_ancho().head(5)
            st.dataframe(
                ejemplo_ventas_ancho,
                use_container_width=True,
                hide_index=True
            )
            st.caption("↓ Descarga el archivo completo de ejemplo")
            csv_ventas_ancho = ejemplo_ventas_ancho.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo (Formato Ancho)",
                data=csv_ventas_ancho,
                file_name="ejemplo_ventas_ancho.csv",
                mime="text/csv",
                key="download_ventas_ancho"
            )
        
        with col_guia2:
            st.markdown("#### 📦 Archivo de Entradas de Stock (Opcional)")
            st.markdown("**Formato: Largo**")
            
            ejemplo_stock = generar_ejemplo_stock()
            st.dataframe(
                ejemplo_stock,
                use_container_width=True,
                hide_index=True
            )
            st.info("💡 **Nota:** Este archivo es opcional pero mejora la precisión del análisis de trazabilidad.")
            
            csv_stock = ejemplo_stock.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo de Stock",
                data=csv_stock,
                file_name="ejemplo_stock.csv",
                mime="text/csv",
                key="download_stock"
            )
        
        st.markdown("---")
        st.markdown("### ✅ Requisitos Importantes")
        st.markdown("""
        - **Fechas:** Formato `YYYY-MM-DD` (ejemplo: 2024-01-15)
        - **Columnas:** No usar espacios adicionales ni caracteres especiales
        - **Cantidades:** Solo números positivos
        - **Codificación:** UTF-8 (estándar para CSV)
        - **Separador:** Coma (`,`)
        """)
    
    # --- Carga de Archivos ---
    st.markdown("### 1️⃣ Sube tus archivos")
    
    col_ventas, col_stock = st.columns(2)
    
    uploaded_file_ventas = col_ventas.file_uploader(
        "📈 Archivo CSV de **Ventas Históricas** (Requerido)",
        type=['csv'],
        key="upload_ventas",
        help="Carga un archivo CSV con tus datos de ventas. Puedes descargar un ejemplo arriba."
    )
    
    uploaded_file_stock = col_stock.file_uploader(
        "📦 Archivo CSV de **Entradas de Stock** (Opcional)",
        type=['csv'],
        key="upload_stock",
        help="Opcional: Carga un archivo CSV con el historial de entradas de stock para mejor trazabilidad."
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
                st.error("❌ Formato de VENTAS no reconocido. Revisa la guía de formatos arriba.")
                st.stop()
            
            # Limpieza robusta de datos de ventas
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
            df_ventas = df_ventas.dropna(subset=['fecha'])
            df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)
            
            # Procesar archivo de STOCK
            df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida']) 
            if uploaded_file_stock is not None:
                try:
                    df_raw_stock = pd.read_csv(uploaded_file_stock)
                    
                    # Validar columnas requeridas
                    columnas_requeridas = ['fecha', 'producto', 'cantidad_recibida']
                    columnas_presentes = df_raw_stock.columns.tolist()
                    
                    # Verificar si las columnas existen (ignorando mayúsculas/minúsculas y espacios)
                    columnas_normalizadas = {col.strip().lower(): col for col in columnas_presentes}
                    
                    if all(col.lower() in columnas_normalizadas for col in columnas_requeridas):
                        # Renombrar columnas si es necesario
                        df_raw_stock = df_raw_stock.rename(columns={
                            columnas_normalizadas['fecha']: 'fecha',
                            columnas_normalizadas['producto']: 'producto',
                            columnas_normalizadas['cantidad_recibida']: 'cantidad_recibida'
                        })
                        
                        df_stock = df_raw_stock[['fecha', 'producto', 'cantidad_recibida']].copy()
                        df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
                        df_stock = df_stock.dropna(subset=['fecha'])
                        df_stock['fecha'] = df_stock['fecha'].dt.normalize()
                        df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
                        st.success("✅ Historial de Entradas de Stock cargado correctamente.")
                    else:
                        st.warning(f"""
                        ⚠️ **El archivo de STOCK no contiene las columnas esperadas.**
                        
                        **Columnas encontradas:** {', '.join(columnas_presentes)}
                        
                        **Columnas requeridas:** fecha, producto, cantidad_recibida
                        
                        💡 Descarga el ejemplo de formato correcto arriba en la guía.
                        """)
                        df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])

                except Exception as e:
                    st.error(f"❌ Error al procesar el archivo de STOCK: {str(e)}")
                    st.info("💡 Descarga el archivo de ejemplo para ver el formato correcto.")
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
                
            st.markdown("### 2️⃣ Resumen de Datos Cargados")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📁 Formato Ventas", formato_detectado.upper())
            with col2: st.metric("📦 Productos únicos", df_ventas['producto'].nunique())
            with col3: st.metric("📅 Total registros", len(df_ventas))
            with col4: st.metric("📊 Días de datos", (df_ventas['fecha'].max() - df_ventas['fecha'].min()).days + 1)
            
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
                        mensaje_stock = "⚠️ **Stock Inicial/Actual no cargado.** Usando Stock = 0. ¡Actualiza el Stock Actual en Control de Inventario Básico!"
                        
                        if not df_inv_basico.empty and 'Producto' in df_inv_basico.columns:
                            stock_row = df_inv_basico[df_inv_basico['Producto'] == producto_seleccionado_inv]
                            if not stock_row.empty:
                                try:
                                    stock_actual = float(stock_row['Stock Actual'].iloc[0])
                                    mensaje_stock = f"Stock Inicial/Actual: **{stock_actual:.2f}** (tomado de Control de Inventario Básico)."
                                except:
                                    stock_actual = 0.0
                        
                        st.info(mensaje_stock)

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
                                st.error(f"❌ No se pudo generar la trazabilidad para {producto_seleccionado_inv}.")
                        
                        except Exception as e:
                            st.error(f"❌ Error al generar la trazabilidad: {str(e)}")

                    # Gráfico Comparativo
                    st.markdown("---")
                    st.markdown("### 📊 Tendencias de Ventas (Visión General)")
                    fig_comparativo = crear_grafico_comparativo(df_exitosos.to_dict('records'))
                    st.pyplot(fig_comparativo)
            
                else:
                    st.info("ℹ️ No se pudo calcular la optimización para ningún producto. Verifica que tengas suficientes datos históricos.")

            else:
                 st.info("👆 Haz clic en 'Calcular para TODOS los productos' para ver los resultados del análisis.")

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
            st.info("💡 Descarga un archivo de ejemplo de la guía de formatos para verificar la estructura correcta.")
            st.stop()
    else:
        st.info("📂 Sube tu archivo de ventas para comenzar el análisis. Puedes descargar ejemplos en la guía de formatos arriba.")

# ============================================
# PÁGINA: CONTROL DE INVENTARIO BÁSICO
# ============================================
elif pagina == "🛒 Control de Inventario Básico":
    inventario_basico_app()

# ============================================
# PÁGINA: RECETAS Y PRODUCTOS
# ============================================
elif pagina == "👨‍🍳 Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("⚠️ El módulo de recetas no está disponible.")
        st.info("Crea el archivo `modules/recipes.py` para habilitar esta funcionalidad.")
