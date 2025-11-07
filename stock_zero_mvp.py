import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union, List
import warnings
warnings.filterwarnings('ignore')


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
        cantidad_a_ordenar = pronostico_diario_promedio * 14
        
        return {
            'producto': nombre_producto,
            'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'demanda_lead_time': round(demanda_lead_time, 2),
            'stock_seguridad': round(stock_seguridad, 2),
            'dias_historicos': len(df_diario)
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


# ============================================
# CONFIGURACIÓN DE TEMA
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide")

# CSS personalizado - Tema Azul Marino
st.markdown("""

    
<style>
/* ===========================
   FIX: expander title y botones de descarga
   =========================== */

/* Expander: forzar texto blanco y fondo azul marino */
.streamlit-expanderHeader,
div[data-testid="stExpander"] .streamlit-expanderHeader {
    color: #ffffff !important;
    background-color: #1e3a5f !important;
    border-left: 3px solid #1e3a5f !important;
    font-weight: 700 !important;
}

/* Si el título del expander está dentro de un botón/label (variaciones DOM) */
div[data-testid="stExpander"] button.streamlit-expanderHeader,
div[data-testid="stExpander"] button .streamlit-expanderHeader,
.streamlit-expanderHeader * {
    color: #ffffff !important;
}

/* Asegurar que el texto dentro del expander (no el header) se mantenga legible */
div[data-testid="stExpander"] .streamlit-expanderContent,
div[data-testid="stExpander"] .streamlit-expanderContent * {
    color: #1a202c !important;
    background-color: #ffffff !important;
}

/* Tabs: mantener texto blanco cuando seleccionados (refuerzo) */
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] * {
    background-color: #1e3a5f !important;
    color: #ffffff !important;
}

/* Botones de descarga - todas las variaciones posibles */
.stDownloadButton > button,
div[data-testid="stDownloadButton"] button,
button[data-testid="stDownloadButton"],
.stDownloadButton button,
div.stDownloadButton > button,
div[jscontroller] .stDownloadButton > button { 
    background-color: #1e3a5f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Forzar color blanco a todo el contenido interno del botón (span, svg, texto) */
.stDownloadButton > button * ,
div[data-testid="stDownloadButton"] button * {
    color: #ffffff !important;
}

/* Hover del botón descarga */
.stDownloadButton > button:hover,
div[data-testid="stDownloadButton"] button:hover {
    background-color: #2d5a8f !important;
}

/* Asegurar que enlaces o etiquetas dentro del botón también sean blancos */
.stDownloadButton a, .stDownloadButton a * {
    color: #ffffff !important;
}

/* Variante: cuando el botón está dentro de un tab/expander (casos DOM distintos) */
div[data-testid="stExpander"] .stDownloadButton > button,
div[data-testid="stExpander"] .stDownloadButton button,
div[role="tablist"] .stDownloadButton > button {
    background-color: #1e3a5f !important;
    color: #ffffff !important;
}

/* Protección extra: si el botón tiene clases dinámicas con css-*, forzar color */
button[class^="css-"] {
    color: inherit !important;
}

/* Quitar sombras indeseadas que puedan hacer el texto difícil de leer */
.stDownloadButton > button:focus,
.stDownloadButton > button:active {
    box-shadow: none !important;
    outline: none !important;
}
</style>
    <style>
    /* === FIX: Colores para tabs seleccionados y botones dentro === */
    
    /* Texto de encabezado del expander "Ver formatos de archivo aceptado" */
    .streamlit-expanderHeader {
        color: white !important;
        background-color: #1e3a5f !important;
        border-left: 3px solid #1e3a5f !important;
    }

    /* Cuando se abre el expander, mantener el fondo claro adentro */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
    }

    /* Tabs (cuando están seleccionados) */
    .stTabs [aria-selected="true"] {
        background-color: #1e3a5f !important;
        color: white !important;
    }

    /* Texto dentro de los tabs activos */
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] label,
    .stTabs [aria-selected="true"] div {
        color: white !important;
    }

    /* Botones de descarga dentro de tabs */
    .stDownloadButton > button {
        background-color: #1e3a5f !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    .stDownloadButton > button:hover {
        background-color: #2d5a8f !important;
    }
    </style>

    <style>
    /* Fondo principal blanco */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Texto principal en gris oscuro */
    .stApp, .stMarkdown, p, span, label {
        color: #1a202c !important;
    }
    
    /* Sidebar con azul marino */
    [data-testid="stSidebar"] {
        background-color: #1e3a5f;
    }
    
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* Headers en azul marino */
    h1, h2, h3 {
        color: #1e3a5f !important;
    }
    
    /* Botones principales en azul marino */
    .stButton > button {
        background-color: #1e3a5f;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2d5a8f;
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    /* Métricas con borde azul */
    [data-testid="stMetricValue"] {
        color: #1e3a5f !important;
        font-weight: 700;
    }
    
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1e3a5f;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #1e3a5f;
        border-radius: 8px;
        padding: 20px;
        background-color: #f8fafc;
    }
    
    [data-testid="stFileUploader"] label {
        color: #1e3a5f !important;
    }
    
    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
    }
    
    [data-testid="stFileUploader"] small {
        color: #64748b !important;
    }
    
    [data-testid="stFileUploader"] button {
        background-color: #1e3a5f !important;
        color: white !important;
        border: none !important;
    }
    
    [data-testid="stFileUploader"] button:hover {
        background-color: #2d5a8f !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-left: 3px solid #1e3a5f;
        font-weight: 600;
        color: #1e3a5f;
    }
    
    /* DataFrames */
    .dataframe {
        border: 1px solid #e2e8f0 !important;
    }
    
    .dataframe th {
        background-color: #1e3a5f !important;
        color: white !important;
        font-weight: 600;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8fafc;
        color: #1e3a5f;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e3a5f;
        color: white !important;
    }
    
    /* Info/Success/Warning boxes */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #1e3a5f;
        color: white;
        border-radius: 8px;
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        background-color: #1e3a5f;
    }
    
    /* Divider */
    hr {
        border-color: #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# INTERFAZ WEB
# ============================================

# Header
st.title("📦 Stock Zero")
st.subheader("Optimización de Inventario para Pymes - Multi-Producto")
st.markdown("---")

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
    
    **Formato Ancho**:
    - fecha
    - [Producto1]
    - [Producto2]
    - ...
    """)

# Upload CSV
st.markdown("### 1️⃣ Sube tu archivo de ventas")
st.markdown("Acepta **múltiples productos** en el mismo archivo")

uploaded_file = st.file_uploader(
    "Selecciona tu archivo CSV",
    type=['csv'],
    help="Puede contener uno o varios productos"
)

# Mostrar ejemplos de formato
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
        
        csv_largo = ejemplo_largo.to_csv(index=False)
        st.download_button(
            "⬇️ Descargar Plantilla Formato Largo",
            csv_largo,
            "plantilla_largo.csv",
            "text/csv"
        )
    
    with tab2:
        st.markdown("**Típico de hojas de Excel**")
        ejemplo_ancho = pd.DataFrame({
            'fecha': ['2024-09-01', '2024-09-02', '2024-09-03'],
            'Cerveza Corona': [45, 52, 48],
            'Tacos al Pastor': [120, 135, 128],
            'Coca-Cola': [38, 41, 35]
        })
        st.dataframe(ejemplo_ancho, use_container_width=True)
        
        csv_ancho = ejemplo_ancho.to_csv(index=False)
        st.download_button(
            "⬇️ Descargar Plantilla Formato Ancho",
            csv_ancho,
            "plantilla_ancho.csv",
            "text/csv"
        )

# Procesar archivo
if uploaded_file is not None:
    try:
        # Leer CSV
        df_raw = pd.read_csv(uploaded_file)
        
        # Detectar formato (Largo vs Ancho)
        formato_detectado = None
        
        if 'producto' in df_raw.columns and 'cantidad_vendida' in df_raw.columns:
            # Formato LARGO
            formato_detectado = "largo"
            df = df_raw.copy()
            
        elif 'fecha' in df_raw.columns and len(df_raw.columns) > 2:
            # Formato ANCHO - convertir a largo
            formato_detectado = "ancho"
            df = df_raw.melt(
                id_vars=['fecha'],
                var_name='producto',
                value_name='cantidad_vendida'
            )
        else:
            st.error("❌ Formato no reconocido. El archivo debe tener:")
            st.markdown("- **Formato Largo:** columnas `fecha`, `producto`, `cantidad_vendida`")
            st.markdown("- **Formato Ancho:** columna `fecha` y una columna por producto")
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
        
        # Mostrar preview
        with st.expander("👁️ Ver datos cargados"):
            st.dataframe(df.head(20), use_container_width=True)
        
        # Lista de productos
        productos = sorted(df['producto'].unique())
        st.markdown(f"**Productos encontrados:** {', '.join(productos)}")
        
        # Botón de cálculo
        st.markdown("### 3️⃣ Calcular Inventario Óptimo")
        
        if st.button("🚀 Calcular para TODOS los productos", type="primary", use_container_width=True):
            with st.spinner(f"Analizando {len(productos)} productos con Holt-Winters..."):
                resultados = procesar_multiple_productos(
                    df,
                    lead_time,
                    stock_seguridad,
                    frecuencia
                )
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown("## 📊 Resultados del Análisis")
            
            # Separar exitosos y con errores
            exitosos = [r for r in resultados if 'error' not in r]
            con_errores = [r for r in resultados if 'error' in r]
            
            if exitosos:
                st.success(f"✅ Se analizaron exitosamente {len(exitosos)} productos")
                
                # Crear DataFrame de resultados
                df_resultados = pd.DataFrame(exitosos)
                
                # Ordenar por cantidad a ordenar (mayor a menor)
                df_resultados = df_resultados.sort_values('cantidad_a_ordenar', ascending=False)
                
                # Calcular totales
                total_reorden = df_resultados['punto_reorden'].sum()
                total_ordenar = df_resultados['cantidad_a_ordenar'].sum()
                
                # Métricas generales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎯 Total Punto de Reorden", f"{total_reorden:.0f} unidades")
                with col2:
                    st.metric("📦 Total a Ordenar", f"{total_ordenar:.0f} unidades")
                with col3:
                    capital_liberado = (total_ordenar * 1.5) - total_ordenar
                    st.metric("💰 Capital Liberado", f"{capital_liberado:.0f} unidades")
                
                # Tabla de resultados detallada
                st.markdown("---")
                st.markdown("### 📋 Recomendaciones por Producto")
                
                # Formatear tabla para display
                df_display = df_resultados[['producto', 'punto_reorden', 'cantidad_a_ordenar', 
                                           'pronostico_diario_promedio', 'dias_historicos']].copy()
                
                df_display.columns = ['Producto', 'Punto de Reorden', 'Cantidad a Ordenar', 
                                     'Venta Diaria Promedio', 'Días Analizados']
                
                # Aplicar formato
                df_display['Punto de Reorden'] = df_display['Punto de Reorden'].apply(lambda x: f"{x:.0f}")
                df_display['Cantidad a Ordenar'] = df_display['Cantidad a Ordenar'].apply(lambda x: f"{x:.0f}")
                df_display['Venta Diaria Promedio'] = df_display['Venta Diaria Promedio'].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Botón de descarga
                csv_resultados = df_resultados.to_csv(index=False)
                st.download_button(
                    "📥 Descargar Resultados Completos (CSV)",
                    csv_resultados,
                    "stock_zero_resultados.csv",
                    "text/csv",
                    use_container_width=True
                )
                
                # Top 5 productos que más necesitas ordenar
                st.markdown("---")
                st.markdown("### 🔝 Top 5 Productos Prioritarios")
                
                top5 = df_resultados.head(5)
                
                for idx, row in top5.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    with col1:
                        st.markdown(f"**{row['producto']}**")
                    with col2:
                        st.metric("Reorden", f"{row['punto_reorden']:.0f}")
                    with col3:
                        st.metric("A Ordenar", f"{row['cantidad_a_ordenar']:.0f}")
                    with col4:
                        st.metric("Diario", f"{row['pronostico_diario_promedio']:.1f}")
                
                # Interpretación
                st.markdown("---")
                st.markdown("### 💡 ¿Cómo usar estos resultados?")
                st.markdown("""
                **Para cada producto:**
                
                1. **Punto de Reorden:** Cuando tu inventario llegue a esta cantidad, es momento de ordenar.
                
                2. **Cantidad a Ordenar:** La cantidad óptima que debes pedir para cubrir ~14 días.
                
                3. **Venta Diaria Promedio:** Tu demanda esperada por día según el análisis.
                
                **Ejemplo práctico:**
                - Si "Cerveza Corona" tiene Punto de Reorden = 50 y Cantidad a Ordenar = 100
                - Cuando te queden 50 cervezas, ordena 100 más
                - Esto optimiza tu capital y evita faltantes
                """)
            
            # Mostrar errores si los hay
            if con_errores:
                st.markdown("---")
                st.warning(f"⚠️ {len(con_errores)} productos no pudieron analizarse:")
                
                for error in con_errores:
                    st.error(f"**{error['producto']}:** {error['error']}")
                
                st.info("💡 **Tip:** Estos productos probablemente necesitan más días de historial de ventas.")
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Verifica que tu archivo CSV esté en uno de los formatos aceptados.")

else:
    # Pantalla inicial
    st.info("👆 **Comienza subiendo tu archivo CSV de ventas (uno o múltiples productos)**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 Paso 1")
        st.markdown("Sube tu CSV con historial de ventas de todos tus productos")
    
    with col2:
        st.markdown("### ⚙️ Paso 2")
        st.markdown("Ajusta la configuración según tu operación")
    
    with col3:
        st.markdown("### 🚀 Paso 3")
        st.markdown("Obtén recomendaciones para cada producto")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b;'>
    <p style='color: #1e3a5f; font-weight: 600; font-size: 16px;'>Stock Zero MVP</p>
    <p>Optimización Multi-Producto con Holt-Winters</p>
    <p>Diseñado para Pymes en México 🇲🇽 | Soporta formato largo y ancho</p>
</div>
""", unsafe_allow_html=True)
