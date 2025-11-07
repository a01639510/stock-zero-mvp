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
        
        # Volumen Total Vendido (Necesario para ABC)
        volumen_total_vendido = df_diario['cantidad_vendida'].sum()
        
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'producto': nombre_producto,
                'error': f'Datos insuficientes (mínimo {frecuencia_estacional * 2} días)',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0,
                'volumen_total_vendido': volumen_total_vendido
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
            'volumen_total_vendido': volumen_total_vendido, # Incluido para ABC
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
            'pronostico_diario_promedio': 0.0,
            'volumen_total_vendido': 0.0
        }


def procesar_multiple_productos(
    df: pd.DataFrame,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> List[Dict]:
    """
    Procesa múltiples productos y realiza la clasificación ABC.
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
        
    # --- Clasificación ABC ---
    # Convertir a DataFrame temporal para Clasificación ABC
    df_resultados = pd.DataFrame(resultados)

    if 'error' not in df_resultados.columns:
        df_resultados['error'] = None
    
    df_resultados['clasificacion_abc'] = 'N/A'

    df_abc = df_resultados[df_resultados['error'].isnull() & (df_resultados['volumen_total_vendido'] > 0)].copy()
    
    if not df_abc.empty:
        # 2. Ordenar por volumen total de venta
        df_abc = df_abc.sort_values('volumen_total_vendido', ascending=False)
        
        # 3. Calcular porcentaje y porcentaje acumulado
        total_volumen = df_abc['volumen_total_vendido'].sum()
        df_abc['volumen_pct'] = (df_abc['volumen_total_vendido'] / total_volumen) * 100
        df_abc['volumen_acum_pct'] = df_abc['volumen_pct'].cumsum()
        
        # 4. Asignar categoría A, B, C (Regla 80/15/5)
        df_abc['clasificacion_abc'] = np.select(
            [
                df_abc['volumen_acum_pct'] <= 80,  # 80% del valor/volumen total
                df_abc['volumen_acum_pct'] <= 95   # 80% + 15% = 95%
            ],
            [
                'A',
                'B'
            ],
            default='C'
        )
        
        # 5. Fusionar la clasificación ABC de vuelta al DataFrame original
        df_resultados.loc[df_abc.index, 'clasificacion_abc'] = df_abc['clasificacion_abc']
    
    return df_resultados.to_dict('records')

# ============================================
# FUNCIONES DE TRAZABILIDAD Y GRÁFICOS (NUEVOS)
# ============================================
def calcular_trazabilidad_inventario(
    df_ventas: pd.DataFrame, 
    df_entradas: pd.DataFrame, 
    nombre_producto: str, 
    stock_actual_manual: float,
    pronostico_diario_promedio: float,
    lead_time: int
):
    """
    Calcula la trazabilidad histórica del stock y la proyecta al futuro.
    
    CORRECCIÓN: Se asegura que todas las comparaciones de fechas usen 
    el tipo datetime.date de Python para evitar errores de atributos.
    """
    import numpy as np # Asegurar que numpy esté disponible en el alcance de la función
    from datetime import datetime, timedelta

    # 1. PREPARACIÓN DE DATOS DIARIOS
    
    ventas_prod = df_ventas[df_ventas['producto'] == nombre_producto][['fecha', 'cantidad_vendida']]
    entradas_prod = df_entradas[df_entradas['producto'] == nombre_producto][['fecha', 'cantidad_recibida']]

    if ventas_prod.empty and entradas_prod.empty:
        return None

    # Encontrar rango de fechas de manera segura
    min_date_ventas = ventas_prod['fecha'].min().date() if not ventas_prod.empty else datetime.now().date()
    min_date_entradas = entradas_prod['fecha'].min().date() if not entradas_prod.empty else datetime.now().date()
    min_date = min(min_date_ventas, min_date_entradas)
    
    fecha_actual = datetime.now().date()
    
    dias_proyeccion = (fecha_actual - min_date).days + lead_time + 10
    fechas = pd.date_range(start=min_date, periods=dias_proyeccion, name='Fecha')
    
    df_diario = pd.DataFrame(index=fechas)
    df_diario['Ventas'] = 0.0
    df_diario['Entradas'] = 0.0
    
    # Mapear ventas y entradas a la serie diaria (uso de .intersection para evitar warnings)
    if not ventas_prod.empty:
        ventas_diarias = ventas_prod.set_index('fecha').resample('D').sum()['cantidad_vendida'].fillna(0)
        df_diario.loc[df_diario.index.intersection(ventas_diarias.index), 'Ventas'] = ventas_diarias
        
    if not entradas_prod.empty:
        entradas_diarias = entradas_prod.set_index('fecha').resample('D').sum()['cantidad_recibida'].fillna(0)
        df_diario.loc[df_diario.index.intersection(entradas_diarias.index), 'Entradas'] = entradas_diarias

    # 2. CÁLCULO DEL INVENTARIO HISTÓRICO
    
    df_diario['Stock'] = 0.0
    stock_t = stock_actual_manual
    
    # Iterar hacia atrás:
    for date_ts in reversed(df_diario.index):
        date = date_ts.date() # Convertir Timestamp a date para comparación
        
        if date > fecha_actual:
            continue 
        
        df_diario.loc[date_ts, 'Stock'] = stock_t
        
        ventas_t = df_diario.loc[date_ts, 'Ventas']
        entradas_t = df_diario.loc[date_ts, 'Entradas']
        
        stock_t = stock_t + ventas_t - entradas_t
        stock_t = max(0, stock_t)
        
    # 3. PROYECCIÓN DEL INVENTARIO FUTURO
    
    # Asegurar el stock del día de hoy
    try:
        df_diario.loc[fecha_actual.strftime("%Y-%m-%d"), 'Stock'] = stock_actual_manual
    except KeyError:
         pass 

    # Proyectar hacia adelante:
    for i, date_ts in enumerate(df_diario.index):
        date = date_ts.date()
        
        if date > fecha_actual:
            
            # Obtener el índice anterior
            idx_anterior = df_diario.index[i - 1]
            stock_anterior = df_diario.loc[idx_anterior, 'Stock']
            stock_proyectado = stock_anterior - pronostico_diario_promedio
            
            df_diario.loc[date_ts, 'Stock'] = max(0, stock_proyectado)
            
    # 4. MARCAR LA DIVISIÓN (LA CORRECCIÓN CLAVE PARA EL ERROR DE ATRIBUTO)
    
    # 🏆 CONVERTIMOS EXPLICITAMENTE EL ÍNDICE A OBJETOS DE FECHA DE PYTHON
    fechas_indice = np.array([d.date() for d in df_diario.index])
    
    # Usamos np.where para la comparación segura.
    df_diario['Tipo'] = np.where(fechas_indice <= fecha_actual, 'Histórico', 'Proyectado')
    
    return df_diario.reset_index()
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
    
    # Filtrar datos
    df_hist = df_trazabilidad[df_trazabilidad['Tipo'] == 'Histórico']
    df_proj = df_trazabilidad[df_trazabilidad['Tipo'] == 'Proyectado']
    
    # 1. Stock Histórico (Línea Sólida)
    ax.plot(df_hist['Fecha'], df_hist['Stock'], 
            color='#1f77b4', linewidth=3, 
            label='Stock Real Histórico')
            
    # 2. Stock Proyectado (Línea Punteada)
    ax.plot(df_proj['Fecha'], df_proj['Stock'], 
            color='#ff7f0e', linewidth=2, linestyle='--',
            label='Stock Proyectado (Demanda media)')

    # 3. Línea del Punto de Reorden (PR)
    ax.axhline(y=punto_reorden, color='red', linestyle='-', 
               linewidth=1.5, alpha=0.8,
               label=f'Punto de Reorden ({punto_reorden:.0f})')
               
    # 4. Línea del Stock Máximo Teórico (PR + OA)
    stock_maximo = punto_reorden + cantidad_a_ordenar
    ax.axhline(y=stock_maximo, color='green', linestyle=':', 
               linewidth=1.5, alpha=0.6,
               label=f'Stock Máximo Teórico ({stock_maximo:.0f})')
               
    # Resaltar la fecha actual
    fecha_actual = datetime.now().date()
    ax.axvline(x=fecha_actual, color='gray', linestyle='-.', alpha=0.5, label='Fecha Actual')
    
    # Configuración del gráfico
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Stock (Unidades)', fontsize=12)
    ax.set_title(f'📉 Trazabilidad y Proyección de Inventario para {nombre}', 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df_trazabilidad) // 10))) # Intervalo dinámico
    plt.xticks(rotation=45, ha='right')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    plt.tight_layout()
    
    return fig


def crear_grafico_comparativo(resultados: List[Dict]):
    # Mantenemos la función comparativa para una visión general
    # ... (código de crear_grafico_comparativo - No está en el código provisto, asumo que existe o la omitiremos)
    # Por ahora, para no romper nada, crearemos una función placeholder:
    
    df = pd.DataFrame([r for r in resultados if 'error' not in r])
    if df.empty:
        return plt.figure()
        
    df_sorted = df.sort_values('volumen_total_vendido', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_sorted['producto'], df_sorted['volumen_total_vendido'], color='skyblue')
    ax.set_title('Volumen Total de Ventas por Producto')
    ax.set_ylabel('Unidades Vendidas')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return fig
    
# La función crear_grafico_individual se ELIMINA ya que es redundante con el nuevo gráfico de Trazabilidad Total


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
    
    df['Faltante?'] = df['Stock Actual'] < df['Punto de Reorden (PR)']
    df['Valor Total'] = df['Stock Actual'] * df['Costo Unitario']
    return df

def inventario_basico_app():
    """Interfaz para el control de inventario básico tipo Excel."""
    
    st.header("🛒 Control de Inventario Básico")
    st.info("💡 Usa esta sección para gestionar el stock físico. Las alertas se activan si el 'Stock Actual' cae por debajo del 'Punto de Reorden'.")

    if 'inventario_df' not in st.session_state:
        st.session_state['inventario_df'] = generar_inventario_base()

    df_inventario = st.session_state['inventario_df'].copy()

    # --- Edición del DataFrame ---
    st.subheader("1️⃣ Inventario Actual (Edición en Vivo)")
    
    editable_columns = ['Producto', 'Categoría', 'Unidad', 'Stock Actual', 'Punto de Reorden (PR)', 'Costo Unitario']
    column_config = {
        "Producto": st.column_config.TextColumn("Producto", required=True),
        "Stock Actual": st.column_config.NumberColumn("Stock Actual", required=True, format="%.2f"),
        "Punto de Reorden (PR)": st.column_config.NumberColumn("Punto de Reorden (PR)", required=True, format="%.2f"),
        "Costo Unitario": st.column_config.NumberColumn("Costo Unitario", format="$%.2f"),
        "Faltante?": st.column_config.CheckboxColumn("Faltante?", disabled=True),
        "Valor Total": st.column_config.NumberColumn("Valor Total", disabled=True, format="$%.2f"),
    }
    
    # Convertir a solo las columnas editables para el data_editor y manejar las demás después
    df_editable_subset = df_inventario[editable_columns]
    
    edited_df = st.data_editor(
        df_editable_subset,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_inventario"
    )

    # Re-calcular columnas derivadas
    if not edited_df.empty:
        try:
            # Asegurar que las columnas son numéricas antes del cálculo
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
        **Ventas:** `fecha`, `producto`, `cantidad_vendida`
        **Stock:** `fecha`, `producto`, `cantidad_recibida`
        """)

    # --- Carga de Archivos ---
    st.markdown("### 1️⃣ Sube tus archivos (Ventas y Stock)")
    
    col_ventas, col_stock = st.columns(2)
    
    with col_ventas:
        uploaded_file_ventas = st.file_uploader(
            "Archivo CSV de **Ventas Históricas** (Requerido)",
            type=['csv'],
            key="upload_ventas"
        )
    
    with col_stock:
        uploaded_file_stock = st.file_uploader(
            "Archivo CSV de **Entradas de Stock** (Opcional para Trazabilidad)",
            type=['csv'],
            key="upload_stock"
        )

    # Procesar archivo de VENTAS
    if uploaded_file_ventas is not None:
        try:
            df_raw_ventas = pd.read_csv(uploaded_file_ventas)
            
            # Detección de formato para VENTAS (mismo código anterior)
            formato_detectado = None
            if 'producto' in df_raw_ventas.columns and 'cantidad_vendida' in df_raw_ventas.columns:
                formato_detectado = "largo"
                df_ventas = df_raw_ventas.copy()
            elif 'fecha' in df_raw_ventas.columns and len(df_raw_ventas.columns) > 2:
                formato_detectado = "ancho"
                df_ventas = df_raw_ventas.melt(id_vars=['fecha'], var_name='producto', value_name='cantidad_vendida')
            else:
                st.error("❌ Formato de VENTAS no reconocido.")
                st.stop()
            
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
            df_ventas = df_ventas.dropna(subset=['fecha'])
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)
            
            # Procesar archivo de STOCK (Nuevo)
            df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida']) # DF vacío por defecto
            if uploaded_file_stock is not None:
                try:
                    df_raw_stock = pd.read_csv(uploaded_file_stock)
                    if 'fecha' in df_raw_stock.columns and 'producto' in df_raw_stock.columns and 'cantidad_recibida' in df_raw_stock.columns:
                        df_stock = df_raw_stock.copy()
                        df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
                        df_stock = df_stock.dropna(subset=['fecha'])
                        df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
                        st.success("✅ Historial de Entradas de Stock cargado.")
                    else:
                        st.warning("⚠️ El archivo de STOCK no contiene las columnas esperadas: `fecha`, `producto`, `cantidad_recibida`. La trazabilidad histórica no estará disponible.")
                        df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])

                except Exception as e:
                    st.error(f"Error al procesar el archivo de STOCK: {str(e)}")
                    df_stock = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])


            st.markdown("### 2️⃣ Datos cargados correctamente")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📁 Formato Ventas", formato_detectado.upper())
            with col2: st.metric("📦 Productos únicos", df_ventas['producto'].nunique())
            with col3: st.metric("📅 Total registros Ventas", len(df_ventas))
            with col4: st.metric("📊 Días de datos Ventas", (df_ventas['fecha'].max() - df_ventas['fecha'].min()).days + 1)
            
            with st.expander("👁️ Ver datos de Ventas"):
                st.dataframe(df_ventas.head(20), use_container_width=True)
            
            productos = sorted(df_ventas['producto'].unique())
            st.markdown(f"**Productos encontrados:** {', '.join(productos)}")
            
            st.markdown("### 3️⃣ Calcular Inventario Óptimo")
            
            if st.button("🚀 Calcular para TODOS los productos", type="primary", use_container_width=True):
                with st.spinner(f"Analizando {len(productos)} productos..."):
                    resultados = procesar_multiple_productos(
                        df_ventas,
                        lead_time,
                        stock_seguridad,
                        frecuencia
                    )
                
                # Convertir lista de diccionarios a DataFrame para manejo más fácil
                df_resultados = pd.DataFrame(resultados)
                df_exitosos = df_resultados[df_resultados['error'].isnull()].sort_values('cantidad_a_ordenar', ascending=False)
                
                st.markdown("---")
                st.markdown("## 📊 Resultados del Análisis")
                
                if not df_exitosos.empty:
                    st.success(f"✅ Se analizaron exitosamente {len(df_exitosos)} productos")
                    
                    # Métricas
                    total_reorden = df_exitosos['punto_reorden'].sum()
                    total_ordenar = df_exitosos['cantidad_a_ordenar'].sum()
                    cobertura_orden = frecuencia / 2
                    
                    col1, col2, col3 = st.columns(3)
                    with col1: st.metric("🎯 Total Punto de Reorden", f"{total_reorden:.0f} unidades")
                    with col2: st.metric("📦 Total a Ordenar", f"{total_ordenar:.0f} unidades")
                    with col3: st.metric("💡 Cobertura de la Orden", f"{cobertura_orden} días")
                    
                    # Tabla con ABC
                    st.markdown("### 📋 Recomendaciones y Clasificación ABC")
                    
                    df_display = df_exitosos[['producto', 'clasificacion_abc', 'punto_reorden', 'cantidad_a_ordenar', 
                                              'pronostico_diario_promedio']].copy()
                    
                    df_display.columns = ['Producto', 'ABC', 'Punto de Reorden', 'Cantidad a Ordenar', 'Venta Diaria Promedio']
                    df_display['Punto de Reorden'] = df_display['Punto de Reorden'].apply(lambda x: f"{x:.0f}")
                    df_display['Cantidad a Ordenar'] = df_display['Cantidad a Ordenar'].apply(lambda x: f"{x:.0f}")
                    df_display['Venta Diaria Promedio'] = df_display['Venta Diaria Promedio'].apply(lambda x: f"{x:.1f}")
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    st.info("""
                    **Clasificación ABC:** **A** (80% del volumen), **B** (15% del volumen), **C** (5% restante).
                    """)
                    
                    # ============================================
                    # GRÁFICO DE TRAZABILIDAD TOTAL (NUEVO CORE)
                    # ============================================
                    st.markdown("---")
                    st.markdown("### 📈 Trazabilidad de Inventario (Histórico y Proyectado)")
                    
                    # Cargar el DF de Inventario Básico del state
                    df_inv_basico = st.session_state.get('inventario_df', pd.DataFrame())
                    
                    # Selector de producto
                    producto_seleccionado_inv = st.selectbox(
                        "Selecciona un producto para ver la trazabilidad de stock:",
                        options=df_exitosos['producto'].tolist(),
                        key="selector_inventario_proyectado"
                    )
                    
                    if producto_seleccionado_inv:
                        resultado_prod = df_exitosos[df_exitosos['producto'] == producto_seleccionado_inv].iloc[0].to_dict()
                        
                        # Obtener Stock Actual
                        stock_actual = 0.0
                        if not df_inv_basico.empty and 'Producto' in df_inv_basico.columns:
                            stock_row = df_inv_basico[df_inv_basico['Producto'] == producto_seleccionado_inv]
                            if not stock_row.empty:
                                stock_actual = pd.to_numeric(stock_row['Stock Actual'].iloc[0], errors='coerce').fillna(0)
                            else:
                                st.warning(f"⚠️ **{producto_seleccionado_inv}** no encontrado en la pestaña de Control de Inventario Básico. Usando Stock Actual = 0.")
                        else:
                            st.warning("⚠️ El Control de Inventario Básico no está cargado. Usando Stock Actual = 0.")
                        
                        # Generar Trazabilidad Total
                        df_trazabilidad = calcular_trazabilidad_inventario(
                            df_ventas,
                            df_stock,
                            producto_seleccionado_inv,
                            stock_actual,
                            resultado_prod['pronostico_diario_promedio'],
                            lead_time
                        )

                        if df_trazabilidad is not None:
                            fig_trazabilidad = crear_grafico_trazabilidad_total(
                                df_trazabilidad,
                                resultado_prod,
                                lead_time
                            )
                            st.pyplot(fig_trazabilidad)
                            
                            st.info(f"""
                            **Análisis de Trazabilidad (Stock Actual: {stock_actual:.0f} unidades):**
                            - **Línea Azul (Stock Real):** Muestra cómo se comportó el inventario históricamente (requiere archivo de Entradas de Stock).
                            - **Línea Naranja Punteada (Proyectado):** Simula la caída del stock futuro usando el Pronóstico Diario.
                            - **Línea Roja (PR):** Tu punto crítico. Si la línea de Stock la cruza, estás en riesgo de quiebre.
                            """)
                        else:
                            st.error(f"❌ No hay datos de ventas o stock disponibles para {producto_seleccionado_inv} para generar la trazabilidad.")

                    # Gráfico Comparativo de todos los productos (se mantiene para visión general)
                    st.markdown("---")
                    st.markdown("### 📊 Tendencias de Ventas (Visión General)")
                    fig_comparativo = crear_grafico_comparativo(df_exitosos.to_dict('records'))
                    st.pyplot(fig_comparativo)

                # Mostrar errores si los hay
                df_errores = df_resultados[df_resultados['error'].notnull()]
                if not df_errores.empty:
                    st.markdown("---")
                    st.warning(f"⚠️ {len(df_errores)} productos no pudieron analizarse por datos insuficientes.")
                    for idx, row in df_errores.iterrows():
                        st.error(f"**{row['producto']}:** {row['error']}")
                
        except Exception as e:
            st.error(f"Error al procesar el archivo de ventas: {str(e)}")

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
