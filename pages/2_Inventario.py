# pages
import streamlit as st
import pandas as pd

st.title("Inventario")

if st.session_state.df_stock is None:
    st.warning("Sube el archivo de stock en **Archivos**")
    st.stop()

df_stock = st.session_state.df_stock.copy()

# === KPIs DINERO ===
col1, col2, col3 = st.columns(3)
valor_total = (df_stock['cantidad'] * df_stock.get('costo_unitario', 10)).sum()
with col1: st.metric("Valor Total Inventario", f"${valor_total:,.0f}")
with col2: st.metric("Productos en Stock", len(df_stock))
with col3: st.metric("Valor Promedio por Item", f"${valor_total/len(df_stock):.0f}" if len(df_stock)>0 else "$0")

# === ALERTAS ===
st.markdown("### Alertas de Stock")
df_bajo = df_stock[df_stock['cantidad'] < 10]
if not df_bajo.empty:
    st.error(f"**{len(df_bajo)} productos con stock bajo**")
    st.dataframe(df_bajo[['producto', 'cantidad']])
else:
    st.success("Todos los productos tienen stock suficiente")

# === EDITAR INVENTARIO ===
st.markdown("### Actualizar Inventario")
edited = st.data_editor(df_stock, num_rows="dynamic")
if st.button("Guardar Cambios en Inventario"):
    st.session_state.df_stock = edited
    st.success("Inventario actualizado globalmente")
