import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def crear_grafico_comparativo(resultados: List[Dict]) -> go.Figure:
    """
    Crea un gráfico interactivo comparando ventas históricas y pronósticos de múltiples productos.
    """
    fig = go.Figure()
    
    # Paleta de colores
    colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    productos_exitosos = [r for r in resultados if 'error' not in r]
    
    for idx, resultado in enumerate(productos_exitosos):
        color = colores[idx % len(colores)]
        nombre = resultado['producto']
        
        # Datos históricos (últimos 30 días)
        df_hist = resultado['datos_historicos']
        fechas_hist = df_hist.index
        ventas_hist = df_hist['cantidad_vendida'].values
        
        # Pronóstico
        fechas_pron = resultado['pronostico_fechas']
        valores_pron = resultado['pronostico_valores']
        
        # Línea sólida: Ventas históricas
        fig.add_trace(go.Scatter(
            x=fechas_hist,
            y=ventas_hist,
            mode='lines+markers',
            name=f'{nombre}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            legendgroup=nombre,
            showlegend=True
        ))
        
        # Línea punteada: Pronóstico
        # Conectar último punto histórico con pronóstico
        ultima_fecha_hist = fechas_hist[-1]
        ultimo_valor_hist = ventas_hist[-1]
        
        fechas_pronostico_completo = [ultima_fecha_hist] + fechas_pron
        valores_pronostico_completo = [ultimo_valor_hist] + valores_pron
        
        fig.add_trace(go.Scatter(
            x=fechas_pronostico_completo,
            y=valores_pronostico_completo,
            mode='lines',
            name=f'{nombre} (Pronóstico)',
            line=dict(color=color, width=2, dash='dash'),
            legendgroup=nombre,
            showlegend=True
        ))
        
        # Línea horizontal: Punto de reorden
        punto_reorden = resultado['punto_reorden']
        
        # Extender línea por todo el rango
        todas_fechas = list(fechas_hist) + fechas_pron
        
        fig.add_trace(go.Scatter(
            x=[todas_fechas[0], todas_fechas[-1]],
            y=[punto_reorden, punto_reorden],
            mode='lines',
            name=f'{nombre} - Punto Reorden ({punto_reorden:.0f})',
            line=dict(color=color, width=1, dash='dot'),
            legendgroup=nombre,
            showlegend=True,
            opacity=0.6
        ))
    
    # Configuración del gráfico
    fig.update_layout(
        title={
            'text': '📊 Ventas Históricas vs Pronóstico por Producto',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Fecha',
        yaxis_title='Cantidad Vendida',
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10)
        ),
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
    )
    
    return fig


# ============================================
# INTERFAZ WEB CON STREAMLIT
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide")

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
                
                # ============================================
                # GRÁFICO COMPARATIVO
                # ============================================
                st.markdown("---")
                st.markdown("### 📈 Visualización: Ventas y Pronósticos")
                
                try:
                    fig = crear_grafico_comparativo(exitosos)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("""
                    **Cómo leer este gráfico:**
                    - **Líneas sólidas:** Ventas reales de los últimos 30 días
                    - **Líneas punteadas:** Pronóstico de ventas futuras (Lead Time)
                    - **Líneas punteadas horizontales:** Punto de reorden (cuando ordenar)
                    - Cuando la demanda proyectada se acerca al punto de reorden, es momento de hacer el pedido
                    """)
                except Exception as e:
                    st.warning(f"No se pudo generar el gráfico: {str(e)}")
                
                # ============================================
                # MÉTRICAS Y TABLA
                # ============================================
                
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
<div style='text-align: center; color: #666;'>
    <p><strong>Stock Zero MVP</strong> - Optimización Multi-Producto con Holt-Winters</p>
    <p>Diseñado para Pymes en México 🇲🇽 | Soporta formato largo y ancho</p>
</div>
""", unsafe_allow_html=True)
