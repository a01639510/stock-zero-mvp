# stock_zero_mvp_centered.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os  # Para variables de entorno

# --- IMPORTACIONES PARA SUPABASE (quita si no lo usas) ---
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.warning("⚠️ Supabase no está instalado. Instala con 'pip install supabase' para habilitar guardado en DB.")

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
    initial_sidebar_state="collapsed"  # Sin sidebar por defecto
)

# ============================================
# TÍTULO CENTRADO Y NAVEGACIÓN PRINCIPAL
# ============================================

# Título centrado
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; color: #4361EE; margin-bottom: 0.5rem;'>
            📦 StockZero
        </h1>
        <p style='font-size: 1.2rem; color: #666; margin-top: 0;'>
            Sistema de Gestión de Inventario
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Valores de configuración fijos
lead_time = 7
stock_seguridad = 3
frecuencia = 7

# --- BOTÓN DE SUBIR ARCHIVOS EN ESQUINA SUPERIOR (SIEMPRE ACTIVO) ---
col_title, col_upload = st.columns([8, 2])  # Para alinear a la derecha
with col_upload:
    if st.button("📤 Subir Archivos", key="upload_button_top", type="primary"):
        st.session_state.show_upload = not st.session_state.get('show_upload', False)

# --- SECCIÓN TIPO POPUP PARA SUBIR ARCHIVOS ---
if st.session_state.get('show_upload', False):
    # Simular popup con CSS (fondo sombreado y centrado)
    st.markdown("""
        <style>
            .popup-container {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                max-width: 80%;
                overflow-y: auto;
            }
            .overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
        </style>
        <div class="overlay" onclick="st.session_state.show_upload = False"></div>
    """, unsafe_allow_html=True)
    
    with st.container():  # Contenedor para el "popup"
        st.markdown('<div class="popup-container">', unsafe_allow_html=True)
        st.header("📂 Subir Archivos de Datos")
        
        with st.expander("📘 Guía de Formatos y Ejemplos", expanded=True):
            st.markdown("### 📊 Formatos Aceptados")
            
            col_guia1, col_guia2 = st.columns(2)
            
            with col_guia1:
                st.markdown("#### 📈 Archivo de Ventas (Requerido)")
                
                # Formato Largo
                st.markdown("**Formato 1: Largo (Recomendado)**")
                # Asume que tienes una función generar_ejemplo_ventas() en tu código original
                ejemplo_ventas_largo = pd.DataFrame({  # Ejemplo simple, reemplaza con tu función
                    'fecha': ['2025-01-01', '2025-01-01'],
                    'producto': ['Café en Grano (Kg)', 'Leche Entera (Litros)'],
                    'cantidad_vendida': [7, 14]
                }).head(5)
                st.dataframe(ejemplo_ventas_largo, use_container_width=True, hide_index=True)
                csv_ventas = ejemplo_ventas_largo.to_csv(index=False)
                st.download_button(label="⬇️ Descargar Ejemplo (Largo)", data=csv_ventas, file_name="ejemplo_ventas_largo.csv", mime="text/csv")
                
                # Formato Ancho (similar)
                st.markdown("**Formato 2: Ancho**")
                # Asume generar_ejemplo_ventas_ancho()
                ejemplo_ventas_ancho = pd.DataFrame({  # Ejemplo
                    'fecha': ['2025-01-01'],
                    'Café en Grano (Kg)': [7],
                    'Leche Entera (Litros)': [14]
                }).head(5)
                st.dataframe(ejemplo_ventas_ancho, use_container_width=True, hide_index=True)
                csv_ancho = ejemplo_ventas_ancho.to_csv(index=False)
                st.download_button(label="⬇️ Descargar Ejemplo (Ancho)", data=csv_ancho, file_name="ejemplo_ventas_ancho.csv", mime="text/csv")
            
            with col_guia2:
                st.markdown("#### 📦 Archivo de Entradas de Stock (Opcional)")
                # Similar, agrega tu ejemplo aquí
                ejemplo_stock = pd.DataFrame({
                    'fecha': ['2024-12-31'],
                    'producto': ['Café en Grano (Kg)'],
                    'cantidad_recibida': [120]
                }).head(5)
                st.dataframe(ejemplo_stock, use_container_width=True, hide_index=True)
                csv_stock = ejemplo_stock.to_csv(index=False)
                st.download_button(label="⬇️ Descargar Ejemplo Stock", data=csv_stock, file_name="ejemplo_stock.csv", mime="text/csv")
        
        # Uploaders
        uploaded_ventas = st.file_uploader("📈 Sube Archivo de Ventas (CSV)", type=["csv"])
        uploaded_stock = st.file_uploader("📦 Sube Archivo de Stock (Opcional, CSV)", type=["csv"])
        
        if uploaded_ventas:
            try:
                df_ventas = pd.read_csv(uploaded_ventas)
                # Validación básica
                required_cols = ['fecha', 'producto']  # Ajusta según formato
                if not all(col in df_ventas.columns for col in required_cols):
                    st.error("❌ Formato inválido. Revisa la guía.")
                else:
                    # Procesamiento (largo/ancho, como en tu código original)
                    # Asume que tienes lógica para convertir ancho a largo si es necesario
                    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
                    st.session_state['df_ventas_trazabilidad'] = df_ventas
                    st.success("✅ Ventas subidas correctamente.")
                    
                    # Guardar en Supabase si disponible
                    if SUPABASE_AVAILABLE:
                        supabase: Client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
                        # Ejemplo: Insertar en tabla 'ventas'
                        data = df_ventas.to_dict('records')
                        supabase.table('ventas').insert(data).execute()
                        st.info("💾 Datos guardados en Supabase (tabla 'ventas').")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if uploaded_stock:
            # Similar procesamiento para stock
            df_stock = pd.read_csv(uploaded_stock)
            df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
            st.session_state['df_stock_trazabilidad'] = df_stock
            st.success("✅ Stock subido correctamente.")
            
            if SUPABASE_AVAILABLE:
                supabase: Client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
                data = df_stock.to_dict('records')
                supabase.table('stock').insert(data).execute()
                st.info("💾 Datos guardados en Supabase (tabla 'stock').")
        
        if st.button("❌ Cerrar", key="close_upload"):
            st.session_state.show_upload = False
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- RESTO DEL CÓDIGO ORIGINAL (Navegación, páginas, etc.) ---
# Navegación centrada como subtítulos
st.markdown("---")
st.markdown("## 🧭 Secciones Disponibles")

# Crear columnas para centrar los botones
col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])

with col2:
    if st.button("📊 Dashboard Inteligente", use_container_width=True, type="primary"):
        st.session_state.pagina_actual = "Dashboard Inteligente"

with col3:
    if st.button("🚀 Optimización de Inventario", use_container_width=True):
        st.session_state.pagina_actual = "Optimización de Inventario"

with col4:
    if st.button("📦 Control de Inventario", use_container_width=True):
        st.session_state.pagina_actual = "Control de Inventario Básico"

if RECIPES_AVAILABLE:
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
    with col3:
        if st.button("👨‍🍳 Recetas y Productos", use_container_width=True):
            st.session_state.pagina_actual = "Recetas y Productos"

# Información del sistema
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        📅 {} | 🌐 Usuario: Demo
    </div>
    """.format(datetime.now().strftime('%d/%m/%Y')), 
    unsafe_allow_html=True
)

# Determinar página actual
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "Dashboard Inteligente"

pagina = st.session_state.pagina_actual

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

st.markdown("---")

if pagina == "Dashboard Inteligente":
    # Importar y ejecutar el dashboard mejorado
    try:
        from pages._0_Dashboard_Enhanced import dashboard_enhanced_app
        dashboard_enhanced_app()
    except ImportError:
        st.error("❌ El módulo del dashboard mejorado no está disponible. Asegúrate de que el archivo 'pages/_0_Dashboard_Enhanced.py' exista.")
    except Exception as e:
        st.error(f"❌ Error al cargar el dashboard mejorado: {str(e)}")

elif pagina == "Optimización de Inventario":
    st.header("🚀 Optimización de Inventario (Pronóstico)")
    st.markdown("Analiza tus datos históricos de ventas para calcular puntos de reorden óptimos.")
    st.markdown("---")
    
    # Usa datos de session_state si ya subidos
    if not st.session_state['df_ventas_trazabilidad'].empty:
        st.success("✅ Datos de ventas ya subidos. Puedes calcular directamente.")
        df_ventas = st.session_state['df_ventas_trazabilidad']
        df_stock = st.session_state.get('df_stock_trazabilidad', pd.DataFrame())
    else:
        st.info("📂 Sube archivos desde el botón superior para comenzar.")
        # Resto de tu código de optimización...

    # ... [resto del código de optimización, usando df_ventas y df_stock]

# ... [Resto del código original para otras páginas]
# ============================================
# CONTENIDO PRINCIPAL SEGÚN PÁGINA SELECCIONADA
# ============================================

st.markdown("---")

if pagina == "Dashboard Inteligente":
    # Importar y ejecutar el dashboard mejorado
    try:
        from pages._0_Dashboard_Enhanced import dashboard_enhanced_app
        dashboard_enhanced_app()
    except ImportError:
        st.error("❌ El módulo del dashboard mejorado no está disponible. Asegúrate de que el archivo 'pages/_0_Dashboard_Enhanced.py' exista.")
    except Exception as e:
        st.error(f"❌ Error al cargar el dashboard mejorado: {str(e)}")

elif pagina == "Optimización de Inventario":
    st.header("🚀 Optimización de Inventario (Pronóstico)")
    st.markdown("Analiza tus datos históricos de ventas para calcular puntos de reorden óptimos.")
    # ... [resto del código de optimización]

elif pagina == "Control de Inventario Básico":
    inventario_basico_app()

elif pagina == "Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("⚠️ El módulo de recetas no está disponible.")
elif pagina == "🚀 Optimización de Inventario":
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
                    columnas_presentes = df_raw_stock.columns.str.strip().str.lower()
                    columnas_normalizadas = {col.lower(): col for col in df_raw_stock.columns}
                    
                    if all(col in columnas_normalizadas for col in columnas_requeridas):
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
                        
                        **Columnas encontradas:** {', '.join(df_raw_stock.columns)}
                        
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

