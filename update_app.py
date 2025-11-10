# update_app.py
import os

# === RUTA DE TU PROYECTO ===
BASE_DIR = "."  # Cambia si tu proyecto está en otra carpeta

# === ARCHIVOS A ACTUALIZAR ===
FILES = {
    "stock_zero_mvp.py": """# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Stock Zero", layout="wide")

# === SIDEBAR ÚNICO CON CONFIGURACIÓN ===
with st.sidebar:
    st.image("https://via.placeholder.com/100", caption="Stock Zero", width=100)
    st.markdown("### Navegación")
    st.markdown("- [Home](stock_zero_mvp.py)")
    st.markdown("- [Archivos](pages/1_Archivos.py)")
    st.markdown("- [Inventario](pages/2_Inventario.py)")
    st.markdown("- [Análisis](pages/3_Analisis.py)")
    st.markdown("- [Productos](pages/4_Productos.py)")
    
    st.markdown("---")
    st.markdown("### Configuración Estacional")
    st.session_state.lead_time = st.slider("Lead Time (días)", 1, 30, 7, key="lead_time")
    st.session_state.stock_seguridad_dias = st.slider("Stock Seguridad (días)", 0, 10, 3, key="seguridad")
    st.session_state.cantidad_minima = st.number_input("Cantidad Mínima por Pedido", min_value=1, value=50, key="min_pedido")

st.title("Stock Zero")
st.markdown("---")

st.header("Main Dashboard")

if 'df_ventas' not in st.session_state or st.session_state.df_ventas is None:
    st.warning("Sube datos en **Archivos** para ver el dashboard.")
    st.stop()

df_ventas = st.session_state.df_ventas.copy()
df_stock = st.session_state.get('df_stock', pd.DataFrame())

# === RECALCULAR SI ES NECESARIO ===
if 'df_resultados' not in st.session_state:
    with st.spinner("Procesando datos..."):
        try:
            from modules.core_analysis import procesar_multiple_productos
            st.session_state.df_resultados = procesar_multiple_productos(
                st.session_state.df_ventas,
                st.session_state.get('df_stock', pd.DataFrame())
            )
        except Exception as e:
            st.error(f"Error: {e}")

# === GRÁFICO DE FLUJO ===
st.markdown("### Flujo de Inventario")

try:
    from modules.analytics import analytics_app
    with st.container():
        analytics_app()

    df_sim = st.session_state.get('df_sim')
    PR = st.session_state.get('PR', 100)

    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    ventas_hist = df_ventas.groupby('fecha')['cantidad_vendida'].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=ventas_hist.index, y=ventas_hist.values, name="Ventas", marker_color="#4361EE"))
    if df_sim is not None and not df_sim.empty:
        fig.add_trace(go.Scatter(x=df_sim['fecha'], y=df_sim['stock'], mode='lines', name="Stock", line=dict(color="#4CC9F0", width=3)))
    fig.add_hline(y=PR, line_dash="dash", line_color="#FF6B6B", annotation_text=f"PR = {PR}")
    fig.update_layout(title="Flujo: Ventas + Stock + Punto de Reorden", height=500)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error en gráfico: {e}")

# === KPIs ===
col1, col2, col3, col4 = st.columns(4)
with col1:
    hoy = ventas_hist.iloc[-1] if len(ventas_hist) > 0 else 0
    st.metric("Ventas Hoy", f"{hoy:.0f}")
with col2:
    total = df_stock['cantidad_recibida'].sum() if not df_stock.empty and 'cantidad_recibida' in df_stock.columns else 0
    st.metric("Stock Total", f"{total:.0f}")
with col3:
    criticos = len(df_stock[df_stock['cantidad_recibida'] < 10]) if not df_stock.empty and 'cantidad_recibida' in df_stock.columns else 0
    st.metric("Productos Críticos", criticos)
with col4:
    valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum() if not df_stock.empty else 0
    st.metric("Valor Inventario", f"${valor:,.0f}")

st.success("Dashboard activo.")
""",

    "pages/1_Archivos.py": """# pages/1_Archivos.py
import streamlit as st
import pandas as pd

st.title("Archivos")

col1, col2 = st.columns(2)
with col1:
    uploaded_ventas = st.file_uploader("Ventas CSV", type="csv", key="ventas_upload")
with col2:
    uploaded_stock = st.file_uploader("Stock CSV", type="csv", key="stock_upload")

if uploaded_ventas:
    df = pd.read_csv(uploaded_ventas)
    st.session_state.df_ventas = df
    st.session_state.df_ventas_trazabilidad = df.copy()
    st.success("Ventas cargadas")
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.rerun()

if uploaded_stock:
    df = pd.read_csv(uploaded_stock)
    st.session_state.df_stock = df
    st.success("Stock cargado")
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.rerun()

if 'df_ventas' in st.session_state:
    st.markdown("### Editar Ventas")
    edited = st.data_editor(st.session_state.df_ventas, num_rows="dynamic")
    if st.button("Guardar Ventas"):
        st.session_state.df_ventas = edited
        st.session_state.df_ventas_trazabilidad = edited
        if 'df_resultados' in st.session_state:
            del st.session_state.df_resultados
        st.rerun()

if 'df_stock' in st.session_state:
    st.markdown("### Editar Stock")
    edited = st.data_editor(st.session_state.df_stock, num_rows="dynamic")
    if st.button("Guardar Stock"):
        st.session_state.df_stock = edited
        if 'df_resultados' in st.session_state:
            del st.session_state.df_resultados
        st.rerun()
""",

    "pages/2_Inventario.py": """# pages/2_Inventario.py
import streamlit as st
from modules.components import inventario_basico_app

st.title("Inventario")

if 'df_stock' not in st.session_state:
    st.warning("Sube stock en **Archivos**")
    st.stop()

df_stock = st.session_state.df_stock.copy()

col1, col2 = st.columns(2)
valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum()
with col1: st.metric("Valor Total", f"${valor:,.0f}")
with col2: st.metric("Productos", len(df_stock))

bajos = df_stock[df_stock['cantidad_recibida'] < 10]
if not bajos.empty:
    st.error(f"{len(bajos)} productos con stock bajo")
    st.dataframe(bajos[['producto', 'cantidad_recibida']])
else:
    st.success("Todo en orden")

inventario_basico_app()

st.markdown("### Actualizar Inventario")
edited = st.data_editor(df_stock, num_rows="dynamic")
if st.button("Guardar cambios"):
    st.session_state.df_stock = edited
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.success("Actualizado")
    st.rerun()
""",

    "pages/3_Analisis.py": """# pages/3_Analisis.py
import streamlit as st
from modules.analytics import analytics_app

st.title("Análisis")

if 'df_ventas' not in st.session_state:
    st.warning("Sube datos en **Archivos**")
    st.stop()

if 'df_resultados' not in st.session_state:
    with st.spinner("Procesando..."):
        try:
            from modules.core_analysis import procesar_multiple_productos
            st.session_state.df_resultados = procesar_multiple_productos(
                st.session_state.df_ventas,
                st.session_state.get('df_stock', pd.DataFrame())
            )
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

analytics_app()
""",

    "pages/4_Productos.py": """# pages/4_Productos.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Productos")

if 'df_ventas' not in st.session_state:
    st.warning("Sube ventas en **Archivos**")
    st.stop()

df_ventas = st.session_state.df_ventas.copy()
df_stock = st.session_state.get('df_stock', pd.DataFrame())

df_merge = df_ventas.merge(df_stock, on='producto', how='left')

producto = st.selectbox("Producto", sorted(df_merge['producto'].unique()))
df_prod = df_merge[df_merge['producto'] == producto]

col1, col2, col3 = st.columns(3)
with col1: st.metric("Ventas Totales", df_prod['cantidad_vendida'].sum())
with col2: st.metric("Stock", df_prod['cantidad_recibida'].sum() if 'cantidad_recibida' in df_prod.columns else 0)
with col3: 
    costo = df_prod.get('costo_unitario', pd.Series([10])).iloc[0] if not df_prod.empty else 10
    st.metric("Costo Unitario", f"${costo:.2f}")

fig = px.line(df_prod.groupby('fecha')['cantidad_vendida'].sum().reset_index(), x='fecha', y='cantidad_vendida')
st.plotly_chart(fig, use_container_width=True)
"""
}

# === ESCRIBIR ARCHIVOS ===
for filename, content in FILES.items():
    path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\n")
    print(f"Actualizado: {filename}")

print("\n¡TODOS LOS ARCHIVOS HAN SIDO ACTUALIZADOS AUTOMÁTICAMENTE!")
print("Ejecuta: streamlit run stock_zero_mvp.py")
