# pages/2_Inventario.py
import streamlit as st
from modules.components import inventario_basico_app

st.title("Inventario")

# === SIDEBAR (SOLO EN PÁGINAS) ===
with st.sidebar:
    st.page_link("stock_zero_mvp.py", label="Home", icon="🏠")
    st.page_link("pages/1_Archivos.py", label="Archivos", icon="📁")
    st.page_link("pages/2_Inventario.py", label="Inventario", icon="📦")
    st.page_link("pages/3_Analisis.py", label="Análisis", icon="📊")
    st.page_link("pages/3_Analisis.py", label="Productos", icon="🛒")

if st.session_state.get('df_stock') is None:
    st.warning("Sube stock en **Archivos**")
    st.stop()

df_stock = st.session_state.df_stock

# === KPIs DINERO ===
col1, col2, col3 = st.columns(3)
valor_total = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum()
with col1: st.metric("Valor Total Inventario", f"${valor_total:,.0f}")
with col2: st.metric("Productos en Stock", len(df_stock))
with col3: st.metric("Valor Promedio por Item", f"${valor_total/len(df_stock):.0f}" if len(df_stock) > 0 else "$0")

# === ALERTAS ===
st.markdown("### Alertas de Stock")
df_bajo = df_stock[df_stock['cantidad_recibida'] < 10]
if not df_bajo.empty:
    st.error(f"**{len(df_bajo)} productos con stock bajo**")
    st.dataframe(df_bajo[['producto', 'cantidad_recibida']])
else:
    st.success("Todos los productos tienen stock suficiente")

# === TU FUNCIÓN ORIGINAL ===
inventario_basico_app()

# === EDITAR INVENTARIO ===
st.markdown("### Actualizar Inventario")
edited = st.data_editor(df_stock, num_rows="dynamic")
if st.button("Guardar Cambios"):
    st.session_state.df_stock = edited
    st.success("Inventario actualizado globalmente")
