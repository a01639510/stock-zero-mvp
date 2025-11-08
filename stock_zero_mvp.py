import streamlit as st
import pandas as pd
import io
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
        st.error("El módulo de recetas no está disponible. Crea el archivo `modules/recipes.py`")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN E INICIO DE LA APLICACIÓN
# ============================================

st.set_page_config(
    page_title="Stock Zero",
    page_icon="Box",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# INICIALIZAR SESSION STATE (PERSISTENCIA)
# ============================================

if 'uploaded_ventas_bytes' not in st.session_state:
    st.session_state.uploaded_ventas_bytes = None
if 'uploaded_stock_bytes' not in st.session_state:
    st.session_state.uploaded_stock_bytes = None

if 'df_ventas' not in st.session_state:
    st.session_state.df_ventas = None
if 'df_stock' not in st.session_state:
    st.session_state.df_stock = None

if 'df_ventas_trazabilidad' not in st.session_state:
    st.session_state.df_ventas_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_vendida'])
if 'df_stock_trazabilidad' not in st.session_state:
    st.session_state.df_stock_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])

if 'inventario_df' not in st.session_state:
    st.session_state.inventario_df = generar_inventario_base(None, use_example_data=True)

# ============================================
# FUNCIONES AUXILIARES PARA EJEMPLOS
# ============================================

def generar_ejemplo_ventas():
    fechas = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    datos = []
    productos = ['Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)']
    for fecha in fechas:
        for producto in productos:
            cantidad = int(10 + (hash(str(fecha) + producto) % 20))
            datos.append({'fecha': fecha.strftime('%Y-%m-%d'), 'producto': producto, 'cantidad_vendida': cantidad})
    return pd.DataFrame(datos)

def generar_ejemplo_stock():
    return pd.DataFrame([
        {'fecha': '2024-01-05', 'producto': 'Café en Grano (Kg)', 'cantidad_recibida': 50},
        {'fecha': '2024-01-12', 'producto': 'Leche Entera (Litros)', 'cantidad_recibida': 100},
        {'fecha': '2024-01-18', 'producto': 'Pan Hamburguesa (Uni)', 'cantidad_recibida': 200},
        {'fecha': '2024-01-25', 'producto': 'Café en Grano (Kg)', 'cantidad_recibida': 50},
    ])

def generar_ejemplo_ventas_ancho():
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
# SIDEBAR CON NAVEGACIÓN
# ============================================

with st.sidebar:
    st.title("Stock Zero")
    st.markdown("### Sistema de Gestión de Inventario")
    st.markdown("---")

    st.markdown("### Navegación")
    opciones_menu = ["Optimización de Inventario", "Control de Inventario Básico"]
    if RECIPES_AVAILABLE:
        opciones_menu.append("Recetas y Productos")

    pagina = st.radio("Selecciona una sección:", opciones_menu, label_visibility="collapsed")
    st.markdown("---")

    # Configuración solo en Optimización
    if pagina == "Optimización de Inventario":
        st.markdown("### Configuración del Análisis")
        lead_time = st.slider("Lead Time (días)", 1, 30, 7, help="Días que tarda tu proveedor en entregar")
        stock_seguridad = st.slider("Stock de Seguridad (días)", 1, 10, 3, help="Días adicionales de buffer")
        frecuencia = st.selectbox("Estacionalidad", [7, 14, 30], index=0,
            format_func=lambda x: f"{x} días ({'Semanal' if x==7 else 'Mensual' if x==30 else 'Quincenal'})")
    else:
        lead_time, stock_seguridad, frecuencia = 7, 3, 7

    st.markdown("---")
    st.markdown("### Información")
    st.caption(f"{datetime.now().strftime('%d/%m/%Y')}")
    st.caption("Usuario: Demo")

    st.markdown("---")
    st.markdown("### Datos Cargados")
    if st.session_state.df_ventas is not None:
        st.success(f"Ventas: {len(st.session_state.df_ventas)} registros")
    else:
        st.warning("Ventas: No cargadas")
    if st.session_state.df_stock is not None:
        st.info(f"Stock: {len(st.session_state.df_stock)} entradas")
    else:
        st.info("Stock: No cargado")

# ============================================
# CONTENIDO PRINCIPAL
# ============================================

if pagina == "Optimización de Inventario":
    st.header("Optimización de Inventario (Pronóstico)")
    st.markdown("Analiza tus datos históricos de ventas para calcular puntos de reorden óptimos.")
    st.markdown("---")

    # --- GUÍA DE FORMATOS (TABLAS TIPO EXCEL) ---
    with st.expander("Guía de Formatos y Ejemplos de Archivos", expanded=False):
        st.markdown("### Formatos Aceptados")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Archivo de Ventas (Requerido)")

            st.markdown("**Formato 1: Largo (Recomendado)**")
            st.dataframe(generar_ejemplo_ventas().head(5), use_container_width=True, hide_index=True)
            st.caption("↓ Descarga completa")
            st.download_button("Descargar Ejemplo (Largo)", generar_ejemplo_ventas().to_csv(index=False),
                               "ejemplo_ventas_largo.csv", "text/csv", key="dl_largo")

            st.markdown("---")
            st.markdown("**Formato 2: Ancho**")
            st.dataframe(generar_ejemplo_ventas_ancho().head(5), use_container_width=True, hide_index=True)
            st.caption("↓ Descarga completa")
            st.download_button("Descargar Ejemplo (Ancho)", generar_ejemplo_ventas_ancho().to_csv(index=False),
                               "ejemplo_ventas_ancho.csv", "text/csv", key="dl_ancho")

        with col2:
            st.markdown("#### Archivo de Entradas de Stock (Opcional)")
            st.dataframe(generar_ejemplo_stock(), use_container_width=True, hide_index=True)
            st.info("Mejora la precisión de la trazabilidad.")
            st.download_button("Descargar Ejemplo de Stock", generar_ejemplo_stock().to_csv(index=False),
                               "ejemplo_stock.csv", "text/csv", key="dl_stock")

        st.markdown("---")
        st.markdown("### Requisitos Importantes")
        st.markdown("""
        - **Fechas:** `YYYY-MM-DD`
        - **Columnas:** Sin espacios ni caracteres especiales
        - **Cant Lovers:** Números positivos
        - **Codificación:** UTF-8
        - **Separador:** Coma (`,`)
        """)

    # --- CARGA PERSISTENTE DE ARCHIVOS ---
    st.markdown("### 1️⃣ Sube tus archivos")

    col_ventas, col_stock = st.columns(2)

    uploaded_file_ventas = col_ventas.file_uploader(
        "Archivo CSV de **Ventas Históricas** (Requerido)",
        type=['csv'], key="uploader_ventas", help="Se mantiene al cambiar de página"
    )

    uploaded_file_stock = col_stock.file_uploader(
        "Archivo CSV de **Entradas de Stock** (Opcional)",
        type=['csv'], key="uploader_stock", help="Historial de entradas"
    )

    # --- PROCESAR VENTAS ---
    if uploaded_file_ventas is not None:
        st.session_state.uploaded_ventas_bytes = uploaded_file_ventas.getvalue()
        try:
            df_raw = pd.read_csv(uploaded_file_ventas)
            if 'producto' not in df_raw.columns and len(df_raw.columns) > 2:
                df_ventas = df_raw.melt(id_vars=['fecha'], var_name='producto', value_name='cantidad_vendida')
                formato = "ancho"
            else:
                df_ventas = df_raw[['fecha', 'producto', 'cantidad_vendida']].copy()
                formato = "largo"

            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
            df_ventas = df_ventas.dropna(subset=['fecha']).copy()
            df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)

            st.session_state.df_ventas = df_ventas
            st.session_state.df_ventas_trazabilidad = df_ventas.copy()
            st.success("Ventas cargadas correctamente.")
        except Exception as e:
            st.error(f"Error: {e}")

    elif st.session_state.uploaded_ventas_bytes is not None:
        try:
            df_ventas = pd.read_csv(io.BytesIO(st.session_state.uploaded_ventas_bytes))
            if 'producto' not in df_ventas.columns and len(df_ventas.columns) > 2:
                df_ventas = df_ventas.melt(id_vars=['fecha'], var_name='producto', value_name='cantidad_vendida')
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
            df_ventas = df_ventas.dropna(subset=['fecha']).copy()
            df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)
            st.session_state.df_ventas = df_ventas
            st.session_state.df_ventas_trazabilidad = df_ventas.copy()
        except:
            pass

    # --- PROCESAR STOCK ---
    if uploaded_file_stock is not None:
        st.session_state.uploaded_stock_bytes = uploaded_file_stock.getvalue()
        try:
            df_raw = pd.read_csv(uploaded_file_stock)
            cols = {c.strip().lower(): c for c in df_raw.columns}
            req = ['fecha', 'producto', 'cantidad_recibida']
            if all(r in cols for r in req):
                df_stock = df_raw.rename(columns={cols[r]: r for r in req})[req].copy()
                df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
                df_stock = df_stock.dropna(subset=['fecha']).copy()
                df_stock['fecha'] = df_stock['fecha'].dt.normalize()
                df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
                st.session_state.df_stock = df_stock
                st.session_state.df_stock_trazabilidad = df_stock.copy()
                st.success("Stock cargado.")
            else:
                st.warning("Columnas de stock no válidas.")
        except Exception as e:
            st.error(f"Error en stock: {e}")

    elif st.session_state.uploaded_stock_bytes is not None:
        try:
            df_stock = pd.read_csv(io.BytesIO(st.session_state.uploaded_stock_bytes))
            cols = {c.strip().lower(): c for c in df_stock.columns}
            req = ['fecha', 'producto', 'cantidad_recibida']
            if all(r in cols for r in req):
                df_stock = df_stock.rename(columns={cols[r]: r for r in req})[req].copy()
                df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
                df_stock = df_stock.dropna(subset=['fecha']).copy()
                df_stock['fecha'] = df_stock['fecha'].dt.normalize()
                df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
                st.session_state.df_stock = df_stock
                st.session_state.df_stock_trazabilidad = df_stock.copy()
        except:
            pass

    # --- CONTINUAR SI HAY DATOS ---
    if st.session_state.df_ventas is not None:
        df_ventas = st.session_state.df_ventas

        # Reiniciar inventario si hay nuevos productos
        if 'inventario_df' in st.session_state:
            current = set(st.session_state.inventario_df['Producto'].tolist())
            example = {'Café en Grano (Kg)', 'Leche Entera (Litros)', 'Pan Hamburguesa (Uni)'}
            if example.issubset(current):
                st.session_state.inventario_df = generar_inventario_base(df_ventas, use_example_data=False)
        else:
            st.session_state.inventario_df = generar_inventario_base(df_ventas)

        st.markdown("### 2️⃣ Resumen de Datos")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Formato", "ANCHO" if 'melt' in locals() else "LARGO")
        with col2: st.metric("Productos", df_ventas['producto'].nunique())
        with col3: st.metric("Registros", len(df_ventas))
        with col4: st.metric("Días", (df_ventas['fecha'].max() - df_ventas['fecha'].min()).days + 1)
        st.markdown(f"**Productos:** {', '.join(sorted(df_ventas['producto'].unique()))}")

        st.markdown("### 3️⃣ Calcular Inventario Óptimo")
        if st.button("Calcular para TODOS los productos", type="primary", use_container_width=True):
            with st.spinner("Analizando..."):
                df_resultados = procesar_multiple_productos(df_ventas, lead_time, stock_seguridad, frecuencia)
            st.session_state.df_resultados = df_resultados
            st.rerun()

        if 'df_resultados' in st.session_state:
            df_resultados = st.session_state.df_resultados
            df_exitosos = df_resultados[df_resultados['error'].isnull()].sort_values('cantidad_a_ordenar', ascending=False)

            st.markdown("---")
            st.markdown("## Resultados del Análisis")
            if not df_exitosos.empty:
                st.success(f"{len(df_exitosos)} productos analizados.")
                col1, col2 = st.columns(2)
                with col1: st.metric("Total PR", f"{df_exitosos['punto_reorden'].sum():.0f}")
                with col2: st.metric("Total a Ordenar", f"{df_exitosos['cantidad_a_ordenar'].sum():.0f}")

                st.markdown("### Recomendaciones ABC")
                df_display = df_exitosos[['producto', 'clasificacion_abc', 'punto_reorden', 'cantidad_a_ordenar']].copy()
                df_display.columns = ['Producto', 'ABC', 'PR', 'Ordenar']
                df_display['PR'] = df_display['PR'].apply(lambda x: f"{x:.0f}")
                df_display['Ordenar'] = df_display['Ordenar'].apply(lambda x: f"{x:.0f}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                st.markdown("### Trazabilidad de Inventario")
                producto = st.selectbox("Producto:", df_exitosos['producto'].tolist(), key="sel_traz")
                if producto:
                    res = df_exitosos[df_exitosos['producto'] == producto].iloc[0].to_dict()
                    df_inv = st.session_state.get('inventario_df', pd.DataFrame())
                    stock_actual = 0.0
                    if not df_inv.empty:
                        row = df_inv[df_inv['Producto'] == producto]
                        if not row.empty:
                            stock_actual = float(row['Stock Actual'].iloc[0])
                    st.info(f"Stock Actual: **{stock_actual:.2f}**")

                    df_traz = calcular_trazabilidad_inventario(
                        st.session_state.df_ventas_trazabilidad,
                        st.session_state.df_stock_trazabilidad,
                        producto, stock_actual, res['punto_reorden'],
                        res['cantidad_a_ordenar'], res['pronostico_diario_promedio'], lead_time
                    )
                    if df_traz is not None and not df_traz.empty:
                        fig = crear_grafico_trazabilidad_total(df_traz, res, lead_time)
                        st.pyplot(fig)

                st.markdown("### Tendencias de Ventas")
                fig = crear_grafico_comparativo(df_exitosos.to_dict('records'))
                st.pyplot(fig)
            else:
                st.info("No hay suficientes datos.")
        else:
            st.info("Haz clic en 'Calcular' para ver resultados.")
    else:
        st.info("Sube tu archivo de ventas para comenzar.")

# ============================================
# OTRAS PÁGINAS
# ============================================
elif pagina == "Control de Inventario Básico":
    inventario_basico_app()

elif pagina == "Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("Módulo de recetas no disponible.")
        st.info("Crea `modules/recipes.py`")
