import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Union
import warnings
warnings.filterwarnings('ignore')


def calcular_orden_optima(
    ruta_archivo_csv: str,
    lead_time: int = 7,
    stock_seguridad_dias: int = 3,
    frecuencia_estacional: int = 7
) -> Dict[str, Union[float, str]]:
    """
    Calcula el punto de reorden y la cantidad óptima a ordenar usando Holt-Winters.
    """
    try:
        # 1. CARGA Y VALIDACIÓN DE DATOS
        df = pd.read_csv(ruta_archivo_csv)
        
        if 'fecha' not in df.columns or 'cantidad_vendida' not in df.columns:
            return {
                'error': 'El CSV debe contener las columnas: fecha, cantidad_vendida',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0
            }
        
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
        df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce').fillna(0)
        
        # 2. PREPARACIÓN DE SERIE TEMPORAL CONTINUA
        df = df.set_index('fecha').sort_index()
        df_diario = df.resample('D').sum()
        df_diario['cantidad_vendida'] = df_diario['cantidad_vendida'].fillna(0)
        
        if len(df_diario) < frecuencia_estacional * 2:
            return {
                'error': f'Se necesitan al menos {frecuencia_estacional * 2} días de datos históricos',
                'punto_reorden': 0.0,
                'cantidad_a_ordenar': 0.0,
                'pronostico_diario_promedio': 0.0
            }
        
        # 3. MODELO HOLT-WINTERS ESTACIONAL
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
        
        # 4. CÁLCULOS DE NEGOCIO
        demanda_lead_time = pronostico.sum()
        pronostico_diario_promedio = pronostico.mean()
        stock_seguridad = pronostico_diario_promedio * stock_seguridad_dias
        punto_reorden = demanda_lead_time + stock_seguridad
        cantidad_a_ordenar = pronostico_diario_promedio * 14
        
        # 5. PREPARAR OUTPUT
        resultado = {
            'punto_reorden': round(punto_reorden, 2),
            'cantidad_a_ordenar': round(cantidad_a_ordenar, 2),
            'pronostico_diario_promedio': round(pronostico_diario_promedio, 2),
            'demanda_lead_time': round(demanda_lead_time, 2),
            'stock_seguridad': round(stock_seguridad, 2),
            'dias_historicos_analizados': len(df_diario),
            'configuracion': {
                'lead_time': lead_time,
                'stock_seguridad_dias': stock_seguridad_dias,
                'frecuencia_estacional': frecuencia_estacional
            }
        }
        
        return resultado
        
    except FileNotFoundError:
        return {
            'error': f'Archivo no encontrado: {ruta_archivo_csv}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0
        }
    
    except Exception as e:
        return {
            'error': f'Error en el cálculo: {str(e)}',
            'punto_reorden': 0.0,
            'cantidad_a_ordenar': 0.0,
            'pronostico_diario_promedio': 0.0
        }


# ============================================
# INTERFAZ WEB CON STREAMLIT
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide")

# Header
st.title("📦 Stock Zero")
st.subheader("Optimización de Inventario para Pymes")
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

# Upload CSV
st.markdown("### 1️⃣ Sube tu archivo de ventas")
st.markdown("Tu archivo CSV debe contener dos columnas: **fecha** y **cantidad_vendida**")

uploaded_file = st.file_uploader(
    "Selecciona tu archivo CSV",
    type=['csv'],
    help="Formato: fecha (YYYY-MM-DD), cantidad_vendida (número)"
)

# Mostrar formato ejemplo
with st.expander("📋 Ver formato de archivo requerido"):
    ejemplo = pd.DataFrame({
        'fecha': ['2024-09-01', '2024-09-02', '2024-09-03', '2024-09-04', '2024-09-05'],
        'cantidad_vendida': [45, 52, 48, 51, 75]
    })
    st.dataframe(ejemplo, use_container_width=True)
    
    # Botón para descargar plantilla
    csv_ejemplo = ejemplo.to_csv(index=False)
    st.download_button(
        "⬇️ Descargar Plantilla CSV",
        csv_ejemplo,
        "plantilla_stock_zero.csv",
        "text/csv",
        help="Descarga esta plantilla y llénala con tus datos"
    )

# Procesar archivo
if uploaded_file is not None:
    try:
        # Guardar temporalmente
        with open("temp_ventas.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Mostrar preview de datos
        st.markdown("### 2️⃣ Vista previa de tus datos")
        df_preview = pd.read_csv("temp_ventas.csv")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df_preview.head(10), use_container_width=True)
        with col2:
            st.metric("Total de registros", len(df_preview))
            st.metric("Rango de fechas", f"{len(df_preview)} días")
        
        # Botón de cálculo
        st.markdown("### 3️⃣ Calcular Inventario Óptimo")
        
        if st.button("🚀 Calcular Ahora", type="primary", use_container_width=True):
            with st.spinner("Analizando tus datos con Holt-Winters..."):
                resultado = calcular_orden_optima(
                    ruta_archivo_csv="temp_ventas.csv",
                    lead_time=lead_time,
                    stock_seguridad_dias=stock_seguridad,
                    frecuencia_estacional=frecuencia
                )
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown("## 📊 Resultados del Análisis")
            
            if 'error' in resultado:
                st.error(f"❌ {resultado['error']}")
                st.info("💡 **Sugerencias:**\n- Verifica que tu CSV tenga las columnas correctas\n- Asegúrate de tener al menos 14 días de datos\n- Revisa el formato de las fechas (YYYY-MM-DD)")
            else:
                # Métricas principales
                st.success("✅ Análisis completado exitosamente")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "🎯 Punto de Reorden",
                        f"{resultado['punto_reorden']:.0f}",
                        help="Cuando tu inventario llegue a este nivel, HAZ el pedido"
                    )
                    st.caption("unidades")
                
                with col2:
                    st.metric(
                        "📦 Cantidad a Ordenar",
                        f"{resultado['cantidad_a_ordenar']:.0f}",
                        help="Ordena esta cantidad para cubrir 14 días de operación"
                    )
                    st.caption("unidades")
                
                with col3:
                    st.metric(
                        "📈 Venta Diaria Promedio",
                        f"{resultado['pronostico_diario_promedio']:.1f}",
                        help="Pronóstico de ventas diarias"
                    )
                    st.caption("unidades/día")
                
                # Detalles adicionales
                st.markdown("---")
                st.markdown("#### 📊 Desglose Detallado")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Demanda durante Lead Time:** {resultado['demanda_lead_time']:.0f} unidades")
                    st.info(f"**Stock de Seguridad:** {resultado['stock_seguridad']:.0f} unidades")
                    st.info(f"**Días analizados:** {resultado['dias_historicos_analizados']} días")
                
                with col2:
                    # Calcular ROI aproximado
                    inventario_tradicional = resultado['cantidad_a_ordenar'] * 1.5
                    capital_liberado = inventario_tradicional - resultado['cantidad_a_ordenar']
                    ahorro_porcentaje = (capital_liberado / inventario_tradicional) * 100
                    
                    st.success(f"💰 **Capital liberado estimado:** {capital_liberado:.0f} unidades")
                    st.success(f"📉 **Reducción de inventario:** {ahorro_porcentaje:.1f}%")
                    st.success(f"✅ **Modelo utilizado:** Holt-Winters Estacional")
                
                # Interpretación para el cliente
                st.markdown("---")
                st.markdown("#### 💡 ¿Qué significa esto para tu negocio?")
                
                st.markdown(f"""
                **Recomendación de Stock Zero:**
                
                1. **Cuándo ordenar:** Cuando tu inventario llegue a **{resultado['punto_reorden']:.0f} unidades**, es momento de hacer el pedido a tu proveedor.
                
                2. **Cuánto ordenar:** Pide **{resultado['cantidad_a_ordenar']:.0f} unidades** para cubrir aproximadamente 14 días de operación.
                
                3. **Beneficio económico:** En lugar de mantener ~{inventario_tradicional:.0f} unidades "por las dudas", solo necesitas {resultado['cantidad_a_ordenar']:.0f} unidades. Esto libera **{capital_liberado:.0f} unidades de capital** que puedes usar en otras áreas de tu negocio.
                
                4. **Protección:** El stock de seguridad de {resultado['stock_seguridad']:.0f} unidades te protege de variaciones inesperadas en la demanda.
                """)
                
                # Configuración usada
                with st.expander("⚙️ Ver configuración del análisis"):
                    st.json(resultado['configuracion'])
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Verifica que tu archivo CSV esté en el formato correcto.")

else:
    # Pantalla inicial cuando no hay archivo
    st.info("👆 **Comienza subiendo tu archivo CSV de ventas**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 Paso 1")
        st.markdown("Prepara tu archivo CSV con el historial de ventas")
    
    with col2:
        st.markdown("### ⚙️ Paso 2")
        st.markdown("Ajusta la configuración según tu negocio")
    
    with col3:
        st.markdown("### 🚀 Paso 3")
        st.markdown("Obtén recomendaciones precisas de inventario")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Stock Zero MVP</strong> - Optimización de inventario basada en Holt-Winters</p>
    <p>Diseñado para Pymes en México 🇲🇽</p>
</div>
""", unsafe_allow_html=True)
